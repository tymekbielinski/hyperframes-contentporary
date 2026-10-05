# Format Profile — Long-form

Applies to long-form videos (16:9, 1920×1080, 30 fps) for every brand. Inherits
`standards/core/motion.md`; supplies the long-form values. Source: frame-by-frame measurement of
Tymek's editor's After Effects video (youtube.com/watch?v=HrYMfy6MZtA) plus Tymek's corrections —
full numbers in the spec, Appendix A.

The quality bar is **smoothness**. Scenes may run long and need not be very dynamic.

## Placement modes
1. **Full-frame scenes** — the edit hard-cuts from the face to the graphic and back.
2. **Over-footage layouts** — lower third, side screen text, mini animations — animate on and off
   over the face.

## Graphic catalogue

| Kind | Types | Built with |
|---|---|---|
| Templated kit | full-screen title · subtitle / step card · lower third (key lines only) · side screen text (1–6 points) | `lib/kit` (see `## Kit` below); new variants per video allowed |
| Recurring devices | chapter roadmap · CTA template | `lib/kit` |
| Custom | screenshot-focus · diagram/flow · comparison split · proof clip · counter/odometer · mini animations | see `## Custom catalogue` below (A–D) |
| Screen recording | full-frame framed card on plain ground | graphics on top **only on request** |

- **Screenshot-focus:** a real (or faithfully recreated) UI card, sharp, on a blurred and dimmed
  backdrop of related UI; a one-line headline beneath; marks on top. The highlight block is usually
  the first beat after the card lands.
- **Chapter roadmap:** introduced once (the system name above a glowing path with numbered nodes);
  at each chapter the edit cuts back to it, the next step card docks onto its node, and the camera
  continues from its last pose.
- **CTA template:** the face scales to 0.80 into a YouTube watch-page player (≈ 0.5 s) → camera
  dives ≈ 2× to the description link → holds ≈ 1.7 s → reverses to the face. Every CTA in the video
  is identical; one may extend into website → booking page → glow title.
- **Proof clip:** client footage in a rounded card; the client's key words appear word by word,
  positive words marked in `status.ok` (text colour on dark ground, block/underline behind `text.primary` on light ground); a big figure lands at the end.

## Kit — `lib/kit`

Templated graphics and the two recurring devices are kit calls:
`HFKit.<component>(tl, host, { format: "long-form", at, … })` builds the layout inside `host` (a 1920×1080
box), adds its tweens to the scene's paused timeline and returns `{ dur, … }` (seconds from `at` until it has
settled). API and contract: `lib/README.md`. A brand picks one variant per component (`tokens.json` `kit`);
new variants are added to the shared kit and become available to every brand.

| Component | Variant | Placement | Layout (1920×1080) | Motion |
|---|---|---|---|---|
| `HFKit.title` | `glow-center` | full-frame | one centred line, 104 px (9.6 % H), warm ambient top glow; optional scribble underline under one word (`underline: <word index>`, measured with `HFText.measureWidth`, so it also builds inside a `display:none` scene) | glow title (pop 70 %, settle 0.4 s `ease.glow`, +430 ms per word); underline one chain gap after it settles (`ease.sweep`) |
| `HFKit.subtitle` | `glass-pill-script` | full-frame | glass pill ≥ 770 px (40 % W) centred on the grid ground; script kicker 72 px (6.7 % H) over the title, 92 px (8.5 % H), in `accent.text` | card entrance (0.43 s `ease.card`) → script write-on at +0.3 s (135 ms/letter) → glow title one chain gap later |
| `HFKit.lowerThird` | `key-line` | over-footage | one key line, 50 px (4.6 % H) body font, centred, baseline ≈ 95 % H; one white → `accent.text` gradient across the line | word entrance; fades out (0.43 s `ease.enter`), gone at `out` |
| `HFKit.sideText` | `grid-panel-chips` | over-footage | grid panel 0–928 px (48 % W); 90 px glass number chips at x 115, rows every 145 px from y 140; labels 48 px (4.4 % H) at x 277, one line each (620 px wide, no wrap); 1–6 points; the face stays on the right | panel slides 80 px + fades (0.6 s `ease.enter`); each point = status chip + its label word by word 0.1 s later, one point every two chain gaps unless each `items[i].at` is given |
| `HFKit.ctaYoutube` | `watch-page-dive` | full-frame, transforms the footage | the face footage inside the player rect of a real watch-page screenshot (`page: {src, width, height, player, link}`; both rects in page pixels and inside the page, else a named error) | scale to 0.80 (0.5 s) → hold 0.5 s → dive 2× onto the link (0.6 s) → hold 1.7 s → back (0.6 s) → hold 0.5 s → face (0.5 s): 4.9 s, all `ease.camera`; a DOM camera, no motion blur on the dive |
| `HFKit.roadmap` | `wave-nodes` | full-frame | system name (92 px caps, wraps within 1300 px, two lines for a long name) above a glowing wavy path that runs 400 px past both ends of the world, so its ends never show; numbered nodes every 640 px (3–6 steps); 250×290 icon cards docked on their nodes | `visit: 0` intro: title word by word, path draws 1.2 s `ease.sweep`, each node pops (0.48 s `ease.enter`) as the line reaches it; `visit: k`: opens on visit k−1's end state, card k docks (card entrance), camera travels 1.6 s `ease.camera` to card k at 1.8× (the card reads ≈ 450 px on screen) |

**Light ground** (`mode: light`): every component drops its glow — titles in dark `text.primary` (word
entrance), the subtitle's title on an `accent.block` marker, the lower third on a frosted white pill, a
frosted white side panel and chips, the roadmap path without bloom. Every component reads `data-hf-mode`
from its nearest ancestor and throws when there is none.

**Over-footage layouts** (lower third, side text) are standalone documents in `compositions/overlays/`: no
`<template>`, their own `data-hf-mode` on the root, root-relative paths (`lib/kit/…`,
`compositions/brand.css`), rendered with `-c … --format=mov`. Never give a kit element an id or class
containing `caption` (QA check 7).

## Custom catalogue

Built per moment from `camera` / `marks` / `text` primitives, in the chosen palette (dark or light
ground). Measured from 6 of Tymek's editor-animated videos plus the reference
(`docs/research/2026-10-03-custom-animation-catalogue.md`). Pick the simplest type that proves the
point: A and B first, C for structure, D when the face should stay on screen.

Evidence for every ID (and every kit component) — reference stills, measured ranges and a quality bar —
is in `references/patterns/<ID>.md`; look at it before building the pattern.

**A. Proof on real UI**

| ID | Type | Layout and motion | Use for |
|---|---|---|---|
| A1 | Screenshot focus + highlight | sharp card ≈ 55–60 % W on a blurred, faded copy (≈ 35 %) of the same screenshot; enters 0.9 → 1 with blur→sharp over 0.25 s; highlight/marker sweeps 0.3 s after landing; optional key-text recolour; hold 0.6–1 s | a claim or quote that is real |
| A2 | Screenshot camera pass | page at 150–250 % (flat) or tilted ≤ 60° in 3D (a tilt, never a flip); 2–3 camera legs ≈ 2 s with readable stops; marks land at the stops; optional synthetic cursor arriving 0.3 s before its mark; may end dimmed and hand off to B1 | prices, pages, tools, long documents |
| A3 | Counter on screenshot | push-in ≈ 0.8 s; the real number counts with deceleration (odometer, `ease.enter`); underline under its label | growth numbers |
| A4 | Proof clip in framed card | rounded card ≈ 56 % W pushing to ≈ 72 %; the client's own words appear word by word beneath (positive words marked in `status.ok`: text colour on dark ground, block/underline behind `text.primary` on light ground); big figure lands at the end | client results |
| A5 | Case-study card stack | centred card ≈ 55–62 % W, 1–2 cards peeking behind; ≈ 1 s per card; the front card steps away (3D tilt, never a flip) to reveal the next; metric chip per card | several results in a row |
| A6 | Channel flash montage | blurred channel pages 0.7–1.3 s each, hard cuts inside one montage scene (the scene's rhythm, not a transition) | breadth of proof |

**B. Headline scenes**

| ID | Type | Layout and motion | Use for |
|---|---|---|---|
| B1 | Backdrop headline | a screenshot or clip appears sharp ≈ 1 s, then dims to ≈ 15 % and blurs (0.5 s, `focus`); a 1–2 line headline builds word by word; an underline/marker lands on the emphasis phrase — red/accent = problem, `status.ok` = positive; list variant adds a bullet ≈ every 1.3 s | the house device for a key line |
| B2 | Headline + labelled callouts | headline mid-frame; 3 callouts in a triangle, each a curved arrow then an icon (real logo or brand icon) + script label, 0.75–1.2 s apart | a method with named parts |
| B3 | Big stat / counter title | a huge number counts up (≈ 1.2–1.4 s) — ghost word behind it, or over the source clip / a cutout; hand-drawn arrow + script subtitle | the one number to remember |
| B4 | Punch word | a single word full-frame on a vignette | a hard "no" / turn |

**C. Diagram canvases** — usually one persistent canvas the face cuts into; on return it resumes

| ID | Type | Layout and motion | Use for |
|---|---|---|---|
| C1 | Flow strip | A → dashed line (swap glyph or arrow) → B, icons ≈ 12 % W; caption word by word; canvas pans as nodes arrive | substitution, cause → effect |
| C2 | Tree | vertical tree; connectors draw top → bottom; camera glides down 2–3 s or tours column by column | comparison, org, formula |
| C3 | Funnel / bands | 3-band shape builds; camera steps band to band; bullets per band | funnels, tiers |
| C4 | Orbit / flywheel | nodes on a ring around a title; camera visits each node while a dashed segment draws to the next; pull back | loops, systems |
| C5 | Card roster | 3–4 glass or tinted cards ("#n" script labels or coloured tiles); camera pushes into one card, its bullets type one per spoken phrase (≈ 2.5–3 s), then pans to the next | numbered lists, components |
| C6 | Range line / annotated chart | line with two dots, colour shifts from `status.x` to `status.ok` as labels land; charts take a strike-through mark | ranges, before/after |
| C7 | Avatar + escalating ticker | avatar on a vertical line; a chip slides out; the number jumps odometer-style; camera lifts up the line | costs or results climbing |
| C8 | Focus card, dim siblings | one card ≈ 38 % W, neighbours ≈ 20 % opacity + blur (`focus`), ✕/✓ badge | picking one option |

**D. Mini animations over the face** — the face stays visible; animate on and off over the footage

| ID | Type | Layout and motion | Use for |
|---|---|---|---|
| D1 | Tiles flanking the face | glass tiles at ≈ 9–38 % and 62–91 % of frame width (real logo or sourced 3D icon + label/stat, ✕/✓), 0.7 s apart | platforms, two numbers |
| D2 | Side screenshot + script + highlight | screenshot on the empty side (≈ 60 % W) with an alpha fade toward the face; script word + words build; `accent.block` wipes behind the key phrase | a claim with its proof |
| D3 | Caption bar | semi-transparent bar fading at its outer edge, `status.ok` or `status.x` tint, upper corner; face punched in to clear it | a positive/negative claim |
| D4 | Tool chip stack | 2–4 stacked glass pills with app logos, one after another; may hand off to the CTA | tools, deliverables |
| D5 | Name lower third | script first name + bold surname + curved arrow, beside the speaker, ≈ 2.7 s | introductions |

Recurring across all types: real screenshots as proof (often over a blurred copy of themselves),
word-by-word text, meaning-coded emphasis colour, a script accent word, hand-drawn marks, camera stops
where marks land. 3D icons and a synthetic cursor are allowed when sourced from a real asset
(record them in `assets/captures/MANIFEST.md`).

## Section formats

Recorded sections are not built in this pipeline. Treat them like screen-share: declare their ranges in
the BRIEF under `screen_share`, they are exempt from the cadence rule, and graphics go on top only on
request. They carry IDs so reference analysis can tag them:

| ID | Type | Notes | Use for |
|---|---|---|---|
| E1 | Board walkthrough + face PiP | recorded Miro board; PiP ≈ 25 % W bottom-right, rounded, soft shadow; zoom out to overview between sections | long structured walkthroughs |
| E2 | Slide deck + round face-cam | recorded slides; face circle ≈ 17 % W bottom-right | lecture-style sections |

## Sound

Graphics are **silent** and timed to speech. The editor owns music and sound effects; nothing is
scored to a beat grid here.

## Density
- **Hook (first `hook_end` seconds, default 80 — set in the BRIEF):** ≥ 60 % graphics (reference: 71 %), and no face-only gap > 6 s.
- **Body:** at least one graphic, even a short one, every ≤ 30 s. Ranges declared as
  screen-share in the BRIEF are exempt. Face punch-ins do not count as graphics.
- Scenes run 2–18 s (median ≈ 6 s). Long scenes are chains of 3–5 beats joined by camera travel,
  not one static layout.
- **Shared canvas:** a long argument is one composition the face cuts into (2–6 s cut-ins). On
  return, the canvas is where it would have been had it kept running.

## Motion values

| Token | Value |
|---|---|
| `ease.camera` | `cubic-bezier(0.32, 0, 0.18, 1)` — short ease-in, peak velocity ≈ 28 % into the move, long settle |
| `ease.camera.slow` | `sine.inOut` — emphasis pushes only, avg 3–4.5 %/s over 2–5 s |
| `ease.enter` | `power3.out` |
| `ease.sweep` | `cubic-bezier(0.47, 0.15, 0.2, 0.95)`, ≈ 360 px/s at 720p (0.5 s short, 1.0 s long, thin seed for the first ≈ 4 frames) |
| `ease.cut` | whip: `ease.camera` over 0.45–0.8 s |
| `ease.glow` | `expo.out` — glow title settle |
| `ease.card` | `power2.out` — card entrance (measured, Appendix A) |
| camera leg | 1.1–2.5 s; peak 0.75–1.2 frame-widths/s; drifts 3.5–4.5 s, peak 0.1–0.3 fw/s |
| zoom | push/pull avg 5–16 %/s (peak 18–64 %/s) over 1.6–4 s |
| hold | 0.2–4 s; creep ≤ 0.5 %/s |
| word entrance | rise ≈ 7 % of frame height + fade + blur→sharp (`focus`), 0.6 s `ease.enter`, stagger 230–330 ms; word by word, never per character |
| glow title | pops to ≈ 70 % brightness, settles 0.4 s `ease.glow`, no scale; halo 60–90 px at 1080p; next word +430 ms; background rack-defocuses behind it; dark ground only — on the light ground titles take no glow: dark `text.primary` with a scribble underline or marker (`accent.block`) |
| card entrance | rise 35–40 px at 720p, 0.43 s `ease.card`, brightens and sharpens |
| chain gap | 450–500 ms between linked beats; peer sets (e.g. three ✕ chips) land together |
| odometer | `ease.enter`, 2.2–7 s, lands on the spoken number |
| motion blur | directional `HFMotionBlur`, shutter per move: ordinary legs 90° (`HFMotionBlur.profilePreset("long-form", "leg")`, reads as ≈ none); whips 180° (`"whip"`); odometer digit roll 144° (`"roll"`) |
| backdrop defocus | blur σ ≈ 4.5 px at 1080p + brightness → 0.6 over 0.5 s, front-loaded (`focus`) |
| screenshots | axis-aligned in bordered cards; dark ground: light halo, no dark drop shadow; light ground: soft neutral shadow from `surface.halo` |

**Ground mode.** Every glow in this profile (glow title, glowing roadmap path, title halos) applies to the dark ground. On a light-ground palette (`mode: light`) glow is replaced by marks: dark `text.primary`, scribble underline, marker or tag block — see `brands/<brand>/brand.md`.

**Not used in long-form:** light leaks, masked wipes, dissolves/crossfades, overshoot.

## Captions
None. Spoken words appear on screen only as a **lower third for key lines** (`kit.lower-third`).
Proof-clip words are the client's quote, not captions.

## Delivery
- **Full-frame scenes:** silent MP4 clips (1920×1080, 30 fps) named by timeline timecode, plus
  `TIMECODES.csv` and a README for the editor.
- **Over-footage layouts:** ProRes 4444 with alpha (`npx hyperframes render --format=mov`).
- `python3 tools/slice.py videos/<slug> --reel <reel.mp4> --overlays <dir>` cuts the clips frame-exact,
  verifies the overlays and writes `TIMECODES.csv` + `README.txt` into `deliver/`.
- Hand-off to the shared drive; media never goes into Git.

## Checklist (run with `standards/core/qa.md`)
- [ ] Hook ≥ 60 % graphics, no face gap > 6 s; body gaps ≤ 30 s (screen-share exempt; punch-ins do not count)
- [ ] Every motion uses a named `ease.*` token; no overshoot
- [ ] Camera moves → holds → moves; each full-frame scene is still for its last 0.3–1 s
- [ ] Words land on their spoken word; cards lead their phrase by 0.3–0.5 s
- [ ] No captions except key-line lower thirds
- [ ] All CTAs use the identical `cta-youtube` treatment
- [ ] Colours and fonts come from the brand palette/font chosen in the BRIEF (plus declared overrides)
