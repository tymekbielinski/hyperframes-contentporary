/* ============================================================================
 * HFWipe — the Shorts masked, motion-blurred scene wipe (standards/formats/shorts.md §1)
 * ----------------------------------------------------------------------------
 * A travelling soft-edged gradient MASK reveals/hides the host while a directional
 * feGaussianBlur smears it along the travel axis (the named Gaussian exception: the
 * blur element is tagged data-blur-reason="wipe"). Blur and feather ride the wipe's
 * SPEED, 4q(1-q): nothing at either end, maximum mid-travel. ease.cut (Shorts) =
 * cubic-bezier(0.65, 0, 0.35, 1), solved by bisection.
 *
 * From the inline Shorts prelude (videos/short4 wipeInOut — filter attached only while
 * travelling, which avoids the background-clip:text ghost) and house.js wipeIn/wipeOut/phaseWipe.
 * One driver per wipe: the mask is a pure function of t. Long-form never uses this.
 * Load after ../profile.js.
 * ==========================================================================*/
(function (root) {
  "use strict";
  var NODE = typeof module !== "undefined" && module.exports;
  var P = NODE ? require("../profile.js") : root.HFProfile;
  var W = P.timing("shorts").wipe, EASE = P.ease("shorts", "ease.cut");
  var GRAD = { left: "to left", right: "to right", down: "to bottom", up: "to top" };

  // Visual state for eased progress q (0 hidden … 1 fully revealed).
  function wipeState(q, blurMax, dir) {
    if (!GRAD[dir]) throw new Error("HFWipe: dir must be left, right, up or down (got " + JSON.stringify(dir) + ")");
    var horiz = dir === "left" || dir === "right";
    if (q >= 1) return { std: horiz ? "0.00 0" : "0 0.00", mask: "none", filterOn: false };
    var speed = 4 * q * (1 - q), v = (blurMax * speed).toFixed(2);
    var std = horiz ? v + " 0" : "0 " + v;
    if (q <= 0) return { std: std, mask: "linear-gradient(" + GRAD[dir] + ", rgba(0,0,0,0) 0%, rgba(0,0,0,0) 100%)", filterOn: false };
    var F = W.featherMin + W.featherGain * speed, a = q * (100 + F) - F, b = a + F;
    return { std: std, mask: "linear-gradient(" + GRAD[dir] + ", rgba(0,0,0,1) " + a.toFixed(2) + "%, rgba(0,0,0,0) " + b.toFixed(2) + "%)", filterOn: true };
  }

  // Eased progress + blur cap at time t for a wipe that reveals at inAt and/or is fully hidden by outAt.
  function wipeProgress(t, inAt, outAt) {
    if (outAt != null && t >= outAt) return { q: 0, blurMax: W.blurOut };
    if (inAt != null && t < inAt + W.inDur) return { q: EASE(Math.max(0, (t - inAt) / W.inDur)), blurMax: W.blurIn };
    if (outAt != null && t > outAt - W.outDur) return { q: 1 - EASE(Math.min(1, (t - (outAt - W.outDur)) / W.outDur)), blurMax: W.blurOut };
    return { q: 1, blurMax: W.blurIn };
  }

  /* cfg = { host, fe (the <feGaussianBlur>), filterId (its <filter> id), dir, inAt?, outAt? }
   * inAt: reveal starts (0.42 s in). outAt: host fully hidden (0.36 s out ends there). At least one.
   * The host should start hidden in CSS (visibility: hidden) when it has an inAt. */
  function wipe(tl, cfg) {
    var host = cfg.host, fe = cfg.fe, inAt = cfg.inAt, outAt = cfg.outAt;
    if (inAt == null && outAt == null) throw new Error("HFWipe: pass inAt, outAt or both");
    if (inAt != null && outAt != null && outAt - inAt < W.inDur + W.outDur) {
      throw new Error("HFWipe: scene too short for a wipe in and out (" + (outAt - inAt).toFixed(2) + " s < " + (W.inDur + W.outDur) + " s)");
    }
    wipeState(1, 0, cfg.dir);   // validates dir at build time
    if (fe) fe.setAttribute("data-blur-reason", "wipe");
    if (inAt != null) host.style.visibility = "hidden";   // hidden until its wipe starts, whatever the CSS says
    var start = inAt != null ? inAt : outAt - W.outDur, end = outAt != null ? outAt : inAt + W.inDur, drv = { t: start };
    function apply() {
      var p = wipeProgress(drv.t, inAt, outAt), s = wipeState(p.q, p.blurMax, cfg.dir);
      if (fe) fe.setAttribute("stdDeviation", s.std);
      host.style.webkitMaskImage = s.mask; host.style.maskImage = s.mask;
      host.style.filter = s.filterOn && cfg.filterId ? "url(#" + cfg.filterId + ")" : "none";
    }
    if (inAt != null) tl.set(host, { visibility: "visible", opacity: 1 }, inAt);
    tl.fromTo(drv, { t: start }, { t: end, duration: end - start, ease: "none", immediateRender: false, onUpdate: apply }, start);
    if (outAt != null) tl.set(host, { visibility: "hidden" }, outAt);
    return end - start;
  }

  // Phase handoff inside one scene: A wipes out while B wipes in 0.10 s later along the same axis.
  function phase(tl, outCfg, inCfg, T, dir) {
    wipe(tl, { host: outCfg.host, fe: outCfg.fe, filterId: outCfg.filterId, dir: dir, outAt: T + W.outDur });
    wipe(tl, { host: inCfg.host, fe: inCfg.fe, filterId: inCfg.filterId, dir: dir, inAt: T + 0.10 });
  }

  var api = { wipeState: wipeState, wipeProgress: wipeProgress, wipe: wipe, phase: phase, IN: W.inDur, OUT: W.outDur };
  if (NODE) module.exports = api;
  root.HFWipe = api;
})(typeof window !== "undefined" ? window : this);
