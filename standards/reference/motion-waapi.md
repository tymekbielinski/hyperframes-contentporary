# Declarative animations in the pipeline — use WAAPI, not Framer Motion

**Framer Motion does not work in HyperFrames.** The renderer is deterministic: for each output
frame it seeks every animation to an exact time and samples in parallel — no wall clock, no
`requestAnimationFrame`. Framer Motion is RAF/real-time driven and React-only, so its motion
either freezes or renders garbage, and it needs a React build this project doesn't have.

**Use the Web Animations API (WAAPI) instead** — it gives the same declarative ergonomics,
needs **zero install** (native browser API), and is a first-class seekable HyperFrames adapter. The
renderer drives it via `document.getAnimations()` → set `currentTime` → pause. Verified rendering:
a standalone test composition (the original waapi-demo.html was not carried over from the client pipeline).

## The contract (follow exactly, or the frame won't seek)

- Create every animation **synchronously at composition setup** (not in a callback/promise/timer).
- `element.animate(keyframes, opts)` with **finite `duration` and `iterations: 1`**.
- `fill: "both"` so the seeked state persists before/after the tween.
- `.pause()` right after creating it (the adapter also pauses on first seek).
- Model clip-local timing with `delay` (WAAPI seeks document-level time).
- Transforms + opacity only — never animate `width`/`height`/`top`/`left`.
- No infinite `iterations`, no `animation.finished` for render-critical DOM, no `Math.random`/`Date.now`.

## Copy-paste helper

Easing values come from `standards/formats/<format>.md` (core motion law rule 4); no curve is
defined here. `EASE_ENTER` below stands for the profile's `ease.enter` value.

```js
// `easing` is required: the caller passes the format profile's named `ease.*` value.
function anim(el, keyframes, { easing, ...opts }) {
  const a = el.animate(keyframes, { fill: "both", iterations: 1, easing, ...opts });
  a.pause();
  return a;
}

// reveal
anim(title, [{ transform: "translateY(34px) scale(.98)", opacity: 0 },
             { transform: "translateY(0) scale(1)",      opacity: 1 }], { duration: 640, delay: 340, easing: EASE_ENTER });

// data-driven stagger (WAAPI's sweet spot)
document.querySelectorAll(".token").forEach((el, i) =>
  anim(el, [{ transform: "translateY(24px) scale(.9)", opacity: 0 },
            { transform: "translateY(0) scale(1)",     opacity: 1 }],
       { duration: 520, delay: 900 + i * 120, easing: EASE_ENTER }));
```

## Rendering a standalone composition to test

A `<template>`-wrapped file must be mounted from `index.html`. To render one file on its own, make its
root a plain `<div id="root" data-composition-id="…" data-width data-height data-duration>` (no
`<template>` wrapper), then: `npx hyperframes render --composition compositions/<your-test>.html`.

## When to still reach for GSAP

GSAP remains the default for full-scene orchestration (long timelines, camera legs, complex sequencing).
Reach for WAAPI when you want lightweight, declarative, data-driven element motion without a timeline —
the Framer-Motion use case. Both are seekable and can coexist in one composition.
