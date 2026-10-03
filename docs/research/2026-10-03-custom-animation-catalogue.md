# Custom Animation Catalogue — research findings (draft, not yet a standard)

**Date:** 2026-10-03 · **Source:** frame-by-frame analysis of 6 long-form videos animated by
Tymek's editor in After Effects, plus the measured reference video (HrYMfy6MZtA, see spec Appendix A).
Per-video logs and representative frames live in the session scratchpad (not in Git).

| Video | Length | Graphics | Hook (0–80 s) | Longest gap | Ground |
|---|---|---|---|---|---|
| ULTRA predictable funnel (reference) | 597 s | ≈ 29 % | 71 % | 98 s | dark |
| I Spent $10,000 on Mentors | 746 s | 31.5 % | ≈ 55 % | 165 s | dark |
| How Alex Hormozi creates 100 posts | 753 s | 77 %* | 65 % | 69 s | dark |
| How Instantly Built a $1M ARR channel (client topic) | 1089 s | 96 %* | 80 % | 29 s (outro) | dark |
| Liam Ottley $540k/mo | 601 s | 23 % | ≈ 45 % | 104 s | **light** |
| The Problem With Clay.com | 641 s | 36 % | 55 % | 130 s | **light** |
| The Stupidly Simple YouTube Strategy | 533 s | 57 % | 75 % | 24 s | **light** |

\* Body is a section format, not animation: Hormozi = screen-recorded HTML slide deck with a round
face-cam (67 % of runtime); Instantly = screen-recorded Miro board walkthrough with face PiP (92 %).

## Universal patterns (present in every or nearly every video)
1. **Hard cut** face ↔ full-frame graphic (≈ 98 % of boundaries). Graphic → graphic changes happen
   only as camera travel on one canvas.
2. **Persistent canvas with face cut-ins that resume** — persona tree, flywheel (Ottley), agent
   roster (Clay), funnel + card carousel (Mentors), formula tree (reference).
3. **Real screenshots are the proof** — 50 %+ of graphics, usually with a **blurred, dimmed copy of
   the same screenshot as the backdrop** behind the sharp focus element.
4. **Text builds word by word** (≈ 0.12–0.33 s/word, blur tail), synced to speech.
5. **Emphasis is colour-coded by meaning:** red/coral underline or marker = problem / key phrase;
   lime/green = positive result. Highlight block or marker behind the key stat.
6. **Script accent word** in a signature/brush script on most headlines.
7. **Hand-drawn marks:** scribble underline, curved arrow, ellipse/circle, strike-through, ✕/✓.
8. **Smooth camera:** legs ≈ 0.6–4 s with short ease-in + long settle, readable stop, marks land at
   the stops; screenshots blurred while moving, sharp on settle.
9. Face footage **punches in/out between 2–3 crops every 3–20 s** (carries long graphic-free stretches).

## Catalogue (merged across videos; counts = uses across the 6 + reference)

### A. Proof on real UI
| # | Type | Layout & motion | Seen in |
|---|---|---|---|
| A1 | **Screenshot focus + highlight** | sharp card ~55–60 % W on blurred/faded copy (~35 %); pop-in 0.9→1 + blur-in 0.25 s; marker/highlight sweeps L→R 0.3 s after landing; optional red text recolour; hold 0.6–1 s | Clay 3, Instantly 3, reference, Ottley |
| A2 | **Screenshot camera pass** | page at 150–250 % (flat) or tilted 45–60° in 3D; 2–3 legs ≈ 2 s each; optional synthetic cursor arriving 0.3 s before the mark draws; may end dimmed → hands off to a backdrop headline | Ottley 6, Clay 5, Simple 5, Mentors 4+2, Instantly 2, Hormozi 2 |
| A3 | **Counter on screenshot** | push-in ≈ 0.8 s; count decelerates (7 steps / 1.75 s, or odometer ~1 s per jump); red underline under the label | Instantly, Clay, Simple, reference, Hormozi |
| A4 | **Proof clip in framed card** | rounded card ~56 % W pushing to ~72 %; client's words word-by-word under it (positive words green); optional inset YouTube card; big figure lands at the end | Simple 8, reference, Mentors |
| A5 | **Case-study card stack / carousel** | centred card ~55–62 % W with 1–2 ghosts behind; ~1 s per card; swap by 3D tilt/rotate burst or arrow click; metric chip/highlight per card | Hormozi 3, Instantly 1, Clay 1 |
| A6 | **Channel flash montage** | blurred channel pages 0.7–1.3 s each, hard-cut back to back | Hormozi 3 |

### B. Headline scenes
| # | Type | Layout & motion | Seen in |
|---|---|---|---|
| B1 | **Backdrop headline** | screenshot/clip sharp ~1 s → dims to ~15 % + blur (0.5 s) → 1–2 line headline types word by word → underline/marker on the emphasis phrase (colour = meaning); list variant adds a bullet every ~1.3 s | Mentors 6, Clay 5, Simple 5, Instantly 3, reference |
| B2 | **Headline + labelled callouts** | headline mid-frame; 3 callouts in a triangle, each = curved arrow then icon + script label, 0.75–1.2 s apart; backdrop drifts | Instantly 1, reference |
| B3 | **Big stat / counter title** | huge number counts up (≈ 1.2–1.4 s) — ghost word behind, falling bills, glow, or over the source clip / a cutout; hand-drawn arrow + script subtitle | Mentors, Hormozi, Simple, Ottley, reference |
| B4 | **Punch word** | single word full-frame on a dark vignette | Simple |

### C. Diagram canvases (usually persistent, camera tours, resume after face cut-ins)
| # | Type | Layout & motion | Seen in |
|---|---|---|---|
| C1 | **Flow strip** | A → (dashed line, swap glyph / arrow) → B, icons ~12 % W; caption word-by-word; canvas pans as nodes arrive | Clay, Hormozi, Ottley, reference |
| C2 | **Tree** (comparison / org / formula) | vertical tree, connectors draw top→bottom, camera glides down 2–3 s, column-by-column tour | Clay, Ottley, reference |
| C3 | **Funnel / band diagram** | 3-band trapezoid builds, camera steps band to band, bullets per layer | Mentors |
| C4 | **Orbit / flywheel / ring** | nodes on a ring around a title; camera visits each node, dashed segment draws to the next, pull back | Ottley, Simple |
| C5 | **Card roster with typed bullets** | 3–4 glass/tinted cards (numbered "#n" script labels or coloured tiles); camera pushes into one card, bullets type per spoken phrase (~2.5–3 s each), pans to next | Mentors, Clay 3, Simple 4 ("SECRET #n"), Instantly 1 |
| C6 | **Range line / annotated chart** | line with two dots, colour fades red→green as labels land; chart with strike-through | Mentors, Simple |
| C7 | **Avatar + escalating ticker** | avatar on a vertical line, chip slides out, odometer jumps, camera lifts up the line | Clay |
| C8 | **Focus card, dim siblings** | one plan card ~38 % W, neighbours ~20 % opacity + blur, ✕ badge pops | Clay |

### D. Mini animations over the face (custom)
| # | Type | Layout & motion | Seen in |
|---|---|---|---|
| D1 | **Tiles flanking the face** | glass tiles at ~9–38 % and ~62–91 % W (logo/3D icon + label/stat, ✕ or ✓), pop in ~0.7 s apart | Mentors, template stills ($46.2M, $200M) |
| D2 | **Side screenshot + script + highlight block** | screenshot on left ~60 % with alpha fade to the right/bottom; script word + white words build; lime block wipes behind the key phrase; fades out with no cut | Hormozi, template still 7 |
| D3 | **Caption bar** | semi-transparent bar fading at its outer edge, green (positive) / red (negative), upper-left or upper-right, face punched in to clear it | Mentors 2 |
| D4 | **Tool chip stack** | 3 stacked glass pills with app logos pop in one after another; can hand off to the CTA | Mentors, Clay (over blurred footage) |
| D5 | **Name lower third** | script first name + bold surname + curved arrow, bottom-right over the shirt, ~2.7 s | Clay |

### E. Section formats (not animation — recorded)
| # | Type | Notes | Seen in |
|---|---|---|---|
| E1 | **Board walkthrough + face PiP** | Miro board recorded; PiP ≈ 25 % W bottom-right, rounded 10 px, soft shadow; section changes = zoom out to overview, zoom in; pen marks follow speech | Instantly (92 %) |
| E2 | **Slide deck + round face-cam** | static HTML slides, face circle ~17 % W bottom-right; 8 slide layouts | Hormozi (67 %) |

## Templated kit, as actually used
- **CTA** in every video; often at the **end of the hook** (50–64 s) as well as later/outro; variants:
  booking page rising from below, calendar sliding over the face.
- **Full-screen title** used mostly *inside* custom scenes (over a blurred backdrop); light-ground
  variant = dark text + red scribble underline or white on a coral block, no glow.
- **Chapter roadmap** in 2 of 7 (reference, Mentors — Mentors variant zooms out into a branching tree).
- **Lower third** rare (Clay name tag; Simple word-by-word captions on a punched-in face).
- **Subtitle/step card, side screen text**: not seen in these 6.

## Findings that conflict with the current standard (need Tymek's decision)
1. **Light ground is a real second look** (3 of 7 videos: silver/white radial, frosted white glass,
   dark text without glow). `brands/contentporary/brand.md` currently says the ground is always dark
   and lists "pure-white grounds in long-form" under *Never*.
2. **Section formats** (E1, E2) make up most of two videos and aren't covered by the pipeline.
3. **Density:** only 1 of 7 videos meets the ≤ 30 s body cadence; gaps of 69–165 s are common and are
   carried by face punch-ins. The rule is intentionally stricter — confirm whether punch-ins count.
4. **3D icons** (clay-style mascots, glowing 3D app icons) and a **synthetic cursor** recur but have no
   asset source or rule yet.
