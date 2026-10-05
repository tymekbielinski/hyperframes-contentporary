# Standard Animation Workflow — Roadmap

**Spec:** `docs/superpowers/specs/2026-10-03-animation-workflow-design.md`

The spec covers five subsystems with a clear dependency order. Each gets its own plan, and each
plan ships working, tested output on its own. Plans 2–5 are written only after the previous plan
has been executed, because each depends on code that doesn't exist yet. Writing them earlier would
mean guessing at interfaces.

| # | Plan | Delivers | Depends on | Status |
|---|---|---|---|---|
| 1 | **Standards & brand layer** | `standards/` (core motion law, QA doc, pipeline doc, long-form + Shorts profiles), `brands/_template/`, `brands/contentporary/`, `tools/brandcheck.py` (brand + BRIEF-choice validator), migration of `context/`, `PIPELINE.md`, `templates/`, slim `CLAUDE.md` | — | **Written:** `2026-10-03-plan-1-standards-and-brand.md` |
| 2 | **Shared library consolidation** | `lib/profile.js` (format eases + timings), `lib/motion-blur.js` (3 forks merged, any aspect), `lib/camera.js`, `lib/marks.js`, `lib/text.js`, `lib/brand.js` (reads Plan 1 tokens/palettes), `lib/shorts/wipe.js`; `demo-transitions.js` retired; node unit tests for determinism (pose/value is a pure function of t) | 1 (token schema) | **Done** (branch `lib-v1`) |
| 3 | **Tools & automated QA gate** | `tools/sync-lib` + `lib.lock`, `tools/new-video` (scaffold + BRIEF template), `tools/probe-cuts`, `tools/cadence-scan`, `tools/slice` (clips + CSV, MP4 + ProRes 4444 alpha), `tools/scan-flicker`, `tools/qa` (runs all 10 checks of spec §9a, uses `brandcheck.py`), preview-pack generator | 1, 2 (lock hashes, blur/easing scans need lib API names) | **Done** (branch `tools-v1`) |
| 4 | **Kit components** | `lib/kit/` — `title`, `subtitle`, `lower-third`, `side-text`, `cta-youtube`, `roadmap`, each with its first named variant matched to the template stills and reference video; brand proof-sheet composition rendered for Contentporary (all palettes) | 2, 3 | **Done** (branch `kit-v1`) |
| 5 | **Entry skill & pilot** | `.claude/skills/contentporary-video/` (routes format/brand/checklist), final `CLAUDE.md` pointer, end-to-end pilot: one long-form graphics package + one Short through the full pipeline, review findings promoted into `standards/` | 1–4 | **Ready to write** |

**Deferred (spec §12):** custom-animation catalogue (from Tymek's reference videos), the Opus 5.5
animation video, font licensing, and exact gold/lime values (sampled from source files instead of
stills). Each becomes an update to `standards/` or `brands/` after Plan 5.

## Notes for Plan 5 (from Plan 4)

- Templated graphics are kit calls: `HFKit.title | subtitle | lowerThird | sideText | ctaYoutube | roadmap (tl, host, { format: "long-form", at, … })` (`lib/README.md` `## Kit`, layouts in `standards/formats/long-form.md` `## Kit`). The entry skill should map a beat-grid row whose `type` is a kit name straight to its call; the kit is long-form only. Build contract: `await document.fonts.ready; await HFText.loadFaces(root)` before building, `await HFText.ready()` before registering the timeline.
- Fonts are not in the repo: without the shared-drive fonts (Satoshi, Helvetica Now Display, SF Pro, Brittany Signature) renders fall back — the script kicker becomes a serif. Run the pilot on a machine with the fonts installed, or add `@font-face` from `brands/<brand>/assets/`. Two checks wait on the real fonts: the serif-fallback kicker and the §9b ghost-text recheck on the lower third (centred + per-word spans + `background-clip:text` was clean only in fallback-font renders).
- CTA: a DOM camera, no motion blur on the 0.6 s dive (the reference shows some). Blurring it needs `HFCamera.rig` `liveBake` over HyperFrames' injected video frames — verify on the pilot footage. A CTA that ends on moving footage needs `check 9 [<slot id>]: the CTA ends on live footage`.
- The CTA needs a real screenshot of the brand's own watch page in `assets/captures/` (MANIFEST row) with the player and description-link rects measured in page pixels (both must lie inside the page). A non-16:9 player rect bleeds the page edge at the face pose; a failed image decode is silent.
- Roadmap: one world per video, one reel slot per visit, same `title` + `steps` in every visit; the 1.8× visit framing (card ≈ 450 px on screen, measured on the reference) and the 1.6 s leg are constants in `lib/kit/roadmap.js` — tune them against the pilot's chapter beats. The wave path runs 400 px past both world edges so its ends never show. With more than 3 steps the intro pose zooms out to fit the wider world and shrinks the title; reference nodes are also larger and its title overlaps the wave.
- Visual tuning left against the reference stills (settle with Tymek, then fold into `brands/contentporary/brand.md`): title — silver top→bottom gradient fill, warmer ambience with darker corners, thinner double scribble (ours is whiter, stronger halo); subtitle — title weight heavier than the reference, soft top-right light sweep missing, the dark glass 2 px `ground-deep` ring reads as a rim hairline; side text — reference labels lighter with a soft glow, grid + dots a bit stronger; lower third — nothing open beyond the §9b recheck above.
- Calibrations made in Plan 4: kit glow titles at `HFKit.GLOW` = 0.6 (lib default 1.2 smears at 1080p), ground grid cell 150 px (the stills) where `brand.md` says ≈ 4 columns (the reference video), the light grid stays faintly visible on `paper` (`brand.md`: no grid on paper).
- Side text has no label-length guard: a label wider than its 620 px column runs past the panel edge (x 928) over the face. Keep labels short or add a guard (throw, or shrink) before relying on long copy.
- Catalogue D1 (tiles flanking the face) and D2 (side screenshot + script + highlight) mini animations are still custom builds from `camera` / `marks` / `text`; promote them to kit variants (`HFKit.register(name, variant, binder, css)` in a new `lib/kit/` file + manifest + a `kit-contract` test) once the pilot has used them.
- Brand proof sheet: `python3 tools/proof_sheet.py <brand>` → `videos/proof-<brand>/`; regenerate whenever a palette changes and get the stills re-approved.

## Notes for Plan 4 (from Plan 3)

- `tools/new_video.py` writes `data-hf-mode` on the `#root` of `index.html` and QA check 3 verifies it against the palette; the light-ground glow guard can read `closest("[data-hf-mode]")`. Standalone overlay documents must set it on their own root.
- The scaffold's `#hf-placeholder` is exempted from the easing check in `tools/qa_probe.mjs` by id (coupled to `new_video.py`); QA check 1 fails, non-waivably, if it survives next to real scenes. Do not name a kit element `hf-placeholder`.
- Kit components must pass every QA check, including the runtime probe (`qa_probe.mjs`: seek, easing vocabulary, blur reasons, text traps); the proof-sheet should be run through `python3 tools/qa.py`.
- Over-footage kit layouts (lower-third, side-text, catalogue D) are standalone documents in `compositions/overlays/` rendered with `-c … --format=mov` (a `<template>` sub-composition cannot render alone). Never give a kit element an id/class containing `caption` — QA check 7 reads that as a caption layer.
- Every kit tween takes an `HFProfile.ease` token (or is an `ease: "none"` driver with `onUpdate`); the probe flags anything else, including a tween with no ease.
- Waivers (BRIEF `exceptions:`) cannot waive infrastructure findings; scoped waivers match whole paths or words, so a kit exception needs the real path.
- Reuse in kit tests: `tools/project.py` (BRIEF, beat grid, slots), `tools/media.py`, `tools/synth.py` (lavfi test clips), `tools/runtime_probe.py` (named errors, timeouts).
- Overlay documents in `compositions/overlays/` must reference files root-relative (`lib/profile.js`, `compositions/brand.css`), not `../../lib/…`: HyperFrames serves every composition with the project root as its base, and `npx hyperframes check` fails relative paths (found in the Plan 3 final-review live run).
- The QA gate probes each overlay live through the studio's per-file route (`/api/projects/<name>/preview/comp/<file>`, HyperFrames 0.8.120) and renders it alone (`render -c`) for settle and flicker — kit layouts get the full gate. If a HyperFrames upgrade drops that route, `runtime_probe.overlay_url` is the one place to change.
- Deferred minors from Plan 3: glitches during fast camera moves can be missed by the flicker rule; a deliberate flash under 8 frames reads as a glitch (waivable); lowercase `## round N` in `critique.md` is ignored by the preview pack; flicker thresholds may need tuning in the pilot (Plan 5).

## Notes for Plans 3–4 (from the Plan 2 final review)

- Plan 3: export one machine-readable lib manifest (now only in `lib/test/hygiene.test.js` `EXPECTED`) for `sync-lib` + `lib.lock`; keep `shorts/wipe.js` in its subdirectory; decide whether `test/`, `examples/`, `README` are hashed. **Done in Plan 3:** `lib/manifest.json` + `tools/sync_lib.py` / `lib.lock`.
- Plan 3: extract the hygiene lexer/scanner (`lex`/`scan`) into a shared module for `tools/qa`; fold in its known gaps (quoted/template eases, `color-mix`/`lab`/`lch`, `url(#…)`/`.blur()` false positives, `.mjs`/`.cjs`, regex after `return`). **Done in Plan 3:** `tools/lawscan.js` (shared with the hygiene test; QA checks 4–6, 10).
- Plan 3: blur-reason tags set at runtime by lib (`setAttribute`) are invisible to static scans — QA check 5 must inspect the rendered DOM; the easing check can use `HFProfile.isProfileEase` over timeline children and must flag tweens with no ease (GSAP's default `power1.out` is off-vocabulary). **Done in Plan 3:** `tools/qa_probe.mjs` runtime probe (checks 5, 6, 10).
- Plan 3: add timing/shutter drift tests (`HFProfile` `TIMING` + `PROFILE_PRESETS` vs the profile markdown) before cadence-scan consumes them; move the wipe's 0.10 s handoff into `timing.wipe`; the ease-row parser should fail clearly on a cell without backticks; the brief template must mark `direction` required; QA gate check #3 enforces brand `status == approved`. **Done in Plan 3:** drift tests in `lib/test/drift.test.js`; check 3 enforces brand `status: approved`.
- Plan 4: the light-ground glow guard must read `data-hf-mode` and THROW if it is missing (the CLI CSS only emits a comment; new-video/kit must set the attribute).
- Plan 4: `words()`/`typeOn`/`scriptWord` return durations only — kits need the word spans (add `splitWords(el)` or `opts.onSpans`), and they discard nested markup; `accentWord` should install its CSS itself (idempotent).
- Plan 4: camera stage, push, marks and text all overwrite inline `transform` — never put two on one element (consider a guard); camera `glFailed` is permanent (revisit only if kits need recovery); extend `visibleBeforeStart` to compare transform/filter; add chained phase→phase wipes on one host to the smoke page.
