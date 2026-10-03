# HFMotionBlur — reusable analytic motion blur for HyperFrames

Deterministic, seek-safe motion blur derived from the animation's own math (not
inferred from rendered pixels). A WebGL fragment shader marches samples along the
**analytic per-pixel velocity** of a camera transform, so translation, zoom
(radial) and any angle all blur correctly. The scene content is rasterised to a
texture **once**, so there is no per-frame DOM cloning and therefore no
content-desync glitch. Not part of HyperFrames — it's a plain, dependency-free
module you drop into a project.

## Use it in a new project

1. **Copy the module in:** `cp lib/motion-blur.js videos/<your-project>/lib/`
2. In a composition, add a `<canvas>` the renderer will capture, and include the module:
   ```html
   <canvas id="gl" width="1920" height="1080"></canvas>
   <script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js"></script>
   <script src="lib/motion-blur.js"></script>  <!-- path relative to the composition -->
   ```
3. Provide the two things that vary per project — **content** and the **camera transform** —
   and let the module own the blur:
   ```js
   // CONTENT (you own): rasterise your UI onto a 2D canvas (transparent where empty)
   var world = document.createElement("canvas"); world.width = 1920; world.height = 1080;
   var ctx = world.getContext("2d"); /* ...draw... */

   // CAMERA (you own): a PURE function of time, transform-origin 0,0
   function camPoseAt(t) { return { tx: /*..*/, ty: /*..*/, s: /*..*/ }; }  // or {x,y,scale}

   // BLUR (module owns):
   var blur = HFMotionBlur.createCameraBlur({
     canvas: document.getElementById("gl"),
     world: world,
     camera: { T: camPoseAt },
     fps: 30, shutter: 1.0, spacing: 1.5, maxN: 48,
     bg: [1, 1, 1, 1]           // clear colour; pass null for transparent-over-DOM
   });

   var tl = gsap.timeline({ paused: true });
   window.__timelines["your-id"] = tl;
   var drv = { v: 0 };
   tl.to(drv, { v: 1, duration: DUR, ease: "none", onUpdate: function(){ blur.render(drv.v * DUR); } }, 0);
   blur.render(0);
   ```

## API

- `HFMotionBlur.analyticMotionVector(T, t, eps?)` → `{tx, ty, s, rot}` — the core primitive
  (central-difference derivative of a transform function). Everything else derives from this.
- `HFMotionBlur.createCameraBlur(cfg)` → `{ render(t), updateWorld(src), motionVector(t) }`
  - `cfg.world` — HTMLCanvasElement / HTMLImageElement / ImageBitmap (RGBA).
  - `cfg.camera.T(t)` — analytic transform, `{tx,ty,s}` or `{x,y,scale}`, origin 0,0.
  - `cfg.fps` `cfg.shutter` (frames; 1.0 ≈ 360°, 0.5 ≈ 180° film) `cfg.spacing` (px/ghost)
    `cfg.maxN` (sample cap) `cfg.bg` (`[r,g,b,a]` 0–1, or `null` for transparent).
  - `render(t)` — call from the timeline `onUpdate`; returns the sample count used.
  - `updateWorld(src)` — swap the texture when content changes (see caveat).
- `HFMotionBlur.blurPreset(name, overrides?)` → `{shutter, spacing, maxN, ease, note}` — a named
  blur setting. `HFMotionBlur.PRESETS` is the full table.

## Blur presets — bridge from `motion-design` material/weight easing

Instead of hand-tuning `shutter`/`spacing`/`maxN`, pick a **material or weight** name from the
LottieFiles `motion-design` skill and pass it as `cfg.preset`. The blur then reads as the move is
*meant to feel*. Any explicit `cfg.shutter`/`spacing`/`maxN` still overrides the preset.

```js
var p = HFMotionBlur.blurPreset("elastic");   // -> { shutter:0.6, spacing:1.0, maxN:72, ease:"back.out(1.7)", ... }

var blur = HFMotionBlur.createCameraBlur({
  canvas: gl, world: world, camera: { T: camPoseAt },
  fps: 30, preset: "elastic"                   // fills shutter/spacing/maxN
});
// apply the MATCHING ease to the camera tween (blur only reads the 3 knobs):
tl.to(cam, { x: -640, ease: p.ease, duration: DUR, onUpdate: function(){ blur.render(...); } }, 0);
```

| Preset | shutter | spacing | maxN | ease | reads as |
|--------|--------:|--------:|-----:|------|----------|
| `rigid` | 1.0 | 1.5 | 48 | `power2.inOut` | metal/stone — clean, no overshoot |
| `elastic` | 0.6 | 1.0 | 72 | `back.out(1.7)` | rubber — snap-back spike, dense samples |
| `fluid` | 1.8 | 1.75 | 80 | `sine.inOut` | water/paint — long smeary trail |
| `paper` | 0.5 | 1.5 | 40 | `power2.out` | cards — 180° filmic |
| `gas` | 2.5 | 2.5 | 96 | `sine.inOut` | smoke/fog — diffuse, very long |
| `glass` | 0.35 | 2.0 | 24 | `power4.out` | brittle — crisp, minimal smear |
| `heavy` | 1.2 | 1.25 | 64 | `power3.out` | modals/overlays — decisive |
| `medium` | 0.7 | 1.5 | 48 | `power2.inOut` | cards/panels |
| `light` | 0.4 | 2.0 | 24 | `power2.out` | tooltips/icons — snappy |
| `film` | 0.5 | 1.5 | 48 | `power2.inOut` | neutral 180° baseline (default fallback) |

**Why the knobs move together:** `shutter` sets trail length (`EXP = shutter/fps`) — heavier/fluid
materials get longer trails. An **overshoot** ease (`elastic`, `back`) reverses velocity at the
snap-back, spiking peak per-pixel velocity; the trail would band/strobe unless sampled denser, so
those presets carry a higher `maxN` and lower `spacing`. This keeps blur direction consistent with
the `motion-design` easing tables rather than guessed per shot.

## Scope & caveat

Handles **camera motion** (pan / zoom / — extendable to rotation). It does **not**
capture live, changing DOM per frame: the DOM→texture path (`<foreignObject>`) is
asynchronous, which a synchronous seeked renderer can't wait on mid-frame. So this
is ideal for content that's **static during the move** (draw it once, blur the
camera). For content that animates *while* the camera moves (typing, count-ups),
you'd pre-rasterise the needed states or render those elements separately.

Working reference (original project): `videos/users-companies-30s/compositions/examples/vector-blur-test.html`
(not carried over — port a fresh example if one is needed here).

### World size (added 2026-09-07)
The shader now samples the world texture in its **own pixel units** (`uWorld`), so the output
canvas and the world texture no longer have to share a size: a 704×1080 panel can pan over a
2992×1568 rasterised screenshot at native resolution. `updateWorld(src)` reads the new size from
`src`; pass `worldSize: [w, h]` to pin it. A W×H world on a W×H canvas behaves exactly as before.

---

# HFDemoTransitions — transition + camera kit for scene-driven shorts

Ported from a product-demo pipeline; the camera-rig/transition mechanics are generic and apply
equally to educational and narrative content. Plain module, GSAP required on the page. Seek-safe: helpers only
add tweens to your paused timeline at explicit times — no wall-clock, no
`repeat: -1`, no tween-time DOM measurement. All colors come from your CSS /
`frame.md` tokens; the module never sets a color.

## Use it in a new project

1. `cp lib/demo-transitions.js videos/<your-project>/lib/`
2. Load GSAP (+ CustomEase for the plateau ease; falls back to `expo.inOut`),
   then `<script src="lib/demo-transitions.js"></script>`.
3. Scene contract: scene 1 visible; scenes 2+ `opacity: 0` in CSS. Outgoing and
   incoming animate at the same `T` — the transition IS the exit.

```js
var ease = HFDemoTransitions.registerPlateau();          // "plateau"
var tl = gsap.timeline({ paused: true });
window.__timelines["main"] = tl;

// Tier 0 — camera legs + persistent micro-drift (poses precomputed at setup)
HFDemoTransitions.cameraLeg(tl, "#cam", { x: -640, y: -210, scale: 1.8 }, 2.0);
HFDemoTransitions.microDrift(tl, "#drift", 0, 12, { seed: 3 });

// Tier 1 — primary world swap
HFDemoTransitions.blurCrossfade(tl, "#s1", "#s2", 6.0, { blur: 12 });

// Tier 2 — accents (once each). #dip is a full-frame overlay you style with
// the primary brand color, starting opacity: 0.
HFDemoTransitions.zoomThrough(tl, "#s2", "#s3", 10.0);
HFDemoTransitions.colorDip(tl, "#s3", "#s4", "#dip", 14.0);
```

## API

- `registerPlateau()` → ease name; registers `"plateau"` (compressed ease-in-out).
- `cameraLeg(tl, camEl, {x,y,scale}, T, dur?)` — one 0.6–0.9s plateau leg.
- `microDrift(tl, driftEl, T, total, {amp,rot,breathe,period,seed}?)` — finite,
  seeded handheld drift filling `[T, T+total]`; layer on a sub-wrapper so it
  composes with legs.
- `blurCrossfade(tl, oldEl, newEl, T, {duration,blur,lag}?)` — primary transition.
- `zoomThrough(tl, oldEl, newEl, T, {duration,push,blur}?)` — accent.
- `colorDip(tl, oldEl, newEl, dipEl, T, {duration,hold}?)` — accent; caller
  styles `dipEl`.

## deep-glow.js — HFDeepGlow (multi-scale bloom)

Physically-inspired "Deep Glow" as a seek-safe SVG filter (bright-pass → multi-radius
blur → weighted additive composite → intensity + tone). NOT a single Gaussian.

```js
var id = HFDeepGlow.inject({ threshold: 0.5, intensity: 1.2, tint: "source" });
el.style.filter = "url(#" + id + ")";
// animate the bloom from the timeline (motion-aware):
tl.to(g, { v: 1.7, ease: "expo.out", onUpdate: () => HFDeepGlow.setIntensity(id, g.v) }, T);
```

Sub-compositions can't reference `../../lib/*` (path check), so inline the `<filter>` markup
(`HFDeepGlow.filterMarkup(id, opts)`) into the composition and drive `setIntensity` locally.
Best on bright text over a dark band (glow brightens toward the tint).
