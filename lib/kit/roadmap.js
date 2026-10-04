/* HFKit.roadmap — variant "wave-nodes" (the chapter roadmap device, reference video ≈ 60/127/234 s).
 * The system name above a glowing wavy path with numbered nodes; at each chapter the edit cuts back
 * to it, the next step card docks onto its node and the camera continues from its last pose.
 * One world, built identically by every visit, so visit k opens exactly where visit k-1 ended:
 *   visit 0 — intro: the title builds word by word, the path draws (1.2 s ease.sweep), each node pops
 *             (0.48 s ease.enter) as the line passes it; camera holds on the whole world.
 *   visit k — opens on visit k-1's end state (title, path, nodes, cards 1…k-1, camera on card k-1),
 *             card k docks (card entrance) and the camera travels to card k (1.6 s ease.camera).
 * Dark ground: path in accent.line with a glow filter (data-blur-reason="glow"), maroon-tinted dark
 * glass cards. Light ground: path in accent.line without bloom, frosted white cards, dark text.
 *
 *   HFKit.roadmap(tl, host, { format: "long-form", at: 0.2, visit: 1, title: "Printing Prediction System",
 *     steps: [{ label: "Predictive Idea Selection", icon: "bulb" }, { label: "Retention Based Editing", icon: "sliders" }, …] })
 *   -> { dur, pose: {cx, cy, z} (the camera's final pose), nodes: [el…], cards: [el…] }
 * Steps 3–6; nodes every 640 px (world 1920 px wide for 3 steps, wider beyond). */
(function (root) {
  "use strict";
  var NODE = typeof module !== "undefined" && module.exports;
  var K = NODE ? require("./kit.js") : root.HFKit;
  var P = NODE ? require("../profile.js") : root.HFProfile;
  var X = NODE ? require("../text.js") : root.HFText;
  var M = NODE ? require("../marks.js") : root.HFMarks;
  var C = NODE ? require("../camera.js") : root.HFCamera;

  var SPACING = 640, X0 = 320, Y_LOW = 700, Y_HIGH = 520, Y_MID = 610, CARD_W = 250, CARD_H = 290, NODE_D = 46;
  var TITLE_W = 1300, DRAW_DUR = 1.2, DRAW_LEAD = 0.3, LEG = 1.6, ZOOM = 1.8, EXT = 400, MIN_STEPS = 3, MAX_STEPS = 6;
  // 24 × 24 stroke icons (currentColor). Unknown names throw; pass none for a number-only card.
  var ICONS = {
    bulb: "M9 18h6M10 21h4M12 3a6 6 0 0 0-4 10.5c.8.8 1 1.5 1 2.5h6c0-1 .2-1.7 1-2.5A6 6 0 0 0 12 3z",
    sliders: "M4 6h9M17 6h3M4 12h3M11 12h9M4 18h11M19 18h1M15 4v4M9 10v4M17 16v4",
    chart: "M4 20V11M10 20V5M16 20v-6M2 20h20",
    target: "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18zM12 8a4 4 0 1 0 0 8a4 4 0 1 0 0-8z"
  };

  // World geometry: pure function of the step count.
  function geometry(n) {
    var nodes = [];
    for (var i = 0; i < n; i++) nodes.push({ x: X0 + i * SPACING, y: i % 2 === 0 ? Y_LOW : Y_HIGH });
    var width = Math.max(K.FRAME.width, 2 * X0 + (n - 1) * SPACING);
    var pts = [{ x: -EXT, y: Y_MID }].concat(nodes, [{ x: width + EXT, y: Y_MID }]);   // EXT: both ends stay off-frame at the visit zoom
    var d = "M" + pts[0].x + " " + pts[0].y;
    for (var j = 0; j < pts.length - 1; j++) {   // Catmull-Rom through every point -> cubic Béziers
      var p0 = pts[Math.max(0, j - 1)], p1 = pts[j], p2 = pts[j + 1], p3 = pts[Math.min(pts.length - 1, j + 2)];
      d += " C" + (p1.x + (p2.x - p0.x) / 6).toFixed(1) + " " + (p1.y + (p2.y - p0.y) / 6).toFixed(1) + " " +
        (p2.x - (p3.x - p1.x) / 6).toFixed(1) + " " + (p2.y - (p3.y - p1.y) / 6).toFixed(1) + " " + p2.x + " " + p2.y;
    }
    return { nodes: nodes, width: width, height: K.FRAME.height, d: d, ext: EXT };
  }
  // Camera pose for visit k: 0 = the whole world; k ≥ 1 = card k, framed at 1.8× (the reference card reads ≈ 450 px wide).
  function pose(geo, k) {
    if (k === 0) return { cx: geo.width / 2, cy: geo.height / 2, z: K.FRAME.width / geo.width };
    var nd = geo.nodes[k - 1];
    return { cx: nd.x, cy: nd.y + 40, z: ZOOM };
  }
  // When the drawing path reaches world x (fraction f of its width): invert ease.sweep by bisection.
  function reach(f, format)   /* f = fraction of the path's x extent */ {
    var e = P.ease(format, "ease.sweep"), lo = 0, hi = 1;
    for (var i = 0; i < 24; i++) { var m = (lo + hi) / 2; if (e(m) < f) lo = m; else hi = m; }
    return (lo + hi) / 2 * DRAW_DUR;
  }

  function waveNodes(tl, host, opts) {
    var b = K.begin("roadmap", host, opts), T = b.at, fmt = b.lf.format;
    var steps = Array.isArray(opts.steps) ? opts.steps : [], n = steps.length, visit = opts.visit == null ? 0 : opts.visit;
    if (n < MIN_STEPS || n > MAX_STEPS) throw new Error("HFKit.roadmap: " + MIN_STEPS + "–" + MAX_STEPS + " steps, got " + n);
    if (!(visit === Math.floor(visit) && visit >= 0 && visit <= n)) throw new Error("HFKit.roadmap: visit must be 0 (intro) … " + n + ", got " + visit);
    if (typeof opts.title !== "string" || !opts.title.trim()) throw new Error("HFKit.roadmap: opts.title is required");
    steps.forEach(function (s, i) {
      if (!s || typeof s.label !== "string" || !s.label.trim()) throw new Error("HFKit.roadmap: step " + (i + 1) + " has no label");
      if (s.icon != null && !Object.prototype.hasOwnProperty.call(ICONS, s.icon)) throw new Error("HFKit.roadmap: step " + (i + 1) + " icon " + JSON.stringify(s.icon) + " (have: " + Object.keys(ICONS).join(", ") + ")");
    });
    var geo = geometry(n);
    K.ground(host, {});
    var stage = K.el("div", "hf-kit-rm-stage", host);
    stage.style.width = geo.width + "px"; stage.style.height = geo.height + "px";
    stage.setAttribute("data-layout-allow-overflow", "");   // the camera moves the world past the frame on purpose
    var title = K.el("div", "hf-kit-headline hf-kit-rm-title", stage, opts.title.trim().replace(/\s+/g, " "));
    title.style.left = (geo.width - TITLE_W) / 2 + "px";
    var art = K.svg("svg", { "class": "hf-kit-rm-path", width: String(geo.width), height: String(geo.height), viewBox: "0 0 " + geo.width + " " + geo.height }, stage);
    var path = K.svg("path", { d: geo.d }, art);
    if (b.mode === "dark") {
      var gid = X.injectGlow({ intensity: 1.1, levels: [3, 8, 18] });
      path.setAttribute("data-blur-reason", "glow");
      path.style.filter = "url(#" + gid + ")";
    }
    var cards = steps.map(function (s, i) {
      var nd = geo.nodes[i], card = K.el("div", "hf-kit-glass hf-kit-rm-card", stage);
      card.style.left = (nd.x - CARD_W / 2) + "px"; card.style.top = (nd.y - CARD_H * 0.4) + "px";
      if (s.icon) {
        var ic = K.svg("svg", { "class": "hf-kit-rm-icon", viewBox: "0 0 24 24" }, card);
        K.svg("path", { d: ICONS[s.icon] }, ic);
      }
      K.el("div", "hf-kit-body hf-kit-rm-label", card, s.label.trim());
      return card;
    });
    var nodes = geo.nodes.map(function (nd, i) {
      var e = K.el("div", "hf-kit-rm-node", stage, String(i + 1));
      e.style.left = (nd.x - NODE_D / 2) + "px"; e.style.top = (nd.y - NODE_D / 2) + "px";
      return e;
    });
    var dur, keys;
    if (visit === 0) {
      cards.forEach(function (c) { c.style.visibility = "hidden"; });
      var wd = X.words(tl, title, T, b.lf), dT = T + DRAW_LEAD;
      M.draw(tl, path, dT, DRAW_DUR, b.lf);
      var last = 0;
      nodes.forEach(function (e, i) {
        var at = dT + reach((geo.nodes[i].x + EXT) / (geo.width + 2 * EXT), fmt);
        last = Math.max(last, at - T + K.pop(tl, e, at));
      });
      dur = Math.max(wd, DRAW_LEAD + DRAW_DUR, last);
      keys = [{ t: 0, cx: pose(geo, 0).cx, cy: pose(geo, 0).cy, z: pose(geo, 0).z }];
    } else {
      cards.forEach(function (c, i) { if (i >= visit) c.style.visibility = "hidden"; });
      X.splitWords(title).forEach(function (sp) {   // same word-span structure as the intro's settled title (centred lines match at the cut)
        sp.style.display = "inline-block"; sp.style.whiteSpace = "pre";
        sp.setAttribute("data-layout-allow-overlap", ""); sp.setAttribute("data-layout-allow-occlusion", "");
      });
      var cd = K.cardIn(tl, cards[visit - 1], T), a = pose(geo, visit - 1), z = pose(geo, visit);
      dur = Math.max(cd, LEG);
      keys = [{ t: 0, cx: a.cx, cy: a.cy, z: a.z }, { t: LEG, cx: z.cx, cy: z.cy, z: z.z }];
    }
    C.rig(tl, { format: fmt, width: K.FRAME.width, height: K.FRAME.height, stage: stage, at: T, keys: keys, dur: dur });
    return { dur: dur, pose: pose(geo, visit), nodes: nodes, cards: cards };
  }

  K.register("roadmap", "wave-nodes", waveNodes, [
    ".hf-kit-rm-stage{position:absolute;left:0;top:0}",
    ".hf-kit-rm-title{position:absolute;width:" + TITLE_W + "px;top:150px;text-align:center;font-size:92px;line-height:1.15;letter-spacing:0.04em;text-transform:uppercase;white-space:normal}",
    ".hf-kit-rm-path{position:absolute;left:0;top:0;overflow:visible}",
    ".hf-kit-rm-path path{fill:none;stroke:var(--hf-accent-line);stroke-width:5;stroke-linecap:round}",
    ".hf-kit-rm-card{width:" + CARD_W + "px;height:" + CARD_H + "px;overflow:hidden;text-align:center}",
    ".hf-kit-dark .hf-kit-rm-card{border-top-color:var(--hf-accent-line)}",
    ".hf-kit-dark .hf-kit-rm-card::before{content:\"\";position:absolute;inset:0;background:linear-gradient(180deg,var(--hf-accent-block) 0%,transparent 75%);opacity:.22}",
    ".hf-kit-rm-icon{position:absolute;left:" + (CARD_W / 2 - 26) + "px;top:30px;width:52px;height:52px;fill:none;stroke:var(--hf-text-primary);stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round}",
    ".hf-kit-rm-label{position:absolute;left:16px;right:16px;top:" + (CARD_H * 0.4 + NODE_D / 2 + 22) + "px;font-size:28px;line-height:1.25}",
    ".hf-kit-rm-node{position:absolute;width:" + NODE_D + "px;height:" + NODE_D + "px;border-radius:50%;background:var(--hf-text-primary);color:var(--hf-ground-deep);" +
      "font-family:var(--hf-font-headline);font-weight:var(--hf-font-headline-weight);font-size:26px;line-height:" + NODE_D + "px;text-align:center}"
  ].join("\n"));
  K.roadmapGeometry = geometry;
  K.roadmapPose = pose;
})(typeof window !== "undefined" ? window : this);
