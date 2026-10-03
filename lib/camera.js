/* ============================================================================
 * HFCamera — world + camera rig: keyed poses, legs, holds, whips, pushes
 * ----------------------------------------------------------------------------
 * Extracted from video 09's lib/house.js (camera, push), brand removed, any aspect.
 * Absorbs cameraLeg from the retired lib/demo-transitions.js: a rig without a blur
 * canvas is a plain DOM camera.
 *
 * Pure function of time: the pose at t depends on t only (keys + profile ease), and
 * one driver tween per rig recomputes it on every seek. During a blur leg the rig shows
 * an HFMotionBlur canvas over a baked world texture; outside legs it shows the DOM and
 * releases the WebGL context (~16 live contexts per page).
 *
 * Load after profile.js and motion-blur.js.
 * ==========================================================================*/
(function (root) {
  "use strict";
  var NODE = typeof module !== "undefined" && module.exports;
  var P = NODE ? require("./profile.js") : root.HFProfile;
  function MB() { return NODE ? require("./motion-blur.js") : root.HFMotionBlur; }

  function lerp(a, b, f) { return a + (b - a) * f; }

  // keys: [{t, cx, cy, z, ease?}] — at time t the design point (cx, cy) sits at screen centre at zoom z.
  // The segment a -> b eases on b.ease (a token name) or defaultEase. Equal neighbouring poses = a hold.
  function track(keys, format, defaultEase) {
    if (!keys || !keys.length) throw new Error("HFCamera: keys must hold at least one pose");
    var ks = keys.slice().sort(function (a, b) { return a.t - b.t; });
    var eases = ks.map(function (k) { return P.ease(format, k.ease || defaultEase || "ease.camera"); });
    return function (t) {
      if (t <= ks[0].t) return { cx: ks[0].cx, cy: ks[0].cy, z: ks[0].z };
      for (var i = 0; i < ks.length - 1; i++) {
        var a = ks[i], b = ks[i + 1];
        if (t >= a.t && t <= b.t) {
          var f = b.t === a.t ? 1 : eases[i + 1]((t - a.t) / (b.t - a.t));
          return { cx: lerp(a.cx, b.cx, f), cy: lerp(a.cy, b.cy, f), z: lerp(a.z, b.z, f) };
        }
      }
      var l = ks[ks.length - 1];
      return { cx: l.cx, cy: l.cy, z: l.z };
    };
  }

  // DOM transform (transform-origin 0 0) that puts design point (cx, cy) at the centre of a W x H frame.
  function domTransform(p, W, H) { return { dx: W / 2 - p.z * p.cx, dy: H / 2 - p.z * p.cy, z: p.z }; }

  // HFMotionBlur pose for a world texture of (W*K) x (H*K) px whose design origin sits at
  // PAD = ((K-1)/2)*(W, H). World units are texture px, so design point p maps to texture px PAD + p.
  function glPose(p, W, H, K) {
    var d = domTransform(p, W, H), padX = (K - 1) / 2 * W, padY = (K - 1) / 2 * H;
    return { tx: d.dx - d.z * padX, ty: d.dy - d.z * padY, s: d.z };
  }

  function normLeg(L) {
    if (Array.isArray(L)) return { from: L[0], to: L[1], kind: "leg" };
    return { from: L.from, to: L.to, kind: L.kind || "leg" };
  }

  /* cfg = {
   *   format: "long-form" | "shorts"      (required — picks eases and blur shutter)
   *   width, height                         (required — the frame, any aspect)
   *   stage                                 the DOM camera wrapper (design coords, origin 0 0)
   *   keys: [{t, cx, cy, z, ease?}]         poses in rig-local time
   *   dur                                   rig duration; at: where it starts on tl (default 0)
   *   ease                                  default segment token (default "ease.camera")
   * blur legs (optional — omit canvas for a plain DOM camera):
   *   canvas                                <canvas> covering the frame, stacked above the stage
   *   legs: [[t0, t1] | {from, to, kind}]   kind = HFMotionBlur.profilePreset kind ("leg", "whip")
   *   bake(ctx, K, t)                       paints the world in design coords (PAD already applied);
   *                                         called ONCE with t = 0 (the settled layout) unless liveBake,
   *                                         which re-bakes at every frame inside a leg with that frame's t
   *   bg                                    [r,g,b,1] out-of-bounds colour, or null (required with canvas)
   *   bgCss                                 opaque ground fill for the texture (omit = transparent)
   *   K (1.5), fps (30), liveBake, liveMedia (as in house.js)
   * } */
  function rig(tl, cfg) {
    var W = cfg.width, H = cfg.height, K = cfg.K || 1.5, at = cfg.at || 0;
    if (!(W > 0 && H > 0)) throw new Error("HFCamera.rig: width and height are required (no default aspect)");
    if (!(cfg.dur > 0)) throw new Error("HFCamera.rig: dur is required");
    var pose = track(cfg.keys, cfg.format, cfg.ease);
    var legs = (cfg.legs || []).map(normLeg);
    var stage = cfg.stage, canvas = cfg.canvas || null;
    if (canvas && legs.length) {
      if (!("bg" in cfg)) throw new Error("HFCamera.rig: bg is required with a blur canvas ([r,g,b,1] or null)");
      if (typeof cfg.bake !== "function") throw new Error("HFCamera.rig: bake(ctx, K, t) is required with a blur canvas");
      legs.forEach(function (L) { MB().profilePreset(cfg.format, L.kind); });   // fail at build, not mid-render
    }
    var blur = null, blurKind = null, world = null, worldCtx = null, glFailed = false;
    stage.style.transformOrigin = "0 0"; stage.style.willChange = "transform";
    if (canvas) {
      var cs = canvas.style;
      cs.position = "absolute"; cs.left = "0"; cs.top = "0"; cs.width = W + "px"; cs.height = H + "px";
      cs.zIndex = "40"; cs.pointerEvents = "none"; cs.opacity = "0"; cs.visibility = "hidden";
    }
    function dom(t) { return domTransform(pose(t), W, H); }
    function gl(t) { return glPose(pose(t), W, H, K); }
    function paintWorld(t) {
      if (!cfg.bgCss || cfg.bgCss === "transparent") worldCtx.clearRect(0, 0, world.width, world.height);
      else { worldCtx.fillStyle = cfg.bgCss; worldCtx.fillRect(0, 0, world.width, world.height); }
      worldCtx.save(); worldCtx.translate((K - 1) / 2 * W, (K - 1) / 2 * H); cfg.bake(worldCtx, K, t); worldCtx.restore();
    }
    function legAt(t) { for (var i = 0; i < legs.length; i++) if (t >= legs[i].from && t < legs[i].to) return legs[i]; return null; }
    function release() { if (blur) { try { blur.dispose(); } catch (e) {} blur = null; blurKind = null; canvas.__hfLost = true; } }
    function ensure(kind) {
      if (blur && blurKind === kind) return;
      release();
      if (glFailed || !MB()) return;
      if (!world) { world = document.createElement("canvas"); world.width = Math.round(W * K); world.height = Math.round(H * K); worldCtx = world.getContext("2d"); paintWorld(0); }
      // A lost context leaves the old <canvas> unusable: swap in a fresh element before re-creating.
      if (canvas.__hfLost) {
        if (!canvas.parentNode) { glFailed = true; if (root.console) console.warn("HFCamera: blur canvas is not attached, showing the DOM pose"); return; }
        var fresh = canvas.cloneNode(false); fresh.__hfLost = false; canvas.parentNode.replaceChild(fresh, canvas); canvas = fresh;
      }
      canvas.width = W; canvas.height = H;
      try {
        blur = MB().createCameraBlur({ canvas: canvas, res: [W, H], world: world, camera: { T: gl }, fps: cfg.fps || 30,
          preset: MB().profilePreset(cfg.format, kind), bg: cfg.bg });
        blurKind = kind;
      } catch (e) { glFailed = true; blur = null; if (root.console) console.warn("HFCamera: blur unavailable, showing the DOM pose (" + (e && e.message) + ")"); }
    }
    var drv = { t: 0 }, lastT = 0;
    function tick(t) {
      var d = dom(t);
      stage.style.transform = "translate(" + d.dx.toFixed(2) + "px," + d.dy.toFixed(2) + "px) scale(" + d.z.toFixed(4) + ")";
      if (!canvas) return;
      var L = legAt(t);
      if (L) {
        ensure(L.kind);
        if (blur) {
          if (cfg.liveBake) { paintWorld(t); blur.updateWorld(world); }
          blur.render(t);
          if (blur.gl && blur.gl.isContextLost()) {   // lost mid-leg: render() no-ops silently, so fall back to the DOM pose
            glFailed = true; release();
            if (root.console) console.warn("HFCamera: WebGL context lost mid-leg, showing the DOM pose");
          } else { canvas.style.opacity = "1"; canvas.style.visibility = "visible"; return; }
        }
      }
      canvas.style.opacity = "0"; canvas.style.visibility = "hidden";
      release();
    }
    tl.fromTo(drv, { t: 0 }, { t: cfg.dur, duration: cfg.dur, ease: "none", immediateRender: false,
      onUpdate: function () { lastT = drv.t; tick(drv.t); } }, at);
    // liveBake + <video>: a seek on the element is async, so repaint the leg when the decoded frame changes.
    (cfg.liveMedia || []).forEach(function (m) {
      var lastVt = -1;
      function repaint() { if (legAt(lastT) && m.currentTime !== lastVt) { lastVt = m.currentTime; tick(lastT); } }
      ["seeked", "loadeddata", "canplay", "timeupdate", "playing", "pause"].forEach(function (ev) { m.addEventListener(ev, repaint); });
      if (m.requestVideoFrameCallback) { (function arm() { m.requestVideoFrameCallback(function () { repaint(); arm(); }); })(); }
    });
    var d0 = dom(0);
    stage.style.transform = "translate(" + d0.dx.toFixed(2) + "px," + d0.dy.toFixed(2) + "px) scale(" + d0.z.toFixed(4) + ")";
    return { pose: pose, dom: dom, gl: gl, refresh: function () { tick(lastT); } };
  }

  /* Scale pushes on one element (holds, emphasis). ALL segments in one call -> one driver, so the
   * scale is a pure function of t whatever order the renderer seeks in (two fromTo tweens on one
   * element rendered alternate frames in different positions — the house.js push flicker).
   * segments: [{T, dur, from, to}]; opts: {format, ease, origin}.
   * Default ease: long-form "ease.camera.slow"; Shorts "ease.camera" (the profile has no slow ease). */
  function push(tl, el, segments, opts) {
    opts = opts || {};
    if (el.__hfPush) throw new Error("HFCamera.push: element already has pushes — pass every segment in one call");
    if (!segments || !segments.length) throw new Error("HFCamera.push: segments must not be empty");
    var e = P.ease(opts.format, opts.ease || (opts.format === "long-form" ? "ease.camera.slow" : "ease.camera"));
    var segs = segments.slice().sort(function (a, b) { return a.T - b.T; });
    for (var i = 1; i < segs.length; i++) {
      if (segs[i].T < segs[i - 1].T + segs[i - 1].dur) throw new Error("HFCamera.push: segments overlap at t=" + segs[i].T);
    }
    function scaleAt(t) {
      if (t <= segs[0].T) return segs[0].from;
      for (var j = 0; j < segs.length; j++) {
        var s = segs[j];
        if (t < s.T) return segs[j - 1].to;
        if (t <= s.T + s.dur) return s.from + (s.to - s.from) * e((t - s.T) / s.dur);
      }
      return segs[segs.length - 1].to;
    }
    el.__hfPush = true;
    el.style.transformOrigin = opts.origin || "50% 50%";
    el.style.transform = "scale(" + segs[0].from + ")";
    var start = segs[0].T, end = segs[segs.length - 1].T + segs[segs.length - 1].dur, drv = { t: start };
    tl.fromTo(drv, { t: start }, { t: end, duration: end - start, ease: "none", immediateRender: false,
      onUpdate: function () { el.style.transform = "scale(" + scaleAt(drv.t).toFixed(5) + ")"; } }, start);
    return scaleAt;
  }

  var api = { track: track, domTransform: domTransform, glPose: glPose, rig: rig, push: push };
  if (NODE) module.exports = api;
  root.HFCamera = api;
})(typeof window !== "undefined" ? window : this);
