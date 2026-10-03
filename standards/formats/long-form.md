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
| Templated kit | full-screen title · subtitle / step card · lower third (key lines only) · side screen text (1–6 points) | `lib/kit` (Plan 4); new variants per video allowed |
| Recurring devices | chapter roadmap · CTA template | `lib/kit` |
| Custom | screenshot-focus · diagram/flow · comparison split · proof clip · counter/odometer · mini animations | `camera` / `marks` / `text` primitives + brand |
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
  positive words in `status.ok`; a big figure lands at the end.

## Density
- **Hook (first `hook_end` seconds, default 80 — set in the BRIEF):** ≥ 60 % graphics (reference: 71 %), and no face-only gap > 6 s.
- **Body:** at least one graphic, even a short one, every ≤ 30 s. Ranges declared as
  screen-share in the BRIEF are exempt.
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
| glow title | pops to ≈ 70 % brightness, settles 0.4 s `ease.glow`, no scale; halo 60–90 px at 1080p; next word +430 ms; background rack-defocuses behind it |
| card entrance | rise 35–40 px at 720p, 0.43 s `ease.card`, brightens and sharpens |
| chain gap | 450–500 ms between linked beats; peer sets (e.g. three ✕ chips) land together |
| odometer | `ease.enter`, 2.2–7 s, lands on the spoken number |
| motion blur | ordinary legs ≈ none (shutter ≤ 90°); whips ≈ 180° directional `HFMotionBlur` |
| backdrop defocus | blur σ ≈ 4.5 px at 1080p + brightness → 0.6 over 0.5 s, front-loaded (`focus`) |
| screenshots | axis-aligned in bordered cards; light halo; no dark drop shadow |

**Not used in long-form:** light leaks, masked wipes, dissolves/crossfades, overshoot.

## Captions
None. Spoken words appear on screen only as a **lower third for key lines** (`kit.lower-third`).
Proof-clip words are the client's quote, not captions.

## Delivery
- **Full-frame scenes:** silent MP4 clips (1920×1080, 30 fps) named by timeline timecode, plus
  `TIMECODES.csv` and a README for the editor.
- **Over-footage layouts:** ProRes 4444 with alpha (`npx hyperframes render --format=mov`).
- Hand-off to the shared drive; media never goes into Git.

## Checklist (run with `standards/core/qa.md`)
- [ ] Hook ≥ 60 % graphics, no face gap > 6 s; body gaps ≤ 30 s (screen-share exempt)
- [ ] Every motion uses a named `ease.*` token; no overshoot
- [ ] Camera moves → holds → moves; each full-frame scene is still for its last 0.3–1 s
- [ ] Words land on their spoken word; cards lead their phrase by 0.3–0.5 s
- [ ] No captions except key-line lower thirds
- [ ] All CTAs use the identical `cta-youtube` treatment
- [ ] Colours and fonts come from the brand palette/font chosen in the BRIEF (plus declared overrides)
