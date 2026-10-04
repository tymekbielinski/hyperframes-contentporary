"""The automated QA gate — standards/core/qa.md §1: all 10 checks, PASS / FAIL per check.

Usage:
  python3 tools/qa.py videos/<slug> [--render R.mp4] [--edit CUT.mp4] [--probe-url URL]
                                    [--skip-render] [--json]

  --render     a render of the project to inspect (checks 9, 10). Default: render a draft with
               `npx hyperframes render -q draft` into renders/qa-draft.mp4.
  --edit       the edited timeline (basic edit + graphics) for the post-render density check.
  --probe-url  probe this URL instead of starting `npx hyperframes preview` (checks 5, 6, 10).
  --skip-render  do not render: checks 9 and 10 report SKIP, so the gate cannot pass.

Writes renders/qa-report.json (read by tools/preview_pack.py). Exit 0 only when every check is PASS
or WAIVED. A BRIEF exception "check <n>: <reason>" waives check n; "check <n> [<text>]: <reason>"
waives only the findings that contain <text>. Every other exception is listed, not applied.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import brandcheck
import cadence_scan
import media
import project as pj
import runtime_probe
import scan_flicker
import sync_lib

ROOT = Path(__file__).resolve().parents[1]
NAMES = {1: "HyperFrames validity", 2: "No lib fork", 3: "BRIEF complete", 4: "Seek-safety", 5: "Blur law",
         6: "Easing vocabulary", 7: "Captions", 8: "Density", 9: "Settle before cut", 10: "Render traps"}
SIZES = {"long-form": (1920, 1080), "shorts": (1080, 1920)}
SETTLE_WINDOW = 0.3     # qa.md check 9: the last 0.3 s of each full-frame scene is still
SETTLE_MAX = 1.5        # mean |Δluma| (0–255, 320×180) per frame step that still counts as "still" (hold creep passes)
SHORTS_EXIT = 0.36      # Shorts scenes leave on the 0.36 s wipe: settle is measured before it
WAIVER = re.compile(r"\s*check\s+(\d+)\s*(?:\[([^\]]+)\])?\s*:\s*(\S.*)", re.I)
PLACEHOLDER = re.compile(r"""\bid\s*=\s*["']hf-placeholder["']""")
CAPTION_LAYER = re.compile(r"""(?:\b(?:id|class)\s*=\s*["'][^"']*\bcaptions?\b[^"']*["']|\bdata-captions\b)""", re.I)


def result(n, findings=None, note="", status=None):
    findings = findings or []
    return {"n": n, "name": NAMES[n], "status": status or ("FAIL" if findings else "PASS"),
            "findings": findings, "note": note}


def composition_files(project) -> list:
    project = Path(project)
    files = [project / "index.html"] if (project / "index.html").is_file() else []
    comp = project / "compositions"
    if comp.is_dir():
        files += sorted(p for p in comp.rglob("*") if p.suffix in (".html", ".js", ".mjs", ".css") and p.is_file())
    return files


def static_scan(project, fmt) -> list:
    files = composition_files(project)
    if not files:
        return []
    node = shutil.which("node")
    if not node:
        raise RuntimeError("node is required for the static scan (tools/lawscan.js)")
    r = subprocess.run([node, str(ROOT / "tools" / "lawscan.js"), "--ruleset", "composition", "--format", fmt,
                        *[str(f.relative_to(project)) for f in files]], capture_output=True, text=True, cwd=project)
    if r.returncode not in (0, 1):
        raise RuntimeError("lawscan failed: " + r.stderr.strip())
    return json.loads(r.stdout)


def placeholder_findings(project) -> list:
    """new_video's inert #hf-placeholder keeps an empty reel valid; once the project has any real scene
    (a composition slot, a compositions/*.html scene or a beat-grid row) it must be gone."""
    project = Path(project)
    index = project / "index.html"
    if not index.is_file() or not PLACEHOLDER.search(re.sub(r"<!--.*?-->", "", index.read_text(), flags=re.S)):
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
        return ["index.html: remove the scaffold placeholder #hf-placeholder now that scenes exist"]
    return []


def check_hyperframes(project):
    found = placeholder_findings(project)
    r = subprocess.run(runtime_probe.hyperframes_cmd() + ["check", str(project)], capture_output=True, text=True)
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
    want = subprocess.run(cmd, capture_output=True, text=True)
    css = Path(project) / "compositions" / "brand.css"
    if want.returncode != 0:
        errors.append("lib/brand.js: " + want.stderr.strip())
    elif not css.is_file() or css.read_text() != want.stdout:
        shown = " ".join(c if " " not in c else repr(c) for c in cmd[1:])
        errors.append(f"compositions/brand.css does not match the BRIEF's palette/font/overrides — regenerate: node {shown} > compositions/brand.css")
    return result(3, errors)


def check_captions(project, brief, rows):
    fmt = brief.get("format")
    layers = []
    for f in composition_files(project):
        text = re.sub(r"<!--.*?-->", "", f.read_text(), flags=re.S)
        for m in CAPTION_LAYER.finditer(text):
            layers.append(f"{f.relative_to(project)}:{text[:m.start()].count(chr(10)) + 1}: caption layer ({m.group(0).strip()})")
    layers += [f"storyboard.md line {r['line']}: row of type {r['type']!r}" for r in rows
               if r["type"].strip().lower() in ("caption", "captions")]
    if fmt == "long-form":
        return result(7, layers, "long-form: no caption layer except kit.lower-third")
    if brief.get("captions") is True:
        return result(7, [] if layers else ["captions: true but no caption layer found (id/class 'captions' or data-captions)"])
    return result(7, layers, "Shorts: captions: false")


def settle_findings(diffs, scenes, fps, max_step=SETTLE_MAX) -> list:
    """scenes: [(label, window_start, window_end)] in render seconds; every step inside must be ≤ max_step."""
    out = []
    for label, a, b in scenes:
        fa, fb = max(0, round(a * fps)), round(b * fps)
        steps = [(diffs[f], f) for f in range(fa, min(fb - 1, len(diffs)))]
        if not steps:
            out.append(f"{label}: no frames in its last {SETTLE_WINDOW} s ({a:.2f}–{b:.2f} s) — is the render complete?")
            continue
        worst, f = max(steps)
        if worst > max_step:
            out.append(f"{label}: still moving in its last {SETTLE_WINDOW} s (frame step {worst:.1f} > {max_step} at {(f + 1) / fps:.2f} s)")
    return out


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


def flicker_findings(diffs, fps, cut_times) -> list:
    cut_frames = {round(t * fps) + k for t in cut_times for k in (-1, 0, 1)}
    return [f"flicker at frame {f} ({f / fps:.2f} s): step {step} vs local {local}"
            for f, step, local in scan_flicker.find_flicker(diffs) if f not in cut_frames]


def apply_waivers(checks, exceptions) -> list:
    """Mutates checks; returns the exceptions that were not waivers (listed in the report)."""
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
        kept = [f for f in c["findings"] if scope and scope not in f]
        waived = len(c["findings"]) - len(kept)
        if waived:
            c["findings"] = kept
            c["waived"] = c.get("waived", []) + [f"{waived} finding(s): {reason}"]
            if not kept:
                c["status"] = "WAIVED"
    return listed


def run_gate(project, render=None, edit=None, probe_url=None, skip_render=False, probe=None, root=ROOT) -> dict:
    project = Path(project)
    checks = {}
    try:
        brief = pj.read_brief(project)
    except pj.ProjectError as e:
        brief, brief_error = {}, str(e)
    else:
        brief_error = None
    fmt = brief.get("format") if brief.get("format") in pj.FORMATS else "long-form"
    try:
        rows = pj.read_storyboard(project)
        rows_error = None
    except pj.ProjectError as e:
        rows, rows_error = [], str(e)

    checks[1] = check_hyperframes(project)
    checks[2] = result(2, sync_lib.check(project, root))
    checks[3] = result(3, [brief_error]) if brief_error else check_brief(project, brief, root)

    static = static_scan(project, fmt)
    try:
        runtime = probe(project, fmt) if probe else (
            runtime_probe.probe_url(probe_url, fmt, SIZES[fmt]) if probe_url else
            runtime_probe.probe_project(project, fmt, SIZES[fmt]))
        runtime_error = None
    except runtime_probe.ProbeError as e:
        runtime, runtime_error = {"findings": []}, f"runtime probe failed: {e}"

    def merged(n):
        found = [f"{f['file']}:{f['line']}: {f['message']}" for f in static if f["check"] == n]
        found += [f"runtime{'' if f.get('t') is None else ' @ ' + str(f['t']) + ' s'}: {f['message']}"
                  for f in runtime["findings"] if f["check"] == n]
        return found + ([runtime_error] if runtime_error and n in (5, 6, 10) else [])

    checks[4] = result(4, merged(4))
    checks[5] = result(5, merged(5))
    checks[6] = result(6, merged(6))
    checks[7] = result(7, [rows_error]) if rows_error else check_captions(project, brief, rows)

    if rows_error or brief_error:
        checks[8] = result(8, [rows_error or brief_error])
    else:
        try:
            reports = [cadence_scan.report(project)] + ([cadence_scan.report(project, edit=edit)] if edit else [])
            checks[8] = result(8, [f"{r['source']}: {x['name']}: {x['detail']}" for r in reports for x in r["results"] if not x["ok"]])
            checks[8]["density"] = reports
            cadence_warnings = [f"{r['source']}: {w}" for r in reports for w in r.get("warnings") or []]
            if cadence_warnings:     # shown, never failing on their own
                checks[8]["warnings"] = cadence_warnings
        except (pj.ProjectError, media.MediaError, ValueError) as e:
            checks[8] = result(8, [str(e)])

    render_path, render_note = render, ""
    if not render_path and not skip_render:
        render_path = project / "renders" / "qa-draft.mp4"
        render_path.parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(runtime_probe.hyperframes_cmd() + ["render", str(project), "-q", "draft", "-o", str(render_path)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            render_path, render_note = None, "draft render failed: " + (r.stderr or r.stdout).strip()[-400:]
    if not render_path:
        why = render_note or "skipped: no render (--skip-render)"
        checks[9] = result(9, [render_note] if render_note else [], why, status=None if render_note else "SKIP")
        f10 = merged(10) + ([render_note] if render_note else [])
        checks[10] = result(10, f10, why, status=None if f10 else "SKIP")
    else:
        try:
            fps = media.video_info(render_path)["fps"]
            diffs = media.frame_diffs(render_path)
            cuts = boundaries(project, fmt, rows) + (media.scene_cuts(render_path) if fmt == "shorts" else [])
            checks[9] = result(9, settle_findings(diffs, scene_windows(project, fmt, rows), fps), f"render: {render_path}")
            checks[10] = result(10, merged(10) + flicker_findings(diffs, fps, cuts), f"render: {render_path}")
        except (media.MediaError, pj.ProjectError) as e:
            checks[9] = result(9, [str(e)])
            checks[10] = result(10, merged(10) + [str(e)])

    ordered = [checks[n] for n in sorted(checks)]
    listed = apply_waivers(ordered, brief.get("exceptions"))
    warnings = [f"check {c['n']}: {w}" for c in ordered for w in c.get("warnings", [])]
    warnings += [f"runtime probe: {w}" for w in runtime.get("warnings") or []]
    report = {"project": str(project), "format": fmt, "checks": ordered, "exceptions": listed,
              "waivers": [e for e in (brief.get("exceptions") or []) if e not in listed], "warnings": warnings,
              "ok": all(c["status"] in ("PASS", "WAIVED") for c in ordered)}
    out = project / "renders" / "qa-report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n")
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
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv[1:])
    if not Path(a.project).is_dir():
        print(f"{a.project}: not a directory")
        return 2
    r = run_gate(a.project, a.render, a.edit, a.probe_url, a.skip_render)
    print(json.dumps(r, indent=2) if a.json else format_report(r))
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
