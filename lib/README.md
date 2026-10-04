# Shared library — `lib/`

One motion library for every brand and both formats. Every module is a **pure function of time**
(seek-safe: the renderer seeks frames in any order, across parallel workers), is **styled only by
brand CSS variables**, and uses only the **closed easing vocabulary** of the format profile.
Rules: `standards/core/motion.md` → `standards/formats/<format>.md`. Spec: §8 of
`docs/superpowers/specs/2026-10-03-animation-workflow-design.md`.

Plain browser scripts (each also loads in node for tests); GSAP must already be on the page. No
other runtime dependencies.

## Load order

```html
<script src="vendor/gsap.min.js"></script>
<script src="lib/profile.js"></script>      <!-- HFProfile: eases + timings per format -->
<script src="lib/motion-blur.js"></script>  <!-- HFMotionBlur -->
<script src="lib/camera.js"></script>       <!-- HFCamera  (needs profile, motion-blur) -->
<script src="lib/marks.js"></script>        <!-- HFMarks   (needs profile) -->
<script src="lib/text.js"></script>         <!-- HFText    (needs profile, motion-blur) -->
<script src="lib/brand.js"></script>        <!-- HFBrand -->
<script src="lib/kit/kit.js"></script>      <!-- HFKit     (long-form only; needs all of the above) -->
<script src="lib/kit/title.js"></script>    <!-- …then each component: title, subtitle, lower-third, -->
<script src="lib/kit/subtitle.js"></script> <!--   side-text, cta-youtube, roadmap (manifest loadOrder) -->
<script src="lib/kit/lower-third.js"></script>
<script src="lib/kit/side-text.js"></script>
<script src="lib/kit/cta-youtube.js"></script>
<script src="lib/kit/roadmap.js"></script>
<script src="lib/shorts/wipe.js"></script>  <!-- HFWipe    (Shorts only; needs profile) -->
```

Projects never hand-copy or edit these. `python3 tools/sync_lib.py videos/<slug>` copies the modules
listed in `lib/manifest.json` (the one machine-readable module list; `loadOrder` is the order above)
into `videos/<slug>/lib/` and writes `lib.lock` (sha256 per module); `--check` exits 1 on an edited
copy, a stale lock or a stray file. `test/`, `examples/` and this README are not synced. Improvements
go into root `lib/` first, then re-sync.

## Contract (what every module guarantees, and what callers must do)

- **`format` is required** (`"long-form"` or `"shorts"`) on every binder. It picks eases, timings and
  the motion-blur shutter. An ease token the format does not define throws, naming both
  (e.g. `ease.glow` in Shorts — the glow title is long-form only).
- **Binders add tweens at explicit times** to your paused timeline. Anything evaluated per frame
  (camera, pushes, glow, odometer, wipe) uses **one driver tween** over a pure function of `t`, so
  the result never depends on the order frames were seeked.
- **Pre-start state is written at build time** and equals each tween's from-state, so a frame before
  an element's time looks the same whether the playhead got there forwards or backwards.
- **No colours in the library.** Style marks and text with the brand variables below, e.g.
  `stroke: var(--hf-accent-line)`, `color: var(--hf-text-primary)`. The only literals allowed are
  pure-black alpha masks, marked `/* hf-allow: alpha-mask */`.
- **Every Gaussian is tagged** `data-blur-reason` (`focus` / `glow`; `wipe` in Shorts), and each
  Gaussian site carries its own tag on the same or the previous line
  (enforced by `lib/test/hygiene.test.js`). Movement blur is only ever `HFMotionBlur`.
- **One inline-transform writer per element.** Camera (stage, push), marks (highlight, chips), text
  (word spans) and every kit entrance overwrite an element's inline `transform`; each claims the element
  with `HFProfile.claimTransform(el, owner)` and a second, different owner throws naming both. Wrap the
  element and give each binder its own. Elements they animate must not carry a stylesheet transform.
- **Split text keeps its markup.** `HFText.splitWords(el)` / `splitChars(el)` wrap every word / code point
  in a span and leave element children (`<b>`, an accent `<span>`) in place (`data-hf-nosplit` keeps one
  whole); `words`, `typeOn` and `HFMarks.scriptWord` use them and hand the spans to `opts.onSpans(spans)`.
- **`HFText.accentWord` installs its own stylesheet** (once); `installCss()` is no longer required.
- **One `glowTitle` per glow filter id** — glow intensity is per filter, so two titles sharing an id
  share their intensity.
- **Await `HFText.ready()` before registering or rendering the timeline.** Odometer strips and
  `rasterText` images depend on fonts/SVGs that load asynchronously; `ready()` resolves once every
  font load, measure and raster decode started by any `HFText` binder has finished (it re-checks until
  no new work started meanwhile). A frame rendered earlier could differ from one rendered later.
- **Build order for text that is measured (kit components, `HFMarks.highlight`):** `await document.fonts.ready;
  await HFText.loadFaces(root)` before building. A scene that starts later is `display:none` at build; `loadFaces`
  requests the faces of every element under `root` (hidden ones too) and every declared `@font-face`, so the build
  measures the real face, not the fallback.
- **WebGL context loss:** after any context loss, `HFCamera.rig` falls back to the DOM pose for the
  rest of that rig, and `HFText.odometer` shows its DOM digits for the rest of that odometer.
- **WebGL context lifetime:** a rig holds a context only inside a blur leg; an odometer only inside
  `T < t < T + dur` (outside it the DOM digits are the truth, and the label becomes visible just after `T`).
- **`HFCamera.rig` `bake(ctx, K, t)` is called once, with `t = 0`** (the settled layout), unless
  `liveBake: true`, which re-bakes every frame inside a leg with that frame's `t`.
- **`HFMarks.swap` interpolates numeric props only.** A `var(--hf-…)` colour value is not
  interpolated: it flips at `T`. For a colour change use an attribute/class swap styled by the brand
  variable (as `HFText.accentWord` does with `data-hf-accent`).
- **`HFWipe` writes `host.style.filter` every frame** of its phases. Do not put `HFText.defocus`, a
  glow filter or any other filter on the same host — wrap one in the other instead.

## Modules

| Module | Global | Main API |
|---|---|---|
| `profile.js` | `HFProfile` | `ease(format, token)` → `p ⇒ eased` · `easeSpec` · `tokens(format)` · `timing(format)` · `bezier(x1,y1,x2,y2)` |
| `motion-blur.js` | `HFMotionBlur` | `createCameraBlur(cfg)` → `{render(t), renderRegions(t, regions), updateWorld(src), dispose(), size()}` · `profilePreset(format, kind)` · `analyticMotionVector` |
| `camera.js` | `HFCamera` | `rig(tl, cfg)` (keyed poses, holds, blur legs/whips, DOM-only when no canvas) · `push(tl, el, segments, opts)` · `track` · `glPose` |
| `marks.js` | `HFMarks` | `highlight` · `draw` · `swap` · `statusChip` · `seedChip` · `scriptWord` · paths: `ringPath` `scribblePath` `strikePath` `arrowPath` `elbowPath` `outlinePath` |
| `text.js` | `HFText` | `words` · `typeOn` · `glowTitle` (`opts.intensity`, default 1.2) · `defocus` · `accentWord` · `odometer` (`opts.fps`, default 30) · `rasterText` · `glowFilter` / `injectGlow` · `splitWords` / `splitChars` · `blurPx` · `measureWidth(el, onRemeasure)` (font-safe, works in `display:none` scenes) · `loadFaces(root)` · `track(promise)` / `ready()` |
| `brand.js` | `HFBrand` | `cssVars(tokens, palette, {font, overrides, scale})` · `toCss` · `apply(el, vars[, mode])` (throws if the palette mode can't be determined; sets `data-hf-mode`) · `mode(palette)` · `toGl(colour)` · CLI |
| `shorts/wipe.js` | `HFWipe` | `wipe(tl, {host, fe, filterId, dir, inAt, outAt})` · `phase(tl, out, in, T, dir)` (chain phases on one host freely: edges snap within 1 µs) |
| `kit/kit.js` + `kit/<component>.js` | `HFKit` | `title` · `subtitle` · `lowerThird` · `sideText` · `ctaYoutube` · `roadmap` — each `(tl, host, opts)` → `{ dur, … }`; `register` · `variants(name)` · `mode(host)` · `ground` · `cardIn` · `slideIn` · `fadeOut` · `pop` |

### Motion-blur shutter by format (`HFMotionBlur.profilePreset(format, kind)`)

| format | kind | shutter | angle | use |
|---|---|---:|---:|---|
| long-form | `leg` | 0.25 | 90° | ordinary camera legs (reads as ≈ no blur) |
| long-form | `whip` | 0.5 | 180° | whips |
| long-form | `roll` | 0.4 | 144° | odometer digit roll |
| shorts | `leg` | 0.7 | 252° | camera legs through a tall stage |
| shorts | `roll` | 0.4 | 144° | odometer digit roll |

World units are the world texture's own pixels (`uWorld`), so any canvas size can pan over any
texture size; nothing assumes 1920×1080. The generic material presets (`PRESETS`, `blurPreset`)
remain for frozen-era callers only.

### Brand variables (`lib/brand.js`)

Every palette role becomes `--hf-<role>-<sub>` in kebab-case: `--hf-ground-deep`,
`--hf-ground-centre`, `--hf-ground-grid`, `--hf-ground-dots`, `--hf-surface-fill`,
`--hf-surface-fill-alt`, `--hf-surface-bevel`, `--hf-surface-halo`, `--hf-text-primary`,
`--hf-text-secondary`, `--hf-accent-block`, `--hf-accent-text`, `--hf-accent-glow`,
`--hf-accent-line`, `--hf-accent-script`, `--hf-status-ok`, `--hf-status-x`; palette extras become
`--hf-extras-<name>`. Fonts: `--hf-font-headline` (+ `-weight`, the BRIEF's `font:` choice),
`--hf-font-body` (+ `-weight`), `--hf-font-script`, `--hf-font-captions`. Layout:
`--hf-card-radius`, `--hf-stat-radius`, `--hf-frame-padding`.

Generate a project's stylesheet at build time (deterministic, no fetch while rendering):

```bash
node lib/brand.js brands/contentporary --palette red --font helvetica > compositions/brand.css
```

CLI CSS output starts with an `/* hf-mode: dark|light */` comment; `HFBrand.apply` sets
`data-hf-mode` on the root and throws if the palette's mode can't be determined.

Overrides from the BRIEF: `--override accentScript=<colour>` (repeatable). A palette role that is
missing, a font the brand does not have, or an override that is not a palette role exits 1 with
the reason.

## Kit — `lib/kit/` (long-form templated graphics)

`HFKit.<component>(tl, host, opts)` builds a whole templated layout inside `host` — a 1920×1080 box the
kit sizes but never transforms — adds its tweens to `tl` and returns `{ dur, … }` (seconds from `opts.at`
until settled). Every component: `opts.format` must be `"long-form"`; `opts.at` (default 0) is when it
starts; `opts.variant` picks a variant (default: the first, the only one today). Layouts, sizes and
timings: `standards/formats/long-form.md` `## Kit`. Built only on `HFProfile`, `HFCamera`, `HFMarks`,
`HFText` and the brand variables; the kit's stylesheet (`<style id="hf-kit-css">`, installed once) holds
no colour literal.

| Call | Options | Returns |
|---|---|---|
| `HFKit.title(tl, host, o)` | `text`, `underline` (word index, optional) | `{dur, words}` |
| `HFKit.subtitle(tl, host, o)` | `title`, `kicker` (optional script line, e.g. "Step 1") | `{dur, pill, kicker, words}` |
| `HFKit.lowerThird(tl, host, o)` | `text`, `out` (optional: gone by then) | `{dur, words}` |
| `HFKit.sideText(tl, host, o)` | `items` (1–6 strings or `{text, at}`), `out` | `{dur, chips, labels}` |
| `HFKit.ctaYoutube(tl, host, o)` | `footage` (the face `<video>` — give it an `id`), `page: {src, width, height, player: [x,y,w,h], link: [x,y,w,h]}` (a real screenshot; both rects in page px and inside the page) | `{dur, poses}` |
| `HFKit.roadmap(tl, host, o)` | `title`, `steps` (3–6 × `{label, icon?}`; icons `bulb` `sliders` `chart` `target`), `visit` (0 = intro, k = dock card k) | `{dur, pose, nodes, cards}` |

- **Ground mode:** each component reads `data-hf-mode` from `host.closest("[data-hf-mode]")` and throws
  when there is none (`new_video` writes it on `index.html`'s root; an overlay document sets it on its own
  root). The resolved mode goes on the host as `hf-kit-dark` / `hf-kit-light`, which the kit CSS keys off,
  so a light scene nested in a dark root (the proof sheet) styles correctly. Light drops every glow.
- **Build order:** the contract's build-order and `HFText.ready()` bullets above apply to every
  component (they measure text, hidden scenes included; the CTA's page-image decode is tracked by `ready()`).
- **The roadmap is one world:** every visit builds the same geometry, so a visit-k scene opens exactly
  where visit k−1 ended; give each visit its own reel slot and the same `title` + `steps`.
- **The CTA camera is a DOM camera** (no motion blur on the dive): live footage cannot be baked into a blur
  texture yet. The scene ends on the footage itself, so if the face moves in the CTA's last 0.3 s, waive it
  in the BRIEF: `check 9 [<cta slot id>]: the CTA ends on live footage`.
- **Brand proof sheet:** `python3 tools/proof_sheet.py <brand>` builds `videos/proof-<brand>/` — title,
  subtitle, lower third and side text in every palette — for onboarding approval.

## Example — a long-form custom scene

```js
var tl = gsap.timeline({ paused: true });
var LF = { format: "long-form", frameHeight: 1080 };
var ground = getComputedStyle(document.documentElement).getPropertyValue("--hf-ground-deep").trim();

HFCamera.rig(tl, { format: "long-form", width: 1920, height: 1080, stage: stage, dur: 8,
  keys: [{ t: 0, cx: 960, cy: 540, z: 1 }, { t: 0.6, cx: 960, cy: 540, z: 1 },     // hold
         { t: 2.4, cx: 1300, cy: 450, z: 1.3 }],                                   // leg on ease.camera
  canvas: glCanvas, legs: [[0.6, 2.4]], bake: paintSettledLayout, bgCss: ground, bg: HFBrand.toGl(ground) });
HFMarks.highlight(tl, document.querySelector("#hl"), 2.5, LF);            // ease.sweep, ≈ 360 px/s @720p
HFText.words(tl, document.querySelector("#headline"), 3.1, LF);           // rise 7 % H, 0.6 s, 280 ms stagger
HFText.odometer(tl, document.querySelector("#figure"), 4, 3, "$150,000", LF);
await HFText.ready();                                                      // fonts/measures landed: frames are final
window.__timelines["scene"] = tl;
```

## Testing

- `node --test "lib/test/*.test.js"` (use the glob form; the directory form fails on node 22) — determinism and contract tests (also run by
  `python3 -m unittest discover -s tools -p 'test_*.py' -v`). `lib/test/hygiene.test.js` scans every
  module with `tools/lawscan.js` (the scanner QA checks 4–6 also run over compositions) for clocks,
  randomness, infinite repeats, hard-coded colours, overshoot or raw eases, and untagged Gaussians
  (colour literals other than marked pure-black alpha masks are banned). `lib/test/drift.test.js`
  fails when `HFProfile` timings (incl. the kit's card, chain-gap, node and CTA values) or `HFMotionBlur`
  shutters drift from the profile markdown. `lib/test/kit-<component>.test.js` run the kit contract
  (`lib/test/kit-contract.js`: long-form only, throws without `data-hf-mode`, deterministic, profile eases
  only, build-time style = from-state incl. transform and filter, no glow on the light ground) plus each
  component's own layout and timing.
- `lib/examples/smoke.html` — real GSAP + WebGL in a browser: builds a long-form and a Shorts scene
  from every module (incl. chained `HFWipe.phase` → `phase` on one host), seeks 52 frames forwards and then shuffled, and compares what paints
  (including blur-canvas pixels). It fails unless both camera blur canvases and the odometer canvas actually painted. Serve the repo root (`python3 -m http.server 8765`), open
  `http://localhost:8765/lib/examples/smoke.html`, expect `PASS`.

## Where things came from (2026-10-03 consolidation)

| Before | Now |
|---|---|
| three `motion-blur.js` forks (root, video 09, Shorts copies) | `motion-blur.js` (root `uWorld` + 09 `renderRegions`, `dispose`, context-loss guards) |
| video 09 `house.js` `camera`, `push`, `bezierY` | `camera.js` `rig`, `push`; `profile.js` `bezier` |
| `demo-transitions.js` `cameraLeg` | `camera.js` `rig` without a canvas (retired: `microDrift`, `blurCrossfade`, `zoomThrough`, `colorDip` contradict core law) |
| `house.js` marks + Shorts prelude `draw`, `chipIn`, `peers` | `marks.js` |
| `house.js` `words`, `typewrite`, `handwrite`, `odometer`, `rasterText`; prelude `kineticText`, `words` | `text.js` (`handwrite` → `marks.scriptWord`) |
| `deep-glow.js` | `text.js` `glowFilter` / `injectGlow` / `setGlowIntensity` (retired as a file) |
| Shorts prelude `wipeInOut`, `house.js` `wipeIn/wipeOut/phaseWipe` | `shorts/wipe.js` |

Dropped on purpose: `popIn` / `kineticText` overshoot (`back.out`), `slamEase` and other off-table
curves, `house.js` `drift` (mandatory idle), the Satoshi-only font fetch (fonts are passed in).
`videos/*` keep their own frozen copies and are not migrated.
