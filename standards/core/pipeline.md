# Production Pipeline

Two production models, both built on real talking-head footage. Entry point: the
`contentporary-video` project skill (Plan 5). Until it exists, follow this file directly.

## Project layout (both formats)
```
videos/<slug>/  BRIEF.md · transcript.json · storyboard.md · assets/captures/MANIFEST.md
                compositions/ · lib/ + lib.lock · deliver/
```

## BRIEF fields
```yaml
format: long-form            # long-form | shorts
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

## Long-form
1. **Intake.** `tools/new-video` (Plan 3) scaffolds `videos/<slug>/` and syncs `lib/`. Inputs: the
   basic-edit export (a proxy is fine) and its transcript (`npx hyperframes transcribe`).
2. **Storyboard.** Map graphics to transcript timecodes: kit / device / custom, and placement mode
   (full-frame or over-footage). Check density on the plan before building (hook ≥ 60 %, body gaps
   ≤ 30 s). The runner approves the storyboard.
3. **Capture.** Real screenshots or faithful recreations into `assets/captures/`, each recorded in
   `MANIFEST.md` (URL, UI mode, what's visible, caveats).
4. **Build.** Full-frame scenes as one reel (shared canvases where an argument spans face cut-ins);
   over-footage layouts as separate transparent compositions. Use `lib/kit` and the
   `camera` / `marks` / `text` primitives.
5. **Automated gate** (`standards/core/qa.md` §1).
6. **Preview pack → sign-off** by the runner (`standards/core/qa.md` §2).
7. **Render and slice.** Full-frame: silent MP4 clips + `TIMECODES.csv` + README. Over-footage:
   ProRes 4444 with alpha. Into `deliver/`, then the shared drive (media never goes into Git).
8. **Hand-off.** The editor places the clips on the timeline. Client videos: V1 via `client-ops`.
9. **Feedback.** Apply the promotion rule. Commit and push code and docs only.

## Shorts
1. **Intake** as above, with the vertical footage and the `captions` flag.
2. **Storyboard** with `tools/probe-cuts`: scene ends land on the footage's own cuts
   (`standards/formats/shorts.md` §1).
3. **Capture** as above.
4. **Build** one composition over the footage.
5. **Automated gate.**
6. **Preview pack → sign-off.**
7. **Render** one finished MP4; hand off as above.
8. **Feedback** as above.

## Git
Follow the sync rules in `CLAUDE.md`: pull at session start and before pushing; commit and push
only when asked; footage, audio and renders never go into Git.
