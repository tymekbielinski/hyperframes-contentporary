/* ============================================================================
 * HFMotionBlur — analytic, deterministic motion blur for HyperFrames
 * ----------------------------------------------------------------------------
 * HyperFrames seeks every output frame independently (no wall clock), so motion
 * blur cannot be inferred from rendered pixels or frame-to-frame deltas. Instead
 * it is DERIVED FROM THE ANIMATION'S OWN MATH: every animated transform is a pure
 * function of time T(t) -> {tx, ty, s}. We differentiate it analytically to get
 * the motion vector, and a WebGL fragment shader marches samples along the real
 * per-pixel velocity of the camera transform — translation, zoom (radial) and any
 * angle all blur correctly. The scene content is rasterised to a texture ONCE
 * (you provide it), so there is no per-frame DOM cloning and therefore no
 * content-desync glitch. The whole GL render is a pure function of the given t.
 *
 * This module owns the BLUR. You own the CONTENT: pass any HTMLCanvasElement /
 * HTMLImageElement / ImageBitmap as `world` (e.g. draw your UI with the canvas
 * 2D API, or rasterise a DOM subtree via <foreignObject>). For content that
 * changes over time, call `updateWorld(src)` on the frames where it changes.
 *
 * USAGE (inside a HyperFrames composition script):
 *
 *   var world = document.createElement("canvas"); world.width=1920; world.height=1080;
 *   // ...draw your scene onto world's 2D context (transparent where empty)...
 *
 *   var blur = HFMotionBlur.createCameraBlur({
 *     canvas: document.getElementById("gl"),      // the <canvas> the renderer captures
 *     world:  world,                              // rasterised content (RGBA)
 *     camera: { T: camPoseAt },                   // analytic transform, origin 0,0: T(t)->{tx,ty,s}
 *     fps: 30, shutter: 1.0, spacing: 1.5, maxN: 48,
 *     bg: [1, 1, 1, 1]                            // clear colour (out-of-bounds); null = transparent
 *   });
 *
 *   var drv = { v: 0 };
 *   tl.to(drv, { v: 1, duration: DUR, ease: "none", onUpdate: function(){ blur.render(drv.v*DUR); } }, 0);
 *   blur.render(0);
 *
 * `camera.T(t)` must be a PURE function of t (deterministic, seek-safe): no
 * Date.now / Math.random / network. See analyticMotionVector() for the primitive.
 * ==========================================================================*/
(function (root) {
  "use strict";

  // The core primitive: motion vector = d/dt of a transform function (central difference).
  // T(t) -> {tx,ty,s[,rot]}; returns {tx,ty,s[,rot]} per-second derivatives.
  function analyticMotionVector(T, t, eps) {
    eps = eps || 1e-3;
    var a = T(t - eps), b = T(t + eps), k = 1 / (2 * eps);
    return {
      tx: (b.tx - a.tx) * k,
      ty: (b.ty - a.ty) * k,
      s: (b.s - a.s) * k,
      rot: ((b.rot || 0) - (a.rot || 0)) * k
    };
  }

  // ----------------------------------------------------------------------------
  // Blur presets — a bridge from LottieFiles motion-design's material/weight
  // easing vocabulary (skill: motion-design, reference/timing-easing-tables.md)
  // to blur knobs, so blur DIRECTION matches how the move is meant to FEEL.
  //
  // The physics linking the two tables:
  //   • shutter    -> trail length (EXP = shutter/fps). Heavier + more fluid
  //                   materials read as longer trails; brittle/light read short.
  //   • maxN,spacing -> trail smoothness. An OVERSHOOT ease (elastic/back) reverses
  //                   velocity at the snap-back, spiking peak per-pixel velocity;
  //                   without denser samples (higher maxN, lower spacing) that
  //                   spike bands/strobes. So overshoot in the ease FORCES denser
  //                   sampling — that is why elastic/gas carry high maxN.
  // `ease` is the matching GSAP ease for the CAMERA tween (advisory — the caller
  // applies it; the blur only consumes shutter/spacing/maxN).
  var PRESETS = {
    // material (motion-design "Material-Based Easing")           shutter spacing maxN  ease
    rigid:   { shutter: 1.0,  spacing: 1.5,  maxN: 48, ease: "power2.inOut", note: "metal/stone — clean, 0% overshoot" },
    elastic: { shutter: 0.6,  spacing: 1.0,  maxN: 72, ease: "back.out(1.7)", note: "rubber/gel — snap-back spike needs dense samples" },
    fluid:   { shutter: 1.8,  spacing: 1.75, maxN: 80, ease: "sine.inOut",   note: "water/paint — long smeary trail" },
    paper:   { shutter: 0.5,  spacing: 1.5,  maxN: 40, ease: "power2.out",   note: "cards/sheets — 180 film look" },
    gas:     { shutter: 2.5,  spacing: 2.5,  maxN: 96, ease: "sine.inOut",   note: "smoke/fog — diffuse, very long" },
    glass:   { shutter: 0.35, spacing: 2.0,  maxN: 24, ease: "power4.out",   note: "brittle — crisp, minimal smear" },
    // weight (motion-design "Weight Classification")
    heavy:   { shutter: 1.2,  spacing: 1.25, maxN: 64, ease: "power3.out",   note: "modals/overlays — decisive, smooth" },
    medium:  { shutter: 0.7,  spacing: 1.5,  maxN: 48, ease: "power2.inOut", note: "cards/panels" },
    light:   { shutter: 0.4,  spacing: 2.0,  maxN: 24, ease: "power2.out",   note: "tooltips/badges/icons — snappy" },
    // filmic default (180 shutter angle)
    film:    { shutter: 0.5,  spacing: 1.5,  maxN: 48, ease: "power2.inOut", note: "neutral 180 baseline" }
  };
  // Look up a preset by material/weight name; merge optional overrides on top.
  function blurPreset(name, overrides) {
    var base = PRESETS[name] || PRESETS.film, out = {};
    for (var k in base) if (base.hasOwnProperty(k)) out[k] = base[k];
    if (overrides) for (var j in overrides) if (overrides.hasOwnProperty(j)) out[j] = overrides[j];
    return out;
  }

  var VS = "attribute vec2 p; varying vec2 vUv; void main(){ vUv = p*0.5+0.5; gl_Position = vec4(p,0.0,1.0); }";
  var FS = [
    "precision highp float;",
    "uniform sampler2D uTex; uniform vec2 uRes; uniform vec2 uWorld;",
    "uniform vec2 uT; uniform float uS;",     // camera translate + scale at t
    "uniform vec2 uDT; uniform float uDS;",   // analytic derivatives dT/dt, dS/dt
    "uniform float uExp; uniform int uN;",    // exposure (s), sample count
    "uniform vec4 uBg; uniform float uHasBg;",
    "varying vec2 vUv;",
    "void main(){",
    "  vec2 ps = vec2(vUv.x, 1.0-vUv.y) * uRes;",           // screen pixel (top-left origin)
    "  vec2 vel = uDS*(ps-uT)/uS + uDT;",                    // ANALYTIC per-pixel velocity (px/s)
    "  vec2 disp = vel * uExp;",                             // smear vector over the shutter
    "  vec4 acc = vec4(0.0);",
    "  for(int i=0;i<128;i++){",
    "    if(i>=uN) break;",
    "    float f = (uN>1) ? (float(i)/float(uN-1) - 0.5) : 0.0;",
    "    vec2 sp = ps - disp*f;",                            // walk along the trail
    "    vec2 uv = ((sp - uT)/uS) / uWorld;",                // inverse camera -> world uv (world units = world texture px)
    "    vec4 c = (uv.x<0.0||uv.x>1.0||uv.y<0.0||uv.y>1.0) ? (uHasBg>0.5?uBg:vec4(0.0)) : texture2D(uTex, uv);",
    "    acc += c;",
    "  }",
    "  gl_FragColor = acc / float(uN);",
    "}"
  ].join("\n");

  function compile(gl, type, src) { var s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; }

  function createCameraBlur(cfg) {
    var canvas = cfg.canvas;
    var W = cfg.res ? cfg.res[0] : (canvas.width || 1920);
    var H = cfg.res ? cfg.res[1] : (canvas.height || 1080);
    canvas.width = W; canvas.height = H;
    var gl = canvas.getContext("webgl", { preserveDrawingBuffer: true, antialias: true, premultipliedAlpha: false });
    // A preset (material/weight name, or a preset object) fills shutter/spacing/maxN;
    // any explicit cfg.shutter / cfg.spacing / cfg.maxN still overrides it.
    var pre = cfg.preset ? (typeof cfg.preset === "string" ? blurPreset(cfg.preset) : cfg.preset) : null;
    var fps = cfg.fps || 30,
        shutter = cfg.shutter == null ? (pre ? pre.shutter : 1.0) : cfg.shutter,
        spacing = cfg.spacing || (pre ? pre.spacing : 1.5),
        maxN = cfg.maxN || (pre ? pre.maxN : 48), EXP = shutter / fps, EPS = 1e-3;
    var bg = cfg.bg || null;

    var prog = gl.createProgram();
    gl.attachShader(prog, compile(gl, gl.VERTEX_SHADER, VS));
    gl.attachShader(prog, compile(gl, gl.FRAGMENT_SHADER, FS));
    gl.linkProgram(prog); gl.useProgram(prog);
    var buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    var lp = gl.getAttribLocation(prog, "p"); gl.enableVertexAttribArray(lp); gl.vertexAttribPointer(lp, 2, gl.FLOAT, false, 0, 0);
    var tex = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
    var U = {}; ["uTex", "uRes", "uWorld", "uT", "uS", "uDT", "uDS", "uExp", "uN", "uBg", "uHasBg"].forEach(function (n) { U[n] = gl.getUniformLocation(prog, n); });
    gl.viewport(0, 0, W, H);
    gl.uniform1i(U.uTex, 0);
    gl.uniform4f(U.uBg, bg ? bg[0] : 0, bg ? bg[1] : 0, bg ? bg[2] : 0, bg ? bg[3] : 0);
    gl.uniform1f(U.uHasBg, bg ? 1 : 0);

    // World size in world units. Defaults to the world source's own pixel size so a panel
    // of any W×H can pan over a texture of any size (world px == world units); a caller can
    // still pin it via cfg.worldSize. With a W×H world texture this equals the old behaviour.
    var worldW = W, worldH = H;
    function updateWorld(src) {
      gl.bindTexture(gl.TEXTURE_2D, tex); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, src);
      var sw = src.naturalWidth || src.width, sh = src.naturalHeight || src.height;
      if (cfg.worldSize) { worldW = cfg.worldSize[0]; worldH = cfg.worldSize[1]; }
      else if (sw && sh) { worldW = sw; worldH = sh; }
    }
    if (cfg.world) updateWorld(cfg.world);

    // camera transform normaliser: accept {tx,ty,s} or {x,y,scale}
    function norm(p) { return { tx: p.tx != null ? p.tx : p.x, ty: p.ty != null ? p.ty : p.y, s: p.s != null ? p.s : p.scale }; }
    var camT = function (t) { return norm(cfg.camera.T(t)); };

    function render(t) {
      var c = camT(t), a = camT(t - EPS), b = camT(t + EPS), k = 1 / (2 * EPS);
      var dtx = (b.tx - a.tx) * k, dty = (b.ty - a.ty) * k, ds = (b.s - a.s) * k;
      // adaptive sample count from the worst-corner smear length (keeps ~spacing px per ghost)
      var v0x = ds * (0 - c.tx) / c.s + dtx, v0y = ds * (0 - c.ty) / c.s + dty;
      var v1x = ds * (W - c.tx) / c.s + dtx, v1y = ds * (H - c.ty) / c.s + dty;
      var maxDisp = Math.max(Math.hypot(v0x, v0y), Math.hypot(v1x, v1y)) * EXP;
      var N = Math.max(1, Math.min(maxN, Math.ceil(maxDisp / spacing)));
      gl.useProgram(prog); gl.bindTexture(gl.TEXTURE_2D, tex);
      gl.uniform2f(U.uRes, W, H); gl.uniform2f(U.uWorld, worldW, worldH); gl.uniform2f(U.uT, c.tx, c.ty); gl.uniform1f(U.uS, c.s);
      gl.uniform2f(U.uDT, dtx, dty); gl.uniform1f(U.uDS, ds); gl.uniform1f(U.uExp, EXP); gl.uniform1i(U.uN, N);
      if (bg) { gl.clearColor(bg[0], bg[1], bg[2], bg[3]); } else { gl.clearColor(0, 0, 0, 0); gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA); }
      gl.clear(gl.COLOR_BUFFER_BIT);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      return N;
    }

    return { render: render, updateWorld: updateWorld, motionVector: function (t) { return analyticMotionVector(camT, t); } };
  }

  var api = { analyticMotionVector: analyticMotionVector, createCameraBlur: createCameraBlur, blurPreset: blurPreset, PRESETS: PRESETS };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  root.HFMotionBlur = api;
})(typeof window !== "undefined" ? window : this);
