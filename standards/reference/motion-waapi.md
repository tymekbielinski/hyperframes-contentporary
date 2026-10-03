# Declarative animations in the pipeline — use WAAPI, not Framer Motion

**Framer Motion does not work in HyperFrames.** The renderer is deterministic: for each output
frame it seeks every animation to an exact time and samples in parallel — no wall clock, no
`requestAnimationFrame`. Framer Motion is RAF/real-time driven and React-only, so its motion
either freezes or renders garbage, and it needs a React build this project doesn't have.

**Use the Web Animations API (WAAPI) instead** — it gives the same declarative, spring-y ergonomics,
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

## Copy-paste helper (keeps our plateau + spring feel)

```js
const PLATEAU = "cubic-bezier(0.12, 0, 0.10, 1)"; // our house ease: short accel, long plateau, short decel
const SPRING  = "cubic-bezier(0.2, 1.2, 0.3, 1)";  // Framer-Motion-style overshoot for pops

function anim(el, keyframes, opts) {
  const a = el.animate(keyframes, { fill: "both", iterations: 1, easing: PLATEAU, ...opts });
  a.pause();
  return a;
}

// reveal
anim(title, [{ transform: "translateY(34px) scale(.98)", opacity: 0 },
             { transform: "translateY(0) scale(1)",      opacity: 1 }], { duration: 640, delay: 340 });

// data-driven stagger (WAAPI's sweet spot)
document.querySelectorAll(".token").forEach((el, i) =>
  anim(el, [{ transform: "translateY(24px) scale(.9)", opacity: 0 },
            { transform: "translateY(0) scale(1)",     opacity: 1 }],
       { duration: 520, delay: 900 + i * 120, easing: SPRING }));
```

## Rendering a standalone composition to test

A `<template>`-wrapped file must be mounted from `index.html`. To render one file on its own, make its
root a plain `<div id="root" data-composition-id="…" data-width data-height data-duration>` (no
`<template>` wrapper), then: `npx hyperframes render --composition compositions/<your-test>.html`.

## When to still reach for GSAP

GSAP remains the default for full-scene orchestration (long timelines, camera legs, complex sequencing).
Reach for WAAPI when you want lightweight, declarative, data-driven element motion without a timeline —
the Framer-Motion use case. Both are seekable and can coexist in one composition.
