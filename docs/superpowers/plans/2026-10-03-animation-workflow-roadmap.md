# Standard Animation Workflow — Roadmap

**Spec:** `docs/superpowers/specs/2026-10-03-animation-workflow-design.md`

The spec covers five subsystems with a clear dependency order. Each gets its own plan, and each
plan ships working, tested output on its own. Plans 2–5 are written only after the previous plan
has been executed, because each depends on code that doesn't exist yet. Writing them earlier would
mean guessing at interfaces.

| # | Plan | Delivers | Depends on | Status |
|---|---|---|---|---|
| 1 | **Standards & brand layer** | `standards/` (core motion law, QA doc, pipeline doc, long-form + Shorts profiles), `brands/_template/`, `brands/contentporary/`, `tools/brandcheck.py` (brand + BRIEF-choice validator), migration of `context/`, `PIPELINE.md`, `templates/`, slim `CLAUDE.md` | — | **Written:** `2026-10-03-plan-1-standards-and-brand.md` |
| 2 | **Shared library consolidation** | `lib/motion-blur.js` (3 forks merged, any aspect), `lib/camera.js`, `lib/marks.js`, `lib/text.js`, `lib/brand.js` (reads Plan 1 tokens/palettes), `lib/shorts/wipe.js`; `demo-transitions.js` retired; node unit tests for determinism (pose/value is a pure function of t) | 1 (token schema) | To write after Plan 1 |
| 3 | **Tools & automated QA gate** | `tools/sync-lib` + `lib.lock`, `tools/new-video` (scaffold + BRIEF template), `tools/probe-cuts`, `tools/cadence-scan`, `tools/slice` (clips + CSV, MP4 + ProRes 4444 alpha), `tools/scan-flicker`, `tools/qa` (runs all 10 checks of spec §9a, uses `brandcheck.py`), preview-pack generator | 1, 2 (lock hashes, blur/easing scans need lib API names) | To write after Plan 2 |
| 4 | **Kit components** | `lib/kit/` — `title`, `subtitle`, `lower-third`, `side-text`, `cta-youtube`, `roadmap`, each with its first named variant matched to the template stills and reference video; brand proof-sheet composition rendered for Contentporary (all palettes) | 2, 3 | To write after Plan 3 |
| 5 | **Entry skill & pilot** | `.claude/skills/contentporary-video/` (routes format/brand/checklist), final `CLAUDE.md` pointer, end-to-end pilot: one long-form graphics package + one Short through the full pipeline, review findings promoted into `standards/` | 1–4 | To write after Plan 4 |

**Deferred (spec §12):** custom-animation catalogue (from Tymek's reference videos), the Opus 5.5
animation video, font licensing, and exact gold/lime values (sampled from source files instead of
stills). Each becomes an update to `standards/` or `brands/` after Plan 5.
