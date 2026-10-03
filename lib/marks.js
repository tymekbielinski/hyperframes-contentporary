/* ============================================================================
 * HFMarks — pass-2 annotation marks: highlight sweep, scribble underline, curved and
 * elbow connectors, ✕/✓ status chips, seed chips, strike-through, ring, group outline,
 * script write-on, global recolour swap
 * ----------------------------------------------------------------------------
 * De-duplicated from video 09's lib/house.js and the inline Shorts prelude
 * (videos/short2|3|4). Brand-free: marks never set a colour — style them with the
 * brand's CSS variables (lib/brand.js), e.g. stroke: var(--hf-accent-line).
 *
 * Path generators are pure (wobble is index-seeded, never Math.random). Binders add
 * tweens at explicit times with profile eases only (opts.format is required).
 * Load after profile.js.
 * ==========================================================================*/
(function (root) {
  "use strict";
  var NODE = typeof module !== "undefined" && module.exports;
  var P = NODE ? require("./profile.js") : root.HFProfile;

  function wob(i, amp) { return Math.sin(i * 12.9898) * amp; }
  function n1(v) { return v.toFixed(1); }

  // Hand-drawn ring: wobbled points smoothed Catmull-Rom -> cubic Béziers; overshoots the join like a pen.
  function ringPath(cx, cy, rx, ry, seed) {
    seed = seed || 1; var pts = [], N = 22;
    for (var i = 0; i <= N; i++) {
      var a = -0.6 + (i / N) * Math.PI * 2.08;
      var r1 = rx * (1 + wob(i + seed, 0.035)), r2 = ry * (1 + wob(i * 3 + seed, 0.045));
      pts.push([cx + r1 * Math.cos(a), cy + r2 * Math.sin(a)]);
    }
    function Pt(i) { return pts[Math.max(0, Math.min(pts.length - 1, i))]; }
    var d = "M" + n1(pts[0][0]) + " " + n1(pts[0][1]);
    for (var j = 0; j < pts.length - 1; j++) {
      var p0 = Pt(j - 1), p1 = Pt(j), p2 = Pt(j + 1), p3 = Pt(j + 2);
      d += " C" + n1(p1[0] + (p2[0] - p0[0]) / 6) + " " + n1(p1[1] + (p2[1] - p0[1]) / 6) + " " +
        n1(p2[0] - (p3[0] - p1[0]) / 6) + " " + n1(p2[1] - (p3[1] - p1[1]) / 6) + " " + n1(p2[0]) + " " + n1(p2[1]);
    }
    return d;
  }
  // Scribble underline: a slightly falling, wobbled polyline (one vertex per ~90 px).
  function scribblePath(x, y, w, seed) {
    seed = seed || 1; var d = "M" + x + " " + y, n = Math.max(3, Math.round(w / 90));
    for (var i = 1; i <= n; i++) d += " L" + n1(x + (w * i) / n) + " " + n1(y + wob(i + seed, 3.5) + i * 0.6);
    return d;
  }
  // Strike-through: one gently rising stroke across [x, x + w] at y.
  function strikePath(x, y, w, seed) {
    seed = seed || 1;
    return "M" + n1(x) + " " + n1(y + wob(seed, 2)) + " L" + n1(x + w) + " " + n1(y - w * 0.02 + wob(seed + 1, 2));
  }
  // Curved connector: quadratic arc with a signed bulge (px, perpendicular to the chord) + arrow head.
  function arrowPath(x1, y1, x2, y2, curve, headLen) {
    curve = curve == null ? 120 : curve; headLen = headLen || 30;
    var mx = (x1 + x2) / 2, my = (y1 + y2) / 2, dx = x2 - x1, dy = y2 - y1, L = Math.hypot(dx, dy) || 1;
    var cx = mx + (-dy / L) * curve, cy = my + (dx / L) * curve, ang = Math.atan2(y2 - cy, x2 - cx);
    return {
      shaft: "M" + x1 + " " + y1 + " Q " + n1(cx) + " " + n1(cy) + " " + x2 + " " + y2,
      head: "M" + n1(x2 + headLen * Math.cos(ang + 2.65)) + " " + n1(y2 + headLen * Math.sin(ang + 2.65)) + " L" + x2 + " " + y2 +
        " L" + n1(x2 + headLen * Math.cos(ang - 2.65)) + " " + n1(y2 + headLen * Math.sin(ang - 2.65))
    };
  }
  // Elbow connector: axis-first orthogonal route with one rounded corner (radius clamped to the legs).
  function elbowPath(x1, y1, x2, y2, opts) {
    opts = opts || {};
    var horizFirst = (opts.axis || "h") === "h";
    var r = Math.min(opts.radius == null ? 24 : opts.radius, Math.abs(x2 - x1) / 2, Math.abs(y2 - y1) / 2);
    var sx = x2 >= x1 ? 1 : -1, sy = y2 >= y1 ? 1 : -1;
    if (horizFirst) {
      return "M" + x1 + " " + y1 + " L" + n1(x2 - sx * r) + " " + y1 + " Q " + x2 + " " + y1 + " " + x2 + " " + n1(y1 + sy * r) + " L" + x2 + " " + y2;
    }
    return "M" + x1 + " " + y1 + " L" + x1 + " " + n1(y2 - sy * r) + " Q " + x1 + " " + y2 + " " + n1(x1 + sx * r) + " " + y2 + " L" + x2 + " " + y2;
  }
  // Group outline: a loose hand-drawn box that overshoots its start corner.
  function outlinePath(x, y, w, h, seed) {
    seed = seed || 1; var k = function (i, a) { return n1(wob(i + seed, a)); };
    return "M" + (x + +k(1, 6)) + " " + (y + +k(2, 6)) + " L" + (x + w + +k(3, 6)) + " " + (y + +k(4, 5)) +
      " L" + (x + w + +k(5, 6)) + " " + (y + h + +k(6, 6)) + " L" + (x + +k(7, 6)) + " " + (y + h + +k(8, 5)) +
      " L" + (x + +k(9, 4)) + " " + (y - 4 + +k(10, 3));
  }

  // Highlight sweep duration: ≈ 360 px/s at 720p (scaled to frameHeight), clamped to [0.5, 1.0] s.
  function sweepDuration(widthPx, frameHeight, format) {
    var s = P.timing(format).sweep, pxPerSec = s.pxPerSecPerH * frameHeight;
    return Math.max(s.min, Math.min(s.max, widthPx / pxPerSec));
  }

  function need(opts) { if (!opts || !opts.format) throw new Error("HFMarks: opts.format is required"); return opts; }

  // Draw stroked path(s) over dur from T (ease.sweep). Length is measured once, at build time.
  function draw(tl, pathEls, T, dur, opts) {
    need(opts);
    var ease = P.ease(opts.format, opts.ease || "ease.sweep");
    [].concat(pathEls).forEach(function (p) {
      var len = p.getTotalLength() * 1.03;
      p.style.strokeDasharray = len; p.style.strokeDashoffset = len; p.style.opacity = 1;
      tl.fromTo(p, { strokeDashoffset: len }, { strokeDashoffset: 0, duration: dur, ease: ease, immediateRender: false }, T);
    });
    return dur;
  }
  // Highlight block: grows left -> right behind its text from a thin seed (opts.frameHeight required).
  function highlight(tl, el, T, opts) {
    need(opts);
    if (!(opts.frameHeight > 0)) throw new Error("HFMarks.highlight: opts.frameHeight is required");
    var w = el.offsetWidth || 1, dur = opts.dur || sweepDuration(w, opts.frameHeight, opts.format);
    // Pre-start state written at build = the from-state, so a forward and a backward seek agree.
    // ease.sweep's slow start (0.47, 0.15) is the thin seed of the first ≈ 4 frames.
    el.style.transformOrigin = "0% 50%"; el.style.transform = "scaleX(0)";
    tl.fromTo(el, { scaleX: 0 }, { scaleX: 1, duration: dur, ease: P.ease(opts.format, "ease.sweep"), immediateRender: false }, T);
    return dur;
  }
  // Global recolour: the whole set flips at once (one 133 ms swap, never a stagger).
  function swap(tl, els, T, toVars, opts) {
    need(opts);
    var v = {}; for (var k in toVars) v[k] = toVars[k];
    v.duration = P.timing(opts.format).swap; v.ease = P.ease(opts.format, "ease.cut");
    tl.to(els, v, T);
    return v.duration;
  }
  // ✕ / ✓ status chips (or any peer set): land together — rise + scale + fade on ease.enter.
  function statusChip(tl, els, T, opts) {
    need(opts);
    if (!(opts.frameHeight > 0)) throw new Error("HFMarks.statusChip: opts.frameHeight is required");
    var c = P.timing(opts.format).chip;
    [].concat(els).forEach(function (e) { e.style.opacity = "0"; });
    tl.fromTo(els, { opacity: 0, scale: 0.6, y: c.riseFrac * opts.frameHeight },
      { opacity: 1, scale: 1, y: 0, duration: c.dur, ease: P.ease(opts.format, "ease.enter"), immediateRender: false }, T);
    return c.dur;
  }
  // Shorts chip grammar: a dot seeds, then the pill grows sideways and the label fades in.
  // parts = {pill, label}; transform/opacity only (house.js animated clip-path, which core law 1 forbids).
  function seedChip(tl, parts, T, opts) {
    need(opts);
    if (!parts || !parts.pill || !parts.label) throw new Error("HFMarks.seedChip: pass {pill, label}");
    var c = P.timing(opts.format).chip;
    if (!c.seed) throw new Error("HFMarks.seedChip: the " + opts.format + " profile has no chip seed timing");
    var e = P.ease(opts.format, "ease.enter"), hgt = parts.pill.offsetHeight || 1, w = parts.pill.offsetWidth || 1;
    parts.pill.style.transformOrigin = (hgt / 2) + "px 50%"; parts.pill.style.opacity = "0"; parts.label.style.opacity = "0";
    tl.fromTo(parts.pill, { opacity: 0 }, { opacity: 1, duration: c.seed, ease: e, immediateRender: false }, T);
    tl.fromTo(parts.pill, { scaleX: Math.min(1, hgt / w) }, { scaleX: 1, duration: c.expand, ease: e, immediateRender: false }, T + c.seed);
    tl.fromTo(parts.label, { opacity: 0 }, { opacity: 1, duration: c.expand, ease: e, immediateRender: false }, T + c.seed);
    return c.seed + c.expand;
  }
  // Script write-on: per-character reveal on exact steps (a seek lands on an exact character count).
  // Long-form ≈ 135 ms/letter, starting ≈ 0.3 s before the spoken word (caller picks T); Shorts 67 ms.
  function scriptWord(tl, el, T, opts) {
    need(opts);
    var ms = opts.msPerChar || P.timing(opts.format).scriptMsPerChar;
    var text = el.textContent; el.textContent = "";
    for (var i = 0; i < text.length; i++) {
      var s = document.createElement("span"); s.textContent = text[i]; s.style.opacity = "0"; s.style.display = "inline";
      s.setAttribute("data-layout-allow-overlap", ""); s.setAttribute("data-layout-allow-occlusion", "");
      el.appendChild(s);
      tl.set(s, { opacity: 1 }, T + (i * ms) / 1000);
    }
    el.style.opacity = "1"; el.setAttribute("data-layout-allow-overlap", ""); el.setAttribute("data-layout-allow-occlusion", "");
    return (text.length * ms) / 1000;
  }

  var api = { wob: wob, ringPath: ringPath, scribblePath: scribblePath, strikePath: strikePath, arrowPath: arrowPath,
    elbowPath: elbowPath, outlinePath: outlinePath, sweepDuration: sweepDuration,
    draw: draw, highlight: highlight, swap: swap, statusChip: statusChip, seedChip: seedChip, scriptWord: scriptWord };
  if (NODE) module.exports = api;
  root.HFMarks = api;
})(typeof window !== "undefined" ? window : this);
