# Contentporary — HyperFrames animation pipeline

This folder is a template system for producing Contentporary's own YouTube long-form and Shorts
animations at scale with HyperFrames. Read `PIPELINE.md` first — it defines the structure and the
production loop.

This is a port of `/Users/tymek/Desktop/Hyperframes` (built for client SaaS product-explainer
demos), scoped down to only the brand-agnostic pieces — the animation library, the WAAPI technique
reference, and the pipeline pattern. Client brand tokens, fonts, and old video projects were left
behind. See `PIPELINE.md`'s header for the full port rationale.

## Stay in sync with the team — pull first

This repo is shared by the Contentporary team on GitHub
(`https://github.com/tymekbielinski/hyperframes-contentporary`, branch `main`).

- **At the start of every session, before reading or editing anything:** run `git status`, then
  `git pull`. Tell the user what came in (new commits, or "already up to date").
- **If the pull is blocked by local changes:** do not discard them. `git stash`, `git pull`,
  `git stash pop`, and report any conflicts to the user instead of resolving them silently.
- **If `origin` still points at the old `hyperframes` URL:** run
  `git remote set-url origin https://github.com/tymekbielinski/hyperframes-contentporary.git`.
- **Before pushing:** pull again so you push on top of teammates' latest work. Commit and push
  only when the user asks.
- **Not in Git:** footage, audio, renders and edit exports (`*.mp4`, `*.mov`, `*.wav`, `*.mp3`,
  `*.xml`, `*.edl`, `*.srt`, … — see `.gitignore`). A pull will not bring these; if a project
  references media that isn't on disk, tell the user to get it from the team's shared drive.

Rules for any video task in this folder:
1. Start with the `/hyperframes` skill; it routes to the right workflow.
2. Load the context set before authoring: `context/design-system.md` (READ FIRST),
   `context/frame.md` (brand tokens — measured, normative), `context/motion-craft.md`,
   `context/narrative.md`, `context/voice.md`, `context/custom.md`.
2a. `context/design-system.md` is NORMATIVE and OUTRANKS `motion-craft.md`. It is the concrete
   Contentporary house style, reverse-engineered frame-by-frame from Tymek's own two reference
   reels with measured timings and sampled hex. Its §1 is the rule most builds get wrong:
   **graphics are FULL-FRAME scenes the edit cuts to, built on REAL screenshots — not overlays
   floating on the talking head.** Its §9 lists where `motion-craft.md` over-generalizes.
2b. `context/motion-craft.md` remains the general motion standard for anything `design-system.md`
   does not cover. Default fade-in / hold-still / fade-out animation on a flat background fails
   review. Run both checklists before every render.
2c. **NEVER fake motion blur with a Gaussian.** Any blur representing movement uses
   `lib/motion-blur.js` (`HFMotionBlur`) — the analytic per-pixel-velocity blur. A `feGaussianBlur`
   or CSS `blur()` is an isotropic smudge, not a trail, and is not an acceptable substitute for a
   camera move. Full wiring recipe (texture baking, aspect/`K` constraint, opaque bake, handoff) in
   `context/design-system.md` §8c. The single documented exception is element-level smear on
   content that is itself animating, which the library cannot texture.
3. Scripts live in `scripts/<slug>.md` (format: `templates/script-template.md`). Each script becomes
   one project in `videos/<slug>/` — copy `context/frame.md` into the project so HyperFrames skills
   pick it up as the design spec.
4. Generate TTS narration first (per `context/voice.md`), then time beats to the audio.
5. `npx hyperframes check` before every render; output to `videos/<slug>/<slug>.mp4`.
6. Batch requests ("render all scripts") iterate over `scripts/*.md`, one project each.
7. Content structure (Hook verbatim / Body bullet outline / CTAs verbatim) and the 3 pillars follow
   the root `../CLAUDE.md` — that file is the source of truth for Contentporary's voice and content
   rules; this folder only adds HyperFrames-specific production mechanics on top.

## Reusable animation library — `lib/`

Three portable, dependency-free modules ported from the original SaaS pipeline (full API in
`lib/README.md`):

- **`motion-blur.js` (`HFMotionBlur`)** — deterministic analytic camera motion blur. Handles camera
  motion over static content; ships named presets (rigid/elastic/fluid/paper/gas/glass/heavy/
  medium/light/film) that bridge to `motion-design` easing.
- **`demo-transitions.js` (`HFDemoTransitions`)** — scene transitions + camera rig: `cameraLeg`,
  `microDrift`, `blurCrossfade`, `zoomThrough`, `colorDip`. Originally built for product-demo
  shorts; the mechanics apply equally to breakdown/rebuild scene changes.
- **`deep-glow.js` (`HFDeepGlow`)** — multi-scale bloom as a seek-safe SVG filter, for accent
  highlights and title glow.

None of these are global — copy the ones a project needs: `cp lib/<module>.js videos/<slug>/lib/`.
