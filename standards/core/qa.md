# QA Gate

Three stages: an automated gate that blocks the render, an agent critique loop, then a human sign-off before delivery.
Run the automated gate with `python3 tools/qa.py videos/<slug>`: it prints PASS / FAIL (or SKIP /
WAIVED) for each of the ten checks below and writes `renders/qa-report.json`. It renders a draft
(`npx hyperframes render -q draft`) for checks 9–10 unless given `--render`, probes the live page
through `npx hyperframes preview` for checks 5, 6 and 10, and takes `--edit <cut.mp4>` to measure
density on the edited timeline as well as on the beat grid. Check 1 also fails while the scaffold's `#hf-placeholder`
is still in `index.html` once any scene exists. Density warnings (`cadence_scan`) and runtime-probe
warnings are printed in the report but do not fail a check on their own.

Each check runs in isolation: one that crashes or times out is reported FAIL (`internal error`), the
rest still run. The gate deletes the previous `renders/qa-report.json` when it starts, so a stale
report never survives a run that did not finish. Runtime-probe and render calls have timeouts and
raise named errors (not a hang). Check 10's flicker rule: a frame spike and a partner spike within
8 frames after which the picture returns to the frame before it (motion-aware: the return tolerance
grows with the scene's own movement), which flags glitch blocks but not staggered pop-ins. The standalone
`python3 tools/scan_flicker.py` also lists intended cuts. With `--edit`, density takes its face reference
from `--face-ref`, else the storyboard's face frames (outside the graphics rows ±0.5 s), else the
median of all frames, which prints a loud warning; over-footage rows count as `other` in edit mode.

## 1. Automated gate (blocks render)

| # | Check | Method |
|---|---|---|
| 1 | HyperFrames validity | `npx hyperframes check` |
| 2 | No lib fork | the project's `lib.lock` hashes equal root `lib/` |
| 3 | BRIEF complete | `format`, `brand` (status `approved`), `palette`, `font`, `captions` (Shorts), `film`, `direction` present; `python3 tools/brandcheck.py` passes and the palette/font/overrides choice is valid (`brandcheck.validate_choice`) |
| 4 | Seek-safety | static scan: no `Math.random`, `Date.now`, `repeat: -1`, CSS `infinite` animations |
| 5 | Blur law | every `feGaussianBlur` / `blur()` carries `data-blur-reason` = `focus`, `glow` or `wipe` (`wipe` only in Shorts: wipe feather and element smear); camera and whip blur only via `HFMotionBlur` |
| 6 | Easing vocabulary | no raw curves outside the named `ease.*` tokens |
| 7 | Captions | long-form: no caption layer except `kit.lower-third`; Shorts: matches the `captions` flag |
| 8 | Density | long-form: hook (first `hook_end` s, default 80) ≥ 60 % graphics, no face gap > 6 s, body gaps ≤ 30 s (face punch-ins are not graphics) (BRIEF `screen_share` ranges exempt); Shorts 35–55 % |
| 9 | Settle before cut | the last 0.3 s of each full-frame scene is still (frame difference) |
| 10 | Render traps | text verified in rendered frames, not only snapshots (`standards/formats/shorts.md` §9b traps apply to every format); seek-flicker scan |

**Exceptions:** declared in the BRIEF under `exceptions:`, each with a reason (e.g. a recreated UI
that has no real screenshot). The gate passes declared exceptions and lists them in the preview pack.
An entry `check <n>: <reason>` waives check n; `check <n> [<text>]: <reason>` waives only the findings
of check n that contain `<text>` as a whole path or word (`[a.html]` matches `compositions/a.html`, not
`data.html`). Any other entry (e.g. `F09: recreated Google Calendar — …`) is listed, not applied.
Infrastructure findings are never waivable — a waiver of their check still leaves them, so the check
fails: `runtime probe failed`, `draft render failed` / no frames / render unreadable, `static scan failed`,
`internal error` (a check that crashed, a tool missing or timed out) and the `#hf-placeholder` guard.

## 2. Critique loop (agent, before the human sees anything)

The agent that built the video reviews its own render and fixes what scores low. A good result
usually takes several rounds, not one shot.

1. Render the preview material: a contact sheet of every graphic, three full-res frames per graphic
   (entrance, mid, settled), and a 10 fps strip of every camera move.
2. Score **every graphic** 1–10 on six dimensions, each with one sentence of evidence:
   - **Smooth** — eases in and settles, holds before the cut, no snap, jitter or overshoot.
   - **On-brand** — ground mode, surfaces, headline treatment and marks match the brand and palette.
   - **Readable** — every word legible at phone size and normal speed; nothing cropped or ghosted.
   - **Synced** — lands on the words it illustrates (check against `transcript.json` times).
   - **Purposeful** — proves, structures or emphasises something; nothing from the ban list in
     `standards/core/motion.md`.
   - **Craft** — real UI detail, depth (backdrop, halo, focus), a micro-detail; not generic.
3. Fix every graphic scoring **below 8** on any dimension, re-render it, and re-score.
4. Stop when all scores are 8 or higher, or after **3 rounds**. Anything still below 8 is listed at
   the top of the preview pack for the runner.
5. Record every round's scores and fixes in `videos/<slug>/critique.md`.

## 3. Human review

1. **Preview pack** (`python3 tools/preview_pack.py videos/<slug>` → `renders/preview/index.html`): a contact sheet of every graphic, a draft render of the hook plus one body scene, the density timeline, the exceptions list, and the final critique scores (any graphic still below 8 first).
2. **Sign-off by whoever ran the build**, using these five questions. Tymek sees the final. Each
   question must be answerable by someone other than Tymek:
   1. **Smooth?** Moves ease in and settle; nothing snaps, jitters or overshoots; scenes hold still
      before they cut.
   2. **On-brand?** Ground, surfaces, headline treatment and marks match `brands/<brand>/brand.md`;
      colours come from the chosen palette.
   3. **Readable?** Every word on screen can be read at normal speed; nothing is cropped, ghosted or
      too small at phone size.
   4. **Synced?** Each graphic lands on the words it illustrates (see the transcript times).
   5. **Earns its place?** Each graphic explains, proves or emphasises something; roughly 80 %
      familiar (screenshot + highlight, whiteboard-style marks), 20 % custom brand moments.
3. Final render and delivery. Client videos then go to the client as V1 via `client-ops`.

**Promotion rule:** a review finding that changes how future videos should be made is written into
`standards/` or `brands/<brand>/` in the same session. Never only into a BRIEF or agent memory.
