/* ============================================================================
 * HFMotionBlur — analytic, deterministic motion blur for HyperFrames
 * ----------------------------------------------------------------------------
 * HyperFrames seeks every output frame independently (no wall clock), so motion
 * blur cannot be inferred from rendered pixels or frame-to-frame deltas. Instead
 * it is DERIVED FROM THE ANIMATION'S OWN MATH: every animated transform is a pure
 * function of time T(t) -> {tx, ty, s}. We differentiate it analytically to get
 * the motion vector, and a WebGL fragment shader marches samples along the real
 * per-pixel velocity of the camera transform — translation and zoom (radial)
 * both blur correctly. The scene content is rasterised to a texture ONCE (you
 * provide it), so there is no per-frame DOM cloning. The whole GL render is a
 * pure function of the given t.
 *
 * Aspect-agnostic: the output size is the canvas size (or cfg.res), never assumed;
 * world units are the world texture's own pixels (or cfg.worldSize), so any canvas
 * can pan over any texture.
 *
 * Merged 2026-10-03 from the three forks (root lib, video 09, the Shorts copies):
 * uWorld world sizing (root) + renderRegions, dispose and WebGL context-loss guards (09).
 *
 * USAGE
 *   var blur = HFMotionBlur.createCameraBlur({
 *     canvas: glCanvas,                       // the <canvas> the renderer captures (sized, or pass res)
 *     world:  bakedTexture,                   // canvas / img / ImageBitmap, OPAQUE ground painted in
 *     camera: { T: pose },                    // pure fn of t -> {tx, ty, s}: screen = s * world + t
 *     fps: 30, preset: HFMotionBlur.profilePreset("long-form", "leg"),
 *     bg: [r, g, b, 1]                        // out-of-bounds colour; null = transparent
 *   });
 *   blur.render(t);                           // from the timeline's onUpdate
 *   blur.dispose();                           // free the context when the leg ends (~16 live per page)
 * ==========================================================================*/
(function (root) {
  "use strict";

  // The core primitive: motion vector = d/dt of a transform function (central difference).
  function analyticMotionVector(T, t, eps) {
    eps = eps || 1e-3;
    var a = T(t - eps), b = T(t + eps), k = 1 / (2 * eps);
    return { tx: (b.tx - a.tx) * k, ty: (b.ty - a.ty) * k, s: (b.s - a.s) * k, rot: ((b.rot || 0) - (a.rot || 0)) * k };
  }

  // Shutter per format profile and move kind. shutter is in frames: 1.0 = 360°, 0.5 = 180°.
  // Values: standards/formats/long-form.md and shorts.md ("motion blur" rows).
  var PROFILE_PRESETS = {
    "long-form": {
      leg:  { shutter: 0.25, spacing: 1.5,  maxN: 48 },   // 90° — ordinary legs read as ≈ no blur
      whip: { shutter: 0.5,  spacing: 1.5,  maxN: 64 },   // 180° directional whip
      roll: { shutter: 0.4,  spacing: 1.25, maxN: 48 }    // 144° odometer digit roll
    },
    "shorts": {
      leg:  { shutter: 0.7,  spacing: 1.5,  maxN: 48 },   // 252° — the reels' camera legs (short4 practice)
      roll: { shutter: 0.4,  spacing: 1.25, maxN: 48 }    // 144° odometer digit roll
    }
  };
  function profilePreset(format, kind) {
    var f = PROFILE_PRESETS[format];
    if (!f) throw new Error("HFMotionBlur: unknown format " + JSON.stringify(format));
    var p = f[kind];
    if (!p) throw new Error("HFMotionBlur: " + format + " has no " + JSON.stringify(kind) + " blur (have: " + Object.keys(f).join(", ") + ")");
    return { shutter: p.shutter, spacing: p.spacing, maxN: p.maxN, angle: p.shutter * 360 };
  }

  // Generic material/weight presets, kept for frozen-era callers. New work uses profilePreset().
  var PRESETS = {
    rigid:   { shutter: 1.0,  spacing: 1.5,  maxN: 48, note: "clean, long trail" },
    elastic: { shutter: 0.6,  spacing: 1.0,  maxN: 72, note: "dense samples" },
    fluid:   { shutter: 1.8,  spacing: 1.75, maxN: 80, note: "long smeary trail" },
    paper:   { shutter: 0.5,  spacing: 1.5,  maxN: 40, note: "180° film look" },
    gas:     { shutter: 2.5,  spacing: 2.5,  maxN: 96, note: "diffuse, very long" },
    glass:   { shutter: 0.35, spacing: 2.0,  maxN: 24, note: "crisp, minimal smear" },
    heavy:   { shutter: 1.2,  spacing: 1.25, maxN: 64, note: "decisive, smooth" },
    medium:  { shutter: 0.7,  spacing: 1.5,  maxN: 48, note: "cards/panels" },
    light:   { shutter: 0.4,  spacing: 2.0,  maxN: 24, note: "snappy" },
    film:    { shutter: 0.5,  spacing: 1.5,  maxN: 48, note: "neutral 180° baseline" }
  };
  function blurPreset(name, overrides) {
    var base = PRESETS[name] || PRESETS.film, out = {};
    for (var k in base) if (base.hasOwnProperty(k)) out[k] = base[k];
    if (overrides) for (var j in overrides) if (overrides.hasOwnProperty(j)) out[j] = overrides[j];
    return out;
  }

  // The fragment shader's loop is capped at 128 iterations; uN above that would silently truncate the trail
  // (and divide by the wrong count), so every sample count is clamped to it.
  var MAX_SAMPLES = 128;
  // Samples needed so ghosts sit ~spacing px apart along the worst smear in the rect.
  // c = pose, d = its time derivative; checks all four corners (velocity is affine in screen position).
  function sampleCount(c, d, x0, y0, x1, y1, exp, spacing, maxN) {
    var worst = 0, xs = [x0, x1], ys = [y0, y1];
    for (var i = 0; i < 2; i++) for (var j = 0; j < 2; j++) {
      var vx = d.s * (xs[i] - c.tx) / c.s + d.tx, vy = d.s * (ys[j] - c.ty) / c.s + d.ty;
      worst = Math.max(worst, Math.hypot(vx, vy));
    }
    return Math.max(1, Math.min(MAX_SAMPLES, maxN, Math.ceil(worst * exp / spacing)));
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
    "    vec2 uv = ((sp - uT)/uS) / uWorld;",                // inverse camera -> world uv (world units = texture px)
    "    vec4 c = (uv.x<0.0||uv.x>1.0||uv.y<0.0||uv.y>1.0) ? (uHasBg>0.5?uBg:vec4(0.0)) : texture2D(uTex, uv);",
    "    acc += c;",
    "  }",
    "  gl_FragColor = acc / float(uN);",
    "}"
  ].join("\n");

  function compile(gl, type, src) {
    var s = gl.createShader(type);
    if (!s) throw new Error("HFMotionBlur: WebGL context lost (too many live contexts?)");
    gl.shaderSource(s, src); gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error("HFMotionBlur shader: " + (gl.getShaderInfoLog(s) || "no log — context lost?"));
    return s;
  }

  function createCameraBlur(cfg) {
    var canvas = cfg.canvas;
    var W = cfg.res ? cfg.res[0] : canvas.width, H = cfg.res ? cfg.res[1] : canvas.height;
    if (!(W > 0 && H > 0)) throw new Error("HFMotionBlur: canvas has no size — set canvas.width/height or pass res: [w, h]");
    canvas.width = W; canvas.height = H;
    var gl = canvas.getContext("webgl", { preserveDrawingBuffer: true, antialias: true, premultipliedAlpha: false });
    if (!gl || gl.isContextLost()) throw new Error("HFMotionBlur: could not create a WebGL context (browser limit is ~16 live contexts — dispose blurs you are not showing)");
    // A preset (profilePreset() object, or a legacy material/weight name) fills shutter/spacing/maxN;
    // explicit cfg.shutter / cfg.spacing / cfg.maxN still override it.
    var pre = cfg.preset ? (typeof cfg.preset === "string" ? blurPreset(cfg.preset) : cfg.preset) : null;
    var fps = cfg.fps || 30,
        shutter = cfg.shutter == null ? (pre ? pre.shutter : 1.0) : cfg.shutter,
        spacing = cfg.spacing || (pre ? pre.spacing : 1.5),
        maxN = Math.min(MAX_SAMPLES, cfg.maxN || (pre ? pre.maxN : 48)), EXP = shutter / fps, EPS = 1e-3;
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

    // World size in world units: the world source's own pixel size, unless pinned by cfg.worldSize.
    var worldW = W, worldH = H;
    function updateWorld(src) {
      gl.bindTexture(gl.TEXTURE_2D, tex); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, src);
      var sw = src.naturalWidth || src.width, sh = src.naturalHeight || src.height;
      if (cfg.worldSize) { worldW = cfg.worldSize[0]; worldH = cfg.worldSize[1]; }
      else if (sw && sh) { worldW = sw; worldH = sh; }
    }
    if (cfg.world) updateWorld(cfg.world);

    // camera transform normaliser: accept {tx,ty,s} or {x,y,scale}; no camera = identity
    function norm(p) { return { tx: p.tx != null ? p.tx : p.x, ty: p.ty != null ? p.ty : p.y, s: p.s != null ? p.s : p.scale }; }
    var camT = function (t) { return norm(cfg.camera ? cfg.camera.T(t) : { tx: 0, ty: 0, s: 1 }); };

    function clearFrame() {
      gl.disable(gl.SCISSOR_TEST);
      if (bg) { gl.clearColor(bg[0], bg[1], bg[2], bg[3]); gl.disable(gl.BLEND); }
      else { gl.clearColor(0, 0, 0, 0); gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA); }
      gl.clear(gl.COLOR_BUFFER_BIT);
    }
    function drawPose(T, t, x0, y0, x1, y1) {
      var c = T(t), a = T(t - EPS), b = T(t + EPS), k = 1 / (2 * EPS);
      var d = { tx: (b.tx - a.tx) * k, ty: (b.ty - a.ty) * k, s: (b.s - a.s) * k };
      var N = sampleCount(c, d, x0, y0, x1, y1, EXP, spacing, maxN);
      gl.uniform2f(U.uRes, W, H); gl.uniform2f(U.uWorld, worldW, worldH);
      gl.uniform2f(U.uT, c.tx, c.ty); gl.uniform1f(U.uS, c.s);
      gl.uniform2f(U.uDT, d.tx, d.ty); gl.uniform1f(U.uDS, d.s); gl.uniform1f(U.uExp, EXP); gl.uniform1i(U.uN, N);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      return N;
    }

    function render(t) {
      gl.useProgram(prog); gl.bindTexture(gl.TEXTURE_2D, tex);
      clearFrame();
      return drawPose(camT, t, 0, 0, W, H);
    }

    // Several independent transforms on ONE canvas/context: each region {x,y,w,h,T} (canvas px) is
    // scissored and marched with its own per-pixel velocity (odometer digit columns).
    function renderRegions(t, regions) {
      gl.useProgram(prog); gl.bindTexture(gl.TEXTURE_2D, tex);
      clearFrame();
      gl.enable(gl.SCISSOR_TEST);
      var maxNUsed = 1;
      for (var i = 0; i < regions.length; i++) {
        var R = regions[i], TT = (function (R) { return function (tt) { return norm(R.T(tt)); }; })(R);
        gl.scissor(Math.round(R.x), Math.round(H - R.y - R.h), Math.round(R.w), Math.round(R.h));
        var N = drawPose(TT, t, R.x, R.y, R.x + R.w, R.y + R.h);
        if (N > maxNUsed) maxNUsed = N;
      }
      gl.disable(gl.SCISSOR_TEST);
      return maxNUsed;
    }
    function dispose() { try { var ext = gl.getExtension("WEBGL_lose_context"); if (ext) ext.loseContext(); } catch (e) {} }

    return { render: render, renderRegions: renderRegions, updateWorld: updateWorld, dispose: dispose, gl: gl,
      size: function () { return { width: W, height: H, worldWidth: worldW, worldHeight: worldH }; },
      motionVector: function (t) { return analyticMotionVector(camT, t); } };
  }

  var api = { analyticMotionVector: analyticMotionVector, createCameraBlur: createCameraBlur, blurPreset: blurPreset,
    PRESETS: PRESETS, profilePreset: profilePreset, PROFILE_PRESETS: PROFILE_PRESETS, sampleCount: sampleCount, MAX_SAMPLES: MAX_SAMPLES };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  root.HFMotionBlur = api;
})(typeof window !== "undefined" ? window : this);
