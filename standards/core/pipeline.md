# Production Pipeline

Two production models, both built on real talking-head footage. Entry point: the
`contentporary-video` project skill (Plan 5). Until it exists, follow this file directly.

## Project layout (both formats)
```
videos/<slug>/  BRIEF.md · transcript.json · storyboard.md · critique.md · assets/captures/MANIFEST.md
                index.html · compositions/ (brand.css; long-form: overlays/) · lib/ + lib.lock · deliver/
                renders/ (never committed: drafts, qa-report.json, preview/)
```
`python3 tools/new_video.py <slug> --format long-form|shorts [--palette <p>] [--font <f>]` creates all of
it (brand from `--brand`, default `contentporary`) and never overwrites an existing project.

**Model and effort:** build with Claude Opus 5.5 at **high effort**; use max effort for custom
diagram canvases (catalogue group C) and for critique-loop fixes. Always build in HyperFrames: a model
left without a named framework writes its own renderer.

## BRIEF fields
```yaml
format: long-form            # long-form | shorts
film: "One line: what this video's graphics must make the viewer feel or believe."   # required
direction: "One line of art direction, e.g. 'one canvas per argument; proof first, then the number'."
references:                  # optional: reference videos/stills whose grammar to borrow
  - "youtube.com/watch?v=HrYMfy6MZtA — camera travel, backdrop headlines"
gotchas:                     # things to avoid in this video specifically
  - "No lime on this one — the client's competitor uses it"
brand: contentporary         # folder under brands/, must be status: approved
palette: red                 # one of the brand's palettes
font: helvetica              # one of the brand's headline fonts
overrides:                   # optional one-off palette role overrides
  accentScript: "#BACE7A"
captions: false              # Shorts only: true | false
hook_end: 80                 # long-form only: end of the hook in seconds (default 80)
screen_share:                # long-form only: ranges exempt from the 30 s cadence rule
  - [302.5, 317.0]
exceptions:                  # optional, each with a reason
  - "F09: recreated Google Calendar — no shareable real account"
source: "shared drive path to the basic-edit export / footage"
```
Override keys are palette role paths, dot-separated and flat — e.g. `accent.block`, `accentScript` — not nested YAML.

## Beat grid (the storyboard format)

`storyboard.md` is a table, one row per graphic, written from `transcript.json` and approved by the
runner before any code:

| t_in | t_out | words | placement | type | beats | ease | marks |
|---|---|---|---|---|---|---|---|
| 62.2 | 68.0 | "it's a system that prints…" | full-frame | roadmap | line draws 0–1.2 · node 1 docks 1.4 · push to node 2.4 | ease.camera / ease.enter | — |
| 74.1 | 79.4 | "1.2 million views" | full-frame | A1 | card lands 0.0 · highlight 0.3 · headline words 1.0–2.4 · hold | ease.enter / ease.sweep | highlight-block, script-word |

`type` is a kit name or a catalogue ID from `standards/formats/long-form.md`. Density is checked on
this table before building.

## Long-form
1. **Intake.** `python3 tools/new_video.py <slug> --format long-form` scaffolds `videos/<slug>/` and
   syncs `lib/` (`python3 tools/sync_lib.py videos/<slug>` re-syncs later). The scaffold's `index.html`
   holds a 1px `#hf-placeholder` so the empty project renders; delete it when the first scene exists
   (QA check 1 fails otherwise, and no waiver covers it). Inputs: the
   basic-edit export (a proxy is fine) and its transcript (`npx hyperframes transcribe`).
2. **Beat grid.** Write `storyboard.md` (see Beat grid) from the transcript: every graphic with its kit name or catalogue ID, placement, beats, ease tokens and marks. Check density on the table with `python3 tools/cadence_scan.py videos/<slug>` (hook ≥ 60 %, body gaps ≤ 30 s, punch-ins don't count). The runner approves it.
3. **Capture.** Real screenshots or faithful recreations into `assets/captures/`, each recorded in
   `MANIFEST.md` (URL, UI mode, what's visible, caveats).
4. **Build.** Full-frame scenes as one reel (shared canvases where an argument spans face cut-ins);
   over-footage layouts as standalone transparent documents in `compositions/overlays/` (no `<template>`
   wrapper — each renders on its own with `-c`). Use `lib/kit` and the
   `camera` / `marks` / `text` primitives.
5. **Automated gate:** `python3 tools/qa.py videos/<slug>` (`standards/core/qa.md` §1).
6. **Critique loop** (`standards/core/qa.md` §2) — scores and fixes into `critique.md`.
7. **Preview pack → sign-off** by the runner: `python3 tools/preview_pack.py videos/<slug>` (`standards/core/qa.md` §3).
8. **Render and slice.** `npx hyperframes render videos/<slug> -o videos/<slug>/renders/reel.mp4`; each
   over-footage layout `npx hyperframes render videos/<slug> -c compositions/overlays/<name>.html --format=mov
   -o videos/<slug>/renders/overlays/<name>.mov`; then `python3 tools/slice.py videos/<slug> --reel
   videos/<slug>/renders/reel.mp4 --overlays videos/<slug>/renders/overlays`. Full-frame: silent MP4 clips +
   `TIMECODES.csv` + README. Over-footage: ProRes 4444 with alpha. Into `deliver/` (replaced atomically: built
   in a temp directory, swapped in only when every clip verifies), then the shared drive (media never goes
   into Git).
9. **Hand-off.** The editor places the clips on the timeline. Client videos: V1 via `client-ops`.
10. **Feedback.** Apply the promotion rule. Commit and push code and docs only.

## Shorts
1. **Intake** as above, with the vertical footage and the `captions` flag.
2. **Beat grid** with `python3 tools/probe_cuts.py <footage>`: scene ends land on the footage's own cuts
   (`standards/formats/shorts.md` §1).
3. **Capture** as above.
4. **Build** one composition over the footage.
5. **Automated gate.**
6. **Critique loop.**
7. **Preview pack → sign-off.**
8. **Render** one finished MP4 (`npx hyperframes render videos/<slug> -o videos/<slug>/deliver/<slug>.mp4`); hand off as above.
9. **Feedback** as above.

## Reference → style guide

To adopt a new look (a client's reference video, a new house variant), turn the reference into
rules before building:
1. Extract a frame every 0.5 s (plus 10 fps strips around every transition and camera move).
2. Write a style guide: palette (sampled hex), type, shot lengths, transition types, camera moves,
   texture/grain, how text enters and exits, recurring layouts.
3. Write the shot list / beat grid for the new video in that style, using real screenshots.
4. Take the grammar of the reference, never its content — no logos, characters, footage or copy.
5. Promote the result into `brands/<brand>/` (values) or `standards/` (technique), per the promotion
   rule. This is how `standards/formats/` and the custom catalogue were built.

## Git
Follow the sync rules in `CLAUDE.md`: pull at session start and before pushing; commit and push
only when asked; footage, audio and renders never go into Git.
