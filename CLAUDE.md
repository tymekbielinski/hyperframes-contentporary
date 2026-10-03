# Contentporary — HyperFrames animation pipeline

Graphics for YouTube videos built on real talking-head footage — Contentporary's own channel and
every client. Two formats: **Shorts recut** and **long-form scene clips**. Spec:
`docs/superpowers/specs/2026-10-03-animation-workflow-design.md`.

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

## Rules for any video task

1. Start with the `/hyperframes` skill for HyperFrames mechanics. There is no separate frame spec
   file: for `/hyperframes`, the design spec is `brands/<brand>/` (brand.md, tokens.json, the
   chosen palette).
2. **Precedence:** `standards/core/` → `standards/formats/<format>.md` → `brands/<brand>/` → the
   video's `BRIEF.md`. A lower layer supplies values and never overrides a rule above it.
3. Read, in order: `standards/core/motion.md` (core motion law), the format profile
   (`standards/formats/long-form.md` or `shorts.md`), the brand (`brands/<brand>/brand.md`,
   `tokens.json`, the chosen palette), then `standards/core/pipeline.md`.
4. **Motion blur is never a Gaussian.** Movement blur uses `lib/motion-blur.js` (`HFMotionBlur`).
   Gaussian blur only with `data-blur-reason` = `focus`, `glow` or `wipe` (Shorts: wipe feather and element smear).
5. Long-form never has running captions (key-line lower thirds only). Shorts captions follow the
   BRIEF's `captions` flag.
6. Every video passes `standards/core/qa.md` (automated gate, agent critique loop, then sign-off by whoever ran the build).
7. **Promotion rule:** a finding that changes how future videos are made goes into `standards/` or
   `brands/`, never only into a BRIEF or agent memory.
8. New client → `brands/_template/README.md`. Validate any brand with
   `python3 tools/brandcheck.py brands/<name>`.
9. `videos/*` made before 2026-10-03 are frozen references; don't migrate or restyle them.

## Shared library — `lib/`

Shared by every brand and video; styled only by brand tokens (CSS variables from `lib/brand.js`).
Modules: `profile.js` (format eases + timings), `motion-blur.js`, `camera.js`, `marks.js`, `text.js`,
`brand.js`, `shorts/wipe.js` — API and load order in `lib/README.md`. Never hand-edit a project's copy;
improvements go into root `lib/` first. Until `tools/sync-lib` exists (Plan 3), copy the needed root
`lib/` files into the project unmodified.

## Tests

`python3 -m unittest discover -s tools -p 'test_*.py' -v` — includes the `lib/` node suite
(alone: `node --test "lib/test/*.test.js"`; browser seek check: `lib/examples/smoke.html`).
