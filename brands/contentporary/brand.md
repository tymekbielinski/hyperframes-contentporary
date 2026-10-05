# Contentporary — Brand

**Status:** approved. Precedence: `standards/core` → `standards/formats/<format>` → this brand →
the video BRIEF. This file supplies values and look, never motion technique.

## Constant visual language
Every Contentporary video keeps these, whatever palette or headline font it picks:
- **Two ground modes, chosen per video by the palette's `mode`** (never flat in either):
  - **Dark ground** (`red`, `gold`, `lime`, `reel-dark`): a lit centre falling off to near-black
    corners (vignette edge ≈ 50 % of centre brightness), a faint grid (≈ 4 columns per frame) with a
    dot matrix, a soft light sweep. Dark glass cards with a bevelled 1–2 px light border and a faint
    light halo — never a dark drop shadow in long-form (Shorts screenshots keep their soft shadow, see
    `standards/formats/shorts.md`). Headlines white with a soft glow (halo 60–90 px at 1080p).
  - **Light ground** (`silver`, `paper`, `reel-light`): a silver or white radial/vertical gradient
    with a soft vignette (no grid on `paper`). Frosted white glass cards with a hairline border and a
    soft neutral shadow (`surface.halo`). Headlines in `text.primary` (dark), **no glow**; emphasis by
    marker/highlight block, scribble underline, dark `text.primary` on an `accent.block` marker, or white text on a saturated tag block (`extras.tagBlock`).
  - Card radius ≈ 36 px, stat cards ≈ 31 px at 1080p in both modes; highlight blocks are sharp-cornered.
- **Accent-word count:** one or two accent words in long-form; exactly one accent word per headline
  in Shorts — in the palette's `accent.text`.
- **Accent words:** a sharp-cornered `accent.block` behind a key stat or phrase, or a payoff word in
  the signature script (`accentScript`), negative in the accent colour, positive in `status.ok` — as text colour on the dark ground; on the
  light ground `status.ok` is a fill (block, underline, chip) behind dark `text.primary`.
- **Marks:** highlight block, scribble underline, underline, curved arrow, curved/elbow connectors
  that draw, ✕/✓ status chips, script payoff word, strike-through. Shorts also use the reel set:
  ring, group outline, tinted tool chips.
- **Proof assets:** real screenshots or faithful recreations of real platforms (the dark YouTube
  watch page is the house proof asset). In-screenshot UI is never restyled.

## Palettes (one per video, chosen in the BRIEF)
- `red` — long-form default; measured from the AE reference video.
- `gold` — warm amber; from the template stills (title, step card, side text).
- `lime` — lime accent; from the custom mini-animation still. A one-off lime script accent may also
  be added to `red` via a BRIEF override (`accentScript: "#BACE7A"`), as the reference video did.
- `silver` — light: silver radial + frosted white glass, dark text, coral/red marks (Clay.com, Ottley).
- `paper` — light: white→grey gradient, dark-brown headline on an orange highlight block, lime stats
  (Stupidly Simple).
- `reel-dark` / `reel-light` — Shorts; ground chosen by the screenshot's own UI mode.
A video may override individual palette roles in its BRIEF for a one-off accent. The constant
visual language above must still hold.

## Fonts (headline chosen per video in the BRIEF)
- `helvetica` — Helvetica Now Display Bold (reference video, Shorts reels).
- `geometric` — Satoshi Bold (template stills, video 09).
- Body: SF Pro Display Medium (Inter 500 off Apple machines). Script: monoline signature script
  (Brittany Signature). Shorts burned-in captions, when a Short has them: Garet Heavy.

## Kit variants
The variant names are `lib/kit` variants (`tokens.json` `kit`; layouts and timings in
`standards/formats/long-form.md` `## Kit`):
`glow-center` title (`HFKit.title`) · `glass-pill-script` subtitle (`HFKit.subtitle`: "Step 1" in script
over a glowing title in a glass pill) · `key-line` lower third (`HFKit.lowerThird`: one key line,
bottom-centre, white→warm gradient) · `grid-panel-chips` side text (`HFKit.sideText`: left-half grid
panel, glass number chips, face on the right) · `watch-page-dive` CTA (`HFKit.ctaYoutube`, over a real
screenshot of the brand's own watch page) · `wave-nodes` chapter roadmap (`HFKit.roadmap`: glowing wavy
line, numbered nodes, icon cards). Proof sheet of the four templated layouts in every palette:
`python3 tools/proof_sheet.py contentporary`.
On the light ground every kit variant drops its glow: dark `text.primary` with a scribble underline or an `accent.block` marker; the roadmap path is drawn in `accent.line` without bloom; side-text panels use frosted white glass instead of the dark grid panel.

## Never
- Flat fills in either mode; dark drop shadows under long-form cards on the dark ground; glow on light-ground headlines.
- More than one script word per line. Accent colours outside the chosen palette and BRIEF overrides.
- Light leaks.
