# Contentporary — Brand

**Status:** approved. Precedence: `standards/core` → `standards/formats/<format>` → this brand →
the video BRIEF. This file supplies values and look, never motion technique.

## Constant visual language
Every Contentporary video keeps these, whatever palette or headline font it picks:
- **Ground:** dark, never flat. A lit centre falling off to near-black corners (vignette edge ≈ 50 %
  of centre brightness), a faint grid (≈ 4 columns per frame) with a dot matrix, and a soft light
  sweep. Shorts may use the light ground (`reel-light`) when the screenshot is light-mode.
- **Surfaces:** dark glass cards with a bevelled 1–2 px light border and a faint light halo.
  Never a dark drop shadow (long-form). Card radius ≈ 36 px, stat cards ≈ 31 px at 1080p;
  highlight blocks are sharp-cornered.
- **Headlines:** white, with a soft glow (halo 60–90 px at 1080p) on dark ground; one or two accent
  words in the palette's `accent.text`.
- **Accent words:** a sharp-cornered `accent.block` behind a key stat or phrase, or a payoff word in
  the signature script (`accentScript`), negative in the accent colour, positive in `status.ok`.
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
- `reel-dark` / `reel-light` — Shorts; ground chosen by the screenshot's own UI mode.
A video may override individual palette roles in its BRIEF for a one-off accent. The constant
visual language above must still hold.

## Fonts (headline chosen per video in the BRIEF)
- `helvetica` — Helvetica Now Display Bold (reference video, Shorts reels).
- `geometric` — Satoshi Bold (template stills, video 09).
- Body: SF Pro Display Medium (Inter 500 off Apple machines). Script: monoline signature script
  (Brittany Signature). Shorts burned-in captions, when a Short has them: Garet Heavy.

## Kit variants
`glow-center` title · `glass-pill-script` subtitle ("Step 1" in script over a glowing title in a
glass pill) · `key-line` lower third (one key line, bottom-centre, white→warm gradient) ·
`grid-panel-chips` side text (left-half grid panel, glass number chips, face on the right) ·
`watch-page-dive` CTA · `wave-nodes` chapter roadmap (glowing wavy line, numbered nodes, icon cards).

## Never
- Flat fills, pure-white grounds in long-form, dark drop shadows under cards (long-form).
- More than one script word per line. Accent colours outside the chosen palette and BRIEF overrides.
- Light leaks.
