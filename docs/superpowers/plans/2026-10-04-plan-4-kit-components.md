# Plan 4 — Kit Components Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `lib/kit/` — `title`, `subtitle`, `lower-third`, `side-text`, `cta-youtube`, `roadmap`, each a token-driven, seek-safe binder with its first named variant matched to the template stills and the reference video — plus a brand proof sheet (the four templated layouts in every palette) that passes the QA gate, and the lib hooks the Plan 2 and Plan 3 reviews asked for.

**Architecture:** One core file (`lib/kit/kit.js`, global `HFKit`) holds the variant registry, the ground-mode lookup (`closest("[data-hf-mode]")`, throws when missing), the shared ground/glass stylesheet (brand CSS variables only) and the four entrances (card, slide, fade, pop) built on `HFProfile` timings. Each component is one file that registers `HFKit.<camelName>(tl, host, opts)`: it builds its DOM inside a 1920×1080 `host`, adds tweens to the scene's paused timeline using only `HFProfile` eases, `HFCamera`, `HFMarks` and `HFText`, and returns `{ dur, … }`. The lib gains the hooks the kit needs first (one inline-transform owner per element, word/char spans that keep markup, `glowTitle` intensity, kit timings in `HFProfile` with drift tests, a stricter `visibleBeforeStart`, chained wipes proven in the smoke page). Tools: `tools/kit_preview.py` (fixture project for render-and-compare and the kit QA test) and `tools/proof_sheet.py` (one scene per palette, a normal scaffold so `tools/qa.py` runs on it unchanged).

**Tech Stack:** Plain browser JS (each module also loads in node), GSAP 3 (already on the page), node ≥ 22 built-ins (`node:test`), Python 3 standard library (unittest), ffmpeg (synthetic test media), the HyperFrames CLI 0.8.x (`check | snapshot | preview | render`). No new dependencies.

**Spec:** `docs/superpowers/specs/2026-10-03-animation-workflow-design.md` — §6a (long-form catalogue: kit, roadmap, CTA, motion values), §7 (brands: kit variants, onboarding proof sheet), §8 (`lib/kit/`), Appendix A (measured tokens: cards, nodes, glow title, type sizes). Roadmap: `docs/superpowers/plans/2026-10-03-animation-workflow-roadmap.md` — the Plan 4 row, "Notes for Plan 4 (from Plan 3)" and the Plan-4 bullets of "Notes for Plans 3–4 (from the Plan 2 final review)" (all binding). Normative detail: `standards/formats/long-form.md` (catalogue, motion values, ground mode), `brands/contentporary/brand.md` (kit variants, light-ground rules), `brands/contentporary/tokens.json` + `palettes/*.json`, `standards/core/qa.md`, `lib/README.md`. Builds on Plan 3 (`2026-10-04-plan-3-tools-and-qa.md`, merged to `main` at `0a7584d`).

## Global Constraints

- **Format:** the kit is long-form only — 1920×1080, 30 fps (`standards/formats/long-form.md`). Every component throws unless `opts.format === "long-form"`.
- **Built only on lib primitives:** `HFProfile` eases and timings, `HFCamera`, `HFMarks`, `HFText`, and the `HFBrand` CSS variables (`--hf-<role>-<sub>`). No colour literal anywhere in `lib/` (`tools/lawscan.js` ruleset `lib`, enforced by `lib/test/hygiene.test.js`: no hex, no `rgb()/rgba()/hsl()/color-mix()…`), no `cubic-bezier(` outside `profile.js`, no string ease other than a driver's `"none"`, every Gaussian site tagged `data-blur-reason` (`focus` or `glow`) on the same or the previous line.
- **Easing vocabulary (long-form, verbatim):** `ease.camera` `cubic-bezier(0.32, 0, 0.18, 1)` · `ease.camera.slow` `sine.inOut` · `ease.enter` `power3.out` · `ease.sweep` `cubic-bezier(0.47, 0.15, 0.2, 0.95)` · `ease.cut` = `ease.camera` · `ease.glow` `expo.out` · `ease.card` `power2.out`. Every kit tween takes an `HFProfile.ease(format, token)` or is an `ease: "none"` driver with `onUpdate` — the runtime probe (`tools/qa_probe.mjs`, QA check 6) flags anything else, including a tween with no ease.
- **Motion values (verbatim from `long-form.md`):** word entrance — rise ≈ 7 % of frame height + fade + blur→sharp (`focus`), 0.6 s `ease.enter`, stagger 230–330 ms · glow title — pops to ≈ 70 % brightness, settles 0.4 s `ease.glow`, no scale; halo 60–90 px at 1080p; next word +430 ms; dark ground only · card entrance — rise 35–40 px at 720p, 0.43 s `ease.card`, brightens and sharpens · chain gap — 450–500 ms between linked beats; peer sets land together · camera leg 1.1–2.5 s · hold 0.2–4 s, creep ≤ 0.5 %/s · roadmap nodes (Appendix A) — scale 0→1 in 0.45–0.5 s, chained 0.45–0.5 s apart · CTA — the face scales to 0.80 into a YouTube watch-page player (≈ 0.5 s) → camera dives ≈ 2× to the description link → holds ≈ 1.7 s → reverses to the face; every CTA in the video is identical.
- **Type (Appendix A):** headline cap height ≈ 6.5 % H; glow titles 9–12 % H; labels 4–4.6 % H (SF Pro-style medium); script = monoline signature script.
- **Ground mode:** every component reads `data-hf-mode` via `host.closest("[data-hf-mode]")` and THROWS if it is missing (`new_video` writes it on `index.html`'s root; an overlay document sets it on its own root). Light ground (`brand.md`, verbatim): "On the light ground every kit variant drops its glow: dark `text.primary` with a scribble underline or an `accent.block` marker; the roadmap path is drawn in `accent.line` without bloom; side-text panels use frosted white glass instead of the dark grid panel."
- **Variants (`brands/contentporary/tokens.json` `kit`, verbatim):** `title: glow-center` · `subtitle: glass-pill-script` · `lower-third: key-line` · `side-text: grid-panel-chips` · `cta-youtube: watch-page-dive` · `roadmap: wave-nodes`.
- **Palettes (Contentporary, 7):** `red`, `gold`, `lime`, `reel-dark` (dark) · `silver`, `paper`, `reel-light` (light). The proof sheet renders every one.
- **Placement:** over-footage layouts (lower third, side text) are standalone documents in `compositions/overlays/` — no `<template>`, their own `data-hf-mode` root, root-relative paths (`lib/kit/…`, `compositions/brand.css`), rendered with `-c … --format=mov`. Full-frame components are reel scenes (`<template>` sub-compositions in `index.html` slots). Never give a kit element an id/class containing `caption` (QA check 7) and never name one `hf-placeholder` (QA check 1, probe easing exemption).
- **Credibility (core law 9):** UI is a real screenshot or a faithful recreation. The CTA takes a real watch-page screenshot from `assets/captures/` — the kit never draws platform UI.
- **Fonts are not in the repo** (`brands/contentporary/tokens.json`: Satoshi, Helvetica Now Display, SF Pro Display, Brittany Signature live on the shared drive). Without them renders fall back (the script kicker renders as a serif); every visual check below says what to expect either way.
- **Standard library only** for Python; node built-ins only for JS tests; ffmpeg/ffprobe and the HyperFrames CLI are the only external programs. Tests use synthetic inputs only (ffmpeg `lavfi`, temp directories), never footage, never anything under `videos/`.
- **Edit blocks** are `bash` + Python heredocs run from the repo root; every replacement asserts its target appears exactly once and stops naming the file and the first 70 characters otherwise. "Create" blocks are complete files.
- **Test commands:** node — `node --test lib/test/*.test.js tools/*.test.js` (base: `# pass 85`); Python — `python3 -m unittest discover -s tools -p 'test_*.py' -v` (base on `0a7584d`: `Ran 277 tests … FAILED (errors=14)`, the 14 errors are `test_instantly_*`, gitignored media). **After the plan commit** the roadmap row says "Written", so `test_roadmap_marks_plan_3_done_and_plan_4_ready` also fails (`failures=1`) until Task 1 Step 1. Every "expected" count below includes the 14 errors and nothing else failing.
- **Git:** branch `kit-v1` (from `main` `0a7584d`). Before starting: `git status`, `git pull` (CLAUDE.md sync rule; no upstream yet, so `git fetch origin` and report whether `main` moved). One commit per task, staging only the files the task names. Every commit message ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Never push unless Tymek asks.

**Decisions this plan makes beyond the spec — flag to Tymek at review:**
1. **API shape:** `HFKit.<camelName>(tl, host, opts)` → `{ dur, … }` (`HFKit.title`, `subtitle`, `lowerThird`, `sideText`, `ctaYoutube`, `roadmap`). The spec's `kit.subtitle({ variant, kicker, title })` gains the timeline and host every lib binder takes; `opts.variant` defaults to the first registered variant.
2. **Transform guard lives in `HFProfile`:** `HFProfile.claimTransform(el, owner)` — every module already loads `profile.js`. Camera, marks, `HFText.words` and every kit entrance claim; a second, different owner throws naming both; the same owner may claim again.
3. **Kit timings are `HFProfile` timings** (long-form): `card {dur 0.43, riseFrac 37.5/720}`, `chainGap 0.475`, `node {dur 0.48, gap 0.48}`, `cta {scale 0.8, scaleDur 0.5, dive 2, diveDur 0.6, hold 1.7}`, each drift-tested against `long-form.md` / Appendix A. `diveDur` 0.6 s and the CTA's 0.5 s player holds are measured from the reference (117.2–117.8 s, 116.7–117.2 s), not in the profile text.
4. **Kit CSS keys off a resolved-mode class** (`hf-kit-dark` / `hf-kit-light`, set on the host by `begin()`), not `[data-hf-mode]` selectors: a descendant selector also matches a farther ancestor, so a light proof-sheet scene inside a dark `index.html` root rendered its title in the dark-mode accent colour (found while prototyping).
5. **The CTA takes a real screenshot** (`page: {src, width, height, player, link}`) and uses a **DOM camera — no motion blur on the 0.6 s dive** (the reference shows some): baking live footage into a blur texture needs `liveBake` over HyperFrames' injected video frames, deferred to the pilot. The CTA ends on the live face; if it moves in the last 0.3 s, the BRIEF waives `check 9 [<slot id>]`.
6. **Visual calibration against the stills:** kit glow titles settle at bloom 0.6 (`HFKit.GLOW`; new `HFText.glowTitle` option `intensity`, lib default stays 1.2, which smears at 1080p); ground grid cell 150 px (the stills; `brand.md` says ≈ 4 columns from the reference video); grid and dots drawn with `mix-blend-mode: screen` (dark) / `multiply` (light) so the palettes' sampled grid colours read lighter / darker than the ground as in the stills; the title's warm top glow uses `--hf-extras-ambient-glow` (only `gold` has it) and falls back to `--hf-ground-centre`; the light grid stays faintly visible on `paper` (`brand.md`: no grid on paper).
7. **Proof sheet is its own tool** (`tools/proof_sheet.py <brand>`), not a `new_video` option: it is a brand artefact (N palette scenes, regenerated when palettes change), not a video, and keeping it separate keeps `new_video` single-purpose. It calls `new_video.scaffold`, so the project is a normal one and `tools/qa.py` runs on it unchanged: each scene carries its palette as inline CSS variables (`lib/brand.js --json`) plus its own `data-hf-mode`; `index.html` keeps the BRIEF palette (QA check 3). A `draft` brand fails check 3 until approved — by design.
8. **`tools/kit_preview.py`** (beyond the spec): one fixture project for every component — used by each component's render-and-compare step and by the kit QA test, and the place to preview new variants later.
9. **Catalogue D1/D2 are not kit variants yet:** the stat tiles (stills 4/5) and side screenshot + script (still 7) stay custom builds; candidates for variants after the pilot.
10. **`HFWipe` phase edges snap within 1 µs:** the new chained-phase smoke case found that a host seeked back to before its out-wipe kept the out-phase's first sliver (mask 100 %/108 % with the blur filter attached), because GSAP reports the driver's start (0.9999999999999999) as 1.
11. **Roadmap geometry:** nodes every 640 px from x = 320 (3 steps fill exactly 1920 px), alternating y 700 / 520; system name two lines in a 1300 px column; camera 1.25× on card k with a 1.6 s leg; four built-in line icons (`bulb`, `sliders`, `chart`, `target`).
12. **Side text default timing:** points one per two chain gaps (0.95 s) from half-way through the panel slide, unless each `items[i].at` is given; the lower third's white → warm gradient is `text.primary` → `accent.text`, painted per word (avoids render trap 1, "centred gradient text with transformed word spans") and re-measured when fonts land.
13. **Kit components measure text:** compositions build them after `await document.fonts.ready` and register the timeline after `await HFText.ready()` (the CTA's page decode and the lower third's re-measure are tracked there).

## Review Focus

1. **A scene whose ground mode differs from the page root, or an overlay with no mode at all** — the proof sheet nests light palette scenes in a dark `index.html`; an overlay document is its own page. Expected: each kit host styles by its nearest `data-hf-mode`; no mode anywhere is a named error, never a default. Found while prototyping. Tests: Task 5 `begin(): long-form only, a host, a time ≥ 0; puts the resolved mode on the host as a class`, every component's contract test `throws when no ancestor sets data-hf-mode`, Task 14 `test_each_scene_carries_its_palette_and_mode`.
2. **Seeking backward into a host that is wiped in and later wiped out** (chained `HFWipe.phase` → `phase`). Expected: the same frame whatever the seek order. Found while prototyping (the smoke page failed at t = 0.62 and 0.8). Tests: Task 4 `wipeProgress: phase edges snap…` and the smoke page's chained-phase samples.
3. **Two binders animating one element's transform** — a kit card that a camera also pushes, a highlight on a word span. Expected: a build-time error naming both owners, not a frame-by-frame fight. Tests: Task 1 `claimTransform…`, `rig and push refuse…`, `highlight / statusChip refuse…`; Task 2 `words: … each span is claimed`; Task 5 `entrances … HFKit.cardIn would overwrite … HFKit.pop`.
4. **Roadmap continuity across chapters and step counts** — visit k must open exactly where visit k−1 ended; 3 vs 5–6 steps widen the world. Expected: identical camera pose and docked cards at the cut; nodes every 640 px. Tests: Task 12 `roadmap visit k opens exactly where visit k-1 ended`, `roadmap geometry: … world widens past 3 steps`.
5. **An over-footage layout that never settles or exits too early** — `out` before the last word lands, or a fade still running in the overlay's last 0.3 s (QA check 9 on overlays). Expected: the binder refuses an `out` that leaves no hold; the gate renders each overlay and checks its tail. Tests: Task 9 `lower-third: text required; opts.out must leave a hold`, Task 10 `side-text: explicit item times, 1–6 points…`, Task 13 `test_every_kit_component_passes_the_gate` (overlays probed and rendered) and `test_a_kit_scene_named_caption_fails_check_7`.

---

## File Structure

```
lib/profile.js                 MODIFY  claimTransform(el, owner); long-form TIMING card / chainGap / node / cta
lib/camera.js, lib/marks.js    MODIFY  claim transforms; marks.scriptWord splits with HFText.splitChars + onSpans
lib/text.js                    MODIFY  splitWords / splitChars (keep markup), onSpans on words / typeOn,
                                       words claims spans, glowTitle opts.intensity, accentWord installs CSS,
                                       exports blurPx, track
lib/shorts/wipe.js             MODIFY  phase edges snap (EDGE = 1e-6)
lib/examples/smoke.html        MODIFY  chained phase → phase wipes on one host
lib/manifest.json              MODIFY  kit/ modules + loadOrder (after brand.js, kit.js first)
lib/kit/kit.js                 NEW     HFKit core: registry, mode, begin, ground, glass CSS, cardIn/slideIn/fadeOut/pop
lib/kit/title.js               NEW     HFKit.title — glow-center
lib/kit/subtitle.js            NEW     HFKit.subtitle — glass-pill-script
lib/kit/lower-third.js         NEW     HFKit.lowerThird — key-line
lib/kit/side-text.js           NEW     HFKit.sideText — grid-panel-chips
lib/kit/cta-youtube.js         NEW     HFKit.ctaYoutube — watch-page-dive
lib/kit/roadmap.js             NEW     HFKit.roadmap — wave-nodes
lib/test/helpers.js            MODIFY  fakeText/fakeMixed, classList/closest/hasAttribute, kitHost, descendants,
                                       serialize, parseTransform; visibleBeforeStart compares transform + filter
lib/test/helpers.test.js       NEW     the test doubles' own tests
lib/test/kit-contract.js       NEW     the contract every kit component keeps (shared by the kit tests)
lib/test/kit.test.js           NEW     core: registry, begin/mode, CSS, entrances
lib/test/kit-<component>.test.js NEW   one per component (contract + layout/timing)
lib/test/{profile,drift,camera,marks,text,wipe}.test.js  MODIFY  new hooks
tools/new_video.py             MODIFY  kit/ modules load in long-form projects only
tools/kit_preview.py           NEW     fixture project of kit components (render-and-compare, kit QA test)
tools/proof_sheet.py           NEW     brand proof sheet: one kit scene per palette
tools/test_kit_preview.py, tools/test_kit_qa.py, tools/test_proof_sheet.py   NEW
tools/test_new_video.py, tools/test_sync_lib.py, tools/test_standards_layout.py   MODIFY
lib/README.md, standards/formats/long-form.md, brands/contentporary/brand.md,
brands/_template/README.md, CLAUDE.md, roadmap   MODIFY  kit section, kit table, variant names, proof-sheet step
```

The template stills Tymek shared (2026-10-03) are the visual reference: `1.png` (full-screen title, gold), `2.png` (step card / subtitle), `3.webp` (lower third key line), `4.webp` / `5.webp` (stat tiles over the face — catalogue D1, not built here), `6.webp` (side screen text), `7.webp` (side screenshot + script + highlight — D2, not built here); reference-video strips: roadmap ≈ 59.5–68 s and 126.7–131.9 s, CTA 116.2–121.8 s of HrYMfy6MZtA. They are not in the repo; if they are not on your machine, ask Tymek — every render-and-compare step also lists measured acceptance numbers so it can be judged without them.

Render-and-compare frames go under `renders/` (gitignored). Kill every server you start (`npx hyperframes preview --stop`, the `http.server` in Task 4).

---

### Task 1: Transform guard + kit timings in `HFProfile` (and the roadmap test follows the written plan)

**Files:**
- Modify: `tools/test_standards_layout.py` (roadmap row 4 now says Written), `lib/profile.js`, `lib/camera.js`, `lib/marks.js`
- Test: `lib/test/profile.test.js`, `lib/test/drift.test.js`, `lib/test/camera.test.js`, `lib/test/marks.test.js`

**Interfaces:**
- Consumes: `HFProfile.timing(format)` (deep copy of `TIMING[format]`), the drift-test helpers `nums(file, re)` / `close(lib, md, what)` in `lib/test/drift.test.js`.
- Produces:
  - `HFProfile.claimTransform(el, owner: string) -> el` — sets `el.__hfTransformOwner`; throws `HFProfile: <owner> would overwrite the inline transform that <prev> animates on this element — wrap the element and give each binder its own` when a different owner claimed it; throws `HFProfile.claimTransform: <owner> got no element` for a non-object.
  - Owners used across the lib: `"HFCamera.rig"` (stage), `"HFCamera.push"`, `"HFMarks.highlight"`, `"HFMarks.statusChip"`, `"HFMarks.seedChip"` (this task); `"HFText.words"` (Task 2); `"HFKit.cardIn"`, `"HFKit.slideIn"`, `"HFKit.pop"` (Task 5).
  - `HFProfile.timing("long-form")` gains `card: {dur: 0.43, riseFrac: 37.5/720}`, `chainGap: 0.475`, `node: {dur: 0.48, gap: 0.48}`, `cta: {scale: 0.8, scaleDur: 0.5, dive: 2, diveDur: 0.6, hold: 1.7}`; `timing("shorts")` has none of them.
  - `HFCamera.rig` throws `HFCamera.rig: stage is required` when `cfg.stage` is missing.

- [ ] **Step 1: Make the roadmap layout test follow the written plan**

The plan commit set the roadmap's Plan 4 row to **Written:** `2026-10-04-plan-4-kit-components.md`, so `test_roadmap_marks_plan_3_done_and_plan_4_ready` fails on a fresh checkout. Run: `python3 -m unittest discover -s tools -p 'test_standards_layout.py'` → Expected: `FAILED (failures=1)`, `AssertionError: 'Ready to write' not found in '| 4 | **Kit components** …`. The test edit is part of the first edit block below (Step 3); it renames the test to `test_roadmap_marks_plan_3_done_and_plan_4_written`.

- [ ] **Step 2: Write the failing tests**

````bash
cat >> lib/test/profile.test.js <<'EOF'

test("claimTransform: one inline-transform owner per element, named in the error", function () {
  var el = {};
  assert.equal(P.claimTransform(el, "HFCamera.push"), el);
  assert.doesNotThrow(function () { P.claimTransform(el, "HFCamera.push"); }, "the same owner may claim again");
  assert.throws(function () { P.claimTransform(el, "HFMarks.highlight"); },
    /HFMarks\.highlight would overwrite the inline transform that HFCamera\.push animates on this element/);
  assert.throws(function () { P.claimTransform(null, "HFText.words"); }, /HFText\.words got no element/);
});

test("kit timings: card entrance, chain gap, roadmap nodes, CTA (long-form only)", function () {
  var T = P.timing("long-form");
  assert.deepEqual(T.card, { dur: 0.43, riseFrac: 37.5 / 720 });
  assert.equal(T.chainGap, 0.475);
  assert.deepEqual(T.node, { dur: 0.48, gap: 0.48 });
  assert.deepEqual(T.cta, { scale: 0.8, scaleDur: 0.5, dive: 2, diveDur: 0.6, hold: 1.7 });
  assert.equal(P.timing("shorts").card, undefined);
});
EOF
````

````bash
cat >> lib/test/drift.test.js <<'EOF'

test("kit TIMING matches long-form.md (card entrance, chain gap, CTA) and the spec appendix (roadmap nodes)", function () {
  var T = P.timing("long-form");
  var rise = nums("long-form.md", /\| card entrance \| rise (\d+)–(\d+) px at (\d+)p, ([\d.]+) s `ease\.card`/);
  assert.ok(T.card.riseFrac * rise[2] >= rise[0] && T.card.riseFrac * rise[2] <= rise[1], "card.riseFrac inside " + rise[0] + "–" + rise[1] + " px at " + rise[2] + "p");
  close(T.card.dur, rise[3], "card.dur");
  var gap = nums("long-form.md", /\| chain gap \| (\d+)–(\d+) ms between linked beats/);
  assert.ok(T.chainGap * 1000 >= gap[0] && T.chainGap * 1000 <= gap[1], "chainGap inside " + gap.join("–") + " ms");
  var node = nums("spec", /Roadmap nodes: scale 0→1 in ([\d.]+)–([\d.]+) s, chained ([\d.]+)–([\d.]+) s apart/);
  assert.ok(T.node.dur >= node[0] && T.node.dur <= node[1], "node.dur inside " + node[0] + "–" + node[1] + " s");
  assert.ok(T.node.gap >= node[2] && T.node.gap <= node[3], "node.gap inside " + node[2] + "–" + node[3] + " s");
  var cta = nums("long-form.md", /face scales to ([\d.]+) into a YouTube watch-page player \(≈ ([\d.]+) s\) → camera\s+dives ≈ (\d+)× to the description link → holds ≈ ([\d.]+) s/);
  close(T.cta.scale, cta[0], "cta.scale");
  close(T.cta.scaleDur, cta[1], "cta.scaleDur");
  close(T.cta.dive, cta[2], "cta.dive");
  close(T.cta.hold, cta[3], "cta.hold");
});
EOF
````

````bash
cat >> lib/test/camera.test.js <<'EOF'

test("rig and push refuse an element another binder already transforms", function () {
  var el = h.fakeEl("div");
  C.push(h.fakeTimeline(), el, [{ T: 0, dur: 1, from: 1, to: 1.04 }], { format: "long-form" });
  assert.throws(function () { C.rig(h.fakeTimeline(), { format: "long-form", width: 1920, height: 1080, stage: el, dur: 1, keys: [{ t: 0, cx: 960, cy: 540, z: 1 }] }); },
    /HFCamera\.rig would overwrite the inline transform that HFCamera\.push animates/);
  assert.throws(function () { C.rig(h.fakeTimeline(), { format: "long-form", width: 1920, height: 1080, dur: 1, keys: [{ t: 0, cx: 0, cy: 0, z: 1 }] }); }, /stage is required/);
});
EOF
````

````bash
cat >> lib/test/marks.test.js <<'EOF'

test("highlight / statusChip refuse an element another binder transforms", function () {
  var el = h.fakeEl("div");
  M.highlight(h.fakeTimeline(), el, 0, LF);
  assert.throws(function () { M.statusChip(h.fakeTimeline(), el, 0, LF); }, /HFMarks\.statusChip would overwrite the inline transform that HFMarks\.highlight animates/);
});
EOF
````

Run: `node --test lib/test/profile.test.js lib/test/drift.test.js lib/test/camera.test.js lib/test/marks.test.js`
Expected: FAIL — `P.claimTransform is not a function`; `Cannot read properties of undefined (reading 'riseFrac')` (drift); `Missing expected exception` (camera, marks).

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
        if s.count(a) != 1:
            sys.exit(f"{rel}: expected exactly one match for: {a[:70]!r}")
        s = s.replace(a, b)
    p.write_text(s)

edit("lib/profile.js", [
    ("""      typeOnMsPerChar: null          // long-form text is word by word; a UI type-on must pass msPerChar
    },""",
     """      typeOnMsPerChar: null,         // long-form text is word by word; a UI type-on must pass msPerChar
      card: { dur: 0.43, riseFrac: 37.5 / 720 },                 // card entrance: rise 35–40 px at 720p, 0.43 s ease.card
      chainGap: 0.475,                                            // chain gap 450–500 ms between linked beats
      node: { dur: 0.48, gap: 0.48 },                             // roadmap nodes: scale 0→1 in 0.45–0.5 s, 0.45–0.5 s apart (spec App. A)
      cta: { scale: 0.8, scaleDur: 0.5, dive: 2, diveDur: 0.6, hold: 1.7 }   // CTA template; diveDur: measured 0.6 s (lib default)
    },"""),
    ("""  function isProfileEase(fn) { return typeof fn === "function" && !!fn.token && cache[fn.format + "|" + fn.token] === fn; }
""",
     """  function isProfileEase(fn) { return typeof fn === "function" && !!fn.token && cache[fn.format + "|" + fn.token] === fn; }

  /* One inline-transform writer per element. HFCamera (stage, push), HFMarks (highlight, chips), HFText
   * (words) and every HFKit component overwrite el.style.transform; two of them on one element fight
   * frame by frame. Each binder claims the element first; a second, different owner throws naming both.
   * The same owner may claim again (e.g. a kit component re-binding its own parts). Wrap one element in
   * another to combine two transforms. Lives here because every module already loads profile.js. */
  function claimTransform(el, owner) {
    if (!el || typeof el !== "object") throw new Error("HFProfile.claimTransform: " + owner + " got no element");
    var prev = el.__hfTransformOwner;
    if (prev && prev !== owner) {
      throw new Error("HFProfile: " + owner + " would overwrite the inline transform that " + prev +
        " animates on this element — wrap the element and give each binder its own");
    }
    el.__hfTransformOwner = owner;
    return el;
  }
"""),
    ("""    tokens: tokens, timing: timing, isProfileEase: isProfileEase };""",
     """    tokens: tokens, timing: timing, isProfileEase: isProfileEase, claimTransform: claimTransform };"""),
])
edit("lib/camera.js", [
    ("""    var stage = cfg.stage, canvas = cfg.canvas || null;""",
     """    var stage = cfg.stage, canvas = cfg.canvas || null;
    if (!stage) throw new Error("HFCamera.rig: stage is required");
    P.claimTransform(stage, "HFCamera.rig");"""),
    ("""    if (el.__hfPush) throw new Error("HFCamera.push: element already has pushes — pass every segment in one call");""",
     """    if (el.__hfPush) throw new Error("HFCamera.push: element already has pushes — pass every segment in one call");
    P.claimTransform(el, "HFCamera.push");"""),
])
edit("lib/marks.js", [
    ("""    var w = el.offsetWidth || 1, dur = opts.dur || sweepDuration(w, opts.frameHeight, opts.format);""",
     """    P.claimTransform(el, "HFMarks.highlight");
    var w = el.offsetWidth || 1, dur = opts.dur || sweepDuration(w, opts.frameHeight, opts.format);"""),
    ("""    [].concat(els).forEach(function (e) { e.style.opacity = "0"; e.style.transform = "translateY(" + y0 + "px) scale(0.6)"; });""",
     """    [].concat(els).forEach(function (e) { P.claimTransform(e, "HFMarks.statusChip"); e.style.opacity = "0"; e.style.transform = "translateY(" + y0 + "px) scale(0.6)"; });"""),
    ("""    var e = P.ease(opts.format, "ease.enter"), hgt = parts.pill.offsetHeight || 1, w = parts.pill.offsetWidth || 1;""",
     """    P.claimTransform(parts.pill, "HFMarks.seedChip");
    var e = P.ease(opts.format, "ease.enter"), hgt = parts.pill.offsetHeight || 1, w = parts.pill.offsetWidth || 1;"""),
])
edit("tools/test_standards_layout.py", [
    ("""    def test_roadmap_marks_plan_3_done_and_plan_4_ready(self):
        t = (ROOT / "docs/superpowers/plans/2026-10-03-animation-workflow-roadmap.md").read_text()
        row3 = [l for l in t.splitlines() if l.startswith("| 3 |")][0]
        row4 = [l for l in t.splitlines() if l.startswith("| 4 |")][0]
        self.assertIn("**Done** (branch `tools-v1`)", row3)
        self.assertIn("Ready to write", row4)""",
     """    def test_roadmap_marks_plan_3_done_and_plan_4_written(self):
        t = (ROOT / "docs/superpowers/plans/2026-10-03-animation-workflow-roadmap.md").read_text()
        row3 = [l for l in t.splitlines() if l.startswith("| 3 |")][0]
        row4 = [l for l in t.splitlines() if l.startswith("| 4 |")][0]
        self.assertIn("**Done** (branch `tools-v1`)", row3)
        self.assertIn("**Written:** `2026-10-04-plan-4-kit-components.md`", row4)
        self.assertTrue((ROOT / "docs/superpowers/plans/2026-10-04-plan-4-kit-components.md").is_file())"""),
])
print("Task 1 edits applied")
PY
````

- [ ] **Step 4: Run the tests**

Run: `node --test lib/test/*.test.js tools/*.test.js`
Expected: `# pass 90` `# fail 0`.
Run: `python3 -m unittest discover -s tools -p 'test_standards_layout.py'`
Expected: `Ran 37 tests … OK`.

- [ ] **Step 5: Commit**

````bash
git add lib/profile.js lib/camera.js lib/marks.js lib/test/profile.test.js lib/test/drift.test.js lib/test/camera.test.js lib/test/marks.test.js tools/test_standards_layout.py
git commit -m "feat(lib): one inline-transform owner per element; kit timings in HFProfile with drift tests" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
````

---

### Task 2: Word and character spans that keep markup; `glowTitle` intensity; `accentWord` installs its CSS

**Files:**
- Modify: `lib/text.js`, `lib/marks.js`, `lib/test/helpers.js`
- Test: `lib/test/text.test.js`, `lib/test/marks.test.js`

**Interfaces:**
- Consumes: `HFProfile.claimTransform` (Task 1).
- Produces:
  - `HFText.splitWords(el) -> [span]` / `HFText.splitChars(el) -> [span]` — every text node under `el` becomes one span per word (trailing whitespace collapsed to one space inside the span; a text node's leading whitespace becomes one `" "` text node) or per code point; element children stay in place (their own text is split inside them); an element with `data-hf-nosplit` is left whole. A node without `childNodes` (the test DOM) is treated as one text node.
  - `HFText.words(tl, el, T, opts)` / `HFText.typeOn(…)` / `HFMarks.scriptWord(…)` call `opts.onSpans(spans)` with the spans they animate; `words` claims each span (`"HFText.words"`).
  - `HFText.glowTitle(tl, words, T, opts)` — `opts.intensity` (default `GLOW_DEFAULTS.intensity` = 1.2) is the settled bloom; negative throws `HFText.glowTitle: opts.intensity must be ≥ 0`.
  - `HFText.accentWord(tl, el, T)` installs `<style id="hf-text-css">` itself, once.
  - New exports: `HFText.blurPx(el, reason, px) -> "blur(<px>px)"` (tags the element), `HFText.track(promise)` (what `ready()` waits on).
  - `lib/test/helpers.js`: `fakeText(s)`, `fakeMixed(tag, nodes)` (an element whose `childNodes` hold text nodes and elements), `fakeDocument()` gains `createTextNode`, `createDocumentFragment` (`isFragment`), `head`, `body`; `fakeEl`'s `textContent` is configurable.

- [ ] **Step 1: Write the failing tests**

````bash
cat >> lib/test/text.test.js <<'EOF'

test("splitWords keeps nested markup: words inside <b> stay inside it, spaces stay in their words", function () {
  var b = h.fakeMixed("b", [h.fakeText("Prediction")]);
  var el = h.fakeMixed("h1", [h.fakeText("HIT "), b, h.fakeText(" works  now")]);
  var spans = X.splitWords(el);
  assert.deepEqual(spans.map(function (s) { return s.textContent; }), ["HIT ", "Prediction", "works ", "now"]);
  assert.equal(el.childNodes[1], b);
  assert.equal(b.childNodes[0], spans[1], "the word span sits inside the <b>");
  assert.equal(el.childNodes[2].nodeType, 3, "leading whitespace of a text node becomes one space text node");
  var skip = h.fakeMixed("em", [h.fakeText("as is")]); skip.setAttribute("data-hf-nosplit", "");
  var el2 = h.fakeMixed("p", [h.fakeText("a "), skip]);
  assert.equal(X.splitWords(el2).length, 1, "data-hf-nosplit children are left whole");
});

test("words: opts.onSpans receives the word spans; each span is claimed for its transform", function () {
  var tl = h.fakeTimeline(), el = h.fakeEl("h1", { text: "one two three" }), got = null;
  X.words(tl, el, 0, Object.assign({ onSpans: function (s) { got = s; } }, LF));
  assert.equal(got.length, 3);
  assert.equal(got[0], el.children[0]);
  assert.throws(function () { require("../marks.js").highlight(h.fakeTimeline(), got[0], 1, LF); }, /HFMarks\.highlight would overwrite the inline transform that HFText\.words animates/);
});

test("typeOn: opts.onSpans gets the character spans (before carets are added)", function () {
  var tl = h.fakeTimeline(), got = null;
  X.typeOn(tl, h.fakeEl("span", { text: "Hey" }), 0, { format: "shorts", blinks: 0, onSpans: function (s) { got = s.map(function (x) { return x._text; }); } });
  assert.deepEqual(got, ["H", "e", "y"]);
});

test("glowTitle: opts.intensity sets the settled bloom (default 1.2)", function () {
  var slopes = {}, saved = document.getElementById;
  document.getElementById = function (id) { return { setAttribute: function (k, v) { slopes[id] = v; } }; };
  try {
    var tl = h.fakeTimeline();
    X.glowTitle(tl, [h.fakeEl("span")], 0, Object.assign({ glowId: "gi", intensity: 0.6 }, LF));
    tl.seek(5); assert.equal(slopes["gi-r"], "0.6000");
    var tl2 = h.fakeTimeline();
    X.glowTitle(tl2, [h.fakeEl("span")], 0, Object.assign({ glowId: "gd" }, LF));
    tl2.seek(5); assert.equal(slopes["gd-r"], "1.2000");
    assert.throws(function () { X.glowTitle(h.fakeTimeline(), [h.fakeEl("span")], 0, Object.assign({ glowId: "gx", intensity: -1 }, LF)); }, /intensity must be ≥ 0/);
  } finally { document.getElementById = saved; }
});

test("accentWord installs its stylesheet itself, once", function () {
  var appended = [], present = false, savedGet = document.getElementById, savedHead = document.head;
  document.getElementById = function (id) { return id === "hf-text-css" && present ? {} : null; };
  document.head = { appendChild: function (s) { appended.push(s); present = true; } };
  try {
    var tl = h.fakeTimeline();
    X.accentWord(tl, h.fakeEl("span"), 1);
    X.accentWord(tl, h.fakeEl("span"), 2);
    assert.equal(appended.length, 1);
    assert.equal(appended[0].textContent, X.CSS);
  } finally { document.getElementById = savedGet; document.head = savedHead; }
});

test("blurPx tags the element and returns the CSS string; track() is what ready() waits on", async function () {
  var el = h.fakeEl("div");
  assert.equal(X.blurPx(el, "focus", 4), "blur(4px)");
  assert.equal(el.getAttribute("data-blur-reason"), "focus");
  var release, p = new Promise(function (r) { release = r; }), done = false;
  X.track(p);
  var r = X.ready().then(function () { done = true; });
  await Promise.resolve();
  assert.equal(done, false);
  release(); await r;
  assert.equal(done, true);
});
EOF
````

````bash
cat >> lib/test/marks.test.js <<'EOF'

test("scriptWord: opts.onSpans gets the letter spans; nested markup is kept", function () {
  var tl = h.fakeTimeline(), got = null;
  var b = h.fakeMixed("b", [h.fakeText("p 1")]), el = h.fakeMixed("span", [h.fakeText("St"), b]);
  M.scriptWord(tl, el, 0, { format: "long-form", onSpans: function (s) { got = s; } });
  assert.deepEqual(got.map(function (s) { return s.textContent; }), ["S", "t", "p", " ", "1"]);
  assert.equal(el.childNodes[2], b, "the <b> stays in place");
  assert.equal(b.childNodes.length, 3);
  assert.equal(tl.tweens.length, 5);
});
EOF
````

Run: `node --test lib/test/text.test.js lib/test/marks.test.js`
Expected: FAIL — `h.fakeMixed is not a function`, `X.splitWords is not a function`, `X.blurPx is not a function`; `glowTitle: opts.intensity` sees slope `1.2000` where `0.6000` is expected.

- [ ] **Step 2: Implement**

````bash
python3 - . <<'PY'
import sys
from pathlib import Path
ROOT = Path(sys.argv[1])

def edit(rel, pairs):
    p = ROOT / rel
    s = p.read_text()
    for a, b in pairs:
        if s.count(a) != 1:
            sys.exit(f"{rel}: expected exactly one match for: {a[:70]!r}")
        s = s.replace(a, b)
    p.write_text(s)

edit("lib/text.js", [
    ("""  function layoutOk(el) { el.setAttribute("data-layout-allow-overlap", ""); el.setAttribute("data-layout-allow-occlusion", ""); }
""",
     """  function layoutOk(el) { el.setAttribute("data-layout-allow-overlap", ""); el.setAttribute("data-layout-allow-occlusion", ""); }

  /* ---------- splitting text into spans, keeping nested markup ----------
   * splitWords(el) / splitChars(el) replace every text node under el with one span per word (trailing
   * whitespace collapsed to one space, kept inside the span) or per code point, and return the spans in
   * reading order. Element children (<b>, an accent <span>, a <br>) stay where they are, so their styling
   * survives; an element marked data-hf-nosplit is left whole. A node without childNodes (the test DOM)
   * is treated as one text node. */
  function splitText(el, tokenize) {
    var out = [];
    function span(tok) { var s = document.createElement("span"); s.textContent = tok; out.push(s); return s; }
    if (!el.childNodes) {
      var text = el.textContent; el.textContent = "";
      tokenize(text).forEach(function (tok) { el.appendChild(span(tok)); });
      return out;
    }
    (function walk(node) {
      Array.prototype.slice.call(node.childNodes).forEach(function (c) {
        if (c.nodeType === 3) {
          var frag = document.createDocumentFragment(), toks = tokenize(c.nodeValue);
          if (/^\\s/.test(c.nodeValue) && toks.length && tokenize === wordTokens) frag.appendChild(document.createTextNode(" "));
          toks.forEach(function (tok) { frag.appendChild(span(tok)); });
          node.replaceChild(frag, c);
        } else if (c.nodeType === 1 && !(c.hasAttribute && c.hasAttribute("data-hf-nosplit"))) walk(c);
      });
    })(el);
    return out;
  }
  function wordTokens(text) { return (text.match(/\\S+\\s*/g) || []).map(function (t) { return t.replace(/\\s+$/, " "); }); }
  function charTokens(text) { return Array.from(text); }     // code points: never split a surrogate pair
  function splitWords(el) { return splitText(el, wordTokens); }
  function splitChars(el) { return splitText(el, charTokens); }
"""),
    ("""    var parts = el.textContent.split(/\\s+/).filter(Boolean);
    el.textContent = "";
    if (!parts.length) return 0;
    var rise = w.riseFrac * opts.frameHeight, blur = (w.blurFrac * opts.frameHeight).toFixed(2);
    var e = P.ease(opts.format, "ease.enter");
    parts.forEach(function (word, i) {
      var s = document.createElement("span"), fIn = blurPx(s, "focus", blur), fOut = blurPx(s, "focus", 0);
      s.textContent = word + (i < parts.length - 1 ? " " : "");
      s.style.display = "inline-block"; s.style.whiteSpace = "pre"; s.style.opacity = "0";
      // Build-time style = the full from-state (opacity + rise + blur), so forward and backward seeks agree before T.
      s.style.transform = "translate(0px, " + rise + "px)"; s.style.filter = fIn; layoutOk(s);
      el.appendChild(s);
      tl.fromTo(s, { opacity: 0, y: rise, filter: fIn },
        { opacity: 1, y: 0, filter: fOut, duration: w.dur, ease: e, immediateRender: false }, T + i * stagger);
    });
    return (parts.length - 1) * stagger + w.dur;""",
     """    var spans = splitWords(el);
    if (opts.onSpans) opts.onSpans(spans);
    if (!spans.length) return 0;
    var rise = w.riseFrac * opts.frameHeight, blur = (w.blurFrac * opts.frameHeight).toFixed(2);
    var e = P.ease(opts.format, "ease.enter");
    spans.forEach(function (s, i) {
      var fIn = blurPx(s, "focus", blur), fOut = blurPx(s, "focus", 0);
      P.claimTransform(s, "HFText.words");
      s.style.display = "inline-block"; s.style.whiteSpace = "pre"; s.style.opacity = "0";
      // Build-time style = the full from-state (opacity + rise + blur), so forward and backward seeks agree before T.
      s.style.transform = "translate(0px, " + rise + "px)"; s.style.filter = fIn; layoutOk(s);
      tl.fromTo(s, { opacity: 0, y: rise, filter: fIn },
        { opacity: 1, y: 0, filter: fOut, duration: w.dur, ease: e, immediateRender: false }, T + i * stagger);
    });
    return (spans.length - 1) * stagger + w.dur;"""),
    ("""    var chars = Array.from(el.textContent); el.textContent = "";   // code points: never split a surrogate pair
    var spans = [], carets = [];
    for (var i = 0; i < chars.length; i++) {
      var sp = document.createElement("span"); sp.textContent = chars[i];
      sp.style.display""",
     """    var spans = splitChars(el), chars = spans.map(function (sp) { return sp.textContent; }), carets = [];
    if (opts.onSpans) opts.onSpans(spans);
    for (var i = 0; i < spans.length; i++) {
      var sp = spans[i];
      sp.style.display"""),
    ("""      sp.appendChild(c); el.appendChild(sp); spans.push(sp); carets.push(c);""",
     """      sp.appendChild(c); carets.push(c);"""),
    ("""   * next word +430 ms. One driver: opacity/bloom are pure functions of t. */""",
     """   * next word +430 ms. One driver: opacity/bloom are pure functions of t.
   * opts.intensity: the settled bloom strength (default GLOW_DEFAULTS.intensity, 1.2). */"""),
    ("""    var g = P.timing(opts.format).glow, els = [].concat(wordEls), k = opts.frameHeight / 1080;""",
     """    var g = P.timing(opts.format).glow, els = [].concat(wordEls), k = opts.frameHeight / 1080;
    var peak = opts.intensity == null ? GLOW_DEFAULTS.intensity : opts.intensity;
    if (!(peak >= 0)) throw new Error("HFText.glowTitle: opts.intensity must be ≥ 0");"""),
    ("""      setGlowIntensity(id, (GLOW_DEFAULTS.intensity * glowOpacity(drv.t - T, opts.format)).toFixed(4));""",
     """      setGlowIntensity(id, (peak * glowOpacity(drv.t - T, opts.format)).toFixed(4));"""),
    ("""    (document.head || document.documentElement).appendChild(s);
  }
  function accentWord(tl, el, T) { tl.set(el, { attr: { "data-hf-accent": "1" } }, T); }""",
     """    (document.head || document.documentElement || document.body).appendChild(s);
  }
  // Installs its own stylesheet (idempotent), so a caller never has to remember installCss().
  function accentWord(tl, el, T) { installCss(); tl.set(el, { attr: { "data-hf-accent": "1" } }, T); }"""),
    ("""    rasterText: rasterText, ready: ready, GLOW_DEFAULTS: GLOW_DEFAULTS };""",
     """    rasterText: rasterText, ready: ready, track: track, blurPx: blurPx, splitWords: splitWords, splitChars: splitChars, GLOW_DEFAULTS: GLOW_DEFAULTS };"""),
])
edit("lib/marks.js", [
    (""" * Load after profile.js.
""", """ * Load after profile.js; scriptWord also needs text.js on the page (resolved when called).
"""),
    ("""  var P = NODE ? require("./profile.js") : root.HFProfile;
""", """  var P = NODE ? require("./profile.js") : root.HFProfile;
  function X() { return NODE ? require("./text.js") : root.HFText; }   // scriptWord splits with HFText.splitChars
"""),
    ("""    var chars = Array.from(el.textContent); el.textContent = "";   // code points: never split a surrogate pair
    for (var i = 0; i < chars.length; i++) {
      var s = document.createElement("span"); s.textContent = chars[i]; s.style.opacity = "0"; s.style.display = "inline";
      s.setAttribute("data-layout-allow-overlap", ""); s.setAttribute("data-layout-allow-occlusion", "");
      el.appendChild(s);
      tl.set(s, { opacity: 1 }, T + (i * ms) / 1000);
    }
    el.style.opacity = "1"; el.setAttribute("data-layout-allow-overlap", ""); el.setAttribute("data-layout-allow-occlusion", "");
    return (chars.length * ms) / 1000;""",
     """    // Per code point, nested markup kept (HFText.splitChars); opts.onSpans receives the letter spans.
    var spans = X().splitChars(el);
    if (opts.onSpans) opts.onSpans(spans);
    spans.forEach(function (s, i) {
      s.style.opacity = "0"; s.style.display = "inline";
      s.setAttribute("data-layout-allow-overlap", ""); s.setAttribute("data-layout-allow-occlusion", "");
      tl.set(s, { opacity: 1 }, T + (i * ms) / 1000);
    });
    el.style.opacity = "1"; el.setAttribute("data-layout-allow-overlap", ""); el.setAttribute("data-layout-allow-occlusion", "");
    return (spans.length * ms) / 1000;"""),
])
edit("lib/test/helpers.js", [
    ("""    set: function (v) { el.children = []; el._text = String(v); }
  });""",
     """    set: function (v) { el.children = []; el._text = String(v); },
    configurable: true   // fakeMixed redefines it over childNodes
  });"""),
    ("""  el.style.setProperty = function (k, v) { el.style[k] = v; };
  return el;
}""",
     """  el.style.setProperty = function (k, v) { el.style[k] = v; };
  return el;
}

// A text node and a mixed-content element (childNodes holding text nodes and elements) for the
// splitWords / splitChars markup tests; fakeEl itself has no childNodes (it models a plain-text node).
function fakeText(s) { return { nodeType: 3, nodeValue: s, get textContent() { return this.nodeValue; } }; }
function fakeMixed(tag, nodes) {
  var el = fakeEl(tag);
  el.nodeType = 1; el.childNodes = [];
  function adopt(n) { n.parentNode = el; return n; }
  nodes.forEach(function (n) { el.childNodes.push(adopt(n)); });
  el.appendChild = function (c) { el.childNodes.push(adopt(c)); return c; };
  el.replaceChild = function (n, o) {
    var i = el.childNodes.indexOf(o), add = n.isFragment ? n.children : [n];
    el.childNodes.splice.apply(el.childNodes, [i, 1].concat(add.map(adopt)));
    return o;
  };
  el.hasAttribute = function (k) { return Object.prototype.hasOwnProperty.call(el.attrs, k); };
  Object.defineProperty(el, "textContent", { get: function () { return el.childNodes.map(function (c) { return c.textContent; }).join(""); } });
  return el;
}"""),
    ("""    createElementNS: function (ns, tag) { return fakeEl(tag); },
    getElementById: function () { return null; }
  };""",
     """    createElementNS: function (ns, tag) { return fakeEl(tag); },
    createTextNode: function (s) { return fakeText(s); },
    createDocumentFragment: function () { var f = fakeEl("#fragment"); f.isFragment = true; return f; },
    getElementById: function () { return null; },
    head: fakeEl("head"),
    body: fakeEl("body")
  };"""),
    ("""  seekOrderInvariant: seekOrderInvariant, fakeEl: fakeEl, fakeGl: fakeGl, fakeCanvas: fakeCanvas, fakeDocument: fakeDocument };""",
     """  seekOrderInvariant: seekOrderInvariant, fakeEl: fakeEl, fakeGl: fakeGl, fakeCanvas: fakeCanvas, fakeDocument: fakeDocument,
  fakeText: fakeText, fakeMixed: fakeMixed };"""),
])
print("Task 2 edits applied")
PY
````

- [ ] **Step 3: Run the tests**

Run: `node --test lib/test/*.test.js tools/*.test.js`
Expected: `# pass 97` `# fail 0` (every existing `words` / `typeOn` / `scriptWord` / odometer test still passes: a plain-text element splits exactly as before).

- [ ] **Step 4: Commit**

````bash
git add lib/text.js lib/marks.js lib/test/helpers.js lib/test/text.test.js lib/test/marks.test.js
git commit -m "feat(lib): word/char spans keep markup (splitWords, splitChars, onSpans); glowTitle intensity; accentWord installs its CSS" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
````

---

### Task 3: `visibleBeforeStart` compares transform and filter, not only opacity

**Files:**
- Modify: `lib/test/helpers.js`
- Create: `lib/test/helpers.test.js`

**Interfaces:**
- Consumes: `fakeTimeline`, `fakeEl` (existing).
- Produces:
  - `helpers.parseTransform(str) -> {x, y, scaleX, scaleY, rotation}` — reads `translate`, `translateX`, `translateY`, `scale`, `scaleX`, `scaleY`, `rotate` in any order.
  - `helpers.visibleBeforeStart(tl) -> [tween index]` — for every eased `fromTo` on an element: build-time opacity (unset = 1), transform (from `x`, `y`, `scale`, `scaleX`, `scaleY`, `rotation`) and `filter` must equal the from-values. Every kit test (Tasks 5–12) relies on it.

- [ ] **Step 1: Write the failing test**

Create `lib/test/helpers.test.js`:

````javascript
"use strict";
// The test doubles themselves: visibleBeforeStart must catch a transform or filter that differs from a
// tween's from-state (the Plan 2 review gap), not only an opacity.
var test = require("node:test");
var assert = require("node:assert/strict");
var h = require("./helpers.js");

test("parseTransform reads translate/scale/rotate in any order", function () {
  assert.deepEqual(h.parseTransform("translate(0px, 75.6px)"), { x: 0, y: 75.6, scaleX: 1, scaleY: 1, rotation: 0 });
  assert.deepEqual(h.parseTransform("translateY(12px) scale(0.6)"), { x: 0, y: 12, scaleX: 0.6, scaleY: 0.6, rotation: 0 });
  assert.deepEqual(h.parseTransform("scaleX(0)"), { x: 0, y: 0, scaleX: 0, scaleY: 1, rotation: 0 });
  assert.deepEqual(h.parseTransform(""), { x: 0, y: 0, scaleX: 1, scaleY: 1, rotation: 0 });
});

test("visibleBeforeStart flags opacity, transform and filter that differ from the from-state", function () {
  function one(style, from) {
    var tl = h.fakeTimeline(), el = h.fakeEl("div");
    Object.assign(el.style, style);
    tl.fromTo(el, from, { duration: 1, ease: function () {} }, 1);
    return h.visibleBeforeStart(tl);
  }
  assert.deepEqual(one({ opacity: "0", transform: "translate(0px, 40px)" }, { opacity: 0, y: 40 }), []);
  assert.deepEqual(one({ opacity: "0" }, { opacity: 0, y: 40 }), [0], "rise missing at build");
  assert.deepEqual(one({ transform: "scale(0.5)" }, { scale: 0 }), [0], "wrong scale at build");
  assert.deepEqual(one({ opacity: "0", filter: "blur(8px)" }, { opacity: 0, filter: "blur(0px)" }), [0], "filter differs");
  assert.deepEqual(one({}, { opacity: 1 }), [], "an unset opacity is 1");
  assert.deepEqual(one({}, { opacity: 0 }), [0]);
});
````

Run: `node --test lib/test/helpers.test.js`
Expected: FAIL — `h.parseTransform is not a function`; `visibleBeforeStart` returns `[]` for "rise missing at build" (it only looked at an opacity of 0).

- [ ] **Step 2: Implement**

````bash
python3 - . <<'PY'
import sys
from pathlib import Path
ROOT = Path(sys.argv[1])

def edit(rel, pairs):
    p = ROOT / rel
    s = p.read_text()
    for a, b in pairs:
        if s.count(a) != 1:
            sys.exit(f"{rel}: expected exactly one match for: {a[:70]!r}")
        s = s.replace(a, b)
    p.write_text(s)

edit("lib/test/helpers.js", [
    ("""// Before its start time a tween has never rendered, so the element shows its BUILD-TIME style; after a
// backward seek GSAP shows the from-state. Both must look the same: every eased fromTo that fades from 0
// must find style.opacity "0" already written. Returns the offending tweens' indexes; [] means safe.
function visibleBeforeStart(tl) {
  var out = [];
  tl.eased().forEach(function (tw, i) {
    if (tw.kind !== "fromTo" || tw.from.opacity !== 0) return;
    [].concat(tw.target).forEach(function (t) { if (String(t.style.opacity) !== "0") out.push(i); });
  });
  return out;
}""",
     """// The GSAP transform shorthand a CSS transform string amounts to: translate/translateX/translateY (px),
// scale/scaleX/scaleY, rotate (deg), in any order. Anything else in the string is ignored.
function parseTransform(str) {
  var t = { x: 0, y: 0, scaleX: 1, scaleY: 1, rotation: 0 }, re = /(translateX|translateY|translate|scaleX|scaleY|scale|rotate)\\(([^)]*)\\)/g, m;
  while ((m = re.exec(String(str || "")))) {
    var v = m[2].split(",").map(function (p) { return parseFloat(p); });
    if (m[1] === "translate") { t.x += v[0]; t.y += v.length > 1 ? v[1] : 0; }
    else if (m[1] === "translateX") t.x += v[0];
    else if (m[1] === "translateY") t.y += v[0];
    else if (m[1] === "scale") { t.scaleX *= v[0]; t.scaleY *= v.length > 1 ? v[1] : v[0]; }
    else if (m[1] === "scaleX") t.scaleX *= v[0];
    else if (m[1] === "scaleY") t.scaleY *= v[0];
    else t.rotation += v[0];
  }
  return t;
}
var TRANSFORM_KEYS = ["x", "y", "scale", "scaleX", "scaleY", "rotation"];

// Before its start time a tween has never rendered, so the element shows its BUILD-TIME style; after a
// backward seek GSAP shows the from-state. Both must look the same: for every eased fromTo on an element,
// the build-time opacity (unset = 1), transform (x, y, scale, scaleX, scaleY, rotation) and filter must
// equal the tween's from-values. Returns the offending tweens' indexes; [] means safe.
function visibleBeforeStart(tl) {
  var out = [];
  tl.eased().forEach(function (tw, i) {
    if (tw.kind !== "fromTo") return;
    var f = tw.from;
    [].concat(tw.target).forEach(function (t) {
      if (!t || !t.style) return;   // a plain state object, not an element
      var bad = false;
      if (f.opacity !== undefined) {
        var op = t.style.opacity === undefined || t.style.opacity === "" ? 1 : Number(t.style.opacity);
        if (Math.abs(op - f.opacity) > 1e-9) bad = true;
      }
      if (TRANSFORM_KEYS.some(function (k) { return k in f; })) {
        var have = parseTransform(t.style.transform);
        var sx = f.scaleX != null ? f.scaleX : f.scale != null ? f.scale : 1, sy = f.scaleY != null ? f.scaleY : f.scale != null ? f.scale : 1;
        var want = { x: f.x || 0, y: f.y || 0, scaleX: sx, scaleY: sy, rotation: f.rotation || 0 };
        if (Object.keys(want).some(function (k) { return Math.abs(have[k] - want[k]) > 1e-6; })) bad = true;
      }
      if (f.filter !== undefined && String(t.style.filter || "") !== String(f.filter)) bad = true;
      if (bad && out.indexOf(i) === -1) out.push(i);
    });
  });
  return out;
}"""),
    ("""  fakeText: fakeText, fakeMixed: fakeMixed };""",
     """  fakeText: fakeText, fakeMixed: fakeMixed, parseTransform: parseTransform };"""),
])
print("Task 3 edits applied")
PY
````

- [ ] **Step 3: Run the tests**

Run: `node --test lib/test/*.test.js tools/*.test.js`
Expected: `# pass 99` `# fail 0` — every existing binder already writes its full from-state at build (words, highlight, chips, defocus), so the stricter check passes on them.

- [ ] **Step 4: Commit**

````bash
git add lib/test/helpers.js lib/test/helpers.test.js
git commit -m "test(lib): visibleBeforeStart compares build-time transform and filter with the from-state" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
````

---

### Task 4: Chained phase → phase wipes on one host (smoke page) — and the edge bug they expose

**Files:**
- Modify: `lib/shorts/wipe.js`, `lib/examples/smoke.html`
- Test: `lib/test/wipe.test.js`

**Interfaces:**
- Consumes: `HFWipe.wipe`, `HFWipe.phase`, `HFWipe.IN` (0.42), `HFWipe.OUT` (0.36).
- Produces: `HFWipe.wipeProgress(t, inAt, outAt)` snaps phase edges within `EDGE = 1e-6` s: `wipeProgress(1.0, null, 1.0 + HFWipe.OUT).q === 1`; `wipeProgress(inAt + HFWipe.IN, inAt, null).q === 1`. Phases may be chained freely on one host.

- [ ] **Step 1: Write the failing unit test**

````bash
cat >> lib/test/wipe.test.js <<'EOF'

test("wipeProgress: phase edges snap, so a driver handed a rounded start value shows no out-phase sliver", function () {
  var outAt = 1.0 + Wp.OUT;                       // 1.3599999999999999: its start, outAt - 0.36, is 0.9999999999999999
  assert.equal(Wp.wipeProgress(1.0, null, outAt).q, 1, "GSAP reports the driver's start as 1.0: still fully shown");
  assert.equal(Wp.wipeState(Wp.wipeProgress(1.0, null, outAt).q, 12, "right").filterOn, false);
  var inAt = 0.2;
  assert.equal(Wp.wipeProgress(inAt + Wp.IN, inAt, null).q, 1, "the in-phase's last frame is fully shown");
  assert.equal(Wp.wipeProgress(outAt, null, outAt).q, 0);
});
EOF
````

Run: `node --test lib/test/wipe.test.js`
Expected: FAIL — `0.9999999999999973 !== 1` ("GSAP reports the driver's start as 1.0: still fully shown").

- [ ] **Step 2: Implement (wipe edge + the smoke page's chained phases)**

````bash
python3 - . <<'PY'
import sys
from pathlib import Path
ROOT = Path(sys.argv[1])

def edit(rel, pairs):
    p = ROOT / rel
    s = p.read_text()
    for a, b in pairs:
        if s.count(a) != 1:
            sys.exit(f"{rel}: expected exactly one match for: {a[:70]!r}")
        s = s.replace(a, b)
    p.write_text(s)

edit("lib/shorts/wipe.js", [
    ("""  // Eased progress + blur cap at time t for a wipe that reveals at inAt and/or is fully hidden by outAt.
  function wipeProgress(t, inAt, outAt) {
    if (outAt != null && t >= outAt) return { q: 0, blurMax: W.blurOut };
    if (inAt != null && t < inAt + W.inDur) return { q: EASE(Math.max(0, (t - inAt) / W.inDur)), blurMax: W.blurIn };
    if (outAt != null && t > outAt - W.outDur) return { q: 1 - EASE(Math.min(1, (t - (outAt - W.outDur)) / W.outDur)), blurMax: W.blurOut };""",
     """  // Eased progress + blur cap at time t for a wipe that reveals at inAt and/or is fully hidden by outAt.
  // Phase edges snap within EDGE s: GSAP hands a driver its start value rounded (1.36 - 0.36 is
  // 0.9999999999999999, the driver reports 1), and an unsnapped edge left the out-phase's first sliver
  // (mask 100 %/108 %, blur filter attached) on a host seeked back to before its out-wipe.
  var EDGE = 1e-6;
  function wipeProgress(t, inAt, outAt) {
    if (outAt != null && t >= outAt - EDGE) return { q: 0, blurMax: W.blurOut };
    if (inAt != null && t < inAt + W.inDur - EDGE) return { q: EASE(Math.max(0, (t - inAt) / W.inDur)), blurMax: W.blurIn };
    if (outAt != null && t > outAt - W.outDur + EDGE) return { q: 1 - EASE(Math.min(1, (t - (outAt - W.outDur)) / W.outDur)), blurMax: W.blurOut };"""),
])
edit("lib/examples/smoke.html", [
    ("""  .pill span { position: absolute; left: 30px; top: 18px; font-size: 36px; }""",
     """  .pill span { position: absolute; left: 30px; top: 18px; font-size: 36px; }
  .phase { position: absolute; left: 90px; top: 1500px; width: 900px; height: 300px; font-size: 200px; background: var(--hf-surface-fill); }"""),
    ("""  <svg width="0" height="0"><filter id="mb-sh"><feGaussianBlur id="sh-fe" stdDeviation="0 0"/></filter></svg>
</div>""",
     """  <svg width="0" height="0"><filter id="mb-sh"><feGaussianBlur id="sh-fe" stdDeviation="0 0"/></filter></svg>
  <!-- chained phases on one host: A -> B at 1.0 s, then B -> C at 3.0 s (B is wiped in AND out) -->
  <div id="ph-a" class="phase" style="visibility:hidden">A</div>
  <div id="ph-b" class="phase" style="visibility:hidden">B</div>
  <div id="ph-c" class="phase" style="visibility:hidden">C</div>
  <svg width="0" height="0">
    <filter id="mb-a"><feGaussianBlur id="fe-a" stdDeviation="0 0"/></filter>
    <filter id="mb-b"><feGaussianBlur id="fe-b" stdDeviation="0 0"/></filter>
    <filter id="mb-c"><feGaussianBlur id="fe-c" stdDeviation="0 0"/></filter>
  </svg>
</div>"""),
    ("""    HFMarks.seedChip(tl, { pill: $("sh-pill"), label: $("sh-label") }, 3.0, SH);
""",
     """    HFMarks.seedChip(tl, { pill: $("sh-pill"), label: $("sh-label") }, 3.0, SH);
    function ph(k) { return { host: $("ph-" + k), fe: $("fe-" + k), filterId: "mb-" + k }; }
    HFWipe.wipe(tl, { host: $("ph-a"), fe: $("fe-a"), filterId: "mb-a", dir: "right", inAt: 0.2 });
    HFWipe.phase(tl, ph("a"), ph("b"), 1.0, "right");
    HFWipe.phase(tl, ph("b"), ph("c"), 3.0, "right");
"""),
    ("""      var ids = ["lf-stage", "lf-bg", "lf-hl", "lf-ring", "lf-arrow", "w1", "w2", "lf-title", "sh-host", "sh-stage", "sh-pill", "sh-label", "sh-fe"];""",
     """      var ids = ["lf-stage", "lf-bg", "lf-hl", "lf-ring", "lf-arrow", "w1", "w2", "lf-title", "sh-host", "sh-stage", "sh-pill", "sh-label", "sh-fe",
        "ph-a", "ph-b", "ph-c", "fe-a", "fe-b", "fe-c"];"""),
    ("""    [0.3, 0.45, 0.55, 0.61, 0.62, 5.45, 5.5, 5.65, 5.75, 5.79, 5.9, 6].forEach(""",
     """    // ...and inside both chained phases (A->B 1.0..1.52, B->C 3.0..3.52), where B is first wiped in, then out.
    [0.3, 0.45, 0.55, 0.61, 0.62, 5.45, 5.5, 5.65, 5.75, 5.79, 5.9, 6, 1.05, 1.15, 1.3, 1.36, 1.45, 3.05, 3.15, 3.3, 3.36, 3.45].forEach("""),
    ("""    order.push(6, 0.45, 5.9, 5.5, 5.75, 0.3, 5.45, 0.55, 0.61, 5.79, 0.62, 0);""",
     """    order.push(6, 0.45, 5.9, 5.5, 5.75, 0.3, 5.45, 0.55, 0.61, 5.79, 0.62, 0);
    order.push(6, 3.3, 1.3, 3.15, 1.15, 3.45, 1.45, 0, 3.05, 1.05);   // backward and forward across both phases of host B"""),
])
print("Task 4 edits applied")
PY
````

- [ ] **Step 3: Run the unit tests**

Run: `node --test lib/test/*.test.js tools/*.test.js`
Expected: `# pass 100` `# fail 0`.

- [ ] **Step 4: Run the smoke page in a real browser**

````bash
python3 -m http.server 8765 >/dev/null 2>&1 &
echo "open http://localhost:8765/lib/examples/smoke.html (hard-reload so the browser does not reuse a cached lib/shorts/wipe.js)"
````
Expected in the page: `PASS {"done":true,"ok":true,"mismatches":[],"errors":[],"frames":52}`. (Prototype evidence: with the Step 2 smoke-page change but WITHOUT the `wipe.js` edge fix the page reports `FAIL` with mismatches at t = 0.8 and 0.62 on `#ph-a` — `url("#mb-a")` and a `100% / 108%` mask in the shuffled pass, `none` forward.) Then stop the server: `pkill -f "http.server 8765"`.

- [ ] **Step 5: Commit**

````bash
git add lib/shorts/wipe.js lib/examples/smoke.html lib/test/wipe.test.js
git commit -m "fix(lib): HFWipe phase edges snap so chained phases on one host are seek-safe; smoke page covers them" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
````

---

### Task 5: Kit core — `lib/kit/kit.js` (registry, ground mode, ground + glass, entrances), manifest, scaffold

**Files:**
- Create: `lib/kit/kit.js`, `lib/test/kit-contract.js`, `lib/test/kit.test.js`
- Modify: `lib/test/helpers.js`, `lib/manifest.json`, `tools/new_video.py`, `tools/test_new_video.py`, `tools/test_sync_lib.py`

**Interfaces:**
- Consumes: `HFProfile.ease / timing / claimTransform` (Task 1), `HFText.blurPx` (Task 2), `visibleBeforeStart` (Task 3).
- Produces (`HFKit`, global in the browser, `require("lib/kit/kit.js")` in node):
  - `register(name, variant, binder(tl, host, opts), css?)` — adds `HFKit[camel(name)](tl, host, opts)` dispatching on `opts.variant` (default: the first registered); unknown variant throws `HFKit.<call>: unknown variant "<v>" (have: …)`; a duplicate throws `HFKit: <name>/<variant> registered twice`. `variants(name) -> [variant]`.
  - `mode(host, who) -> "dark" | "light"` — `host.closest("[data-hf-mode]")`; none → `<who>: no data-hf-mode on the host or any ancestor — …`; another value → `<who>: data-hf-mode must be "dark" or "light", got "<v>"`.
  - `begin(name, host, opts) -> {mode, at, who, lf: {format: "long-form", frameHeight: 1080}}` — checks `opts.format === "long-form"` (`… kit components are long-form only …`), `host.appendChild` (`… host must be an element`), `opts.at` (default 0, `… opts.at must be a time in seconds ≥ 0`); installs the kit stylesheet once (`<style id="hf-kit-css">`); adds `hf-kit-host` and `hf-kit-<mode>` to the host.
  - `ground(host, {ambient?, quiet?, dots?}) -> {root, base, ambient?, grid, dots?, sweep, vignette}` (full-frame ground layers).
  - Entrances (each writes its from-state at build and returns its duration): `cardIn(tl, el, T)` (rise `card.riseFrac × 1080` = 56.25 px + fade + `blur(8px) brightness(0.6)` → sharp, `card.dur` 0.43 s `ease.card`, tags `focus`, claims `"HFKit.cardIn"`) · `slideIn(tl, el, T, dx)` (fade + x from `dx`, `words.dur` 0.6 s `ease.enter`, claims `"HFKit.slideIn"`) · `fadeOut(tl, el, T)` (opacity 1 → 0, 0.43 s `ease.enter`, no transform) · `pop(tl, el, T)` (scale 0 → 1 + fade, `node.dur` 0.48 s `ease.enter`, claims `"HFKit.pop"`).
  - Constants: `FORMAT` `"long-form"`, `FRAME` `{width: 1920, height: 1080}`, `GRID_PX` 150, `GLOW` 0.6; `el(tag, cls, parent, text)`, `svg(tag, attrs, parent)`, `installCss()`, `css()` (the full stylesheet text).
  - CSS classes every component uses: `.hf-kit-glass` (dark: dark fill + light sheen, bevelled light rim, faint light halo; light: frosted white, hairline, soft neutral shadow), `.hf-kit-headline`, `.hf-kit-body`, `.hf-kit-script`, `.hf-kit-underline`, `.hf-kit-marker`, `.hf-kit-word`; mode rules are scoped `.hf-kit-dark …` / `.hf-kit-light …`.
  - `lib/test/helpers.js`: `fakeEl` gains `className`, `classList.add/contains`, `hasAttribute`, `closest("[attr]")`; new `kitHost(mode | null)`, `descendants(el)`, `serialize(tl)`.
  - `lib/test/kit-contract.js`: `contract(name, build(tl, host, extra) -> {dur})` registers the contract tests every component runs; `fresh()` resets the fake document; `glowFree(host)`.
  - `lib/manifest.json`: `kit/kit.js` right after `brand.js` in `loadOrder`; `tools/new_video.py` `FORMAT_ONLY = {"shorts": "shorts", "kit": "long-form"}` (kit scripts in long-form `index.html` only).

- [ ] **Step 1: Write the failing tests**

Create `lib/test/kit-contract.js`:

````javascript
"use strict";
/* The contract every kit component must keep, run by each lib/test/kit-<name>.test.js:
 *   long-form only · throws without data-hf-mode · deterministic · profile eases only · no two eased
 *   tweens on one property · build-time style = from-state · light ground has no glow.
 * build(tl, host, extra) calls the component with its fixture options merged with `extra`. */
var test = require("node:test");
var assert = require("node:assert/strict");
var h = require("./helpers.js");
var P = require("../profile.js");

function fresh() {
  global.document = h.fakeDocument();
  global.getComputedStyle = function () { return { getPropertyValue: function () { return ""; } }; };
}

function glowFree(host) {
  return h.descendants(host).filter(function (e) {
    return e.getAttribute("data-blur-reason") === "glow" || /url\(/.test(String(e.style.filter || ""));
  }).length === 0 && document.body.children.filter(function (c) { return c.getAttribute("id") === "hf-glow-host"; }).length === 0;
}

function contract(name, build) {
  test(name + ": long-form only, and throws when no ancestor sets data-hf-mode", function () {
    fresh();
    assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { format: "shorts" }); }, /long-form only/);
    assert.throws(function () { build(h.fakeTimeline(), h.kitHost(null), {}); }, /no data-hf-mode on the host or any ancestor/);
    var bad = h.kitHost("dim");
    assert.throws(function () { build(h.fakeTimeline(), bad, {}); }, /data-hf-mode must be "dark" or "light", got "dim"/);
  });
  ["dark", "light"].forEach(function (mode) {
    test(name + " (" + mode + "): deterministic, profile eases only, no conflicts, build-time style = from-state", function () {
      fresh();
      var a = h.fakeTimeline(), hostA = h.kitHost(mode), ra = build(a, hostA, {});
      fresh();
      var b = h.fakeTimeline(), hostB = h.kitHost(mode);
      build(b, hostB, {});
      assert.equal(h.serialize(a), h.serialize(b), "same inputs, same timeline");
      // glow filter ids count up per page (hf-glow-1, -2 …): equal up to that counter
      function dom(host) { return h.snapshot(h.descendants(host)).replace(/hf-glow-\d+/g, "hf-glow-N"); }
      assert.equal(dom(hostA), dom(hostB), "same inputs, same DOM");
      assert.ok(ra.dur > 0, "returns how long it takes to settle");
      a.eased().forEach(function (tw) { assert.ok(P.isProfileEase(tw.ease), "tween at " + tw.at + " s uses " + (tw.ease && tw.ease.token || tw.ease)); });
      a.drivers().forEach(function (tw) { assert.equal(typeof tw.to.onUpdate, "function", "a linear tween is a driver"); });
      assert.deepEqual(h.conflicts(a), []);
      assert.deepEqual(h.visibleBeforeStart(a), []);
    });
  });
  test(name + " (light): drops every glow", function () {
    fresh();
    var host = h.kitHost("light");
    build(h.fakeTimeline(), host, {});
    assert.ok(glowFree(host), "no glow filter, no glow-tagged element on the light ground");
  });
}

module.exports = { contract: contract, fresh: fresh, glowFree: glowFree };
````

Create `lib/test/kit.test.js`:

````javascript
"use strict";
var test = require("node:test");
var assert = require("node:assert/strict");
var h = require("./helpers.js");
var P = require("../profile.js");
var c = require("./kit-contract.js");
var fs = require("node:fs");
var path = require("node:path");
var K = require("../kit/kit.js");
// Every component file that exists so far (the kit is built one component per task).
var KIT = require("../../brands/contentporary/tokens.json").kit;
var BUILT = Object.keys(KIT).filter(function (n) { return fs.existsSync(path.join(__dirname, "..", "kit", n + ".js")); });
BUILT.forEach(function (n) { require("../kit/" + n + ".js"); });

test("each built component registers the variant brands/contentporary/tokens.json names, under its camel-case call", function () {
  BUILT.forEach(function (name) {
    assert.deepEqual(K.variants(name), [KIT[name]], name);
    assert.equal(typeof K[name.replace(/-([a-z])/g, function (_, ch) { return ch.toUpperCase(); })], "function", name);
  });
});

test("register(): a component is called through its variant; an unknown variant throws naming the ones that exist", function () {
  c.fresh();
  K.register("zz-probe", "plain", function (tl, host, o) { return { dur: 1, got: o.variant || "plain" }; });
  assert.deepEqual(K.zzProbe(h.fakeTimeline(), h.kitHost("dark"), {}), { dur: 1, got: "plain" });
  assert.throws(function () { K.zzProbe(h.fakeTimeline(), h.kitHost("dark"), { variant: "neon" }); },
    /HFKit\.zzProbe: unknown variant "neon" \(have: plain\)/);
  assert.throws(function () { K.register("zz-probe", "plain", function () {}); }, /zz-probe\/plain registered twice/);
});

test("begin(): long-form only, a host, a time ≥ 0; puts the resolved mode on the host as a class", function () {
  c.fresh();
  var host = h.kitHost("light");
  var b = K.begin("zz-probe", host, { format: "long-form", at: 1.5 });
  assert.deepEqual([b.mode, b.at, b.who, b.lf.frameHeight], ["light", 1.5, "HFKit.zzProbe", 1080]);
  assert.ok(host.classList.contains("hf-kit-host") && host.classList.contains("hf-kit-light"));
  assert.throws(function () { K.begin("zz-probe", host, { format: "shorts" }); }, /long-form only/);
  assert.throws(function () { K.begin("zz-probe", {}, { format: "long-form" }); }, /host must be an element/);
  assert.throws(function () { K.begin("zz-probe", host, { format: "long-form", at: -1 }); }, /opts\.at must be a time/);
  assert.doesNotMatch(K.css(), /data-hf-mode/);
});

test("mode(): the host's own data-hf-mode or the nearest ancestor's, never a default", function () {
  var host = h.kitHost("light");
  assert.equal(K.mode(host, "t"), "light");
  host.setAttribute("data-hf-mode", "dark");
  assert.equal(K.mode(host, "t"), "dark");
  assert.throws(function () { K.mode(h.kitHost(null), "HFKit.x"); }, /HFKit\.x: no data-hf-mode/);
});

test("kit CSS: colours are brand variables only, and every glow is scoped to the dark ground", function () {
  var css = K.css();
  assert.doesNotMatch(css, /#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(|color-mix\(/, "no colour literal in the kit stylesheet");
  css.split("}").forEach(function (rule) {
    if (/text-shadow|drop-shadow/.test(rule)) {
      assert.match(rule, /^\s*\.hf-kit-dark /, "glow outside the dark ground: " + rule.trim().slice(0, 90));
    }
  });
});

test("entrances write their from-state at build and use the profile's card/node/words timings", function () {
  c.fresh();
  var T = P.timing("long-form"), tl = h.fakeTimeline(), card = h.fakeEl("div"), dot = h.fakeEl("div"), panel = h.fakeEl("div"), layout = h.fakeEl("div");
  assert.equal(K.cardIn(tl, card, 1), T.card.dur);
  assert.equal(card.getAttribute("data-blur-reason"), "focus");
  assert.equal(K.pop(tl, dot, 2), T.node.dur);
  assert.equal(K.slideIn(tl, panel, 3, -80), T.words.dur);
  assert.equal(K.fadeOut(tl, layout, 5), T.card.dur, "exits fade the layout's root, never an element an entrance animates");
  assert.deepEqual(h.visibleBeforeStart(tl), []);
  assert.deepEqual(tl.eased().map(function (tw) { return tw.ease.token; }), ["ease.card", "ease.enter", "ease.enter", "ease.enter"]);
  assert.throws(function () { K.cardIn(h.fakeTimeline(), dot, 0); }, /HFKit\.cardIn would overwrite the inline transform that HFKit\.pop animates/);
});
````

Run: `node --test lib/test/kit.test.js`
Expected: FAIL — `Cannot find module '../kit/kit.js'`.

- [ ] **Step 2: Implement the core**

Create `lib/kit/kit.js`:

````javascript
/* ============================================================================
 * HFKit — the templated long-form kit: registry, ground, glass, entrances
 * ----------------------------------------------------------------------------
 * Spec §8 (lib/kit) · standards/formats/long-form.md (catalogue, motion values) ·
 * brands/<brand>/brand.md (kit variants, light-ground rules).
 *
 * A kit component is a binder: HFKit.<name>(tl, host, opts) builds its DOM inside `host`
 * (a 1920×1080 box; the kit never transforms the host itself), adds tweens at explicit
 * times to the paused timeline `tl`, and returns { dur, ... } — dur = seconds from opts.at
 * until the layout has settled. It is built ONLY on the lib primitives: HFProfile eases and
 * timings, HFCamera, HFMarks, HFText, and the HFBrand CSS variables. No colour is written
 * here: every colour is a var(--hf-…) from lib/brand.js.
 *
 * Ground mode: every component reads data-hf-mode from host.closest("[data-hf-mode]") and
 * THROWS if it is missing (new_video writes it on index.html's root; an overlay document
 * sets it on its own root). Light ground drops every glow (brand.md): dark text.primary,
 * a scribble underline or an accent.block marker, frosted white glass.
 *
 * Build after `await document.fonts.ready` (components measure text), then
 * `await HFText.ready()` before registering the timeline.
 * Load after profile.js, motion-blur.js, camera.js, marks.js, text.js; components after this file.
 * ==========================================================================*/
(function (root) {
  "use strict";
  var NODE = typeof module !== "undefined" && module.exports;
  var P = NODE ? require("../profile.js") : root.HFProfile;
  function X() { return NODE ? require("../text.js") : root.HFText; }

  var FORMAT = "long-form";
  var FRAME = { width: 1920, height: 1080 };   // long-form frame (standards/formats/long-form.md)
  var GRID_PX = 150;                            // ground grid cell at 1080p, measured on the template stills
  var GLOW = 0.6;                               // settled glow-title bloom for kit titles (lib default 1.2 reads as a smear on 1080p stills)
  var VARIANTS = {};                            // component -> { variant: binder }
  var CSS = [];

  function register(name, variant, binder, css) {
    VARIANTS[name] = VARIANTS[name] || {};
    if (VARIANTS[name][variant]) throw new Error("HFKit: " + name + "/" + variant + " registered twice");
    VARIANTS[name][variant] = binder;
    if (css) CSS.push(css);
    if (!api[camel(name)]) {
      api[camel(name)] = function (tl, host, opts) {
        opts = opts || {};
        var have = Object.keys(VARIANTS[name]), v = opts.variant || have[0];
        if (!VARIANTS[name][v]) throw new Error("HFKit." + camel(name) + ": unknown variant " + JSON.stringify(v) + " (have: " + have.join(", ") + ")");
        return VARIANTS[name][v](tl, host, opts);
      };
    }
  }
  function camel(name) { return name.replace(/-([a-z])/g, function (_, c) { return c.toUpperCase(); }); }
  function variants(name) { return VARIANTS[name] ? Object.keys(VARIANTS[name]) : []; }

  // The ground mode for `host`: its own or its nearest ancestor's data-hf-mode. Never defaulted.
  function mode(host, who) {
    var m = host && typeof host.closest === "function" ? host.closest("[data-hf-mode]") : null;
    if (!m) throw new Error(who + ": no data-hf-mode on the host or any ancestor — set it on the composition root " +
      "(new_video writes it on index.html; an overlay document sets it on its own root)");
    var v = m.getAttribute("data-hf-mode");
    if (v !== "dark" && v !== "light") throw new Error(who + ": data-hf-mode must be \"dark\" or \"light\", got " + JSON.stringify(v));
    return v;
  }

  // Common entry checks: long-form only, a host element, a start time. Returns { mode, at, lf }.
  function begin(name, host, opts) {
    var who = "HFKit." + camel(name);
    if (opts.format !== FORMAT) throw new Error(who + ": kit components are long-form only (opts.format must be \"long-form\", got " + JSON.stringify(opts.format) + ")");
    if (!host || typeof host.appendChild !== "function") throw new Error(who + ": host must be an element");
    var at = opts.at == null ? 0 : opts.at;
    if (!(typeof at === "number" && isFinite(at) && at >= 0)) throw new Error(who + ": opts.at must be a time in seconds ≥ 0");
    installCss();
    var m = mode(host, who);
    // The resolved mode as a class: CSS keys off it, not [data-hf-mode], because a descendant selector would
    // also match a farther ancestor (a light proof-sheet scene inside a dark index root).
    host.classList.add("hf-kit-host", "hf-kit-" + m);
    return { mode: m, at: at, who: who, lf: { format: FORMAT, frameHeight: FRAME.height } };
  }

  function el(tag, cls, parent, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    if (parent) parent.appendChild(e);
    return e;
  }
  function svg(tag, attrs, parent) {
    var e = document.createElementNS("http://www.w3.org/2000/svg", tag);
    Object.keys(attrs || {}).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    if (parent) parent.appendChild(e);
    return e;
  }

  function installCss() {
    if (typeof document === "undefined" || document.getElementById("hf-kit-css")) return;
    var s = document.createElement("style"); s.setAttribute("id", "hf-kit-css"); s.textContent = BASE_CSS + CSS.join("\n");
    (document.head || document.documentElement || document.body).appendChild(s);
  }

  /* Full-frame ground (brand.md "constant visual language"): lit centre, grid + dot matrix and a soft
   * light sweep on the dark ground; a silver/white radial with a faint grid on the light ground. The
   * accent ambience (opts.ambient) is the warm top glow of the glow-center title still. Returns the
   * layers so a component can defocus the grid behind a title. */
  function ground(host, opts) {
    opts = opts || {};
    var g = el("div", "hf-kit-ground" + (opts.quiet ? " hf-kit-ground-quiet" : ""), host);
    var layers = { root: g, base: el("div", "hf-kit-ground-base", g) };
    if (opts.ambient) layers.ambient = el("div", "hf-kit-ground-ambient", g);
    layers.grid = el("div", "hf-kit-ground-grid", g);
    if (opts.dots !== false) layers.dots = el("div", "hf-kit-ground-dots", layers.grid);
    layers.sweep = el("div", "hf-kit-ground-sweep", g);
    layers.vignette = el("div", "hf-kit-ground-vignette", g);
    return layers;
  }

  /* Card entrance (long-form.md "card entrance"): rise 35–40 px at 720p, 0.43 s ease.card, brightens and
   * sharpens (a focus blur + brightness, tagged data-blur-reason="focus"). Build-time style = from-state. */
  function cardIn(tl, e, T) {
    var t = P.timing(FORMAT), c = t.card, rise = +(c.riseFrac * FRAME.height).toFixed(2);
    var px = +(t.words.blurFrac * FRAME.height).toFixed(2);
    var from = { opacity: 0, y: rise, filter: X().blurPx(e, "focus", px) + " brightness(0.6)" };
    var to = { opacity: 1, y: 0, filter: X().blurPx(e, "focus", 0) + " brightness(1)" };
    P.claimTransform(e, "HFKit.cardIn");
    e.style.opacity = "0"; e.style.transform = "translate(0px, " + rise + "px)"; e.style.filter = from.filter;
    to.duration = c.dur; to.ease = P.ease(FORMAT, "ease.card"); to.immediateRender = false;
    tl.fromTo(e, from, to, T);
    return c.dur;
  }
  /* Slide-in for an over-footage panel: fade + travel from `dx` px, words.dur (0.6 s) on ease.enter. */
  function slideIn(tl, e, T, dx) {
    var d = P.timing(FORMAT).words.dur;
    P.claimTransform(e, "HFKit.slideIn");
    e.style.opacity = "0"; e.style.transform = "translate(" + dx + "px, 0px)";
    tl.fromTo(e, { opacity: 0, x: dx }, { opacity: 1, x: 0, duration: d, ease: P.ease(FORMAT, "ease.enter"), immediateRender: false }, T);
    return d;
  }
  /* Exit of an over-footage layout: opacity to 0 over card.dur on ease.enter. Only opacity, so it never
   * fights an entrance transform. */
  function fadeOut(tl, e, T) {
    var d = P.timing(FORMAT).card.dur;
    tl.fromTo(e, { opacity: 1 }, { opacity: 0, duration: d, ease: P.ease(FORMAT, "ease.enter"), immediateRender: false }, T);
    return d;
  }
  // Pop for small round markers (roadmap nodes): scale 0 -> 1 + fade, timing.node.dur on ease.enter.
  function pop(tl, e, T) {
    var d = P.timing(FORMAT).node.dur;
    P.claimTransform(e, "HFKit.pop");
    e.style.opacity = "0"; e.style.transform = "scale(0)";
    tl.fromTo(e, { opacity: 0, scale: 0 }, { opacity: 1, scale: 1, duration: d, ease: P.ease(FORMAT, "ease.enter"), immediateRender: false }, T);
    return d;
  }

  // Shared look. Colours are brand variables only; glow lives under .hf-kit-dark (the host's resolved mode) only.
  var BASE_CSS = [
    ".hf-kit-host{position:absolute;left:0;top:0;width:1920px;height:1080px;overflow:hidden}",
    ".hf-kit-ground,.hf-kit-ground>div{position:absolute;inset:0}",
    ".hf-kit-ground-base{background:radial-gradient(ellipse 75% 70% at 50% 40%,var(--hf-ground-centre) 0%,var(--hf-ground-deep) 100%)}",
    ".hf-kit-ground-ambient{background:radial-gradient(ellipse 60% 75% at 50% 12%,var(--hf-extras-ambient-glow,var(--hf-ground-centre)) 0%,transparent 72%)}",
    ".hf-kit-ground-grid{mix-blend-mode:screen;background-image:linear-gradient(to right,var(--hf-ground-grid) 2px,transparent 2px),linear-gradient(to bottom,var(--hf-ground-grid) 2px,transparent 2px);" +
      "background-size:" + GRID_PX + "px " + GRID_PX + "px;background-position:60px 0;" +
      "-webkit-mask-image:radial-gradient(ellipse 80% 75% at 50% 35%,black 0%,transparent 100%);mask-image:radial-gradient(ellipse 80% 75% at 50% 35%,black 0%,transparent 100%)}",
    ".hf-kit-ground-dots{position:absolute;inset:0;background-image:radial-gradient(circle,var(--hf-ground-dots) 1.6px,transparent 2.2px);background-size:15px " + GRID_PX / 2 + "px;background-position:68px 37px;opacity:.9}",
    ".hf-kit-ground-sweep{background:linear-gradient(112deg,transparent 45%,var(--hf-surface-halo) 62%,transparent 78%)}",
    ".hf-kit-ground-vignette{background:radial-gradient(ellipse 85% 85% at 50% 45%,transparent 55%,var(--hf-ground-deep) 100%)}",
    ".hf-kit-light .hf-kit-ground-dots{display:none}",
    ".hf-kit-light .hf-kit-ground-grid{mix-blend-mode:multiply;opacity:.8}",
    ".hf-kit-ground-quiet .hf-kit-ground-grid{opacity:.35}",
    // dark glass: dark fill, light sheen top-left, bevelled light rim, faint light halo (never a dark drop shadow)
    ".hf-kit-glass{position:absolute;box-sizing:border-box;border-radius:var(--hf-card-radius)}",
    ".hf-kit-dark .hf-kit-glass{background:linear-gradient(165deg,var(--hf-surface-fill-alt) 0%,var(--hf-surface-fill) 38%,var(--hf-surface-fill) 100%);" +
      "border:2px solid var(--hf-surface-fill-alt);box-shadow:inset 0 2px 0 var(--hf-surface-bevel),inset 0 -2px 6px var(--hf-ground-deep),0 0 0 2px var(--hf-ground-deep),0 0 70px var(--hf-surface-halo)}",
    ".hf-kit-dark .hf-kit-glass::after{content:\"\";position:absolute;inset:-2px;border-radius:inherit;border:2px solid var(--hf-surface-bevel);opacity:.35;pointer-events:none}",
    // light glass: frosted white, hairline border, soft neutral shadow from surface.halo
    ".hf-kit-light .hf-kit-glass{background:var(--hf-surface-fill);border:1px solid var(--hf-surface-bevel);box-shadow:0 18px 48px var(--hf-surface-halo),0 2px 6px var(--hf-surface-halo)}",
    ".hf-kit-headline{font-family:var(--hf-font-headline);font-weight:var(--hf-font-headline-weight);color:var(--hf-text-primary);white-space:nowrap}",
    ".hf-kit-body{font-family:var(--hf-font-body);font-weight:var(--hf-font-body-weight);color:var(--hf-text-primary)}",
    ".hf-kit-script{font-family:var(--hf-font-script);color:var(--hf-accent-script);white-space:nowrap}",
    ".hf-kit-underline{position:absolute;left:-2%;width:104%;top:88%;height:0.32em;overflow:visible;pointer-events:none}",
    ".hf-kit-underline path{fill:none;stroke:var(--hf-accent-line);stroke-width:5;stroke-linecap:round;vector-effect:non-scaling-stroke}",
    ".hf-kit-marker{position:absolute;left:-0.12em;right:-0.12em;top:12%;bottom:4%;background:var(--hf-accent-block);z-index:-1}",
    ".hf-kit-word{position:relative;display:inline-block;white-space:pre}"
  ].join("\n");

  var api = { FORMAT: FORMAT, FRAME: FRAME, GRID_PX: GRID_PX, GLOW: GLOW, register: register, variants: variants, mode: mode, begin: begin,
    el: el, svg: svg, installCss: installCss, ground: ground, cardIn: cardIn, slideIn: slideIn, fadeOut: fadeOut, pop: pop,
    css: function () { return BASE_CSS + CSS.join("\n"); } };
  if (NODE) module.exports = api;
  root.HFKit = api;
})(typeof window !== "undefined" ? window : this);
````

Then the helpers, manifest, scaffold and their tests:

````bash
python3 - . <<'PY'
import json
import sys
from pathlib import Path
ROOT = Path(sys.argv[1])

def edit(rel, pairs):
    p = ROOT / rel
    s = p.read_text()
    for a, b in pairs:
        if s.count(a) != 1:
            sys.exit(f"{rel}: expected exactly one match for: {a[:70]!r}")
        s = s.replace(a, b)
    p.write_text(s)

edit("lib/test/helpers.js", [
    ("""    tagName: (tag || "div").toUpperCase(), style: {}, attrs: {}, children: [], parentNode: null,""",
     """    tagName: (tag || "div").toUpperCase(), style: {}, attrs: {}, children: [], parentNode: null, className: "","""),
    ("""    getAttribute: function (k) { return Object.prototype.hasOwnProperty.call(el.attrs, k) ? el.attrs[k] : null; },""",
     """    getAttribute: function (k) { return Object.prototype.hasOwnProperty.call(el.attrs, k) ? el.attrs[k] : null; },
    hasAttribute: function (k) { return Object.prototype.hasOwnProperty.call(el.attrs, k); },
    // Only "[attr]" selectors — what the kit's ground-mode lookup uses.
    closest: function (sel) {
      var m = /^\\[([\\w-]+)\\]$/.exec(sel);
      if (!m) throw new Error("fakeEl.closest: only [attr] selectors, got " + sel);
      for (var e = el; e; e = e.parentNode) if (e.attrs && Object.prototype.hasOwnProperty.call(e.attrs, m[1])) return e;
      return null;
    },"""),
    ("""  el.style.setProperty = function (k, v) { el.style[k] = v; };
  return el;
}
""",
     """  el.style.setProperty = function (k, v) { el.style[k] = v; };
  el.classList = {
    add: function () { [].slice.call(arguments).forEach(function (c) { if (!el.classList.contains(c)) el.className = (el.className + " " + c).trim(); }); },
    contains: function (c) { return (" " + el.className + " ").indexOf(" " + c + " ") !== -1; }
  };
  return el;
}
"""),
    ("""function fakeDocument() {""",
     """// A host inside a root carrying data-hf-mode (mode null = no attribute anywhere), as a kit component sees it.
function kitHost(mode) {
  var root = fakeEl("div"), host = fakeEl("div");
  if (mode) root.setAttribute("data-hf-mode", mode);
  root.appendChild(host);
  return host;
}
// Every element under (and including) el.
function descendants(el) {
  var out = [el];
  (el.children || []).forEach(function (c) { out = out.concat(descendants(c)); });
  return out;
}
// The timeline as plain data (eases by token), to compare two builds for determinism.
function serialize(tl) {
  function clean(v) {
    var o = {};
    Object.keys(v || {}).forEach(function (k) {
      if (typeof v[k] === "function") o[k] = v[k].token || (k === "onUpdate" ? "fn" : "fn?");
      else if (k !== "immediateRender") o[k] = v[k];
    });
    return o;
  }
  return JSON.stringify(tl.tweens.map(function (tw) {
    return { kind: tw.kind, at: tw.at, dur: tw.dur, from: clean(tw.from), to: clean(tw.to || tw.vars), ease: tw.ease && tw.ease.token || tw.ease };
  }));
}

function fakeDocument() {"""),
    ("""  fakeText: fakeText, fakeMixed: fakeMixed, parseTransform: parseTransform };""",
     """  fakeText: fakeText, fakeMixed: fakeMixed, parseTransform: parseTransform, kitHost: kitHost, descendants: descendants, serialize: serialize };"""),
])
m = ROOT / "lib" / "manifest.json"
data = json.loads(m.read_text())
data["note"] = data["note"].replace("shorts/ modules load in Shorts projects only.",
                                    "shorts/ modules load in Shorts projects only, kit/ modules in long-form projects only (kit/kit.js before the components).")
data["modules"] = sorted(data["modules"] + ["kit/kit.js"])
data["loadOrder"].insert(data["loadOrder"].index("brand.js") + 1, "kit/kit.js")
m.write_text(json.dumps(data, indent=2) + "\n")
edit("tools/new_video.py", [
    ("""GSAP = "https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"
""", """GSAP = "https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"
FORMAT_ONLY = {"shorts": "shorts", "kit": "long-form"}   # lib/<dir>/ modules that load in one format only
"""),
    ("""    order = [m for m in sync_lib.load_manifest(root)["loadOrder"] if fmt == "shorts" or not m.startswith("shorts/")]""",
     """    order = [m for m in sync_lib.load_manifest(root)["loadOrder"] if FORMAT_ONLY.get(m.split("/")[0], fmt) == fmt]"""),
])
edit("tools/test_new_video.py", [
    ("""        self.assertTrue((p / "lib" / "shorts" / "wipe.js").is_file(), "every manifest module is synced")""",
     """        self.assertTrue((p / "lib" / "shorts" / "wipe.js").is_file(), "every manifest module is synced")
        self.assertTrue((p / "lib" / "kit" / "kit.js").is_file(), "kit modules are synced too")"""),
    ("""        self.assertIn('<script src="lib/shorts/wipe.js"></script>', sh)""",
     """        self.assertIn('<script src="lib/shorts/wipe.js"></script>', sh)
        self.assertNotIn("lib/kit/", sh, "the kit is long-form only")
        self.assertIn('<script src="lib/kit/kit.js"></script>', lf)
        self.assertLess(lf.index("lib/brand.js"), lf.index("lib/kit/kit.js"))"""),
])
edit("tools/test_sync_lib.py", [
    ("""        self.assertIn("shorts/wipe.js", m["modules"])""",
     """        self.assertIn("shorts/wipe.js", m["modules"])
        kit = [x for x in m["loadOrder"] if x.startswith("kit/")]
        self.assertEqual(kit[0], "kit/kit.js", "the kit core loads before its components")
        self.assertEqual(sorted(kit), sorted("kit/" + f.name for f in (ROOT / "lib" / "kit").glob("*.js")))
        self.assertGreater(m["loadOrder"].index("kit/kit.js"), m["loadOrder"].index("brand.js"))"""),
])
print("Task 5 edits applied")
PY
````

- [ ] **Step 3: Run the tests**

Run: `node --test lib/test/*.test.js tools/*.test.js`
Expected: `# pass 106` `# fail 0` (`hygiene.test.js` now scans `lib/kit/kit.js`: no colour literal, every `blur(` site tagged).
Run: `python3 -m unittest discover -s tools -p 'test_new_video.py'` and `… -p 'test_sync_lib.py'`
Expected: `Ran 7 tests … OK` and `Ran 11 tests … OK`.

- [ ] **Step 4: Commit**

````bash
git add lib/kit/kit.js lib/test/kit-contract.js lib/test/kit.test.js lib/test/helpers.js lib/manifest.json tools/new_video.py tools/test_new_video.py tools/test_sync_lib.py
git commit -m "feat(kit): HFKit core — registry, ground mode guard, ground and glass styles, entrances; kit loads in long-form projects" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
````

---

### Task 6: `tools/kit_preview.py` — the fixture project for render-and-compare and the kit QA test

**Files:**
- Create: `tools/kit_preview.py`, `tools/test_kit_preview.py`

**Interfaces:**
- Consumes: `new_video.scaffold(slug, fmt, brand, palette, font, videos_dir, root) -> Path`, `new_video.GSAP`, `project.root_attrs`, `synth._ffmpeg(args)`.
- Produces:
  - `kit_preview.build(components=None, palette="gold", font="geometric", videos_dir=None, slug=None, root=ROOT) -> (project: Path, looks: [(label, "index.html" | overlay rel, t)])` — scaffolds `<videos_dir or renders/kit-preview>/<slug or kit-<palette>>` and writes, in `ORDER` (`title`, `subtitle`, `roadmap`, `cta-youtube`, `lower-third`, `side-text`): full-frame components as reel scenes `NN-<key>` (roadmap = intro `03-roadmap` + visit 1 `04-roadmap-2`; slots 4 / 4 / 4 / 3 / 5.5 s → reel 20.5 s), over-footage ones as `compositions/overlays/lower-third.html` / `side-text.html`; BRIEF film/direction, beat-grid rows, a transcript; for the CTA a synthetic `assets/captures/watch-page.png` (2560×1440, player `[112, 150, 1600, 900]`, link `[150, 1235, 560, 44]`) and `face.mp4`. Unknown component → `ValueError("unknown kit component(s) …")`. An overlay-only preview keeps the scaffold placeholder.
  - `kit_preview.FIXTURES` — `component -> [(key, dur, kit call, extra markup, look times)]`; `kit_preview.ORDER`, `OVER_FOOTAGE`.
  - CLI `python3 tools/kit_preview.py [component …] [--palette p] [--font f] [--videos-dir d] [--slug s]` prints the `npx hyperframes snapshot … --at … --no-end -o renders/kit/<slug>` command, one overlay render command per overlay with its look times, and the re-sync hint.

- [ ] **Step 1: Write the failing test**

Create `tools/test_kit_preview.py`:

````python
import io
import re
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import kit_preview as kp
import project as pj
import synth

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("node") and synth.HAVE_FFMPEG, "needs node and ffmpeg")
class KitPreviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.videos = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_every_component_full_frame_scenes_then_overlays(self):
        p, looks = kp.build(videos_dir=self.videos)
        self.assertEqual(p.name, "kit-gold")
        slots = pj.composition_slots(p)
        self.assertEqual([s["id"] for s in slots], ["01-title", "02-subtitle", "03-roadmap", "04-roadmap-2", "05-cta"])
        self.assertEqual([s["start"] for s in slots], [0, 4, 8, 12, 15])
        self.assertEqual(pj.root_attrs(p)["data-duration"], "20.5")
        self.assertEqual(sorted(x.name for x in (p / "compositions" / "overlays").glob("*.html")), ["lower-third.html", "side-text.html"])
        rows = pj.read_storyboard(p)
        self.assertEqual([r["placement"] for r in rows].count("over-footage"), 2)
        self.assertEqual(pj.validate_brief(pj.read_brief(p)), [])
        self.assertTrue((p / "assets" / "captures" / "watch-page.png").is_file())
        self.assertTrue((p / "assets" / "captures" / "face.mp4").is_file())
        self.assertIn(("01-title", "index.html", 3.6), looks)
        self.assertIn(("lower-third", "compositions/overlays/lower-third.html", 3.0), looks)
        self.assertNotIn("hf-placeholder", (p / "index.html").read_text())

    def test_scene_and_overlay_wiring(self):
        p, _ = kp.build(videos_dir=self.videos)
        cta = (p / "compositions" / "05-cta.html").read_text()
        self.assertIn('<video id="05-cta-face" class="cta-face"', cta, "the footage video has an id (HyperFrames media rule)")
        self.assertIn("""document.querySelector('[data-composition-id="05-cta"] .cta-face')""", cta)
        ov = (p / "compositions" / "overlays" / "side-text.html").read_text()
        self.assertNotIn("<template>", ov)
        self.assertNotIn("../", ov, "overlays use root-relative paths")
        self.assertIn('<script src="lib/kit/side-text.js"></script>', ov)
        self.assertIn('href="compositions/brand.css"', ov)
        self.assertIn('data-hf-mode="dark"', ov)
        for f in (p / "compositions").rglob("*.html"):
            self.assertNotRegex(f.read_text(), r"""(?:id|class)\s*=\s*["'][^"']*caption""", f.name)

    def test_light_palette_and_subset(self):
        p, looks = kp.build(["lower-third"], palette="silver", videos_dir=self.videos)
        self.assertEqual(p.name, "kit-silver")
        self.assertEqual(pj.composition_slots(p), [])
        self.assertIn('data-hf-mode="light"', (p / "compositions" / "overlays" / "lower-third.html").read_text())
        self.assertIn("hf-placeholder", (p / "index.html").read_text(), "an overlay-only preview keeps the scaffold placeholder")
        self.assertFalse((p / "assets" / "captures" / "face.mp4").exists())
        with self.assertRaisesRegex(ValueError, r"unknown kit component\(s\) badge"):
            kp.build(["badge"], videos_dir=self.videos)

    def test_cli_prints_snapshot_and_overlay_commands(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(kp.main(["kit_preview.py", "title", "side-text", "--videos-dir", str(self.videos)]), 0)
        text = out.getvalue()
        self.assertRegex(text, r"npx hyperframes snapshot \S+kit-gold --at 1,3\.6 --no-end -o \S+renders/kit/kit-gold")
        self.assertIn("-c compositions/overlays/side-text.html --format=mov -q draft", text)
        self.assertIn("(look at 3.9 s)", text)
        self.assertIn("python3 tools/sync_lib.py", text)


if __name__ == "__main__":
    unittest.main()
````

Run: `python3 -m unittest discover -s tools -p 'test_kit_preview.py'`
Expected: `ModuleNotFoundError: No module named 'kit_preview'`.

- [ ] **Step 2: Implement**

Create `tools/kit_preview.py`:

````python
"""Kit preview: a long-form project holding chosen kit components with fixture copy, for render-and-compare
against the template stills and for the kit QA test (tools/test_kit_qa.py).

Full-frame components become reel scenes, in this order: title, subtitle, roadmap (intro + visit 1),
cta-youtube; over-footage ones become standalone documents compositions/overlays/<name>.html. The CTA gets a
synthetic watch-page screenshot and a still face clip (ffmpeg) — real projects use real captures.

Usage:
  python3 tools/kit_preview.py [component ...] [--palette gold] [--font geometric] [--videos-dir renders/kit-preview] [--slug kit-<palette>]
Default: every component. Prints the snapshot / overlay-render commands and the times worth looking at.
After a lib change, re-sync instead of rebuilding: python3 tools/sync_lib.py <project>.
"""
import argparse
import json
import re
import sys
from pathlib import Path

import new_video
import project as pj
import synth

ROOT = Path(__file__).resolve().parents[1]
ORDER = ["title", "subtitle", "roadmap", "cta-youtube", "lower-third", "side-text"]
STEPS = ('[{ label: "Predictive Idea Selection", icon: "bulb" }, { label: "Retention Based Editing", icon: "sliders" }, '
         '{ label: "Qualified Sales Calls", icon: "target" }]')
PAGE = ('{ src: "assets/captures/watch-page.png", width: 2560, height: 1440, '
        'player: [112, 150, 1600, 900], link: [150, 1235, 560, 44] }')
# component -> [(scene key, duration s, kit call, extra markup in the scene root, times to look at (scene-local s))]
FIXTURES = {
    "title": [("title", 4, 'HFKit.title(tl, host, { format: "long-form", at: 0.2, text: "Printing Prediction System", underline: 1 });', "", [1.0, 3.6])],
    "subtitle": [("subtitle", 4, 'HFKit.subtitle(tl, host, { format: "long-form", at: 0.2, kicker: "Step 1", title: "HIT Prediction" });', "", [0.5, 3.6])],
    "roadmap": [
        ("roadmap", 4, 'HFKit.roadmap(tl, host, { format: "long-form", at: 0.2, visit: 0, title: "Printing Prediction System", steps: ' + STEPS + ' });', "", [1.2, 3.6]),
        ("roadmap-2", 3, 'HFKit.roadmap(tl, host, { format: "long-form", at: 0.2, visit: 1, title: "Printing Prediction System", steps: ' + STEPS + ' });', "", [0.1, 2.8]),
    ],
    "cta-youtube": [("cta", 5.5, 'HFKit.ctaYoutube(tl, host, { format: "long-form", at: 0, page: ' + PAGE +
                     ', footage: document.querySelector(\'[data-composition-id="{id}"] .cta-face\') });',
                     '<video id="{id}-face" class="cta-face" src="assets/captures/face.mp4" data-start="0" data-duration="5.5" muted playsinline></video>',
                     [0.3, 1.2, 2.5, 5.3])],
    "lower-third": [("lower-third", 4, 'HFKit.lowerThird(tl, host, { format: "long-form", at: 0.3, text: "and I\'ve helped online entrepreneurs", out: 3.4 });', "", [3.0])],
    "side-text": [("side-text", 5, 'HFKit.sideText(tl, host, { format: "long-form", at: 0.2, items: ["Video performance", "Retention", "CTR (Click through rate)"], out: 4.4 });', "", [3.9])],
}
OVER_FOOTAGE = {"lower-third", "side-text"}
SCENE = """<template>
  <style>#root {{ position: absolute; inset: 0; overflow: hidden; }}</style>
  <div id="root" data-composition-id="{id}" data-width="1920" data-height="1080"><div class="kit-host"></div>{extra}</div>
  <script>
    (async function () {{
      var tl = gsap.timeline({{ paused: true }});
      await document.fonts.ready;
      var host = document.querySelector('[data-composition-id="{id}"] .kit-host');
      {call}
      await HFText.ready();
      window.__timelines["{id}"] = tl;
    }})();
  </script>
</template>
"""
OVERLAY = """<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=1920, height=1080">
  <script src="{gsap}"></script>
{scripts}
  <link rel="stylesheet" href="compositions/brand.css">
  <style>
    html, body {{ margin: 0; width: 1920px; height: 1080px; overflow: hidden; background: transparent; }}
    #{id}-root {{ position: relative; width: 1920px; height: 1080px; overflow: hidden; }}
  </style>
</head>
<body>
  <div id="{id}-root" data-composition-id="{id}" data-hf-mode="{mode}" data-start="0" data-duration="{dur:g}" data-width="1920" data-height="1080"><div class="kit-host"></div></div>
  <script>
    (async function () {{
      var tl = gsap.timeline({{ paused: true }});
      await document.fonts.ready;
      var host = document.querySelector("#{id}-root .kit-host");
      {call}
      await HFText.ready();
      window.__timelines["{id}"] = tl;
    }})();
  </script>
</body>
</html>
"""


def write_media(project):
    """A stand-in watch-page screenshot (player + description link) and a still face clip."""
    cap = Path(project) / "assets" / "captures"
    synth._ffmpeg(["-f", "lavfi", "-i", "color=c=0x0f0f0f:s=2560x1440,drawbox=x=112:y=150:w=1600:h=900:color=0x272727:t=fill,"
                   "drawbox=x=112:y=1170:w=1600:h=220:color=0x222222:t=fill,drawbox=x=150:y=1235:w=560:h=44:color=0x3ea6ff:t=fill",
                   "-frames:v", "1", str(cap / "watch-page.png")])
    synth._ffmpeg(["-f", "lavfi", "-i", "color=c=0x8a7d72:s=1920x1080:r=30:d=6", "-pix_fmt", "yuv420p", str(cap / "face.mp4")])


def build(components=None, palette="gold", font="geometric", videos_dir=None, slug=None, root=ROOT):
    """Scaffold and fill the preview project. Returns (project, looks): looks = [(label, reel or overlay rel, t)]."""
    components = components or ORDER
    unknown = [c for c in components if c not in FIXTURES]
    if unknown:
        raise ValueError(f"unknown kit component(s) {', '.join(unknown)} (have: {', '.join(ORDER)})")
    project = new_video.scaffold(slug or f"kit-{palette}", "long-form", "contentporary", palette, font,
                                 videos_dir or Path(root) / "renders" / "kit-preview", root)
    mode = pj.root_attrs(project)["data-hf-mode"]
    scripts = re.findall(r'    <script src="lib/[^"]+"></script>', (project / "index.html").read_text())
    slots, rows, looks, t, n = [], [], [], 0.0, 0
    for comp in [c for c in ORDER if c in components]:
        for key, dur, call, extra, at in FIXTURES[comp]:
            if comp in OVER_FOOTAGE:
                rel = f"compositions/overlays/{key}.html"
                (project / rel).write_text(OVERLAY.format(id=key, dur=dur, call=call, mode=mode, gsap=new_video.GSAP, scripts="\n".join(scripts)))
                rows.append(f'| {t:g} | {t + dur:g} | "{key}" | over-footage | {comp} | — | ease.enter | — |')
                looks += [(key, rel, a) for a in at]
                continue
            n += 1
            sid = f"{n:02d}-{key}"
            (project / "compositions" / f"{sid}.html").write_text(
                SCENE.format(id=sid, call=call.replace("{id}", sid), extra=extra.replace("{id}", sid)))
            slots.append(f'<div id="s-{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" '
                         f'data-start="{t:g}" data-duration="{dur:g}" data-track-index="1" data-width="1920" data-height="1080"></div>')
            rows.append(f'| {t:g} | {t + dur:g} | "{key}" | full-frame | {comp} | — | ease.camera | — |')
            looks += [(sid, "index.html", round(t + a, 3)) for a in at]
            t += dur
    if slots:   # a reel with scenes replaces the scaffold placeholder; an overlay-only preview keeps it
        index = project / "index.html"
        html = re.sub(r'\n\s*<!-- placeholder[^\n]*-->\n\s*<div id="hf-placeholder"[^\n]*</div>', "\n      " + "\n      ".join(slots), index.read_text())
        html = re.sub(r'\n\s*tl\.to\("#hf-placeholder"[^\n]*', "", html)
        index.write_text(html.replace('data-duration="5"', f'data-duration="{t:g}"', 1))
    brief = (project / "BRIEF.md").read_text().replace('film: ""', 'film: "Every kit component, as the template stills show it"')
    (project / "BRIEF.md").write_text(brief.replace('direction: ""', 'direction: "Kit preview: one scene or overlay per component"'))
    (project / "storyboard.md").write_text((project / "storyboard.md").read_text().rstrip("\n") + "\n" + "\n".join(rows) + "\n")
    (project / "transcript.json").write_text(json.dumps([{"text": "(kit preview)", "start": 0, "end": max(t, 5.0)}]) + "\n")
    if "cta-youtube" in components:
        write_media(project)
    return project, looks


def main(argv) -> int:
    ap = argparse.ArgumentParser(prog="python3 tools/kit_preview.py", description="Preview project for lib/kit components.")
    ap.add_argument("components", nargs="*")
    ap.add_argument("--palette", default="gold")
    ap.add_argument("--font", default="geometric")
    ap.add_argument("--videos-dir")
    ap.add_argument("--slug")
    a = ap.parse_args(argv[1:])
    try:
        project, looks = build(a.components or None, a.palette, a.font, a.videos_dir, a.slug)
    except ValueError as e:
        print(e)
        return 1
    out = ROOT / "renders" / "kit" / project.name
    reel = [t for _, rel, t in looks if rel == "index.html"]
    print(f"created {project}")
    if reel:
        print(f"  stills:  npx hyperframes snapshot {project} --at {','.join(f'{t:g}' for t in reel)} --no-end -o {out}")
    for key in sorted({k for k, rel, _ in looks if rel != "index.html"}):
        ts = ",".join(f"{t:g}" for k, _, t in looks if k == key)
        print(f"  overlay: npx hyperframes render {project} -c compositions/overlays/{key}.html --format=mov -q draft -o {out}/{key}.mov"
              f"   (look at {ts} s)")
    print(f"  after a lib change: python3 tools/sync_lib.py {project}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
````

- [ ] **Step 3: Run the tests**

Run: `python3 -m unittest discover -s tools -p 'test_kit_preview.py' -v`
Expected: `Ran 4 tests … OK` (≈ 2 s). The project only holds files: the components it calls arrive in Tasks 7–12.

- [ ] **Step 4: Commit**

````bash
git add tools/kit_preview.py tools/test_kit_preview.py
git commit -m "feat(tools): kit_preview builds a fixture project of kit components for render-and-compare" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
````

---

### Task 7: `HFKit.title` — variant `glow-center`

**Files:**
- Create: `lib/kit/title.js`, `lib/test/kit-title.test.js`
- Modify: `lib/manifest.json`

**Interfaces:**
- Consumes: `HFKit.register / begin / ground / el / svg / cardIn / slideIn / fadeOut / pop / FRAME / GLOW` (Task 5), `HFText.words / splitWords / glowTitle / defocus / track` (Task 2), `HFMarks.draw / highlight / statusChip / scriptWord / scribblePath / sweepDuration`, `HFCamera.rig / domTransform`, `HFProfile.timing / ease`; the contract in `lib/test/kit-contract.js`.
- Produces: `HFKit.title(tl, host, {format: "long-form", at, text, underline?}) -> {dur, words: [span]}` — full-frame. Dark: ground with warm ambience (`--hf-extras-ambient-glow`, else `--hf-ground-centre`), grid defocused behind the title (`HFText.defocus`), `HFText.glowTitle` at bloom `HFKit.GLOW`; light: `HFText.words`, no ambience, no glow. `underline: i` draws a double-pass scribble (`accent.line`) inside word i, one chain gap after the title settles, on `ease.sweep` (`HFMarks.sweepDuration` of the word width). Throws `HFKit.title: opts.text is required`, `HFKit.title: underline <i> is not a word index (0–<n-1>)`. Type: 104 px, line top 478 px (centred on 540).

- [ ] **Step 1: Write the failing test**

Create `lib/test/kit-title.test.js`:

````javascript
"use strict";
var test = require("node:test");
var assert = require("node:assert/strict");
var h = require("./helpers.js");
var P = require("../profile.js");
var c = require("./kit-contract.js");
var K = require("../kit/kit.js");
require("../kit/title.js");

function build(tl, host, extra) {
  return K.title(tl, host, Object.assign({ format: "long-form", at: 0.2, text: "Printing  Prediction System", underline: 1 }, extra));
}
c.contract("title", build);

test("title (dark): glow title words 430 ms apart, warm ambience, underline after it settles", function () {
  c.fresh();
  var tl = h.fakeTimeline(), host = h.kitHost("dark"), r = build(tl, host, {});
  assert.deepEqual(r.words.map(function (s) { return s._text; }), ["Printing ", "Prediction ", "System"]);
  assert.equal(r.words[1].children[0].getAttribute("class"), "hf-kit-underline", "the underline lives inside its word");
  r.words.forEach(function (s) { assert.equal(s.getAttribute("data-blur-reason"), "glow"); });
  assert.equal(tl.drivers().length, 1, "one glow driver");
  assert.ok(h.descendants(host).some(function (e) { return e.className === "hf-kit-ground-ambient"; }));
  var draw = tl.eased().filter(function (tw) { return tw.ease.token === "ease.sweep"; })[0];
  var glow = 2 * P.timing("long-form").glow.nextWord + P.timing("long-form").glow.settle;
  assert.ok(Math.abs(draw.at - (0.2 + glow + P.timing("long-form").chainGap)) < 1e-9, "underline starts one chain gap after the title settles");
  assert.ok(Math.abs(r.dur - (draw.at - 0.2 + draw.dur)) < 1e-9);
  assert.deepEqual(h.seekOrderInvariant(tl, [0, 0.2, 0.3, 0.63, 0.9, 1.06, 1.5, 4], r.words), []);
});

test("title (light): words entrance in text.primary, no ambience, same underline", function () {
  c.fresh();
  var tl = h.fakeTimeline(), host = h.kitHost("light"), r = build(tl, host, {});
  assert.equal(tl.drivers().length, 0);
  r.words.forEach(function (s) { assert.equal(s.getAttribute("data-blur-reason"), "focus"); });
  assert.ok(!h.descendants(host).some(function (e) { return e.className === "hf-kit-ground-ambient"; }));
  assert.equal(tl.eased().filter(function (tw) { return tw.ease.token === "ease.sweep"; }).length, 1);
});

test("title: text is required; underline must name a word", function () {
  c.fresh();
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { text: "  " }); }, /opts\.text is required/);
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { underline: 7 }); }, /underline 7 is not a word index \(0–2\)/);
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { at: -1 }); }, /opts\.at must be a time/);
});
````

- [ ] **Step 2: Run it to make sure it fails**

Run: `node --test lib/test/kit-title.test.js`
Expected: FAIL — `Cannot find module '../kit/title.js'`.

- [ ] **Step 3: Implement**

Create `lib/kit/title.js`:

````javascript
/* HFKit.title — variant "glow-center" (template still: full-screen title, gold).
 * A centred one-line headline on the full-frame ground; the grid rack-defocuses behind it.
 * Dark ground: HFText.glowTitle (pop to 70 %, settle 0.4 s ease.glow, next word +430 ms), warm
 * ambient glow at the top. Light ground: no glow — HFText.words in dark text.primary.
 * Optional scribble underline (accent.line) under one word, drawn on ease.sweep once the title
 * has settled — the glow-center still's underline; on the light ground it is the emphasis mark.
 *
 *   HFKit.title(tl, host, { format: "long-form", at: 0.2, text: "Printing Prediction System", underline: 1 })
 *   -> { dur, words: [span…] }
 * Type: 104 px (9.6 % of frame height; long-form glow titles are 9–12 % H). */
(function (root) {
  "use strict";
  var NODE = typeof module !== "undefined" && module.exports;
  var K = NODE ? require("./kit.js") : root.HFKit;
  var P = NODE ? require("../profile.js") : root.HFProfile;
  var X = NODE ? require("../text.js") : root.HFText;
  var M = NODE ? require("../marks.js") : root.HFMarks;

  // A double-pass scribble (out and back) in a 1000 × 40 box, stretched under its word.
  function scribble(seed) {
    return M.scribblePath(20, 16, 960, seed) + M.scribblePath(985, 26, -950, seed + 2).replace(/^M/, " L");
  }
  function underline(tl, word, T, lf) {
    var box = K.svg("svg", { "class": "hf-kit-underline", viewBox: "0 0 1000 40", preserveAspectRatio: "none" }, word);
    var path = K.svg("path", { d: scribble(3) }, box);
    var dur = M.sweepDuration(word.offsetWidth || 1, lf.frameHeight, lf.format);
    M.draw(tl, path, T, dur, lf);
    return dur;
  }

  function glowCenter(tl, host, opts) {
    var b = K.begin("title", host, opts), T = b.at;
    if (typeof opts.text !== "string" || !opts.text.trim()) throw new Error("HFKit.title: opts.text is required");
    var g = K.ground(host, { ambient: b.mode === "dark", quiet: true });
    var line = K.el("div", "hf-kit-title hf-kit-headline", host, opts.text.trim().replace(/\s+/g, " "));
    var spans, dur;
    if (b.mode === "dark") {
      spans = X.splitWords(line);
      X.defocus(tl, g.grid, T, b.lf);
      dur = X.glowTitle(tl, spans, T, Object.assign({ intensity: K.GLOW }, b.lf));
    } else {
      dur = X.words(tl, line, T, Object.assign({ onSpans: function (s) { spans = s; } }, b.lf));
    }
    spans.forEach(function (s) { s.classList.add("hf-kit-word"); });
    if (opts.underline != null) {
      var w = spans[opts.underline];
      if (!w) throw new Error("HFKit.title: underline " + opts.underline + " is not a word index (0–" + (spans.length - 1) + ")");
      var gap = P.timing(b.lf.format).chainGap;
      dur += gap + underline(tl, w, T + dur + gap, b.lf);
    }
    return { dur: dur, words: spans };
  }

  K.register("title", "glow-center", glowCenter, [
    ".hf-kit-title{position:absolute;left:0;right:0;top:478px;text-align:center;font-size:104px;line-height:1.2;letter-spacing:0.005em}"
  ].join("\n"));
})(typeof window !== "undefined" ? window : this);
````

List it in the manifest (the hygiene test requires `lib/` to hold exactly the manifest modules):

````bash
python3 - . title <<'PY'
# List one kit component in lib/manifest.json: modules sorted; loadOrder right after the last kit/ entry.
import json
import sys
from pathlib import Path
ROOT, name = Path(sys.argv[1]), sys.argv[2]
m = ROOT / "lib" / "manifest.json"
data = json.loads(m.read_text())
rel = f"kit/{name}.js"
if rel in data["modules"]:
    sys.exit(f"{rel} is already listed")
data["modules"] = sorted(data["modules"] + [rel])
last = max(i for i, x in enumerate(data["loadOrder"]) if x.startswith("kit/"))
data["loadOrder"].insert(last + 1, rel)
m.write_text(json.dumps(data, indent=2) + "\n")
print(f"listed {rel}")
PY
````

- [ ] **Step 4: Run the tests**

Run: `node --test lib/test/*.test.js tools/*.test.js`
Expected: `# pass 113` `# fail 0` (`kit.test.js` now also checks that `title` registers the variant `tokens.json` names; `hygiene.test.js` scans `lib/kit/title.js`).

- [ ] **Step 5: Render and compare with the template still**

`STILLS` below is the folder holding Tymek's template stills (`1.png` … `7.webp`); if you do not have them, compare against the acceptance numbers alone.

````bash
python3 tools/kit_preview.py title --palette gold --slug title-gold
npx hyperframes snapshot renders/kit-preview/title-gold --at 1,3.6 --no-end -o renders/kit/title-gold
python3 tools/kit_preview.py title --palette silver --slug title-silver
npx hyperframes snapshot renders/kit-preview/title-silver --at 3.6 --no-end -o renders/kit/title-silver
ffmpeg -loglevel error -y -i renders/kit/title-gold/frame-01-at-3.6s.png -i "$STILLS/1.png" \
  -filter_complex "[0]scale=960:540[a];[1]scale=960:540[b];[a][b]hstack" renders/kit/title-compare.png
````
Acceptance (view every frame named above; fix and re-run `python3 tools/sync_lib.py <project>` + the render until all hold):
- One centred line, vertical centre at 540 ± 20 px; the line spans ≈ 60–70 % of the frame width (1.png: x 350–1565; it depends on the installed headline font); cap height ≈ 6–7 % H (68–75 px) — 104 px type, inside the 9–12 % H glow-title band.
- Gold: a warm amber radial glow from the top centre fading to near-black corners (1.png); the grid at most faintly visible (it is defocused, σ 4.5 px, brightness 0.6).
- A soft white halo hugs the letters; letter counters (`e`, `o`, `g`) stay open — a smear that fills them means the bloom is too strong.
- An amber double-stroke scribble sits under word 2, ≈ 0.3–0.4 em below the baseline, spanning the word; at 1 s it is not there yet (it draws after the title settles, ≈ 1.8–2.6 s).
- Silver (light): the same layout, dark `text.primary`, no halo, no amber ambience, coral underline (`accent.line`).

- [ ] **Step 6: Commit**

````bash
git add lib/kit/title.js lib/test/kit-title.test.js lib/manifest.json
git commit -m "feat(kit): HFKit.title — variant `glow-center`" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
````

---

### Task 8: `HFKit.subtitle` — variant `glass-pill-script`

**Files:**
- Create: `lib/kit/subtitle.js`, `lib/test/kit-subtitle.test.js`
- Modify: `lib/manifest.json`

**Interfaces:**
- Consumes: `HFKit.register / begin / ground / el / svg / cardIn / slideIn / fadeOut / pop / FRAME / GLOW` (Task 5), `HFText.words / splitWords / glowTitle / defocus / track` (Task 2), `HFMarks.draw / highlight / statusChip / scriptWord / scribblePath / sweepDuration`, `HFCamera.rig / domTransform`, `HFProfile.timing / ease`; the contract in `lib/test/kit-contract.js`.
- Produces: `HFKit.subtitle(tl, host, {format: "long-form", at, title, kicker?}) -> {dur, pill, kicker: [letter span], words: [span]}` — full-frame on the grid ground. Pill (`.hf-kit-glass`, min 770 px wide, centred, top 404 px) enters with `HFKit.cardIn` at `at`; the kicker (`.hf-kit-script`, 72 px) writes on with `HFMarks.scriptWord` from `at + 0.3` (135 ms/letter); the title (92 px) starts one chain gap after the kicker (`at + 0.3 + 0.475`): dark = `HFText.glowTitle` in `accent.text` at bloom `HFKit.GLOW`; light = `HFText.words` in `text.primary` then an `accent.block` marker sweeps behind it one chain gap after the last word lands (`HFMarks.highlight`). Without a kicker the title starts after the card (`at + 0.43`). Throws `HFKit.subtitle: opts.title is required`.

- [ ] **Step 1: Write the failing test**

Create `lib/test/kit-subtitle.test.js`:

````javascript
"use strict";
var test = require("node:test");
var assert = require("node:assert/strict");
var h = require("./helpers.js");
var P = require("../profile.js");
var c = require("./kit-contract.js");
var K = require("../kit/kit.js");
require("../kit/subtitle.js");

function build(tl, host, extra) {
  return K.subtitle(tl, host, Object.assign({ format: "long-form", at: 0.2, kicker: "Step 1", title: "HIT Prediction" }, extra));
}
c.contract("subtitle", build);

test("subtitle (dark): pill card entrance, script kicker at +0.3 s, glowing title one chain gap later", function () {
  c.fresh();
  var T = P.timing("long-form"), tl = h.fakeTimeline(), r = build(tl, h.kitHost("dark"), {});
  var card = tl.eased()[0];
  assert.equal(card.target, r.pill); assert.equal(card.ease.token, "ease.card"); assert.equal(card.at, 0.2);
  assert.equal(r.kicker.length, 6);
  var sets = tl.tweens.filter(function (tw) { return tw.kind === "set"; });
  assert.ok(Math.abs(sets[0].at - 0.5) < 1e-9 && Math.abs(sets[1].at - (0.5 + T.scriptMsPerChar / 1000)) < 1e-9, "135 ms per letter from +0.3 s");
  var glow = tl.drivers()[0];
  assert.ok(Math.abs(glow.at - (0.5 + T.chainGap)) < 1e-9);
  r.words.forEach(function (s) { assert.equal(s.getAttribute("data-blur-reason"), "glow"); });
});

test("subtitle (light): title words, then an accent.block marker sweeps behind it", function () {
  c.fresh();
  var tl = h.fakeTimeline(), host = h.kitHost("light"), r = build(tl, host, {});
  var sweep = tl.eased().filter(function (tw) { return tw.ease.token === "ease.sweep"; });
  assert.equal(sweep.length, 1);
  assert.equal(sweep[0].target.className, "hf-kit-marker");
  var lastWord = tl.eased().filter(function (tw) { return r.words.indexOf(tw.target) !== -1; }).pop();
  assert.ok(sweep[0].at >= lastWord.at + lastWord.dur, "the marker follows the landed title");
});

test("subtitle: title required; kicker optional", function () {
  c.fresh();
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { title: "" }); }, /opts\.title is required/);
  var r = build(h.fakeTimeline(), h.kitHost("dark"), { kicker: null });
  assert.deepEqual(r.kicker, []);
});
````

- [ ] **Step 2: Run it to make sure it fails**

Run: `node --test lib/test/kit-subtitle.test.js`
Expected: FAIL — `Cannot find module '../kit/subtitle.js'`.

- [ ] **Step 3: Implement**

Create `lib/kit/subtitle.js`:

````javascript
/* HFKit.subtitle — variant "glass-pill-script" (template still: step card).
 * A "Step 1" script kicker over a title in a glass pill, centred on the grid ground.
 * Dark ground: dark glass pill (bevelled light rim, faint halo), title in accent.text with
 * HFText.glowTitle. Light ground: frosted white glass, title in dark text.primary (HFText.words)
 * with an accent.block marker sweeping behind it — no glow.
 * Motion: pill card entrance (0.43 s ease.card) → script write-on at +0.3 s (135 ms/letter) →
 * title one chain gap (≈ 0.475 s) after the kicker starts.
 *
 *   HFKit.subtitle(tl, host, { format: "long-form", at: 0.2, kicker: "Step 1", title: "HIT Prediction" })
 *   -> { dur, pill, kicker: [letter span…], words: [span…] }
 * Pill ≥ 40 % of frame width, centred at 50 % / 50 %; kicker 72 px (6.7 % H); title 92 px (8.5 % H). */
(function (root) {
  "use strict";
  var NODE = typeof module !== "undefined" && module.exports;
  var K = NODE ? require("./kit.js") : root.HFKit;
  var P = NODE ? require("../profile.js") : root.HFProfile;
  var X = NODE ? require("../text.js") : root.HFText;
  var M = NODE ? require("../marks.js") : root.HFMarks;

  var KICKER_LEAD = 0.3;   // the kicker starts writing 0.3 s into the card entrance

  function glassPillScript(tl, host, opts) {
    var b = K.begin("subtitle", host, opts), T = b.at, t = P.timing(b.lf.format);
    if (typeof opts.title !== "string" || !opts.title.trim()) throw new Error("HFKit.subtitle: opts.title is required");
    K.ground(host, {});
    var row = K.el("div", "hf-kit-sub-row", host);
    var pill = K.el("div", "hf-kit-glass hf-kit-sub-pill", row);
    var kicker = opts.kicker ? K.el("div", "hf-kit-script hf-kit-sub-kicker", pill, opts.kicker) : null;
    var title = K.el("div", "hf-kit-headline hf-kit-sub-title", pill, opts.title.trim().replace(/\s+/g, " "));
    var dur = K.cardIn(tl, pill, T), letters = [], words = [];
    if (kicker) dur = Math.max(dur, KICKER_LEAD + M.scriptWord(tl, kicker, T + KICKER_LEAD, Object.assign({ onSpans: function (s) { letters = s; } }, b.lf)));
    var tT = T + (kicker ? KICKER_LEAD + t.chainGap : t.card.dur);
    if (b.mode === "dark") {
      words = X.splitWords(title);
      dur = Math.max(dur, tT - T + X.glowTitle(tl, words, tT, Object.assign({ intensity: K.GLOW }, b.lf)));
    } else {
      var wd = X.words(tl, title, tT, Object.assign({ onSpans: function (s) { words = s; } }, b.lf));
      var marker = K.el("div", "hf-kit-marker", title);
      var mT = tT + wd + t.chainGap;
      dur = Math.max(dur, mT - T + M.highlight(tl, marker, mT, b.lf));
    }
    return { dur: dur, pill: pill, kicker: letters, words: words };
  }

  K.register("subtitle", "glass-pill-script", glassPillScript, [
    ".hf-kit-sub-row{position:absolute;left:0;right:0;top:404px;text-align:center}",
    ".hf-kit-sub-pill{position:relative;display:inline-block;min-width:770px;padding:34px 96px 40px;text-align:center}",
    ".hf-kit-sub-kicker{font-size:72px;line-height:1.15;margin-bottom:2px}",
    ".hf-kit-sub-title{position:relative;font-size:92px;line-height:1.3;z-index:0}",
    ".hf-kit-dark .hf-kit-sub-title{color:var(--hf-accent-text)}"
  ].join("\n"));
})(typeof window !== "undefined" ? window : this);
````

List it in the manifest (the hygiene test requires `lib/` to hold exactly the manifest modules):

````bash
python3 - . subtitle <<'PY'
# List one kit component in lib/manifest.json: modules sorted; loadOrder right after the last kit/ entry.
import json
import sys
from pathlib import Path
ROOT, name = Path(sys.argv[1]), sys.argv[2]
m = ROOT / "lib" / "manifest.json"
data = json.loads(m.read_text())
rel = f"kit/{name}.js"
if rel in data["modules"]:
    sys.exit(f"{rel} is already listed")
data["modules"] = sorted(data["modules"] + [rel])
last = max(i for i, x in enumerate(data["loadOrder"]) if x.startswith("kit/"))
data["loadOrder"].insert(last + 1, rel)
m.write_text(json.dumps(data, indent=2) + "\n")
print(f"listed {rel}")
PY
````

- [ ] **Step 4: Run the tests**

Run: `node --test lib/test/*.test.js tools/*.test.js`
Expected: `# pass 120` `# fail 0` (`kit.test.js` now also checks that `subtitle` registers the variant `tokens.json` names; `hygiene.test.js` scans `lib/kit/subtitle.js`).

- [ ] **Step 5: Render and compare with the template still**

`STILLS` below is the folder holding Tymek's template stills (`1.png` … `7.webp`); if you do not have them, compare against the acceptance numbers alone.

````bash
python3 tools/kit_preview.py subtitle --palette gold --slug subtitle-gold
npx hyperframes snapshot renders/kit-preview/subtitle-gold --at 0.5,3.6 --no-end -o renders/kit/subtitle-gold
python3 tools/kit_preview.py subtitle --palette paper --slug subtitle-paper
npx hyperframes snapshot renders/kit-preview/subtitle-paper --at 3.6 --no-end -o renders/kit/subtitle-paper
ffmpeg -loglevel error -y -i renders/kit/subtitle-gold/frame-01-at-3.6s.png -i "$STILLS/2.png" \
  -filter_complex "[0]scale=960:540[a];[1]scale=960:540[b];[a][b]hstack" renders/kit/subtitle-compare.png
````
Acceptance (view every frame named above; fix and re-run `python3 tools/sync_lib.py <project>` + the render until all hold):
- Pill centred: ≈ 770–820 × 250–290 px (prototype: x 556–1364, y 404–686; 2.png: x 575–1345, y 410–665), radius ≈ 36 px; a lighter bevelled rim (top edge brightest), a faint light halo, no dark drop shadow.
- Grid lines (150 px cells) and dotted rows visible around the pill, lighter than the ground, fading to the corners (2.png).
- Kicker ≈ 6.7 % H above the title; with Brittany Signature installed it is a monoline script, without it a serif fallback (note it, do not restyle the kit).
- Title ≈ 8.5 % H in warm `accent.text` (gold: pale amber) with a soft glow — counters open, no smear. At 0.5 s the pill is mid-entrance (lower, dimmer, slightly soft) and the title is not visible.
- Paper (light): frosted white pill with a soft neutral shadow; dark-brown title on an orange `accent.block` marker; no glow.

- [ ] **Step 6: Commit**

````bash
git add lib/kit/subtitle.js lib/test/kit-subtitle.test.js lib/manifest.json
git commit -m "feat(kit): HFKit.subtitle — variant `glass-pill-script`" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
````

---

### Task 9: `HFKit.lowerThird` — variant `key-line`

**Files:**
- Create: `lib/kit/lower-third.js`, `lib/test/kit-lower-third.test.js`
- Modify: `lib/manifest.json`

**Interfaces:**
- Consumes: `HFKit.register / begin / ground / el / svg / cardIn / slideIn / fadeOut / pop / FRAME / GLOW` (Task 5), `HFText.words / splitWords / glowTitle / defocus / track` (Task 2), `HFMarks.draw / highlight / statusChip / scriptWord / scribblePath / sweepDuration`, `HFCamera.rig / domTransform`, `HFProfile.timing / ease`; the contract in `lib/test/kit-contract.js`.
- Produces: `HFKit.lowerThird(tl, host, {format: "long-form", at, text, out?}) -> {dur, words: [span]}` — over-footage, one line centred at top 962 px (50 px body font, line-height 1.3 → baseline ≈ 1012 px). Dark: words via `HFText.words`, each word painted with one shared `text.primary` (0–45 %) → `accent.text` (100 %) gradient (`background-size` = line width, `background-position` = −word offset; repainted once fonts land via `HFText.track`). Light: the line is a frosted pill entering with `HFKit.cardIn`; words start 0.15 s later; no gradient. `out`: the root fades (`HFKit.fadeOut`, 0.43 s) to be gone at `out`; an `out` earlier than landing + fade throws `HFKit.lowerThird: opts.out (<s> s) leaves no hold …`. Throws `HFKit.lowerThird: opts.text is required`. No id/class contains `caption`.

- [ ] **Step 1: Write the failing test**

Create `lib/test/kit-lower-third.test.js`:

````javascript
"use strict";
var test = require("node:test");
var assert = require("node:assert/strict");
var h = require("./helpers.js");
var P = require("../profile.js");
var c = require("./kit-contract.js");
var K = require("../kit/kit.js");
require("../kit/lower-third.js");

function build(tl, host, extra) {
  return K.lowerThird(tl, host, Object.assign({ format: "long-form", at: 0.3, text: "and I've helped online entrepreneurs", out: 3.4 }, extra));
}
c.contract("lower-third", build);

test("lower-third (dark): one line, words with one continuous white→warm gradient, fades out at opts.out", function () {
  c.fresh();
  var tl = h.fakeTimeline(), host = h.kitHost("dark"), r = build(tl, host, {});
  assert.equal(r.words.length, 5);
  r.words.forEach(function (s) {
    assert.ok(s.classList.contains("hf-kit-lt-word"));
    assert.equal(s.style.backgroundSize, "400px 100%", "every word is painted with the whole line's gradient");
  });
  var fade = tl.eased().filter(function (tw) { return tw.to.opacity === 0; })[0];
  assert.ok(Math.abs(fade.at + fade.dur - 3.4) < 1e-9, "gone at opts.out");
  assert.equal(fade.target.className, "hf-kit-lt");
  assert.doesNotMatch(h.descendants(host).map(function (e) { return e.className + " " + (e.getAttribute("id") || ""); }).join(" "), /caption/i, "QA check 7 must not read it as a caption layer");
});

test("lower-third (light): a frosted pill enters first, words 0.15 s later, no gradient", function () {
  c.fresh();
  var tl = h.fakeTimeline(), r = build(tl, h.kitHost("light"), {});
  var first = tl.eased()[0];
  assert.equal(first.ease.token, "ease.card"); assert.equal(first.target.className, "hf-kit-body hf-kit-lt-line");
  assert.ok(Math.abs(tl.eased()[1].at - 0.45) < 1e-9);
  r.words.forEach(function (s) { assert.ok(!s.classList.contains("hf-kit-lt-word")); });
});

test("lower-third: text required; opts.out must leave a hold", function () {
  c.fresh();
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { text: "" }); }, /opts\.text is required/);
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { out: 1.2 }); }, /leaves no hold/);
  var r = build(h.fakeTimeline(), h.kitHost("dark"), { out: null });
  assert.ok(r.dur > 0);
});
````

- [ ] **Step 2: Run it to make sure it fails**

Run: `node --test lib/test/kit-lower-third.test.js`
Expected: FAIL — `Cannot find module '../kit/lower-third.js'`.

- [ ] **Step 3: Implement**

Create `lib/kit/lower-third.js`:

````javascript
/* HFKit.lowerThird — variant "key-line" (template still: lower third key line).
 * Over-footage layout: ONE key line, bottom-centre, word by word (the long-form word entrance).
 * This is the only on-screen text for spoken words in long-form (no captions — standards/formats/long-form.md).
 * Dark ground: white→warm gradient text (text.primary → accent.text, continuous across the words).
 * Light ground: dark text.primary on a frosted white glass pill (card entrance) — no gradient, no glow.
 * opts.out: when the line has faded out (fade 0.43 s on ease.enter ends at opts.out).
 *
 *   HFKit.lowerThird(tl, host, { format: "long-form", at: 0.3, text: "and I've helped online entrepreneurs", out: 3.2 })
 *   -> { dur, words: [span…] }
 * Type: 50 px body font (4.6 % H); baseline ≈ 95 % of frame height, centred. */
(function (root) {
  "use strict";
  var NODE = typeof module !== "undefined" && module.exports;
  var K = NODE ? require("./kit.js") : root.HFKit;
  var P = NODE ? require("../profile.js") : root.HFProfile;
  var X = NODE ? require("../text.js") : root.HFText;

  var PILL_LEAD = 0.15;   // light ground: words start 0.15 s after the pill starts entering

  function keyLine(tl, host, opts) {
    var b = K.begin("lower-third", host, opts), T = b.at;
    if (typeof opts.text !== "string" || !opts.text.trim()) throw new Error("HFKit.lowerThird: opts.text is required");
    var rootEl = K.el("div", "hf-kit-lt", host);
    var line = K.el("div", "hf-kit-body hf-kit-lt-line", rootEl, opts.text.trim().replace(/\s+/g, " "));
    var words = [], dur = 0, wT = T;
    if (b.mode === "light") { K.cardIn(tl, line, T); wT = T + PILL_LEAD; }
    dur = wT - T + X.words(tl, line, wT, Object.assign({ onSpans: function (s) { words = s; } }, b.lf));
    if (b.mode === "dark") {
      // One gradient across the whole line: each word shows its own slice (positions re-measured once fonts land).
      var paint = function () {
        var W = line.offsetWidth || 1;
        words.forEach(function (s) { s.style.backgroundSize = W + "px 100%"; s.style.backgroundPosition = (-(s.offsetLeft || 0)) + "px 0px"; });
      };
      words.forEach(function (s) { s.classList.add("hf-kit-lt-word"); });
      paint();
      if (typeof document !== "undefined" && document.fonts && document.fonts.ready) X.track(document.fonts.ready.then(paint));
    }
    if (opts.out != null) {
      var fade = P.timing(b.lf.format).card.dur;
      if (!(opts.out - fade >= T + dur)) throw new Error("HFKit.lowerThird: opts.out (" + opts.out + " s) leaves no hold — the line lands at " + (T + dur).toFixed(2) + " s and fades for " + fade + " s");
      K.fadeOut(tl, rootEl, opts.out - fade);
    }
    return { dur: dur, words: words };
  }

  K.register("lower-third", "key-line", keyLine, [
    ".hf-kit-lt{position:absolute;left:0;right:0;top:962px;text-align:center}",
    ".hf-kit-lt-line{position:relative;display:inline-block;font-size:50px;line-height:1.3;letter-spacing:0.01em;white-space:nowrap}",
    ".hf-kit-lt-word{background-image:linear-gradient(90deg,var(--hf-text-primary) 0%,var(--hf-text-primary) 45%,var(--hf-accent-text) 100%);" +
      "-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;color:transparent}",
    ".hf-kit-light .hf-kit-lt-line{padding:12px 40px 14px;border-radius:var(--hf-card-radius);background:var(--hf-surface-fill);" +
      "border:1px solid var(--hf-surface-bevel);box-shadow:0 14px 40px var(--hf-surface-halo)}"
  ].join("\n"));
})(typeof window !== "undefined" ? window : this);
````

List it in the manifest (the hygiene test requires `lib/` to hold exactly the manifest modules):

````bash
python3 - . lower-third <<'PY'
# List one kit component in lib/manifest.json: modules sorted; loadOrder right after the last kit/ entry.
import json
import sys
from pathlib import Path
ROOT, name = Path(sys.argv[1]), sys.argv[2]
m = ROOT / "lib" / "manifest.json"
data = json.loads(m.read_text())
rel = f"kit/{name}.js"
if rel in data["modules"]:
    sys.exit(f"{rel} is already listed")
data["modules"] = sorted(data["modules"] + [rel])
last = max(i for i, x in enumerate(data["loadOrder"]) if x.startswith("kit/"))
data["loadOrder"].insert(last + 1, rel)
m.write_text(json.dumps(data, indent=2) + "\n")
print(f"listed {rel}")
PY
````

- [ ] **Step 4: Run the tests**

Run: `node --test lib/test/*.test.js tools/*.test.js`
Expected: `# pass 127` `# fail 0` (`kit.test.js` now also checks that `lower-third` registers the variant `tokens.json` names; `hygiene.test.js` scans `lib/kit/lower-third.js`).

- [ ] **Step 5: Render and compare with the template still**

`STILLS` below is the folder holding Tymek's template stills (`1.png` … `7.webp`); if you do not have them, compare against the acceptance numbers alone.

````bash
python3 tools/kit_preview.py lower-third --palette gold --slug lt-gold
npx hyperframes render renders/kit-preview/lt-gold -c compositions/overlays/lower-third.html --format=mov -q draft -o renders/kit/lt-gold/lower-third.mov
ffprobe -v error -show_entries stream=codec_name,profile,pix_fmt -of compact renders/kit/lt-gold/lower-third.mov
ffmpeg -loglevel error -y -i "$STILLS/4.webp" -ss 3.0 -i renders/kit/lt-gold/lower-third.mov \
  -filter_complex "[0]scale=1920:1080[bg];[bg][1]overlay=format=auto" -frames:v 1 renders/kit/lt-gold/over-face.png
ffmpeg -loglevel error -y -i renders/kit/lt-gold/over-face.png -i "$STILLS/3.webp" \
  -filter_complex "[0]scale=960:540[a];[1]scale=960:540[b];[a][b]hstack" renders/kit/lower-third-compare.png
python3 tools/kit_preview.py lower-third --palette silver --slug lt-silver
npx hyperframes render renders/kit-preview/lt-silver -c compositions/overlays/lower-third.html --format=mov -q draft -o renders/kit/lt-silver/lower-third.mov
````
(No stills? Use `-f lavfi -i color=c=0x777777:s=1920x1080:d=1` as the backdrop instead of `4.webp`.)
Acceptance (view every frame named above; fix and re-run `python3 tools/sync_lib.py <project>` + the render until all hold):
- `ffprobe` prints `codec_name=prores|profile=4444|pix_fmt=yuva444p12le` (alpha), and outside the line the frame is fully transparent.
- One line, centred, baseline ≈ 1010–1030 px (3.webp: ≈ 1032); text height ≈ 4.6–4.8 % H; the line spans ≈ 40–55 % W (font-dependent; 3.webp ≈ 54 %).
- White over roughly the first half, warming to gold `accent.text` at the right end, continuous across word boundaries — no colour step between two words. No pill, no shadow, no glow on the dark palette.
- Silver (light): a frosted white pill (radius ≈ 36 px, hairline border, soft shadow) behind dark `text.primary`.

- [ ] **Step 6: Commit**

````bash
git add lib/kit/lower-third.js lib/test/kit-lower-third.test.js lib/manifest.json
git commit -m "feat(kit): HFKit.lowerThird — variant `key-line`" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
````

---

### Task 10: `HFKit.sideText` — variant `grid-panel-chips`

**Files:**
- Create: `lib/kit/side-text.js`, `lib/test/kit-side-text.test.js`
- Modify: `lib/manifest.json`

**Interfaces:**
- Consumes: `HFKit.register / begin / ground / el / svg / cardIn / slideIn / fadeOut / pop / FRAME / GLOW` (Task 5), `HFText.words / splitWords / glowTitle / defocus / track` (Task 2), `HFMarks.draw / highlight / statusChip / scriptWord / scribblePath / sweepDuration`, `HFCamera.rig / domTransform`, `HFProfile.timing / ease`; the contract in `lib/test/kit-contract.js`.
- Produces: `HFKit.sideText(tl, host, {format: "long-form", at, items, out?}) -> {dur, chips: [el], labels: [[span]]}` — over-footage. Panel 0–928 × 1080 px slides in 80 px + fades (`HFKit.slideIn`, 0.6 s) at `at`; dark = dark grid panel (`HFKit.ground` inside it), light = frosted white panel (no grid). Each item (`"text"` or `{text, at}`; 1–6): a 90 px `.hf-kit-glass` chip at x 115, y 140 + 145·i with its number in `accent.text` (`HFMarks.statusChip`), and its label (48 px body, x 277) word by word 0.1 s later; default item times `at + 0.3 + i × 0.95`. `out`: everything fades to be gone at `out`. Throws `HFKit.sideText: 1–6 items, got <n>`, `… item <i> has no text`, `… item <i> lands at <t> s, before the panel (<at> s)`, `… opts.out (<s> s) leaves no hold …`.

- [ ] **Step 1: Write the failing test**

Create `lib/test/kit-side-text.test.js`:

````javascript
"use strict";
var test = require("node:test");
var assert = require("node:assert/strict");
var h = require("./helpers.js");
var P = require("../profile.js");
var c = require("./kit-contract.js");
var K = require("../kit/kit.js");
require("../kit/side-text.js");

var ITEMS = ["Video performance", "Retention", "CTR (Click through rate)"];
function build(tl, host, extra) {
  return K.sideText(tl, host, Object.assign({ format: "long-form", at: 0.2, items: ITEMS, out: 4.4 }, extra));
}
c.contract("side-text", build);

test("side-text: panel slides in, each point = chip (status chip) + label words 0.1 s later, rows 145 px apart", function () {
  c.fresh();
  var T = P.timing("long-form"), tl = h.fakeTimeline(), r = build(tl, h.kitHost("dark"), {});
  assert.equal(r.chips.length, 3);
  assert.deepEqual(r.chips.map(function (e) { return e.style.top; }), ["140px", "285px", "430px"]);
  assert.deepEqual(r.chips.map(function (e) { return e.children[0].textContent; }), ["1", "2", "3"]);
  var chipAt = r.chips.map(function (e) { return tl.eased().filter(function (tw) { return [].concat(tw.target).indexOf(e) !== -1; })[0].at; });
  var first = 0.2 + T.words.dur / 2;
  chipAt.forEach(function (a, i) { assert.ok(Math.abs(a - (first + i * 2 * T.chainGap)) < 1e-9, "point " + i); });
  var label0 = tl.eased().filter(function (tw) { return tw.target === r.labels[0][0]; })[0];
  assert.ok(Math.abs(label0.at - (chipAt[0] + 0.1)) < 1e-9);
});

test("side-text: explicit item times, 1–6 points, a point before the panel throws", function () {
  c.fresh();
  var tl = h.fakeTimeline(), r = build(tl, h.kitHost("dark"), { items: [{ text: "One", at: 1 }, { text: "Two", at: 2.5 }], out: null });
  assert.equal(r.chips.length, 2);
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { items: [] }); }, /1–6 items, got 0/);
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { items: ["a", "b", "c", "d", "e", "f", "g"] }); }, /1–6 items, got 7/);
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { items: [{ text: "x", at: 0.1 }] }); }, /before the panel/);
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { out: 2 }); }, /leaves no hold/);
});

test("side-text (light): frosted panel, no grid ground inside it", function () {
  c.fresh();
  var host = h.kitHost("light");
  build(h.fakeTimeline(), host, {});
  assert.ok(!h.descendants(host).some(function (e) { return e.className === "hf-kit-ground"; }));
});
````

- [ ] **Step 2: Run it to make sure it fails**

Run: `node --test lib/test/kit-side-text.test.js`
Expected: FAIL — `Cannot find module '../kit/side-text.js'`.

- [ ] **Step 3: Implement**

Create `lib/kit/side-text.js`:

````javascript
/* HFKit.sideText — variant "grid-panel-chips" (template still: side screen text).
 * Over-footage layout: a left-half panel with 1–6 numbered points; the face stays on the right.
 * Dark ground: the dark grid panel (ground + grid + dot matrix), dark glass number chips with the
 * number in accent.text, labels in text.primary with a faint halo. Light ground: a frosted white
 * glass panel, frosted chips, dark labels — no glow.
 * Motion: panel slides in 80 px + fades (0.6 s ease.enter); each point lands on its time: chip as a
 * status chip (rise + scale + fade, 0.5 s ease.enter) and its label word by word 0.1 s later.
 * items: ["Video performance", …] or [{ text, at }] — at defaults to one point every 2 chain gaps.
 * opts.out: when the panel has faded out.
 *
 *   HFKit.sideText(tl, host, { format: "long-form", at: 0.2, items: ["Video performance", "Retention", "CTR"] })
 *   -> { dur, chips: [el…], labels: [[span…]…] }
 * Panel 0–928 px (48 % W); chips 90 px at x 115, rows every 145 px from y 140; labels 48 px (4.4 % H) at x 277. */
(function (root) {
  "use strict";
  var NODE = typeof module !== "undefined" && module.exports;
  var K = NODE ? require("./kit.js") : root.HFKit;
  var P = NODE ? require("../profile.js") : root.HFProfile;
  var X = NODE ? require("../text.js") : root.HFText;
  var M = NODE ? require("../marks.js") : root.HFMarks;

  var ROW_TOP = 140, ROW_PITCH = 145, LABEL_LAG = 0.1, PANEL_DX = -80, MAX_ITEMS = 6;

  function gridPanelChips(tl, host, opts) {
    var b = K.begin("side-text", host, opts), T = b.at, t = P.timing(b.lf.format);
    var items = (opts.items || []).map(function (it) { return typeof it === "string" ? { text: it } : it; });
    if (items.length < 1 || items.length > MAX_ITEMS) throw new Error("HFKit.sideText: 1–" + MAX_ITEMS + " items, got " + items.length);
    var rootEl = K.el("div", "hf-kit-st", host);
    var panel = K.el("div", "hf-kit-st-panel", rootEl);
    if (b.mode === "dark") K.ground(panel, {});
    var dur = K.slideIn(tl, panel, T, PANEL_DX), chips = [], labels = [];
    var first = T + dur * 0.5, step = 2 * t.chainGap;
    items.forEach(function (it, i) {
      if (typeof it.text !== "string" || !it.text.trim()) throw new Error("HFKit.sideText: item " + i + " has no text");
      var at = it.at == null ? first + i * step : it.at;
      if (at < T) throw new Error("HFKit.sideText: item " + i + " lands at " + at + " s, before the panel (" + T + " s)");
      var top = ROW_TOP + i * ROW_PITCH;
      var chip = K.el("div", "hf-kit-glass hf-kit-st-chip", rootEl);
      chip.style.top = top + "px";
      K.el("span", "hf-kit-st-num", chip, String(i + 1));
      var label = K.el("div", "hf-kit-body hf-kit-st-label", rootEl, it.text.trim().replace(/\s+/g, " "));
      label.style.top = (top + 16) + "px";
      var cd = M.statusChip(tl, chip, at, b.lf), spans = [];
      var wd = X.words(tl, label, at + LABEL_LAG, Object.assign({ onSpans: function (s) { spans = s; } }, b.lf));
      chips.push(chip); labels.push(spans);
      dur = Math.max(dur, at - T + Math.max(cd, LABEL_LAG + wd));
    });
    if (opts.out != null) {
      if (!(opts.out - t.card.dur >= T + dur)) throw new Error("HFKit.sideText: opts.out (" + opts.out + " s) leaves no hold — the last point lands at " + (T + dur).toFixed(2) + " s");
      K.fadeOut(tl, rootEl, opts.out - t.card.dur);
    }
    return { dur: dur, chips: chips, labels: labels };
  }

  K.register("side-text", "grid-panel-chips", gridPanelChips, [
    ".hf-kit-st{position:absolute;inset:0}",
    ".hf-kit-st-panel{position:absolute;left:0;top:0;width:928px;height:1080px;overflow:hidden}",
    ".hf-kit-dark .hf-kit-st-panel{background:var(--hf-ground-deep)}",
    ".hf-kit-light .hf-kit-st-panel{background:var(--hf-surface-fill);border-right:1px solid var(--hf-surface-bevel);box-shadow:0 0 60px var(--hf-surface-halo)}",
    ".hf-kit-st-chip{left:115px;width:90px;height:90px;border-radius:18px;display:flex;align-items:center;justify-content:center}",
    ".hf-kit-st-num{font-family:var(--hf-font-body);font-weight:var(--hf-font-body-weight);font-size:42px;color:var(--hf-accent-text)}",
    ".hf-kit-st-label{position:absolute;left:277px;width:620px;font-size:48px;line-height:1.2;white-space:nowrap}",
    ".hf-kit-dark .hf-kit-st-label{text-shadow:0 0 22px var(--hf-surface-halo)}"
  ].join("\n"));
})(typeof window !== "undefined" ? window : this);
````

List it in the manifest (the hygiene test requires `lib/` to hold exactly the manifest modules):

````bash
python3 - . side-text <<'PY'
# List one kit component in lib/manifest.json: modules sorted; loadOrder right after the last kit/ entry.
import json
import sys
from pathlib import Path
ROOT, name = Path(sys.argv[1]), sys.argv[2]
m = ROOT / "lib" / "manifest.json"
data = json.loads(m.read_text())
rel = f"kit/{name}.js"
if rel in data["modules"]:
    sys.exit(f"{rel} is already listed")
data["modules"] = sorted(data["modules"] + [rel])
last = max(i for i, x in enumerate(data["loadOrder"]) if x.startswith("kit/"))
data["loadOrder"].insert(last + 1, rel)
m.write_text(json.dumps(data, indent=2) + "\n")
print(f"listed {rel}")
PY
````

- [ ] **Step 4: Run the tests**

Run: `node --test lib/test/*.test.js tools/*.test.js`
Expected: `# pass 134` `# fail 0` (`kit.test.js` now also checks that `side-text` registers the variant `tokens.json` names; `hygiene.test.js` scans `lib/kit/side-text.js`).

- [ ] **Step 5: Render and compare with the template still**

`STILLS` below is the folder holding Tymek's template stills (`1.png` … `7.webp`); if you do not have them, compare against the acceptance numbers alone.

````bash
python3 tools/kit_preview.py side-text --palette gold --slug st-gold
npx hyperframes render renders/kit-preview/st-gold -c compositions/overlays/side-text.html --format=mov -q draft -o renders/kit/st-gold/side-text.mov
ffmpeg -loglevel error -y -i "$STILLS/4.webp" -ss 3.9 -i renders/kit/st-gold/side-text.mov \
  -filter_complex "[0]scale=1920:1080[bg];[bg][1]overlay=format=auto" -frames:v 1 renders/kit/st-gold/over-face.png
ffmpeg -loglevel error -y -i renders/kit/st-gold/over-face.png -i "$STILLS/6.webp" \
  -filter_complex "[0]scale=960:540[a];[1]scale=960:540[b];[a][b]hstack" renders/kit/side-text-compare.png
python3 tools/kit_preview.py side-text --palette silver --slug st-silver
npx hyperframes render renders/kit-preview/st-silver -c compositions/overlays/side-text.html --format=mov -q draft -o renders/kit/st-silver/side-text.mov
````
Acceptance (view every frame named above; fix and re-run `python3 tools/sync_lib.py <project>` + the render until all hold):
- Panel exactly x 0–928 (48 % W), full height, hard right edge; everything right of x 928 is transparent (the face shows untouched).
- Inside the panel: 150 px grid lines and dotted rows, lighter than the panel ground, a lit area near the top (6.webp).
- Chips 90 × 90 px at x 115, tops at y 140 / 285 / 430, dark glass with a lighter rim; numbers 1–3 in gold `accent.text`.
- Labels start at x 277, ≈ 4.4 % H, white `text.primary` with a faint halo, vertically centred on their chips.
- Silver (light): frosted white panel with a hairline right border and soft shadow, frosted chips, dark labels, coral numbers; no grid, no halo.

- [ ] **Step 6: Commit**

````bash
git add lib/kit/side-text.js lib/test/kit-side-text.test.js lib/manifest.json
git commit -m "feat(kit): HFKit.sideText — variant `grid-panel-chips`" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
````

---

### Task 11: `HFKit.ctaYoutube` — variant `watch-page-dive`

**Files:**
- Create: `lib/kit/cta-youtube.js`, `lib/test/kit-cta-youtube.test.js`
- Modify: `lib/manifest.json`

**Interfaces:**
- Consumes: `HFKit.register / begin / ground / el / svg / cardIn / slideIn / fadeOut / pop / FRAME / GLOW` (Task 5), `HFText.words / splitWords / glowTitle / defocus / track` (Task 2), `HFMarks.draw / highlight / statusChip / scriptWord / scribblePath / sweepDuration`, `HFCamera.rig / domTransform`, `HFProfile.timing / ease`; the contract in `lib/test/kit-contract.js`.
- Produces: `HFKit.ctaYoutube(tl, host, {format: "long-form", at, footage, page: {src, width, height, player: [x, y, w, h], link: [x, y, w, h]}}) -> {dur: 4.9, poses: {face, player, link}}` — full-frame. Builds a stage (`page.width × page.height`) holding the screenshot `<img>` and a player slot into which it moves `footage` (the face `<video>` — it needs an `id`, HyperFrames' media rule — or a still), then one DOM camera (`HFCamera.rig`, no blur canvas) from `at`: face (player fills the frame, z = max(1920/w, 1080/h)) → 0.5 s → player at 0.80 → hold 0.5 → 0.6 s → link at 2× → hold 1.7 → 0.6 s → player → hold 0.5 → 0.5 s → face; all `ease.camera`. `HFKit.ctaPoses(page, FRAME, timing.cta) -> {face, player, link}` (pure). The page image's decode is tracked (`HFText.track`). Throws `HFKit.ctaYoutube: page needs src, width and height (a real watch-page screenshot)`, `… opts.footage must be the face <video> (or a still) element`, `… page.<player|link> must be [x, y, w, h] in page pixels`.

- [ ] **Step 1: Write the failing test**

Create `lib/test/kit-cta-youtube.test.js`:

````javascript
"use strict";
var test = require("node:test");
var assert = require("node:assert/strict");
var h = require("./helpers.js");
var P = require("../profile.js");
var c = require("./kit-contract.js");
var K = require("../kit/kit.js");
require("../kit/cta-youtube.js");

var PAGE = { src: "assets/captures/watch-page.png", width: 2560, height: 1440, player: [112, 150, 1600, 900], link: [150, 1235, 560, 44] };
function build(tl, host, extra) {
  return K.ctaYoutube(tl, host, Object.assign({ format: "long-form", at: 0, footage: h.fakeEl("video"), page: PAGE }, extra));
}
c.contract("cta-youtube", build);

test("cta poses: the player fills the frame, then 0.80 of it, then 2× onto the link", function () {
  var p = K.ctaPoses(PAGE, K.FRAME, P.timing("long-form").cta);
  assert.deepEqual(p.face, { cx: 912, cy: 600, z: 1.2 });
  assert.ok(Math.abs(p.player.z - 0.96) < 1e-12);
  assert.deepEqual([p.link.cx, p.link.cy], [430, 1257]);
  assert.ok(Math.abs(p.link.z - 1.92) < 1e-12);
});

test("cta: one DOM camera over 4.9 s — scale 0.5, hold 0.5, dive 0.6, hold 1.7, back 0.6, hold 0.5, up 0.5", function () {
  c.fresh();
  var tl = h.fakeTimeline(), host = h.kitHost("dark"), face = h.fakeEl("video"), r = build(tl, host, { footage: face, at: 1 });
  assert.ok(Math.abs(r.dur - 4.9) < 1e-9);
  assert.equal(tl.drivers().length, 1);
  assert.equal(tl.drivers()[0].at, 1);
  var stage = h.descendants(host).filter(function (e) { return e.className === "hf-kit-cta-stage"; })[0];
  assert.equal(face.parentNode.className, "hf-kit-cta-player", "the footage sits in the player slot");
  function zoom(t) { tl.seek(t); return parseFloat(/scale\(([\d.]+)\)/.exec(stage.style.transform)[1]); }
  assert.equal(zoom(1), 1.2); assert.equal(zoom(1.75), 0.96); assert.equal(zoom(3.5), 1.92); assert.equal(zoom(5.2), 0.96); assert.equal(zoom(6), 1.2);
  assert.deepEqual(h.seekOrderInvariant(tl, [0, 1, 1.25, 1.5, 2, 2.3, 2.6, 4, 4.6, 5, 5.4, 5.9, 7], [stage]), []);
});

test("cta: a real page screenshot and the footage element are required", function () {
  c.fresh();
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { page: { width: 10, height: 10 } }); }, /page needs src, width and height/);
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { footage: null }); }, /opts\.footage must be/);
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { page: Object.assign({}, PAGE, { link: [1, 2, 3] }) }); }, /page\.link must be \[x, y, w, h\]/);
});
````

- [ ] **Step 2: Run it to make sure it fails**

Run: `node --test lib/test/kit-cta-youtube.test.js`
Expected: FAIL — `Cannot find module '../kit/cta-youtube.js'`.

- [ ] **Step 3: Implement**

Create `lib/kit/cta-youtube.js`:

````javascript
/* HFKit.ctaYoutube — variant "watch-page-dive" (the long-form CTA template).
 * The face footage scales to 0.80 into a YouTube watch-page player (0.5 s) → the camera dives 2× to
 * the description link (0.6 s) → holds 1.7 s → reverses: back to the player (0.6 s), holds 0.5 s,
 * scales back up to the full-frame face (0.5 s). Every CTA in a video is identical (long-form.md).
 * Core law 7: this is the one long-form graphic that transforms the footage instead of cutting.
 * Core law 9: the watch page is a REAL screenshot (the brand's own channel page, recorded in
 * assets/captures/MANIFEST.md) — the kit never draws or restyles platform UI.
 * The camera is a DOM camera (HFCamera.rig without a blur canvas): live footage cannot be baked into
 * a blur texture yet, and long-form ordinary legs read as no blur.
 * Both grounds look the same (no glow to drop); data-hf-mode is still required.
 *
 *   HFKit.ctaYoutube(tl, host, { format: "long-form", at: 0, footage: videoEl,
 *     page: { src: "assets/captures/watch-page.png", width: 2560, height: 1440,
 *             player: [x, y, w, h], link: [x, y, w, h] } })          // rects in page pixels
 *   -> { dur, poses: { face, player, link } }  */
(function (root) {
  "use strict";
  var NODE = typeof module !== "undefined" && module.exports;
  var K = NODE ? require("./kit.js") : root.HFKit;
  var P = NODE ? require("../profile.js") : root.HFProfile;
  var C = NODE ? require("../camera.js") : root.HFCamera;
  var X = NODE ? require("../text.js") : root.HFText;

  var PLAYER_HOLD = 0.5;   // hold at 0.80 before the dive and after the return (measured 0.5 s)

  function rect(r, name) {
    if (!Array.isArray(r) || r.length !== 4 || !r.every(function (v) { return typeof v === "number" && isFinite(v); }) || !(r[2] > 0 && r[3] > 0)) {
      throw new Error("HFKit.ctaYoutube: page." + name + " must be [x, y, w, h] in page pixels");
    }
    return { x: r[0], y: r[1], w: r[2], h: r[3] };
  }

  // The four camera poses, in page pixels. Pure: tests and later CTAs reuse it.
  function poses(page, frame, c) {
    var pl = rect(page.player, "player"), ln = rect(page.link, "link");
    var zFace = Math.max(frame.width / pl.w, frame.height / pl.h);
    var face = { cx: pl.x + pl.w / 2, cy: pl.y + pl.h / 2, z: zFace };
    var player = { cx: face.cx, cy: face.cy, z: zFace * c.scale };
    var link = { cx: ln.x + ln.w / 2, cy: ln.y + ln.h / 2, z: player.z * c.dive };
    return { face: face, player: player, link: link };
  }

  function watchPageDive(tl, host, opts) {
    var b = K.begin("cta-youtube", host, opts), T = b.at, c = P.timing(b.lf.format).cta;
    var page = opts.page || {};
    if (typeof page.src !== "string" || !(page.width > 0 && page.height > 0)) throw new Error("HFKit.ctaYoutube: page needs src, width and height (a real watch-page screenshot)");
    if (!opts.footage || typeof opts.footage.appendChild !== "function") throw new Error("HFKit.ctaYoutube: opts.footage must be the face <video> (or a still) element");
    var p = poses(page, K.FRAME, c), pl = rect(page.player, "player");
    var stage = K.el("div", "hf-kit-cta-stage", host);
    stage.style.width = page.width + "px"; stage.style.height = page.height + "px";
    stage.setAttribute("data-layout-allow-overflow", "");   // the page is larger than the frame on purpose
    var img = K.el("img", "hf-kit-cta-page", stage);
    img.setAttribute("src", page.src); img.setAttribute("alt", "");
    img.style.width = page.width + "px"; img.style.height = page.height + "px";
    var slot = K.el("div", "hf-kit-cta-player", stage);
    slot.style.left = pl.x + "px"; slot.style.top = pl.y + "px"; slot.style.width = pl.w + "px"; slot.style.height = pl.h + "px";
    slot.appendChild(opts.footage);
    opts.footage.classList.add("hf-kit-cta-footage");
    [img, slot].forEach(function (e) { e.setAttribute("data-layout-allow-overlap", ""); e.setAttribute("data-layout-allow-occlusion", ""); });
    if (typeof img.decode === "function") X.track(img.decode());
    var t1 = c.scaleDur, t2 = t1 + PLAYER_HOLD, t3 = t2 + c.diveDur, t4 = t3 + c.hold, t5 = t4 + c.diveDur, t6 = t5 + PLAYER_HOLD, t7 = t6 + c.scaleDur;
    function key(t, q) { return { t: t, cx: q.cx, cy: q.cy, z: q.z }; }
    C.rig(tl, { format: b.lf.format, width: K.FRAME.width, height: K.FRAME.height, stage: stage, at: T, dur: t7,
      keys: [key(0, p.face), key(t1, p.player), key(t2, p.player), key(t3, p.link), key(t4, p.link), key(t5, p.player), key(t6, p.player), key(t7, p.face)] });
    return { dur: t7, poses: p };
  }

  K.register("cta-youtube", "watch-page-dive", watchPageDive, [
    ".hf-kit-cta-stage{position:absolute;left:0;top:0}",
    ".hf-kit-cta-page{position:absolute;left:0;top:0;display:block}",
    ".hf-kit-cta-player{position:absolute;overflow:hidden}",
    ".hf-kit-cta-footage{position:absolute;left:0;top:0;width:100%;height:100%;object-fit:cover}"
  ].join("\n"));
  K.ctaPoses = poses;
})(typeof window !== "undefined" ? window : this);
````

List it in the manifest (the hygiene test requires `lib/` to hold exactly the manifest modules):

````bash
python3 - . cta-youtube <<'PY'
# List one kit component in lib/manifest.json: modules sorted; loadOrder right after the last kit/ entry.
import json
import sys
from pathlib import Path
ROOT, name = Path(sys.argv[1]), sys.argv[2]
m = ROOT / "lib" / "manifest.json"
data = json.loads(m.read_text())
rel = f"kit/{name}.js"
if rel in data["modules"]:
    sys.exit(f"{rel} is already listed")
data["modules"] = sorted(data["modules"] + [rel])
last = max(i for i, x in enumerate(data["loadOrder"]) if x.startswith("kit/"))
data["loadOrder"].insert(last + 1, rel)
m.write_text(json.dumps(data, indent=2) + "\n")
print(f"listed {rel}")
PY
````

- [ ] **Step 4: Run the tests**

Run: `node --test lib/test/*.test.js tools/*.test.js`
Expected: `# pass 141` `# fail 0` (`kit.test.js` now also checks that `cta-youtube` registers the variant `tokens.json` names; `hygiene.test.js` scans `lib/kit/cta-youtube.js`).

- [ ] **Step 5: Render and compare with the template still**

`STILLS` below is the folder holding Tymek's template stills (`1.png` … `7.webp`); if you do not have them, compare against the acceptance numbers alone.

````bash
python3 tools/kit_preview.py cta-youtube --palette gold --slug cta-gold
npx hyperframes snapshot renders/kit-preview/cta-gold --at 0.3,1.2,2.5,5.3 --no-end -o renders/kit/cta-gold
````
The preview uses a synthetic page (dark ground, grey player, blue link bar) and a flat face clip; for the comparison view the reference strip (HrYMfy6MZtA 116.2–121.8 s).
Acceptance (view every frame named above; fix and re-run `python3 tools/sync_lib.py <project>` + the render until all hold):
- 0.3 s: the face is shrinking into the player (≈ 0.85–0.9 of the frame), page dark around it.
- 1.2 s: player at 0.80 of the frame width (1536 px of the 1920 frame — the 1600 px player × 0.96 zoom), the page visible around it.
- 2.5 s: the blue link bar fills ≈ 55 % of the frame width, centred (560 px × 1.92); the camera is holding.
- 5.3 s: the face fills the frame again exactly as at 0 s (the scene ends on the footage).

- [ ] **Step 6: Commit**

````bash
git add lib/kit/cta-youtube.js lib/test/kit-cta-youtube.test.js lib/manifest.json
git commit -m "feat(kit): HFKit.ctaYoutube — variant `watch-page-dive`" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
````

---

### Task 12: `HFKit.roadmap` — variant `wave-nodes`

**Files:**
- Create: `lib/kit/roadmap.js`, `lib/test/kit-roadmap.test.js`
- Modify: `lib/manifest.json`

**Interfaces:**
- Consumes: `HFKit.register / begin / ground / el / svg / cardIn / slideIn / fadeOut / pop / FRAME / GLOW` (Task 5), `HFText.words / splitWords / glowTitle / defocus / track` (Task 2), `HFMarks.draw / highlight / statusChip / scriptWord / scribblePath / sweepDuration`, `HFCamera.rig / domTransform`, `HFProfile.timing / ease`; the contract in `lib/test/kit-contract.js`.
- Produces: `HFKit.roadmap(tl, host, {format: "long-form", at, title, steps: [{label, icon?}] (3–6), visit}) -> {dur, pose, nodes: [el], cards: [el]}` — full-frame, one world built identically by every visit: nodes every 640 px from x 320 at y 700 / 520 alternating (world width `max(1920, 640 + 640·(n−1))`), a Catmull-Rom path from x −60 to width + 60 through them (`accent.line`; dark: glow filter tagged `glow`), the system name (92 px caps, 1300 px column, top 150), 250 × 290 cards centred on their nodes with the node at 40 % of the card height, icons `bulb` `sliders` `chart` `target` (24 × 24 strokes). `visit 0`: title word by word at `at`, path draws 1.2 s on `ease.sweep` from `at + 0.3`, each node pops (`HFKit.pop`) when the drawing line reaches its x (`ease.sweep` inverted by bisection), cards hidden, camera on the whole world. `visit k ≥ 1`: title, path, nodes and cards 1…k−1 static; card k docks (`HFKit.cardIn`) at `at`; camera from `pose(k−1)` to `pose(k)` (centre node k, y + 40, z 1.25) in 1.6 s `ease.camera`. `HFKit.roadmapGeometry(n)`, `HFKit.roadmapPose(geo, k)` (pure). Throws `HFKit.roadmap: 3–6 steps, got <n>`, `… visit must be 0 (intro) … <n>, got <v>`, `… step <i> has no label`, `… step <i> icon "<x>" (have: bulb, sliders, chart, target)`, `… opts.title is required`.

- [ ] **Step 1: Write the failing test**

Create `lib/test/kit-roadmap.test.js`:

````javascript
"use strict";
var test = require("node:test");
var assert = require("node:assert/strict");
var h = require("./helpers.js");
var P = require("../profile.js");
var c = require("./kit-contract.js");
var K = require("../kit/kit.js");
require("../kit/roadmap.js");

var STEPS = [{ label: "Predictive Idea Selection", icon: "bulb" }, { label: "Retention Based Editing", icon: "sliders" }, { label: "Qualified Sales Calls", icon: "target" }];
function build(tl, host, extra) {
  return K.roadmap(tl, host, Object.assign({ format: "long-form", at: 0.2, visit: 1, title: "Printing Prediction System", steps: STEPS }, extra));
}
c.contract("roadmap", build);
c.contract("roadmap intro", function (tl, host, extra) { return build(tl, host, Object.assign({ visit: 0 }, extra)); });

test("roadmap geometry: nodes every 640 px alternating low/high, world widens past 3 steps", function () {
  var g3 = K.roadmapGeometry(3), g5 = K.roadmapGeometry(5);
  assert.deepEqual(g3.nodes, [{ x: 320, y: 700 }, { x: 960, y: 520 }, { x: 1600, y: 700 }]);
  assert.equal(g3.width, 1920);
  assert.equal(g5.width, 3200);
  assert.equal(g3.d, K.roadmapGeometry(3).d, "pure");
  assert.match(g3.d, /^M-60 610 C/);
});

test("roadmap intro: path draws on ease.sweep, each node pops when the line reaches it", function () {
  c.fresh();
  var tl = h.fakeTimeline(), host = h.kitHost("dark"), r = build(tl, host, { visit: 0 });
  var draw = tl.eased().filter(function (tw) { return tw.ease.token === "ease.sweep"; })[0];
  assert.equal(draw.at, 0.5); assert.equal(draw.dur, 1.2);
  var e = P.ease("long-form", "ease.sweep");
  var pops = r.nodes.map(function (n) { return tl.eased().filter(function (tw) { return tw.target === n; })[0]; });
  pops.forEach(function (tw, i) {
    var f = K.roadmapGeometry(3).nodes[i].x / 1920;
    assert.ok(Math.abs(e((tw.at - draw.at) / draw.dur) - f) < 1e-5, "node " + (i + 1) + " pops as the line reaches it");
    assert.equal(tw.dur, P.timing("long-form").node.dur);
  });
  r.cards.forEach(function (card) { assert.equal(card.style.visibility, "hidden"); });
  assert.equal(r.pose.z, 1);
});

test("roadmap visit k opens exactly where visit k-1 ended (camera + docked cards)", function () {
  c.fresh();
  var prev = build(h.fakeTimeline(), h.kitHost("dark"), { visit: 1 });
  c.fresh();
  var tl = h.fakeTimeline(), host = h.kitHost("dark"), r = build(tl, host, { visit: 2 });
  var stage = h.descendants(host).filter(function (e) { return e.className === "hf-kit-rm-stage"; })[0];
  tl.seek(0);
  var d0 = require("../camera.js").domTransform(prev.pose, 1920, 1080);
  assert.equal(stage.style.transform, "translate(" + d0.dx.toFixed(2) + "px," + d0.dy.toFixed(2) + "px) scale(" + d0.z.toFixed(4) + ")");
  assert.deepEqual(r.cards.map(function (e) { return e.style.visibility || "visible"; }), ["visible", "visible", "hidden"]);
  assert.equal(tl.eased()[0].target, r.cards[1], "card 2 docks");
  assert.equal(tl.eased()[0].ease.token, "ease.card");
  assert.deepEqual(h.seekOrderInvariant(tl, [0, 0.2, 0.6, 1.0, 1.4, 1.8, 3], [stage]), []);
});

test("roadmap: 3–6 steps, visit within range, known icons, a title", function () {
  c.fresh();
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { steps: STEPS.slice(0, 2) }); }, /3–6 steps, got 2/);
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { visit: 4 }); }, /visit must be 0 \(intro\) … 3, got 4/);
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { steps: [{ label: "a", icon: "rocket" }, STEPS[1], STEPS[2]] }); }, /icon "rocket" \(have: bulb, sliders, chart, target\)/);
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { title: "" }); }, /opts\.title is required/);
});
````

- [ ] **Step 2: Run it to make sure it fails**

Run: `node --test lib/test/kit-roadmap.test.js`
Expected: FAIL — `Cannot find module '../kit/roadmap.js'`.

- [ ] **Step 3: Implement**

Create `lib/kit/roadmap.js`:

````javascript
/* HFKit.roadmap — variant "wave-nodes" (the chapter roadmap device, reference video ≈ 60/127/234 s).
 * The system name above a glowing wavy path with numbered nodes; at each chapter the edit cuts back
 * to it, the next step card docks onto its node and the camera continues from its last pose.
 * One world, built identically by every visit, so visit k opens exactly where visit k-1 ended:
 *   visit 0 — intro: the title builds word by word, the path draws (1.2 s ease.sweep), each node pops
 *             (0.48 s ease.enter) as the line passes it; camera holds on the whole world.
 *   visit k — opens on visit k-1's end state (title, path, nodes, cards 1…k-1, camera on card k-1),
 *             card k docks (card entrance) and the camera travels to card k (1.6 s ease.camera).
 * Dark ground: path in accent.line with a glow filter (data-blur-reason="glow"), maroon-tinted dark
 * glass cards. Light ground: path in accent.line without bloom, frosted white cards, dark text.
 *
 *   HFKit.roadmap(tl, host, { format: "long-form", at: 0.2, visit: 1, title: "Printing Prediction System",
 *     steps: [{ label: "Predictive Idea Selection", icon: "bulb" }, { label: "Retention Based Editing", icon: "sliders" }, …] })
 *   -> { dur, pose: {cx, cy, z} (the camera's final pose), nodes: [el…], cards: [el…] }
 * Steps 3–6; nodes every 640 px (world 1920 px wide for 3 steps, wider beyond). */
(function (root) {
  "use strict";
  var NODE = typeof module !== "undefined" && module.exports;
  var K = NODE ? require("./kit.js") : root.HFKit;
  var P = NODE ? require("../profile.js") : root.HFProfile;
  var X = NODE ? require("../text.js") : root.HFText;
  var M = NODE ? require("../marks.js") : root.HFMarks;
  var C = NODE ? require("../camera.js") : root.HFCamera;

  var SPACING = 640, X0 = 320, Y_LOW = 700, Y_HIGH = 520, Y_MID = 610, CARD_W = 250, CARD_H = 290, NODE_D = 46;
  var TITLE_W = 1300, DRAW_DUR = 1.2, DRAW_LEAD = 0.3, LEG = 1.6, ZOOM = 1.25, MIN_STEPS = 3, MAX_STEPS = 6;
  // 24 × 24 stroke icons (currentColor). Unknown names throw; pass none for a number-only card.
  var ICONS = {
    bulb: "M9 18h6M10 21h4M12 3a6 6 0 0 0-4 10.5c.8.8 1 1.5 1 2.5h6c0-1 .2-1.7 1-2.5A6 6 0 0 0 12 3z",
    sliders: "M4 6h9M17 6h3M4 12h3M11 12h9M4 18h11M19 18h1M15 4v4M9 10v4M17 16v4",
    chart: "M4 20V11M10 20V5M16 20v-6M2 20h20",
    target: "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18zM12 8a4 4 0 1 0 0 8a4 4 0 1 0 0-8z"
  };

  // World geometry: pure function of the step count.
  function geometry(n) {
    var nodes = [];
    for (var i = 0; i < n; i++) nodes.push({ x: X0 + i * SPACING, y: i % 2 === 0 ? Y_LOW : Y_HIGH });
    var width = Math.max(K.FRAME.width, 2 * X0 + (n - 1) * SPACING);
    var pts = [{ x: -60, y: Y_MID }].concat(nodes, [{ x: width + 60, y: Y_MID }]);
    var d = "M" + pts[0].x + " " + pts[0].y;
    for (var j = 0; j < pts.length - 1; j++) {   // Catmull-Rom through every point -> cubic Béziers
      var p0 = pts[Math.max(0, j - 1)], p1 = pts[j], p2 = pts[j + 1], p3 = pts[Math.min(pts.length - 1, j + 2)];
      d += " C" + (p1.x + (p2.x - p0.x) / 6).toFixed(1) + " " + (p1.y + (p2.y - p0.y) / 6).toFixed(1) + " " +
        (p2.x - (p3.x - p1.x) / 6).toFixed(1) + " " + (p2.y - (p3.y - p1.y) / 6).toFixed(1) + " " + p2.x + " " + p2.y;
    }
    return { nodes: nodes, width: width, height: K.FRAME.height, d: d };
  }
  // Camera pose for visit k: 0 = the whole world; k ≥ 1 = card k, framed at 1.25×.
  function pose(geo, k) {
    if (k === 0) return { cx: geo.width / 2, cy: geo.height / 2, z: K.FRAME.width / geo.width };
    var nd = geo.nodes[k - 1];
    return { cx: nd.x, cy: nd.y + 40, z: ZOOM };
  }
  // When the drawing path reaches world x (fraction f of its width): invert ease.sweep by bisection.
  function reach(f, format) {
    var e = P.ease(format, "ease.sweep"), lo = 0, hi = 1;
    for (var i = 0; i < 24; i++) { var m = (lo + hi) / 2; if (e(m) < f) lo = m; else hi = m; }
    return (lo + hi) / 2 * DRAW_DUR;
  }

  function waveNodes(tl, host, opts) {
    var b = K.begin("roadmap", host, opts), T = b.at, fmt = b.lf.format;
    var steps = opts.steps || [], n = steps.length, visit = opts.visit == null ? 0 : opts.visit;
    if (n < MIN_STEPS || n > MAX_STEPS) throw new Error("HFKit.roadmap: " + MIN_STEPS + "–" + MAX_STEPS + " steps, got " + n);
    if (!(visit === Math.floor(visit) && visit >= 0 && visit <= n)) throw new Error("HFKit.roadmap: visit must be 0 (intro) … " + n + ", got " + visit);
    if (typeof opts.title !== "string" || !opts.title.trim()) throw new Error("HFKit.roadmap: opts.title is required");
    steps.forEach(function (s, i) {
      if (!s || typeof s.label !== "string" || !s.label.trim()) throw new Error("HFKit.roadmap: step " + (i + 1) + " has no label");
      if (s.icon != null && !ICONS[s.icon]) throw new Error("HFKit.roadmap: step " + (i + 1) + " icon " + JSON.stringify(s.icon) + " (have: " + Object.keys(ICONS).join(", ") + ")");
    });
    var geo = geometry(n);
    K.ground(host, {});
    var stage = K.el("div", "hf-kit-rm-stage", host);
    stage.style.width = geo.width + "px"; stage.style.height = geo.height + "px";
    stage.setAttribute("data-layout-allow-overflow", "");   // the camera moves the world past the frame on purpose
    var title = K.el("div", "hf-kit-headline hf-kit-rm-title", stage, opts.title.trim().replace(/\s+/g, " "));
    title.style.left = (geo.width - TITLE_W) / 2 + "px";
    var art = K.svg("svg", { "class": "hf-kit-rm-path", width: String(geo.width), height: String(geo.height), viewBox: "0 0 " + geo.width + " " + geo.height }, stage);
    var path = K.svg("path", { d: geo.d }, art);
    if (b.mode === "dark") {
      var gid = X.injectGlow({ intensity: 1.1, levels: [3, 8, 18] });
      path.setAttribute("data-blur-reason", "glow");
      path.style.filter = "url(#" + gid + ")";
    }
    var cards = steps.map(function (s, i) {
      var nd = geo.nodes[i], card = K.el("div", "hf-kit-glass hf-kit-rm-card", stage);
      card.style.left = (nd.x - CARD_W / 2) + "px"; card.style.top = (nd.y - CARD_H * 0.4) + "px";
      if (s.icon) {
        var ic = K.svg("svg", { "class": "hf-kit-rm-icon", viewBox: "0 0 24 24" }, card);
        K.svg("path", { d: ICONS[s.icon] }, ic);
      }
      K.el("div", "hf-kit-body hf-kit-rm-label", card, s.label.trim());
      return card;
    });
    var nodes = geo.nodes.map(function (nd, i) {
      var e = K.el("div", "hf-kit-rm-node", stage, String(i + 1));
      e.style.left = (nd.x - NODE_D / 2) + "px"; e.style.top = (nd.y - NODE_D / 2) + "px";
      return e;
    });
    var dur, keys;
    if (visit === 0) {
      cards.forEach(function (c) { c.style.visibility = "hidden"; });
      var wd = X.words(tl, title, T, b.lf), dT = T + DRAW_LEAD;
      M.draw(tl, path, dT, DRAW_DUR, b.lf);
      var last = 0;
      nodes.forEach(function (e, i) {
        var at = dT + reach(geo.nodes[i].x / geo.width, fmt);
        last = Math.max(last, at - T + K.pop(tl, e, at));
      });
      dur = Math.max(wd, DRAW_LEAD + DRAW_DUR, last);
      keys = [{ t: 0, cx: pose(geo, 0).cx, cy: pose(geo, 0).cy, z: pose(geo, 0).z }];
    } else {
      cards.forEach(function (c, i) { if (i >= visit) c.style.visibility = "hidden"; });
      var cd = K.cardIn(tl, cards[visit - 1], T), a = pose(geo, visit - 1), z = pose(geo, visit);
      dur = Math.max(cd, LEG);
      keys = [{ t: 0, cx: a.cx, cy: a.cy, z: a.z }, { t: T, cx: a.cx, cy: a.cy, z: a.z }, { t: T + LEG, cx: z.cx, cy: z.cy, z: z.z }];
    }
    C.rig(tl, { format: fmt, width: K.FRAME.width, height: K.FRAME.height, stage: stage, keys: keys, dur: T + dur });
    return { dur: dur, pose: pose(geo, visit), nodes: nodes, cards: cards };
  }

  K.register("roadmap", "wave-nodes", waveNodes, [
    ".hf-kit-rm-stage{position:absolute;left:0;top:0}",
    ".hf-kit-rm-title{position:absolute;width:" + TITLE_W + "px;top:150px;text-align:center;font-size:92px;line-height:1.15;letter-spacing:0.04em;text-transform:uppercase;white-space:normal}",
    ".hf-kit-rm-path{position:absolute;left:0;top:0;overflow:visible}",
    ".hf-kit-rm-path path{fill:none;stroke:var(--hf-accent-line);stroke-width:5;stroke-linecap:round}",
    ".hf-kit-rm-card{width:" + CARD_W + "px;height:" + CARD_H + "px;overflow:hidden;text-align:center}",
    ".hf-kit-dark .hf-kit-rm-card{border-top-color:var(--hf-accent-line)}",
    ".hf-kit-dark .hf-kit-rm-card::before{content:\"\";position:absolute;inset:0;background:linear-gradient(180deg,var(--hf-accent-block) 0%,transparent 75%);opacity:.22}",
    ".hf-kit-rm-icon{position:absolute;left:" + (CARD_W / 2 - 26) + "px;top:30px;width:52px;height:52px;fill:none;stroke:var(--hf-text-primary);stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round}",
    ".hf-kit-rm-label{position:absolute;left:16px;right:16px;top:" + (CARD_H * 0.4 + NODE_D / 2 + 22) + "px;font-size:28px;line-height:1.25}",
    ".hf-kit-rm-node{position:absolute;width:" + NODE_D + "px;height:" + NODE_D + "px;border-radius:50%;background:var(--hf-text-primary);color:var(--hf-ground-deep);" +
      "font-family:var(--hf-font-headline);font-weight:var(--hf-font-headline-weight);font-size:26px;line-height:" + NODE_D + "px;text-align:center}"
  ].join("\n"));
  K.roadmapGeometry = geometry;
  K.roadmapPose = pose;
})(typeof window !== "undefined" ? window : this);
````

List it in the manifest (the hygiene test requires `lib/` to hold exactly the manifest modules):

````bash
python3 - . roadmap <<'PY'
# List one kit component in lib/manifest.json: modules sorted; loadOrder right after the last kit/ entry.
import json
import sys
from pathlib import Path
ROOT, name = Path(sys.argv[1]), sys.argv[2]
m = ROOT / "lib" / "manifest.json"
data = json.loads(m.read_text())
rel = f"kit/{name}.js"
if rel in data["modules"]:
    sys.exit(f"{rel} is already listed")
data["modules"] = sorted(data["modules"] + [rel])
last = max(i for i, x in enumerate(data["loadOrder"]) if x.startswith("kit/"))
data["loadOrder"].insert(last + 1, rel)
m.write_text(json.dumps(data, indent=2) + "\n")
print(f"listed {rel}")
PY
````

- [ ] **Step 4: Run the tests**

Run: `node --test lib/test/*.test.js tools/*.test.js`
Expected: `# pass 153` `# fail 0` (`kit.test.js` now also checks that `roadmap` registers the variant `tokens.json` names; `hygiene.test.js` scans `lib/kit/roadmap.js`).

- [ ] **Step 5: Render and compare with the template still**

`STILLS` below is the folder holding Tymek's template stills (`1.png` … `7.webp`); if you do not have them, compare against the acceptance numbers alone.

````bash
python3 tools/kit_preview.py roadmap --palette red --slug roadmap-red
npx hyperframes snapshot renders/kit-preview/roadmap-red --at 1.2,3.6,4.1,6.8 --no-end -o renders/kit/roadmap-red
python3 tools/kit_preview.py roadmap --palette silver --slug roadmap-silver
npx hyperframes snapshot renders/kit-preview/roadmap-silver --at 3.6,6.8 --no-end -o renders/kit/roadmap-silver
````
Compare with the reference strips (HrYMfy6MZtA 59.5–68 s intro, 126.7–131.9 s step 1).
Acceptance (view every frame named above; fix and re-run `python3 tools/sync_lib.py <project>` + the render until all hold):
- 1.2 s (intro): title words arriving; the path drawn about half-way from the left; node 1 popped, node 2 popping or not yet.
- 3.6 s: the system name in two lines of caps centred in the top third (≈ y 150–380); one glowing wavy line from the left edge to the right edge through nodes at x 320 / 960 / 1600, y 700 / 520 / 700; nodes ≈ 46 px light discs with dark numerals (reference: small white circles).
- 4.1 s (visit 1 just started): the same world, same framing as 3.6 s; card 1 rising from below onto node 1.
- 6.8 s: camera at 1.25× on card 1 (centred), card 1 docked with node 1 at 40 % of its height, icon above, label below; maroon-tinted dark glass in `red` (reference: dark-maroon glassy card).
- Silver (light): no glow on the path, frosted white cards, dark title and labels.

- [ ] **Step 6: Commit**

````bash
git add lib/kit/roadmap.js lib/test/kit-roadmap.test.js lib/manifest.json
git commit -m "feat(kit): HFKit.roadmap — variant `wave-nodes`" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
````

---

### Task 13: Every kit component through the QA gate (`tools/test_kit_qa.py`, fake CLI + one live run)

**Files:**
- Create: `tools/test_kit_qa.py`

**Interfaces:**
- Consumes: `kit_preview.build(videos_dir=…) -> (project, looks)` (Task 6) with all six components (Tasks 7–12); `qa.run_gate(project, render=None, edit=None, probe_url=None, skip_render=False, probe=None, …) -> report`, `qa.overlay_files(project)`, `qa.format_report(report)`; `test_qa.FAKE_HF` (the fake HyperFrames CLI: `check` passes, `render` copies `$FAKE_HF_RENDER_SRC`, `render -c` copies `$FAKE_HF_OVERLAY_SRC`); `project.root_attrs`; `synth._ffmpeg`.
- Produces: `test_kit_qa.clean_probe(project, fmt)` — a fake runtime probe covering the reel and every overlay with no findings. The live test (`HF_LIVE=1`) is the documented end-to-end proof.

- [ ] **Step 1: Write the test**

Create `tools/test_kit_qa.py`:

````python
"""Every kit component in one long-form project (tools/kit_preview.py), through the QA gate.

Unit run (fast): the HyperFrames CLI is a fake (check passes, renders copy a still clip) and the runtime probe
is a fake; checks 2, 3, 4–7 (static scan), 8 and 9's plan cross-check run for real on the kit's scenes.
Live run (network, ≈ 2 min): HF_LIVE=1 python3 -m unittest discover -s tools -p 'test_kit_qa.py' -v — the real
gate: `npx hyperframes check | preview | render`, the Chrome runtime probe, overlay renders.
"""
import os
import shlex
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import kit_preview
import project as pj
import qa
import synth
import test_qa as tq


def clean_probe(project, fmt):
    """A fake runtime probe: the reel and every overlay probed, no findings."""
    return {"timelines": 5, "tweens": 60, "samples": 40, "findings": [], "errors": [],
            "overlays": [{"file": rel, "samples": 30, "findings": [], "errors": []} for rel in qa.overlay_files(project)]}


@unittest.skipUnless(synth.HAVE_FFMPEG and shutil.which("node"), "needs ffmpeg and node")
class KitGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = {k: os.environ.get(k) for k in ("HF_CLI", "FAKE_HF_CHECK", "FAKE_HF_RENDER_SRC", "FAKE_HF_OVERLAY_SRC")}
        self.p, _ = kit_preview.build(videos_dir=Path(self.tmp.name))

    def tearDown(self):
        for k, v in self.env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self.tmp.cleanup()

    def fake_cli(self):
        d = Path(self.tmp.name)
        (d / "fake_hf.py").write_text(tq.FAKE_HF)
        total = float(pj.root_attrs(self.p)["data-duration"])
        reel, overlay = d / "reel.mp4", d / "overlay.mp4"
        synth._ffmpeg(["-f", "lavfi", "-i", f"color=c=0x101418:s=1920x1080:r=30:d={total:g}", "-pix_fmt", "yuv420p", str(reel)])
        synth._ffmpeg(["-f", "lavfi", "-i", "color=c=0x101418:s=1920x1080:r=30:d=5", "-pix_fmt", "yuv420p", str(overlay)])
        os.environ.update(HF_CLI=f"{shlex.quote(sys.executable)} {shlex.quote(str(d / 'fake_hf.py'))}", FAKE_HF_CHECK="0",
                          FAKE_HF_RENDER_SRC=str(reel), FAKE_HF_OVERLAY_SRC=str(overlay))

    def test_every_kit_component_passes_the_gate(self):
        self.fake_cli()
        r = qa.run_gate(self.p, probe=clean_probe)
        self.assertEqual({c["n"]: c["status"] for c in r["checks"]}, {n: "PASS" for n in range(1, 11)}, qa.format_report(r))
        self.assertEqual(r["probe"]["overlays"], {"compositions/overlays/lower-third.html": 30, "compositions/overlays/side-text.html": 30})

    def test_a_kit_scene_named_caption_fails_check_7(self):
        self.fake_cli()
        f = self.p / "compositions" / "01-title.html"
        f.write_text(f.read_text().replace('<div class="kit-host"></div>', '<div class="kit-host captions"></div>'))
        c7 = qa.run_gate(self.p, probe=clean_probe)["checks"][6]
        self.assertEqual(c7["status"], "FAIL")
        self.assertIn("compositions/01-title.html", c7["findings"][0])

    @unittest.skipUnless(os.environ.get("HF_LIVE") == "1", "live HyperFrames run: set HF_LIVE=1 (network, ≈ 2 min)")
    def test_live_gate(self):
        r = qa.run_gate(self.p)
        self.assertTrue(r["ok"], qa.format_report(r))


if __name__ == "__main__":
    unittest.main()
````

- [ ] **Step 2: Run it**

Run: `python3 -m unittest discover -s tools -p 'test_kit_qa.py' -v`
Expected: `Ran 3 tests … OK (skipped=1)` (≈ 5 s): with the CLI and the probe faked, checks 2 (the project's `lib/kit/*` equal root `lib/`), 3, 4–7 (static scan of the kit scenes and overlays), 8 and 9's slot/grid cross-check run for real.

- [ ] **Step 3: The live run (network, ≈ 2 min — do it once, paste the tail into the task report)**

Run: `HF_LIVE=1 python3 -m unittest discover -s tools -p 'test_kit_qa.py' -k live -v`
Expected: `test_live_gate … ok`, `Ran 1 test in ~105 s`, `OK`. (Prototype: real `npx hyperframes check` (0 errors), preview + Chrome probe of the reel and both overlays, draft render of the reel and of each overlay, all ten checks PASS.) The same gate by hand on a preview project:

````bash
python3 tools/kit_preview.py --palette gold --slug gate-gold
python3 tools/qa.py renders/kit-preview/gate-gold
````
Expected: ten `PASS` lines, `runtime probe: <n> samples (index.html); compositions/overlays/lower-third.html: <n> samples; compositions/overlays/side-text.html: <n> samples`, `RESULT: PASS`. Repeat with `--palette silver --slug gate-silver` (light ground): `RESULT: PASS`.

- [ ] **Step 4: Commit**

````bash
git add tools/test_kit_qa.py
git commit -m "test(kit): every kit component through the QA gate (fake CLI; HF_LIVE=1 for the real gate)" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
````

---

### Task 14: Brand proof sheet — `tools/proof_sheet.py`

**Files:**
- Create: `tools/proof_sheet.py`, `tools/test_proof_sheet.py`

**Interfaces:**
- Consumes: `brandcheck.load_brand(dir) -> {"tokens", "palettes": {name: palette}}` (raises `BrandError`), `new_video.scaffold(…)`, `node lib/brand.js <brand> --palette p --font f --json` (palette → CSS variables), the kit (Tasks 5–10).
- Produces:
  - `proof_sheet.build(brand, videos_dir=None, slug=None, font=None, root=ROOT) -> Path` — scaffolds `videos/<slug or proof-<brand>>/` (long-form, BRIEF palette = the brand default) and writes one scene per palette in `tokens.json` order (`compositions/proof-<palette>.html`, 4.5 s each): a 2 × 2 grid of half-scale 1920×1080 frames — `HFKit.title` (q1), `HFKit.subtitle` (q2), `HFKit.lowerThird` (q3) and `HFKit.sideText` (q4) over a neutral footage stand-in — inside a `.proof-scene` wrapper that carries the palette's CSS variables inline and its `data-hf-mode`; a label pill `<palette> · <mode>` (class `proof-label`, never "caption"). Also BRIEF film/direction, one full-frame beat-grid row per palette, a transcript spanning the reel. `ValueError` for an unknown brand (named by `brandcheck`) or an existing project (named by `new_video`).
  - `proof_sheet.SCENE_DUR` = 4.5; CLI `python3 tools/proof_sheet.py <brand> [--videos-dir d] [--slug s] [--font f]` prints the gate, render and stills commands (stills at each scene's last 0.2 s).

- [ ] **Step 1: Write the failing test**

Create `tools/test_proof_sheet.py`:

````python
import html
import io
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import brandcheck
import project as pj
import proof_sheet as ps
import qa
import synth
import test_qa as tq

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class ProofSheetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.videos = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_one_scene_per_palette_in_brand_order(self):
        p = ps.build("contentporary", videos_dir=self.videos)
        self.assertEqual(p.name, "proof-contentporary")
        names = brandcheck.load_brand(ROOT / "brands" / "contentporary")["tokens"]["palettes"]
        slots = pj.composition_slots(p)
        self.assertEqual([s["id"] for s in slots], ["proof-" + n for n in names])
        self.assertEqual([s["start"] for s in slots], [i * ps.SCENE_DUR for i in range(len(names))])
        self.assertEqual(pj.root_attrs(p)["data-duration"], f"{len(names) * ps.SCENE_DUR:g}")
        self.assertEqual(len(pj.read_storyboard(p)), len(names))
        self.assertEqual(pj.validate_brief(pj.read_brief(p)), [])

    def test_each_scene_carries_its_palette_and_mode(self):
        p = ps.build("contentporary", videos_dir=self.videos)
        palettes = brandcheck.load_brand(ROOT / "brands" / "contentporary")["palettes"]
        for name in ("gold", "silver", "paper"):
            text = (p / "compositions" / f"proof-{name}.html").read_text()
            self.assertIn(f'class="proof-scene" data-hf-mode="{palettes[name]["mode"]}"', text)
            want = json.loads(subprocess.run(["node", str(ROOT / "lib" / "brand.js"), str(ROOT / "brands" / "contentporary"),
                                              "--palette", name, "--json"], capture_output=True, text=True).stdout)
            style = html.unescape(re.search(r'class="proof-scene"[^>]*style="([^"]*)"', text).group(1))
            got = dict(kv.split(": ", 1) for kv in style.split("; "))
            self.assertEqual(got, want)
            for call in ("HFKit.title(", "HFKit.subtitle(", "HFKit.lowerThird(", "HFKit.sideText("):
                self.assertIn(call, text)
            self.assertNotRegex(text, r"""(?:id|class)\s*=\s*["'][^"']*caption""", "QA check 7 must not see a caption layer")
            self.assertNotIn("hf-placeholder", text)

    def test_refuses_unknown_brand_and_existing_project(self):
        with self.assertRaisesRegex(ValueError, "ghost not found"):
            ps.build("ghost", videos_dir=self.videos)
        ps.build("contentporary", videos_dir=self.videos)
        with self.assertRaisesRegex(ValueError, "already exists"):
            ps.build("contentporary", videos_dir=self.videos)

    def test_cli_prints_the_next_commands(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(ps.main(["proof_sheet.py", "contentporary", "--videos-dir", str(self.videos)]), 0)
        text = out.getvalue()
        self.assertIn("7 palettes, 31.5 s", text)
        self.assertIn("python3 tools/qa.py", text)
        self.assertIn("--at 4.3,8.8,13.3,17.8,22.3,26.8,31.3 --no-end", text)

    @unittest.skipUnless(synth.HAVE_FFMPEG, "needs ffmpeg")
    def test_proof_sheet_passes_the_gate(self):
        p = ps.build("contentporary", videos_dir=self.videos)
        fake, reel = self.videos / "fake_hf.py", self.videos / "reel.mp4"
        fake.write_text(tq.FAKE_HF)
        synth._ffmpeg(["-f", "lavfi", "-i", "color=c=0x101418:s=1920x1080:r=30:d=31.5", "-pix_fmt", "yuv420p", str(reel)])
        saved = {k: os.environ.get(k) for k in ("HF_CLI", "FAKE_HF_CHECK", "FAKE_HF_RENDER_SRC")}
        os.environ.update(HF_CLI=f"{shlex.quote(sys.executable)} {shlex.quote(str(fake))}", FAKE_HF_CHECK="0", FAKE_HF_RENDER_SRC=str(reel))
        try:
            r = qa.run_gate(p, probe=tq.clean_probe)
        finally:
            for k, v in saved.items():
                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        self.assertEqual({c["n"]: c["status"] for c in r["checks"]}, {n: "PASS" for n in range(1, 11)}, qa.format_report(r))


if __name__ == "__main__":
    unittest.main()
````

Run: `python3 -m unittest discover -s tools -p 'test_proof_sheet.py'`
Expected: `ModuleNotFoundError: No module named 'proof_sheet'`.

- [ ] **Step 2: Implement**

Create `tools/proof_sheet.py`:

````python
"""Brand proof sheet: a long-form project that shows the kit — full-screen title, subtitle, lower third and
side screen text — in EVERY palette of a brand, one scene per palette, for onboarding approval
(brands/_template/README.md). The project is a normal scaffold (tools/new_video.py), so the QA gate runs on it.

Each palette scene carries its own palette as inline CSS variables (from lib/brand.js --json) and its own
data-hf-mode on a wrapper, so the kit reads the right ground mode; index.html keeps the BRIEF palette (QA
check 3). The lower third and side text sit over a neutral footage stand-in.

Usage:
  python3 tools/proof_sheet.py <brand> [--videos-dir videos] [--slug proof-<brand>] [--font <key>]
Then:
  python3 tools/qa.py videos/proof-<brand>              (a draft brand fails check 3 until approved — expected)
  npx hyperframes render videos/proof-<brand> -o videos/proof-<brand>/renders/proof.mp4
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import brandcheck
import new_video

ROOT = Path(__file__).resolve().parents[1]
SCENE_DUR = 4.5        # every kit animation lands by ≈ 3 s; the last 0.3 s is still (QA check 9)
COPY = {"title": "Printing Prediction System", "kicker": "Step 1", "subtitle": "HIT Prediction",
        "key_line": "and I've helped online entrepreneurs",
        "points": ["Video performance", "Retention", "CTR (Click through rate)"]}

SCENE = """<template>
  <style>
    #root {{ position: absolute; inset: 0; overflow: hidden; }}
    .proof-scene {{ position: absolute; inset: 0; background: var(--hf-ground-deep); }}
    .proof-q {{ position: absolute; width: 1920px; height: 1080px; transform: scale(0.5); transform-origin: 0 0; overflow: hidden; }}
    .proof-q.q1 {{ left: 0; top: 0; }} .proof-q.q2 {{ left: 960px; top: 0; }}
    .proof-q.q3 {{ left: 0; top: 540px; }} .proof-q.q4 {{ left: 960px; top: 540px; }}
    .proof-footage {{ position: absolute; inset: 0; background: radial-gradient(ellipse 30% 45% at 62% 46%, #b9a89a 0%, #8c7d72 45%, transparent 70%), linear-gradient(160deg, #9aa3aa 0%, #5d656c 100%); }}
    .proof-label {{ position: absolute; left: 24px; top: 20px; padding: 6px 16px; border-radius: 999px; font: 600 26px system-ui, sans-serif;
      color: var(--hf-text-primary); background: var(--hf-surface-fill); border: 1px solid var(--hf-surface-bevel); z-index: 5; }}
  </style>
  <div id="root" data-composition-id="{id}" data-width="1920" data-height="1080">
    <div class="proof-scene" data-hf-mode="{mode}" style="{vars}">
      <div class="proof-q q1"><div class="kit-host"></div></div>
      <div class="proof-q q2"><div class="kit-host"></div></div>
      <div class="proof-q q3"><div class="proof-footage"></div><div class="kit-host"></div></div>
      <div class="proof-q q4"><div class="proof-footage"></div><div class="kit-host"></div></div>
      <div class="proof-label">{palette} · {mode}</div>
    </div>
  </div>
  <script>
    (async function () {{
      var tl = gsap.timeline({{ paused: true }});
      await document.fonts.ready;
      var hosts = document.querySelectorAll('[data-composition-id="{id}"] .kit-host');
      var LF = {{ format: "long-form" }};
      HFKit.title(tl, hosts[0], Object.assign({{ at: 0.2, text: {title}, underline: 1 }}, LF));
      HFKit.subtitle(tl, hosts[1], Object.assign({{ at: 0.3, kicker: {kicker}, title: {subtitle} }}, LF));
      HFKit.lowerThird(tl, hosts[2], Object.assign({{ at: 0.4, text: {key_line} }}, LF));
      HFKit.sideText(tl, hosts[3], Object.assign({{ at: 0.2, items: {points} }}, LF));
      await HFText.ready();
      window.__timelines["{id}"] = tl;
    }})();
  </script>
</template>
"""


def palette_vars(root, brand_dir, palette, font) -> str:
    """The palette's CSS variables as one inline style string (lib/brand.js --json, sorted)."""
    r = subprocess.run([shutil.which("node") or "node", str(Path(root) / "lib" / "brand.js"), str(brand_dir),
                        "--palette", palette, "--font", font, "--json"], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise ValueError(f"lib/brand.js failed for palette {palette}: {r.stderr.strip()}")
    return "; ".join(f"{k}: {v}" for k, v in sorted(json.loads(r.stdout).items())).replace('"', "&quot;")


def build(brand, videos_dir=None, slug=None, font=None, root=ROOT) -> Path:
    """Scaffold videos/<slug>/ (default proof-<brand>) with one kit scene per palette; return its path."""
    root = Path(root)
    brand_dir = root / "brands" / brand
    try:
        loaded = brandcheck.load_brand(brand_dir)
    except brandcheck.BrandError as e:
        raise ValueError(str(e))
    tokens, palettes = loaded["tokens"], loaded["palettes"]
    font = font or tokens["fonts"]["defaultHeadline"]
    project = new_video.scaffold(slug or f"proof-{brand}", "long-form", brand, None, font, videos_dir, root)
    slots, rows, t = [], [], 0.0
    for name in tokens["palettes"]:
        sid = "proof-" + name
        scene = SCENE.format(id=sid, palette=name, mode=palettes[name]["mode"],
                             vars=palette_vars(root, brand_dir, name, font),
                             **{k: json.dumps(v) for k, v in COPY.items()})
        (project / "compositions" / f"{sid}.html").write_text(scene)
        slots.append(f'<div id="s-{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" '
                     f'data-start="{t:g}" data-duration="{SCENE_DUR:g}" data-track-index="1" data-width="1920" data-height="1080"></div>')
        rows.append(f'| {t:g} | {t + SCENE_DUR:g} | "{name} palette" | full-frame | proof-sheet | '
                    f'title · subtitle · lower-third · side-text | ease.glow / ease.card / ease.enter / ease.sweep | — |')
        t += SCENE_DUR
    index = project / "index.html"
    html = index.read_text()
    html, n = re.subn(r'\n\s*<!-- placeholder[^\n]*-->\n\s*<div id="hf-placeholder"[^\n]*</div>', "\n      " + "\n      ".join(slots), html)
    html, k = re.subn(r'\n\s*tl\.to\("#hf-placeholder"[^\n]*', "", html)
    if (n, k) != (1, 1):
        raise ValueError("new_video's index.html changed shape — update proof_sheet.build()")
    index.write_text(html.replace('data-duration="5"', f'data-duration="{t:g}"', 1))
    brief = (project / "BRIEF.md").read_text()
    brief = brief.replace('film: ""', f'film: "Approve the {brand} brand: every kit layout in every palette"')
    brief = brief.replace('direction: ""', 'direction: "Proof sheet: one scene per palette, kit components only"')
    (project / "BRIEF.md").write_text(brief)
    (project / "storyboard.md").write_text((project / "storyboard.md").read_text().rstrip("\n") + "\n" + "\n".join(rows) + "\n")
    # The proof sheet has no speech; this one segment gives the density check its runtime.
    (project / "transcript.json").write_text(json.dumps([{"text": "(proof sheet, no speech)", "start": 0, "end": t}]) + "\n")
    return project


def main(argv) -> int:
    ap = argparse.ArgumentParser(prog="python3 tools/proof_sheet.py", description="Kit proof sheet in every palette of a brand.")
    ap.add_argument("brand")
    ap.add_argument("--videos-dir")
    ap.add_argument("--slug")
    ap.add_argument("--font")
    a = ap.parse_args(argv[1:])
    try:
        project = build(a.brand, a.videos_dir, a.slug, a.font)
    except ValueError as e:
        print(e)
        return 1
    n = len(brandcheck.load_brand(ROOT / "brands" / a.brand)["tokens"]["palettes"])
    stills = ",".join(f"{i * SCENE_DUR + SCENE_DUR - 0.2:g}" for i in range(n))
    print(f"created {project} — {n} palettes, {n * SCENE_DUR:g} s")
    print(f"  gate:   python3 tools/qa.py {project}")
    print(f"  render: npx hyperframes render {project} -o {project}/renders/proof.mp4")
    print(f"  stills: npx hyperframes snapshot {project} --at {stills} --no-end -o {project}/renders/proof-stills")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
````

- [ ] **Step 3: Run the tests**

Run: `python3 -m unittest discover -s tools -p 'test_proof_sheet.py' -v`
Expected: `Ran 5 tests … OK` (≈ 6 s).

- [ ] **Step 4: Live gate + render the Contentporary proof sheet (≈ 3 min) and look at every palette**

````bash
python3 tools/proof_sheet.py contentporary --videos-dir renders/proof
python3 tools/qa.py renders/proof/proof-contentporary
npx hyperframes snapshot renders/proof/proof-contentporary --at 4.3,8.8,13.3,17.8,22.3,26.8,31.3 --no-end -o renders/proof/proof-contentporary/renders/proof-stills
````
Expected gate: ten `PASS`, `runtime probe: 93 samples (index.html)`, `RESULT: PASS` (prototype: 1 min 22 s). Stills (one per palette: red, gold, lime, silver, paper, reel-dark, reel-light), each a 2 × 2 grid labelled `<palette> · <mode>`:
- Dark palettes (`red`, `gold`, `lime`, `reel-dark`): glowing white title with the accent underline; dark glass pill with the title in `accent.text` and a soft glow; white→`accent.text` key line, no pill; dark grid side panel, chips with accent numbers.
- Light palettes (`silver`, `paper`, `reel-light`): no glow anywhere; dark `text.primary` title with the `accent.line` underline; frosted white pill, dark title on the `accent.block` marker (paper: dark brown on orange); the key line on a frosted pill; frosted white side panel. A light scene must never show a dark-mode colour (that was the nested-mode bug, Decision 4).
Then render the video for Tymek: `npx hyperframes render renders/proof/proof-contentporary -o renders/proof/proof-contentporary/renders/proof.mp4`. The proof sheet is not committed (it is regenerable; `renders/` is gitignored).

- [ ] **Step 5: Commit**

````bash
git add tools/proof_sheet.py tools/test_proof_sheet.py
git commit -m "feat(tools): proof_sheet builds the brand proof sheet — the kit in every palette, gate-ready" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
````

---

### Task 15: Docs close-out — kit section, kit table, variant names, proof-sheet step, roadmap

**Files:**
- Modify: `lib/README.md`, `standards/formats/long-form.md`, `brands/contentporary/brand.md`, `brands/_template/README.md`, `CLAUDE.md`, `docs/superpowers/plans/2026-10-03-animation-workflow-roadmap.md`, `tools/test_standards_layout.py`

**Interfaces:**
- Consumes: everything above (real names only: `HFKit.<call>`, `tools/proof_sheet.py`, `tools/kit_preview.py`, `HFProfile.claimTransform`, `HFText.splitWords`, `opts.onSpans`).
- Produces: the `long-form.md` section "Kit — lib/kit" (the table: component, variant, placement, layout, motion — values equal the code); the `lib/README.md` section "Kit — lib/kit/" + load order + contract bullets; `brand.md` variant names → calls; onboarding step 8 → the real commands; roadmap: Plan 4 **Done** (branch `kit-v1`), Plan 5 **Ready to write**, `## Notes for Plan 5 (from Plan 4)`; `test_standards_layout.py` `KitDocsTests` and `test_roadmap_marks_plan_4_done_and_plan_5_ready`.

- [ ] **Step 1: Write the docs**

````bash
python3 - . <<'PY'
import sys
from pathlib import Path
ROOT = Path(sys.argv[1])

def edit(rel, pairs):
    p = ROOT / rel
    s = p.read_text()
    for a, b in pairs:
        if s.count(a) != 1:
            sys.exit(f"{rel}: expected exactly one match for: {a[:70]!r}")
        s = s.replace(a, b)
    p.write_text(s)

KIT_SECTION = """## Kit — `lib/kit`

Templated graphics and the two recurring devices are kit calls:
`HFKit.<component>(tl, host, { format: "long-form", at, … })` builds the layout inside `host` (a 1920×1080
box), adds its tweens to the scene's paused timeline and returns `{ dur, … }` (seconds from `at` until it has
settled). API and contract: `lib/README.md`. A brand picks one variant per component (`tokens.json` `kit`);
new variants are added to the shared kit and become available to every brand.

| Component | Variant | Placement | Layout (1920×1080) | Motion |
|---|---|---|---|---|
| `HFKit.title` | `glow-center` | full-frame | one centred line, 104 px (9.6 % H), warm ambient top glow; optional scribble underline under one word (`underline: <word index>`) | glow title (pop 70 %, settle 0.4 s `ease.glow`, +430 ms per word); underline one chain gap after it settles (`ease.sweep`) |
| `HFKit.subtitle` | `glass-pill-script` | full-frame | glass pill ≥ 770 px (40 % W) centred on the grid ground; script kicker 72 px (6.7 % H) over the title, 92 px (8.5 % H), in `accent.text` | card entrance (0.43 s `ease.card`) → script write-on at +0.3 s (135 ms/letter) → glow title one chain gap later |
| `HFKit.lowerThird` | `key-line` | over-footage | one key line, 50 px (4.6 % H) body font, centred, baseline ≈ 95 % H; one white → `accent.text` gradient across the line | word entrance; fades out (0.43 s `ease.enter`), gone at `out` |
| `HFKit.sideText` | `grid-panel-chips` | over-footage | grid panel 0–928 px (48 % W); 90 px glass number chips at x 115, rows every 145 px from y 140; labels 48 px (4.4 % H) at x 277; 1–6 points; the face stays on the right | panel slides 80 px + fades (0.6 s `ease.enter`); each point = status chip + its label word by word 0.1 s later, one point every two chain gaps unless each `items[i].at` is given |
| `HFKit.ctaYoutube` | `watch-page-dive` | full-frame, transforms the footage | the face footage inside the player rect of a real watch-page screenshot (`page: {src, width, height, player, link}`) | scale to 0.80 (0.5 s) → hold 0.5 s → dive 2× onto the link (0.6 s) → hold 1.7 s → back (0.6 s) → hold 0.5 s → face (0.5 s): 4.9 s, all `ease.camera` |
| `HFKit.roadmap` | `wave-nodes` | full-frame | system name (92 px caps, two lines) above a glowing wavy path; numbered nodes every 640 px (3–6 steps); 250×290 icon cards docked on their nodes | `visit: 0` intro: title word by word, path draws 1.2 s `ease.sweep`, each node pops (0.48 s `ease.enter`) as the line reaches it; `visit: k`: opens on visit k−1's end state, card k docks (card entrance), camera travels 1.6 s `ease.camera` |

**Light ground** (`mode: light`): every component drops its glow — titles in dark `text.primary` (word
entrance), the subtitle's title on an `accent.block` marker, the lower third on a frosted white pill, a
frosted white side panel and chips, the roadmap path without bloom. Every component reads `data-hf-mode`
from its nearest ancestor and throws when there is none.

**Over-footage layouts** (lower third, side text) are standalone documents in `compositions/overlays/`: no
`<template>`, their own `data-hf-mode` on the root, root-relative paths (`lib/kit/…`,
`compositions/brand.css`), rendered with `-c … --format=mov`. Never give a kit element an id or class
containing `caption` (QA check 7).

"""

edit("standards/formats/long-form.md", [
    ("| `lib/kit` (Plan 4); new variants per video allowed |", "| `lib/kit` (see `## Kit` below); new variants per video allowed |"),
    ("## Custom catalogue\n", KIT_SECTION + "## Custom catalogue\n"),
])

edit("brands/contentporary/brand.md", [
    ("""## Kit variants
`glow-center` title · `glass-pill-script` subtitle ("Step 1" in script over a glowing title in a
glass pill) · `key-line` lower third (one key line, bottom-centre, white→warm gradient) ·
`grid-panel-chips` side text (left-half grid panel, glass number chips, face on the right) ·
`watch-page-dive` CTA · `wave-nodes` chapter roadmap (glowing wavy line, numbered nodes, icon cards).""",
     """## Kit variants
The variant names are `lib/kit` variants (`tokens.json` `kit`; layouts and timings in
`standards/formats/long-form.md` `## Kit`):
`glow-center` title (`HFKit.title`) · `glass-pill-script` subtitle (`HFKit.subtitle`: "Step 1" in script
over a glowing title in a glass pill) · `key-line` lower third (`HFKit.lowerThird`: one key line,
bottom-centre, white→warm gradient) · `grid-panel-chips` side text (`HFKit.sideText`: left-half grid
panel, glass number chips, face on the right) · `watch-page-dive` CTA (`HFKit.ctaYoutube`, over a real
screenshot of the brand's own watch page) · `wave-nodes` chapter roadmap (`HFKit.roadmap`: glowing wavy
line, numbered nodes, icon cards). Proof sheet of all four templated layouts in every palette:
`python3 tools/proof_sheet.py contentporary`."""),
])

edit("brands/_template/README.md", [
    ("""8. Render the brand proof sheet (Plan 4 tooling): full-screen title, subtitle, lower third and
   side screen text in every palette.""",
     """8. Build and render the brand proof sheet — full-screen title, subtitle, lower third and side screen
   text in every palette, one scene per palette:
   `python3 tools/proof_sheet.py <client-slug>` (writes `videos/proof-<client-slug>/`), then
   `python3 tools/qa.py videos/proof-<client-slug>` (every check passes except 3 while the brand is still
   `draft`), then render the stills the tool prints
   (`npx hyperframes snapshot videos/proof-<client-slug> --at … --no-end -o videos/proof-<client-slug>/renders/proof-stills`)
   and the video (`npx hyperframes render videos/proof-<client-slug> -o videos/proof-<client-slug>/renders/proof.mp4`)."""),
])

edit("CLAUDE.md", [
    ("""Modules: `profile.js` (format eases + timings), `motion-blur.js`, `camera.js`, `marks.js`, `text.js`,
`brand.js`, `shorts/wipe.js` — API and load order in `lib/README.md`.""",
     """Modules: `profile.js` (format eases + timings), `motion-blur.js`, `camera.js`, `marks.js`, `text.js`,
`brand.js`, `shorts/wipe.js`, and the long-form kit `kit/` (`HFKit.title`, `subtitle`, `lowerThird`,
`sideText`, `ctaYoutube`, `roadmap` — templated graphics are kit calls) — API and load order in `lib/README.md`."""),
    ("""the gate has not run) · `slice.py` (long-form delivery) · `scan_flicker.py` · `brandcheck.py`.""",
     """the gate has not run) · `slice.py` (long-form delivery) · `scan_flicker.py` · `brandcheck.py` ·
`proof_sheet.py` (brand proof sheet: the kit in every palette, for onboarding approval)."""),
])

edit("lib/README.md", [
    ("""<script src="lib/brand.js"></script>        <!-- HFBrand -->
<script src="lib/shorts/wipe.js"></script>  <!-- HFWipe    (Shorts only; needs profile) -->""",
     """<script src="lib/brand.js"></script>        <!-- HFBrand -->
<script src="lib/kit/kit.js"></script>      <!-- HFKit     (long-form only; needs all of the above) -->
<script src="lib/kit/title.js"></script>    <!-- …then each component: title, subtitle, lower-third, -->
<script src="lib/kit/subtitle.js"></script> <!--   side-text, cta-youtube, roadmap (manifest loadOrder) -->
<script src="lib/kit/lower-third.js"></script>
<script src="lib/kit/side-text.js"></script>
<script src="lib/kit/cta-youtube.js"></script>
<script src="lib/kit/roadmap.js"></script>
<script src="lib/shorts/wipe.js"></script>  <!-- HFWipe    (Shorts only; needs profile) -->"""),
    ("""- **Marks and text helpers overwrite an element's inline `transform`.** Elements they animate must not
  carry a stylesheet transform.""",
     """- **One inline-transform writer per element.** Camera (stage, push), marks (highlight, chips), text
  (word spans) and every kit entrance overwrite an element's inline `transform`; each claims the element
  with `HFProfile.claimTransform(el, owner)` and a second, different owner throws naming both. Wrap the
  element and give each binder its own. Elements they animate must not carry a stylesheet transform.
- **Split text keeps its markup.** `HFText.splitWords(el)` / `splitChars(el)` wrap every word / code point
  in a span and leave element children (`<b>`, an accent `<span>`) in place (`data-hf-nosplit` keeps one
  whole); `words`, `typeOn` and `HFMarks.scriptWord` use them and hand the spans to `opts.onSpans(spans)`.
- **`HFText.accentWord` installs its own stylesheet** (once); `installCss()` is no longer required."""),
    ("""| `shorts/wipe.js` | `HFWipe` | `wipe(tl, {host, fe, filterId, dir, inAt, outAt})` · `phase(tl, out, in, T, dir)` |""",
     """| `shorts/wipe.js` | `HFWipe` | `wipe(tl, {host, fe, filterId, dir, inAt, outAt})` · `phase(tl, out, in, T, dir)` (chain phases on one host freely: edges snap within 1 µs) |
| `kit/kit.js` + `kit/<component>.js` | `HFKit` | `title` · `subtitle` · `lowerThird` · `sideText` · `ctaYoutube` · `roadmap` — each `(tl, host, opts)` → `{ dur, … }`; `variants(name)` · `mode(host)` · `ground` · `cardIn` · `slideIn` · `fadeOut` · `pop` |"""),
    ("""| `text.js` | `HFText` | `words` · `typeOn` · `glowTitle` · `defocus` · `accentWord` (+ `installCss()`) · `odometer` (`opts.fps`, default 30) · `rasterText` · `glowFilter` / `injectGlow` · `ready()` |""",
     """| `text.js` | `HFText` | `words` · `typeOn` · `glowTitle` (`opts.intensity`, default 1.2) · `defocus` · `accentWord` · `odometer` (`opts.fps`, default 30) · `rasterText` · `glowFilter` / `injectGlow` · `splitWords` / `splitChars` · `blurPx` · `track(promise)` / `ready()` |"""),
    ("""## Example — a long-form custom scene""",
     """## Kit — `lib/kit/` (long-form templated graphics)

`HFKit.<component>(tl, host, opts)` builds a whole templated layout inside `host` — a 1920×1080 box the
kit sizes but never transforms — adds its tweens to `tl` and returns `{ dur, … }` (seconds from `opts.at`
until settled). Every component: `opts.format` must be `"long-form"`; `opts.at` (default 0) is when it
starts; `opts.variant` picks a variant (default: the first, the only one today). Layouts, sizes and
timings: `standards/formats/long-form.md` `## Kit`. Built only on `HFProfile`, `HFCamera`, `HFMarks`,
`HFText` and the brand variables; the kit's stylesheet (`<style id="hf-kit-css">`, installed once) holds
no colour literal.

| Call | Options | Returns |
|---|---|---|
| `HFKit.title(tl, host, o)` | `text`, `underline` (word index, optional) | `{dur, words}` |
| `HFKit.subtitle(tl, host, o)` | `title`, `kicker` (optional script line, e.g. "Step 1") | `{dur, pill, kicker, words}` |
| `HFKit.lowerThird(tl, host, o)` | `text`, `out` (optional: gone by then) | `{dur, words}` |
| `HFKit.sideText(tl, host, o)` | `items` (1–6 strings or `{text, at}`), `out` | `{dur, chips, labels}` |
| `HFKit.ctaYoutube(tl, host, o)` | `footage` (the face `<video>` — give it an `id`), `page: {src, width, height, player: [x,y,w,h], link: [x,y,w,h]}` (a real screenshot, page px) | `{dur, poses}` |
| `HFKit.roadmap(tl, host, o)` | `title`, `steps` (3–6 × `{label, icon?}`; icons `bulb` `sliders` `chart` `target`), `visit` (0 = intro, k = dock card k) | `{dur, pose, nodes, cards}` |

- **Ground mode:** each component reads `data-hf-mode` from `host.closest("[data-hf-mode]")` and throws
  when there is none (`new_video` writes it on `index.html`'s root; an overlay document sets it on its own
  root). The resolved mode goes on the host as `hf-kit-dark` / `hf-kit-light`, which the kit CSS keys off,
  so a light scene nested in a dark root (the proof sheet) styles correctly. Light drops every glow.
- **Build after `await document.fonts.ready`** (the lower third and markers measure text), then
  `await HFText.ready()` before registering the timeline (the CTA's page image decode is tracked there).
- **The roadmap is one world:** every visit builds the same geometry, so a visit-k scene opens exactly
  where visit k−1 ended; give each visit its own reel slot and the same `title` + `steps`.
- **The CTA camera is a DOM camera** (no motion blur on the dive): live footage cannot be baked into a blur
  texture yet. The scene ends on the footage itself, so if the face moves in the CTA's last 0.3 s, waive it
  in the BRIEF: `check 9 [<cta slot id>]: the CTA ends on live footage`.
- **Brand proof sheet:** `python3 tools/proof_sheet.py <brand>` builds `videos/proof-<brand>/` — title,
  subtitle, lower third and side text in every palette — for onboarding approval.

## Example — a long-form custom scene"""),
    ("""  fails when `HFProfile` timings or `HFMotionBlur` shutters drift from the profile markdown.""",
     """  fails when `HFProfile` timings (incl. the kit's card, chain-gap, node and CTA values) or `HFMotionBlur`
  shutters drift from the profile markdown. `lib/test/kit-<component>.test.js` run the kit contract
  (`lib/test/kit-contract.js`: long-form only, throws without `data-hf-mode`, deterministic, profile eases
  only, build-time style = from-state incl. transform and filter, no glow on the light ground) plus each
  component's own layout and timing."""),
    ("""  from every module, seeks 42 frames forwards and then shuffled, and compares what paints""",
     """  from every module (incl. chained `HFWipe.phase` → `phase` on one host), seeks 52 frames forwards and then shuffled, and compares what paints"""),
])
print("docs updated")
PY
````

- [ ] **Step 2: Mark the roadmap and pin the docs with tests**

````bash
python3 - . <<'PY'
import sys
from pathlib import Path
ROOT = Path(sys.argv[1])

def edit(rel, pairs):
    p = ROOT / rel
    s = p.read_text()
    for a, b in pairs:
        if s.count(a) != 1:
            sys.exit(f"{rel}: expected exactly one match for: {a[:70]!r}")
        s = s.replace(a, b)
    p.write_text(s)

NOTES5 = """## Notes for Plan 5 (from Plan 4)

- Templated graphics are kit calls: `HFKit.title | subtitle | lowerThird | sideText | ctaYoutube | roadmap (tl, host, { format: "long-form", at, … })` (`lib/README.md` `## Kit`, layouts in `standards/formats/long-form.md` `## Kit`). The entry skill should map a beat-grid row whose `type` is a kit name straight to its call; the kit is long-form only.
- Fonts are not in the repo: without the shared-drive fonts (Satoshi, Helvetica Now Display, SF Pro, Brittany Signature) renders fall back — the script kicker becomes a serif. Run the pilot on a machine with the fonts installed, or add `@font-face` from `brands/<brand>/assets/`.
- CTA: a DOM camera, no motion blur on the 0.6 s dive (the reference shows some). Blurring it needs `HFCamera.rig` `liveBake` over HyperFrames' injected video frames — verify on the pilot footage. A CTA that ends on moving footage needs `check 9 [<slot id>]: the CTA ends on live footage`.
- The CTA needs a real screenshot of the brand's own watch page in `assets/captures/` (MANIFEST row) with the player and description-link rects measured in page pixels.
- Roadmap: one world per video, one reel slot per visit, same `title` + `steps` in every visit; the 1.25× framing on card k and the 1.6 s leg are lib defaults — tune them against the pilot's chapter beats.
- Visual calibration made in Plan 4 against the template stills: kit glow titles at `HFKit.GLOW` = 0.6 (lib default 1.2 smears at 1080p), ground grid cell 150 px (the stills) where `brand.md` says ≈ 4 columns (the reference video), the light grid stays faintly visible on `paper` (`brand.md`: no grid on paper). Settle each in `brands/contentporary/brand.md` after the pilot.
- Catalogue D1 (tiles flanking the face) and D2 (side screenshot + script + highlight) are still custom builds from `camera` / `marks` / `text`; promote them to kit variants (`HFKit.register(name, variant, binder, css)` in a new `lib/kit/` file + manifest + a `kit-contract` test) once the pilot has used them.
- Brand proof sheet: `python3 tools/proof_sheet.py <brand>` → `videos/proof-<brand>/`; regenerate whenever a palette changes and get the stills re-approved.
"""

edit("docs/superpowers/plans/2026-10-03-animation-workflow-roadmap.md", [
    ("| 2, 3 | **Written:** `2026-10-04-plan-4-kit-components.md` |", "| 2, 3 | **Done** (branch `kit-v1`) |"),
    ("| 1–4 | To write after Plan 4 |", "| 1–4 | **Ready to write** |"),
    ("## Notes for Plan 4 (from Plan 3)\n", NOTES5 + "\n## Notes for Plan 4 (from Plan 3)\n"),
])

p = ROOT / "tools" / "test_standards_layout.py"
s = p.read_text()
a = """    def test_roadmap_marks_plan_3_done_and_plan_4_written(self):
        t = (ROOT / "docs/superpowers/plans/2026-10-03-animation-workflow-roadmap.md").read_text()
        row3 = [l for l in t.splitlines() if l.startswith("| 3 |")][0]
        row4 = [l for l in t.splitlines() if l.startswith("| 4 |")][0]
        self.assertIn("**Done** (branch `tools-v1`)", row3)
        self.assertIn("**Written:** `2026-10-04-plan-4-kit-components.md`", row4)
        self.assertTrue((ROOT / "docs/superpowers/plans/2026-10-04-plan-4-kit-components.md").is_file())"""
b = """    def test_roadmap_marks_plan_4_done_and_plan_5_ready(self):
        t = (ROOT / "docs/superpowers/plans/2026-10-03-animation-workflow-roadmap.md").read_text()
        row3 = [l for l in t.splitlines() if l.startswith("| 3 |")][0]
        row4 = [l for l in t.splitlines() if l.startswith("| 4 |")][0]
        row5 = [l for l in t.splitlines() if l.startswith("| 5 |")][0]
        self.assertIn("**Done** (branch `tools-v1`)", row3)
        self.assertIn("**Done** (branch `kit-v1`)", row4)
        self.assertIn("**Ready to write**", row5)
        self.assertIn("## Notes for Plan 5 (from Plan 4)", t)"""
if s.count(a) != 1:
    sys.exit("test_standards_layout.py: Plan-4-written roadmap test not found")
s = s.replace(a, b)
a = """

if __name__ == "__main__":
    unittest.main()"""
b = """


class KitDocsTests(unittest.TestCase):
    def test_no_plan_4_placeholders_left(self):
        for rel in ToolsDocsTests.DOCS + ["brands/_template/README.md", "brands/contentporary/brand.md"]:
            self.assertNotIn("(Plan 4", (ROOT / rel).read_text(), rel)

    def test_long_form_kit_table_names_every_call_and_variant(self):
        import json
        t = (ROOT / "standards" / "formats" / "long-form.md").read_text()
        self.assertIn("## Kit — `lib/kit`", t)
        kit = json.loads((ROOT / "brands" / "contentporary" / "tokens.json").read_text())["kit"]
        calls = {"title": "HFKit.title", "subtitle": "HFKit.subtitle", "lower-third": "HFKit.lowerThird",
                 "side-text": "HFKit.sideText", "cta-youtube": "HFKit.ctaYoutube", "roadmap": "HFKit.roadmap"}
        for name, variant in kit.items():
            row = [l for l in t.splitlines() if l.startswith(f"| `{calls[name]}` |")]
            self.assertEqual(len(row), 1, name)
            self.assertIn(f"| `{variant}` |", row[0])
            self.assertIn(calls[name], (ROOT / "brands" / "contentporary" / "brand.md").read_text())
            self.assertIn(calls[name], (ROOT / "lib" / "README.md").read_text())

    def test_onboarding_and_claude_md_name_the_proof_sheet(self):
        self.assertIn("python3 tools/proof_sheet.py <client-slug>", (ROOT / "brands" / "_template" / "README.md").read_text())
        self.assertIn("proof_sheet.py", (ROOT / "CLAUDE.md").read_text())
        self.assertTrue((ROOT / "tools" / "proof_sheet.py").is_file())

    def test_lib_readme_documents_the_plan_2_review_hooks(self):
        t = (ROOT / "lib" / "README.md").read_text()
        for s in ["HFProfile.claimTransform", "splitWords", "opts.onSpans", "accentWord` installs its own stylesheet",
                  "lib/kit/kit.js", "data-hf-mode", "proof_sheet.py"]:
            self.assertIn(s, t, s)


if __name__ == "__main__":
    unittest.main()"""
if s.count(a) != 1:
    sys.exit("test_standards_layout.py: module footer not found")
p.write_text(s.replace(a, b))
print("roadmap + layout tests updated")
PY
````

- [ ] **Step 3: Run the whole suite**

Run: `python3 -m unittest discover -s tools -p 'test_*.py' -v`
Expected: `Ran 293 tests … FAILED (errors=14, skipped=1)` — the 14 `test_instantly_*` errors and the live kit gate skipped; nothing else.
Run: `node --test lib/test/*.test.js tools/*.test.js`
Expected: `# pass 153` `# fail 0`.

- [ ] **Step 4: Commit**

````bash
git add lib/README.md standards/formats/long-form.md brands/contentporary/brand.md brands/_template/README.md CLAUDE.md docs/superpowers/plans/2026-10-03-animation-workflow-roadmap.md tools/test_standards_layout.py
git commit -m "docs: kit section and table, variant names, proof-sheet onboarding step; roadmap marks Plan 4 done" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
````

---

## Self-Review

**1. Spec coverage** (spec §6a, §7, §8, Appendix A; roadmap Plan 4 row and both note lists):

| Requirement | Task |
|---|---|
| `lib/kit/` — `title` `glow-center` (template still 1) | 7 |
| `subtitle` `glass-pill-script` — "Step 1" script kicker over a glowing title in a dark glass pill (still 2) | 8 |
| `lower-third` `key-line` — one key line bottom-centre, white→warm gradient (still 3); the only spoken-word text in long-form | 9 |
| `side-text` `grid-panel-chips` — left-half grid panel, numbered glass chips, face on the right, 1–6 points (still 6) | 10 |
| `cta-youtube` `watch-page-dive` — face to 0.80 in a watch-page player ≈ 0.5 s, dive ≈ 2× to the link, hold ≈ 1.7 s, reverse; identical every time | 11 (+ timings 1) |
| `roadmap` `wave-nodes` — glowing wavy path, numbered nodes, icon cards; introduced once, revisited per chapter docking the next card, camera continues from the last pose | 12 |
| Each component token-driven, seek-safe, built only on `HFProfile` / `HFCamera` / `HFMarks` / `HFText` / `HFBrand` variables | 5–12 (contract: profile eases only, from-state at build, no conflicts; hygiene: no colour literals) |
| Reads `data-hf-mode` via `closest("[data-hf-mode]")`, throws if missing; light mode drops glow per `brand.md` | 5 (`mode`, `begin`), 7–12 (contract + per-component light tests) |
| `words()` / `typeOn` / `scriptWord` expose spans and keep nested markup; `accentWord` installs its CSS | 2 |
| A guard against two transform-writing binders on one element | 1 (+ 2 words, 5 kit entrances) |
| `visibleBeforeStart` compares transform / filter | 3 |
| Chained phase → phase wipes on one host in the smoke page | 4 |
| Existing lib tests, hygiene scan and drift tests keep passing; manifest + `loadOrder` list the kit; `sync_lib` / `new_video` include it | 1–12 (`# pass` grows 85 → 153, never a failure), 5 (manifest, `FORMAT_ONLY`), 7–12 (manifest per component) |
| Over-footage layouts are standalone overlay documents, root-relative paths, own `data-hf-mode`; full-frame components usable as reel scenes; no `caption` / `hf-placeholder` names | 6 (`kit_preview` writes both shapes), 13 (gate + caption test) |
| Brand proof sheet — title, subtitle, lower third, side text in every palette; tool vs `new_video` option decided and justified; passes `tools/qa.py` | 14 (Decision 7) |
| Visual fidelity: render and compare each component with its still / reference strip, acceptance notes with proportions, glow, bevel, type sizes | 7–12 Step 5, 14 Step 4 |
| Tests: node unit tests per component (determinism, seek parity, throws on missing mode, light no-glow, profile eases only, no colour literals); a Python test building a project with every kit component through the gate (fake CLI + live run) | 5–12, 13 |
| Docs: `lib/README.md` kit section; `long-form.md` kit table → real API; `brand.md` variants → real names; `_template/README.md` proof-sheet step → real command; `CLAUDE.md`; roadmap Plan 4 Done / Plan 5 Ready + notes for Plan 5 | 15 |

Deferred on purpose (flagged above): catalogue D1/D2 as kit variants (Decision 9), motion blur on the CTA dive (Decision 5), font installation (Global Constraints), `HFCamera` `glFailed` recovery (not needed: the kit's cameras are DOM-only).

**2. Placeholder scan:** every code step is a complete file or an exact, asserted replacement; no TBD/TODO; every run step names its command and expected output; the render steps name their frames and the numbers to judge them by.

**3. Type consistency:** `HFKit.begin` → `{mode, at, who, lf}` is what every component destructures; `HFKit.cardIn / slideIn / fadeOut / pop` return durations the components add up into `dur`; `HFText.words(…, {onSpans})`, `splitWords`, `glowTitle(…, {intensity})`, `track`, `blurPx` (Task 2) are the names Tasks 5–12 call; `HFProfile.timing("long-form").card / chainGap / node / cta` (Task 1) are the fields `kit.js`, `subtitle.js`, `side-text.js`, `cta-youtube.js` and `roadmap.js` read; `kit_preview.build` → `(project, looks)` is what `test_kit_preview.py` and `test_kit_qa.py` unpack; `proof_sheet.build` → `Path`; `helpers.kitHost / descendants / serialize / parseTransform` (Tasks 3, 5) are what `kit-contract.js` uses.

**4. Review Focus:** the five lines above, each pinned by named tests in Tasks 1, 2, 4, 5, 9, 10, 12, 13, 14.

**Prototype:** every code block in this plan was run in a scratch worktree of `kit-v1` (`0a7584d`), then replayed task by task on a second fresh worktree from the plan's own blocks; after each task the node suite passed (85 → 90 → 97 → 99 → 100 → 106 → 106 → 113 → 120 → 127 → 134 → 141 → 153 → 153 → 153) and at the end `Ran 293 tests … FAILED (errors=14, skipped=1)` (only the baseline `test_instantly_*` errors; the live kit gate skipped). Live, against HyperFrames 0.8.121: `npx hyperframes check` passed the full kit preview (0 errors; layout infos only for the camera worlds, now marked `data-layout-allow-overflow`); `python3 tools/qa.py` reported all ten checks PASS on the kit preview in `gold` (dark) and `silver` (light), with the CTA on a real `<video>`, and on the Contentporary proof sheet (7 palettes, 93 probe samples); `HF_LIVE=1` `test_live_gate` passed in ≈ 105 s; overlay renders were ProRes 4444 `yuva444p12le`. The smoke page passed with 52 frames after the `HFWipe` edge fix and failed without it (mismatch at 0.62 s and 0.8 s on `#ph-a`). Visual comparison against the stills: title (amber top glow, white halo, scribble under word 2), subtitle (pill ≈ 808 × 282 at the still's position, bevelled rim, grid + dot rows, gold glowing title), lower third (continuous white→gold gradient, baseline ≈ 1012 px), side text (panel 0–928, chips and labels at the still's coordinates) and the roadmap / CTA (matching the reference strips' framing) all matched; the remaining differences are the brand fonts not installed on the prototype machine (headline fallback heavier; the script kicker fell back to a serif) and the lib-level calibrations listed in Decision 6.
