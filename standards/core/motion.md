# Core Motion Law

**Applies to every brand and every format.** Precedence: this file → `standards/formats/<format>.md`
→ `brands/<brand>/` → the video BRIEF. A lower layer supplies values (timings, colours, fonts) and
never overrides a rule here. Replaces `context/motion-craft.md` and the brand-agnostic half of
`context/design-system.md`.

## The law

1. **Seek-safe or it doesn't ship.** One paused master timeline; helpers add tweens at explicit
   times. No `Math.random()` / `Date.now()` (seed anything pseudo-random). No `repeat: -1`. Animate
   `transform`, `opacity` and `filter` only — never `width`/`height`/`top`/`left`; for "container
   grows", animate `scaleY` on a wrapper or tween between pre-measured transforms. Technique
   reference: `standards/reference/motion-waapi.md`.
2. **Move → hold → move.** Elements and the camera travel, settle, then rest. During a hold the
   camera may creep at most 0.5 %/s, unless the format profile sets a hold-push rate. There is no "bed never stops" rule and no mandatory idle
   animation: stillness is used deliberately as contrast.
3. **No overshoot by default.** No bounce, elastic or `back.out` unless the format profile names the
   exact exception.
4. **Named easing vocabulary.** Every tween uses one of these names, whose values the format profile
   sets. No ad-hoc curves in compositions.
   - `ease.camera` — camera legs, pans, pushes, pulls.
   - `ease.enter` — element entrances (words, cards, chips, counters).
   - `ease.sweep` — highlight blocks, underlines, connectors drawing.
   - `ease.cut` — transitions between scenes inside a graphic (whips, wipes).

   A profile may add named extras (e.g. `ease.camera.slow`).
5. **Blur law.**
   - Blur that represents **movement** — camera legs, whips, fast element travel of static content, odometer digit
     roll — uses `HFMotionBlur` (`lib/motion-blur.js`): directional, along the per-pixel velocity,
     with the shutter set by the format profile. `HFMotionBlur` cannot texture an element whose
     own content is animating while it moves. That element-level smear may use a directional
     Gaussian only in Shorts, tagged `wipe`; in long-form such an element moves without smear.
   - Gaussian blur (`feGaussianBlur`, CSS `blur()`) is allowed only for non-motion purposes, and
     every use carries `data-blur-reason` with one of:
     - `focus` — focus/defocus: backdrop rack-defocus behind a title, words sharpening as they
       enter, depth-of-field on a thumbnail inside a card.
     - `glow` — glow and bloom.
     - `wipe` — Shorts only: the masked wipe feather and element-level smear (see
       `standards/formats/shorts.md`).
   - A Gaussian standing in for a camera move is never acceptable.
6. **Graphics sync to speech.** An element lands on its spoken word, up to 0.3 s early. Cards and
   nodes lead their phrase by 0.3–0.5 s. Cuts land on the key word ±0.1 s. On-screen text may
   paraphrase speech instead of quoting it.
7. **Footage ↔ full-frame graphic is a hard cut.** Transitions happen inside graphics, as camera
   travel through one world. Over-footage layouts (lower third, side screen text, mini animations)
   animate on and off over the footage. The long-form CTA template is the other exception: it
   transforms the footage itself (scale into a player and back).
8. **Settle, then hold.** A full-frame graphic is still for its last 0.3–1 s before it cuts out.
9. **Credibility.** UI is a real screenshot or a faithful recreation of a real platform. Diagrams,
   data and illustration are free. Invented UI posing as real is not allowed. Exceptions are
   declared in the BRIEF (`exceptions:`) with a reason.
10. **Two-pass build.** Lay the artifact out first; then annotate it in a visibly different register
    (marks). Pass 2 may reinterpret pass 1 — recolouring existing elements is stronger than
    rebuilding. Which marks and which colours come from the brand.

## Craft notes (apply everywhere)
- Odometers: each digit column rolls vertically with its own motion blur, and digits lock
  right-to-left, leading digit last.
- Budget one real-product micro-detail per UI scene (e.g. a favicon swapping in as the typed text
  becomes a recognisable name).
- A state change across a whole set (recolour) is one global swap, not a stagger.
- Peer sets and chained beats are different rhythms; the format profile gives both values.

## Not in this file (by design)
Timings, colours, fonts, text-reveal mode (per character or per word), graphics density, caption
policy. Those live in `standards/formats/` and `brands/`.
