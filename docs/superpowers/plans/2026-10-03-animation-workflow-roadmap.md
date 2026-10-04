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
| 4 | **Kit components** | `lib/kit/` — `title`, `subtitle`, `lower-third`, `side-text`, `cta-youtube`, `roadmap`, each with its first named variant matched to the template stills and reference video; brand proof-sheet composition rendered for Contentporary (all palettes) | 2, 3 | **Written:** `2026-10-04-plan-4-kit-components.md` |
| 5 | **Entry skill & pilot** | `.claude/skills/contentporary-video/` (routes format/brand/checklist), final `CLAUDE.md` pointer, end-to-end pilot: one long-form graphics package + one Short through the full pipeline, review findings promoted into `standards/` | 1–4 | To write after Plan 4 |

**Deferred (spec §12):** custom-animation catalogue (from Tymek's reference videos), the Opus 5.5
animation video, font licensing, and exact gold/lime values (sampled from source files instead of
stills). Each becomes an update to `standards/` or `brands/` after Plan 5.

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
