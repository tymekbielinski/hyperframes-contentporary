# Plan 3 — Tools & Automated QA Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give every video project one-command tooling — scaffold, lib sync with content hashes, density scan, source-cut probe, flicker scan, delivery slicing, a preview pack — and an automated QA gate that runs all ten checks of `standards/core/qa.md` §1 with a clear PASS / FAIL per check.

**Architecture:** Each tool is one focused Python 3 standard-library file in `tools/` with a `main(argv)` CLI and importable functions, tested by `tools/test_<tool>.py` (unittest) on small synthetic inputs — ffmpeg `lavfi` clips generated per test, never footage. Shared readers sit underneath: `project.py` (BRIEF YAML block, beat grid, `index.html` slots, transcript), `media.py` (every measurement done by an ffmpeg filter: scene cuts, frame differences, luma samples, frames). The core-motion-law scanner moves out of `lib/test/hygiene.test.js` into `tools/lawscan.js` so the library test and QA checks 4–6 share it. What a static scan cannot see (blur reasons set with `setAttribute`, eases chosen at runtime, the render-only text traps) is read from the live page: `runtime_probe.py` serves the project with `npx hyperframes preview` — HyperFrames' own bundler and runtime — and `qa_probe.mjs` drives the chrome-headless-shell HyperFrames already downloads over the DevTools protocol from Node 22 built-ins. `qa.py` composes all of it into the gate.

**Tech Stack:** Python 3 standard library (unittest, subprocess, json, csv, statistics, html), Node ≥ 22 built-ins (`node:test`, global `WebSocket` and `fetch`), ffmpeg/ffprobe, the HyperFrames CLI (`npx hyperframes check | render | preview | browser`). No new dependencies.

**Spec:** `docs/superpowers/specs/2026-10-03-animation-workflow-design.md` — §8 (distribution: `sync-lib` + `lib.lock`), §9 (QA gate; superseded in detail by `standards/core/qa.md`), §10 (pipeline; superseded in detail by `standards/core/pipeline.md`). Roadmap: `docs/superpowers/plans/2026-10-03-animation-workflow-roadmap.md` — the Plan 3 row and "Notes for Plans 3–4". Normative detail: `standards/core/qa.md`, `standards/core/pipeline.md`, `standards/formats/long-form.md`, `standards/formats/shorts.md`, `lib/README.md`. Builds on Plan 2 (`2026-10-03-plan-2-shared-library.md`, merged to `main` at `4ba20c6`).

## Global Constraints

- **The ten automated checks, verbatim from `standards/core/qa.md` §1:** 1 HyperFrames validity (`npx hyperframes check`) · 2 No lib fork (the project's `lib.lock` hashes equal root `lib/`) · 3 BRIEF complete (`format`, `brand` (status `approved`), `palette`, `font`, `captions` (Shorts), `film`, `direction` present; `python3 tools/brandcheck.py` passes and the palette/font/overrides choice is valid (`brandcheck.validate_choice`)) · 4 Seek-safety (static scan: no `Math.random`, `Date.now`, `repeat: -1`, CSS `infinite` animations) · 5 Blur law (every `feGaussianBlur` / `blur()` carries `data-blur-reason` = `focus`, `glow` or `wipe` (`wipe` only in Shorts); camera and whip blur only via `HFMotionBlur`) · 6 Easing vocabulary (no raw curves outside the named `ease.*` tokens) · 7 Captions (long-form: no caption layer except `kit.lower-third`; Shorts: matches the `captions` flag) · 8 Density (long-form: hook (first `hook_end` s, default 80) ≥ 60 % graphics, no face gap > 6 s, body gaps ≤ 30 s (face punch-ins are not graphics) (BRIEF `screen_share` ranges exempt); Shorts 35–55 %) · 9 Settle before cut (the last 0.3 s of each full-frame scene is still (frame difference)) · 10 Render traps (text verified in rendered frames; `shorts.md` §9b traps apply to every format; seek-flicker scan).
- **Exceptions** are declared in the BRIEF under `exceptions:`, each with a reason; the gate passes declared exceptions and lists them in the preview pack.
- **Preview pack contents (`qa.md` §3):** a contact sheet of every graphic, a draft render of the hook plus one body scene, the density timeline, the exceptions list, and the final critique scores (any graphic still below 8 first).
- **BRIEF fields (`pipeline.md`):** `format` (long-form | shorts), `film` (required), `direction`, `references`, `gotchas`, `brand` (must be `status: approved`), `palette`, `font`, `overrides` (flat dot-path palette roles), `captions` (Shorts only: true | false), `hook_end` (long-form, default 80), `screen_share` (long-form ranges), `exceptions` (each with a reason), `source`.
- **Beat grid columns (`pipeline.md`):** `| t_in | t_out | words | placement | type | beats | ease | marks |`.
- **Project layout (`pipeline.md`):** `videos/<slug>/  BRIEF.md · transcript.json · storyboard.md · critique.md · assets/captures/MANIFEST.md · compositions/ · lib/ + lib.lock · deliver/`.
- **Delivery:** long-form full-frame scenes → silent MP4 clips (1920×1080, 30 fps) named by timeline timecode + `TIMECODES.csv` + README; over-footage layouts → ProRes 4444 with alpha (`npx hyperframes render --format=mov`); Shorts → one finished MP4 (1080×1920, 30 fps).
- **Shorts cuts:** `ffmpeg … select='gt(scene,0.20)'`; scene end = source cut + exit duration (wipe out 0.36 s).
- **Formats:** long-form 1920×1080, Shorts 1080×1920; every tool takes the size from the format, never assumes 16:9.
- **Standard library only** for Python; Node built-ins only for JS; ffmpeg/ffprobe and the HyperFrames CLI are the only external programs. No network beyond what HyperFrames itself needs (GSAP from its CDN, `npx`).
- **Tests use synthetic inputs only** (ffmpeg `lavfi` sources, temp directories); never real footage, never anything under `videos/`.
- **`videos/*` is frozen.** Read `videos/09-youtube-seo-high-ticket/scripts/slice.mjs`, `scan-flicker.py` and `deliver/` for the port; never edit them.
- **Edit blocks** in this plan are `bash` + Python heredocs: run each from the repo root. Every replacement asserts its target text appears exactly once, so a mismatch stops with the file and the first 70 characters of the missing text instead of editing the wrong place. "Create" / "Overwrite" blocks are complete files.
- **Test command:** `python3 -m unittest discover -s tools -p 'test_*.py' -v`. Baseline on `4ba20c6`: `Ran 80 tests … FAILED (errors=14)` — the 14 errors are `test_instantly_*` (gitignored media missing). Every "expected" count below includes those 14 errors and nothing else failing.
- **Git:** branch `tools-v1`. Before starting, run `git status` and `git pull` (CLAUDE.md sync rule; this branch has no upstream yet, so `git fetch origin` and report whether `main` moved). One commit per task, staging only the files the task names. Every commit message ends with the trailer `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Never push unless Tymek asks.

**Decisions this plan makes beyond the spec — flag to Tymek at review:**
1. **Tool names use underscores** (`tools/sync_lib.py`, `new_video.py`, `probe_cuts.py`, `cadence_scan.py`, `scan_flicker.py`, `slice.py`, `qa.py`, `preview_pack.py`): the spec's hyphenated names cannot be imported by the tests or by `qa.py`.
2. **`lib/manifest.json` is the one module list.** `modules` is what `sync_lib` copies and `lib.lock` hashes (sha256), and what the hygiene test asserts; `loadOrder` is the `<script>` order `new_video` writes. `lib/test/`, `lib/examples/` and `lib/README.md` are neither synced nor hashed. `sync_lib` never deletes; a stray file in a project's `lib/` fails check 2.
3. **The runtime view comes from `npx hyperframes preview --background`** (its studio serves the bundled composition with the runtime injected at `/api/projects/<name>/preview`) driven by chrome-headless-shell over CDP — chosen over `hyperframes snapshot` (pixels only, no DOM or timelines) and over a home-made static server (would not mount sub-compositions or nest timelines the way the runtime does). That URL is a studio-internal route; if a HyperFrames upgrade moves it, `qa.py --probe-url` and `HF_CLI` (pin a version) are the escape hatches.
4. **Density counting:** over-footage layouts leave the face on screen, so they count toward the 30 s body cadence but not toward the hook's 60 % or its 6 s face gaps. Post-render density (`--edit`) classifies frames by distance from the median frame (5 fps, 32×18 luma, Otsu threshold, floor 12); `--face-ref T` / `--threshold D` override when graphics dominate an edit.
5. **Check 9 "still" = every frame step in the last 0.3 s ≤ 1.5 mean |Δluma| (0–255, at 320×180)**, so hold creep passes; Shorts scenes are measured in the 0.3 s before their 0.36 s wipe-out. Tune `SETTLE_MAX` after the Plan 5 pilot.
6. **Flicker scan ignores intended cuts** (long-form slot boundaries; Shorts storyboard in/out times and the render's own scene cuts > 0.20). Blind spot: a one-frame full-screen flash exactly on a cut.
7. **Waiver syntax for exceptions:** `check <n>: <reason>` waives check n; `check <n> [<text>]: <reason>` waives only check-n findings containing `<text>`; every other entry (e.g. `F09: …`) is listed in the pack, not applied.
8. **Check 3 also verifies** that `compositions/brand.css` equals `node lib/brand.js` output for the BRIEF's palette/font/overrides and that the root's `data-hf-mode` matches the palette mode (`new_video` writes both), and rejects unknown BRIEF fields (typo guard). The BRIEF's YAML lives in one fenced block, parsed by a standard-library subset parser (colours must be quoted: a bare `#` starts a comment, as in YAML).
9. **Caption layer** (check 7) = an element whose id/class contains the word `caption(s)`, a `data-captions` attribute, or a beat-grid row of type `captions`.
10. **Over-footage layouts are standalone documents** in `compositions/overlays/` (HyperFrames `render -c` cannot render a `<template>` sub-composition alone — verified while prototyping); `slice` pairs them with over-footage rows in file-name order, checks ProRes 4444 + alpha, and replaces its own old `scene-*` / `overlay-*` files in `deliver/`.
11. **`qa.py` renders a draft itself** (`npx hyperframes render -q draft` → `renders/qa-draft.mp4`) unless given `--render`; `--skip-render` reports checks 9–10 as SKIP, which fails the gate. `qa-report.json` and the preview pack live in `renders/` (already gitignored).
12. **`scan_flicker` keeps video 09's thresholds but computes frame differences with ffmpeg** (`tblend` + `signalstats`) instead of numpy.

## Review Focus

1. **Values exactly on a density boundary** — a hook of exactly 60 %, a face gap of exactly 6 s, a body gap of exactly 30 s, a Short at exactly 35 % or 55 %, built from summed float intervals (`10 × 4.8 s` sums to 47.999…). Expected: PASS (the profiles say ≥ and ≤). Found while prototyping. Tests: Task 7 `test_long_form_hook_share_boundary`, `test_long_form_hook_face_gap_boundary`, `test_body_cadence_boundary_and_tail`, `test_shorts_band_edges`.
2. **An intended hard cut read as render flicker** — the cut between two reel scenes, or a jump cut in Shorts footage, is a single huge frame step exactly like a glitch. Expected: cuts are ignored, a one-frame glitch inside a scene is still reported. Tests: Task 6 `test_one_frame_glitch_is_reported`, Task 10 `test_check_10_flicker_but_not_the_scene_cut`.
3. **Motion-law violations that exist only at runtime** — a blur that appears mid-timeline on an untagged element, a reason set by `setAttribute`, a tween with no ease (GSAP falls back to `power1.out`), an ease inherited from timeline `defaults`. Expected: the gate sees them in the live page, and lib's own runtime tags pass. Tests: Task 9 `test_blur_reasons_seen_at_runtime`, `test_eases`; Task 10 `test_runtime_findings_merge_into_their_checks`, `test_probe_failure_fails_5_6_10`.
4. **A BRIEF or brand the gate cannot honour** — a typo'd field (`palete:`), an unquoted colour (`accentScript: #BACE7A` is a YAML comment), a missing brand folder, malformed `tokens.json` or palette JSON, a draft brand. Expected: a named error in check 3, never a traceback or a silent default. Tests: Task 4 `test_unknown_field_catches_typos`, `test_unquoted_colour_is_a_comment_and_a_named_error`, `test_missing_brand_folder_is_a_named_error`, `test_malformed_tokens_is_a_named_error`, `test_malformed_palette_is_a_named_error`, `test_draft_brand_fails_check_3`.
5. **Alpha deliverables** — an over-footage MOV that is ProRes 422 (no alpha), and a 4444 overlay whose transparency is dropped (black) or never composited in the contact sheet. Expected: `slice` refuses non-4444/no-alpha files by name; the preview pack shows the layout over a grey backdrop. Found while prototyping (the first contact sheet lost its overlay tile). Tests: Task 6 `test_extract_frame_flattens_alpha_over_a_backdrop`, Task 8 `test_overlay_must_be_prores_4444_alpha`, Task 11 `test_pack_contents`.

---

## File Structure

```
lib/manifest.json            NEW  the module list: modules (synced + hashed) and loadOrder
lib/test/drift.test.js       NEW  HFProfile TIMING + HFMotionBlur shutters vs the profile markdown
lib/test/hygiene.test.js     MODIFY (Task 1) → REWRITE (Task 3): manifest + tools/lawscan.js
lib/test/profile.test.js     MODIFY  ease-row parser fails clearly; handoff assertion
lib/test/wipe.test.js        MODIFY  phase handoff from timing.wipe.handoff
lib/profile.js               MODIFY  timing("shorts").wipe.handoff = 0.10
lib/shorts/wipe.js           MODIFY  phase() uses W.handoff
tools/sync_lib.py            NEW  sync root lib/ into a project + lib.lock; --check
tools/lawscan.js             NEW  core-law static scanner (rulesets lib | composition) + CLI
tools/lawscan.test.js        NEW  scanner fixtures (moved from hygiene + the closed gaps + HTML)
tools/brandcheck.py          MODIFY  named errors for missing folder / malformed JSON; strict colours
tools/project.py             NEW  BRIEF YAML block, validate_brief (check 3), beat grid, slots, transcript
tools/new_video.py           NEW  scaffold videos/<slug>/
tools/media.py               NEW  ffmpeg/ffprobe helpers
tools/synth.py               NEW  lavfi test clips for the media tests
tools/probe_cuts.py          NEW  Shorts source cuts + scene ends
tools/scan_flicker.py        NEW  isolated-jump flicker detector (port of video 09)
tools/cadence_scan.py        NEW  density on the beat grid (plan) and on the edit (post-render)
tools/slice.py               NEW  long-form delivery: clips + TIMECODES.csv + README (port of slice.mjs)
tools/qa_probe.mjs           NEW  headless-Chrome runtime probe (checks 5, 6, 10)
tools/runtime_probe.py       NEW  preview lifecycle + Chrome discovery around qa_probe.mjs
tools/qa.py                  NEW  the gate: all ten checks, waivers, renders/qa-report.json
tools/preview_pack.py        NEW  renders/preview/index.html for sign-off
tools/test_*.py              NEW  one per tool (sync_lib, project, new_video, media_tools, cadence_scan,
                                  slice, runtime_probe, qa, preview_pack)
tools/test_lib_node.py       MODIFY  also runs tools/*.test.js
tools/test_brandcheck.py, tools/test_standards_layout.py   MODIFY
CLAUDE.md, lib/README.md, standards/core/{qa,pipeline}.md, standards/formats/{long-form,shorts}.md,
roadmap                      MODIFY  "Plan 3" placeholders become the real commands
```

Run everything at any point with `python3 -m unittest discover -s tools -p 'test_*.py' -v` (it includes the node suites through `tools/test_lib_node.py`).

---

### Task 1: Lib manifest + `tools/sync_lib.py` (`lib.lock`, `--check`)

**Files:**
- Create: `lib/manifest.json`, `tools/sync_lib.py`, `tools/test_sync_lib.py`
- Modify: `lib/test/hygiene.test.js`, `CLAUDE.md`, `lib/README.md`, `standards/formats/shorts.md`

**Interfaces:**
- Consumes: root `lib/` modules from Plan 2 (`brand.js camera.js marks.js motion-blur.js profile.js shorts/wipe.js text.js`).
- Produces:
  - `lib/manifest.json` — `{"note", "modules": [...], "loadOrder": [...]}`.
  - `sync_lib.load_manifest(root=ROOT) -> {"modules": sorted list, "loadOrder": list}`; raises `ValueError` naming the file.
  - `sync_lib.file_hash(path) -> "sha256:<hex>"`; `sync_lib.build_lock(lib_dir, modules) -> {"source": "lib/", "files": {rel: hash}}`.
  - `sync_lib.sync(project, root=ROOT) -> lock dict` (writes `<project>/lib/<module>` + `<project>/lib.lock`; never deletes).
  - `sync_lib.check(project, root=ROOT) -> list[str]` (`[]` = exact locked copy) — QA check 2.
  - `sync_lib.LOCK_NAME = "lib.lock"`; CLI `python3 tools/sync_lib.py videos/<slug> [--check]` → exit 0 / 1 / 2.

- [ ] **Step 1: Write the failing test**

Create `tools/test_sync_lib.py`:

````python
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import sync_lib as sl

ROOT = Path(__file__).resolve().parents[1]


def make_root(base: Path) -> Path:
    root = base / "repo"
    (root / "lib" / "shorts").mkdir(parents=True)
    (root / "lib" / "a.js").write_text("var a = 1;\n")
    (root / "lib" / "shorts" / "w.js").write_text("var w = 2;\n")
    (root / "lib" / "README.md").write_text("docs stay in root\n")
    (root / "lib" / "manifest.json").write_text(json.dumps(
        {"modules": ["shorts/w.js", "a.js"], "loadOrder": ["a.js", "shorts/w.js"]}))
    return root


class ManifestTests(unittest.TestCase):
    def test_real_manifest_lists_existing_modules(self):
        m = sl.load_manifest(ROOT)
        self.assertIn("shorts/wipe.js", m["modules"])
        self.assertEqual(m["loadOrder"][0], "profile.js")
        for rel in m["modules"]:
            self.assertTrue((ROOT / "lib" / rel).is_file(), rel)

    def test_load_order_must_cover_modules(self):
        with tempfile.TemporaryDirectory() as t:
            root = make_root(Path(t))
            (root / "lib" / "manifest.json").write_text(json.dumps(
                {"modules": ["a.js", "shorts/w.js"], "loadOrder": ["a.js"]}))
            with self.assertRaisesRegex(ValueError, "loadOrder must list exactly the modules"):
                sl.load_manifest(root)

    def test_malformed_manifest_is_named(self):
        with tempfile.TemporaryDirectory() as t:
            root = make_root(Path(t))
            (root / "lib" / "manifest.json").write_text("{nope")
            with self.assertRaisesRegex(ValueError, "manifest.json is not valid JSON"):
                sl.load_manifest(root)


class SyncCheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.root = make_root(base)
        self.project = base / "videos" / "demo"
        self.project.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_sync_copies_only_modules_and_writes_lock(self):
        lock = sl.sync(self.project, self.root)
        self.assertEqual((self.project / "lib" / "shorts" / "w.js").read_text(), "var w = 2;\n")
        self.assertFalse((self.project / "lib" / "README.md").exists())
        self.assertFalse((self.project / "lib" / "manifest.json").exists())
        self.assertEqual(sorted(lock["files"]), ["a.js", "shorts/w.js"])
        self.assertTrue(lock["files"]["a.js"].startswith("sha256:"))
        on_disk = json.loads((self.project / "lib.lock").read_text())
        self.assertEqual(on_disk, lock)

    def test_check_clean_after_sync(self):
        sl.sync(self.project, self.root)
        self.assertEqual(sl.check(self.project, self.root), [])

    def test_check_catches_edited_copy(self):
        sl.sync(self.project, self.root)
        (self.project / "lib" / "a.js").write_text("var a = 99;\n")
        self.assertEqual(sl.check(self.project, self.root),
                         ["lib/a.js differs from root lib/a.js (edited copy?) — fix root lib/, then re-sync"])

    def test_check_catches_root_change_after_sync(self):
        sl.sync(self.project, self.root)
        (self.root / "lib" / "a.js").write_text("var a = 3;\n")
        problems = sl.check(self.project, self.root)
        self.assertIn("lib.lock: a.js is stale (root lib/a.js changed since the last sync) — re-run sync", problems)

    def test_check_catches_extra_file_and_sync_never_deletes_it(self):
        (self.project / "lib").mkdir()
        (self.project / "lib" / "house.js").write_text("// local fork\n")
        sl.sync(self.project, self.root)
        self.assertTrue((self.project / "lib" / "house.js").is_file())
        self.assertEqual(sl.check(self.project, self.root),
                         ["lib/house.js is not a root lib/ module (project code belongs in compositions/)"])

    def test_check_missing_and_malformed_lock(self):
        self.assertEqual(sl.check(self.project, self.root),
                         [f"lib.lock missing — run: python3 tools/sync_lib.py {self.project}"])
        (self.project / "lib.lock").write_text("not json")
        self.assertEqual(sl.check(self.project, self.root),
                         ['lib.lock is not valid (expected JSON with a "files" map) — re-run sync'])

    def test_check_catches_missing_copy(self):
        sl.sync(self.project, self.root)
        (self.project / "lib" / "shorts" / "w.js").unlink()
        self.assertEqual(sl.check(self.project, self.root),
                         ["lib/shorts/w.js is missing from the project — re-run sync"])

    def test_cli_exit_codes(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(sl.main(["sync_lib.py"]), 2)
            self.assertEqual(sl.main(["sync_lib.py", str(self.project), "--check"]), 1)
        self.assertIn("lib.lock missing", out.getvalue())


if __name__ == "__main__":
    unittest.main()
````

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 -m unittest discover -s tools -p 'test_sync_lib.py' -v`
Expected: ERROR — `ModuleNotFoundError: No module named 'sync_lib'`.

- [ ] **Step 3: Write the manifest and the tool**

Create `lib/manifest.json`:

````json
{
  "note": "Runtime modules of the shared library. tools/sync_lib.py copies exactly these into videos/<slug>/lib/ and pins them in lib.lock; test/, examples/ and README.md stay in root lib/. loadOrder is the <script> order (lib/README.md); shorts/ modules load in Shorts projects only.",
  "modules": ["brand.js", "camera.js", "marks.js", "motion-blur.js", "profile.js", "shorts/wipe.js", "text.js"],
  "loadOrder": ["profile.js", "motion-blur.js", "camera.js", "marks.js", "text.js", "brand.js", "shorts/wipe.js"]
}
````

Create `tools/sync_lib.py`:

````python
"""Copy the shared library into a video project and pin it with lib.lock (content hashes).

Spec section 8 (distribution) and standards/core/qa.md check 2. Projects never hand-copy lib/:
this tool copies exactly the modules listed in lib/manifest.json and records their hashes.

Usage:
  python3 tools/sync_lib.py videos/<slug>           copy root lib/ modules + write lib.lock
  python3 tools/sync_lib.py videos/<slug> --check   exit 1 (listing every problem) unless the
                                                    project's lib/ and lib.lock equal root lib/
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK_NAME = "lib.lock"
IGNORED = {".DS_Store"}


def load_manifest(root=ROOT) -> dict:
    """Return lib/manifest.json as {"modules": [...sorted], "loadOrder": [...]}; raise ValueError if malformed."""
    path = Path(root) / "lib" / "manifest.json"
    try:
        data = json.loads(path.read_text())
    except FileNotFoundError:
        raise ValueError(f"{path} not found")
    except json.JSONDecodeError as e:
        raise ValueError(f"{path} is not valid JSON ({e.msg} at line {e.lineno})")
    mods, order = data.get("modules"), data.get("loadOrder")
    for key, value in (("modules", mods), ("loadOrder", order)):
        if not isinstance(value, list) or not value or not all(isinstance(m, str) and m for m in value):
            raise ValueError(f"{path}: {key} must be a non-empty list of paths")
    if sorted(mods) != sorted(order) or len(set(mods)) != len(mods):
        raise ValueError(f"{path}: loadOrder must list exactly the modules, once each")
    return {"modules": sorted(mods), "loadOrder": list(order)}


def file_hash(path) -> str:
    return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_lock(lib_dir, modules) -> dict:
    return {"source": "lib/", "files": {m: file_hash(Path(lib_dir) / m) for m in sorted(modules)}}


def sync(project, root=ROOT) -> dict:
    """Copy every manifest module from root lib/ into <project>/lib/ and write <project>/lib.lock.

    Never deletes anything: a file in the project's lib/ that is not a manifest module stays put,
    and check() reports it.
    """
    project, root = Path(project), Path(root)
    modules = load_manifest(root)["modules"]
    src, dst = root / "lib", project / "lib"
    missing = [m for m in modules if not (src / m).is_file()]
    if missing:
        raise FileNotFoundError("root lib/ is missing manifest modules: " + ", ".join(missing))
    for m in modules:
        (dst / m).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src / m, dst / m)
    lock = build_lock(src, modules)
    (project / LOCK_NAME).write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n")
    return lock


def check(project, root=ROOT) -> list:
    """Problems that make the project's lib/ a fork of root lib/; [] means an exact, locked copy."""
    project, root = Path(project), Path(root)
    modules = load_manifest(root)["modules"]
    lock_path = project / LOCK_NAME
    if not lock_path.is_file():
        return [f"{LOCK_NAME} missing — run: python3 tools/sync_lib.py {project}"]
    try:
        locked = json.loads(lock_path.read_text())["files"]
        if not isinstance(locked, dict):
            raise TypeError
    except (ValueError, KeyError, TypeError):
        return [f"{LOCK_NAME} is not valid (expected JSON with a \"files\" map) — re-run sync"]
    want = build_lock(root / "lib", modules)["files"]
    problems = []
    for m in modules:
        if m not in locked:
            problems.append(f"{LOCK_NAME}: {m} is not locked — re-run sync")
        elif locked[m] != want[m]:
            problems.append(f"{LOCK_NAME}: {m} is stale (root lib/{m} changed since the last sync) — re-run sync")
        copy = project / "lib" / m
        if not copy.is_file():
            problems.append(f"lib/{m} is missing from the project — re-run sync")
        elif file_hash(copy) != want[m]:
            problems.append(f"lib/{m} differs from root lib/{m} (edited copy?) — fix root lib/, then re-sync")
    for m in sorted(set(locked) - set(modules)):
        problems.append(f"{LOCK_NAME}: {m} is not a root lib/ module")
    lib_dir = project / "lib"
    if lib_dir.is_dir():
        for p in sorted(lib_dir.rglob("*")):
            rel = p.relative_to(lib_dir).as_posix()
            if p.is_file() and p.name not in IGNORED and rel not in modules:
                problems.append(f"lib/{rel} is not a root lib/ module (project code belongs in compositions/)")
    return problems


def main(argv) -> int:
    args = [a for a in argv[1:] if a != "--check"]
    if len(args) != 1:
        print("usage: python3 tools/sync_lib.py videos/<slug> [--check]")
        return 2
    project = Path(args[0])
    if not project.is_dir():
        print(f"{project}: not a directory")
        return 2
    try:
        if "--check" in argv:
            problems = check(project)
            for p in problems:
                print(p)
            if problems:
                return 1
            print(f"OK {project}/lib matches root lib/ ({LOCK_NAME} current)")
            return 0
        lock = sync(project)
    except (ValueError, FileNotFoundError) as e:
        print(e)
        return 1
    print(f"synced {len(lock['files'])} modules into {project}/lib + {LOCK_NAME}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
````

- [ ] **Step 4: Point the hygiene test at the manifest**

Run from the repo root (each replacement asserts its target appears exactly once):

````bash
python3 - . <<'PY'
import sys
from pathlib import Path
ROOT = Path(sys.argv[1])

def edit(rel, pairs):
    p = ROOT / rel
    s = p.read_text()
    for a, b in pairs:
        assert s.count(a) == 1, (rel, a[:70])
        s = s.replace(a, b)
    p.write_text(s)

edit("lib/test/hygiene.test.js", [
("""var EXPECTED = ["brand.js", "camera.js", "marks.js", "motion-blur.js", "profile.js", "shorts/wipe.js", "text.js"];""",
 """// The one machine-readable list of runtime modules — also what tools/sync_lib.py copies and locks.
var EXPECTED = require("../manifest.json").modules.slice().sort();"""),
("""else if (d.name.endsWith(".js")) out.push""",
 'else if (/\\.[cm]?js$/.test(d.name)) out.push'),
('''test("lib/ holds exactly the Plan 2 modules (retired files stay retired)"''',
 '''test("lib/ holds exactly the manifest modules (retired files stay retired)"'''),
])
PY
````

- [ ] **Step 5: Run the tests**

Run: `python3 -m unittest discover -s tools -p 'test_sync_lib.py' -v`
Expected: `Ran 11 tests … OK`.
Run: `node --test lib/test/*.test.js`
Expected: `# pass 76`, `# fail 0`.

- [ ] **Step 6: Replace the "until sync-lib exists" placeholders**

````bash
python3 - . <<'PY'
import sys
from pathlib import Path
ROOT = Path(sys.argv[1])

def edit(rel, pairs):
    p = ROOT / rel
    s = p.read_text()
    for a, b in pairs:
        assert s.count(a) == 1, (rel, a[:70])
        s = s.replace(a, b)
    p.write_text(s)

edit("CLAUDE.md", [
("""improvements go into root `lib/` first. Until `tools/sync-lib` exists (Plan 3), copy the needed root
`lib/` files into the project unmodified.""",
 """improvements go into root `lib/` first, then re-sync. `python3 tools/sync_lib.py videos/<slug>` copies the
modules listed in `lib/manifest.json` and writes `lib.lock`; `--check` fails on any drift."""),
])
edit("lib/README.md", [
("""Projects never hand-copy or edit these: until `tools/sync-lib` exists (Plan 3), copy the files you
need from root `lib/` unmodified. Improvements go into root `lib/` first.""",
 """Projects never hand-copy or edit these. `python3 tools/sync_lib.py videos/<slug>` copies the modules
listed in `lib/manifest.json` (the one machine-readable module list; `loadOrder` is the order above)
into `videos/<slug>/lib/` and writes `lib.lock` (sha256 per module); `--check` exits 1 on an edited
copy, a stale lock or a stray file. `test/`, `examples/` and this README are not synced. Improvements
go into root `lib/` first, then re-sync."""),
])
edit("standards/formats/shorts.md", [
("""(`tools/sync-lib`; never hand-copy or edit the copy)""",
 """(`python3 tools/sync_lib.py videos/<slug>`; never hand-copy or edit the copy)"""),
])
PY
````

Run: `python3 -m unittest discover -s tools -p 'test_*.py'`
Expected: `Ran 91 tests … FAILED (errors=14)` — only `test_instantly_*`.

- [ ] **Step 7: Commit**

```bash
git add lib/manifest.json tools/sync_lib.py tools/test_sync_lib.py lib/test/hygiene.test.js CLAUDE.md lib/README.md standards/formats/shorts.md
git commit -m "feat(tools): lib manifest + sync_lib with lib.lock hashes and --check

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Profile drift guards + the wipe handoff in `timing.wipe`

The roadmap asks for these before any tool consumes profile values: a test that fails when `HFProfile` timings or `HFMotionBlur` shutters drift from the profile markdown, the wipe's literal `0.10` s handoff moved into `timing("shorts").wipe.handoff` (and written into `shorts.md`), and an ease-row parser that fails with a message instead of a `TypeError`.

**Files:**
- Create: `lib/test/drift.test.js`
- Modify: `lib/test/profile.test.js`, `lib/test/wipe.test.js`, `lib/profile.js`, `lib/shorts/wipe.js`, `standards/formats/shorts.md`

**Interfaces:**
- Consumes: `HFProfile.timing(format)`, `HFMotionBlur.profilePreset(format, kind)`, `HFMotionBlur.PROFILE_PRESETS`.
- Produces: `HFProfile.timing("shorts").wipe.handoff === 0.10`; `HFWipe.phase` starts the incoming wipe at `T + handoff`; `shorts.md` wipe table row `| phase handoff | **0.10s** | … |`.

- [ ] **Step 1: Write the failing tests**

Create `lib/test/drift.test.js`:

````javascript
"use strict";
// Drift guards: HFProfile TIMING and HFMotionBlur PROFILE_PRESETS must say what the profile markdown says.
// When a profile value changes, change lib/ in the same commit — these tests name the value that drifted.
var test = require("node:test");
var assert = require("node:assert/strict");
var fs = require("node:fs");
var path = require("node:path");
var P = require("../profile.js");
var MB = require("../motion-blur.js");

var ROOT = path.resolve(__dirname, "..", "..");
var FILES = {
  "long-form.md": path.join(ROOT, "standards", "formats", "long-form.md"),
  "shorts.md": path.join(ROOT, "standards", "formats", "shorts.md"),
  "spec": path.join(ROOT, "docs", "superpowers", "specs", "2026-10-03-animation-workflow-design.md")
};
var cache = {};
function text(file) { return cache[file] || (cache[file] = fs.readFileSync(FILES[file], "utf8")); }

// The numbers captured by `re` in `file`; fails naming the pattern when the markdown no longer matches.
function nums(file, re) {
  var m = re.exec(text(file));
  assert.ok(m, file + " no longer matches " + re + " — update the profile and lib/ together");
  return m.slice(1).map(parseFloat);
}
function num(file, re) { return nums(file, re)[0]; }
function close(lib, md, what) { assert.ok(Math.abs(lib - md) < 1e-9, what + ": lib " + lib + " vs markdown " + md); }

test("long-form TIMING matches long-form.md (and the spec appendix for the script rate)", function () {
  var T = P.timing("long-form");
  close(T.words.dur, num("long-form.md", /\| word entrance \|[^|\n]*?, ([\d.]+) s `ease\.enter`/), "words.dur");
  close(T.words.riseFrac, num("long-form.md", /\| word entrance \| rise ≈ (\d+) % of frame height/) / 100, "words.riseFrac");
  var st = nums("long-form.md", /\| word entrance \|[^|\n]*stagger (\d+)–(\d+) ms/);
  close(T.words.staggerRange[0], st[0] / 1000, "words.staggerRange[0]");
  close(T.words.staggerRange[1], st[1] / 1000, "words.staggerRange[1]");
  assert.ok(T.words.stagger >= T.words.staggerRange[0] && T.words.stagger <= T.words.staggerRange[1], "words.stagger inside its range");
  close(T.glow.pop, num("long-form.md", /\| glow title \| pops to ≈ (\d+) % brightness/) / 100, "glow.pop");
  close(T.glow.settle, num("long-form.md", /\| glow title \|[^|\n]*settles ([\d.]+) s `ease\.glow`/), "glow.settle");
  close(T.glow.nextWord, num("long-form.md", /\| glow title \|[^|\n]*next word \+(\d+) ms/) / 1000, "glow.nextWord");
  var halo = nums("long-form.md", /\| glow title \|[^|\n]*halo (\d+)–(\d+) px at 1080p/);
  assert.ok(T.glow.haloFrac * 1080 >= halo[0] && T.glow.haloFrac * 1080 <= halo[1], "glow.haloFrac inside " + halo.join("–") + " px");
  close(T.defocus.sigmaFrac * 1080, num("long-form.md", /\| backdrop defocus \| blur σ ≈ ([\d.]+) px at 1080p/), "defocus.sigmaFrac");
  close(T.defocus.brightness, num("long-form.md", /\| backdrop defocus \|[^|\n]*brightness → ([\d.]+)/), "defocus.brightness");
  close(T.defocus.dur, num("long-form.md", /\| backdrop defocus \|[^|\n]*over ([\d.]+) s/), "defocus.dur");
  var sw = nums("long-form.md", /\| `ease\.sweep` \|[^|\n]*≈ (\d+) px\/s at (\d+)p \(([\d.]+) s short, ([\d.]+) s long/);
  close(T.sweep.pxPerSecPerH, sw[0] / sw[1], "sweep.pxPerSecPerH");
  close(T.sweep.min, sw[2], "sweep.min");
  close(T.sweep.max, sw[3], "sweep.max");
  close(T.scriptMsPerChar, num("spec", /Script word: ≈ (\d+) ms\/letter/), "scriptMsPerChar");
});

test("Shorts TIMING matches shorts.md", function () {
  var T = P.timing("shorts");
  close(T.typeOnMsPerChar, num("shorts.md", /≈ (\d+) ms\/char/), "typeOnMsPerChar");
  close(T.swap, num("shorts.md", /(\d+) ms — a hard global swap/) / 1000, "swap");
  close(T.words.stagger, num("shorts.md", /~(\d+) ms per word/) / 1000, "words.stagger");
  close(T.chip.expand, num("shorts.md", /expands horizontally ~(\d+) ms/) / 1000, "chip.expand");
  close(T.wipe.inDur, num("shorts.md", /\| duration in \| \*\*([\d.]+)s\*\*/), "wipe.inDur");
  close(T.wipe.outDur, num("shorts.md", /\| duration out \| \*\*([\d.]+)s\*\*/), "wipe.outDur");
  var blur = nums("shorts.md", /\| blur \| `(\d+)px` in \/ `(\d+)px` out/);
  close(T.wipe.blurIn, blur[0], "wipe.blurIn");
  close(T.wipe.blurOut, blur[1], "wipe.blurOut");
  var fe = nums("shorts.md", /\| mask feather \| `(\d+) \+ (\d+) · 4q\(1-q\)`/);
  close(T.wipe.featherMin, fe[0], "wipe.featherMin");
  close(T.wipe.featherGain, fe[1], "wipe.featherGain");
  close(T.wipe.handoff, num("shorts.md", /\| phase handoff \| \*\*([\d.]+)s\*\*/), "wipe.handoff");
});

test("motion-blur shutters match both profiles (and Shorts has no whip)", function () {
  function angle(format, kind) { return MB.profilePreset(format, kind).angle; }
  close(angle("long-form", "leg"), num("long-form.md", /ordinary legs (\d+)°/), "long-form leg");
  close(angle("long-form", "whip"), num("long-form.md", /whips (\d+)°/), "long-form whip");
  close(angle("long-form", "roll"), num("long-form.md", /odometer digit roll (\d+)°/), "long-form roll");
  close(angle("shorts", "leg"), num("shorts.md", /camera legs (\d+)°/), "shorts leg");
  close(angle("shorts", "roll"), num("shorts.md", /odometer digit roll (\d+)°/), "shorts roll");
  assert.match(text("shorts.md"), /Shorts have no whips/);
  assert.deepEqual(Object.keys(MB.PROFILE_PRESETS.shorts).sort(), ["leg", "roll"]);
  assert.deepEqual(Object.keys(MB.PROFILE_PRESETS["long-form"]).sort(), ["leg", "roll", "whip"]);
});
````

Update the profile and wipe tests:

````bash
python3 - . <<'PY'
import sys
from pathlib import Path
ROOT = Path(sys.argv[1])

def edit(rel, pairs):
    p = ROOT / rel
    s = p.read_text()
    for a, b in pairs:
        assert s.count(a) == 1, (rel, a[:70])
        s = s.replace(a, b)
    p.write_text(s)

edit("lib/test/profile.test.js", [
('// Pull `| \\`ease.x\\` | <cell> |` rows out of a profile; the value is the cell\'s first backticked string.\nfunction tableEases(file) {\n  var text = fs.readFileSync(path.join(ROOT, "standards", "formats", file), "utf8"), out = {};\n  text.split("\\n").forEach(function (line) {\n    var m = /^\\| `(ease\\.[a-z.]+)` \\| ([^|]+)\\|/.exec(line);\n    if (!m) return;\n    var v = /`([^`]+)`/.exec(m[2]);\n    out[m[1]] = v[1];\n  });\n  return out;\n}\n',
 '// Pull `| \\`ease.x\\` | <cell> |` rows out of profile markdown; the value is the cell\'s first backticked\n// string. A row whose value cell has no backticks fails with a message naming the file and token.\nfunction parseEaseRows(text, label) {\n  var out = {};\n  text.split("\\n").forEach(function (line) {\n    var m = /^\\| `(ease\\.[a-z.]+)` \\| ([^|]+)\\|/.exec(line);\n    if (!m) return;\n    var v = /`([^`]+)`/.exec(m[2]);\n    assert.ok(v, label + ": the value cell of " + m[1] + " must contain a backticked spec, got: " + m[2].trim());\n    out[m[1]] = v[1];\n  });\n  return out;\n}\nfunction tableEases(file) {\n  return parseEaseRows(fs.readFileSync(path.join(ROOT, "standards", "formats", file), "utf8"), file);\n}\n\ntest("ease-row parser fails clearly on a value cell without backticks", function () {\n  assert.deepEqual(parseEaseRows("| `ease.enter` | `power3.out` |", "x.md"), { "ease.enter": "power3.out" });\n  assert.throws(function () { parseEaseRows("| `ease.enter` | power3.out |", "x.md"); },\n    /x\\.md: the value cell of ease\\.enter must contain a backticked spec, got: power3\\.out/);\n});\n'),
("""  assert.equal(P.timing("shorts").wipe.inDur, 0.42);
""",
 """  assert.equal(P.timing("shorts").wipe.inDur, 0.42);
  assert.equal(P.timing("shorts").wipe.handoff, 0.10);
"""),
])
edit("lib/test/wipe.test.js", [
("""test("phase: outgoing wipes out at T, incoming wipes in at T + 0.10", function () {""",
 """test("phase: outgoing wipes out at T, incoming wipes in at T + timing.wipe.handoff (0.10)", function () {"""),
("""assert.equal(d[0].at, 4); assert.equal(d[1].at, 4.1);""",
 """assert.equal(d[0].at, 4); assert.equal(d[1].at, 4 + P.timing("shorts").wipe.handoff);"""),
])
PY
````

- [ ] **Step 2: Run them to verify they fail**

Run: `node --test lib/test/*.test.js`
Expected: 3 failures — `Shorts TIMING matches shorts.md` (`shorts.md no longer matches /\| phase handoff …/`), `timing() returns a copy callers cannot mutate` (`undefined !== 0.1`), `phase: outgoing wipes out at T, incoming …` (`4.1 !== NaN`).

- [ ] **Step 3: Implement**

````bash
python3 - . <<'PY'
import sys
from pathlib import Path
ROOT = Path(sys.argv[1])

def edit(rel, pairs):
    p = ROOT / rel
    s = p.read_text()
    for a, b in pairs:
        assert s.count(a) == 1, (rel, a[:70])
        s = s.replace(a, b)
    p.write_text(s)

edit("lib/profile.js", [
("""wipe: { inDur: 0.42, outDur: 0.36, blurIn: 14, blurOut: 12, featherMin: 8, featherGain: 34 }""",
 """wipe: { inDur: 0.42, outDur: 0.36, blurIn: 14, blurOut: 12, featherMin: 8, featherGain: 34, handoff: 0.10 }"""),
])
edit("lib/shorts/wipe.js", [
("""// Phase handoff inside one scene: A wipes out while B wipes in 0.10 s later along the same axis.""",
 """// Phase handoff inside one scene: A wipes out while B wipes in timing.wipe.handoff (0.10 s) later along the same axis."""),
("""inAt: T + 0.10 });""",
 """inAt: T + W.handoff });"""),
])
edit("standards/formats/shorts.md", [
("""| mask feather | `8 + 34 · 4q(1-q)` (%) | softest while moving fastest, tight at rest |
""",
 """| mask feather | `8 + 34 · 4q(1-q)` (%) | softest while moving fastest, tight at rest |
| phase handoff | **0.10s** | inside one scene, the incoming phase starts its wipe-in 0.10 s after the outgoing phase starts its wipe-out (`HFWipe.phase`) |
"""),
])
PY
````

- [ ] **Step 4: Run the tests**

Run: `node --test lib/test/*.test.js`
Expected: `# pass 80`, `# fail 0`.
Mutation check (proves the guard bites):
`sed -i.bak 's/typeOnMsPerChar: 67/typeOnMsPerChar: 70/' lib/profile.js && node --test lib/test/drift.test.js; mv lib/profile.js.bak lib/profile.js`
Expected: one failure, `typeOnMsPerChar: lib 70 vs markdown 67`; the `mv` restores the file (re-run the suite: `# fail 0`).

- [ ] **Step 5: Commit**

```bash
git add lib/test/drift.test.js lib/test/profile.test.js lib/test/wipe.test.js lib/profile.js lib/shorts/wipe.js standards/formats/shorts.md
git commit -m "test(lib): timing and shutter drift guards; wipe handoff into timing.wipe

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Shared scanner `tools/lawscan.js`

Extract `lex`/`scan` from `lib/test/hygiene.test.js` into one module both the library test (ruleset `lib`) and QA checks 4–6 (ruleset `composition`) use, and close the gaps the Plan 2 review listed: quoted / template-literal eases and repeats, `color-mix`/`lab`/`lch`/`oklab`, `url(#…)` and DOM `.blur()` false positives, `.mjs`/`.cjs` modules, and a regex literal after `return`. Compositions are HTML, so prose between tags is masked first (an apostrophe in copy must not open a string), and blur-reason values and directional Gaussians are checked per format.

**Files:**
- Create: `tools/lawscan.js`, `tools/lawscan.test.js`
- Rewrite: `lib/test/hygiene.test.js`, `tools/test_lib_node.py`
- Modify: `lib/README.md`, `CLAUDE.md`

**Interfaces:**
- Consumes: `lib/manifest.json` `modules` (Task 1).
- Produces:
  - `lawscan.scan(rel, raw, {ruleset: "lib" | "composition", format: "long-form" | "shorts"}) -> [{file, line, check, message}]` — `check` is the `qa.md` check number (4, 5, 6; `0` for the lib-only colour rule).
  - `lawscan.lex(raw) -> {src, marks}`, `lawscan.htmlMask(raw) -> string`, `lawscan.format(finding) -> "file:line: message"`, `lawscan.REASONS = ["focus", "glow", "wipe"]`.
  - CLI `node tools/lawscan.js [--ruleset lib|composition] [--format long-form|shorts] FILE...` → JSON array on stdout; exit 0 (clean), 1 (findings), 2 (usage / bad format).

- [ ] **Step 1: Write the failing test**

Create `tools/lawscan.test.js`:

````javascript
"use strict";
// Fixtures for tools/lawscan.js — run by tools/test_lib_node.py with the lib/ node suite.
var test = require("node:test");
var assert = require("node:assert/strict");
var L = require("./lawscan.js");

function hits(src) { return L.scan("x.js", src, { ruleset: "lib" }).length; }
function comp(src, format, rel) { return L.scan(rel || "c.html", src, { ruleset: "composition", format: format || "long-form" }); }

test("lib ruleset: catches what its messages claim (fixtures carried from hygiene.test.js)", function () {
  ["a = '#fff';", "a = '#FFFA';", "a = '#12345678';", "a = 'rgba(1,2,3,1)';", "a = 'RGB(1,2,3)';", "a = 'hsl(1,2%,3%)';", "a = 'oklch(1 0 0)';", "a = 'hwb(1 2% 3%)';"]
    .forEach(function (s) { assert.equal(hits(s), 1, s); });
  assert.equal(hits("a = 'rgba(0,0,0,0)'; /* hf-allow: alpha-mask */"), 0);
  assert.equal(hits("a = '#000'; // plain"), 1);
  assert.equal(hits("a = 'rgba(0,0,0,0)'; /* hf-allow: alpha-mask */\nb = '#fff';"), 1);
  assert.equal(hits("a = 'url(#glow-x)'; id = '#glow-x';"), 0);
  ["{ ease: 'back.out(1.7)' }", "{ ease: \"power2.out\" }", "x = Elastic.easeOut", "x = 'bounce.inOut'", "x = Back.easeIn", "{ repeat: Infinity }", "{ repeat: -1 }"]
    .forEach(function (s) { assert.ok(hits(s) >= 1, s); });
  assert.equal(hits("{ ease: 'none' }"), 0);
  assert.equal(hits("{ ease: \"none\" }"), 0);
  assert.equal(hits("// back.out is forbidden\n/* repeat: -1 */"), 0);
  var tagged = "el.setAttribute('data-blur-reason','focus'); el.style.filter = 'blur(2px)';";
  assert.equal(hits(tagged), 0);
  assert.equal(hits(tagged + "\n\n\n\n\nel.style.filter = 'blur(9px)';"), 1);
  assert.equal(hits("a = '<feGaussianBlur in=\"x\"/>';"), 1);
  assert.equal(hits("a = '<feGaussianBlur data-blur-reason=\"glow\"/>';"), 0);
  assert.equal(hits("s.backdropFilter = 'x'; css = 'backdrop-filter: blur(4px)';"), 3);
  assert.equal(hits("a = '#ff0000'; /* hf-allow: alpha-mask */"), 1);
  assert.equal(hits("a = '#000 #f00'; /* hf-allow: alpha-mask */"), 1);
  assert.equal(hits("a = 'rgba(0, 0, 0, .4)'; /* hf-allow: alpha-mask */"), 0);
  assert.equal(hits("a = 'rgb( 0 , 0 , 0 ) #00000000 #0000 #000000'; /* hf-allow: alpha-mask */"), 0);
  assert.equal(hits("a = 'rgba(0,0,0,0)'; b = 'rgba(1,0,0,1)'; /* hf-allow: alpha-mask */"), 1);
  assert.equal(hits("a = '#000 /* hf-allow: alpha-mask */';"), 1);
  assert.equal(hits("a = /\"/g; b = '#fff';"), 1);
  assert.equal(hits("a = 'blur(1px)'; b = 'blur(2px)'; x.setAttribute('data-blur-reason','focus');"), 1);
  assert.equal(hits("x.setAttribute('data-blur-reason','focus');\na = 'blur(1px)';"), 0);
  assert.equal(hits("x.setAttribute('data-blur-reason','focus');\na = 'blur(1px)';\nb = 'blur(2px)';"), 1);
  assert.equal(hits("t(x, 'data-blur-reason');\na = 'blur(1px)';\n\nb = 'blur(2px)';"), 1);
  assert.equal(hits("a = 'blur(1px)';\nx.setAttribute('data-blur-reason','focus');"), 1);
  assert.equal(hits("el.style.backdropFilter = 'x';"), 1);
  assert.equal(L.format(L.scan("x.js", "\n\nb = 'blur(1px)';")[0]).indexOf("x.js:3:"), 0);
});

test("known gaps from the Plan 2 review are closed", function () {
  // quoted keys and template-literal eases
  assert.equal(hits("{ ease: `power2.out` }"), 1);
  assert.equal(hits("{ \"ease\": \"power2.out\" }"), 1);
  assert.equal(hits("{ 'repeat': -1 }"), 1);
  // modern colour functions
  ["a = 'color-mix(in srgb, red, blue)';", "a = 'lab(50% 40 59)';", "a = 'lch(52% 72 50)';", "a = 'oklab(0.5 0.1 0.1)';"]
    .forEach(function (s) { assert.equal(hits(s), 1, s); });
  assert.equal(hits("label(x); vocab(y);"), 0);
  // url(#id) and DOM .blur() are not colours / Gaussians
  assert.equal(hits("f.style.filter = 'url(#fade)'; g = 'url(#beef)';"), 0);
  assert.equal(hits("input.blur(); el.blur();"), 0);
  // a regex literal after `return` (and other keywords) is not division: the quote inside is not a string
  assert.equal(hits("function f(){ return /\"/g; } // back.out is banned"), 0);
  assert.equal(hits("x = typeof /'/; // repeat: -1"), 0);
});

test("composition ruleset: HTML prose is masked, line numbers survive", function () {
  assert.deepEqual(comp("<p>it's a \"test\"</p><script>var t = Date.now();</script>").map(function (f) { return [f.line, f.check]; }), [[1, 4]]);
  assert.deepEqual(comp("<p>don't</p>\n<script>\nvar x = 1;\n</script>\n<style>.a{animation: spin 2s infinite linear}</style>").map(function (f) { return [f.line, f.check]; }), [[5, 4]]);
  assert.deepEqual(comp("<!-- Math.random() is banned -->\n<style>.a { color: #fff }</style>"), []);
  assert.equal(comp("\n\n<script>Math.random()</script>")[0].line, 3);
  assert.deepEqual(comp("<script>tl.to(el, { x: 10, ease: \"power2.out\" });</script>").map(function (f) { return f.check; }), [6]);
  assert.deepEqual(comp("<style>.a { transition: transform 1s cubic-bezier(0.2, 0, 0, 1) }</style>").map(function (f) { return f.check; }), [6]);
});

test("composition ruleset: blur reasons are checked per format", function () {
  assert.deepEqual(comp("<filter><feGaussianBlur stdDeviation=\"4\"/></filter>").map(function (f) { return f.check; }), [5]);
  assert.deepEqual(comp("<feGaussianBlur data-blur-reason=\"glow\" stdDeviation=\"4\"/>"), []);
  assert.deepEqual(comp("<feGaussianBlur\n  data-blur-reason=\"focus\" stdDeviation=\"4\"/>"), [], "tag on the next line of a multi-line SVG tag");
  assert.deepEqual(comp("<div style=\"filter: blur(4px)\" data-blur-reason=\"focus\"></div>"), []);
  var lf = comp("<feGaussianBlur data-blur-reason=\"wipe\" stdDeviation=\"14 0\"/>", "long-form").map(function (f) { return f.message; });
  assert.equal(lf.length, 2);
  assert.match(lf[0], /"wipe" is Shorts-only/);
  assert.match(lf[1], /directional Gaussian/);
  assert.deepEqual(comp("<feGaussianBlur data-blur-reason=\"wipe\" stdDeviation=\"14 0\"/>", "shorts"), []);
  assert.match(comp("<feGaussianBlur data-blur-reason=\"smear\" stdDeviation=\"3\"/>")[0].message, /"smear" is not focus, glow or wipe/);
  assert.match(comp("<script>fe.setAttribute(\"data-blur-reason\", \"haze\"); fe.setAttribute('stdDeviation', 3);</script>")[0].message, /"haze"/);
  assert.deepEqual(comp("<style>.a{color:#fff;background:rgba(1,2,3,1)}</style>"), [], "colours are a lib rule, not a QA check");
  assert.throws(function () { comp("<p></p>", "tiktok"); }, /format must be long-form or shorts/);
});

test("cli: JSON out, exit 1 on findings, 2 on bad usage", function () {
  var fs = require("fs"), os = require("os"), path = require("path");
  var dir = fs.mkdtempSync(path.join(os.tmpdir(), "lawscan-")), f = path.join(dir, "a.html");
  fs.writeFileSync(f, "<script>Math.random()</script>");
  var out = "", err = "";
  var io = { out: function (s) { out += s; }, err: function (s) { err += s; } };
  assert.equal(L.cli(["--ruleset", "composition", "--format", "shorts", f], io), 1);
  assert.equal(JSON.parse(out)[0].check, 4);
  assert.equal(L.cli([], io), 2);
  assert.match(err, /usage/);
  fs.rmSync(dir, { recursive: true });
});
````

- [ ] **Step 2: Run it to verify it fails**

Run: `node --test tools/lawscan.test.js`
Expected: FAIL — `Cannot find module './lawscan.js'`.

- [ ] **Step 3: Write the scanner**

Create `tools/lawscan.js`:

````javascript
"use strict";
/* lawscan — the core-motion-law static scanner, shared by lib/test/hygiene.test.js (ruleset "lib")
 * and tools/qa.py (ruleset "composition", QA checks 4, 5 and 6). Node built-ins only.
 *
 *   node tools/lawscan.js [--ruleset lib|composition] [--format long-form|shorts] FILE...
 *   → prints a JSON array of findings {file, line, check, message}; exit 1 if any.
 *
 * Static scanning cannot see what a script decides at runtime (a blur reason set with a computed
 * value, an ease picked from a variable). tools/qa_probe.mjs covers those in the rendered DOM.
 */
var fs = require("fs");

var MARKER = /^\/\*\s*hf-allow:\s*alpha-mask\s*\*\/$/;
var REASONS = ["focus", "glow", "wipe"];

// [pattern, check number, message, rulesets]. Check numbers follow standards/core/qa.md §1.
var RULES = [
  [/Math\.random|Date\.now|performance\.now/, 4, "non-deterministic clock/randomness (core law 1)", "lib composition"],
  [/["'`]?repeat["'`]?\s*:\s*(-1|Infinity)/, 4, "infinite repeat (core law 1)", "lib composition"],
  [/animation(?:-iteration-count)?\s*:[^;{}"'`]*\binfinite\b/i, 4, "CSS infinite animation (core law 1)", "lib composition"],
  [/(?<!url\()#(?:[0-9a-f]{3,4}|[0-9a-f]{6}|[0-9a-f]{8})(?![0-9a-z_-])/i, 0, "hard-coded colour — use brand CSS variables", "lib"],
  [/\b(rgba?|hsla?|oklch|oklab|lab|lch|hwb|color-mix)\(/i, 0, "hard-coded colour function — use brand CSS variables", "lib"],
  [/\b(back|elastic|bounce)\.(in|out|inout|ease\w*)/i, 6, "overshoot ease (core law 3)", "lib composition"],
  [/["'`]?\bease["'`]?\s*:\s*["'`](?!none["'`])/, 6, "string ease other than the driver's \"none\" — use HFProfile.ease (core law 4)", "lib composition"]
];
// Only pure black is excusable on an alpha-mask line: #000 #0000 #000000 #00000000, rgb(0,0,0), rgba(0,0,0,<alpha>).
var BLACK = /#(?:0{3,4}|0{6}|0{8})(?![0-9a-z])|\brgba?\(\s*0\s*,\s*0\s*,\s*0\s*(?:,\s*[0-9.]+\s*)?\)/gi;
// A `/` after one of these keywords starts a regex literal, not a division.
var REGEX_KEYWORD = /(?:^|[^\w$.])(?:return|typeof|case|do|else|in|of|void|yield|await|delete|throw|new)\s*$/;

// Walk JS/CSS source tracking string state, so `/*` inside a string is not a comment.
// Returns the source with comments blanked (newlines kept) and the 0-based lines of real alpha-mask markers.
function lex(raw) {
  var out = "", marks = {}, i = 0, n = raw.length, q = null, line = 0;
  while (i < n) {
    var c = raw[i], d = raw[i + 1];
    if (q) {
      out += c; if (c === "\n") line++;
      if (c === "\\") { out += d || ""; if (d === "\n") line++; i += 2; continue; }
      if (c === q) q = null;
      i++; continue;
    }
    if (c === "'" || c === '"' || c === "`") { q = c; out += c; i++; continue; }
    if (c === "/" && d === "*") {
      var end = raw.indexOf("*/", i + 2); end = end === -1 ? n : end + 2;
      var text = raw.slice(i, end);
      if (MARKER.test(text)) marks[line] = true;
      out += text.replace(/[^\n]/g, " "); line += (text.match(/\n/g) || []).length; i = end; continue;
    }
    if (c === "/" && d === "/") { while (i < n && raw[i] !== "\n") { out += " "; i++; } continue; }
    var before = out.slice(-40);
    if (c === "/" && (/[(,=:\[!&|?{};]\s*$|^\s*$/.test(before) || REGEX_KEYWORD.test(before))) {   // regex literal: skip it so a quote inside is not a string
      var j = i + 1, cls = false;
      while (j < n && raw[j] !== "\n" && (cls || raw[j] !== "/")) { if (raw[j] === "\\") j++; else if (raw[j] === "[") cls = true; else if (raw[j] === "]") cls = false; j++; }
      out += raw.slice(i, j + 1); i = j + 1; continue;
    }
    out += c; if (c === "\n") line++;
    i++;
  }
  return { src: out, marks: marks };
}

// HTML → the same text with HTML comments and the prose between tags blanked (newlines kept), so an
// apostrophe in copy never opens a "string". Tags, <script> and <style> bodies are kept verbatim.
function htmlMask(raw) {
  var re = /<!--[\s\S]*?(?:-->|$)|<(script|style)\b[^>]*>[\s\S]*?(?:<\/\1\s*>|$)|<[^>]*>?/gi, out = "", last = 0, m;
  function blank(s) { return s.replace(/[^\n]/g, " "); }
  while ((m = re.exec(raw))) {
    out += blank(raw.slice(last, m.index));
    out += m[0].indexOf("<!--") === 0 ? blank(m[0]) : m[0];
    last = re.lastIndex;
    if (m[0] === "") re.lastIndex++;
  }
  return out + blank(raw.slice(last));
}

function reasonsOn(line) {
  var out = [], re = /data-blur-reason\W{1,4}([A-Za-z]+)/g, m;
  while ((m = re.exec(line))) out.push(m[1]);
  return out;
}

/* Findings for one file. opts.ruleset: "lib" (default) or "composition"; opts.format: "long-form" |
 * "shorts" (composition only — decides whether a `wipe` reason / directional Gaussian is allowed).
 * Lib rule: a Gaussian site's data-blur-reason is on the same line or the line before. Composition:
 * also the line after (multi-line SVG tags), and literal reason values are checked. */
function scan(rel, raw, opts) {
  opts = opts || {};
  var ruleset = opts.ruleset || "lib", comp = ruleset === "composition", fmt = opts.format || "long-form";
  if (comp && fmt !== "long-form" && fmt !== "shorts") throw new Error("lawscan: format must be long-form or shorts, got " + JSON.stringify(fmt));
  var src = /\.html?$/i.test(rel) ? htmlMask(raw) : raw;
  var out = [], lx = lex(src), lines = lx.src.split("\n"), tagUsed = {};
  function hit(i, check, message) { out.push({ file: rel, line: i + 1, check: check, message: message }); }
  function free(i) { return i < 0 || i >= lines.length ? 0 : (lines[i].match(/data-blur-reason/g) || []).length - (tagUsed[i] || 0); }
  lines.forEach(function (line, i) {
    RULES.forEach(function (r) {
      if (r[3].split(" ").indexOf(ruleset) === -1) return;
      var l = r[1] === 0 && lx.marks[i] ? line.replace(BLACK, "") : line;
      if (r[0].test(l)) hit(i, r[1], r[2]);
    });
    if (rel !== "profile.js" && /cubic-bezier\(/.test(line)) hit(i, 6, "raw cubic-bezier outside profile.js (core law 4)");
    var sites = (line.match(/(^|[^A-Za-z.])blur\(|<feGaussianBlur|backdrop-filter|backdropFilter/g) || []).length;
    for (var s = 0; s < sites; s++) {
      var spot = [i - 1, i].concat(comp ? [i + 1] : []).filter(function (k) { return free(k) > 0; })[0];
      if (spot === undefined) hit(i, 5, "Gaussian site without its own data-blur-reason (same line or line before" + (comp ? " or after" : "") + ")");
      else tagUsed[spot] = (tagUsed[spot] || 0) + 1;
    }
    if (!comp) return;
    reasonsOn(line).forEach(function (r) {
      if (REASONS.indexOf(r) === -1) hit(i, 5, "data-blur-reason \"" + r + "\" is not focus, glow or wipe");
      else if (r === "wipe" && fmt !== "shorts") hit(i, 5, "data-blur-reason \"wipe\" is Shorts-only (wipe feather and element smear)");
    });
    var sd = /stdDeviation\s*=\s*["']\s*([\d.]+)[\s,]+([\d.]+)\s*["']/.exec(line);
    if (sd && fmt === "long-form" && parseFloat(sd[1]) !== parseFloat(sd[2])) {
      hit(i, 5, "directional Gaussian (stdDeviation \"" + sd[1] + " " + sd[2] + "\") is movement blur — use HFMotionBlur");
    }
  });
  return out;
}

function format(f) { return f.file + ":" + f.line + ": " + f.message; }

function cli(argv, io) {
  var opts = { ruleset: "lib" }, files = [];
  for (var i = 0; i < argv.length; i++) {
    if (argv[i] === "--ruleset") opts.ruleset = argv[++i];
    else if (argv[i] === "--format") opts.format = argv[++i];
    else files.push(argv[i]);
  }
  if (!files.length || ["lib", "composition"].indexOf(opts.ruleset) === -1) {
    io.err("usage: node tools/lawscan.js [--ruleset lib|composition] [--format long-form|shorts] FILE...\n");
    return 2;
  }
  var found = [];
  try {
    files.forEach(function (f) { found = found.concat(scan(f, fs.readFileSync(f, "utf8"), opts)); });
  } catch (e) { io.err(e.message + "\n"); return 2; }
  io.out(JSON.stringify(found, null, 1) + "\n");
  return found.length ? 1 : 0;
}

module.exports = { lex: lex, htmlMask: htmlMask, scan: scan, format: format, cli: cli, RULES: RULES, REASONS: REASONS };
if (require.main === module) {
  process.exitCode = cli(process.argv.slice(2), { out: function (s) { process.stdout.write(s); }, err: function (s) { process.stderr.write(s); } });
}
````

- [ ] **Step 4: Run the scanner tests**

Run: `node --test tools/lawscan.test.js`
Expected: `# pass 5`, `# fail 0`.

- [ ] **Step 5: Rewire the hygiene test and the node runner**

Overwrite `lib/test/hygiene.test.js` (the fixtures now live in `tools/lawscan.test.js`):

````javascript
"use strict";
// Static scan of every shared module: the core motion law, enforced on the library itself.
// The scanner lives in tools/lawscan.js (shared with the QA gate); its fixtures are tools/lawscan.test.js.
var test = require("node:test");
var assert = require("node:assert/strict");
var fs = require("node:fs");
var path = require("node:path");
var lawscan = require("../../tools/lawscan.js");

var LIB = path.resolve(__dirname, "..");
// The one machine-readable list of runtime modules — also what tools/sync_lib.py copies and locks.
var EXPECTED = require("../manifest.json").modules.slice().sort();

function modules() {
  var out = [];
  (function walk(dir) {
    fs.readdirSync(dir, { withFileTypes: true }).forEach(function (d) {
      var p = path.join(dir, d.name);
      if (d.isDirectory()) { if (d.name !== "test" && d.name !== "examples") walk(p); }
      else if (/\.[cm]?js$/.test(d.name)) out.push(path.relative(LIB, p).split(path.sep).join("/"));
    });
  })(LIB);
  return out.sort();
}

test("lib/ holds exactly the manifest modules (retired files stay retired)", function () {
  assert.deepEqual(modules(), EXPECTED);
});

test("no module breaks the motion law", function () {
  var problems = [];
  modules().forEach(function (rel) {
    problems = problems.concat(lawscan.scan(rel, fs.readFileSync(path.join(LIB, rel), "utf8"), { ruleset: "lib" }).map(lawscan.format));
  });
  assert.deepEqual(problems, []);
});
````

Overwrite `tools/test_lib_node.py`:

````python
"""Runs the lib/ and tools/ node test suites (node built-ins only) as part of the repo's unittest run."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which("node")


@unittest.skipUnless(NODE, "node is not installed")
class LibNodeSuite(unittest.TestCase):
    def test_node_suite_passes(self):
        # Expand the glob here: node < 21 does not expand globs passed to --test.
        files = [str(p) for p in sorted((ROOT / "lib" / "test").glob("*.test.js"))]
        self.assertTrue(files, "no lib/test/*.test.js files found")
        files += [str(p) for p in sorted((ROOT / "tools").glob("*.test.js"))]
        r = subprocess.run([NODE, "--test", *files], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, (r.stdout + r.stderr)[-6000:])


if __name__ == "__main__":
    unittest.main()
````

Then the docs:

````bash
python3 - . <<'PY'
import sys
from pathlib import Path
ROOT = Path(sys.argv[1])

def edit(rel, pairs):
    p = ROOT / rel
    s = p.read_text()
    for a, b in pairs:
        assert s.count(a) == 1, (rel, a[:70])
        s = s.replace(a, b)
    p.write_text(s)

edit("lib/README.md", [
("""`python3 -m unittest discover -s tools -p 'test_*.py' -v`). `lib/test/hygiene.test.js` scans every
  module for clocks, randomness, infinite repeats, hard-coded colours, overshoot or raw eases, and
  untagged Gaussians (colour literals other than marked pure-black alpha masks are banned).""",
 """`python3 -m unittest discover -s tools -p 'test_*.py' -v`). `lib/test/hygiene.test.js` scans every
  module with `tools/lawscan.js` (the scanner QA checks 4–6 also run over compositions) for clocks,
  randomness, infinite repeats, hard-coded colours, overshoot or raw eases, and untagged Gaussians
  (colour literals other than marked pure-black alpha masks are banned). `lib/test/drift.test.js`
  fails when `HFProfile` timings or `HFMotionBlur` shutters drift from the profile markdown."""),
])
edit("CLAUDE.md", [
("""(alone: `node --test "lib/test/*.test.js"`; browser seek check: `lib/examples/smoke.html`).""",
 """(alone: `node --test "lib/test/*.test.js" "tools/*.test.js"`; browser seek check: `lib/examples/smoke.html`).
Media-tool tests generate their own clips with ffmpeg; the runtime-probe test needs the
chrome-headless-shell HyperFrames downloads (`npx hyperframes browser ensure`)."""),
])
PY
````

- [ ] **Step 6: Run the suites**

Run: `node --test lib/test/*.test.js tools/*.test.js`
Expected: `# pass 84`, `# fail 0`.
Run: `python3 -m unittest discover -s tools -p 'test_*.py'`
Expected: `Ran 91 tests … FAILED (errors=14)`.

- [ ] **Step 7: Commit**

```bash
git add tools/lawscan.js tools/lawscan.test.js lib/test/hygiene.test.js tools/test_lib_node.py lib/README.md CLAUDE.md
git commit -m "refactor(lib): extract the motion-law scanner to tools/lawscan.js and close its known gaps

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: `brandcheck` robustness + `tools/project.py` (BRIEF, beat grid, slots)

`brandcheck.validate_choice` must return a named error instead of a traceback for a missing brand folder or malformed JSON, and `is_colour` must reject `"#F26666\n"` (`$` matches before a newline) and channels above 255. `project.py` reads the project files every later tool needs and owns QA check 3's BRIEF rules.

**Files:**
- Modify: `tools/brandcheck.py`, `tools/test_brandcheck.py`
- Create: `tools/project.py`, `tools/test_project.py`

**Interfaces:**
- Consumes: `brandcheck.validate_brand`, `brandcheck.validate_choice`, `brandcheck.load_brand`.
- Produces:
  - `brandcheck.BrandError`; `load_brand` raises it (`"brand folder <dir> not found"`, `"<folder>: <file> is not valid JSON (<msg> at line <n>)"`); `validate_brand` / `validate_choice` return it as their one error.
  - `project.ProjectError`; `project.FORMATS = ("long-form", "shorts")`; `project.PLACEMENTS = ("full-frame", "over-footage")`; `project.GRID_COLUMNS`; `project.DEFAULT_HOOK_END = 80.0`.
  - `project.parse_yaml_subset(text, label) -> dict`; `project.read_brief(project) -> dict` (first ```` ```yaml ```` block of `BRIEF.md`, errors name the file line).
  - `project.validate_brief(brief, root=ROOT) -> list[str]` (check 3; includes brand validity + choice).
  - `project.hook_end(brief) -> float`; `project.screen_share(brief) -> [(a, b)]`.
  - `project.parse_storyboard(text, label) -> [row]`, `project.read_storyboard(project)`; row = `{"row", "line", "t_in", "t_out" (float), "words", "placement", "type", "beats", "ease", "marks"}`.
  - `project.composition_slots(project) -> [{"id", "src", "start", "dur"}]` (sorted by start); `project.root_attrs(project) -> dict`; `project.transcript_duration(project) -> float | None`.

- [ ] **Step 1: Write the failing tests**

````bash
python3 - . <<'PY'
import sys
from pathlib import Path
ROOT = Path(sys.argv[1])

def edit(rel, pairs):
    p = ROOT / rel
    s = p.read_text()
    for a, b in pairs:
        assert s.count(a) == 1, (rel, a[:70])
        s = s.replace(a, b)
    p.write_text(s)

edit("tools/test_brandcheck.py", [
("""    def test_rejects_other_formats(self):
        for v in ["#fff", "red", "rgb(1,2,3)", "F26666", "#F2666", "", None, 12]:
            self.assertFalse(bc.is_colour(v), v)
""",
 '    def test_rejects_other_formats(self):\n        for v in ["#fff", "red", "rgb(1,2,3)", "F26666", "#F2666", "", None, 12]:\n            self.assertFalse(bc.is_colour(v), v)\n\n    def test_rejects_trailing_newline_and_out_of_range_channels(self):\n        for v in ["#F26666\\n", "rgba(0,0,0,1)\\n", "rgba(256,0,0,1)", "rgba(0,999,0,0.5)"]:\n            self.assertFalse(bc.is_colour(v), repr(v))\n        self.assertTrue(bc.is_colour("rgba(255,255,255,0.5)"))\n'),
("""    def test_draft_brand_cannot_be_used(self):""",
 """    def test_missing_brand_folder_is_a_named_error(self):
        ghost = Path(self.tmp.name) / "ghost"
        self.assertEqual(bc.validate_choice(ghost, "red"), [f"brand folder {ghost} not found"])

    def test_malformed_tokens_is_a_named_error(self):
        (self.brand / "tokens.json").write_text("{ nope")
        errs = bc.validate_choice(self.brand, "red")
        self.assertEqual(len(errs), 1)
        self.assertTrue(errs[0].startswith("acme: tokens.json is not valid JSON ("), errs)
        self.assertEqual(bc.validate_brand(self.brand), errs)

    def test_malformed_palette_is_a_named_error(self):
        (self.brand / "palettes" / "red.json").write_text("[1,")
        errs = bc.validate_brand(self.brand)
        self.assertEqual(len(errs), 1)
        self.assertTrue(errs[0].startswith("acme/palettes: red.json is not valid JSON ("), errs)

    def test_draft_brand_cannot_be_used(self):"""),
])
PY
````

Create `tools/test_project.py`:

````python
import json
import tempfile
import unittest
from pathlib import Path

import project as pj

ROOT = Path(__file__).resolve().parents[1]

GOOD_LF = {
    "format": "long-form", "film": "Make the viewer believe the system is predictable.",
    "direction": "One canvas per argument; proof first, then the number.",
    "brand": "contentporary", "palette": "red", "font": "helvetica",
    "hook_end": 80, "screen_share": [[302.5, 317.0]],
    "exceptions": ["F09: recreated Google Calendar — no shareable real account"],
}

BRIEF_MD = """# BRIEF — demo

Free prose above the block is fine.

```yaml
format: shorts          # long-form | shorts
film: "One line: it's about trust."
direction: 'Hard cuts; tall camera worlds'
references:
  - "youtube.com/watch?v=HrYMfy6MZtA — camera travel"
brand: contentporary
palette: reel-dark
font: geometric
overrides:
  accentScript: "#BACE7A"   # quoted: a bare # starts a comment
captions: false
screen_share:
  - [302.5, 317.0]
exceptions:
```
"""

GRID = """# Storyboard

| t_in | t_out | words | placement | type | beats | ease | marks |
|---|---|---|---|---|---|---|---|
| 62.2 | 68.0 | "it's a system \\| that prints…" | full-frame | roadmap | line draws 0–1.2 | ease.camera | — |
| 74.1 | 79.4 | "1.2 million views" | over-footage | lower-third | lands 0.0 | ease.enter | highlight-block |

Notes after the table are ignored.
"""


class YamlSubsetTests(unittest.TestCase):
    def test_brief_block_parses(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / "BRIEF.md").write_text(BRIEF_MD)
            b = pj.read_brief(t)
        self.assertEqual(b["format"], "shorts")
        self.assertEqual(b["film"], "One line: it's about trust.")
        self.assertEqual(b["direction"], "Hard cuts; tall camera worlds")
        self.assertEqual(b["overrides"], {"accentScript": "#BACE7A"})
        self.assertIs(b["captions"], False)
        self.assertEqual(b["screen_share"], [[302.5, 317.0]])
        self.assertIsNone(b["exceptions"])
        self.assertEqual(b["references"], ["youtube.com/watch?v=HrYMfy6MZtA — camera travel"])

    def test_bad_line_names_the_file_line(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / "BRIEF.md").write_text("# B\n\n```yaml\nformat: shorts\nthis is not yaml\n```\n")
            with self.assertRaisesRegex(pj.ProjectError, r"BRIEF\.md line 5: expected 'key: value'"):
                pj.read_brief(t)

    def test_missing_block_and_file(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaisesRegex(pj.ProjectError, "BRIEF.md not found"):
                pj.read_brief(t)
            (Path(t) / "BRIEF.md").write_text("format: shorts\n")
            with self.assertRaisesRegex(pj.ProjectError, "no ```yaml block"):
                pj.read_brief(t)

    def test_duplicate_key_and_tabs_rejected(self):
        with self.assertRaisesRegex(pj.ProjectError, "duplicate key 'font'"):
            pj.parse_yaml_subset("font: a\nfont: b\n")
        with self.assertRaisesRegex(pj.ProjectError, "spaces, not tabs"):
            pj.parse_yaml_subset("gotchas:\n\t- x\n")


class ValidateBriefTests(unittest.TestCase):
    def test_good_long_form_brief(self):
        self.assertEqual(pj.validate_brief(dict(GOOD_LF), ROOT), [])

    def test_required_fields_named(self):
        errs = pj.validate_brief({"format": "long-form"}, ROOT)
        for field in ("film", "direction", "brand", "palette", "font"):
            self.assertTrue(any(e.startswith(f"{field} is required") for e in errs), (field, errs))

    def test_shorts_needs_captions_flag(self):
        b = dict(GOOD_LF, format="shorts", palette="reel-dark")
        del b["hook_end"], b["screen_share"]
        self.assertIn("captions is required for Shorts (true or false)", pj.validate_brief(b, ROOT))
        b["captions"] = True
        self.assertEqual(pj.validate_brief(b, ROOT), [])

    def test_long_form_rejects_captions_and_bad_ranges(self):
        b = dict(GOOD_LF, captions=True, screen_share=[[317.0, 302.5]], hook_end=-5)
        errs = pj.validate_brief(b, ROOT)
        self.assertIn("captions: long-form has no running captions (key-line lower thirds only)", errs)
        self.assertIn("screen_share range [317.0, 302.5] must be [start, end] seconds with start < end", errs)
        self.assertIn("hook_end must be a positive number of seconds, got -5", errs)
        self.assertIn("screen_share must be a list of [start, end] ranges",
                      pj.validate_brief(dict(GOOD_LF, screen_share="302-317"), ROOT))

    def test_unknown_field_catches_typos(self):
        errs = pj.validate_brief(dict(GOOD_LF, palete="red"), ROOT)
        self.assertTrue(errs[0].startswith("unknown BRIEF field 'palete'"), errs)

    def test_unquoted_colour_is_a_comment_and_a_named_error(self):
        b = pj.parse_yaml_subset("overrides:\n  accentScript: #BACE7A\n")
        self.assertEqual(b, {"overrides": {"accentScript": None}})
        self.assertIn("override 'accentScript' is not a colour: None",
                      pj.validate_brief(dict(GOOD_LF, overrides=b["overrides"]), ROOT))

    def test_exception_needs_a_reason(self):
        errs = pj.validate_brief(dict(GOOD_LF, exceptions=["F09", "check 6:   "]), ROOT)
        self.assertIn("exception 'F09' has no reason (each entry is '<what>: <reason>')", errs)
        self.assertIn("exception 'check 6:   ' has no reason (each entry is '<what>: <reason>')", errs)

    def test_brand_choice_flows_through_brandcheck(self):
        errs = pj.validate_brief(dict(GOOD_LF, palette="neon", font="comic"), ROOT)
        self.assertTrue(any(e.startswith("palette 'neon' not in brand contentporary") for e in errs), errs)
        self.assertTrue(any(e.startswith("font 'comic' not in brand contentporary") for e in errs), errs)
        self.assertIn("brand 'ghost': no folder brands/ghost/", pj.validate_brief(dict(GOOD_LF, brand="ghost"), ROOT))

    def test_draft_brand_fails_check_3(self):
        with tempfile.TemporaryDirectory() as t:
            src = ROOT / "brands" / "contentporary"
            dst = Path(t) / "brands" / "contentporary"
            (dst / "palettes").mkdir(parents=True)
            tokens = json.loads((src / "tokens.json").read_text())
            tokens["status"] = "draft"
            (dst / "tokens.json").write_text(json.dumps(tokens))
            for p in (src / "palettes").glob("*.json"):
                (dst / "palettes" / p.name).write_text(p.read_text())
            self.assertIn("brand contentporary is not approved (status: draft)", pj.validate_brief(dict(GOOD_LF), t))

    def test_hook_end_default(self):
        self.assertEqual(pj.hook_end({}), 80.0)
        self.assertEqual(pj.hook_end({"hook_end": 45}), 45.0)


class StoryboardTests(unittest.TestCase):
    def test_parses_rows_and_escaped_pipes(self):
        rows = pj.parse_storyboard(GRID)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["t_in"], 62.2)
        self.assertEqual(rows[0]["words"], '"it\'s a system | that prints…"')
        self.assertEqual(rows[1]["placement"], "over-footage")
        self.assertEqual((rows[1]["row"], rows[1]["line"]), (2, 6))

    def test_errors_name_the_line(self):
        with self.assertRaisesRegex(pj.ProjectError, "no beat-grid table"):
            pj.parse_storyboard("| a | b |\n|---|---|\n")
        bad = GRID.replace("| 74.1 | 79.4 |", "| 74.1 | 70.0 |")
        with self.assertRaisesRegex(pj.ProjectError, r"storyboard\.md line 6: t_out 70\.0 must be after t_in 74\.1"):
            pj.parse_storyboard(bad)
        with self.assertRaisesRegex(pj.ProjectError, "placement must be full-frame or over-footage, got 'overlay'"):
            pj.parse_storyboard(GRID.replace("over-footage", "overlay"))

    def test_empty_grid_is_empty(self):
        self.assertEqual(pj.parse_storyboard("| " + " | ".join(pj.GRID_COLUMNS) + " |\n|---|---|---|---|---|---|---|---|\n"), [])


class SlotsTranscriptTests(unittest.TestCase):
    def test_slots_sorted_and_root_attrs(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / "index.html").write_text(
                '<div id="root" data-composition-id="main" data-hf-mode="dark" data-width="1920">\n'
                '<div data-composition-id="b" data-start="4" data-duration="3" data-composition-src="compositions/b.html"></div>\n'
                '<div data-composition-src="compositions/a.html" data-composition-id="a" data-start="0" data-duration="4"></div>\n'
                '</div>')
            self.assertEqual([s["id"] for s in pj.composition_slots(t)], ["a", "b"])
            self.assertEqual(pj.composition_slots(t)[1], {"id": "b", "src": "compositions/b.html", "start": 4.0, "dur": 3.0})
            self.assertEqual(pj.root_attrs(t)["data-hf-mode"], "dark")

    def test_transcript_duration(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertIsNone(pj.transcript_duration(t))
            (Path(t) / "transcript.json").write_text(json.dumps([{"text": "a", "start": 0.1, "end": 0.4}, {"text": "b", "start": 0.5, "end": 61.25}]))
            self.assertEqual(pj.transcript_duration(t), 61.25)
            (Path(t) / "transcript.json").write_text(json.dumps({"words": [{"text": "a", "start": 0, "end": 9.5}]}))
            self.assertEqual(pj.transcript_duration(t), 9.5)


if __name__ == "__main__":
    unittest.main()
````

- [ ] **Step 2: Run them to verify they fail**

Run: `python3 -m unittest discover -s tools -p 'test_brandcheck.py' -v`
Expected: 4 failures/errors — `test_rejects_trailing_newline_and_out_of_range_channels`, `test_missing_brand_folder_is_a_named_error` (`NotADirectoryError`/`FileNotFoundError`), `test_malformed_tokens_is_a_named_error` (`JSONDecodeError`), `test_malformed_palette_is_a_named_error`.
Run: `python3 -m unittest discover -s tools -p 'test_project.py' -v`
Expected: ERROR — `ModuleNotFoundError: No module named 'project'`.

- [ ] **Step 3: Harden brandcheck**

````bash
python3 - . <<'PY'
import sys
from pathlib import Path
ROOT = Path(sys.argv[1])

def edit(rel, pairs):
    p = ROOT / rel
    s = p.read_text()
    for a, b in pairs:
        assert s.count(a) == 1, (rel, a[:70])
        s = s.replace(a, b)
    p.write_text(s)

edit("tools/brandcheck.py", [
('_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")\n_RGBA = re.compile(r"^rgba\\(\\s*\\d{1,3}\\s*,\\s*\\d{1,3}\\s*,\\s*\\d{1,3}\\s*,\\s*(0|1|0?\\.\\d+)\\s*\\)$")\n\n\ndef is_colour(value) -> bool:\n    return isinstance(value, str) and bool(_HEX.match(value) or _RGBA.match(value))\n',
 '_HEX = re.compile(r"#[0-9A-Fa-f]{6}")\n_RGBA = re.compile(r"rgba\\(\\s*(\\d{1,3})\\s*,\\s*(\\d{1,3})\\s*,\\s*(\\d{1,3})\\s*,\\s*(0|1|0?\\.\\d+)\\s*\\)")\n\n\nclass BrandError(Exception):\n    """A brand folder that cannot be read (missing folder or file, malformed JSON)."""\n\n\ndef is_colour(value) -> bool:\n    if not isinstance(value, str):\n        return False\n    if _HEX.fullmatch(value):\n        return True\n    m = _RGBA.fullmatch(value)\n    return bool(m) and all(int(c) <= 255 for c in m.groups()[:3])\n\n\ndef _read_json(path: Path, label: str):\n    try:\n        return json.loads(path.read_text())\n    except FileNotFoundError:\n        raise BrandError(f"{label}: missing {path.name}")\n    except json.JSONDecodeError as e:\n        raise BrandError(f"{label}: {path.name} is not valid JSON ({e.msg} at line {e.lineno})")\n'),
("""def load_brand(brand_dir: Path) -> dict:
    brand_dir = Path(brand_dir)
    tokens = json.loads((brand_dir / "tokens.json").read_text())
    palettes = {}
    for name in tokens.get("palettes", []):
        f = brand_dir / "palettes" / f"{name}.json"
        if f.is_file():
            palettes[name] = json.loads(f.read_text())
    return {"tokens": tokens, "palettes": palettes}
""",
 '''def load_brand(brand_dir: Path) -> dict:
    """Read tokens.json and every listed palette. Raises BrandError naming the folder and file."""
    brand_dir = Path(brand_dir)
    if not brand_dir.is_dir():
        raise BrandError(f"brand folder {brand_dir} not found")
    tokens = _read_json(brand_dir / "tokens.json", brand_dir.name)
    if not isinstance(tokens, dict):
        raise BrandError(f"{brand_dir.name}: tokens.json must be a JSON object")
    palettes = {}
    for name in tokens.get("palettes") or []:
        f = brand_dir / "palettes" / f"{name}.json"
        if f.is_file():
            palettes[name] = _read_json(f, f"{brand_dir.name}/palettes")
    return {"tokens": tokens, "palettes": palettes}
'''),
("""    if not (brand_dir / "tokens.json").is_file():
        return [f"{folder}: missing tokens.json"]
    brand = load_brand(brand_dir)
""",
 """    if not (brand_dir / "tokens.json").is_file():
        return [f"{folder}: missing tokens.json"]
    try:
        brand = load_brand(brand_dir)
    except BrandError as e:
        return [str(e)]
"""),
("""    brand_dir = Path(brand_dir)
    brand = load_brand(brand_dir)
    t = brand["tokens"]
    name = t.get("name", brand_dir.name)""",
 """    brand_dir = Path(brand_dir)
    try:
        brand = load_brand(brand_dir)
    except BrandError as e:
        return [str(e)]
    t = brand["tokens"]
    name = t.get("name", brand_dir.name)"""),
("""    brand_dir = Path(argv[1])
    errors = validate_brand(brand_dir)""",
 """    brand_dir = Path(argv[1])
    if not brand_dir.is_dir():
        print(f"brand folder {brand_dir} not found")
        return 1
    errors = validate_brand(brand_dir)"""),
])
PY
````

- [ ] **Step 4: Write `tools/project.py`**

Create `tools/project.py`:

````python
"""Read a video project's files: BRIEF.md, storyboard.md (beat grid), index.html slots, transcript.json.

Field rules: standards/core/pipeline.md (BRIEF fields, beat grid) and standards/core/qa.md check 3.
Standard library only — the BRIEF's YAML is a small subset parsed here (no PyYAML).
"""
import json
import re
from pathlib import Path

import brandcheck

ROOT = Path(__file__).resolve().parents[1]
FORMATS = ("long-form", "shorts")
PLACEMENTS = ("full-frame", "over-footage")
GRID_COLUMNS = ["t_in", "t_out", "words", "placement", "type", "beats", "ease", "marks"]
REASON_HINT = "each entry is '<what>: <reason>'"
FIELDS = {"format", "film", "direction", "references", "gotchas", "brand", "palette", "font",
          "overrides", "captions", "hook_end", "screen_share", "exceptions", "source"}
DEFAULT_HOOK_END = 80.0


class ProjectError(Exception):
    """A project file that is missing or cannot be parsed. The message names the file and line."""


# ---------------------------------------------------------------- YAML subset (the BRIEF block)

def _strip_comment(s: str) -> str:
    q = None
    for i, c in enumerate(s):
        if q:
            if c == q:
                q = None
        elif c in "\"'":
            q = c
        elif c == "#" and (i == 0 or s[i - 1] in " \t"):
            return s[:i].rstrip()
    return s.rstrip()


def _scalar(s: str, where: str):
    s = s.strip()
    if s == "" or s in ("null", "~"):
        return None
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    if s[0] in "\"'":
        raise ProjectError(f"{where}: unterminated quote in {s!r}")
    if s.startswith("["):
        if not s.endswith("]"):
            raise ProjectError(f"{where}: unterminated list {s!r}")
        inner = s[1:-1].strip()
        return [_scalar(x, where) for x in inner.split(",")] if inner else []
    if s in ("true", "false"):
        return s == "true"
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        return s


def parse_yaml_subset(text: str, label: str = "BRIEF.md") -> dict:
    """`key: scalar`, `key:` + indented `- item` lines, or `key:` + indented `sub: scalar` lines.

    Scalars: quoted strings, numbers, true/false, null, flow lists `[a, b]`. `#` starts a comment
    after whitespace (quote colours: `"#BACE7A"`). Anything else raises ProjectError with the line.
    """
    out, key, line_no = {}, None, 0
    for line_no, raw in enumerate(text.splitlines(), 1):
        where = f"{label} line {line_no}"
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            raise ProjectError(f"{where}: indent with spaces, not tabs")
        line = _strip_comment(raw)
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        body = line.strip()
        if indent == 0:
            m = re.fullmatch(r"([A-Za-z_][\w.-]*)\s*:(.*)", body)
            if not m:
                raise ProjectError(f"{where}: expected 'key: value', got {body!r}")
            key = m.group(1)
            if key in out:
                raise ProjectError(f"{where}: duplicate key {key!r}")
            out[key] = _scalar(m.group(2), where)
            continue
        if key is None or (out[key] is not None and not isinstance(out[key], (list, dict))):
            raise ProjectError(f"{where}: unexpected indented line {body!r}")
        if body.startswith("- ") or body == "-":
            if out[key] is None:
                out[key] = []
            if not isinstance(out[key], list):
                raise ProjectError(f"{where}: {key} mixes list items and keys")
            out[key].append(_scalar(body[1:], where))
            continue
        m = re.fullmatch(r"([A-Za-z_][\w.-]*)\s*:(.*)", body)
        if not m:
            raise ProjectError(f"{where}: expected '- item' or 'sub: value' under {key}, got {body!r}")
        if out[key] is None:
            out[key] = {}
        if not isinstance(out[key], dict):
            raise ProjectError(f"{where}: {key} mixes list items and keys")
        out[key][m.group(1)] = _scalar(m.group(2), where)
    return out


# ---------------------------------------------------------------- BRIEF

def read_brief(project) -> dict:
    """Parse the first ```yaml block of <project>/BRIEF.md."""
    path = Path(project) / "BRIEF.md"
    if not path.is_file():
        raise ProjectError(f"{path} not found")
    text = path.read_text()
    m = re.search(r"^```ya?ml[ \t]*\n(.*?)^```", text, re.S | re.M)
    if not m:
        raise ProjectError(f"{path}: no ```yaml block (the BRIEF fields live in one fenced yaml block)")
    offset = text[: m.start(1)].count("\n")
    try:
        return parse_yaml_subset(m.group(1), "BRIEF.md")
    except ProjectError as e:
        # report file line numbers, not block line numbers
        msg = re.sub(r"BRIEF\.md line (\d+)", lambda g: f"BRIEF.md line {int(g.group(1)) + offset}", str(e))
        raise ProjectError(msg)


def _nonempty_str(v) -> bool:
    return isinstance(v, str) and v.strip() != ""


def _num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def validate_brief(brief: dict, root=ROOT) -> list:
    """QA check 3: every error that makes the BRIEF incomplete or its brand choice invalid."""
    errors = []
    for k in sorted(set(brief) - FIELDS):
        errors.append(f"unknown BRIEF field {k!r} (fields: {', '.join(sorted(FIELDS))})")
    fmt = brief.get("format")
    if fmt not in FORMATS:
        errors.append(f"format must be long-form or shorts, got {fmt!r}")
    for k, what in (("film", "one line: what the graphics must make the viewer feel or believe"),
                    ("direction", "one line of art direction")):
        if not _nonempty_str(brief.get(k)):
            errors.append(f"{k} is required ({what})")
    for k in ("brand", "palette", "font"):
        if not _nonempty_str(brief.get(k)):
            errors.append(f"{k} is required")
    for k in ("references", "gotchas"):
        v = brief.get(k)
        if v is not None and not (isinstance(v, list) and all(_nonempty_str(x) for x in v)):
            errors.append(f"{k} must be a list of strings")
    overrides = brief.get("overrides")
    if overrides is not None and not isinstance(overrides, dict):
        errors.append("overrides must be a map of palette role paths to colours")
        overrides = None
    captions = brief.get("captions")
    if fmt == "shorts" and not isinstance(captions, bool):
        errors.append("captions is required for Shorts (true or false)")
    if fmt == "long-form":
        if captions is True:
            errors.append("captions: long-form has no running captions (key-line lower thirds only)")
        hook = brief.get("hook_end")
        if hook is not None and not (_num(hook) and hook > 0):
            errors.append(f"hook_end must be a positive number of seconds, got {hook!r}")
        ranges = brief.get("screen_share")
        if ranges is not None and not isinstance(ranges, list):
            errors.append("screen_share must be a list of [start, end] ranges")
        for r in ranges if isinstance(ranges, list) else []:
            if not (isinstance(r, list) and len(r) == 2 and all(_num(x) for x in r) and r[0] < r[1]):
                errors.append(f"screen_share range {r!r} must be [start, end] seconds with start < end")
    exceptions = brief.get("exceptions")
    if exceptions is not None:
        if not isinstance(exceptions, list):
            errors.append(f"exceptions must be a list ({REASON_HINT})")
        else:
            for e in exceptions:
                if not (isinstance(e, str) and re.fullmatch(r"\s*\S[^:]*:\s*\S.*", e)):
                    errors.append(f"exception {e!r} has no reason ({REASON_HINT})")
    if _nonempty_str(brief.get("brand")) and _nonempty_str(brief.get("palette")):
        brand_dir = Path(root) / "brands" / brief["brand"]
        if not brand_dir.is_dir():
            errors.append(f"brand {brief['brand']!r}: no folder brands/{brief['brand']}/")
        else:
            errors += brandcheck.validate_brand(brand_dir)
            errors += brandcheck.validate_choice(brand_dir, brief["palette"], brief.get("font"), overrides)
    return list(dict.fromkeys(errors))


def hook_end(brief: dict) -> float:
    v = brief.get("hook_end")
    return float(v) if _num(v) else DEFAULT_HOOK_END


def screen_share(brief: dict) -> list:
    return [(float(a), float(b)) for a, b in (brief.get("screen_share") or [])]


# ---------------------------------------------------------------- storyboard (beat grid)

def _cells(line: str) -> list:
    parts = re.split(r"(?<!\\)\|", line.strip())
    return [p.strip().replace("\\|", "|") for p in parts[1:-1]]


def parse_storyboard(text: str, label: str = "storyboard.md") -> list:
    """Rows of the beat-grid table (header exactly the pipeline.md columns), in file order.

    Each row: {"row": n, "line": file line, "t_in", "t_out" (floats), and the other columns as text}.
    """
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip().startswith("|") and _cells(line) == GRID_COLUMNS:
            start = i
            break
    if start is None:
        raise ProjectError(f"{label}: no beat-grid table (header: | {' | '.join(GRID_COLUMNS)} |)")
    rows = []
    for i in range(start + 2, len(lines)):
        line = lines[i]
        if not line.strip().startswith("|"):
            break
        cells = _cells(line)
        where = f"{label} line {i + 1}"
        if len(cells) != len(GRID_COLUMNS):
            raise ProjectError(f"{where}: expected {len(GRID_COLUMNS)} cells, got {len(cells)}")
        row = dict(zip(GRID_COLUMNS, cells))
        try:
            row["t_in"], row["t_out"] = float(row["t_in"]), float(row["t_out"])
        except ValueError:
            raise ProjectError(f"{where}: t_in and t_out must be seconds, got {cells[0]!r}, {cells[1]!r}")
        if row["t_out"] <= row["t_in"]:
            raise ProjectError(f"{where}: t_out {row['t_out']} must be after t_in {row['t_in']}")
        if row["placement"] not in PLACEMENTS:
            raise ProjectError(f"{where}: placement must be full-frame or over-footage, got {row['placement']!r}")
        row["row"], row["line"] = len(rows) + 1, i + 1
        rows.append(row)
    return rows


def read_storyboard(project) -> list:
    path = Path(project) / "storyboard.md"
    if not path.is_file():
        raise ProjectError(f"{path} not found")
    return parse_storyboard(path.read_text())


# ---------------------------------------------------------------- index.html slots, transcript

def _attrs(tag: str) -> dict:
    return dict(re.findall(r'([\w:-]+)\s*=\s*"([^"]*)"', tag))


def composition_slots(project) -> list:
    """Sub-composition slots of <project>/index.html, sorted by data-start:
    [{"id", "src", "start", "dur"}]. These are the full-frame scenes of a long-form reel."""
    path = Path(project) / "index.html"
    if not path.is_file():
        raise ProjectError(f"{path} not found")
    slots = []
    for tag in re.findall(r"<[a-zA-Z][^>]*\bdata-composition-src\s*=[^>]*>", path.read_text()):
        a = _attrs(tag)
        try:
            slots.append({"id": a.get("data-composition-id") or a["data-composition-src"],
                          "src": a["data-composition-src"],
                          "start": float(a["data-start"]), "dur": float(a["data-duration"])})
        except (KeyError, ValueError):
            raise ProjectError(f"{path}: slot {tag[:80]!r} needs numeric data-start and data-duration")
    return sorted(slots, key=lambda s: s["start"])


def root_attrs(project) -> dict:
    """Attributes of the root composition element (the first tag with data-composition-id)."""
    path = Path(project) / "index.html"
    m = re.search(r"<[a-zA-Z][^>]*\bdata-composition-id\s*=[^>]*>", path.read_text()) if path.is_file() else None
    return _attrs(m.group(0)) if m else {}


def transcript_duration(project):
    """End time of the last word in <project>/transcript.json, or None if there is no transcript."""
    path = Path(project) / "transcript.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise ProjectError(f"{path} is not valid JSON ({e.msg} at line {e.lineno})")
    words = data if isinstance(data, list) else (data.get("words") or data.get("segments") or [])
    ends = [w["end"] for w in words if isinstance(w, dict) and _num(w.get("end"))]
    return max(ends) if ends else None
````

- [ ] **Step 5: Run the tests**

Run: `python3 -m unittest discover -s tools -p 'test_brandcheck.py' -v` → `Ran 30 tests … OK`.
Run: `python3 -m unittest discover -s tools -p 'test_project.py' -v` → `Ran 19 tests … OK`.
Run: `python3 tools/brandcheck.py brands/nope` → `brand folder brands/nope not found` (exit 1); `python3 tools/brandcheck.py brands/contentporary` → `OK contentporary (approved)`.
Run: `python3 -m unittest discover -s tools -p 'test_*.py'` → `Ran 114 tests … FAILED (errors=14)`.

- [ ] **Step 6: Commit**

```bash
git add tools/brandcheck.py tools/test_brandcheck.py tools/project.py tools/test_project.py
git commit -m "feat(tools): project.py (BRIEF, beat grid, slots) and named brandcheck errors

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: `tools/new_video.py` — scaffold a project

Creates `videos/<slug>/` exactly as `pipeline.md` lays it out, plus what HyperFrames needs to run `check` on day one: an `index.html` root sized for the format with the synced lib in load order, `data-hf-mode` from the palette, and `compositions/brand.css` from `lib/brand.js`. The BRIEF template marks `film` and `direction` REQUIRED; check 3 fails on them until filled. A scaffold made this way passed `npx hyperframes check` (0 errors) while prototyping.

**Files:**
- Create: `tools/new_video.py`, `tools/test_new_video.py`
- Modify: `standards/core/pipeline.md`

**Interfaces:**
- Consumes: `sync_lib.sync`, `sync_lib.load_manifest(root)["loadOrder"]` (Task 1); `brandcheck.load_brand`, `validate_brand`, `validate_choice`, `BrandError` (Task 4); `project.read_brief`, `validate_brief`, `read_storyboard` (tests); `node lib/brand.js <brand> --palette P --font F`.
- Produces: `new_video.scaffold(slug, fmt, brand="contentporary", palette=None, font=None, videos_dir=None, root=ROOT) -> Path` (raises `ValueError` with the reason; never overwrites); `new_video.SIZES = {"long-form": (1920, 1080), "shorts": (1080, 1920)}`; CLI `python3 tools/new_video.py <slug> --format long-form|shorts [--brand] [--palette] [--font] [--videos-dir]`. Files: `BRIEF.md`, `storyboard.md` (empty beat grid), `critique.md` (Round 1 table header `| graphic | smooth | on-brand | readable | synced | purposeful | craft | notes |`), `assets/captures/MANIFEST.md`, `compositions/brand.css`, `compositions/overlays/.gitkeep` (long-form), `deliver/.gitkeep`, `index.html` (root `data-composition-id="main"`, `data-hf-mode`), `lib/` + `lib.lock`.

- [ ] **Step 1: Write the failing test**

Create `tools/test_new_video.py`:

````python
import io
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import new_video as nv
import project as pj
import sync_lib

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class ScaffoldTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.videos = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_long_form_layout(self):
        p = nv.scaffold("10-demo", "long-form", videos_dir=self.videos)
        for rel in ["BRIEF.md", "storyboard.md", "critique.md", "assets/captures/MANIFEST.md",
                    "compositions/brand.css", "compositions/overlays/.gitkeep", "deliver/.gitkeep",
                    "index.html", "lib.lock", "lib/profile.js"]:
            self.assertTrue((p / rel).is_file(), rel)
        self.assertTrue((p / "lib" / "shorts" / "wipe.js").is_file(), "every manifest module is synced")
        self.assertEqual(sync_lib.check(p), [])

    def test_brief_template_fails_only_on_required_direction_and_film(self):
        p = nv.scaffold("10-demo", "long-form", videos_dir=self.videos)
        brief = pj.read_brief(p)
        self.assertEqual((brief["format"], brief["palette"], brief["font"], brief["hook_end"]),
                         ("long-form", "red", "helvetica", 80))
        self.assertEqual(pj.validate_brief(brief), [
            "film is required (one line: what the graphics must make the viewer feel or believe)",
            "direction is required (one line of art direction)"])
        text = (p / "BRIEF.md").read_text()
        self.assertIn('film: ""                     # REQUIRED', text)
        self.assertIn('direction: ""                # REQUIRED', text)

    def test_index_root_and_scripts_follow_format_and_palette(self):
        lf = (nv.scaffold("10-demo", "long-form", videos_dir=self.videos) / "index.html").read_text()
        self.assertIn('data-hf-mode="dark"', lf)
        self.assertIn('data-width="1920" data-height="1080"', lf)
        self.assertNotIn("lib/shorts/wipe.js", lf)
        self.assertLess(lf.index("lib/profile.js"), lf.index("lib/camera.js"))
        sh = (nv.scaffold("s9-demo", "shorts", palette="reel-light", videos_dir=self.videos) / "index.html").read_text()
        self.assertIn('data-hf-mode="light"', sh)
        self.assertIn('data-width="1080" data-height="1920"', sh)
        self.assertIn('<script src="lib/shorts/wipe.js"></script>', sh)
        brief = pj.read_brief(self.videos / "s9-demo")
        self.assertIs(brief["captions"], False)
        self.assertNotIn("hook_end", brief)

    def test_brand_css_comes_from_the_chosen_palette(self):
        css = (nv.scaffold("10-demo", "long-form", palette="paper", font="geometric", videos_dir=self.videos)
               / "compositions" / "brand.css").read_text()
        self.assertTrue(css.startswith("/* hf-mode: light"))
        self.assertIn('--hf-font-headline: "Satoshi"', css)

    def test_storyboard_and_critique_templates_parse(self):
        p = nv.scaffold("10-demo", "long-form", videos_dir=self.videos)
        self.assertEqual(pj.read_storyboard(p), [])
        self.assertIn("| graphic | smooth | on-brand | readable | synced | purposeful | craft | notes |",
                      (p / "critique.md").read_text())

    def test_refuses_bad_input_and_never_overwrites(self):
        nv.scaffold("10-demo", "long-form", videos_dir=self.videos)
        with self.assertRaisesRegex(ValueError, "already exists"):
            nv.scaffold("10-demo", "long-form", videos_dir=self.videos)
        with self.assertRaisesRegex(ValueError, "slug 'Bad Slug'"):
            nv.scaffold("Bad Slug", "long-form", videos_dir=self.videos)
        with self.assertRaisesRegex(ValueError, "palette 'neon' not in brand contentporary"):
            nv.scaffold("11-demo", "long-form", palette="neon", videos_dir=self.videos)
        with self.assertRaisesRegex(ValueError, "brand folder .*ghost not found"):
            nv.scaffold("12-demo", "long-form", brand="ghost", videos_dir=self.videos)
        self.assertFalse((self.videos / "11-demo").exists())

    def test_cli(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(nv.main(["new_video.py", "13-demo", "--format", "shorts", "--videos-dir", str(self.videos)]), 0)
            self.assertEqual(nv.main(["new_video.py", "13-demo", "--format", "shorts", "--videos-dir", str(self.videos)]), 1)
        self.assertIn("created", out.getvalue())
        self.assertIn("already exists", out.getvalue())


if __name__ == "__main__":
    unittest.main()
````

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 -m unittest discover -s tools -p 'test_new_video.py' -v`
Expected: ERROR — `ModuleNotFoundError: No module named 'new_video'`.

- [ ] **Step 3: Write the scaffolder**

Create `tools/new_video.py`:

````python
"""Scaffold a video project: videos/<slug>/ with BRIEF, beat grid, critique log, captures manifest,
deliver/, an index.html root, the brand stylesheet and a synced, locked lib/.

Layout: standards/core/pipeline.md. Never overwrites an existing project.
Usage:
  python3 tools/new_video.py <slug> --format long-form|shorts [--brand contentporary]
                             [--palette <name>] [--font <key>] [--videos-dir videos]
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

import brandcheck
import sync_lib

ROOT = Path(__file__).resolve().parents[1]
SLUG = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")
SIZES = {"long-form": (1920, 1080), "shorts": (1080, 1920)}
GSAP = "https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"

BRIEF = """# BRIEF — {slug}

Fields: `standards/core/pipeline.md` (BRIEF fields). `python3 tools/qa.py videos/{slug}` (check 3)
fails until every REQUIRED field is filled. Keep the fields inside the yaml block.

```yaml
format: {format}
film: ""                     # REQUIRED — one line: what this video's graphics must make the viewer feel or believe
direction: ""                # REQUIRED — one line of art direction, e.g. "one canvas per argument; proof first, then the number"
references:                  # optional: reference videos/stills whose grammar to borrow
gotchas:                     # optional: things to avoid in this video specifically
brand: {brand}               # REQUIRED — folder under brands/, must be status: approved
palette: {palette}           # REQUIRED — one of the brand's palettes
font: {font}                 # REQUIRED — one of the brand's headline fonts
overrides:                   # optional one-off palette role overrides, flat dot paths, quoted colours: accentScript: "#BACE7A"
{format_fields}exceptions:                  # optional, each "<what>: <reason>"; "check <n>: <reason>" waives QA check n
source: ""                   # shared-drive path to the basic-edit export / footage
```
"""
LONG_FORM_FIELDS = """hook_end: 80                 # end of the hook in seconds
screen_share:                # ranges exempt from the 30 s cadence rule, e.g. - [302.5, 317.0]
"""
SHORTS_FIELDS = """captions: false              # REQUIRED for Shorts — true | false (never re-add captions the footage already carries)
"""

STORYBOARD = """# Storyboard — {slug}

The beat grid (`standards/core/pipeline.md`): one row per graphic, written from `transcript.json`
and approved by the runner before any code. `placement` is `full-frame` or `over-footage`; `type` is a
kit name or a catalogue ID (`standards/formats/long-form.md`). Times are seconds on the edit timeline.
Check density on this table: `python3 tools/cadence_scan.py videos/{slug}`.
Example row: `| 62.2 | 68.0 | "it's a system that prints…" | full-frame | roadmap | line draws 0–1.2 · node 1 docks 1.4 | ease.camera / ease.enter | — |`

| t_in | t_out | words | placement | type | beats | ease | marks |
|---|---|---|---|---|---|---|---|
"""

CRITIQUE = """# Critique — {slug}

Critique loop: `standards/core/qa.md` §2. One section per round; score every graphic 1–10 on each
dimension with one sentence of evidence in `notes`. Fix anything below 8, re-render, re-score; stop at
all ≥ 8 or after 3 rounds. The preview pack reads the last round's table.

## Round 1

| graphic | smooth | on-brand | readable | synced | purposeful | craft | notes |
|---|---|---|---|---|---|---|---|
"""

MANIFEST = """# Captures — {slug}

Every screenshot or recreation in `assets/captures/` gets one row (`standards/core/pipeline.md`, Capture).

| file | source URL | UI mode | what's visible | caveats |
|---|---|---|---|---|
"""

INDEX = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width={w}, height={h}">
    <script src="{gsap}"></script>
{scripts}
    <link rel="stylesheet" href="compositions/brand.css">
    <style>
      html, body {{ margin: 0; width: {w}px; height: {h}px; overflow: hidden; background: var(--hf-ground-deep); }}
      #root {{ position: relative; width: {w}px; height: {h}px; overflow: hidden; }}
      #root > div[data-composition-src] {{ position: absolute; inset: 0; }}
    </style>
  </head>
  <body>
    <!-- {slug} — {placement_note} -->
    <div id="root" data-composition-id="main" data-hf-mode="{mode}" data-start="0" data-duration="5" data-width="{w}" data-height="{h}">
    </div>
    <script>
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
"""
PLACEMENT_NOTE = {
    "long-form": "full-frame scene reel: one slot per full-frame scene, in timeline order "
                 "(data-composition-src, data-start, data-duration). Over-footage layouts are standalone transparent "
                 "documents (no template wrapper) in compositions/overlays/, each rendered with -c ... --format=mov.",
    "shorts": "one composition over the vertical footage; scene ends land on the footage's own cuts "
              "(python3 tools/probe_cuts.py <footage>).",
}


def scaffold(slug, fmt, brand="contentporary", palette=None, font=None, videos_dir=None, root=ROOT) -> Path:
    """Create the project and return its path. Raises ValueError with the reason on bad input."""
    root = Path(root)
    if not SLUG.fullmatch(slug or ""):
        raise ValueError(f"slug {slug!r} must be lowercase letters, digits and dashes (e.g. 10-youtube-funnel)")
    if fmt not in SIZES:
        raise ValueError(f"format must be long-form or shorts, got {fmt!r}")
    project = Path(videos_dir or root / "videos") / slug
    if project.exists():
        raise ValueError(f"{project} already exists — new_video never overwrites a project")
    brand_dir = root / "brands" / brand
    try:
        tokens = brandcheck.load_brand(brand_dir)["tokens"]
    except brandcheck.BrandError as e:
        raise ValueError(str(e))
    palette = palette or tokens.get("defaultPalette")
    font = font or (tokens.get("fonts") or {}).get("defaultHeadline")
    errors = [e for e in brandcheck.validate_choice(brand_dir, palette, font) if "is not approved" not in e]
    errors += brandcheck.validate_brand(brand_dir)
    if errors:
        raise ValueError("; ".join(errors))
    mode = brandcheck.load_brand(brand_dir)["palettes"][palette]["mode"]
    node = shutil.which("node")
    if not node:
        raise ValueError("node is required (it generates compositions/brand.css from the brand)")
    css = subprocess.run([node, str(root / "lib" / "brand.js"), str(brand_dir), "--palette", palette, "--font", font],
                         capture_output=True, text=True)
    if css.returncode != 0:
        raise ValueError("lib/brand.js failed: " + css.stderr.strip())

    w, h = SIZES[fmt]
    order = [m for m in sync_lib.load_manifest(root)["loadOrder"] if fmt == "shorts" or not m.startswith("shorts/")]
    files = {
        "BRIEF.md": BRIEF.format(slug=slug, format=fmt, brand=brand, palette=palette, font=font,
                                 format_fields=LONG_FORM_FIELDS if fmt == "long-form" else SHORTS_FIELDS),
        "storyboard.md": STORYBOARD.format(slug=slug),
        "critique.md": CRITIQUE.format(slug=slug),
        "assets/captures/MANIFEST.md": MANIFEST.format(slug=slug),
        "compositions/brand.css": css.stdout,
        "deliver/.gitkeep": "",
        "index.html": INDEX.format(w=w, h=h, gsap=GSAP, mode=mode, slug=slug, placement_note=PLACEMENT_NOTE[fmt],
                                   scripts="\n".join(f'    <script src="lib/{m}"></script>' for m in order)),
    }
    if fmt == "long-form":
        files["compositions/overlays/.gitkeep"] = ""
    for rel, text in files.items():
        (project / rel).parent.mkdir(parents=True, exist_ok=True)
        (project / rel).write_text(text)
    sync_lib.sync(project, root)
    return project


def main(argv) -> int:
    ap = argparse.ArgumentParser(prog="python3 tools/new_video.py", description="Scaffold videos/<slug>/.")
    ap.add_argument("slug")
    ap.add_argument("--format", required=True, choices=sorted(SIZES))
    ap.add_argument("--brand", default="contentporary")
    ap.add_argument("--palette")
    ap.add_argument("--font")
    ap.add_argument("--videos-dir")
    a = ap.parse_args(argv[1:])
    try:
        project = scaffold(a.slug, a.format, a.brand, a.palette, a.font, a.videos_dir)
    except ValueError as e:
        print(e)
        return 1
    status = brandcheck.load_brand(ROOT / "brands" / a.brand)["tokens"].get("status")
    if status != "approved":
        print(f"warning: brand {a.brand} is {status} — the QA gate fails until it is approved")
    print(f"created {project} — fill BRIEF.md (film, direction), then write storyboard.md")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
````

- [ ] **Step 4: Run the tests**

Run: `python3 -m unittest discover -s tools -p 'test_new_video.py' -v`
Expected: `Ran 7 tests … OK`.
Optional live check (needs network for GSAP/npx): `python3 tools/new_video.py 99-scratch --format long-form --videos-dir /tmp/hf && npx hyperframes check /tmp/hf/99-scratch` → `Check passed`; then `rm -rf /tmp/hf`.

- [ ] **Step 5: Document the command**

````bash
python3 - . <<'PY'
import sys
from pathlib import Path
ROOT = Path(sys.argv[1])

def edit(rel, pairs):
    p = ROOT / rel
    s = p.read_text()
    for a, b in pairs:
        assert s.count(a) == 1, (rel, a[:70])
        s = s.replace(a, b)
    p.write_text(s)

edit("standards/core/pipeline.md", [
("""```
videos/<slug>/  BRIEF.md · transcript.json · storyboard.md · critique.md · assets/captures/MANIFEST.md
                compositions/ · lib/ + lib.lock · deliver/
```""",
 """```
videos/<slug>/  BRIEF.md · transcript.json · storyboard.md · critique.md · assets/captures/MANIFEST.md
                index.html · compositions/ (brand.css; long-form: overlays/) · lib/ + lib.lock · deliver/
                renders/ (never committed: drafts, qa-report.json, preview/)
```
`python3 tools/new_video.py <slug> --format long-form|shorts [--palette <p>] [--font <f>]` creates all of
it (brand from `--brand`, default `contentporary`) and never overwrites an existing project."""),
("""1. **Intake.** `tools/new-video` (Plan 3) scaffolds `videos/<slug>/` and syncs `lib/`. Inputs: the
   basic-edit export (a proxy is fine) and its transcript (`npx hyperframes transcribe`).""",
 """1. **Intake.** `python3 tools/new_video.py <slug> --format long-form` scaffolds `videos/<slug>/` and
   syncs `lib/` (`python3 tools/sync_lib.py videos/<slug>` re-syncs later). Inputs: the
   basic-edit export (a proxy is fine) and its transcript (`npx hyperframes transcribe`)."""),
])
PY
````

Run: `python3 -m unittest discover -s tools -p 'test_*.py'` → `Ran 121 tests … FAILED (errors=14)`.

- [ ] **Step 6: Commit**

```bash
git add tools/new_video.py tools/test_new_video.py standards/core/pipeline.md
git commit -m "feat(tools): new_video scaffolds videos/<slug> with BRIEF, beat grid, brand.css and a locked lib

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: `media.py`, `probe_cuts.py`, `scan_flicker.py` (+ `synth.py` test clips)

**Files:**
- Create: `tools/media.py`, `tools/synth.py`, `tools/probe_cuts.py`, `tools/scan_flicker.py`, `tools/test_media_tools.py`
- Modify: `standards/core/pipeline.md`, `standards/formats/shorts.md`

**Interfaces:**
- Consumes: ffmpeg/ffprobe on `PATH`.
- Produces:
  - `media.MediaError`; `media.tool(name)`; `media.run(args, binary=False) -> stdout` (raises with stderr tail).
  - `media.video_info(path) -> {"duration", "width", "height", "fps", "codec", "profile", "pix_fmt", "frames"}`.
  - `media.frame_diffs(path, size=(320, 180)) -> [float]` — `d[i]` = mean |Δluma| (0–255) between frame i and i+1.
  - `media.gray_frames(path, fps, size=(32, 18)) -> [bytes]`; `media.scene_cuts(path, threshold=0.20) -> [seconds]`.
  - `media.extract_frame(path, t, out_png, width=480, background=None) -> Path` (8-bit RGB; `background` composites alpha over that colour).
  - `synth.HAVE_FFMPEG`; `synth.segments(path, [(colour, secs)], size, fps, noise)`, `synth.moving(path, secs, size, fps, glitch_frame)`, `synth.moving_then_still(path, moving_secs, still_secs, size, fps, glitch_frame)`, `synth.prores(path, secs, size, fps, alpha=True)`, `synth.concat(path, parts, fps)`.
  - `probe_cuts.THRESHOLD = 0.20`, `probe_cuts.EXIT = 0.36`, `probe_cuts.scene_ends(cuts, exit_dur) -> [{"cut", "scene_end"}]`; CLI `python3 tools/probe_cuts.py FOOTAGE [--threshold] [--exit] [--json]`.
  - `scan_flicker.find_flicker(diffs) -> [(frame, step, local)]`, `scan_flicker.scan(path) -> {"file", "frames", "median", "flicker"}`; CLI exit 1 if any file flickers.

- [ ] **Step 1: Write the test clips helper and the failing tests**

Create `tools/synth.py` (test support, not a test module — the test discovery pattern `test_*.py` skips it):

````python
"""Synthetic test videos for the media-tool tests (ffmpeg lavfi sources — never real footage)."""
import shutil
import subprocess

HAVE_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


def _ffmpeg(args):
    subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-y", *args], check=True)


def segments(path, parts, size=(160, 90), fps=30, noise=False):
    """Concatenate solid-colour segments: parts = [("0x808080", 2.0), ("navy", 1.5), ...].
    noise=True adds light temporal grain (deterministic seed) so frames are not bit-identical."""
    w, h = size
    args, labels = [], ""
    for i, (colour, secs) in enumerate(parts):
        args += ["-f", "lavfi", "-i", f"color=c={colour}:s={w}x{h}:r={fps}:d={secs}"]
        labels += f"[{i}:v]"
    chain = f"{labels}concat=n={len(parts)}:v=1:a=0"
    if noise:
        chain += ",noise=alls=6:allf=t:all_seed=7"
    _ffmpeg(args + ["-filter_complex", chain, "-pix_fmt", "yuv420p", "-r", str(fps), str(path)])
    return path


def moving(path, secs, size=(160, 90), fps=30, glitch_frame=None):
    """testsrc2 (smooth, continuous motion); glitch_frame paints one white box on that frame only."""
    w, h = size
    vf = ["-vf", f"drawbox=x=20:y=20:w=60:h=40:color=white:t=fill:enable='eq(n,{glitch_frame})'"] if glitch_frame else []
    _ffmpeg(["-f", "lavfi", "-i", f"testsrc2=s={w}x{h}:r={fps}:d={secs}", *vf, "-pix_fmt", "yuv420p", str(path)])
    return path


def moving_then_still(path, moving_secs, still_secs, size=(160, 90), fps=30, glitch_frame=None):
    """testsrc2 motion, then its last frame held for still_secs — for the settle-before-cut check.
    glitch_frame paints one white box on that frame only (a render flicker)."""
    w, h = size
    vf = f"tpad=stop_mode=clone:stop_duration={still_secs}"
    if glitch_frame:
        vf = f"drawbox=x=20:y=20:w=60:h=40:color=white:t=fill:enable='eq(n,{glitch_frame})'," + vf
    _ffmpeg(["-f", "lavfi", "-i", f"testsrc2=s={w}x{h}:r={fps}:d={moving_secs}",
             "-vf", vf, "-pix_fmt", "yuv420p", str(path)])
    return path


def prores(path, secs, size=(160, 90), fps=30, alpha=True):
    """A ProRes clip: 4444 with alpha (what `hyperframes render --format=mov` delivers) or 422 HQ without."""
    w, h = size
    src = f"color=c=red@0.5:s={w}x{h}:r={fps}:d={secs},format=rgba"   # format in the source keeps the alpha
    codec = ["-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le"] if alpha else \
            ["-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le"]
    _ffmpeg(["-f", "lavfi", "-i", src, *codec, str(path)])
    return path


def concat(path, parts, fps=30):
    """Concatenate existing clips (same size) back to back."""
    args, labels = [], ""
    for i, p in enumerate(parts):
        args += ["-i", str(p)]
        labels += f"[{i}:v]"
    _ffmpeg(args + ["-filter_complex", f"{labels}concat=n={len(parts)}:v=1:a=0", "-pix_fmt", "yuv420p",
                    "-r", str(fps), str(path)])
    return path
````

Create `tools/test_media_tools.py`:

````python
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import media
import probe_cuts
import scan_flicker
import synth

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(synth.HAVE_FFMPEG, "ffmpeg/ffprobe not installed")
class MediaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        d = Path(cls.tmp.name)
        cls.cuts = synth.segments(d / "cuts.mp4", [("red", 1), ("blue", 1), ("white", 1)])

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_video_info(self):
        info = media.video_info(self.cuts)
        self.assertEqual((info["width"], info["height"], info["fps"], info["frames"]), (160, 90, 30.0, 90))
        self.assertAlmostEqual(info["duration"], 3.0, places=2)

    def test_missing_file_is_a_named_error(self):
        with self.assertRaisesRegex(media.MediaError, "nope.mp4 not found"):
            media.video_info("nope.mp4")

    def test_scene_cuts_at_the_0_20_threshold(self):
        self.assertEqual(media.scene_cuts(self.cuts), [1.0, 2.0])

    def test_frame_diffs_one_per_frame_pair(self):
        d = media.frame_diffs(self.cuts)
        self.assertEqual(len(d), 89)
        self.assertEqual(d[0], 0.0)
        self.assertGreater(d[29], 10)    # red → blue between frames 29 and 30

    def test_extract_frame_flattens_alpha_over_a_backdrop(self):
        with tempfile.TemporaryDirectory() as t:
            mov = synth.prores(Path(t) / "a.mov", 1)            # red at 50 % alpha
            png = media.extract_frame(mov, 0.5, Path(t) / "a.png", width=160, background="0x3a3a3a")
            self.assertEqual(media.video_info(png)["pix_fmt"], "rgb24")
            r, g, b = media.run(["ffmpeg", "-v", "error", "-i", str(png), "-vf", "crop=1:1:80:45", "-f", "rawvideo",
                                 "-pix_fmt", "rgb24", "-"], binary=True)
            self.assertGreater(r, g + 60, (r, g, b))           # red over grey, not grey alone
            self.assertGreater(g, 15, (r, g, b))                # and the grey shows through

    def test_gray_frames(self):
        frames = media.gray_frames(self.cuts, 2)
        self.assertEqual((len(frames), len(frames[0])), (6, 32 * 18))
        self.assertGreater(frames[5][0], frames[3][0])   # white is brighter than blue


@unittest.skipUnless(synth.HAVE_FFMPEG, "ffmpeg/ffprobe not installed")
class ProbeCutsTests(unittest.TestCase):
    def test_scene_end_is_cut_plus_exit(self):
        self.assertEqual(probe_cuts.scene_ends([1.0, 2.5]), [{"cut": 1.0, "scene_end": 1.36}, {"cut": 2.5, "scene_end": 2.86}])
        self.assertEqual(probe_cuts.scene_ends([1.0], 0.5), [{"cut": 1.0, "scene_end": 1.5}])

    def test_defaults_match_shorts_profile(self):
        md = (ROOT / "standards" / "formats" / "shorts.md").read_text()
        self.assertIn("gt(scene,%.2f)" % probe_cuts.THRESHOLD, md)
        self.assertIn("| duration out | **%.2fs** |" % probe_cuts.EXIT, md)

    def test_cli_json(self):
        with tempfile.TemporaryDirectory() as t:
            f = synth.segments(Path(t) / "c.mp4", [("red", 1), ("white", 1)])
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(probe_cuts.main(["probe_cuts.py", str(f), "--json"]), 0)
            self.assertEqual(json.loads(out.getvalue()), [{"cut": 1.0, "scene_end": 1.36}])
            with redirect_stdout(io.StringIO()):
                self.assertEqual(probe_cuts.main(["probe_cuts.py", str(Path(t) / "missing.mp4")]), 2)


@unittest.skipUnless(synth.HAVE_FFMPEG, "ffmpeg/ffprobe not installed")
class FlickerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        d = Path(cls.tmp.name)
        cls.smooth = synth.moving(d / "smooth.mp4", 3)
        cls.glitch = synth.moving(d / "glitch.mp4", 3, glitch_frame=45)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_find_flicker_rule(self):
        smooth = [3.0, 3.2, 3.1, 3.4, 3.3, 3.2, 3.1, 3.0]
        self.assertEqual(scan_flicker.find_flicker(smooth), [])
        spiky = smooth[:4] + [30.0] + smooth[4:]
        self.assertEqual(scan_flicker.find_flicker(spiky), [(5, 30.0, 3.15)])
        ramp = [1, 2, 4, 8, 12, 16, 12, 8, 4, 2, 1]    # a camera move: big but smooth
        self.assertEqual(scan_flicker.find_flicker([float(x) for x in ramp]), [])

    def test_smooth_motion_passes(self):
        self.assertEqual(scan_flicker.scan(self.smooth)["flicker"], [])

    def test_one_frame_glitch_is_reported(self):
        self.assertEqual([hit[0] for hit in scan_flicker.scan(self.glitch)["flicker"]], [45, 46])
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(scan_flicker.main(["scan_flicker.py", str(self.glitch)]), 1)
            self.assertEqual(scan_flicker.main(["scan_flicker.py", str(self.smooth)]), 0)
        self.assertIn("FLICKER=2", out.getvalue())


if __name__ == "__main__":
    unittest.main()
````

- [ ] **Step 2: Run them to verify they fail**

Run: `python3 -m unittest discover -s tools -p 'test_media_tools.py' -v`
Expected: ERROR — `ModuleNotFoundError: No module named 'media'`.

- [ ] **Step 3: Write the helpers and the two tools**

Create `tools/media.py`:

````python
"""ffmpeg / ffprobe helpers shared by the media tools (probe_cuts, scan_flicker, cadence_scan, slice,
qa, preview_pack). Standard library only; every measurement is done by ffmpeg filters so long videos
stay fast without numpy.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path


class MediaError(Exception):
    """ffmpeg/ffprobe missing, a file that is not there, or a command that failed (stderr included)."""


def tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise MediaError(f"{name} not found — install ffmpeg (it provides ffmpeg and ffprobe)")
    return path


def run(args, binary=False):
    r = subprocess.run(args, capture_output=True, text=not binary)
    if r.returncode != 0:
        err = r.stderr.decode(errors="replace") if binary else r.stderr
        raise MediaError(f"{Path(args[0]).name} failed ({r.returncode}): {err.strip()[-800:]}")
    return r.stdout


def _need(path) -> str:
    if not Path(path).is_file():
        raise MediaError(f"{path} not found")
    return str(path)


def video_info(path) -> dict:
    """{"duration", "width", "height", "fps", "codec", "profile", "pix_fmt", "frames"} of the first video stream."""
    out = run([tool("ffprobe"), "-v", "error", "-select_streams", "v:0", "-count_packets",
                "-show_entries", "format=duration:stream=codec_name,profile,pix_fmt,width,height,r_frame_rate,nb_read_packets",
                "-of", "json", _need(path)])
    data = json.loads(out)
    if not data.get("streams"):
        raise MediaError(f"{path} has no video stream")
    s = data["streams"][0]
    num, _, den = s.get("r_frame_rate", "0/1").partition("/")
    return {"duration": float(data.get("format", {}).get("duration", 0.0)), "width": int(s["width"]),
            "height": int(s["height"]), "fps": float(num) / float(den or 1), "codec": s.get("codec_name"),
            "profile": s.get("profile"), "pix_fmt": s.get("pix_fmt"), "frames": int(s.get("nb_read_packets", 0))}


def _metadata_values(text: str, key: str) -> list:
    return [float(v) for v in re.findall(re.escape(key) + r"=([-\d.]+)", text)]


def frame_diffs(path, size=(320, 180)) -> list:
    """Mean absolute luma difference (0–255) between consecutive frames: d[i] = |frame i+1 − frame i|."""
    w, h = size
    out = run([tool("ffmpeg"), "-v", "error", "-nostdin", "-i", _need(path), "-an", "-vf",
                f"scale={w}:{h},format=gray,tblend=all_mode=difference,signalstats,"
                "metadata=print:key=lavfi.signalstats.YAVG:file=-", "-f", "null", "-"])
    return _metadata_values(out, "lavfi.signalstats.YAVG")


def gray_frames(path, fps: float, size=(32, 18)) -> list:
    """Frames sampled at `fps`, downscaled to `size`, as bytes of 8-bit luma (one bytes object per frame)."""
    w, h = size
    raw = run([tool("ffmpeg"), "-v", "error", "-nostdin", "-i", _need(path), "-an", "-vf",
                f"fps={fps},scale={w}:{h},format=gray", "-f", "rawvideo", "-"], binary=True)
    n = w * h
    return [raw[i:i + n] for i in range(0, len(raw) - n + 1, n)]


def scene_cuts(path, threshold: float = 0.20) -> list:
    """Source cut times (s): frames whose ffmpeg scene score exceeds `threshold` (shorts.md §1 uses 0.20)."""
    out = run([tool("ffmpeg"), "-v", "error", "-nostdin", "-i", _need(path), "-an", "-filter_complex",
                f"select='gt(scene,{threshold})',metadata=print:file=-", "-f", "null", "-"])
    return [round(float(t), 3) for t in re.findall(r"pts_time:([\d.]+)", out)]


def extract_frame(path, t: float, out_png, width: int = 480, background=None) -> Path:
    """Write the frame at time t, scaled to `width`, to out_png as 8-bit RGB. With `background`
    (an ffmpeg colour) a clip with alpha is composited over it first, so transparency stays visible."""
    src = [tool("ffmpeg"), "-v", "error", "-nostdin", "-y", "-ss", f"{max(t, 0):.3f}", "-i", _need(path)]
    if background is None:
        graph = f"scale={width}:-2,format=rgb24"
    else:   # the backdrop is painted from the same frame, so both overlay inputs share one timestamp
        graph = (f"scale={width}:-2,format=rgba,split[fg][s];[s]drawbox=x=0:y=0:w=iw:h=ih:color={background}@1:t=fill[bg];"
                 "[bg][fg]overlay=format=auto,format=rgb24")
    run(src + ["-filter_complex", graph, "-frames:v", "1", str(out_png)])
    return Path(out_png)
````

Create `tools/probe_cuts.py`:

````python
"""List the footage's own cuts so Shorts scene ends land on them (standards/formats/shorts.md §1).

Scene threshold 0.20 (ffmpeg `select='gt(scene,0.20)'`). Place every scene end so the exit wipe finishes
just AFTER the nearest source cut: end = cut + exit duration (the 0.36 s wipe out by default).

Usage: python3 tools/probe_cuts.py FOOTAGE [--threshold 0.20] [--exit 0.36] [--json]
"""
import argparse
import json
import sys

import media

THRESHOLD = 0.20    # shorts.md §1
EXIT = 0.36         # shorts.md wipe "duration out" (HFProfile timing("shorts").wipe.outDur)


def scene_ends(cuts, exit_dur=EXIT) -> list:
    """[{"cut": t, "scene_end": t + exit}] — the latest a graphic may end so its exit covers the cut."""
    return [{"cut": c, "scene_end": round(c + exit_dur, 3)} for c in cuts]


def main(argv) -> int:
    ap = argparse.ArgumentParser(prog="python3 tools/probe_cuts.py")
    ap.add_argument("footage")
    ap.add_argument("--threshold", type=float, default=THRESHOLD)
    ap.add_argument("--exit", type=float, default=EXIT, dest="exit_dur")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv[1:])
    try:
        rows = scene_ends(media.scene_cuts(a.footage, a.threshold), a.exit_dur)
    except media.MediaError as e:
        print(e)
        return 2
    if a.json:
        print(json.dumps(rows))
    else:
        print(f"{len(rows)} source cuts (scene > {a.threshold}); scene end = cut + {a.exit_dur} s exit")
        for r in rows:
            print(f"  cut {r['cut']:8.3f}  ->  scene end {r['scene_end']:8.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
````

Create `tools/scan_flicker.py`:

````python
"""Detect render flicker in a rendered video: an ISOLATED jump against its local neighbourhood.

Real motion (a camera move, a mark landing) has a smooth envelope: neighbouring frame steps are of
similar size. Render flicker — parallel workers rendering blocks of frames from different seek states —
shows a single frame pair whose step dwarfs its neighbours. Ported from video 09's scan-flicker.py
(same thresholds); frame differences now come from ffmpeg (tools/media.py), so no numpy.

Usage: python3 tools/scan_flicker.py VIDEO [VIDEO...]   (exit 1 if any file flickers)
"""
import statistics
import sys
from pathlib import Path

import media

MIN_STEP = 2.5      # mean |Δluma| (0–255) a step must exceed to count at all
RATIO = 4.0         # ... and exceed RATIO × the local median
MARGIN = 2.0        # ... and the local median + MARGIN
WINDOW = 4          # neighbours on each side


def find_flicker(diffs) -> list:
    """[(frame, step, local_median)] for every isolated jump; frame is the 0-based index of the frame
    that differs from its predecessor (diffs[i] compares frame i and i+1, so frame = i + 1)."""
    hits = []
    for i, d in enumerate(diffs):
        ctx = diffs[max(0, i - WINDOW):i] + diffs[i + 1:i + 1 + WINDOW]
        if not ctx:
            continue
        local = statistics.median(ctx)
        if d > MIN_STEP and d > max(RATIO * local, local + MARGIN):
            hits.append((i + 1, round(d, 1), round(local, 2)))
    return hits


def scan(path) -> dict:
    diffs = media.frame_diffs(path)
    return {"file": str(path), "frames": len(diffs) + 1,
            "median": round(statistics.median(diffs), 2) if diffs else 0.0, "flicker": find_flicker(diffs)}


def main(argv) -> int:
    if len(argv) < 2:
        print("usage: python3 tools/scan_flicker.py VIDEO [VIDEO...]")
        return 2
    bad = 0
    for f in argv[1:]:
        try:
            r = scan(f)
        except media.MediaError as e:
            print(e)
            return 2
        bad += bool(r["flicker"])
        print("%-30s frames=%4d median=%.2f  FLICKER=%d %s" % (
            Path(f).name, r["frames"], r["median"], len(r["flicker"]), r["flicker"][:10]))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
````

- [ ] **Step 4: Run the tests**

Run: `python3 -m unittest discover -s tools -p 'test_media_tools.py' -v`
Expected: `Ran 12 tests … OK`.

- [ ] **Step 5: Document the commands**

````bash
python3 - . <<'PY'
import sys
from pathlib import Path
ROOT = Path(sys.argv[1])

def edit(rel, pairs):
    p = ROOT / rel
    s = p.read_text()
    for a, b in pairs:
        assert s.count(a) == 1, (rel, a[:70])
        s = s.replace(a, b)
    p.write_text(s)

edit("standards/core/pipeline.md", [
("""2. **Beat grid** with `tools/probe-cuts`: scene ends land on the footage's own cuts""",
 """2. **Beat grid** with `python3 tools/probe_cuts.py <footage>`: scene ends land on the footage's own cuts"""),
])
edit("standards/formats/shorts.md", [
("""Probe the source first:

```bash""",
 """Probe the source first — `python3 tools/probe_cuts.py <footage>` lists every cut and its scene end
(cut + 0.36 s), running exactly this:

```bash"""),
])
PY
````

Run: `python3 -m unittest discover -s tools -p 'test_*.py'` → `Ran 133 tests … FAILED (errors=14)`.

- [ ] **Step 6: Commit**

```bash
git add tools/media.py tools/synth.py tools/probe_cuts.py tools/scan_flicker.py tools/test_media_tools.py standards/core/pipeline.md standards/formats/shorts.md
git commit -m "feat(tools): media helpers, probe_cuts and scan_flicker (ffmpeg-only, no numpy)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: `tools/cadence_scan.py` — density on the plan and on the edit

Plan-time: the beat grid's full-frame rows (hook share, hook face gaps) and all rows (body cadence) against the runtime from `transcript.json`. Post-render: full-frame graphics measured on the edited timeline by distance from the median (talking-head) frame, plus the grid's over-footage rows, which the edit cannot show. The same `evaluate()` serves both, and QA check 8 and the preview pack call `report()`.

**Files:**
- Create: `tools/cadence_scan.py`, `tools/test_cadence_scan.py`
- Modify: `standards/core/pipeline.md`

**Interfaces:**
- Consumes: `project.read_brief`, `read_storyboard`, `transcript_duration`, `hook_end`, `screen_share`, `FORMATS`, `DEFAULT_HOOK_END` (Task 4); `media.gray_frames`, `video_info` (Task 6).
- Produces:
  - Constants `HOOK_MIN = 0.60`, `HOOK_GAP = 6.0`, `BODY_GAP = 30.0`, `SHORTS_BAND = (0.35, 0.55)`, `EDIT_FPS = 5`, `MIN_DIST = 12.0`, `EPS = 1e-6`.
  - `merge(intervals)`, `coverage(intervals, a, b)`, `gaps(intervals, a, b)`.
  - `evaluate(fmt, full_frame, duration, hook_end=80, screen_share=(), other=()) -> [{"name", "ok", "value", "detail"}]` — names: `"hook graphics ≥ 60 %"`, `"hook face gaps ≤ 6 s"`, `"body cadence ≤ 30 s"` (long-form); `"full-frame share 35–55 %"` (Shorts).
  - `face_distances(video, fps=5, face_ref=None) -> [float]`, `graphic_intervals(distances, fps=5, threshold=None) -> [(a, b)]`, `otsu(values)`.
  - `report(project, edit=None, duration=None, face_ref=None, threshold=None) -> {"format", "source", "duration", "hook_end", "full_frame", "over_footage", "screen_share", "results", "ok"}`; `format_report(r) -> str`; CLI exit 0 / 1 (a FAIL) / 2 (input error).

- [ ] **Step 1: Write the failing test**

Create `tools/test_cadence_scan.py`:

````python
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import cadence_scan as cs
import synth

ROOT = Path(__file__).resolve().parents[1]
HEADER = "| t_in | t_out | words | placement | type | beats | ease | marks |\n|---|---|---|---|---|---|---|---|\n"


def make_project(base: Path, fmt: str, rows, duration=None, extra_yaml="") -> Path:
    p = base / "proj"
    p.mkdir()
    (p / "BRIEF.md").write_text(f"# B\n\n```yaml\nformat: {fmt}\n{extra_yaml}```\n")
    grid = "".join(f"| {a} | {b} | \"w\" | {pl} | A1 | — | ease.enter | — |\n" for a, b, pl in rows)
    (p / "storyboard.md").write_text("# S\n\n" + HEADER + grid)
    if duration:
        (p / "transcript.json").write_text(json.dumps([{"text": "x", "start": 0, "end": duration}]))
    return p


def by_name(results):
    return {r["name"]: r for r in results}


class IntervalTests(unittest.TestCase):
    def test_merge_coverage_gaps(self):
        self.assertEqual(cs.merge([(5, 8), (0, 2), (1, 3), (8, 9)]), [(0.0, 3.0), (5.0, 9.0)])
        self.assertEqual(cs.coverage([(0, 3), (5, 9)], 2, 6), 2.0)
        self.assertEqual(cs.gaps([(2, 3), (5, 9)], 0, 10), [(0, 2.0), (3.0, 5.0), (9.0, 10)])
        self.assertEqual(cs.gaps([], 0, 4), [(0, 4)])


class EvaluateTests(unittest.TestCase):
    def test_long_form_hook_share_boundary(self):
        ok = by_name(cs.evaluate("long-form", [(i * 8, i * 8 + 4.8) for i in range(10)], 100))
        self.assertTrue(ok["hook graphics ≥ 60 %"]["ok"], ok)
        self.assertEqual(ok["hook graphics ≥ 60 %"]["value"], 0.6)
        low = by_name(cs.evaluate("long-form", [(i * 8, i * 8 + 4.7) for i in range(10)], 100))
        self.assertFalse(low["hook graphics ≥ 60 %"]["ok"])

    def test_long_form_hook_face_gap_boundary(self):
        base = [(0, 34), (40, 80)]
        self.assertTrue(by_name(cs.evaluate("long-form", base, 80))["hook face gaps ≤ 6 s"]["ok"])
        r = by_name(cs.evaluate("long-form", [(0, 34), (40.1, 80)], 80))["hook face gaps ≤ 6 s"]
        self.assertFalse(r["ok"])
        self.assertIn("34.0–40.1", r["detail"])

    def test_body_cadence_boundary_and_tail(self):
        hook = [(0, 80)]
        self.assertTrue(by_name(cs.evaluate("long-form", hook + [(110, 112)], 142))["body cadence ≤ 30 s"]["ok"])
        r = by_name(cs.evaluate("long-form", hook + [(111, 112)], 142))["body cadence ≤ 30 s"]
        self.assertFalse(r["ok"])
        self.assertIn("80.0–111.0", r["detail"])
        tail = by_name(cs.evaluate("long-form", hook, 111))["body cadence ≤ 30 s"]
        self.assertFalse(tail["ok"], "the stretch to the end of the video counts")

    def test_screen_share_exempt_and_over_footage_counts_for_body_only(self):
        hook = [(0, 80)]
        r = by_name(cs.evaluate("long-form", hook, 200, screen_share=[(100, 190)]))["body cadence ≤ 30 s"]
        self.assertTrue(r["ok"], r)
        self.assertIn("screen_share exempt", r["detail"])
        body = by_name(cs.evaluate("long-form", hook + [(140, 141)], 141, other=[(105, 110)]))
        self.assertTrue(body["body cadence ≤ 30 s"]["ok"])
        hook_only = by_name(cs.evaluate("long-form", [], 80, other=[(0, 80)]))
        self.assertFalse(hook_only["hook graphics ≥ 60 %"]["ok"], "over-footage layouts leave the face on screen")

    def test_short_long_form_uses_its_runtime_as_the_hook(self):
        r = by_name(cs.evaluate("long-form", [(0, 36)], 60, hook_end=80))
        self.assertEqual(r["hook graphics ≥ 60 %"]["value"], 0.6)
        self.assertEqual(r["body cadence ≤ 30 s"]["value"], 0.0)

    def test_shorts_band_edges(self):
        for secs, ok in ((35, True), (55, True), (34, False), (56, False)):
            self.assertEqual(cs.evaluate("shorts", [(0, secs)], 100)[0]["ok"], ok, secs)

    def test_thresholds_match_the_profiles(self):
        lf = (ROOT / "standards" / "formats" / "long-form.md").read_text()
        sh = (ROOT / "standards" / "formats" / "shorts.md").read_text()
        self.assertIn("default 80", lf)
        self.assertIn("≥ %d %% graphics" % round(cs.HOOK_MIN * 100), lf)
        self.assertIn("no face-only gap > %d s" % cs.HOOK_GAP, lf)
        self.assertIn("every ≤ %d s" % cs.BODY_GAP, lf)
        self.assertIn("QA band: %d–%d %%" % tuple(round(x * 100) for x in cs.SHORTS_BAND), sh)


class PlanReportTests(unittest.TestCase):
    def test_plan_report_from_the_beat_grid(self):
        with tempfile.TemporaryDirectory() as t:
            p = make_project(Path(t), "long-form", [(0, 50, "full-frame"), (52, 80, "full-frame"),
                                                    (100, 103, "over-footage")], duration=130,
                             extra_yaml="screen_share:\n  - [104, 129]\n")
            r = cs.report(p)
            self.assertTrue(r["ok"], cs.format_report(r))
            self.assertEqual(r["full_frame"], [(0.0, 50.0), (52.0, 80.0)])
            self.assertEqual(r["over_footage"], [(100.0, 103.0)])
            self.assertEqual(r["source"], "plan: storyboard.md")
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(cs.main(["cadence_scan.py", str(p)]), 0)
            self.assertIn("PASS  hook graphics ≥ 60 %", out.getvalue())

    def test_needs_a_runtime(self):
        with tempfile.TemporaryDirectory() as t:
            p = make_project(Path(t), "shorts", [(1, 4, "full-frame")], extra_yaml="captions: false\n")
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(cs.main(["cadence_scan.py", str(p)]), 2)
            self.assertIn("pass --duration or add transcript.json", out.getvalue())
            self.assertEqual(cs.report(p, duration=10)["results"][0]["value"], 0.3)


@unittest.skipUnless(synth.HAVE_FFMPEG, "ffmpeg/ffprobe not installed")
class EditMeasurementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.edit = synth.segments(Path(cls.tmp.name) / "edit.mp4",
                                  [("0x808080", 3), ("navy", 4), ("0x808080", 3)], noise=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_graphic_runs_found_by_face_distance(self):
        runs = cs.graphic_intervals(cs.face_distances(self.edit))
        self.assertEqual(len(runs), 1, runs)
        self.assertAlmostEqual(runs[0][0], 3.0, delta=0.2)
        self.assertAlmostEqual(runs[0][1], 7.0, delta=0.2)

    def test_face_ref_frame_gives_the_same_answer(self):
        runs = cs.graphic_intervals(cs.face_distances(self.edit, face_ref=1.0))
        self.assertAlmostEqual(runs[0][0], 3.0, delta=0.2)

    def test_edit_report_for_a_short(self):
        p = make_project(Path(self.tmp.name), "shorts", [(3, 7, "full-frame")], extra_yaml="captions: false\n")
        r = cs.report(p, edit=str(self.edit))
        self.assertTrue(r["ok"], cs.format_report(r))
        self.assertAlmostEqual(r["results"][0]["value"], 0.4, delta=0.03)
        self.assertTrue(r["source"].startswith("edit: "))


if __name__ == "__main__":
    unittest.main()
````

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 -m unittest discover -s tools -p 'test_cadence_scan.py' -v`
Expected: ERROR — `ModuleNotFoundError: No module named 'cadence_scan'`.

- [ ] **Step 3: Write the scanner**

Create `tools/cadence_scan.py`:

````python
"""Graphics density — standards/core/qa.md check 8 — on the plan and on the edit.

  python3 tools/cadence_scan.py videos/<slug>                 plan: the storyboard.md beat grid
  python3 tools/cadence_scan.py videos/<slug> --edit CUT.mp4  edit: full-frame graphics measured on the
                                                             edited timeline + over-footage grid rows
  options: --duration S (default: transcript.json) · --face-ref T · --threshold D · --json

Rules (standards/formats/long-form.md, shorts.md):
  long-form  hook (first hook_end s, default 80) ≥ 60 % full-frame graphics, no face-only gap > 6 s;
             body: a graphic (full-frame or over-footage) at least every 30 s; BRIEF screen_share
             ranges are exempt; face punch-ins are not graphics.
  shorts     full-frame graphics 35–55 % of the runtime.
Over-footage layouts leave the face on screen, so they do not count toward the hook share or the
hook face gaps; they do reset the 30 s body clock.

Edit measurement: frames sampled at 5 fps, 32×18 luma. The reference is the per-pixel median frame
(the talking head dominates any edit), or the frame at --face-ref. A frame whose mean distance from
the reference exceeds the threshold (Otsu over all distances, never below 12) is a graphic.
"""
import argparse
import json
import statistics
import sys
from pathlib import Path

import media
import project as pj

HOOK_MIN, HOOK_GAP, BODY_GAP = 0.60, 6.0, 30.0
SHORTS_BAND = (0.35, 0.55)
EDIT_FPS, MIN_DIST = 5, 12.0
EPS = 1e-6          # summed float intervals: a hook of exactly 60 % must pass


def merge(intervals) -> list:
    out = []
    for a, b in sorted((float(a), float(b)) for a, b in intervals if b > a):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [tuple(x) for x in out]


def coverage(intervals, a, b) -> float:
    return sum(max(0.0, min(y, b) - max(x, a)) for x, y in merge(intervals))


def gaps(intervals, a, b) -> list:
    """Uncovered stretches of [a, b], in order."""
    out, cur = [], a
    for x, y in merge(intervals):
        if y <= a or x >= b:
            continue
        if x > cur:
            out.append((cur, x))
        cur = max(cur, y)
    if cur < b:
        out.append((cur, b))
    return out


def _result(name, ok, value, detail):
    return {"name": name, "ok": bool(ok), "value": value, "detail": detail}


def evaluate(fmt, full_frame, duration, hook_end=pj.DEFAULT_HOOK_END, screen_share=(), other=()) -> list:
    """Density results for one timeline. full_frame/other/screen_share are [(start, end)] seconds."""
    if duration <= 0:
        raise ValueError("duration must be positive")
    if fmt == "shorts":
        share = coverage(full_frame, 0, duration) / duration
        lo, hi = SHORTS_BAND
        return [_result("full-frame share 35–55 %", lo - EPS <= share <= hi + EPS, round(share, 4),
                        f"{share:.1%} of {duration:.1f} s")]
    hook = min(hook_end, duration)
    share = coverage(full_frame, 0, hook) / hook
    hook_gaps = gaps(full_frame, 0, hook)
    longest = max((b - a for a, b in hook_gaps), default=0.0)
    over = [f"{a:.1f}–{b:.1f}" for a, b in hook_gaps if b - a > HOOK_GAP + EPS]
    covered = list(full_frame) + list(other) + list(screen_share)
    body_gaps = gaps(covered, hook, duration) if duration > hook else []
    body_longest = max((b - a for a, b in body_gaps), default=0.0)
    body_over = [f"{a:.1f}–{b:.1f}" for a, b in body_gaps if b - a > BODY_GAP + EPS]
    return [
        _result("hook graphics ≥ 60 %", share >= HOOK_MIN - EPS, round(share, 4), f"{share:.1%} of 0–{hook:g} s"),
        _result("hook face gaps ≤ 6 s", longest <= HOOK_GAP + EPS, round(longest, 2),
                f"longest {longest:.1f} s" + (f" ({', '.join(over)})" if over else "")),
        _result("body cadence ≤ 30 s", body_longest <= BODY_GAP + EPS, round(body_longest, 2),
                f"longest {body_longest:.1f} s" + (f" ({', '.join(body_over)})" if body_over else "")
                + (" · screen_share exempt" if screen_share else "")),
    ]


# ---------------------------------------------------------------- edit measurement

def otsu(values) -> float:
    hist = [0] * 256
    for v in values:
        hist[min(255, max(0, int(round(v))))] += 1
    total, sum_all = len(values), sum(i * h for i, h in enumerate(hist))
    best, cut, w0, sum0 = -1.0, 0, 0, 0.0
    for t in range(256):
        w0 += hist[t]
        if w0 == 0 or w0 == total:
            continue
        sum0 += t * hist[t]
        m0, m1 = sum0 / w0, (sum_all - sum0) / (total - w0)
        between = w0 * (total - w0) * (m0 - m1) ** 2
        if between > best:
            best, cut = between, t
    return cut + 0.5


def face_distances(video, fps=EDIT_FPS, face_ref=None) -> list:
    frames = media.gray_frames(video, fps)
    if not frames:
        raise media.MediaError(f"{video}: no frames decoded")
    if face_ref is None:
        ref = [statistics.median(f[p] for f in frames) for p in range(len(frames[0]))]
    else:
        k = min(len(frames) - 1, max(0, int(round(face_ref * fps))))
        ref = list(frames[k])
    n = len(ref)
    return [sum(abs(f[p] - ref[p]) for p in range(n)) / n for f in frames]


def graphic_intervals(distances, fps=EDIT_FPS, threshold=None) -> list:
    """Runs of samples whose distance exceeds the threshold, as [(start, end)] seconds."""
    t = threshold if threshold is not None else max(otsu(distances), MIN_DIST)
    out, start = [], None
    for i, d in enumerate(distances + [-1.0]):
        if d > t and start is None:
            start = i
        elif d <= t and start is not None:
            out.append((round(start / fps, 3), round(i / fps, 3)))
            start = None
    return out


# ---------------------------------------------------------------- reports

def report(project, edit=None, duration=None, face_ref=None, threshold=None) -> dict:
    project = Path(project)
    brief = pj.read_brief(project)
    fmt = brief.get("format")
    if fmt not in pj.FORMATS:
        raise pj.ProjectError(f"BRIEF format must be long-form or shorts, got {fmt!r}")
    rows = pj.read_storyboard(project)
    other = [(r["t_in"], r["t_out"]) for r in rows if r["placement"] == "over-footage"]
    if edit:
        full = graphic_intervals(face_distances(edit, face_ref=face_ref), threshold=threshold)
        duration = duration or media.video_info(edit)["duration"]
        source = f"edit: {edit}"
    else:
        full = [(r["t_in"], r["t_out"]) for r in rows if r["placement"] == "full-frame"]
        duration = duration or pj.transcript_duration(project)
        source = "plan: storyboard.md"
    if not duration:
        raise pj.ProjectError("no runtime: pass --duration or add transcript.json")
    share = pj.screen_share(brief) if fmt == "long-form" else []
    results = evaluate(fmt, full, duration, pj.hook_end(brief), share, other if fmt == "long-form" else ())
    return {"format": fmt, "source": source, "duration": duration, "hook_end": pj.hook_end(brief),
            "full_frame": merge(full), "over_footage": merge(other), "screen_share": share,
            "results": results, "ok": all(r["ok"] for r in results)}


def format_report(r) -> str:
    lines = [f"density ({r['format']}, {r['source']}, {r['duration']:.1f} s)"]
    for x in r["results"]:
        lines.append(f"  {'PASS' if x['ok'] else 'FAIL'}  {x['name']:<26} {x['detail']}")
    return "\n".join(lines)


def main(argv) -> int:
    ap = argparse.ArgumentParser(prog="python3 tools/cadence_scan.py")
    ap.add_argument("project")
    ap.add_argument("--edit")
    ap.add_argument("--duration", type=float)
    ap.add_argument("--face-ref", type=float)
    ap.add_argument("--threshold", type=float)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv[1:])
    try:
        r = report(a.project, a.edit, a.duration, a.face_ref, a.threshold)
    except (pj.ProjectError, media.MediaError, ValueError) as e:
        print(e)
        return 2
    print(json.dumps(r) if a.json else format_report(r))
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
````

- [ ] **Step 4: Run the tests**

Run: `python3 -m unittest discover -s tools -p 'test_cadence_scan.py' -v`
Expected: `Ran 13 tests … OK`. (Without `EPS`, `test_long_form_hook_share_boundary` fails: 10 × 4.8 s sums to 47.999… — Review Focus 1.)

- [ ] **Step 5: Document the command**

````bash
python3 - . <<'PY'
import sys
from pathlib import Path
ROOT = Path(sys.argv[1])

def edit(rel, pairs):
    p = ROOT / rel
    s = p.read_text()
    for a, b in pairs:
        assert s.count(a) == 1, (rel, a[:70])
        s = s.replace(a, b)
    p.write_text(s)

edit("standards/core/pipeline.md", [
("""Check density on the table (hook ≥ 60 %, body gaps ≤ 30 s, punch-ins don't count).""",
 """Check density on the table with `python3 tools/cadence_scan.py videos/<slug>` (hook ≥ 60 %, body gaps ≤ 30 s, punch-ins don't count)."""),
])
PY
````

Run: `python3 -m unittest discover -s tools -p 'test_*.py'` → `Ran 146 tests … FAILED (errors=14)`.

- [ ] **Step 6: Commit**

```bash
git add tools/cadence_scan.py tools/test_cadence_scan.py standards/core/pipeline.md
git commit -m "feat(tools): cadence_scan density check on the beat grid and on the edited timeline

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: `tools/slice.py` — long-form delivery

Port of video 09's `scripts/slice.mjs`: frame-exact silent MP4 per full-frame scene (`-ss` on the exact frame boundary, `-frames:v N`, libx264 CRF 14, yuv420p, faststart), named `scene-NN_MM-SS-FF.mp4` by timeline timecode, plus each over-footage MOV verified as ProRes 4444 with alpha and renamed `overlay-NN_MM-SS-FF.mov`, `TIMECODES.csv` (09's columns plus `kind`) and `README.txt`. Placement comes from the beat grid; every reel slot / overlay file must agree with its row's duration within 1.5 frames, or nothing is written.

**Files:**
- Create: `tools/slice.py`, `tools/test_slice.py`
- Modify: `standards/core/pipeline.md`, `standards/formats/long-form.md`

**Interfaces:**
- Consumes: `project.read_brief`, `read_storyboard`, `composition_slots` (Task 4); `media.video_info`, `run`, `tool` (Task 6); `synth.moving`, `segments`, `prores` (tests).
- Produces: `slice.SliceError`; `slice.COLUMNS` (`kind, scene, file, timeline_in_tc, timeline_out_tc, timeline_in_s, timeline_out_s, in_frame, out_frame, duration_s, frames, title`); `slice.tc(seconds, fps) -> "HH:MM:SS:FF"`; `slice.tc_file(seconds, fps) -> "MM-SS-FF"` (`HH-MM-SS-FF` past an hour); `slice.plan(project, reel, overlays_dir=None, fps=30.0) -> [clip]`; `slice.slice_project(project, reel, overlays_dir=None, out_dir=None, fps=30.0) -> [csv row]`; CLI `python3 tools/slice.py videos/<slug> --reel R [--overlays DIR] [--out DIR] [--fps 30]`.

- [ ] **Step 1: Write the failing test**

Create `tools/test_slice.py`:

````python
import csv
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import media
import slice as sl
import synth

HEADER = "| t_in | t_out | words | placement | type | beats | ease | marks |\n|---|---|---|---|---|---|---|---|\n"
INDEX = """<div id="root" data-composition-id="main" data-hf-mode="dark">
  <div data-composition-id="01-hook" data-composition-src="compositions/01-hook.html" data-start="0" data-duration="2"></div>
  <div data-composition-id="02-proof" data-composition-src="compositions/02-proof.html" data-start="2" data-duration="2"></div>
</div>"""
GRID = HEADER + (
    '| 10.0 | 12.0 | "the hook" | full-frame | B1 | — | ease.enter | — |\n'
    '| 20.0 | 21.0 | "key line" | over-footage | lower-third | — | ease.enter | — |\n'
    '| 30.5 | 32.5 | "the proof" | full-frame | A1 | — | ease.enter | highlight-block |\n')


class TimecodeTests(unittest.TestCase):
    def test_tc(self):
        self.assertEqual(sl.tc(96.5, 30), "00:01:36:15")
        self.assertEqual(sl.tc_file(96.5, 30), "01-36-15")
        self.assertEqual(sl.tc_file(3725.0, 30), "01-02-05-00")


@unittest.skipUnless(synth.HAVE_FFMPEG, "ffmpeg/ffprobe not installed")
class SliceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        self.p = d / "10-demo"
        self.p.mkdir()
        (self.p / "BRIEF.md").write_text("```yaml\nformat: long-form\n```\n")
        (self.p / "index.html").write_text(INDEX)
        (self.p / "storyboard.md").write_text(GRID)
        self.reel = synth.moving(d / "reel.mp4", 4)
        self.overlays = d / "overlays"
        self.overlays.mkdir()
        synth.prores(self.overlays / "01-key-line.mov", 1)

    def tearDown(self):
        self.tmp.cleanup()

    def test_clips_csv_and_readme(self):
        stale = self.p / "deliver" / "scene-09_00-00-00.mp4"
        stale.parent.mkdir()
        stale.write_text("old")
        rows = sl.slice_project(self.p, self.reel, self.overlays)
        out = self.p / "deliver"
        self.assertEqual([r["file"] for r in rows], ["scene-01_00-10-00.mp4", "scene-02_00-30-15.mp4", "overlay-01_00-20-00.mov"])
        self.assertFalse(stale.exists(), "a re-slice removes stale clips")
        for name in ("scene-01_00-10-00.mp4", "scene-02_00-30-15.mp4"):
            info = media.video_info(out / name)
            self.assertEqual((info["frames"], info["codec"], info["pix_fmt"]), (60, "h264", "yuv420p"), name)
        self.assertEqual(media.video_info(out / "overlay-01_00-20-00.mov")["codec"], "prores")
        with open(out / "TIMECODES.csv") as f:
            csv_rows = list(csv.DictReader(f))
        self.assertEqual(list(csv_rows[0]), sl.COLUMNS)
        self.assertEqual(csv_rows[1]["timeline_in_tc"], "00:00:30:15")
        self.assertEqual(csv_rows[1]["timeline_out_tc"], "00:00:32:15")
        self.assertEqual((csv_rows[1]["in_frame"], csv_rows[1]["out_frame"], csv_rows[1]["title"]), ("915", "975", "the proof"))
        self.assertEqual(csv_rows[2]["kind"], "over-footage")
        readme = (out / "README.txt").read_text()
        self.assertIn("scene-01_00-10-00.mp4  ->  drop at 00:00:10:00", readme)
        self.assertIn("ProRes 4444 with alpha", readme)

    def test_cut_is_frame_exact_at_scene_boundaries(self):
        reel = synth.segments(Path(self.tmp.name) / "two.mp4", [("red", 2), ("blue", 2)])
        sl.slice_project(self.p, reel, self.overlays)
        first = media.gray_frames(self.p / "deliver" / "scene-01_00-10-00.mp4", 30)
        second = media.gray_frames(self.p / "deliver" / "scene-02_00-30-15.mp4", 30)
        ref = media.gray_frames(reel, 1)
        red, blue = ref[1][0], ref[3][0]
        self.assertGreater(abs(red - blue), 20)
        self.assertEqual((len(first), len(second)), (60, 60))
        self.assertLess(abs(first[-1][0] - red), 4, "scene 1 ends on its own last frame")
        self.assertLess(abs(second[0][0] - blue), 4, "scene 2 starts on its own first frame")

    def test_duration_mismatch_names_slot_and_row(self):
        (self.p / "storyboard.md").write_text(GRID.replace("| 30.5 | 32.5 |", "| 30.5 | 33.5 |"))
        with self.assertRaisesRegex(sl.SliceError, r"slot 02-proof lasts 2\.00 s but storyboard row 3 \(line 5\) lasts 3\.00 s"):
            sl.plan(self.p, self.reel, self.overlays)

    def test_count_mismatch(self):
        (self.p / "storyboard.md").write_text(HEADER + '| 10.0 | 12.0 | "x" | full-frame | B1 | — | — | — |\n')
        with self.assertRaisesRegex(sl.SliceError, "2 scene slots but storyboard.md has 1 full-frame rows"):
            sl.plan(self.p, self.reel)

    def test_overlay_must_be_prores_4444_alpha(self):
        (self.overlays / "01-key-line.mov").unlink()
        synth.prores(self.overlays / "01-key-line.mov", 1, alpha=False)
        with self.assertRaisesRegex(sl.SliceError, "not ProRes 4444 with alpha"):
            sl.plan(self.p, self.reel, self.overlays)

    def test_missing_overlays_dir(self):
        with self.assertRaisesRegex(sl.SliceError, r"1 over-footage rows but \(no --overlays dir\) has 0 \.mov files"):
            sl.plan(self.p, self.reel)

    def test_shorts_are_refused(self):
        (self.p / "BRIEF.md").write_text("```yaml\nformat: shorts\n```\n")
        with self.assertRaisesRegex(sl.SliceError, "one finished MP4"):
            sl.plan(self.p, self.reel)

    def test_cli(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(sl.main(["slice.py", str(self.p), "--reel", str(self.reel), "--overlays", str(self.overlays)]), 0)
            self.assertEqual(sl.main(["slice.py", str(self.p), "--reel", str(self.reel)]), 1)
        self.assertIn("3 clips + TIMECODES.csv + README.txt", out.getvalue())


if __name__ == "__main__":
    unittest.main()
````

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 -m unittest discover -s tools -p 'test_slice.py' -v`
Expected: ERROR — `ModuleNotFoundError: No module named 'slice'`.

- [ ] **Step 3: Write the slicer**

Create `tools/slice.py`:

````python
"""Package a long-form graphics render for the editor: clips named by timeline timecode + TIMECODES.csv + README.

Full-frame scenes: the rendered reel (index.html, one slot per scene in timeline order) is cut into
frame-exact silent MP4s. Over-footage layouts: each is its own composition rendered as ProRes 4444
with alpha (`npx hyperframes render -c compositions/overlays/<name>.html --format=mov -o
renders/overlays/<name>.mov`); slice verifies and renames them. Timeline placement comes from the
storyboard.md beat grid: full-frame rows pair with reel slots in order, over-footage rows with the
overlay files in name order, and every pairing must agree on duration (±1.5 frames).
Ported from video 09's scripts/slice.mjs. Delivery rules: standards/formats/long-form.md.

Usage: python3 tools/slice.py videos/<slug> --reel renders/reel.mp4 [--overlays renders/overlays]
                              [--out deliver] [--fps 30]
"""
import argparse
import csv
import shutil
import sys
from pathlib import Path

import media
import project as pj

COLUMNS = ["kind", "scene", "file", "timeline_in_tc", "timeline_out_tc", "timeline_in_s", "timeline_out_s",
           "in_frame", "out_frame", "duration_s", "frames", "title"]
TOLERANCE_FRAMES = 1.5


class SliceError(Exception):
    """A pairing or input that would produce wrong clips. Nothing is written when this is raised."""


def tc(seconds: float, fps: float) -> str:
    f = round(seconds * fps)
    ifps = round(fps)
    s = f // ifps
    return f"{s // 3600:02d}:{s // 60 % 60:02d}:{s % 60:02d}:{f % ifps:02d}"


def tc_file(seconds: float, fps: float) -> str:
    t = tc(seconds, fps).replace(":", "-")
    return t[3:] if t.startswith("00-") else t


def _title(words: str) -> str:
    return words.strip().strip('"“”').strip()


def plan(project, reel, overlays_dir=None, fps=30.0) -> list:
    """Every clip to write, as dicts (one per TIMECODES.csv row plus the cut/copy source). Raises SliceError."""
    project = Path(project)
    if pj.read_brief(project).get("format") != "long-form":
        raise SliceError("slice is for long-form; a Short is delivered as one finished MP4 (render it to deliver/<slug>.mp4)")
    rows = pj.read_storyboard(project)
    full = sorted((r for r in rows if r["placement"] == "full-frame"), key=lambda r: r["t_in"])
    over = sorted((r for r in rows if r["placement"] == "over-footage"), key=lambda r: r["t_in"])
    slots = pj.composition_slots(project)
    if len(slots) != len(full):
        raise SliceError(f"index.html has {len(slots)} scene slots but storyboard.md has {len(full)} full-frame rows")
    reel_info = media.video_info(reel)
    clips, tol = [], TOLERANCE_FRAMES / fps
    for n, (slot, row) in enumerate(zip(slots, full), 1):
        want = row["t_out"] - row["t_in"]
        if abs(slot["dur"] - want) > tol:
            raise SliceError(f"slot {slot['id']} lasts {slot['dur']:.2f} s but storyboard row {row['row']} "
                             f"(line {row['line']}) lasts {want:.2f} s — fix one so they agree")
        if slot["start"] + slot["dur"] > reel_info["duration"] + tol:
            raise SliceError(f"slot {slot['id']} ends at {slot['start'] + slot['dur']:.2f} s, after the reel ({reel_info['duration']:.2f} s) — re-render")
        clips.append({"kind": "full-frame", "scene": slot["id"], "n": n, "t_in": row["t_in"],
                      "frames": round(slot["dur"] * fps), "src_start": slot["start"], "title": _title(row["words"]),
                      "file": f"scene-{n:02d}_{tc_file(row['t_in'], fps)}.mp4"})
    movs = sorted(Path(overlays_dir).glob("*.mov")) if overlays_dir else []
    if len(movs) != len(over):
        raise SliceError(f"storyboard.md has {len(over)} over-footage rows but "
                         f"{overlays_dir or '(no --overlays dir)'} has {len(movs)} .mov files")
    for n, (mov, row) in enumerate(zip(movs, over), 1):
        info = media.video_info(mov)
        if info["codec"] != "prores" or "4444" not in str(info["profile"]) or not str(info["pix_fmt"]).startswith("yuva"):
            raise SliceError(f"{mov.name} is {info['codec']} {info['profile']} {info['pix_fmt']}, not ProRes 4444 with alpha "
                             "— render it with npx hyperframes render --format=mov")
        want = row["t_out"] - row["t_in"]
        if abs(info["duration"] - want) > tol:
            raise SliceError(f"{mov.name} lasts {info['duration']:.2f} s but storyboard row {row['row']} "
                             f"(line {row['line']}) lasts {want:.2f} s")
        clips.append({"kind": "over-footage", "scene": mov.stem, "n": n, "t_in": row["t_in"],
                      "frames": round(info["duration"] * fps), "src": mov, "title": _title(row["words"]),
                      "file": f"overlay-{n:02d}_{tc_file(row['t_in'], fps)}.mov"})
    return clips


def _cut(reel, clip, out, fps):
    start = round(clip["src_start"] * fps) / fps
    media.run([media.tool("ffmpeg"), "-nostdin", "-v", "error", "-y", "-ss", f"{start:.6f}", "-i", str(reel),
                "-frames:v", str(clip["frames"]), "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "14",
                "-pix_fmt", "yuv420p", "-r", f"{fps:g}", "-movflags", "+faststart", str(out)])


def _readme(slug, clips, fps):
    full = [c for c in clips if c["kind"] == "full-frame"]
    over = [c for c in clips if c["kind"] == "over-footage"]
    example = (f"      {full[0]['file']}  ->  drop at {tc(full[0]['t_in'], fps)}\n" if full else "")
    return (f"{slug} — graphics for the basic-edit timeline\n"
            f"{len(full)} full-screen scene clip(s), {len(over)} over-footage layout(s).\n\n"
            "HOW TO USE\n"
            "  Each file is named with the timecode it goes at on your basic-edit timeline:\n"
            f"{example}"
            "  scene-*.mp4: full-screen graphics, silent, hard cut in and out. Drop each on a video track\n"
            "  above the talking head at its timecode. Keep your edit audio underneath.\n"
            "  overlay-*.mov: ProRes 4444 with alpha. Place above the talking head at its timecode; the\n"
            "  footage shows through everywhere outside the layout.\n\n"
            "  TIMECODES.csv has the same information for every clip: in/out timecode, in/out frame,\n"
            f"  duration and frame count ({fps:g} fps).\n")


def slice_project(project, reel, overlays_dir=None, out_dir=None, fps=30.0) -> list:
    project = Path(project)
    clips = plan(project, reel, overlays_dir, fps)
    out = Path(out_dir) if out_dir else project / "deliver"
    out.mkdir(parents=True, exist_ok=True)
    for old in list(out.glob("scene-*.mp4")) + list(out.glob("overlay-*.mov")):
        old.unlink()   # slice owns these names; a re-slice must not leave stale clips behind
    rows = []
    for c in clips:
        if c["kind"] == "full-frame":
            _cut(reel, c, out / c["file"], fps)
        else:
            shutil.copyfile(c["src"], out / c["file"])
        in_f = round(c["t_in"] * fps)
        out_f = in_f + c["frames"]
        rows.append({"kind": c["kind"], "scene": c["scene"], "file": c["file"], "timeline_in_tc": tc(c["t_in"], fps),
                     "timeline_out_tc": tc(out_f / fps, fps), "timeline_in_s": f"{c['t_in']:.2f}",
                     "timeline_out_s": f"{out_f / fps:.2f}", "in_frame": in_f, "out_frame": out_f,
                     "duration_s": f"{c['frames'] / fps:.2f}", "frames": c["frames"], "title": c["title"]})
    with open(out / "TIMECODES.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    (out / "README.txt").write_text(_readme(project.name, clips, fps))
    return rows


def main(argv) -> int:
    ap = argparse.ArgumentParser(prog="python3 tools/slice.py")
    ap.add_argument("project")
    ap.add_argument("--reel", required=True)
    ap.add_argument("--overlays")
    ap.add_argument("--out")
    ap.add_argument("--fps", type=float, default=30.0)
    a = ap.parse_args(argv[1:])
    try:
        rows = slice_project(a.project, a.reel, a.overlays, a.out, a.fps)
    except (SliceError, pj.ProjectError, media.MediaError) as e:
        print(e)
        return 1
    for r in rows:
        print(f"{r['file']:<28} -> timeline {r['timeline_in_tc']}  ({r['frames']} frames)")
    print(f"{len(rows)} clips + TIMECODES.csv + README.txt -> {a.out or Path(a.project) / 'deliver'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
````

- [ ] **Step 4: Run the tests**

Run: `python3 -m unittest discover -s tools -p 'test_slice.py' -v`
Expected: `Ran 9 tests … OK`.

- [ ] **Step 5: Document the render + slice commands**

````bash
python3 - . <<'PY'
import sys
from pathlib import Path
ROOT = Path(sys.argv[1])

def edit(rel, pairs):
    p = ROOT / rel
    s = p.read_text()
    for a, b in pairs:
        assert s.count(a) == 1, (rel, a[:70])
        s = s.replace(a, b)
    p.write_text(s)

edit("standards/core/pipeline.md", [
("""   over-footage layouts as separate transparent compositions. Use `lib/kit` and the""",
 """   over-footage layouts as standalone transparent documents in `compositions/overlays/` (no `<template>`
   wrapper — each renders on its own with `-c`). Use `lib/kit` and the"""),
("""8. **Render and slice.** Full-frame: silent MP4 clips + `TIMECODES.csv` + README. Over-footage:
   ProRes 4444 with alpha. Into `deliver/`, then the shared drive (media never goes into Git).""",
 """8. **Render and slice.** `npx hyperframes render videos/<slug> -o videos/<slug>/renders/reel.mp4`; each
   over-footage layout `npx hyperframes render videos/<slug> -c compositions/overlays/<name>.html --format=mov
   -o videos/<slug>/renders/overlays/<name>.mov`; then `python3 tools/slice.py videos/<slug> --reel
   videos/<slug>/renders/reel.mp4 --overlays videos/<slug>/renders/overlays`. Full-frame: silent MP4 clips +
   `TIMECODES.csv` + README. Over-footage: ProRes 4444 with alpha. Into `deliver/`, then the shared
   drive (media never goes into Git)."""),
("""8. **Render** one finished MP4; hand off as above.""",
 """8. **Render** one finished MP4 (`npx hyperframes render videos/<slug> -o videos/<slug>/deliver/<slug>.mp4`); hand off as above."""),
])
edit("standards/formats/long-form.md", [
("""- **Over-footage layouts:** ProRes 4444 with alpha (`npx hyperframes render --format=mov`).
- Hand-off to the shared drive; media never goes into Git.""",
 """- **Over-footage layouts:** ProRes 4444 with alpha (`npx hyperframes render --format=mov`).
- `python3 tools/slice.py videos/<slug> --reel <reel.mp4> --overlays <dir>` cuts the clips frame-exact,
  verifies the overlays and writes `TIMECODES.csv` + `README.txt` into `deliver/`.
- Hand-off to the shared drive; media never goes into Git."""),
])
PY
````

Run: `python3 -m unittest discover -s tools -p 'test_*.py'` → `Ran 155 tests … FAILED (errors=14)`.

- [ ] **Step 6: Commit**

```bash
git add tools/slice.py tools/test_slice.py standards/core/pipeline.md standards/formats/long-form.md
git commit -m "feat(tools): slice long-form renders into timecoded clips, ProRes 4444 overlays and TIMECODES.csv

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 9: Runtime probe — `qa_probe.mjs` + `runtime_probe.py`

The roadmap's binding note: blur-reason tags set at runtime by lib are invisible to static scans, so check 5 must inspect the live DOM, and the easing check reads every timeline child through `HFProfile.isProfileEase` and flags tweens with no ease. The probe also finds the two render-only text traps (`shorts.md` §9b) from computed styles. `runtime_probe.probe_project` serves the project with `npx hyperframes preview --background` (bundler + runtime, so sub-compositions mount and nest as they render) and stops the preview only if it started it. Prototype evidence: on a real scaffold with HyperFrames 0.8.29, GSAP and lib binders (`HFText.defocus`, `HFText.words`, `HFMarks.highlight`), the probe reported exactly the one seeded `ease: "power2.out"` tween and nothing from lib.

**Files:**
- Create: `tools/qa_probe.mjs`, `tools/runtime_probe.py`, `tools/test_runtime_probe.py`

**Interfaces:**
- Consumes: `HFProfile.isProfileEase` (in the page, from the synced `lib/profile.js`), `window.__timelines`, `HFText.ready()` when present; GSAP's `timeline.getChildren(true, true, false)`, `tween.vars`, `duration()`, `startTime()`, `targets()`, `parent`, `seek()`.
- Produces:
  - `node tools/qa_probe.mjs --url URL --format F --chrome PATH [--width W --height H] [--samples N] [--timeout MS]` → stdout JSON `{"timelines", "tweens", "samples", "duration", "findings": [{"check": 5|6|10, "message", "t"}], "errors"}`; exit 2 with a message on stderr when the page cannot be probed.
  - `runtime_probe.ProbeError`; `runtime_probe.hyperframes_cmd() -> list` (`$HF_CLI` or `npx --yes hyperframes`); `runtime_probe.find_chrome(allow_npx=True) -> str | None` (`$HF_CHROME`, `~/.cache/puppeteer/chrome-headless-shell/*/*/chrome-headless-shell`, then `npx hyperframes browser path`).
  - `runtime_probe.probe_url(url, fmt, size, chrome=None, samples=24, timeout_ms=30000) -> dict`; `runtime_probe.probe_project(project, fmt, size, port=3930, **kw) -> dict`.

- [ ] **Step 1: Write the failing test**

Create `tools/test_runtime_probe.py` (the page uses a stand-in for GSAP with exactly the API the probe reads, so the test runs offline):

````python
import functools
import http.server
import shutil
import tempfile
import threading
import unittest
from pathlib import Path

import runtime_probe as rp

ROOT = Path(__file__).resolve().parents[1]
CHROME = rp.find_chrome(allow_npx=False)

# A stand-in for GSAP with exactly the API qa_probe reads: getChildren / vars / duration / startTime /
# targets / parent / seek. seek(t) fires every onUpdate, the way a driver tween renders.
FAKE_GSAP = """
function Tween(target, vars, at, parent) { this._t = [target]; this.vars = vars; this._at = at; this.parent = parent; }
Tween.prototype.duration = function () { return this.vars.duration || 0; };
Tween.prototype.startTime = function () { return this._at; };
Tween.prototype.targets = function () { return this._t; };
function TL(vars) { this.vars = vars || {}; this.kids = []; this.parent = null; }
TL.prototype.to = function (target, vars, at) { this.kids.push(new Tween(target, vars, at, this)); return this; };
TL.prototype.set = function (target, vars, at) { return this.to(target, Object.assign({ duration: 0 }, vars), at); };
TL.prototype.getChildren = function () { return this.kids; };
TL.prototype.duration = function () { return Math.max.apply(null, [0].concat(this.kids.map(function (k) { return k._at + k.duration(); }))); };
TL.prototype.seek = function (t) { this.kids.forEach(function (k) { if (k.vars.onUpdate) k.vars.onUpdate(t); }); return this; };
"""

PAGE = """<!doctype html><html><head><meta charset="utf-8">
<script src="profile.js"></script><script>%s</script>
<style>
  .grad { background: linear-gradient(90deg, #fff, #888); -webkit-background-clip: text; background-clip: text;
          color: transparent; font-size: 40px; line-height: 1.0; }
  .centred { text-align: center; line-height: 1.4; }
</style></head><body>
<div id="root" data-composition-id="main" data-duration="4">
  <svg width="0" height="0"><filter id="f1"><feGaussianBlur id="bare" stdDeviation="3"/></filter>
    <filter id="f2"><feGaussianBlur id="glow" data-blur-reason="glow" stdDeviation="3"/></filter>
    <filter id="f3"><feGaussianBlur id="smear" data-blur-reason="wipe" stdDeviation="8 0"/></filter></svg>
  <div id="late"></div><div id="tagged"></div>
  <p id="cropped" class="grad">Cropped</p>
  <p id="ghost" class="grad centred"><span style="transform: translateY(4px)">Ghost</span></p>
</div>
<script>
  var E = function (t) { return HFProfile.ease("long-form", t); };
  var tl = new TL();
  tl.to("#a", { x: 1, duration: 1, ease: E("ease.enter") }, 0);            // ok
  tl.to("#b", { x: 1, duration: 1 }, 0.5);                                 // no ease
  tl.to("#c", { x: 1, duration: 1, ease: "power2.out" }, 1);               // raw string
  tl.to("#d", { x: 1, duration: 1, ease: function (p) { return p; } }, 1); // foreign function
  tl.to("#e", { x: 1, duration: 1, ease: "none" }, 2);                     // linear, not a driver
  tl.set("#f", { x: 0 }, 0);                                               // set: nothing to ease
  var late = document.getElementById("late"), tagged = document.getElementById("tagged");
  tagged.setAttribute("data-blur-reason", "focus");                       // set at runtime, like lib does
  tl.to({ t: 0 }, { t: 1, duration: 4, ease: "none", onUpdate: function (t) {   // a driver: allowed
    late.style.filter = t > 1.5 ? "blur(4px)" : "none";                   // untagged blur appears mid-timeline
    tagged.style.filter = "blur(2px)";
  } }, 0);
  var withDefaults = new TL({ defaults: { ease: E("ease.camera") } });
  withDefaults.to("#g", { x: 1, duration: 1 }, 0);                         // inherits the profile ease
  window.__timelines = { main: tl, other: withDefaults };
</script></body></html>""" % FAKE_GSAP


@unittest.skipUnless(CHROME and shutil.which("node"), "needs node and chrome-headless-shell (npx hyperframes browser ensure)")
class ProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        d = Path(cls.tmp.name)
        shutil.copyfile(ROOT / "lib" / "profile.js", d / "profile.js")
        (d / "index.html").write_text(PAGE)
        (d / "empty.html").write_text("<!doctype html><p>no timelines</p>")
        handler = functools.partial(QuietHandler, directory=str(d))
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        cls.result = rp.probe_url(cls.base + "/index.html", "long-form", (1920, 1080), samples=9, timeout_ms=10000)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.tmp.cleanup()

    def messages(self, check):
        return [f["message"] for f in self.result["findings"] if f["check"] == check]

    def test_counts(self):
        self.assertEqual(self.result["timelines"], 2)
        self.assertEqual(self.result["tweens"], 8)
        self.assertEqual(self.result["samples"], 9)

    def test_eases(self):
        m = self.messages(6)
        self.assertEqual(len(m), 4, m)
        self.assertTrue(any("#b" in x and "has no ease" in x for x in m), m)
        self.assertTrue(any('raw ease "power2.out"' in x for x in m), m)
        self.assertTrue(any("not an HFProfile.ease token" in x for x in m), m)
        self.assertTrue(any("#e" in x and "is linear but is not a driver" in x for x in m), m)

    def test_blur_reasons_seen_at_runtime(self):
        m = self.messages(5)
        self.assertIn("main feGaussianBlur#bare: feGaussianBlur without data-blur-reason", m)
        self.assertIn('main feGaussianBlur#smear: data-blur-reason "wipe" is Shorts-only', m)
        late = [f for f in self.result["findings"] if "div#late" in f["message"]]
        self.assertEqual(len(late), 1, self.result["findings"])
        self.assertGreater(late[0]["t"], 1.5, "found by seeking, not in the load-time DOM")
        self.assertFalse([x for x in m if "#tagged" in x or "#glow" in x], m)
        self.assertTrue(any("directional Gaussian" in x for x in m), m)

    def test_render_traps(self):
        m = self.messages(10)
        self.assertTrue(any("p#cropped" in x and "line-height 1" in x for x in m), m)
        self.assertTrue(any("p#ghost" in x and "ghosts in the render" in x for x in m), m)

    def test_page_without_timelines_is_an_error(self):
        with self.assertRaisesRegex(rp.ProbeError, "no timeline registered"):
            rp.probe_url(self.base + "/empty.html", "long-form", (640, 360), samples=2, timeout_ms=1500)


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class CliPrefixTests(unittest.TestCase):
    def test_hf_cli_override(self):
        import os
        old = os.environ.get("HF_CLI")
        os.environ["HF_CLI"] = "npx --yes hyperframes@0.8.29"
        try:
            self.assertEqual(rp.hyperframes_cmd(), ["npx", "--yes", "hyperframes@0.8.29"])
        finally:
            if old is None:
                del os.environ["HF_CLI"]
            else:
                os.environ["HF_CLI"] = old


if __name__ == "__main__":
    unittest.main()
````

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 -m unittest discover -s tools -p 'test_runtime_probe.py' -v`
Expected: ERROR — `ModuleNotFoundError: No module named 'runtime_probe'`. (If chrome-headless-shell is missing, run `npx hyperframes browser ensure` first; otherwise the probe tests skip.)

- [ ] **Step 3: Write the probe and its wrapper**

Create `tools/qa_probe.mjs`:

````javascript
// qa_probe — the runtime half of QA checks 5, 6 and 10. Node ≥ 22 built-ins only (global WebSocket + fetch).
//
//   node tools/qa_probe.mjs --url URL --format long-form|shorts --chrome PATH [--width 1920 --height 1080]
//                           [--samples 24] [--timeout 30000]
//   → prints {"timelines", "tweens", "samples", "findings": [{check, message, t}], "errors": [...]} as JSON.
//   Exit 0 when the page was probed (findings or not), 2 when it could not be (message on stderr).
//
// Why a live page: lib binders set data-blur-reason with setAttribute and pick eases at runtime, so a
// static scan cannot see them. tools/qa.py serves the project through `npx hyperframes preview` (the
// HyperFrames bundler + runtime, so sub-compositions mount and timelines nest exactly as they render),
// and this script drives a headless Chrome over the DevTools protocol: it waits for the timelines to
// register (and HFText.ready()), reads every tween's ease, then seeks through the timeline and
// inspects the DOM at each sample for blur reasons and the two render-only text traps.
import { spawn } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

// Runs inside the page. Must be self-contained (it is serialised with Function.prototype.toString).
async function pageProbe(opts) {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const deadline = Date.now() + opts.timeout;
  let last = -1, stableSince = 0;
  for (;;) {   // timelines register asynchronously (sub-compositions, fonts): wait for a stable count
    const n = Object.keys(window.__timelines || {}).length;
    if (n > 0 && n === last) { if (Date.now() - stableSince > 500) break; } else { last = n; stableSince = Date.now(); }
    if (Date.now() > deadline) return { error: n ? "timelines kept changing until the timeout" : "no timeline registered on window.__timelines" };
    await sleep(100);
  }
  if (window.HFText && typeof window.HFText.ready === "function") await window.HFText.ready();

  const findings = [], keys = new Set();
  const r2 = (x) => Math.round(x * 100) / 100;
  function add(check, message, t) { const k = check + "|" + message; if (!keys.has(k)) { keys.add(k); findings.push({ check, message, t: t == null ? null : r2(t) }); } }
  function describe(el) {
    if (!el || !el.tagName) return String(el);
    let d = (el.localName || el.tagName.toLowerCase()) + (el.id ? "#" + el.id : "");
    if (!el.id && typeof el.className === "string" && el.className.trim()) d += "." + el.className.trim().split(/\s+/)[0];
    const comp = el.closest && el.closest("[data-composition-id]");
    return comp && comp !== el ? comp.getAttribute("data-composition-id") + " " + d : d;
  }
  const tls = window.__timelines, ids = Object.keys(tls);
  const HP = window.HFProfile;

  // Check 6 — every tween with a duration uses an HFProfile.ease token (or "none" on a driver tween).
  const seen = new Set();
  for (const id of ids) {
    const tl = tls[id];
    if (!tl || typeof tl.getChildren !== "function") continue;
    for (const tw of tl.getChildren(true, true, false)) {
      if (seen.has(tw)) continue;
      seen.add(tw);
      if (!(tw.duration() > 0)) continue;
      let ease = tw.vars.ease, p = tw.parent;
      while (ease === undefined && p) { ease = p.vars && p.vars.defaults ? p.vars.defaults.ease : undefined; p = p.parent; }
      const targets = typeof tw.targets === "function" ? tw.targets() : [];
      const label = `${id}: tween on ${describe(targets[0])} at ${r2(tw.startTime())} s`;
      if (ease === undefined) add(6, `${label} has no ease (GSAP's default power1.out is not in the vocabulary)`);
      else if (typeof ease === "function") { if (!(HP && HP.isProfileEase(ease))) add(6, `${label} uses an ease function that is not an HFProfile.ease token`); }
      else if (ease === "none" || ease === "linear") { if (!tw.vars.onUpdate) add(6, `${label} is linear but is not a driver tween (drivers have onUpdate)`); }
      else add(6, `${label} uses the raw ease ${JSON.stringify(ease)} — use HFProfile.ease(format, token)`);
    }
  }

  // Seek plan: the root composition's timeline drives nested children; timelines outside it are seeked too.
  const rootEl = document.querySelector("[data-composition-id]");
  const rootId = rootEl && rootEl.getAttribute("data-composition-id");
  const rootTl = tls[rootId] || null;
  const nestedIn = (tl, anc) => { for (let p = tl.parent; p; p = p.parent) if (p === anc) return true; return false; };
  const drivers = ids.map((id) => tls[id]).filter((tl) => tl && typeof tl.seek === "function" && (tl === rootTl || !rootTl || !nestedIn(tl, rootTl)));
  const attrDur = rootEl ? parseFloat(rootEl.getAttribute("data-duration")) : NaN;
  const dur = Number.isFinite(attrDur) && attrDur > 0 ? attrDur : Math.max(0, ...drivers.map((tl) => tl.duration()));
  const n = Math.max(2, opts.samples);
  const times = Array.from({ length: n }, (_, i) => Math.min(dur, (dur * i) / (n - 1)));

  const REASONS = ["focus", "glow", "wipe"];
  function reasonProblem(el, why) {
    const r = el.getAttribute("data-blur-reason");
    if (!r) return `${describe(el)}: ${why} without data-blur-reason`;
    if (!REASONS.includes(r)) return `${describe(el)}: data-blur-reason "${r}" is not focus, glow or wipe`;
    if (r === "wipe" && opts.format !== "shorts") return `${describe(el)}: data-blur-reason "wipe" is Shorts-only`;
    return null;
  }
  for (const t of times) {
    for (const tl of drivers) tl.seek(tl === rootTl || !rootTl ? t : Math.min(t, tl.duration()), false);
    for (const el of document.querySelectorAll("*")) {
      if (el.tagName === "feGaussianBlur") {
        const bad = reasonProblem(el, "feGaussianBlur");
        if (bad) add(5, bad, t);
        const sd = String(el.getAttribute("stdDeviation") || "0").trim().split(/[\s,]+/).map(parseFloat);
        if (sd.length === 2 && sd[0] !== sd[1] && !(opts.format === "shorts" && el.getAttribute("data-blur-reason") === "wipe")) {
          add(5, `${describe(el)}: directional Gaussian (stdDeviation "${sd.join(" ")}") is movement blur — use HFMotionBlur`, t);
        }
        continue;
      }
      const cs = getComputedStyle(el);
      for (const prop of ["filter", "backdropFilter"]) {
        if (String(cs[prop] || "").includes("blur(")) { const bad = reasonProblem(el, `CSS ${prop} blur()`); if (bad) add(5, bad, t); }
      }
      if (cs.backgroundClip === "text" || cs.webkitBackgroundClip === "text") {
        const lh = parseFloat(cs.lineHeight), fs = parseFloat(cs.fontSize);
        if (Number.isFinite(lh) && Number.isFinite(fs) && lh < 1.3 * fs - 0.01) {
          add(10, `${describe(el)}: gradient text with line-height ${r2(lh / fs)}× the font size crops its glyphs — keep ≥ 1.3 (shorts.md §9b trap 2)`, t);
        }
        if (cs.textAlign === "center" && [...el.querySelectorAll("*")].some((c) => c.style && c.style.transform)) {
          add(10, `${describe(el)}: centred gradient text with transformed word spans ghosts in the render — use a solid colour (shorts.md §9b trap 1)`, t);
        }
      }
    }
  }
  return { timelines: ids.length, tweens: seen.size, samples: times.length, duration: dur, findings };
}

function args(argv) {
  const a = { samples: 24, timeout: 30000, width: 1920, height: 1080 };
  for (let i = 0; i < argv.length; i++) {
    const k = argv[i].replace(/^--/, "");
    a[k] = ["samples", "timeout", "width", "height"].includes(k) ? Number(argv[++i]) : argv[++i];
  }
  return a;
}

async function waitFor(fn, ms, what) {
  const end = Date.now() + ms;
  for (;;) {
    const v = await fn();
    if (v) return v;
    if (Date.now() > end) throw new Error("timed out waiting for " + what);
    await new Promise((r) => setTimeout(r, 100));
  }
}

async function main() {
  const a = args(process.argv.slice(2));
  if (!a.url || !["long-form", "shorts"].includes(a.format) || !a.chrome) {
    process.stderr.write("usage: node tools/qa_probe.mjs --url URL --format long-form|shorts --chrome PATH [--width W --height H] [--samples N]\n");
    return 2;
  }
  if (typeof WebSocket === "undefined") { process.stderr.write("qa_probe needs node ≥ 22 (global WebSocket)\n"); return 2; }
  if (!existsSync(a.chrome)) { process.stderr.write("chrome not found: " + a.chrome + "\n"); return 2; }
  const profile = mkdtempSync(join(tmpdir(), "hf-qa-probe-"));
  const chrome = spawn(a.chrome, ["--headless", "--remote-debugging-port=0", "--user-data-dir=" + profile, "--no-first-run",
    "--no-default-browser-check", "--hide-scrollbars", "--mute-audio", `--window-size=${a.width},${a.height}`, "about:blank"],
    { stdio: "ignore" });
  let ws;
  try {
    const portFile = join(profile, "DevToolsActivePort");
    const port = await waitFor(() => existsSync(portFile) && readFileSync(portFile, "utf8").split("\n")[0], 15000, "Chrome to start");
    const pages = await waitFor(async () => {
      const list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
      return list.filter((t) => t.type === "page").length ? list : null;
    }, 10000, "a Chrome page");
    ws = new WebSocket(pages.find((t) => t.type === "page").webSocketDebuggerUrl);
    await new Promise((ok, fail) => { ws.onopen = ok; ws.onerror = () => fail(new Error("DevTools connection failed")); });
    let id = 0;
    const pending = new Map(), waiters = [], errors = [];
    ws.onmessage = (ev) => {
      const m = JSON.parse(ev.data);
      if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); return; }
      if (m.method === "Runtime.exceptionThrown") errors.push(m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text);
      waiters.forEach((w) => w(m));
    };
    const send = (method, params = {}) => new Promise((ok) => { const i = ++id; pending.set(i, ok); ws.send(JSON.stringify({ id: i, method, params })); });
    const loaded = new Promise((ok) => waiters.push((m) => { if (m.method === "Page.loadEventFired") ok(); }));
    await send("Page.enable");
    await send("Runtime.enable");
    await send("Emulation.setDeviceMetricsOverride", { width: a.width, height: a.height, deviceScaleFactor: 1, mobile: false });
    const nav = await send("Page.navigate", { url: a.url });
    if (nav.result && nav.result.errorText) throw new Error("navigation failed: " + nav.result.errorText);
    await Promise.race([loaded, new Promise((_, fail) => setTimeout(() => fail(new Error("page load timed out")), a.timeout))]);
    const res = await send("Runtime.evaluate", { expression: `(${pageProbe.toString()})(${JSON.stringify({ format: a.format, samples: a.samples, timeout: a.timeout })})`,
      awaitPromise: true, returnByValue: true });
    if (res.result.exceptionDetails) throw new Error("probe threw: " + (res.result.exceptionDetails.exception?.description || res.result.exceptionDetails.text));
    const out = res.result.result.value;
    if (out.error) throw new Error(out.error);
    out.errors = errors;
    process.stdout.write(JSON.stringify(out) + "\n");
    return 0;
  } catch (e) {
    process.stderr.write("qa_probe: " + e.message + "\n");
    return 2;
  } finally {
    try { ws && ws.close(); } catch (e) { /* closing anyway */ }
    chrome.kill("SIGKILL");
    await new Promise((r) => setTimeout(r, 200));
    rmSync(profile, { recursive: true, force: true });
  }
}

process.exitCode = await main();
````

Create `tools/runtime_probe.py`:

````python
"""Runtime view of a composition for QA checks 5, 6 and 10: serve it with `npx hyperframes preview`
(HyperFrames' own bundler + runtime) and probe it in headless Chrome with tools/qa_probe.mjs.

Chrome: $HF_CHROME, else the chrome-headless-shell HyperFrames downloads for rendering
(~/.cache/puppeteer/chrome-headless-shell/...), else `npx hyperframes browser path`.
"""
import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tools" / "qa_probe.mjs"


class ProbeError(Exception):
    """The page could not be probed (no Chrome, preview failed, page never registered a timeline)."""


def hyperframes_cmd() -> list:
    """The HyperFrames CLI prefix; $HF_CLI overrides it (e.g. a pinned version, or a test stub)."""
    return shlex.split(os.environ.get("HF_CLI", "npx --yes hyperframes"))


def find_chrome(allow_npx=True):
    env = os.environ.get("HF_CHROME")
    if env:
        return env if Path(env).is_file() else None
    cache = Path.home() / ".cache" / "puppeteer" / "chrome-headless-shell"
    found = sorted(cache.glob("*/*/chrome-headless-shell")) + sorted(cache.glob("*/*/chrome-headless-shell.exe"))
    if found:
        return str(found[-1])
    if allow_npx:
        r = subprocess.run(hyperframes_cmd() + ["browser", "path"], capture_output=True, text=True)
        lines = [l.strip() for l in r.stdout.splitlines() if l.strip()]
        if r.returncode == 0 and lines and Path(lines[-1]).is_file():
            return lines[-1]
    return None


def probe_url(url, fmt, size, chrome=None, samples=24, timeout_ms=30000) -> dict:
    node = shutil.which("node")
    chrome = chrome or find_chrome()
    if not node or not chrome:
        raise ProbeError("runtime probe needs node ≥ 22 and Chrome (set HF_CHROME or run: npx hyperframes browser ensure)")
    r = subprocess.run([node, str(PROBE), "--url", url, "--format", fmt, "--chrome", chrome,
                        "--width", str(size[0]), "--height", str(size[1]), "--samples", str(samples),
                        "--timeout", str(timeout_ms)], capture_output=True, text=True)
    if r.returncode != 0:
        raise ProbeError((r.stderr or r.stdout).strip() or f"qa_probe exited {r.returncode}")
    return json.loads(r.stdout)


def probe_project(project, fmt, size, port=3930, **kw) -> dict:
    """Start (or reuse) the project's background preview, probe it, stop it if this call started it."""
    project = Path(project).resolve()
    hf = hyperframes_cmd()
    r = subprocess.run(hf + ["preview", str(project), "--background", "--no-open", "--port", str(port), "--json"],
                       capture_output=True, text=True)
    try:
        start = json.loads(r.stdout.strip().splitlines()[-1])["result"]
        url = f"{start['serverUrl']}/api/projects/{start['projectName']}/preview"
    except (ValueError, KeyError, IndexError):
        raise ProbeError("npx hyperframes preview did not start: " + (r.stderr or r.stdout).strip()[-600:])
    try:
        return probe_url(url, fmt, size, **kw)
    finally:
        if start.get("state") == "started":
            subprocess.run(hf + ["preview", str(project), "--stop", "--json"], capture_output=True, text=True)
````

- [ ] **Step 4: Run the tests**

Run: `python3 -m unittest discover -s tools -p 'test_runtime_probe.py' -v`
Expected: `Ran 6 tests … OK` (≈ 13 s: two Chrome launches and a 1.5 s no-timeline timeout).
Optional live check on a scaffold with one composition (needs network): `HF_CLI="npx --yes hyperframes@0.8.29" python3 -c "import sys; sys.path.insert(0,'tools'); import runtime_probe as rp; print(rp.probe_project('/tmp/hf/99-scratch', 'long-form', (1920, 1080)))"` → `findings: []`.

- [ ] **Step 5: Commit**

```bash
git add tools/qa_probe.mjs tools/runtime_probe.py tools/test_runtime_probe.py
git commit -m "feat(tools): runtime probe — live-page blur reasons, eases and text traps via hyperframes preview

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 10: `tools/qa.py` — the automated gate

**Files:**
- Create: `tools/qa.py`, `tools/test_qa.py`
- Modify: `standards/core/qa.md`, `standards/core/pipeline.md`, `CLAUDE.md`

**Interfaces:**
- Consumes: `sync_lib.check` (T1); `lawscan.js` CLI (T3); `project.*`, `brandcheck.load_brand` (T4); `media.video_info`, `frame_diffs`, `scene_cuts` (T6); `scan_flicker.find_flicker` (T6); `cadence_scan.report` (T7); `runtime_probe.hyperframes_cmd`, `probe_url`, `probe_project`, `ProbeError` (T9); `new_video.scaffold`, `synth.*` (tests).
- Produces:
  - `qa.run_gate(project, render=None, edit=None, probe_url=None, skip_render=False, probe=None, root=ROOT) -> {"project", "format", "checks": [{"n", "name", "status": PASS|FAIL|SKIP|WAIVED, "findings", "note", "waived"?, "density"? (check 8)}], "exceptions", "waivers", "ok"}`; writes `<project>/renders/qa-report.json`. `probe` is an injectable `(project, fmt) -> probe dict` (tests).
  - `qa.result(n, findings=None, note="", status=None)`, `qa.apply_waivers(checks, exceptions) -> listed`, `qa.settle_findings(diffs, scenes, fps, max_step=1.5)`, `qa.scene_windows(project, fmt, rows)`, `qa.flicker_findings(diffs, fps, cut_times)`, `qa.check_captions(project, brief, rows)`, `qa.format_report(report) -> str`, `qa.NAMES`, `qa.SETTLE_WINDOW = 0.3`, `qa.SETTLE_MAX = 1.5`.
  - CLI `python3 tools/qa.py videos/<slug> [--render R] [--edit CUT] [--probe-url URL] [--skip-render] [--json]` → exit 0 only when every check is PASS or WAIVED.

- [ ] **Step 1: Write the failing test**

Create `tools/test_qa.py` (a fake HyperFrames CLI stands in for `check` and `render`; the probe is injected):

````python
import io
import json
import os
import shlex
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import new_video
import qa
import synth

ROOT = Path(__file__).resolve().parents[1]
FAKE_HF = """import os, shutil, sys
args = sys.argv[1:]
if args[0] == "check":
    print("fake hyperframes check: " + os.environ.get("FAKE_HF_CHECK_MSG", "ok"))
    sys.exit(int(os.environ.get("FAKE_HF_CHECK", "0")))
if args[0] == "render":
    shutil.copyfile(os.environ["FAKE_HF_RENDER_SRC"], args[args.index("-o") + 1])
    sys.exit(0)
sys.exit(3)
"""
HEADER = "| t_in | t_out | words | placement | type | beats | ease | marks |\n|---|---|---|---|---|---|---|---|\n"
GOOD_GRID = HEADER + (
    '| 0.0 | 50.0 | "hook" | full-frame | B1 | — | ease.enter | — |\n'
    '| 52.0 | 80.0 | "proof" | full-frame | A1 | — | ease.enter | — |\n'
    '| 100.0 | 104.0 | "key line" | over-footage | lower-third | — | ease.enter | — |\n')
SCENE = """<template>
<div id="root" data-composition-id="01-hook"><div id="h1">Proof first</div>
<svg><filter id="g"><feGaussianBlur data-blur-reason="glow" stdDeviation="6"/></filter></svg></div>
<script>
  var tl = gsap.timeline({ paused: true });
  HFText.words(tl, document.querySelector("#h1"), 0.5, { format: "long-form", frameHeight: 1080 });
  window.__timelines["01-hook"] = tl;
</script>
</template>
"""
SLOTS = ('<div id="s01" data-composition-id="01-hook" data-composition-src="compositions/01-hook.html" data-start="0" data-duration="2"></div>\n'
         '      <div id="s02" data-composition-id="02-proof" data-composition-src="compositions/02-proof.html" data-start="2" data-duration="2"></div>\n')


def clean_probe(project, fmt):
    return {"timelines": 2, "tweens": 4, "samples": 24, "findings": []}


@unittest.skipUnless(synth.HAVE_FFMPEG and shutil.which("node"), "needs ffmpeg and node")
class GateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.media = tempfile.TemporaryDirectory()
        d = Path(cls.media.name)
        settled = synth.moving_then_still(d / "settled.mp4", 1.5, 0.5)
        moving = synth.moving(d / "moving.mp4", 2)
        glitched = synth.moving_then_still(d / "glitched.mp4", 1.5, 0.5, glitch_frame=20)
        cls.good_reel = synth.concat(d / "good.mp4", [settled, settled])          # two scenes, both settle
        cls.unsettled_reel = synth.concat(d / "unsettled.mp4", [settled, moving])  # scene 2 moves into its cut
        cls.glitch_reel = synth.concat(d / "glitch.mp4", [settled, glitched])      # one-frame glitch at reel frame 80
        fake = d / "fake_hf.py"
        fake.write_text(FAKE_HF)
        cls.hf_cli = f"{shlex.quote(sys.executable)} {shlex.quote(str(fake))}"

    @classmethod
    def tearDownClass(cls):
        cls.media.cleanup()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = {k: os.environ.get(k) for k in ("HF_CLI", "FAKE_HF_CHECK", "FAKE_HF_RENDER_SRC")}
        os.environ["HF_CLI"] = self.hf_cli
        os.environ["FAKE_HF_CHECK"] = "0"
        self.p = new_video.scaffold("10-demo", "long-form", videos_dir=Path(self.tmp.name))
        brief = (self.p / "BRIEF.md").read_text()
        brief = brief.replace('film: ""', 'film: "Believe the system is predictable"')
        brief = brief.replace('direction: ""', 'direction: "One canvas per argument"')
        (self.p / "BRIEF.md").write_text(brief)
        (self.p / "storyboard.md").write_text(GOOD_GRID)
        (self.p / "transcript.json").write_text(json.dumps([{"text": "x", "start": 0, "end": 110}]))
        index = (self.p / "index.html").read_text().replace('data-height="1080">\n    </div>', 'data-height="1080">\n      ' + SLOTS + '    </div>')
        (self.p / "index.html").write_text(index)
        (self.p / "compositions" / "01-hook.html").write_text(SCENE)

    def tearDown(self):
        for k, v in self.env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self.tmp.cleanup()

    def gate(self, **kw):
        kw.setdefault("render", self.good_reel)
        kw.setdefault("probe", clean_probe)
        return qa.run_gate(self.p, **kw)

    def status(self, report):
        return {c["n"]: c["status"] for c in report["checks"]}

    def test_good_project_passes_all_ten(self):
        r = self.gate()
        self.assertEqual(self.status(r), {n: "PASS" for n in range(1, 11)}, qa.format_report(r))
        self.assertTrue(r["ok"])
        self.assertTrue((self.p / "renders" / "qa-report.json").is_file())
        self.assertIn("RESULT: PASS", qa.format_report(r))

    def test_check_1_hyperframes_check_failure(self):
        os.environ["FAKE_HF_CHECK"] = "1"
        c = self.gate()["checks"][0]
        self.assertEqual(c["status"], "FAIL")
        self.assertIn("fake hyperframes check: ok", c["findings"][-1])

    def test_check_2_edited_lib_copy(self):
        (self.p / "lib" / "camera.js").write_text("// forked\n")
        c = self.gate()["checks"][1]
        self.assertEqual(c["findings"], ["lib/camera.js differs from root lib/camera.js (edited copy?) — fix root lib/, then re-sync"])

    def test_check_3_incomplete_brief_and_stale_brand_css(self):
        text = (self.p / "BRIEF.md").read_text()
        (self.p / "BRIEF.md").write_text(text.replace('direction: "One canvas per argument"', 'direction: ""'))
        self.assertIn("direction is required (one line of art direction)", self.gate()["checks"][2]["findings"])
        (self.p / "BRIEF.md").write_text(text.replace("palette: red", "palette: silver"))
        found = self.gate()["checks"][2]["findings"]
        self.assertIn("index.html root data-hf-mode is 'dark', palette silver is 'light'", found)
        self.assertTrue(any(f.startswith("compositions/brand.css does not match") and "--palette silver" in f for f in found), found)

    def test_checks_4_5_6_static_findings(self):
        (self.p / "compositions" / "02-proof.html").write_text(
            "<template><div id=\"root\" data-composition-id=\"02-proof\"><svg><filter><feGaussianBlur stdDeviation=\"3\"/></filter></svg></div>\n"
            "<script>var x = Math.random(); tl.to('#a', { x: 1, duration: 1, ease: \"power2.out\" });</script></template>\n")
        st = self.status(self.gate())
        self.assertEqual((st[4], st[5], st[6]), ("FAIL", "FAIL", "FAIL"))
        r = self.gate()
        self.assertTrue(r["checks"][3]["findings"][0].startswith("compositions/02-proof.html:2: non-deterministic"), r["checks"][3])

    def test_runtime_findings_merge_into_their_checks(self):
        def probe(project, fmt):
            return {"findings": [{"check": 5, "message": "main div#x: CSS filter blur() without data-blur-reason", "t": 1.5},
                                 {"check": 6, "message": "main: tween on div#y at 2 s has no ease", "t": None},
                                 {"check": 10, "message": "p#g: centred gradient text ...", "t": 0.5}]}
        r = self.gate(probe=probe)
        self.assertEqual(r["checks"][4]["findings"], ["runtime @ 1.5 s: main div#x: CSS filter blur() without data-blur-reason"])
        self.assertEqual(r["checks"][5]["findings"], ["runtime: main: tween on div#y at 2 s has no ease"])
        self.assertEqual(r["checks"][9]["status"], "FAIL")

    def test_probe_failure_fails_5_6_10(self):
        def probe(project, fmt):
            raise qa.runtime_probe.ProbeError("no timeline registered on window.__timelines")
        st = self.status(self.gate(probe=probe))
        self.assertEqual((st[5], st[6], st[10]), ("FAIL", "FAIL", "FAIL"))

    def test_check_7_caption_layer_in_long_form(self):
        (self.p / "compositions" / "03-caps.html").write_text('<div class="captions word-layer">hi</div>\n<!-- class="captions" in a comment is fine -->\n')
        c = self.gate()["checks"][6]
        self.assertEqual(c["findings"], ['compositions/03-caps.html:1: caption layer (class="captions word-layer")'])

    def test_check_8_density_on_the_plan(self):
        (self.p / "storyboard.md").write_text(HEADER + '| 0.0 | 30.0 | "hook" | full-frame | B1 | — | — | — |\n')
        c = self.gate()["checks"][7]
        self.assertEqual(c["status"], "FAIL")
        self.assertTrue(any("hook graphics ≥ 60 %" in f for f in c["findings"]), c["findings"])

    def test_check_9_scene_still_moving_at_its_cut(self):
        c = self.gate(render=self.unsettled_reel)["checks"][8]
        self.assertEqual(len(c["findings"]), 1, c)
        self.assertTrue(c["findings"][0].startswith("02-proof: still moving in its last 0.3 s"), c["findings"])

    def test_check_10_flicker_but_not_the_scene_cut(self):
        c = self.gate(render=self.glitch_reel)["checks"][9]
        self.assertEqual([f.split(" (")[0] for f in c["findings"]], ["flicker at frame 80", "flicker at frame 81"], c["findings"])

    def test_waivers_and_listed_exceptions(self):
        text = (self.p / "BRIEF.md").read_text()
        (self.p / "BRIEF.md").write_text(text.replace("exceptions:                  #", 'exceptions:\n  - "check 9: hold-push into the CTA by design"\n  - "F09: recreated Google Calendar — no real account"\n#'))
        r = self.gate(render=self.unsettled_reel)
        c9 = r["checks"][8]
        self.assertEqual(c9["status"], "WAIVED")
        self.assertEqual(c9["waived"], ["1 finding(s): hold-push into the CTA by design"])
        self.assertEqual(r["exceptions"], ["F09: recreated Google Calendar — no real account"])
        self.assertTrue(r["ok"], qa.format_report(r))

    def test_scoped_waiver_keeps_other_findings(self):
        checks = [qa.result(n) for n in range(1, 11)]
        checks[4] = qa.result(5, ["compositions/a.html:3: Gaussian site without…", "compositions/b.html:9: Gaussian site without…"])
        listed = qa.apply_waivers(checks, ["check 5 [a.html]: legacy recreation", "check 12: nonsense"])
        self.assertEqual(checks[4]["status"], "FAIL")
        self.assertEqual(checks[4]["findings"], ["compositions/b.html:9: Gaussian site without…"])
        self.assertEqual(listed, ["check 12: nonsense"])

    def test_skip_render_cannot_pass(self):
        r = self.gate(render=None, skip_render=True)
        self.assertEqual((self.status(r)[9], self.status(r)[10]), ("SKIP", "SKIP"))
        self.assertFalse(r["ok"])

    def test_draft_render_through_hyperframes(self):
        os.environ["FAKE_HF_RENDER_SRC"] = str(self.good_reel)
        r = self.gate(render=None)
        self.assertEqual(self.status(r)[9], "PASS", qa.format_report(r))
        self.assertTrue((self.p / "renders" / "qa-draft.mp4").is_file())

    def test_cli(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(qa.main(["qa.py", str(Path(self.tmp.name) / "nope")]), 2)
        self.assertIn("not a directory", out.getvalue())


@unittest.skipUnless(synth.HAVE_FFMPEG and shutil.which("node"), "needs ffmpeg and node")
class ShortsGateTests(unittest.TestCase):
    def test_shorts_captions_flag_and_settle_before_the_wipe(self):
        with tempfile.TemporaryDirectory() as t:
            p = new_video.scaffold("s1-demo", "shorts", palette="reel-dark", videos_dir=Path(t))
            brief = (p / "BRIEF.md").read_text().replace('film: ""', 'film: "x"').replace('direction: ""', 'direction: "y"')
            (p / "BRIEF.md").write_text(brief.replace("captions: false", "captions: true"))
            rows = [{"row": 1, "line": 3, "t_in": 1.0, "t_out": 4.0, "placement": "full-frame", "type": "A1"}]
            self.assertEqual(qa.scene_windows(p, "shorts", rows), [("row 1 (1–4 s)", 4.0 - 0.36 - 0.3, 4.0 - 0.36)])
            c = qa.check_captions(p, qa.pj.read_brief(p), [])
            self.assertEqual(c["findings"], ["captions: true but no caption layer found (id/class 'captions' or data-captions)"])


if __name__ == "__main__":
    unittest.main()
````

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 -m unittest discover -s tools -p 'test_qa.py' -v`
Expected: ERROR — `ModuleNotFoundError: No module named 'qa'`.

- [ ] **Step 3: Write the gate**

Create `tools/qa.py`:

````python
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


def check_hyperframes(project):
    r = subprocess.run(runtime_probe.hyperframes_cmd() + ["check", str(project)], capture_output=True, text=True)
    if r.returncode == 0:
        return result(1)
    tail = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()][-15:]
    return result(1, tail or [f"npx hyperframes check exited {r.returncode}"])


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
    report = {"project": str(project), "format": fmt, "checks": ordered, "exceptions": listed,
              "waivers": [e for e in (brief.get("exceptions") or []) if e not in listed],
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
````

- [ ] **Step 4: Run the tests**

Run: `python3 -m unittest discover -s tools -p 'test_qa.py' -v`
Expected: `Ran 17 tests … OK` (≈ 7 s).
Optional live run on a filled-in scaffold (network; ≈ 2 min with the draft render): `HF_CLI="npx --yes hyperframes@0.8.29" python3 tools/qa.py /tmp/hf/99-scratch` → ten lines, `RESULT: PASS` once the BRIEF, beat grid and transcript are filled and every tween uses `HFProfile.ease`.

- [ ] **Step 5: Document the gate**

````bash
python3 - . <<'PY'
import sys
from pathlib import Path
ROOT = Path(sys.argv[1])

def edit(rel, pairs):
    p = ROOT / rel
    s = p.read_text()
    for a, b in pairs:
        assert s.count(a) == 1, (rel, a[:70])
        s = s.replace(a, b)
    p.write_text(s)

edit("standards/core/qa.md", [
("""Automated checks are implemented by `tools/qa` (Plan 3). Until it exists, run each check by hand.""",
 """Run the automated gate with `python3 tools/qa.py videos/<slug>`: it prints PASS / FAIL (or SKIP /
WAIVED) for each of the ten checks below and writes `renders/qa-report.json`. It renders a draft
(`npx hyperframes render -q draft`) for checks 9–10 unless given `--render`, probes the live page
through `npx hyperframes preview` for checks 5, 6 and 10, and takes `--edit <cut.mp4>` to measure
density on the edited timeline as well as on the beat grid."""),
("""that has no real screenshot). The gate passes declared exceptions and lists them in the preview pack.""",
 """that has no real screenshot). The gate passes declared exceptions and lists them in the preview pack.
An entry `check <n>: <reason>` waives check n; `check <n> [<text>]: <reason>` waives only the findings
of check n that contain `<text>`. Any other entry (e.g. `F09: recreated Google Calendar — …`) is
listed, not applied."""),
])
edit("standards/core/pipeline.md", [
("""5. **Automated gate** (`standards/core/qa.md` §1).""",
 """5. **Automated gate:** `python3 tools/qa.py videos/<slug>` (`standards/core/qa.md` §1)."""),
])
edit("CLAUDE.md", [
("""6. Every video passes `standards/core/qa.md` (automated gate, agent critique loop, then sign-off by whoever ran the build).""",
 """6. Every video passes `standards/core/qa.md` (automated gate `python3 tools/qa.py videos/<slug>`, agent critique loop, then sign-off by whoever ran the build)."""),
])
PY
````

Run: `python3 -m unittest discover -s tools -p 'test_*.py'` → `Ran 178 tests … FAILED (errors=14)`.

- [ ] **Step 6: Commit**

```bash
git add tools/qa.py tools/test_qa.py standards/core/qa.md standards/core/pipeline.md CLAUDE.md
git commit -m "feat(tools): qa.py runs all ten QA checks with PASS/FAIL per check and BRIEF waivers

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 11: `tools/preview_pack.py` — the sign-off pack

**Files:**
- Create: `tools/preview_pack.py`, `tools/test_preview_pack.py`
- Modify: `standards/core/qa.md`, `standards/core/pipeline.md`

**Interfaces:**
- Consumes: `project.read_brief`, `read_storyboard`, `composition_slots`, `hook_end` (T4); `media.extract_frame`, `video_info`, `run`, `tool` (T6); `cadence_scan.report` (T7); `<project>/renders/qa-report.json` (T10); `<project>/critique.md` (T5 template).
- Produces: `preview_pack.parse_critique(text) -> {"round", "rows": [{"graphic", "scores": {dim: int|None}, "notes", "low": [dims]}]}` (last round, low scorers first); `preview_pack.graphics(project, fmt, rows)`; `preview_pack.density_svg(report, width=960) -> str`; `preview_pack.build(project, render, overlays=None, out_dir=None) -> Path` (`renders/preview/index.html`, `contact-sheet.png`, `frames/NNN.png`, `hook.mp4` + `body.mp4` (long-form) or `short.mp4`); CLI `python3 tools/preview_pack.py videos/<slug> [--render R] [--overlays DIR]`.

- [ ] **Step 1: Write the failing test**

Create `tools/test_preview_pack.py`:

````python
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import media
import preview_pack as pp
import synth

HEADER = "| t_in | t_out | words | placement | type | beats | ease | marks |\n|---|---|---|---|---|---|---|---|\n"
CRITIQUE = """# Critique — demo

## Round 1

| graphic | smooth | on-brand | readable | synced | purposeful | craft | notes |
|---|---|---|---|---|---|---|---|
| 01-hook | 5 | 9 | 9 | 9 | 9 | 9 | snapped |

## Round 2

| graphic | smooth | on-brand | readable | synced | purposeful | craft | notes |
|---|---|---|---|---|---|---|---|
| 01-hook | 9 | 9 | 9 | 9 | 9 | 9 | eased now |
| 02-proof | 9 | 7 | 9 | 9 | ? | 9 | palette drift |
"""


class CritiqueTests(unittest.TestCase):
    def test_last_round_low_scorers_first(self):
        c = pp.parse_critique(CRITIQUE)
        self.assertEqual(c["round"], 2)
        self.assertEqual([r["graphic"] for r in c["rows"]], ["02-proof", "01-hook"])
        self.assertEqual(c["rows"][0]["low"], ["on-brand", "purposeful"])
        self.assertIsNone(c["rows"][0]["scores"]["purposeful"])
        self.assertEqual(c["rows"][1]["low"], [])

    def test_no_rounds(self):
        self.assertEqual(pp.parse_critique("# nothing yet"), {"round": None, "rows": []})


@unittest.skipUnless(synth.HAVE_FFMPEG, "ffmpeg/ffprobe not installed")
class BuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        self.p = d / "10-demo"
        self.p.mkdir()
        (self.p / "BRIEF.md").write_text('```yaml\nformat: long-form\nhook_end: 80\nexceptions:\n  - "F09: recreated calendar"\n```\n')
        (self.p / "index.html").write_text(
            '<div id="root" data-composition-id="main">'
            '<div data-composition-id="01-hook" data-composition-src="compositions/01.html" data-start="0" data-duration="2"></div>'
            '<div data-composition-id="02-proof" data-composition-src="compositions/02.html" data-start="2" data-duration="2"></div></div>')
        (self.p / "storyboard.md").write_text(HEADER + '| 10.0 | 12.0 | "hook" | full-frame | B1 | — | — | — |\n'
                                              '| 100.0 | 102.0 | "proof" | full-frame | A1 | — | — | — |\n')
        (self.p / "transcript.json").write_text(json.dumps([{"text": "x", "start": 0, "end": 120}]))
        (self.p / "critique.md").write_text(CRITIQUE)
        self.reel = synth.segments(d / "reel.mp4", [("red", 2), ("blue", 2)])
        self.overlays = d / "overlays"
        self.overlays.mkdir()
        synth.prores(self.overlays / "01-key-line.mov", 1)

    def tearDown(self):
        self.tmp.cleanup()

    def test_pack_contents(self):
        index = pp.build(self.p, self.reel, self.overlays)
        out = index.parent
        self.assertEqual(out, self.p / "renders" / "preview")
        self.assertEqual(sorted(p.name for p in (out / "frames").iterdir()), ["001.png", "002.png", "003.png"])
        for f in sorted((out / "frames").iterdir()):
            self.assertEqual(media.video_info(f)["pix_fmt"], "rgb24", f.name)   # alpha flattened: tile needs one format
        sheet = media.video_info(out / "contact-sheet.png")
        self.assertEqual(sheet["width"], 4 * 480 + 5 * 8)
        rgb = media.run(["ffmpeg", "-v", "error", "-i", str(out / "contact-sheet.png"), "-vf", "scale=4:1",
                         "-pix_fmt", "rgb24", "-f", "rawvideo", "-"], binary=True)
        r, g = rgb[6], rgb[7]                                    # third tile: the 50 % red overlay over grey
        self.assertGreater(r, g + 20, "the overlay tile shows the layout, not just the backdrop")
        self.assertAlmostEqual(media.video_info(out / "hook.mp4")["duration"], 2.0, delta=0.1)
        self.assertAlmostEqual(media.video_info(out / "body.mp4")["duration"], 2.0, delta=0.1)
        page = index.read_text()
        self.assertLess(page.index("02-proof"), page.index("eased now"), "low scorers listed first")
        self.assertIn("1 graphic(s) below 8", page)
        self.assertIn("F09: recreated calendar", page)
        self.assertIn('aria-label="density timeline"', page)
        self.assertIn("No renders/qa-report.json", page)
        self.assertIn("over-footage · 01-key-line", page)

    def test_qa_report_is_summarised_and_rebuild_replaces_the_pack(self):
        (self.p / "renders").mkdir()
        (self.p / "renders" / "qa-report.json").write_text(json.dumps(
            {"ok": False, "checks": [{"n": 9, "name": "Settle before cut", "status": "FAIL", "findings": ["02-proof: still moving"]}]}))
        pp.build(self.p, self.reel)
        stray = self.p / "renders" / "preview" / "frames" / "999.png"
        stray.write_text("old")
        page = pp.build(self.p, self.reel).read_text()
        self.assertFalse(stray.exists())
        self.assertIn("Automated gate — <span class='fail'>FAIL</span>", page)
        self.assertIn("02-proof: still moving", page)

    def test_cli_missing_render(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(pp.main(["preview_pack.py", str(self.p)]), 1)
        self.assertIn("qa-draft.mp4 not found", out.getvalue())


if __name__ == "__main__":
    unittest.main()
````

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 -m unittest discover -s tools -p 'test_preview_pack.py' -v`
Expected: ERROR — `ModuleNotFoundError: No module named 'preview_pack'`.

- [ ] **Step 3: Write the generator**

Create `tools/preview_pack.py`:

````python
"""Generate the preview pack for human sign-off (standards/core/qa.md §3) into renders/preview/.

Contents (index.html links everything): the final critique scores (any graphic still below 8 first),
a contact sheet of every graphic (one settled frame each), a draft of the hook plus one body scene
(long-form; a Short links its whole render), the density timeline, the exceptions list, and the
automated gate's result when renders/qa-report.json exists. renders/ is never committed.

Usage: python3 tools/preview_pack.py videos/<slug> [--render renders/qa-draft.mp4] [--overlays renders/overlays]
"""
import argparse
import html
import json
import re
import shutil
import sys
from pathlib import Path

import cadence_scan
import media
import project as pj

DIMENSIONS = ["smooth", "on-brand", "readable", "synced", "purposeful", "craft"]
PASS_SCORE = 8
SETTLED_LEAD = 0.35   # the settled frame: 0.35 s before a scene's cut (inside the 0.3–1 s hold)
SHORTS_EXIT = 0.36


def parse_critique(text: str) -> dict:
    """The last '## Round N' table of critique.md → {"round": N | None, "rows": [...]}, low scorers first."""
    rounds = list(re.finditer(r"^## Round (\d+)\s*$", text, re.M))
    if not rounds:
        return {"round": None, "rows": []}
    last = rounds[-1]
    rows = []
    for line in text[last.end():].splitlines():
        if line.startswith("## "):
            break
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 8 or cells[0] in ("graphic", "") or set(cells[0]) <= {"-", ":"}:
            continue
        scores = {}
        for dim, cell in zip(DIMENSIONS, cells[1:7]):
            scores[dim] = int(cell) if re.fullmatch(r"\d{1,2}", cell) else None
        low = [d for d, s in scores.items() if s is None or s < PASS_SCORE]
        rows.append({"graphic": cells[0], "scores": scores, "notes": cells[7], "low": low})
    rows.sort(key=lambda r: (not r["low"], ))
    return {"round": int(last.group(1)), "rows": rows}


def graphics(project, fmt, rows) -> list:
    """Every graphic in the render: {"label", "timeline" (s on the edit), "start", "end" (s in the render)}."""
    full = [r for r in rows if r["placement"] == "full-frame"]
    if fmt == "shorts":
        return [{"label": f"{r['type']} {r['t_in']:g}–{r['t_out']:g} s", "timeline": r["t_in"], "start": r["t_in"],
                 "end": r["t_out"] - SHORTS_EXIT} for r in full]
    slots = pj.composition_slots(project)
    out = []
    for i, s in enumerate(slots):
        row = full[i] if len(full) == len(slots) else None
        out.append({"label": s["id"] + (f" · {row['type']}" if row else ""), "timeline": row["t_in"] if row else None,
                    "start": s["start"], "end": s["start"] + s["dur"]})
    return out


def density_svg(report, width=960) -> str:
    dur, h = report["duration"], 46
    x = lambda t: round(t / dur * width, 1)
    bars = [f'<rect x="0" y="12" width="{width}" height="22" fill="#2a2a2a"/>']
    for a, b in report.get("screen_share", []):
        bars.append(f'<rect x="{x(a)}" y="12" width="{x(b) - x(a)}" height="22" fill="#555"><title>screen share {a:g}–{b:g} s</title></rect>')
    for a, b in report["over_footage"]:
        bars.append(f'<rect x="{x(a)}" y="24" width="{max(1, x(b) - x(a))}" height="10" fill="#8fb3ff"><title>over-footage {a:g}–{b:g} s</title></rect>')
    for a, b in report["full_frame"]:
        bars.append(f'<rect x="{x(a)}" y="12" width="{max(1, x(b) - x(a))}" height="22" fill="#f26666"><title>full-frame {a:g}–{b:g} s</title></rect>')
    if report["format"] == "long-form":
        he = min(report["hook_end"], dur)
        bars.append(f'<line x1="{x(he)}" y1="4" x2="{x(he)}" y2="42" stroke="#fff" stroke-dasharray="3 3"/>'
                    f'<text x="{x(he) + 4}" y="10" fill="#ccc" font-size="10">hook_end {he:g} s</text>')
    return f'<svg viewBox="0 0 {width} {h}" width="100%" role="img" aria-label="density timeline">{"".join(bars)}</svg>'


def _cut(src, start, end, out):
    media.run([media.tool("ffmpeg"), "-v", "error", "-nostdin", "-y", "-ss", f"{start:.3f}", "-i", str(src),
               "-t", f"{max(0.04, end - start):.3f}", "-an", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", str(out)])


def build(project, render, overlays=None, out_dir=None) -> Path:
    project = Path(project)
    brief = pj.read_brief(project)
    fmt = brief.get("format")
    if fmt not in pj.FORMATS:
        raise pj.ProjectError(f"BRIEF format must be long-form or shorts, got {fmt!r}")
    rows = pj.read_storyboard(project)
    out = Path(out_dir) if out_dir else project / "renders" / "preview"
    if out.exists():
        shutil.rmtree(out)
    (out / "frames").mkdir(parents=True)

    items = graphics(project, fmt, rows)
    for i, g in enumerate(items, 1):
        g["frame"] = f"frames/{i:03d}.png"
        media.extract_frame(render, max(g["start"], g["end"] - SETTLED_LEAD), out / g["frame"])
    for j, mov in enumerate(sorted(Path(overlays).glob("*.mov")) if overlays else [], len(items) + 1):
        info = media.video_info(mov)
        g = {"label": f"over-footage · {mov.stem}", "timeline": None, "frame": f"frames/{j:03d}.png"}
        media.extract_frame(mov, max(0.0, info["duration"] - SETTLED_LEAD), out / g["frame"], background="0x3a3a3a")
        items.append(g)
    if items:
        cols = 4
        media.run([media.tool("ffmpeg"), "-v", "error", "-nostdin", "-y", "-framerate", "1", "-i", str(out / "frames" / "%03d.png"),
                   "-vf", f"scale=480:-2,tile={cols}x{-(-len(items) // cols)}:padding=8:margin=8:color=0x202020",
                   "-frames:v", "1", str(out / "contact-sheet.png")])

    drafts = []
    if fmt == "long-form" and items and items[0].get("start") is not None:
        hook_end = pj.hook_end(brief)
        scenes = [g for g in items if "start" in g]
        hook = [g for g in scenes if g["timeline"] is not None and g["timeline"] < hook_end] or scenes[:1]
        body = [g for g in scenes if g["timeline"] is not None and g["timeline"] >= hook_end][:1]
        _cut(render, hook[0]["start"], hook[-1]["end"], out / "hook.mp4")
        drafts.append(("hook.mp4", f"hook: {len(hook)} scene(s)"))
        if body:
            _cut(render, body[0]["start"], body[0]["end"], out / "body.mp4")
            drafts.append(("body.mp4", f"body: {body[0]['label']}"))
    elif fmt == "shorts":
        shutil.copyfile(render, out / "short.mp4")
        drafts.append(("short.mp4", "the whole Short"))

    try:
        density = cadence_scan.report(project)
    except (pj.ProjectError, ValueError) as e:
        density = {"error": str(e)}
    crit_path = project / "critique.md"
    critique = parse_critique(crit_path.read_text()) if crit_path.is_file() else {"round": None, "rows": []}
    qa_path = project / "renders" / "qa-report.json"
    qa = json.loads(qa_path.read_text()) if qa_path.is_file() else None
    (out / "index.html").write_text(render_html(project.name, fmt, items, drafts, density, critique, qa,
                                                brief.get("exceptions") or []))
    return out / "index.html"


def render_html(slug, fmt, items, drafts, density, critique, qa, exceptions) -> str:
    e = html.escape
    parts = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Preview pack — {e(slug)}</title>",
             "<style>body{font:15px/1.5 system-ui,sans-serif;background:#111;color:#eee;margin:24px;max-width:1100px}"
             "h1,h2{font-weight:600}table{border-collapse:collapse;margin:8px 0}td,th{border:1px solid #333;padding:4px 8px;text-align:left}"
             ".low{color:#f88;font-weight:600}.pass{color:#8d8}.fail{color:#f88}figure{display:inline-block;margin:6px;width:250px;vertical-align:top}"
             "figure img{width:100%;border:1px solid #333}figcaption{font-size:12px;color:#aaa}a{color:#9cf}</style></head><body>",
             f"<h1>Preview pack — {e(slug)} <small>({e(fmt)})</small></h1>"]
    # 1. critique scores, low first
    parts.append("<h2>Critique scores" + (f" — round {critique['round']}" if critique["round"] else "") + "</h2>")
    if critique["rows"]:
        low = [r for r in critique["rows"] if r["low"]]
        parts.append(f"<p class='{'low' if low else 'pass'}'>{len(low)} graphic(s) below {PASS_SCORE} on some dimension.</p>")
        parts.append("<table><tr><th>graphic</th>" + "".join(f"<th>{d}</th>" for d in DIMENSIONS) + "<th>notes</th></tr>")
        for r in critique["rows"]:
            cells = "".join(f"<td class='{'low' if d in r['low'] else ''}'>{'—' if r['scores'][d] is None else r['scores'][d]}</td>" for d in DIMENSIONS)
            parts.append(f"<tr><td class='{'low' if r['low'] else ''}'>{e(r['graphic'])}</td>{cells}<td>{e(r['notes'])}</td></tr>")
        parts.append("</table>")
    else:
        parts.append("<p class='low'>No critique scores recorded yet — run the critique loop (standards/core/qa.md §2) into critique.md.</p>")
    # 2. automated gate
    if qa:
        parts.append(f"<h2>Automated gate — <span class='{'pass' if qa['ok'] else 'fail'}'>{'PASS' if qa['ok'] else 'FAIL'}</span></h2><table>")
        for c in qa["checks"]:
            parts.append(f"<tr><td>{c['n']}</td><td>{e(c['name'])}</td><td class='{'pass' if c['status'] in ('PASS', 'WAIVED') else 'fail'}'>{c['status']}</td>"
                         f"<td>{'<br>'.join(e(f) for f in c['findings'][:5])}</td></tr>")
        parts.append("</table>")
    else:
        parts.append("<h2>Automated gate</h2><p class='low'>No renders/qa-report.json — run python3 tools/qa.py first.</p>")
    # 3. drafts + contact sheet
    parts.append("<h2>Drafts</h2><ul>" + "".join(f"<li><a href='{f}'>{f}</a> — {e(d)}</li>" for f, d in drafts) + "</ul>")
    parts.append(f"<h2>Every graphic ({len(items)})</h2>")
    if items:
        parts.append("<p><a href='contact-sheet.png'>contact-sheet.png</a></p>")
    for g in items:
        when = f" · timeline {g['timeline']:.1f} s" if g.get("timeline") is not None else ""
        parts.append(f"<figure><img src='{g['frame']}' alt=''><figcaption>{e(g['label'])}{when}</figcaption></figure>")
    # 4. density
    parts.append("<h2>Density</h2>")
    if "error" in density:
        parts.append(f"<p class='low'>{e(density['error'])}</p>")
    else:
        parts.append(density_svg(density))
        parts.append("<ul>" + "".join(f"<li class='{'pass' if r['ok'] else 'fail'}'>{'PASS' if r['ok'] else 'FAIL'} — {e(r['name'])}: {e(r['detail'])}</li>"
                                      for r in density["results"]) + "</ul>")
    # 5. exceptions
    parts.append("<h2>Exceptions</h2>" + ("<ul>" + "".join(f"<li>{e(str(x))}</li>" for x in exceptions) + "</ul>" if exceptions else "<p>None declared.</p>"))
    parts.append("</body></html>\n")
    return "\n".join(parts)


def main(argv) -> int:
    ap = argparse.ArgumentParser(prog="python3 tools/preview_pack.py")
    ap.add_argument("project")
    ap.add_argument("--render")
    ap.add_argument("--overlays")
    a = ap.parse_args(argv[1:])
    render = Path(a.render) if a.render else Path(a.project) / "renders" / "qa-draft.mp4"
    try:
        index = build(a.project, render, a.overlays)
    except (pj.ProjectError, media.MediaError) as e:
        print(e)
        return 1
    print(f"preview pack → {index}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
````

- [ ] **Step 4: Run the tests**

Run: `python3 -m unittest discover -s tools -p 'test_preview_pack.py' -v`
Expected: `Ran 5 tests … OK`.

- [ ] **Step 5: Document the command**

````bash
python3 - . <<'PY'
import sys
from pathlib import Path
ROOT = Path(sys.argv[1])

def edit(rel, pairs):
    p = ROOT / rel
    s = p.read_text()
    for a, b in pairs:
        assert s.count(a) == 1, (rel, a[:70])
        s = s.replace(a, b)
    p.write_text(s)

edit("standards/core/qa.md", [
("""1. **Preview pack** (generated): a contact sheet""",
 """1. **Preview pack** (`python3 tools/preview_pack.py videos/<slug>` → `renders/preview/index.html`): a contact sheet"""),
])
edit("standards/core/pipeline.md", [
("""7. **Preview pack → sign-off** by the runner (`standards/core/qa.md` §3).""",
 """7. **Preview pack → sign-off** by the runner: `python3 tools/preview_pack.py videos/<slug>` (`standards/core/qa.md` §3)."""),
])
PY
````

Run: `python3 -m unittest discover -s tools -p 'test_*.py'` → `Ran 183 tests … FAILED (errors=14)`.

- [ ] **Step 6: Commit**

```bash
git add tools/preview_pack.py tools/test_preview_pack.py standards/core/qa.md standards/core/pipeline.md
git commit -m "feat(tools): preview_pack builds the sign-off pack (critique, gate, contact sheet, drafts, density, exceptions)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 12: Docs close-out + roadmap

**Files:**
- Modify: `tools/test_standards_layout.py`, `CLAUDE.md`, `docs/superpowers/plans/2026-10-03-animation-workflow-roadmap.md`

**Interfaces:**
- Consumes: every tool from Tasks 1–11; the doc edits of Tasks 1, 3, 5–8, 10, 11.
- Produces: tests that fail if a "Plan 3" placeholder returns or a documented `python3 tools/<x>.py` does not exist; the roadmap row marked done with notes for Plan 4.

- [ ] **Step 1: Write the doc tests**

````bash
python3 - . <<'PY'
import sys
from pathlib import Path
ROOT = Path(sys.argv[1])

def edit(rel, pairs):
    p = ROOT / rel
    s = p.read_text()
    for a, b in pairs:
        assert s.count(a) == 1, (rel, a[:70])
        s = s.replace(a, b)
    p.write_text(s)

edit("tools/test_standards_layout.py", [
("""

if __name__ == "__main__":""",
 '\n\nclass ToolsDocsTests(unittest.TestCase):\n    DOCS = ["CLAUDE.md", "lib/README.md", "standards/core/qa.md", "standards/core/pipeline.md",\n            "standards/formats/long-form.md", "standards/formats/shorts.md"]\n\n    def test_no_plan_3_placeholders_left(self):\n        for rel in self.DOCS:\n            t = (ROOT / rel).read_text()\n            for stale in ["(Plan 3)", "tools/sync-lib", "tools/new-video", "tools/probe-cuts", "`tools/qa`"]:\n                self.assertNotIn(stale, t, f"{rel}: {stale}")\n\n    def test_every_documented_tool_exists(self):\n        import re\n        seen = set()\n        for rel in self.DOCS:\n            for tool in re.findall(r"python3 tools/([\\w-]+\\.py)", (ROOT / rel).read_text()):\n                seen.add(tool)\n                self.assertTrue((ROOT / "tools" / tool).is_file(), f"{rel}: tools/{tool}")\n        self.assertTrue({"new_video.py", "sync_lib.py", "cadence_scan.py", "probe_cuts.py", "qa.py",\n                         "preview_pack.py", "slice.py"} <= seen, seen)\n\n    def test_qa_doc_names_the_gate_and_waiver_syntax(self):\n        t = (ROOT / "standards" / "core" / "qa.md").read_text()\n        for s in ["python3 tools/qa.py videos/<slug>", "check <n>: <reason>", "python3 tools/preview_pack.py",\n                  "renders/qa-report.json"]:\n            self.assertIn(s, t)\n\n\nif __name__ == "__main__":'),
])
PY
````

- [ ] **Step 2: Run them**

Run: `python3 -m unittest discover -s tools -p 'test_standards_layout.py' -v`
Expected: `Ran 34 tests … OK` — Tasks 1–11 already replaced every placeholder; if one fails, its message names the file and the stale string or missing tool.

- [ ] **Step 3: Tools section in CLAUDE.md, roadmap row**

````bash
python3 - . <<'PY'
import sys
from pathlib import Path
ROOT = Path(sys.argv[1])

def edit(rel, pairs):
    p = ROOT / rel
    s = p.read_text()
    for a, b in pairs:
        assert s.count(a) == 1, (rel, a[:70])
        s = s.replace(a, b)
    p.write_text(s)

edit("CLAUDE.md", [
("""## Tests""",
 """## Tools — `tools/`

`new_video.py` (scaffold a project) · `sync_lib.py` (lib copy + `lib.lock`) · `cadence_scan.py`
(density) · `probe_cuts.py` (Shorts source cuts) · `qa.py` (the automated gate) · `preview_pack.py`
(sign-off pack) · `slice.py` (long-form delivery) · `scan_flicker.py` · `brandcheck.py`. Each prints
its usage with no arguments; the commands in context are in `standards/core/pipeline.md`.

## Tests"""),
])
edit("docs/superpowers/plans/2026-10-03-animation-workflow-roadmap.md", [
("""| 1, 2 (lock hashes, blur/easing scans need lib API names) | **Written:** `2026-10-04-plan-3-tools-and-qa.md` |""",
 """| 1, 2 (lock hashes, blur/easing scans need lib API names) | **Done** (branch `tools-v1`) |"""),
("""## Notes for Plans 3–4 (from the Plan 2 final review)""",
 """## Notes for Plan 4 (from Plan 3)

- `tools/new_video.py` writes `data-hf-mode` on the `#root` of `index.html` and QA check 3 verifies it against the palette; the light-ground glow guard can read `closest("[data-hf-mode]")`. Standalone overlay documents must set it on their own root.
- Over-footage kit layouts (lower-third, side-text, catalogue D) are standalone documents in `compositions/overlays/` rendered with `-c … --format=mov` (a `<template>` sub-composition cannot render alone). Never give a kit element an id/class containing `caption` — QA check 7 reads that as a caption layer.
- Every kit tween takes an `HFProfile.ease` token (or is an `ease: "none"` driver with `onUpdate`); `tools/qa_probe.mjs` flags anything else, including a tween with no ease.
- Reuse in kit tests: `tools/project.py` (BRIEF, beat grid, slots), `tools/media.py`, `tools/synth.py` (lavfi test clips).

## Notes for Plans 3–4 (from the Plan 2 final review)"""),
])
PY
````

- [ ] **Step 4: Full verification**

Run: `python3 -m unittest discover -s tools -p 'test_*.py' -v`
Expected: `Ran 186 tests … FAILED (errors=14)` — the 14 are `test_instantly_*` only (check with `python3 -m unittest discover -s tools -p 'test_*.py' 2>&1 | grep -E '^(ERROR|FAIL):' | grep -v instantly` → no output).
Run: `node --test lib/test/*.test.js tools/*.test.js` → `# pass 84`, `# fail 0`.
Run: `git status --short` → only the three files of this task modified.

- [ ] **Step 5: Commit**

```bash
git add tools/test_standards_layout.py CLAUDE.md docs/superpowers/plans/2026-10-03-animation-workflow-roadmap.md
git commit -m "docs: tools section, Plan 3 placeholders guarded, roadmap marks Plan 3 done

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Self-Review

**1. Spec coverage** (spec §8–§10, `qa.md`, `pipeline.md`, roadmap Plan 3 row and notes):

| Requirement | Task |
|---|---|
| `tools/sync-lib` + `lib.lock` content hashes, check mode | 1 |
| One machine-readable lib manifest shared by sync and the hygiene test; `shorts/wipe.js` kept in its subdirectory; decide what is hashed | 1 (`lib/manifest.json`; modules only) |
| Timing + shutter drift tests; wipe 0.10 s handoff into `timing.wipe`; ease-row parser fails clearly | 2 |
| Extract `lex`/`scan` into a shared module; fold in quoted/template eases, `color-mix`/`lab`/`lch`, `url(#…)`/`.blur()`, `.mjs`/`.cjs`, regex after `return` | 3 |
| `validate_choice` named errors for a missing brand / malformed JSON; `is_colour` fullmatch + 0–255 | 4 |
| BRIEF template marks `direction` (and `film`) required | 5 (template) + 4 (`validate_brief`) |
| `tools/new-video`: BRIEF, beat-grid storyboard, `critique.md`, `assets/captures/MANIFEST.md`, `deliver/`, synced lib | 5 |
| `tools/probe-cuts` (`gt(scene,0.20)`, end = cut + exit) | 6 |
| `tools/scan-flicker` | 6 |
| `tools/cadence-scan` on the storyboard and on the edit (hook ≥ 60 % within `hook_end`, gap ≤ 6 s, body ≤ 30 s, screen-share exempt, punch-ins excluded; Shorts 35–55 %) | 7 |
| `tools/slice`: MP4 clips named by timeline timecode + `TIMECODES.csv` + README; ProRes 4444 alpha for over-footage | 8 |
| QA check 5 inspects the DOM; easing via `isProfileEase` over timeline children; tweens with no ease flagged | 9, 10 |
| `tools/qa`: all ten checks, PASS/FAIL each, uses `brandcheck`, check 3 enforces `status == approved`, exceptions passed and listed | 10 |
| Preview pack: contact sheet, hook + body draft, density timeline, exceptions, critique scores (below 8 first) | 11 |
| Docs: real commands replace "Plan 3" placeholders (CLAUDE.md, pipeline, qa, lib/README, profiles, roadmap) | 1, 3, 5–8, 10–12 |

Deferred on purpose: OCR of rendered text (check 10's "text verified in rendered frames" stays visual — the pack's contact sheet and the critique loop cover it; the gate catches the two known traps and flicker); sound (out of scope, spec §12).

**2. Placeholder scan:** every code step is a complete file or an exact asserted replacement; no TBD/TODO; each task's commands carry their expected output.

**3. Type consistency:** `project.read_storyboard` rows (`row`, `line`, `t_in`, `t_out`, `placement`, `type`, `words`) are what `cadence_scan.report`, `slice.plan`, `qa.scene_windows`, `qa.check_captions` and `preview_pack.graphics` read; `composition_slots` (`id`, `src`, `start`, `dur`) feeds `slice`, `qa` and `preview_pack`; probe findings `{check, message, t}` are merged by `qa.run_gate`; `cadence_scan.report` keys (`full_frame`, `over_footage`, `screen_share`, `hook_end`, `results`) are what `preview_pack.density_svg` draws.

**4. Review Focus:** five lines above, each pinned by named tests in Tasks 4, 6–11.

**Prototype:** every code block in this plan was run in a scratch copy of the repo (git worktree at `4ba20c6`): 186 Python tests (only the 14 baseline `test_instantly_*` errors) and 84 node tests pass. Live checks against HyperFrames 0.8.29: a `new_video` scaffold passes `npx hyperframes check`; the runtime probe through `hyperframes preview` flagged only the seeded raw ease; `qa.py` reported all ten checks PASS on a filled scaffold after the fix; `render -c compositions/overlays/<x>.html --format=mov` produced ProRes 4444 `yuva444p12le`, which `slice.py` accepted; the preview pack showed the scene and the overlay.
