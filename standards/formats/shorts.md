# Format Profile — Shorts

Applies to Shorts (9:16, 1080×1920, 30 fps) for every brand. Inherits `standards/core/motion.md`;
supplies the Shorts values. Measured frame-by-frame from Tymek's two reference reels
(`tymek.bielinski_DXPO0upgpDE.mp4` = Reel A, `tymek ad v3.mp4` = Reel B). Colours and fonts are
not in this file: Contentporary's reel values live in `brands/contentporary/palettes/reel-dark.json`
and `reel-light.json`.

**Easing values** (closed table; no other curve names in this profile):

| Token | Value |
|---|---|
| `ease.camera` | `cubic-bezier(0.65, 0, 0.35, 1)` (profile ease, solved by bisection) |
| `ease.cut` | `cubic-bezier(0.65, 0, 0.35, 1)` — deliberately the same curve as `ease.camera` (the wipe) |
| `ease.enter` | `power3.out` — provisional: entrance curves were not measured in the reels (timings in the beat sheets are) |
| `ease.sweep` | `cubic-bezier(0.47, 0.15, 0.2, 0.95)` — provisional, carried from the long-form measurement |

hold push: ≈ 3.4 %/s (profile hold-push rate; overrides the core 0.5 %/s creep cap)

**Presentation:** screenshots are composited slightly rotated (~1–3°) with a soft drop shadow.

## 1. The structural rule everything else hangs off

**Graphics are not overlays. They are full-frame scenes that the edit CUTS TO.**

The talking head disappears entirely. A graphic scene occupies the whole canvas, runs 1.4–8.8s,
and hard-cuts back to the speaker. Nothing dissolves; nothing floats over the footage.

Measured hard cuts:

| Reel | Cuts | Graphic scenes | Graphic screen time |
|---|---|---|---|
| A | 4.53 · 9.53 · 12.17 · 18.90 · 24.23 · 25.93 · 34.73 · 36.13 · 38.90 | 5 | **~20.0s of 43.8s — 46%** |
| B | 2.17 · 4.77 · 7.23 · 12.50 · 13.80 · 16.67 · 19.10 · 27.93 · 31.80 · 36.07 · 36.73 · 38.07 · 38.73 · 40.40 · 50.93 · 54.73 | 6 | **~28s of 63.2s — 44%** |

**Roughly 45% of the runtime is full-frame graphics.** That is the format. A short with graphics
sprinkled over the speaker is a different, weaker product — it is not what these reels do.

**Captions are a per-project flag** (`captions:` in the BRIEF). If the source footage already
carries burned-in captions, never re-add them. Either way, no caption appears over a full-frame
graphic scene: the subtitle layer belongs to the talking head only.

### The scene transition — a bezier-eased motion-blurred wipe

Scenes change on a travelling soft-edged **mask**, not a cut and not an opacity fade. The card's
content is smeared along the travel axis by a directional `feGaussianBlur` (the named Gaussian exception — tag it `data-blur-reason="wipe"`), and the reveal is a
moving gradient mask whose feather decays in lockstep with the smear, so edge and content sharpen
together as the wipe lands. (Masking, not `clip-path` — clipping applies *after* the filter and
keeps a razor edge no matter how blurred the content is.)

| knob | value | why |
|---|---|---|
| easing | **`cubic-bezier(0.65, 0, 0.35, 1)`** | symmetric ease-in-out — the wipe leaves and arrives at **zero velocity** |
| duration in | **0.42s** | |
| duration out | **0.36s** | |
| blur | `14px` in / `12px` out, scaled by `4q(1-q)` | peaks mid-travel, nothing at either end |
| mask feather | `8 + 34 · 4q(1-q)` (%) | softest while moving fastest, tight at rest |

**The easing is the whole point.** `power2.out` on the way in and `power2.in` on the way out both
put peak velocity *exactly at the cut* — the transition starts and ends at full speed, which reads
as a snap however short you make it. A symmetric bezier moves the peak to the middle of the travel,
where the blur and the feather are also at maximum, so the fast part of the move is the part the eye
can't resolve anyway.

Blur and feather must ride the wipe's **speed**, not its position. Driving them off `(1 - q)` — max
at the start, zero at the end — smears hardest at the instant the scene appears, which is backwards.

Solve the bezier deterministically (bisection, ~24 iterations) rather than reaching for CustomEase;
the renderer seeks, so the curve has to be a pure function of time.

### Land scene boundaries ON the footage's own cuts

The underlying clip has its own jump cuts. A graphic scene that ends a few frames *before* one
leaves an orphaned tail of the outgoing shot — it flashes for 2-8 frames and then hard-cuts, which
reads as a glitch, not an edit.

Probe the source first:

```bash
ffmpeg -v info -i input-video.mp4 -filter_complex "select='gt(scene,0.20)',metadata=print:file=-" \
  -an -f null - 2>/dev/null | grep -oE "pts_time:[0-9.]+"
```

Then place every scene end so the **exit transition finishes just AFTER** the nearest source cut —
end = cut + the exit duration. The cut then happens while the graphic still covers the frame, and
the transition only ever reveals the incoming shot. Ending exactly ON the cut is second best (the
exit reveals slivers of the outgoing shot); ending before it is the failure case.

A scene *start* has no such constraint — it can begin mid-shot.

## 6. Measured motion — the calendar scene, beat by beat

Reel A, 4.567 → 9.533 (4.97s). This is the canonical two-pass build; copy its shape.

| t | event | measured detail |
|---|---|---|
| 4.567 | **hard cut** to the dark scene | card already at full size — no entrance |
| 4.700–5.700 | 8 blue pips fill the month | **~125 ms apart**, card **completely static** |
| 5.800–6.800 | camera pushes **1.00 → 1.10** | starts *after* the pips, runs *under* the title |
| 6.067–6.600 | `Meetings` types on | **~2 frames per character ≈ 67 ms/char**, each char settling from below |
| 6.800–7.400 | whole composition **translates up ~280px** | the layout move that makes room for pass 2 |
| **7.200–7.333** | **all pips recolour blue → red** | **4 frames ≈ 133 ms — a hard global swap, NOT staggered** |
| 7.37–7.90 | `Uneducated Leads` lands below | |
| 8.2+ | red glowing lead icon fades up beneath | |
| 8.400–9.200 | slow push **1.075 → 1.105** | ≈ 3.4 %/s during the hold |
| 9.533 | **hard cut** back to the speaker | |

Two things to take from this that are easy to get wrong:

- **The recolour is instant.** 133 ms, whole set at once. Staggering it kills the "the same thing
  was always this" reveal.
- **Nothing moves during the pip build.** The camera waits, then moves between phases. Stillness is
  used deliberately as contrast against the moves.

---

## 7. Measured motion — the chip diagram, beat by beat

Reel B, 24.7 → 28.0. The canonical *chain*.

| t | event | measured detail |
|---|---|---|
| 24.70–24.90 | channel page **blur-crossfades to white** | **6 frames ≈ 200 ms**, both layers blurring |
| ~25.00 | the single thumbnail artifact is alone on white | |
| 25.167 | **STRATEGY** (top-left) | seeds as a small coloured dot, then **expands horizontally ~167 ms** to reveal its label |
| 25.533 | **SCRIPTING** (top-right) | **+367 ms** |
| 26.167 | **EDITING** (bottom-left) | **+633 ms** — a real beat of dead air |
| 26.467 | **POSTING** (bottom-right) | **+300 ms** |
| | each chip's red arc draws toward the artifact as it lands | |
| 26.93–27.6 | `We Handle Everything!` lands **word by word** | **~200 ms per word** |
| 27.3–28.0 | red underline **draws left→right, trailing the words** | finishes after the last word |
| 28.0 | **hard cut** | |

**Do not copy the 24.70 crossfade.** Blur crossfades are dropped from the standard (spec §11); a scene
change inside a graphic uses the masked wipe (§1).

**The chip entrance grammar is its own thing:** a coloured dot appears, then the pill *grows
sideways* out of it to expose the label. That is not scale-down-from-oversize. Use it for anything
tag-like; keep scale-down entrances for headline type.

Chip-to-chip intervals are **300–630 ms**, not 110–170 ms. These are causal chain links with
visible dead air between them, not a stagger group. The 110–170 ms band applies *within* a set of
peers (the calendar pips at 125 ms); it does not apply to chained beats.

---

## 8. The camera is a character

Reel B travels across its screenshots continuously: measured **7–16 % scale per second**, with
deliberate reframes mid-scene (push in on the sub count, pull back to reveal the video grid, push
into a single thumbnail). The screenshot is treated as **a large world the camera explores**, not
as a card that appears.

This is the biggest single difference between these reels and a card-based overlay build. If a
scene shows a long document (a payments list, a channel page), the move *is* the animation — you
scroll and push through it, and the annotations land where the camera stops.

---

## 8b. Multi-phase camera — how to fix a crowded scene

A scene with more than ~3 elements presented at once reads as a slide. The fix is not to shrink
the content, it is to **make the stage taller than the frame and travel through it**, so the layout
is only ever ~60% visible and is read in passes.

The recipe, as built on short4's funnel:

1. **Lay the content out past the frame.** Stage 2800px against a 1920px frame; keep every element
   inside the frame's *width* so no camera position ever crops horizontally.
2. **Hold zoom constant** and move only in Y. A pure pan means the blur is single-axis and can be
   derived exactly; mixing zoom in adds a radial component a directional blur can't represent.
3. **Ease every leg on the profile ease (`ease.camera`)** — `cubic-bezier(0.65, 0, 0.35, 1)`, solved by bisection
   through a keyframe track so the pose stays a pure function of time and survives seeking.
4. **Blur with the real library — `lib/motion-blur.js` (`HFMotionBlur`). Never a Gaussian.**
   See § 8c. A `feGaussianBlur` driven off camera velocity *looks* like motion blur in a still and
   is wrong in motion: it is an isotropic smudge, not a trail along the per-pixel velocity field.

   ```js
   var blur = HFMotionBlur.createCameraBlur({
     canvas: glCanvas, world: bakedTextureImg,
     camera: { T: pose },              // pure function of local time -> {tx,ty,s}
     fps: 30, preset: "medium", bg: [0.031, 0.035, 0.043, 1]
   });
   // during a leg: hide the DOM stage, show the canvas, and blur.render(t) each frame
   ```

5. **Put every leg in a quiet gap** — nothing may animate inside a move window, or the smear
   fights the content.
6. **Land the incoming element INSIDE the tail of its own leg.** This is the one that is easy to
   get wrong: if the camera arrives before the content does, you get a dead frame of empty
   background at the end of every move. Overlap them by ~0.2s.

## 8c. Motion blur is ALWAYS the library — never a Gaussian

**Rule: any blur that represents movement uses `lib/motion-blur.js` (`HFMotionBlur`). A
`feGaussianBlur` or CSS `blur()` is never an acceptable stand-in for motion blur.**

`HFMotionBlur` marches samples along the **analytic per-pixel velocity** of the camera transform,
so a pan trails along the pan axis and a zoom trails radially outward from the centre — different
directions in different parts of the same frame. A Gaussian cannot do that: it is one isotropic
radius everywhere, so it reads as an out-of-focus smudge rather than a moving one, and the failure
is obvious the moment there is any zoom component.

### Wiring it up

1. **Sync the shared library into the project** (`tools/sync-lib`; never hand-copy or edit the copy) and load `lib/motion-blur.js` after GSAP.
2. **Bake a world texture per leg.** The blur samples a *static* image, so each camera leg needs a
   still of the settled layout as it appears during that leg. Generate a standalone bake page that
   mounts the card's scoped `<style>` plus its stage subtree at 1:1, with the elements visible for
   that leg forced to `opacity:1`, then screenshot it.
3. **The texture must carry the canvas aspect ratio.** The shader maps it onto world rect
   `[0,uRes.x] × [0,uRes.y]`, so a texture of any other aspect is silently stretched. For a
   canvas of W × H, pick a blow-up factor `K`, size the texture `W·K × H·K`, place the stage
   origin at `PAD_X = (W/2)(K-1)`, `PAD_Y = (H/2)(K-1)`, and scale the pose by `K`:

   ```js
   function pose(t) {                       // stage point (W/2, cy) -> canvas centre at zoom Z
     var Z = zOf(t), cy = cyOf(t);
     return { tx: W / 2 - Z * (W / 2 + PAD_X), ty: H / 2 - Z * (cy + PAD_Y), s: Z * K };
   }
   ```

   Padding exists so a pulled-back or off-centre camera still samples real pixels instead of
   running off the texture edge.
4. **Bake OPAQUE.** The pass averages RGBA across samples; a straight-alpha PNG averages its
   transparent texels and blows the whole frame out to white. Paint the scene's ground into the
   texture and pass the matching `bg` for out-of-bounds samples.
5. **Hand off cleanly.** During a leg, `opacity:0` the DOM stage and show the canvas; restore on
   exit. Nothing may animate inside a leg window or the texture stops matching the DOM.

### The one place the library does not apply

`createCameraBlur` handles *camera motion over static content* — it cannot capture live, changing
DOM per frame (the DOM→texture path is async and a seeked renderer cannot wait on it). So an
element-level smear (a panel sliding in while its own content animates) still uses a directional
`feGaussianBlur`, as card-04's row slams do. That is a documented limitation of the technique, not
a licence to approximate a camera move.

In Shorts this smear is filed under the same named exception as the wipe: tag it
`data-blur-reason="wipe"`. It does not exist in long-form.

## 9b. Two render-only text traps

Both of these look perfect in a live browser and only appear in encoded frames, so **check text
in the rendered MP4, never only in `hyperframes snapshot`.**

**1. `background-clip: text` + GSAP-animated word spans + `text-align: center` = ghost text.**
Gradient-filled text paints a background and clips it to the glyphs. When such text is split into
per-word spans that GSAP transforms, and the block is centred, the renderer rasterises that
background layer at its *stale, left-aligned* position — so a flat-white duplicate of the label
appears at the left edge of the frame, on top of the correct centred one.

Left-aligned gradient text is fine. Centred gradient text with no per-word animation is fine. The
combination is not. For a centred, word-animated label, **use a solid colour**:

```css
/* was: background-image: linear-gradient(...); background-clip: text;
        color: transparent; -webkit-text-fill-color: transparent; */
color: #F4F6F8;
```

**2. `line-height` shorter than the glyphs crops gradient text.** `background-clip: text` paints
only inside the element's background box, so a box shorter than the ascenders leaves the tops of
the letters with nothing to show through — they look sliced off. Keep `line-height >= 1.3` on any
gradient-filled text; never set it below the font size (e.g. `56px` type on a `62px` line box).

## Density and delivery
- ≈ 45 % of runtime is full-frame graphics (QA band: 35–55 %); scenes 1.4–8.8 s; full-frame only, no overlays on the face.
- Delivery: one finished MP4 (1080×1920, 30 fps).

## Checklist (run with `standards/core/qa.md`)
- [ ] Full-frame scene the edit cuts to, not an overlay; scene ends land on the footage's own cuts
- [ ] Built on a real screenshot (or faithful recreation), rotated 1–3° with a soft shadow
- [ ] Ground matches the screenshot's UI mode (`reel-dark` / `reel-light` or the brand's equivalent)
- [ ] Pass 1 builds plainly; pass 2 annotates with the brand's marks
- [ ] Peer sets ~125 ms apart; chained beats 300–630 ms with visible dead air; set recolour = one 133 ms swap
- [ ] Type-on ~67 ms/char; word-by-word ~200 ms/word
- [ ] Camera travels across document-shaped screenshots (7–16 %/s) and holds while a discrete set builds
- [ ] Captions match the BRIEF flag and never sit over a graphic scene
