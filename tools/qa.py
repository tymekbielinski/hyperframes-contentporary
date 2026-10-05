"""The automated QA gate — standards/core/qa.md §1: all 11 checks, PASS / FAIL per check.

Usage:
  python3 tools/qa.py videos/<slug> [--render R.mp4] [--overlays DIR] [--edit CUT.mp4 [--face-ref T]
                                    [--threshold D]] [--probe-url URL] [--skip-render] [--json]

  --render     a render of the project to inspect (checks 9, 10). Default: render a draft with
               `npx hyperframes render -q draft` into renders/qa-draft.mp4.
  --overlays   renders of the over-footage overlays (<name>.mov / .mp4 per compositions/overlays/<name>.html).
               Default: render each overlay as a draft (`render -c compositions/overlays/<name>.html`) into
               renders/qa-overlays/. Each overlay must settle (check 9) and not flicker (check 10).
  --edit       the edited timeline (basic edit + graphics) for the post-render density check;
               --face-ref / --threshold are passed to tools/cadence_scan.py.
  --probe-url  probe this URL instead of starting `npx hyperframes preview` (checks 5, 6, 10); overlays are
               probed through the same studio's per-file route (/preview/comp/<file>).
  --skip-render  do not render: checks 9 and 10 report SKIP, so the gate cannot pass.

The runtime probe (checks 5, 6, 10) covers index.html and every compositions/overlays/*.html document, each
through `npx hyperframes preview` (overlays via the studio route /api/projects/<name>/preview/comp/<file>).
Check 9 also cross-checks the plan: long-form slots must pair one-to-one with the full-frame grid rows, each
within ±1.5 frames of its row; full-frame rows with no slot (or a Short's grid with no full-frame scene) is
"nothing measured", a FAIL. The report records generated_at, the render inspected and inputs_hash (see
tools/project.py inputs_hash) so the preview pack can tell a stale report.

Writes renders/qa-report.json (read by tools/preview_pack.py). Exit 0 only when every check is PASS
or WAIVED. A BRIEF exception "check <n>: <reason>" waives check n; "check <n> [<text>]: <reason>"
waives only the findings that contain <text> as a whole path or word. Every other exception is listed, not
applied. Infrastructure findings (class Infra: probe/render/scan failures, internal errors, the placeholder
guard) are never waived. Each check is isolated: an exception inside one is a FAIL of that check.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import brandcheck
import cadence_scan
import media
import project as pj
import refs
import runtime_probe
import scan_flicker
import sync_lib

ROOT = Path(__file__).resolve().parents[1]
NAMES = {1: "HyperFrames validity", 2: "No lib fork", 3: "BRIEF complete", 4: "Seek-safety", 5: "Blur law",
         6: "Easing vocabulary", 7: "Captions", 8: "Density", 9: "Settle before cut", 10: "Render traps", 11: "Reference patterns"}
SIZES = {"long-form": (1920, 1080), "shorts": (1080, 1920)}
SETTLE_WINDOW = 0.3     # qa.md check 9: the last 0.3 s of each full-frame scene is still
SETTLE_MAX = 1.5        # mean |Δluma| (0–255, 320×180) per frame step that still counts as "still" (hold creep passes)
SHORTS_EXIT = 0.36      # Shorts scenes leave on the 0.36 s wipe: settle is measured before it
CHECK_TIMEOUT = 300     # s — `npx hyperframes check` (first run downloads the CLI)
RENDER_TIMEOUT = 1800   # s — `npx hyperframes render -q draft`
WAIVER = re.compile(r"\s*check\s+(\d+)\s*(?:\[([^\]]+)\])?\s*:\s*(\S.*)", re.I)
PLACEHOLDER = re.compile(r"""\bid\s*=\s*["']hf-placeholder["']""")
PLACEHOLDER_MSG = "index.html: remove the scaffold placeholder #hf-placeholder now that scenes exist"
BRAND_JS_TIMEOUT = 60  # s — `node lib/brand.js` (check 3)
OVERLAY_DIR = "compositions/overlays"
CAPTION_LAYER = re.compile(r"""(?:\b(?:id|class)\s*=\s*["'][^"']*\bcaptions?\b[^"']*["']|\bdata-captions\b)""", re.I)


class Infra(str):
    """A finding no BRIEF waiver can clear: the gate could not inspect something (probe failed, draft render
    failed or has no frames, internal error, tool missing or timed out) or the scaffold placeholder guard."""


def result(n, findings=None, note="", status=None):
    findings = findings or []
    return {"n": n, "name": NAMES[n], "status": status or ("FAIL" if findings else "PASS"),
            "findings": findings, "note": note}


def internal(e) -> Infra:
    return Infra(f"internal error: {type(e).__name__}: {e}")


def guarded(n, fn, *args):
    """Run one check; any exception becomes a FAIL of that check, never a crash of the gate."""
    try:
        return fn(*args)
    except Exception as e:
        return result(n, [internal(e)])


def read_text(path, project) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise ValueError(f"{Path(path).relative_to(project)} is not UTF-8 text (byte {e.start}: {e.reason})")


def run_hf(args, timeout_s, what):
    """The HyperFrames CLI with a timeout, killed as a process group on timeout; a CompletedProcess, or an Infra
    message when it could not run or finish."""
    try:
        return runtime_probe.run_with_timeout(runtime_probe.hyperframes_cmd() + args, timeout_s)
    except runtime_probe.ProbeError as e:
        return Infra(f"{what}: {e} (set HF_CLI to a working HyperFrames CLI)")


def composition_files(project) -> list:
    project = Path(project)
    files = [project / "index.html"] if (project / "index.html").is_file() else []
    comp = project / "compositions"
    if comp.is_dir():
        files += sorted(p for p in comp.rglob("*") if p.suffix in (".html", ".js", ".mjs", ".css") and p.is_file())
    return files


def overlay_files(project) -> list:
    """Over-footage overlay documents (standalone HTML), as project-relative posix paths, in name order."""
    d = Path(project) / OVERLAY_DIR
    return [p.relative_to(project).as_posix() for p in sorted(d.glob("*.html")) if p.is_file()] if d.is_dir() else []


def static_scan(project, fmt) -> list:
    files = composition_files(project)
    if not files:
        return []
    for f in files:
        read_text(f, project)          # a non-UTF-8 file is named, not silently decoded with replacements
    node = shutil.which("node")
    if not node:
        raise RuntimeError("node is required for the static scan (tools/lawscan.js)")
    r = subprocess.run([node, str(ROOT / "tools" / "lawscan.js"), "--ruleset", "composition", "--format", fmt,
                        *[str(f.relative_to(project)) for f in files]], capture_output=True, text=True, cwd=project,
                       timeout=120)
    if r.returncode not in (0, 1):
        raise RuntimeError("lawscan failed: " + r.stderr.strip()[-400:])
    try:
        found = json.loads(r.stdout)
        if not isinstance(found, list) or not all(isinstance(f, dict) and {"file", "line", "check", "message"} <= set(f) for f in found):
            raise ValueError("expected a JSON list of findings")
    except ValueError as e:
        raise RuntimeError(f"lawscan printed unusable output ({e}): {(r.stdout or r.stderr).strip()[:300]}")
    return found


def placeholder_findings(project) -> list:
    """new_video's inert #hf-placeholder keeps an empty reel valid; once the project has any real scene
    (a composition slot, a compositions/*.html scene or a beat-grid row) it must be gone."""
    project = Path(project)
    index = project / "index.html"
    if not index.is_file() or not PLACEHOLDER.search(re.sub(r"<!--.*?-->", "", read_text(index, project), flags=re.S)):
        return []
    try:
        slots = pj.composition_slots(project)
    except pj.ProjectError:
        slots = []
    try:
        rows = pj.read_storyboard(project)
    except pj.ProjectError:
        rows = []
    scenes = sorted((project / "compositions").glob("*.html")) if (project / "compositions").is_dir() else []
    if slots or rows or scenes:
        return [Infra(PLACEHOLDER_MSG)]
    return []


def check_hyperframes(project):
    try:
        found = placeholder_findings(project)
    except Exception as e:
        found = [internal(e)]
    r = run_hf(["check", str(project)], CHECK_TIMEOUT, "npx hyperframes check")
    if isinstance(r, Infra):
        return result(1, found + [r])
    if r.returncode == 0:
        return result(1, found)
    tail = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()][-15:]
    return result(1, found + (tail or [f"npx hyperframes check exited {r.returncode}"]))


def check_brief(project, brief, root=ROOT):
    errors = pj.validate_brief(brief, root)
    brand, palette, font = brief.get("brand"), brief.get("palette"), brief.get("font")
    if errors or not all(isinstance(x, str) for x in (brand, palette, font)):
        return result(3, errors)
    brand_dir = Path(root) / "brands" / brand
    mode = brandcheck.load_brand(brand_dir)["palettes"][palette]["mode"]
    root_mode = pj.root_attrs(project).get("data-hf-mode")
    if root_mode != mode:
        errors.append(f"index.html root data-hf-mode is {root_mode!r}, palette {palette} is {mode!r}")
    cmd = [shutil.which("node") or "node", str(Path(root) / "lib" / "brand.js"), str(brand_dir), "--palette", palette, "--font", font]
    for k, v in (brief.get("overrides") or {}).items():
        cmd += ["--override", f"{k}={v}"]
    shown = " ".join(c if " " not in c else repr(c) for c in cmd[1:])
    try:
        want = subprocess.run(cmd, capture_output=True, text=True, timeout=BRAND_JS_TIMEOUT)
    except subprocess.TimeoutExpired:
        return result(3, errors + [Infra(f"lib/brand.js timed out after {BRAND_JS_TIMEOUT} s (node {shown})")])
    css = Path(project) / "compositions" / "brand.css"
    if want.returncode != 0:
        errors.append("lib/brand.js: " + want.stderr.strip())
        return result(3, errors)
    try:
        have = css.read_text(encoding="utf-8") if css.is_file() else None
    except UnicodeDecodeError as e:
        errors.append(f"compositions/brand.css is not UTF-8 text (byte {e.start}: {e.reason}) — regenerate: node {shown} > compositions/brand.css")
        return result(3, errors)
    if have != want.stdout:
        errors.append(f"compositions/brand.css does not match the BRIEF's palette/font/overrides — regenerate: node {shown} > compositions/brand.css")
    return result(3, errors)


def check_captions(project, brief, rows):
    fmt = brief.get("format")
    layers = []
    for f in composition_files(project):
        text = re.sub(r"<!--.*?-->", "", read_text(f, project), flags=re.S)
        for m in CAPTION_LAYER.finditer(text):
            layers.append(f"{f.relative_to(project)}:{text[:m.start()].count(chr(10)) + 1}: caption layer ({m.group(0).strip()})")
    layers += [f"storyboard.md line {r['line']}: row of type {r['type']!r}" for r in rows
               if r["type"].strip().lower() in ("caption", "captions")]
    if fmt == "long-form":
        return result(7, layers, "long-form: no caption layer except kit.lower-third")
    if brief.get("captions") is True:
        return result(7, [] if layers else ["captions: true but no caption layer found (id/class 'captions' or data-captions)"])
    return result(7, layers, "Shorts: captions: false")


def check_patterns(rows, fmt, root=ROOT):
    """Check 11: every long-form storyboard row cites a kit name or catalogue ID (references/README.md);
    an ID-shaped token that is not in the registry fails; a pattern with no reviewed exemplar warns."""
    if fmt != "long-form":
        return result(11, [], "shorts: no pattern registry yet")
    lib = refs.load_library(root)
    findings, warnings = [], []
    for r in rows:
        where = f"storyboard.md line {r['line']}"
        known, unknown = refs.type_ids(r["type"], lib["registry"])
        if unknown:
            findings.append(f"{where}: unknown pattern ID(s) {', '.join(unknown)} — use an ID from standards/formats/long-form.md")
        if not known and not unknown:
            findings.append(f"{where}: type {r['type']!r} cites no kit name or catalogue ID")
        warnings += [f"{where}: {pid} has no reviewed reference exemplar yet" for pid in known if not refs.exemplars(lib, pid)]
    out = result(11, findings, "type column → standards/formats/long-form.md IDs; evidence in references/patterns/")
    out["warnings"] = warnings
    return out


def settle_findings(diffs, scenes, fps, max_step=SETTLE_MAX) -> list:
    """scenes: [(label, window_start, window_end)] in render seconds; every step inside must be ≤ max_step."""
    out = []
    for label, a, b in scenes:
        fa, fb = max(0, round(a * fps)), round(b * fps)
        steps = [(diffs[f], f) for f in range(fa, min(fb - 1, len(diffs)))]
        if not steps:
            out.append(Infra(f"{label}: no frames in its last {SETTLE_WINDOW} s ({a:.2f}–{b:.2f} s) — is the render complete?"))
            continue
        worst, f = max(steps)
        if worst > max_step:
            out.append(f"{label}: still moving in its last {SETTLE_WINDOW} s (frame step {worst:.1f} > {max_step} at {(f + 1) / fps:.2f} s)")
    return out


def plan_findings(project, fmt, rows, fps) -> list:
    """Check 9's plan cross-check (it needs no render). Long-form: index.html slots pair one-to-one with the
    full-frame grid rows in timeline order, each within ±1.5 frames of its row (tools/project.py slot_pairing,
    shared with slice.py). Full-frame rows with no slot, or a Short's grid with no full-frame row, leave check 9
    nothing to measure — a FAIL, never a silent PASS."""
    full = [r for r in rows if r["placement"] == "full-frame"]
    if fmt == "long-form":
        slots = pj.composition_slots(project)
        if full and not slots:
            return [f"storyboard.md has {len(full)} full-frame row(s) but index.html has no scene slots — nothing measured"]
        return pj.slot_pairing(slots, rows, fps)[1]
    if rows and not full:
        return [f"storyboard.md has {len(rows)} row(s) but no full-frame scene — nothing measured (check 9 settles full-frame rows)"]
    return []


def size_findings(info, fmt, label) -> list:
    want = SIZES[fmt]
    if (info["width"], info["height"]) != want:
        return [Infra(f"{label} is {info['width']}×{info['height']}, expected {want[0]}×{want[1]} ({fmt}) — inspect the right render")]
    return []


def scene_windows(project, fmt, rows) -> list:
    if fmt == "long-form":
        return [(s["id"], s["start"] + s["dur"] - SETTLE_WINDOW, s["start"] + s["dur"]) for s in pj.composition_slots(project)]
    return [(f"row {r['row']} ({r['t_in']:g}–{r['t_out']:g} s)", r["t_out"] - SHORTS_EXIT - SETTLE_WINDOW, r["t_out"] - SHORTS_EXIT)
            for r in rows if r["placement"] == "full-frame"]


def boundaries(project, fmt, rows) -> list:
    """Render times where a hard cut is intended (never reported as flicker)."""
    if fmt == "long-form":
        return [s["start"] for s in pj.composition_slots(project)]
    return [t for r in rows if r["placement"] == "full-frame" for t in (r["t_in"], r["t_out"])]


def flicker_findings(diffs, fps, cut_times, compare) -> list:
    """compare: scan_flicker.frame_comparer(render) — confirms the picture returned to its prior frame."""
    cut_frames = {round(t * fps) + k for t in cut_times for k in (-1, 0, 1)}
    return [f"flicker at frame {f} ({f / fps:.2f} s): step {step} vs local {local}"
            for f, step, local in scan_flicker.find_flicker(diffs, compare) if f not in cut_frames]


def scope_matches(scope, finding) -> bool:
    """A scoped waiver's text must match a whole path or word: [a.html] matches compositions/a.html:3 but not
    data.html or a.html.bak."""
    return re.search(r"(?<![\w.-])" + re.escape(scope) + r"(?![\w-]|\.\w)", finding) is not None


def apply_waivers(checks, exceptions) -> list:
    """Mutates checks; returns the exceptions that were not waivers (listed in the report).
    Infra findings (the gate could not inspect something, or the placeholder guard) are never waived."""
    listed = []
    for e in exceptions or []:
        m = WAIVER.fullmatch(e) if isinstance(e, str) else None
        if not m or int(m.group(1)) not in NAMES:
            listed.append(e)
            continue
        c = next(c for c in checks if c["n"] == int(m.group(1)))
        scope, reason = m.group(2), m.group(3)
        if c["status"] != "FAIL":
            continue
        kept = [f for f in c["findings"] if isinstance(f, Infra) or (scope and not scope_matches(scope, f))]
        waived = len(c["findings"]) - len(kept)
        if waived:
            c["findings"] = kept
            c["waived"] = c.get("waived", []) + [f"{waived} finding(s): {reason}"]
            if not kept:
                c["status"] = "WAIVED"
    return listed


def check_density(project, edit, face_ref=None, threshold=None):
    try:
        reports = [cadence_scan.report(project)] + (
            [cadence_scan.report(project, edit=edit, face_ref=face_ref, threshold=threshold)] if edit else [])
    except (pj.ProjectError, media.MediaError, ValueError) as e:
        return result(8, [str(e)])
    failing = [(r, x) for r in reports for x in r["results"] if not x["ok"]]
    c = result(8, [f"{r['source']}: {x['name']}: {x['detail']}" for r, x in failing if not r.get("advisory")])
    c["density"] = reports
    cadence_warnings = [f"{r['source']}: {w}" for r in reports for w in r.get("warnings") or []]
    # an edit measured without a storyboard grid is advisory: its failures are shown, never failing on their own
    cadence_warnings += [f"{r['source']}: advisory FAIL: {x['name']}: {x['detail']}" for r, x in failing if r.get("advisory")]
    if cadence_warnings:     # shown, never failing on their own
        c["warnings"] = cadence_warnings
    return c


def measure(path, fmt, label):
    """(info, diffs, size findings) of one render, or raises media.MediaError."""
    info = media.video_info(path)
    return info, media.frame_diffs(path), size_findings(info, fmt, label)


def check_reel(project, fmt, rows, render_path):
    """Checks 9 and 10 on the reel: ([findings 9], [findings 10], fps)."""
    try:
        info, diffs, bad = measure(render_path, fmt, "render")
    except media.MediaError as e:
        bad = Infra(f"render unreadable: {e}")
        return [bad], [bad], 30.0
    fps = info["fps"]
    try:
        f9 = bad + settle_findings(diffs, scene_windows(project, fmt, rows), fps)
    except Exception as e:
        f9 = bad + [internal(e)]
    try:
        cuts = boundaries(project, fmt, rows) + (media.scene_cuts(render_path) if fmt == "shorts" else [])
        f10 = bad + flicker_findings(diffs, fps, cuts, scan_flicker.frame_comparer(render_path))
    except Exception as e:
        f10 = bad + [internal(e)]
    return f9, f10, fps


def render_overlays(project, overlays, overlays_dir):
    """{overlay rel: render path | Infra}. Given renders come from overlays_dir (<stem>.mov or .mp4); otherwise
    each overlay document is rendered as a draft with `npx hyperframes render -c <file>`."""
    out = {}
    for rel in overlays:
        stem = Path(rel).stem
        if overlays_dir:
            found = [Path(overlays_dir) / f"{stem}{ext}" for ext in (".mov", ".mp4") if (Path(overlays_dir) / f"{stem}{ext}").is_file()]
            out[rel] = found[0] if found else Infra(f"{rel}: no render {stem}.mov or {stem}.mp4 in {overlays_dir}")
            continue
        path = Path(project) / "renders" / "qa-overlays" / f"{stem}.mp4"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.unlink(missing_ok=True)
        r = run_hf(["render", str(project), "-c", rel, "-q", "draft", "-o", str(path)], RENDER_TIMEOUT, f"{rel}: draft render failed")
        if isinstance(r, Infra):
            out[rel] = r
        elif r.returncode != 0 or not path.is_file():
            out[rel] = Infra(f"{rel}: draft render failed: " + ((r.stderr or r.stdout).strip()[-400:] or f"exit {r.returncode}"))
        else:
            out[rel] = path
    return out


def check_overlay_render(rel, path, fmt):
    """Checks 9 and 10 on one overlay render: it settles (its last 0.3 s is still) and does not flicker."""
    if isinstance(path, Infra):
        return [path], [path]
    try:
        info, diffs, bad = measure(path, fmt, f"{rel}: render")
    except media.MediaError as e:
        bad = Infra(f"{rel}: render unreadable: {e}")
        return [bad], [bad]
    fps = info["fps"]
    end = (len(diffs) + 1) / fps
    f9 = bad + settle_findings(diffs, [(rel, end - SETTLE_WINDOW, end)], fps)
    try:
        f10 = bad + [f"{rel}: {f}" for f in flicker_findings(diffs, fps, [], scan_flicker.frame_comparer(path))]
    except Exception as e:
        f10 = bad + [Infra(f"{rel}: internal error: {type(e).__name__}: {e}")]
    return f9, f10


def runtime_findings(runtime, overlays, n) -> list:
    """Runtime-probe findings for check n: the reel's, then each overlay's prefixed with its file. Page exceptions
    are check 10 findings; an overlay the probe failed on (or never reported) is an Infra finding of 5, 6 and 10."""
    def fmt_one(f):
        return f"runtime{'' if f.get('t') is None else ' @ ' + str(f['t']) + ' s'}: {f.get('message')}"
    found = [fmt_one(f) for f in runtime.get("findings") or [] if isinstance(f, dict) and f.get("check") == n]
    if n == 10:
        found += [f"page error: {e}" for e in runtime.get("errors") or []]
    by_file = {o.get("file"): o for o in runtime.get("overlays") or [] if isinstance(o, dict)}
    for rel in overlays:
        o = by_file.get(rel)
        if o is None or (o.get("error") is None and not isinstance(o.get("findings"), list)):
            if n in (5, 6, 10):
                found.append(Infra(f"runtime probe did not cover {rel}"))
            continue
        if o.get("error") is not None:
            if n in (5, 6, 10):
                found.append(Infra(f"runtime probe failed: {rel}: {o['error']}"))
            continue
        found += [f"{rel}: {fmt_one(f)}" for f in o["findings"] if isinstance(f, dict) and f.get("check") == n]
        if n == 10:
            found += [f"{rel}: page error: {e}" for e in o.get("errors") or []]
    return found


def probe_summary(runtime, overlays) -> dict:
    by_file = {o.get("file"): o for o in runtime.get("overlays") or [] if isinstance(o, dict)}
    return {"samples": runtime.get("samples"),
            "overlays": {rel: (by_file[rel].get("samples") if rel in by_file and by_file[rel].get("error") is None
                               else "not probed") for rel in overlays}}


def run_gate(project, render=None, edit=None, probe_url=None, skip_render=False, probe=None, root=ROOT,
             face_ref=None, threshold=None, overlays_dir=None) -> dict:
    project = Path(project)
    out = project / "renders" / "qa-report.json"
    out.unlink(missing_ok=True)        # a crash must never leave an old PASS behind
    checks = {}
    try:
        brief, brief_error = pj.read_brief(project), None
        if not isinstance(brief, dict):
            raise ValueError("BRIEF did not parse to a mapping")
    except pj.ProjectError as e:
        brief, brief_error = {}, str(e)
    except Exception as e:
        brief, brief_error = {}, internal(e)
    fmt = brief.get("format") if brief.get("format") in pj.FORMATS else "long-form"
    try:
        rows, rows_error = pj.read_storyboard(project), None
    except pj.ProjectError as e:
        rows, rows_error = [], str(e)
    except Exception as e:
        rows, rows_error = [], internal(e)
    overlays = overlay_files(project)

    checks[1] = guarded(1, check_hyperframes, project)
    checks[2] = guarded(2, lambda: result(2, sync_lib.check(project, root)))
    checks[3] = result(3, [brief_error]) if brief_error else guarded(3, check_brief, project, brief, root)

    try:
        static, static_error = static_scan(project, fmt), None
    except Exception as e:
        static, static_error = [], Infra(f"static scan failed: {type(e).__name__}: {e}")
    try:
        if probe:
            runtime = probe(project, fmt)
        elif probe_url:
            runtime = runtime_probe.probe_url(probe_url, fmt, SIZES[fmt])
            if overlays:
                runtime["overlays"] = runtime_probe.probe_overlays(probe_url, overlays, fmt, SIZES[fmt])
        else:
            runtime = runtime_probe.probe_project(project, fmt, SIZES[fmt], overlays=overlays)
        if not isinstance(runtime, dict) or not isinstance(runtime.get("findings"), list):
            raise runtime_probe.ProbeError("probe returned no findings list")
        runtime_error = None
    except runtime_probe.ProbeError as e:
        runtime, runtime_error = {"findings": []}, Infra(f"runtime probe failed: {e}")
    except Exception as e:
        runtime, runtime_error = {"findings": []}, Infra(f"runtime probe failed: {type(e).__name__}: {e}")

    def merged(n):
        found = [f"{f['file']}:{f['line']}: {f['message']}" for f in static if f["check"] == n]
        if runtime_error:
            found += [runtime_error] if n in (5, 6, 10) else []
        else:
            found += runtime_findings(runtime, overlays, n)
        return found + ([static_error] if static_error and n in (4, 5, 6, 10) else [])

    checks[4] = result(4, merged(4))
    checks[5] = result(5, merged(5))
    checks[6] = result(6, merged(6))
    checks[7] = result(7, [rows_error]) if rows_error else guarded(7, check_captions, project, brief, rows)
    checks[8] = result(8, [rows_error or brief_error]) if rows_error or brief_error else \
        guarded(8, check_density, project, edit, face_ref, threshold)
    checks[11] = result(11, [rows_error]) if rows_error else guarded(11, check_patterns, rows, fmt, root)

    render_path, render_note = render, None
    if not render_path and not skip_render:
        render_path = project / "renders" / "qa-draft.mp4"
        render_path.parent.mkdir(parents=True, exist_ok=True)
        render_path.unlink(missing_ok=True)
        r = run_hf(["render", str(project), "-q", "draft", "-o", str(render_path)], RENDER_TIMEOUT, "draft render failed")
        if isinstance(r, Infra):
            render_path, render_note = None, r
        elif r.returncode != 0:
            render_path, render_note = None, Infra("draft render failed: " + (r.stderr or r.stdout).strip()[-400:])

    f9, f10, fps = [], merged(10), 30.0
    if render_path:
        try:
            r9, r10, fps = check_reel(project, fmt, rows, render_path)
        except Exception as e:
            r9, r10 = [internal(e)], [internal(e)]
        f9, f10 = f9 + r9, f10 + r10
    elif render_note:
        f9, f10 = f9 + [render_note], f10 + [render_note]
    if not rows_error:
        try:
            f9 = plan_findings(project, fmt, rows, fps) + f9
        except Exception as e:
            f9 = [internal(e)] + f9
    if overlays and not skip_render:
        try:
            for rel, path in render_overlays(project, overlays, overlays_dir).items():
                o9, o10 = check_overlay_render(rel, path, fmt)
                f9, f10 = f9 + o9, f10 + o10
        except Exception as e:
            f9, f10 = f9 + [internal(e)], f10 + [internal(e)]
    note = f"render: {render_path}" if render_path else (render_note or "skipped: no render (--skip-render)")
    skipped = not render_path and not render_note
    checks[9] = result(9, f9, note, status=None if f9 or not skipped else "SKIP")
    checks[10] = result(10, f10, note, status=None if f10 or not skipped else "SKIP")

    ordered = [checks[n] for n in sorted(checks)]
    listed = apply_waivers(ordered, brief.get("exceptions"))
    warnings = [f"check {c['n']}: {w}" for c in ordered for w in c.get("warnings", [])]
    warnings += [f"runtime probe: {w}" for w in runtime.get("warnings") or []]
    report = {"project": str(project), "format": fmt, "checks": ordered, "exceptions": listed,
              "waivers": [e for e in (brief.get("exceptions") or []) if e not in listed], "warnings": warnings,
              "probe": probe_summary(runtime, overlays),
              "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "render": str(Path(render_path).resolve()) if render_path else None,
              # hashed last: the preview server may stamp data-hf-id attributes into project files during the probe
              "inputs_hash": pj.inputs_hash(project, root),
              "ok": all(c["status"] in ("PASS", "WAIVED") for c in ordered)}
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + ".tmp")
    tmp.write_text(json.dumps(report, indent=2) + "\n")
    os.replace(tmp, out)               # atomic: a reader never sees a half-written report
    return report


def format_report(r) -> str:
    lines = [f"QA gate — {r['project']} ({r['format']})"]
    for c in r["checks"]:
        lines.append(f"  {c['n']:>2} {c['status']:<6} {c['name']}" + (f"  ({c['note']})" if c["note"] and c["status"] != "PASS" else ""))
        lines += [f"         - {f}" for f in c["findings"][:20]]
        if len(c["findings"]) > 20:
            lines.append(f"         … {len(c['findings']) - 20} more")
        lines += [f"         waived: {w}" for w in c.get("waived", [])]
        lines += [f"         warning: {w}" for w in c.get("warnings", [])]
    lines += [f"  warning: {w}" for w in r.get("warnings", []) if w.startswith("runtime probe: ")]
    pr = r.get("probe") or {}
    if pr.get("samples") is not None or pr.get("overlays"):
        lines.append("  runtime probe: " + "; ".join(
            [f"{pr.get('samples')} samples (index.html)"] +
            [f"{rel}: {n} samples" if isinstance(n, int) else f"{rel}: {n}" for rel, n in (pr.get("overlays") or {}).items()]))
    if r["exceptions"]:
        lines.append("  exceptions (listed in the preview pack): " + "; ".join(map(str, r["exceptions"])))
    failed = [c for c in r["checks"] if c["status"] not in ("PASS", "WAIVED")]
    lines.append("  RESULT: PASS" if r["ok"] else f"  RESULT: FAIL ({len(failed)} of {len(r['checks'])} checks not passing)")
    return "\n".join(lines)


def main(argv) -> int:
    ap = argparse.ArgumentParser(prog="python3 tools/qa.py")
    ap.add_argument("project")
    ap.add_argument("--render")
    ap.add_argument("--edit")
    ap.add_argument("--probe-url")
    ap.add_argument("--skip-render", action="store_true")
    ap.add_argument("--overlays")
    ap.add_argument("--face-ref", type=float)
    ap.add_argument("--threshold", type=float)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv[1:])
    if (a.face_ref is not None or a.threshold is not None) and not a.edit:
        ap.error("--face-ref and --threshold apply to the edit density: pass --edit too")
    if not Path(a.project).is_dir():
        print(f"{a.project}: not a directory")
        return 2
    r = run_gate(a.project, a.render, a.edit, a.probe_url, a.skip_render, face_ref=a.face_ref,
                 threshold=a.threshold, overlays_dir=a.overlays)
    print(json.dumps(r, indent=2) if a.json else format_report(r))
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
