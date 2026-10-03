# Standard Animation Workflow — Design Spec

**Date:** 2026-10-03 · **Author:** Tymek Bieliński (decisions) with Claude (analysis, drafting)
**Status:** Draft for review — not yet committed, not yet implemented.
**Repo:** `tymekbielinski/hyperframes-contentporary` (`main`)

## 1. Goal

One animation workflow for every YouTube video Contentporary produces — its own channel and every
client — so that AI-built (HyperFrames) graphics reach the quality of Tymek's editor's After Effects
work, consistently, from the first video to the hundredth.

Success means:
- Any team member can run a video through the pipeline and get on-brand, smooth graphics without
  Tymek reviewing it.
- A new client is onboarded by filling one brand folder, not by forking motion rules.
- Motion technique (blur, camera, easing, QA) is identical across all brands and cannot drift
  per project.

## 2. Scope

**In:** two production models, both built on real talking-head footage:
1. **Shorts recut** — graphics on vertical footage, rendered as one finished MP4.
2. **Long-form scene clips** — graphics delivered as clips for the editor to place on the
   basic-edit timeline.

**Out:** TTS / faceless videos, SaaS product-demo videos, and anything not built on footage.
**Deferred (separate follow-ups, layered onto this structure later):**
- Custom-animation layouts, learned from more reference videos Tymek will share.
- Techniques from the "great animations with Opus 5.5" video (link not yet shared).

## 3. Problems this fixes (inventory findings)

- The docs describe a TTS-narrated product; every real project is graphics-on-footage
  (`PIPELINE.md`, `voice.md`, `templates/script-template.md` vs. `videos/*`).
- Contradictory "universal" rules: idle motion (motion-craft §1/§8 vs. design-system §9),
  transitions (dissolves vs. hard cuts vs. masked wipe), the Gaussian ban vs. design-system's own
  Gaussian wipe, three competing "house" eases, conflicting chain gaps and word rates, three
  different caption rules.
- Contentporary brand values (hex, fonts, marks, pillars) are loaded for every video, so there is
  no way to do client work.
- Code drift: three forks of `motion-blur.js`; two parallel engines (`house.js` in video 09, an
  inline prelude copy-pasted across the Shorts); dead lib copies; old violations spreading via
  reuse (card-06).
- Rules living outside the repo (agent memory, BRIEFs) — e.g. video 09's real look.
- Stale references: `../CLAUDE.md` (missing), `scripts/`, `context/assets/`, "frame.md has
  placeholders only".
- No defined client onboarding, QA gate, delivery spec, or cadence rule.

## 4. Architecture

Three layers of rules, one shared code library, one entry point.

```
.claude/skills/contentporary-video/   entry point (project skill, in git)
standards/
  core/      motion.md · qa.md · pipeline.md            — every brand, every format
  formats/   long-form.md · shorts.md                  — every brand, per format
brands/
  _template/                                          — client onboarding starts here
  contentporary/                                      — first brand instance
lib/         shared motion code, styled only by tokens  — every brand, every format
tools/       sync-lib · new-video · probe-cuts · cadence-scan · slice · scan-flicker
videos/<slug>/                                         — one project per video
```

**Precedence:** core → format profile → brand → video BRIEF. A lower layer supplies *values*
(colours, fonts, timings the upper layer delegates); it never overrides a rule of the layer above.
Brands never touch motion technique. BRIEF exceptions are allowed only through the declared
`exceptions:` mechanism (§8a).

## 5. Core motion law — `standards/core/motion.md`

Applies to every brand and format. Replaces `context/motion-craft.md` and the brand-agnostic half
of `context/design-system.md`.

1. **Seek-safe or it doesn't ship.** One paused timeline; no randomness; no infinite repeats;
   animate transform / opacity / filter only. (Existing HyperFrames contract.)
2. **Move → hold → move.** Elements travel, settle, then rest. During a hold the camera may creep
   at most 0.5 %/s, unless the format profile sets a hold-push rate. No "bed never stops", no mandatory idles.
3. **No overshoot by default.** No bounce / elastic / back.out unless a format profile names the
   exception.
4. **Named easing vocabulary.** All motion uses `ease.camera`, `ease.enter`, `ease.sweep`,
   `ease.cut` (+ profile-defined extras). Values are set by the format profile. No ad-hoc curves.
5. **Blur law.**
   - Blur that represents *movement* (camera legs, whips, fast element travel of static content,
     odometer digit roll) uses `HFMotionBlur` — directional, with the shutter set by the format
     profile. `HFMotionBlur` cannot texture an element whose own content is animating while it
     moves; that element-level smear may use a directional Gaussian only in Shorts, tagged `wipe`
     (in long-form such an element moves without smear).
   - Gaussian blur is allowed only for non-motion purposes: focus/defocus (backdrop rack-defocus,
     word blur→sharp entrance), glow/bloom, and — Shorts only — the wipe feather and element smear (`wipe`, named exception).
6. **Sync to speech.** Elements land on their word (lead 0–0.3 s); cards/nodes lead their phrase
   by 0.3–0.5 s; cuts land on the key word ±0.1 s. On-screen text may paraphrase speech.
7. **Footage ↔ full-frame graphic is a hard cut.** Transitions happen inside graphics as camera
   travel through one world. Over-footage layouts (lower third, side text, mini) animate on/off
   over the footage. The long-form CTA template is the one other exception: it transforms the
   footage itself (scale into a player and back) instead of cutting.
8. **Settle, then hold** 0.3–1 s before a full-frame graphic cuts out.
9. **Credibility.** UI is a real screenshot or a faithful recreation of a real platform (e.g. the
   dark YouTube watch page). Diagrams, data and illustration are free. Invented UI posing as real
   is not allowed.
10. **Two-pass build.** Lay out first, then annotate with marks. Which marks and which colours
    come from the brand.

Deliberately **not** in core: timings, colours, fonts, text-reveal mode, density.

## 6. Format profiles

### 6a. Long-form — `standards/formats/long-form.md`

Source: frame-by-frame measurement of Tymek's editor's AE video "How to build ULTRA predictable
Youtube Sales Funnel for B2B High-Ticket Offer" (youtube.com/watch?v=HrYMfy6MZtA), plus Tymek's
corrections and template stills. Measured data: Appendix A.

**Placement modes:** (1) full-frame scenes, hard-cut from the face; (2) over-footage layouts —
lower third, side screen text, mini animations — animating on/off over the face.

**Graphic catalogue:**

| Kind | Types | Built with |
|---|---|---|
| Templated kit | full-screen title · subtitle / step card · lower third (key lines only) · side screen text (1–6 points) | `lib/kit`; new variants per video allowed |
| Recurring devices | chapter roadmap · CTA template | `lib/kit` |
| Custom | screenshot-focus · diagram/flow · comparison split · proof clip · counter/odometer · mini animations | core + brand primitives (`camera`/`marks`/`text`) |
| Screen recording | full-frame framed card on plain ground | graphics on top **only on request** |

- **Chapter roadmap:** introduced once; revisited at each chapter; the camera continues from its
  last pose and docks the next step card.
- **CTA template:** the face scales to 0.80 into a YouTube watch-page player (≈0.5 s) → camera
  dives ≈2× to the description link → holds ≈1.7 s → reverses to the face. Repeated identically;
  one instance may extend into website → booking → glow title.

**Density:**
- **Hook (first `hook_end` s, default 80 — BRIEF field):** ≥ 60 % graphics (reference: 71 %), no face-only gap > 6 s.
- **Body:** at least one graphic (even short) every ≤ 30 s. Screen-share ranges are exempt.
- Scenes 2–18 s, median ≈ 6 s; long scenes are chains of 3–5 beats joined by camera travel.
- **Shared canvas:** a long argument is one composition the face cuts into; on return it resumes
  where it would have been.

**Motion values:**

| Token | Value |
|---|---|
| `ease.camera` | `cubic-bezier(0.32, 0, 0.18, 1)` (peak velocity ≈ 28 % into the move) |
| `ease.camera.slow` | `sine.inOut` — emphasis pushes only, avg 3–4.5 %/s over 2–5 s |
| `ease.enter` | `power3.out` |
| `ease.sweep` | `cubic-bezier(0.47, 0.15, 0.2, 0.95)`, ≈ 360 px/s @720p (0.5–1.0 s) |
| `ease.cut` | whip: `ease.camera` over 0.45–0.8 s |
| `ease.glow` | `expo.out` — glow title settle |
| `ease.card` | `power2.out` — card entrance (measured, Appendix A) |
| camera leg | 1.1–2.5 s; peak 0.75–1.2 frame-widths/s; drifts 3.5–4.5 s, peak 0.1–0.3 fw/s |
| zoom | avg 5–16 %/s, peak 18–64 %/s |
| hold | 0.2–4 s, creep ≤ 0.5 %/s |
| word entrance | rise ≈ 7 % frame height + fade + blur→sharp, 0.6 s, stagger 230–330 ms; word-level only |
| glow title | pop to ≈ 70 %, settle 0.4 s `ease.glow`, no scale; halo 60–90 px @1080; next word +430 ms |
| chain gap | 450–500 ms; peer sets land together |
| motion blur | ordinary legs ≈ none (shutter ≤ 90°); whips ≈ 180° directional `HFMotionBlur` |
| backdrop defocus | blur σ ≈ 4.5 px @1080 + brightness → 0.6 over 0.5 s, front-loaded |
| screenshots | axis-aligned in bordered cards; light halo, no dark drop shadow |
| not used | light leaks, wipes, dissolves |

**Captions:** none. Spoken words appear only as a **lower third for key lines**.

**Delivery:** full-frame scenes → silent MP4 clips named by timeline timecode + `TIMECODES.csv` +
README. Over-footage layouts → ProRes 4444 with alpha (`hyperframes render --format=mov`).

### 6b. Shorts — `standards/formats/shorts.md`

Mostly `context/design-system.md` §1, §6–§8, moved unchanged:
- Full-frame only — no overlays on the face. ≈ 45 % graphics (QA band 35–55 %); scenes 1.4–8.8 s; scene ends land
  on the footage's own cuts (`probe-cuts`, scene threshold 0.20; end = source cut + exit duration).
- Masked motion-blurred wipe: `cubic-bezier(0.65, 0, 0.35, 1)`, 0.42 s in / 0.36 s out,
  Gaussian feather as the named exception.
- Easing tokens: `ease.camera` and `ease.cut` = `cubic-bezier(0.65, 0, 0.35, 1)`; `ease.enter` =
  `power3.out` (provisional, not measured); `ease.sweep` = `cubic-bezier(0.47, 0.15, 0.2, 0.95)`
  (provisional, from long-form). Hold push ≈ 3.4 %/s is the profile hold-push rate.
- Punchy timings: chips seed → expand; type-on ≈ 67 ms/char; peers 125 ms; chained beats
  300–630 ms; global recolour 133 ms; hold push ≈ 3.4 %/s (profile rate, overrides core creep cap); taller multi-phase camera worlds.
- Captions per project (flag in BRIEF). If the footage already carries them, never re-add.
- Delivery: one finished MP4.
- §8c motion-blur numbers rewritten for any aspect ratio (no hard-coded 1080×1920).

## 7. Brands — `brands/<name>/`

A brand supplies values and assets, never motion.

```
brands/<name>/
  brand.md       constant visual language (prose, read by Claude)
  tokens.json    machine-readable values → CSS variables via lib/brand.js
  palettes/      named palettes (e.g. red.json, gold.json, lime.json)
  assets/        logo, font sources/licences, MANIFEST.md (provenance)
  narrative.md   CTA destination + link, offer, pillars, tone
```

**Palette roles** (every palette fills every slot): `ground` (deep, lit centre, grid, dots),
`surface` (glass fill, bevel, halo), `text` (primary, secondary), `accent` (highlight block,
keywords, connectors, title glow), `accentScript` (handwriting), `status.ok`, `status.x`.

**Per-video choices** (in the BRIEF): `palette:` (one of the brand's palettes), optional one-off
overrides (e.g. `accentScript: "#BACE7A"`), and `font:` (one of the brand's allowed headline
fonts).

**Kit variants:** variants live in shared `lib/kit/`, styled only by tokens. A brand lists its
default variant per component; new variants created "to keep it fresh" are added to the shared kit
and become available to every brand.

**Onboarding a client:** copy `brands/_template/` → capture brand guide / site / Figma → map onto
palette roles, pick fonts and kit variants → render a proof sheet (full-screen title, subtitle,
lower third, side screen text in each palette) → Tymek approves → `status: approved`. Only approved
brands pass the QA gate.

**`brands/contentporary/` (initial content):**
- Visual language: dark ground with grid + dots + vignette + soft light sweep; glass surfaces with
  bevelled edge and light halo; glowing headline text; signature script for accent/payoff words;
  marks = highlight block, scribble underline, curved/elbow connectors, ✕/✓ chips, script payoff
  word, strike-through.
- Headline fonts (picked per video): Helvetica Now Display Bold, or a Satoshi-style geometric sans.
  Body: SF Pro-style medium. Script: monoline signature script.
- Palettes: `red` (from the reference video — Appendix A), `gold` (from the template stills),
  `lime` (from the custom mini animation). Shorts-reel values from `design-system.md` §3–§4 carried
  over as the Shorts defaults.
- `narrative.md`: current `context/narrative.md` content (pillars, beat structure, CTA rules).

## 8. Shared library — `lib/`

Every module is used by every brand and video, is styled only by tokens, and is a pure function of
time (seek-safe; shared-canvas resume comes free).

| Module | Responsibility | Source |
|---|---|---|
| `motion-blur.js` | directional camera/element blur; aspect-agnostic world sizing | merge of the 3 forks: root (`uWorld`/worldSize) + video 09 (`renderRegions`, WebGL context-loss guards) |
| `camera.js` | world + camera rig: poses, legs, holds, whips, texture baking for blur, bezier solver (bisection) | extracted from video 09 `lib/house.js`, brand removed; absorbs `cameraLeg` |
| `marks.js` | highlight sweep, scribble underline, curved/elbow connectors (draw), ✕/✓ chips, strike-through, ring, script write-on | `house.js` marks + Shorts prelude, de-duplicated |
| `text.js` | word entrance, glow title (bloom via deep-glow), accent words, odometer | `house.js` + `deep-glow.js` |
| `brand.js` | load `tokens.json` + chosen palette + chosen font → CSS variables | new |
| `kit/` | `title`, `subtitle`, `lower-third`, `side-text`, `cta-youtube`, `roadmap` — each with named variants | new; matched to the template stills + reference video |
| `shorts/wipe.js` | masked motion-blurred wipe | Shorts prelude |

**Retired:** `demo-transitions.js` (unused; `microDrift`/`blurCrossfade` contradict core).

**Distribution:** projects never hand-copy `lib/`. `tools/sync-lib` copies it into
`videos/<slug>/lib/` and writes `lib.lock` (content hashes). Improvements are made in root `lib/`
first, then re-synced.

**Usage:** templated graphics are kit calls (e.g.
`kit.subtitle({ variant, kicker: 'Step 1', title: 'HIT Prediction' })`); custom scenes are
hand-built from `camera` / `marks` / `text`, so they inherit the motion law automatically.

## 9. QA gate — `standards/core/qa.md`

### 9a. Automated (blocks render)

| # | Check | Method |
|---|---|---|
| 1 | HyperFrames validity | `npx hyperframes check` |
| 2 | No lib fork | `lib.lock` hashes == root `lib/` |
| 3 | BRIEF complete | format, brand (`approved`), palette, font, captions flag (Shorts) |
| 4 | Seek-safety | static scan: `Math.random`, `Date.now`, infinite repeats, CSS infinite animations |
| 5 | Blur law | every `feGaussianBlur` / `blur()` carries a reason tag (`focus`/`glow`/`wipe`; `wipe` only in Shorts: wipe feather and element smear); camera/whip blur only via `HFMotionBlur` |
| 6 | Easing vocabulary | no raw curves outside `ease.*` tokens |
| 7 | Captions | long-form: no caption layer except `kit.lower-third`; Shorts: matches flag |
| 8 | Density | long-form: hook (first `hook_end` s, default 80) ≥ 60 %, no face gap > 6 s, body gaps ≤ 30 s (BRIEF screen-share ranges exempt); Shorts 35–55 % |
| 9 | Settle before cut | last 0.3 s of each full-frame scene is still (frame-diff) |
| 10 | Render traps | text verified in rendered frames (design-system §9b traps); seek-flicker scan |

**Exceptions:** declared in the BRIEF under `exceptions:` with a reason; the gate passes them and
lists them in the preview pack.

### 9b. Human review

- **Preview pack** (generated): contact sheet of every graphic, draft render of the hook + one
  body scene, density timeline, exceptions list.
- **Sign-off: whoever ran the build**, using the 5-question checklist (smooth? on-brand? readable?
  synced to speech? every graphic earns its place — the 80/20 familiarity test). Tymek sees the
  final. The checklist must be answerable by someone other than Tymek.
- Client videos then go to the client as V1 via `client-ops`.
- **Promotion rule:** a review finding that changes a rule is written into `standards/` or the
  brand — never only into a BRIEF or agent memory.

## 10. Pipeline — `standards/core/pipeline.md`

**Entry point:** project skill `.claude/skills/contentporary-video/` (in git, shared with the
team). Routes "make the graphics for `<video>`" to format, brand and checklist. `CLAUDE.md` shrinks
to the git-sync protocol + "use the skill".

**Project layout (both formats):**
```
videos/<slug>/  BRIEF.md · transcript.json · storyboard.md · assets/captures/MANIFEST.md
                compositions/ · lib/ + lib.lock · deliver/
```

**BRIEF fields:** `format`, `brand`, `palette`, `font`, overrides, `captions` (Shorts),
`hook_end` (long-form, default 80), `screen_share` ranges (long-form), `exceptions`, source footage path.

**Long-form:**
1. Intake — `tools/new-video` scaffolds and syncs lib; inputs: basic-edit export (proxy OK) +
   transcript (`hyperframes transcribe`).
2. Storyboard — graphics mapped to transcript timecodes (kit / device / custom; placement mode);
   density checked on the plan. Runner approves.
3. Capture — real screenshots or faithful recreations → `assets/captures/` + MANIFEST.
4. Build — full-frame reel (shared canvases) + separate alpha comps for over-footage layouts,
   from kit + primitives.
5. Automated gate (§9a).
6. Preview pack → runner signs off (§9b).
7. Render + slice — MP4 clips + ProRes 4444 alpha + `TIMECODES.csv` + README → `deliver/` →
   shared drive (media never in git).
8. Hand-off — editor places clips; client videos → V1 via `client-ops`.
9. Feedback — rule changes promoted into `standards/` / brand; commit and push code only.

**Shorts:** intake (vertical footage + captions flag) → storyboard with `probe-cuts` → capture →
build one composition over the footage → gate → preview → render one MP4 → hand-off → feedback.

## 11. Migration

| Today | Becomes |
|---|---|
| `context/design-system.md` | split: `standards/core/motion.md` · `standards/formats/shorts.md` · `brands/contentporary/` |
| `context/motion-craft.md` | reconciled into `standards/core/motion.md`; contradicting rules dropped (constant bed motion, mandatory idles, "110–170 ms always" stagger, blur crossfades) |
| `context/frame.md` | `brands/contentporary/tokens.json` + palettes |
| `context/narrative.md` | `brands/contentporary/narrative.md` |
| `context/custom.md` | merged into format profiles |
| `context/motion-waapi.md` | kept as a technique reference (stale `waapi-demo` path fixed) |
| `context/voice.md`, TTS steps in `PIPELINE.md`, `templates/script-template.md` | removed (no TTS/faceless format) |
| `PIPELINE.md` | replaced by `standards/core/pipeline.md` |
| `CLAUDE.md` | slimmed: git sync + entry skill + precedence |
| `lib/motion-blur.js` + forks, `deep-glow.js`, `demo-transitions.js` | merged / folded / retired per §8 |
| video 09 `lib/house.js`, Shorts prelude, `scripts/slice.mjs`, `scan-flicker.py` | extracted into `lib/` and `tools/` |
| `videos/*` | frozen as-is (not migrated) |
| stale refs (`../CLAUDE.md`, `scripts/`, `context/assets/`, "placeholders only") | removed |

## 12. Open items / deferred

- ~~Custom-animation catalogue~~ — resolved in Plan 1b: catalogue in `standards/formats/long-form.md`
  (research: `docs/research/2026-10-03-custom-animation-catalogue.md`); light ground added as a second
  look (palette `mode`).
- ~~Opus 5.5 animation video~~ — resolved in Plan 1b: ban list (core), beat grid, director's-brief
  BRIEF fields, critique loop (QA §2), model/effort, reference → style procedure. Sound stays out of
  scope (graphics are silent; the editor scores).
- Font licensing for team machines and client work — each brand's `assets/` records font sources;
  fonts live on the shared drive.
- Exact gold and lime palette values — to be sampled from source files when the Contentporary brand
  folder is built (current values are from stills).

---

## Appendix A — Measured long-form reference tokens

Source video: HrYMfy6MZtA (1280×720, 30 fps, 597 s). 27 graphic scenes; 24 camera moves fitted;
colours sampled from compressed frames (±6/channel). Raw data and scripts were produced in a
session scratchpad; the values below are the retained record.

**Structure**
- Footage ↔ graphic boundaries: hard cuts in ≈ 40 of 48.
- Hook 0–80 s: 71 % graphics, longest face gap 5.7 s. Body: ≈ 29 % graphics; gaps of 37, 82, 23,
  24, 98, 25, 25 s (the ≤ 30 s rule is deliberately stricter than the reference).
- Scenes 1.7–18.3 s, median ≈ 6 s. Shared canvas with face cut-ins of 2–6 s (e.g. 385.7–426.3 s).
- Chapter roadmap at ≈ 60, 127, 234, 340 s. CTA at ≈ 117, 525, 556 (extended), 590 s.

**Camera**
- Pooled easing fit (rms error): free fit `(0.32, 0, 0.18, 1)` 5.7 %; `(0.4, 0, 0.2, 1)` 7.2 %;
  `power2.out` 9.2 %; `(0.65, 0, 0.35, 1)` 21.7 %; `expo.inOut` 25.6 %.
- Legs 1.1–2.5 s; travel peak 0.75–1.2 fw/s (avg 0.25–0.38); drift peak 0.1–0.3 fw/s.
- Pushes/pulls 9–28 % over 1.6–4 s (avg 5–16 %/s); emphasis pushes avg 3–4.5 %/s (`sine.inOut`).
- Hold creep median ≈ 0.3 %/s.
- Motion blur: ordinary legs ≈ none; whip (424.6–425.9 s) directional, ≈ 130–180° shutter.

**Elements** (no overshoot anywhere)
- Words: rise 50–55 px @720 (≈ 7 % H), fade, blur→sharp ≈ 0.45 s; `power3.out` 0.6–0.67 s;
  stagger 233–333 ms; land 0–130 ms of the spoken word.
- Highlight sweep: 0.5 s (short) / 1.0 s (long), ≈ 360 px/s @720, fit `(0.47, 0.16, 0.23, 0.90)`.
- Script word: ≈ 135 ms/letter, starts ≈ 0.3 s before the spoken word.
- Glow title: pop to ≈ 70 %, settle ≈ 0.4 s `expo.out`; second word +0.43 s.
- Roadmap nodes: scale 0→1 in 0.45–0.5 s, chained 0.45–0.5 s apart.
- Cards: rise 35–40 px, 0.43 s `power2.out`; proof card push-up 1.3 s `power3.out`.
- ✕ chips: simultaneous, 0.45–0.57 s `power3.out`.
- Odometer: `power3.out`, 2.2–7 s, lands on the spoken number.

**Colour (red palette)**
- Ground: corners `#050505`–`#101010`; lit centre `#1E1E1E`–`#2C2C2D`; vignette edge ≈ 50 %;
  grid `#1A1A1A`–`#242424`, ≈ 4 columns per frame.
- Red: block `#F26666`; text `#D74B50`; glow title `#F96E71` (halo `#431D1D`); roadmap line
  `#EA9EA4` / glow `#622F31`.
- Neutrals: white `#EEEEEE`–`#F9F9F9`; secondary `#ACACAC`; connectors `#777777`.
- Cards: `#1C1B1B` / `#343233`, border 1–2 px `#7C7C7C`–`#B0B0B0`, radius 30–42 px @1080;
  roadmap cards maroon `#301010`–`#381010`.
- Accents: script lime `#BACE7A` (per-video); `status.ok` `#5C9064`; `status.x` `#975154`.

**Type**
- Headline ≈ Helvetica Now Display Bold, cap height ≈ 6.5 % H; glow titles 9–12 % H;
  labels 4–4.6 % H (SF Pro-style medium); script = monoline signature script.
