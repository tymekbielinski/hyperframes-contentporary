/* ============================================================================
 * HFKit — the templated long-form kit: registry, ground, glass, entrances
 * ----------------------------------------------------------------------------
 * Spec §8 (lib/kit) · standards/formats/long-form.md (catalogue, motion values) ·
 * brands/<brand>/brand.md (kit variants, light-ground rules).
 *
 * A kit component is a binder: HFKit.<name>(tl, host, opts) builds its DOM inside `host`
 * (a 1920×1080 box; the kit never transforms the host itself), adds tweens at explicit
 * times to the paused timeline `tl`, and returns { dur, ... } — dur = seconds from opts.at
 * until the layout has settled. It is built ONLY on the lib primitives: HFProfile eases and
 * timings, HFCamera, HFMarks, HFText, and the HFBrand CSS variables. No colour is written
 * here: every colour is a var(--hf-…) from lib/brand.js.
 *
 * Ground mode: every component reads data-hf-mode from host.closest("[data-hf-mode]") and
 * THROWS if it is missing (new_video writes it on index.html's root; an overlay document
 * sets it on its own root). Light ground drops every glow (brand.md): dark text.primary,
 * a scribble underline or an accent.block marker, frosted white glass.
 *
 * Build after `await document.fonts.ready; await HFText.loadFaces(root)` (components measure text, hidden
 * scenes included), then
 * `await HFText.ready()` before registering the timeline.
 * Load after profile.js, motion-blur.js, camera.js, marks.js, text.js; components after this file.
 * ==========================================================================*/
(function (root) {
  "use strict";
  var NODE = typeof module !== "undefined" && module.exports;
  var P = NODE ? require("../profile.js") : root.HFProfile;
  function X() { return NODE ? require("../text.js") : root.HFText; }

  var FORMAT = "long-form";
  var FRAME = { width: 1920, height: 1080 };   // long-form frame (standards/formats/long-form.md)
  var GRID_PX = 150;                            // ground grid cell at 1080p, measured on the template stills
  var GLOW = 0.6;                               // settled glow-title bloom for kit titles (lib default 1.2 reads as a smear on 1080p stills)
  var VARIANTS = {};                            // component -> { variant: binder }
  var CSS = [];

  function register(name, variant, binder, css) {
    if (!VARIANTS[name] && api[camel(name)] !== undefined) throw new Error("HFKit: " + name + " collides with the existing HFKit." + camel(name));
    VARIANTS[name] = VARIANTS[name] || {};
    if (VARIANTS[name][variant]) throw new Error("HFKit: " + name + "/" + variant + " registered twice");
    VARIANTS[name][variant] = binder;
    if (css) CSS.push(css);
    if (!api[camel(name)]) {
      api[camel(name)] = function (tl, host, opts) {
        opts = opts || {};
        var have = Object.keys(VARIANTS[name]), v = opts.variant || have[0];
        if (!VARIANTS[name][v]) throw new Error("HFKit." + camel(name) + ": unknown variant " + JSON.stringify(v) + " (have: " + have.join(", ") + ")");
        return VARIANTS[name][v](tl, host, opts);
      };
    }
  }
  function camel(name) { return name.replace(/-([a-z])/g, function (_, c) { return c.toUpperCase(); }); }
  function variants(name) { return VARIANTS[name] ? Object.keys(VARIANTS[name]) : []; }

  // The ground mode for `host`: its own or its nearest ancestor's data-hf-mode. Never defaulted.
  function mode(host, who) {
    var m = host && typeof host.closest === "function" ? host.closest("[data-hf-mode]") : null;
    if (!m) throw new Error(who + ": no data-hf-mode on the host or any ancestor — set it on the composition root " +
      "(new_video writes it on index.html; an overlay document sets it on its own root)");
    var v = m.getAttribute("data-hf-mode");
    if (v !== "dark" && v !== "light") throw new Error(who + ": data-hf-mode must be \"dark\" or \"light\", got " + JSON.stringify(v));
    return v;
  }

  // Common entry checks: long-form only, a host element, a start time. Returns { mode, at, lf }.
  function begin(name, host, opts) {
    opts = opts || {};
    var who = "HFKit." + camel(name);
    if (opts.format !== FORMAT) throw new Error(who + ": kit components are long-form only (opts.format must be \"long-form\", got " + JSON.stringify(opts.format) + ")");
    if (!host || typeof host.appendChild !== "function") throw new Error(who + ": host must be an element");
    var at = opts.at == null ? 0 : opts.at;
    if (!(typeof at === "number" && isFinite(at) && at >= 0)) throw new Error(who + ": opts.at must be a time in seconds ≥ 0");
    installCss();
    var m = mode(host, who);
    // The resolved mode as a class: CSS keys off it, not [data-hf-mode], because a descendant selector would
    // also match a farther ancestor (a light proof-sheet scene inside a dark index root). Kit hosts must not
    // nest: a host inside another kit host of the opposite mode would match both mode classes' rules.
    host.classList.add("hf-kit-host", "hf-kit-" + m);
    return { mode: m, at: at, who: who, lf: { format: FORMAT, frameHeight: FRAME.height } };
  }

  function el(tag, cls, parent, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    if (parent) parent.appendChild(e);
    return e;
  }
  function svg(tag, attrs, parent) {
    var e = document.createElementNS("http://www.w3.org/2000/svg", tag);
    Object.keys(attrs || {}).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    if (parent) parent.appendChild(e);
    return e;
  }

  function installCss() {
    if (typeof document === "undefined" || document.getElementById("hf-kit-css")) return;
    var s = document.createElement("style"); s.setAttribute("id", "hf-kit-css"); s.textContent = BASE_CSS + CSS.join("\n");
    (document.head || document.documentElement || document.body).appendChild(s);
  }

  /* Full-frame ground (brand.md "constant visual language"): lit centre, grid + dot matrix and a soft
   * light sweep on the dark ground; a silver/white radial with a faint grid on the light ground. The
   * accent ambience (opts.ambient) is the warm top glow of the glow-center title still. Returns the
   * layers so a component can defocus the grid behind a title. */
  function ground(host, opts) {
    opts = opts || {};
    var g = el("div", "hf-kit-ground" + (opts.quiet ? " hf-kit-ground-quiet" : ""), host);
    var layers = { root: g, base: el("div", "hf-kit-ground-base", g) };
    if (opts.ambient) layers.ambient = el("div", "hf-kit-ground-ambient", g);
    layers.grid = el("div", "hf-kit-ground-grid", g);
    if (opts.dots !== false) layers.dots = el("div", "hf-kit-ground-dots", layers.grid);
    layers.sweep = el("div", "hf-kit-ground-sweep", g);
    layers.vignette = el("div", "hf-kit-ground-vignette", g);
    return layers;
  }

  /* Card entrance (long-form.md "card entrance"): rise 35–40 px at 720p, 0.43 s ease.card, brightens and
   * sharpens (a focus blur + brightness, tagged data-blur-reason="focus"). Build-time style = from-state. */
  function cardIn(tl, e, T) {
    var t = P.timing(FORMAT), c = t.card, rise = +(c.riseFrac * FRAME.height).toFixed(2);
    var px = +(t.words.blurFrac * FRAME.height).toFixed(2);
    var from = { opacity: 0, y: rise, filter: X().blurPx(e, "focus", px) + " brightness(0.6)" };
    var to = { opacity: 1, y: 0, filter: X().blurPx(e, "focus", 0) + " brightness(1)" };
    P.claimTransform(e, "HFKit.cardIn");
    e.style.opacity = "0"; e.style.transform = "translate(0px, " + rise + "px)"; e.style.filter = from.filter;
    to.duration = c.dur; to.ease = P.ease(FORMAT, "ease.card"); to.immediateRender = false;
    tl.fromTo(e, from, to, T);
    return c.dur;
  }
  /* Slide-in for an over-footage panel: fade + travel from `dx` px, words.dur (0.6 s) on ease.enter. */
  function slideIn(tl, e, T, dx) {
    var d = P.timing(FORMAT).words.dur;
    P.claimTransform(e, "HFKit.slideIn");
    e.style.opacity = "0"; e.style.transform = "translate(" + dx + "px, 0px)";
    tl.fromTo(e, { opacity: 0, x: dx }, { opacity: 1, x: 0, duration: d, ease: P.ease(FORMAT, "ease.enter"), immediateRender: false }, T);
    return d;
  }
  /* Exit of an over-footage layout: opacity to 0 over card.dur on ease.enter. Only opacity, so it never
   * fights an entrance transform. */
  function fadeOut(tl, e, T) {
    var d = P.timing(FORMAT).card.dur;
    tl.fromTo(e, { opacity: 1 }, { opacity: 0, duration: d, ease: P.ease(FORMAT, "ease.enter"), immediateRender: false }, T);
    return d;
  }
  // Pop for small round markers (roadmap nodes): scale 0 -> 1 + fade, timing.node.dur on ease.enter.
  function pop(tl, e, T) {
    var d = P.timing(FORMAT).node.dur;
    P.claimTransform(e, "HFKit.pop");
    e.style.opacity = "0"; e.style.transform = "scale(0)";
    tl.fromTo(e, { opacity: 0, scale: 0 }, { opacity: 1, scale: 1, duration: d, ease: P.ease(FORMAT, "ease.enter"), immediateRender: false }, T);
    return d;
  }

  // Shared look. Colours are brand variables only; glow lives under .hf-kit-dark (the host's resolved mode) only.
  var BASE_CSS = [
    ".hf-kit-host{position:absolute;left:0;top:0;width:1920px;height:1080px;overflow:hidden}",
    ".hf-kit-ground,.hf-kit-ground>div{position:absolute;inset:0}",
    ".hf-kit-ground-base{background:radial-gradient(ellipse 75% 70% at 50% 40%,var(--hf-ground-centre) 0%,var(--hf-ground-deep) 100%)}",
    ".hf-kit-ground-ambient{background:radial-gradient(ellipse 60% 75% at 50% 12%,var(--hf-extras-ambient-glow,var(--hf-ground-centre)) 0%,transparent 72%)}",
    ".hf-kit-ground-grid{mix-blend-mode:screen;background-image:linear-gradient(to right,var(--hf-ground-grid) 2px,transparent 2px),linear-gradient(to bottom,var(--hf-ground-grid) 2px,transparent 2px);" +
      "background-size:" + GRID_PX + "px " + GRID_PX + "px;background-position:60px 0;" +
      "-webkit-mask-image:radial-gradient(ellipse 80% 75% at 50% 35%,black 0%,transparent 100%);mask-image:radial-gradient(ellipse 80% 75% at 50% 35%,black 0%,transparent 100%)}",
    ".hf-kit-ground-dots{position:absolute;inset:0;background-image:radial-gradient(circle,var(--hf-ground-dots) 1.6px,transparent 2.2px);background-size:15px " + GRID_PX / 2 + "px;background-position:68px 37px;opacity:.9}",
    ".hf-kit-ground-sweep{background:linear-gradient(112deg,transparent 45%,var(--hf-surface-halo) 62%,transparent 78%)}",
    ".hf-kit-ground-vignette{background:radial-gradient(ellipse 85% 85% at 50% 45%,transparent 55%,var(--hf-ground-deep) 100%)}",
    ".hf-kit-light .hf-kit-ground-dots{display:none}",
    ".hf-kit-light .hf-kit-ground-grid{mix-blend-mode:multiply;opacity:.8}",
    ".hf-kit-ground-quiet .hf-kit-ground-grid{opacity:.35}",
    // dark glass: dark fill, light sheen top-left, bevelled light rim, faint light halo (never a dark drop shadow)
    ".hf-kit-glass{position:absolute;box-sizing:border-box;border-radius:var(--hf-card-radius)}",
    ".hf-kit-dark .hf-kit-glass{background:linear-gradient(165deg,var(--hf-surface-fill-alt) 0%,var(--hf-surface-fill) 38%,var(--hf-surface-fill) 100%);" +
      "border:2px solid var(--hf-surface-fill-alt);box-shadow:inset 0 2px 0 var(--hf-surface-bevel),inset 0 -2px 6px var(--hf-ground-deep),0 0 0 2px var(--hf-ground-deep),0 0 70px var(--hf-surface-halo)}",
    ".hf-kit-dark .hf-kit-glass::after{content:\"\";position:absolute;inset:-2px;border-radius:inherit;border:2px solid var(--hf-surface-bevel);opacity:.35;pointer-events:none}",
    // light glass: frosted white, hairline border, soft neutral shadow from surface.halo
    ".hf-kit-light .hf-kit-glass{background:var(--hf-surface-fill);border:1px solid var(--hf-surface-bevel);box-shadow:0 18px 48px var(--hf-surface-halo),0 2px 6px var(--hf-surface-halo)}",
    ".hf-kit-headline{font-family:var(--hf-font-headline);font-weight:var(--hf-font-headline-weight);color:var(--hf-text-primary);white-space:nowrap}",
    ".hf-kit-body{font-family:var(--hf-font-body);font-weight:var(--hf-font-body-weight);color:var(--hf-text-primary)}",
    ".hf-kit-script{font-family:var(--hf-font-script);color:var(--hf-accent-script);white-space:nowrap}",
    ".hf-kit-underline{position:absolute;left:-2%;width:104%;top:88%;height:0.32em;overflow:visible;pointer-events:none}",
    ".hf-kit-underline path{fill:none;stroke:var(--hf-accent-line);stroke-width:5;stroke-linecap:round}",
    ".hf-kit-marker{position:absolute;left:-0.12em;right:-0.12em;top:12%;bottom:4%;background:var(--hf-accent-block);z-index:-1}",
    ".hf-kit-word{position:relative;display:inline-block;white-space:pre}"
  ].join("\n");

  var api = { FORMAT: FORMAT, FRAME: FRAME, GRID_PX: GRID_PX, GLOW: GLOW, register: register, variants: variants, mode: mode, begin: begin,
    el: el, svg: svg, installCss: installCss, ground: ground, cardIn: cardIn, slideIn: slideIn, fadeOut: fadeOut, pop: pop,
    css: function () { return BASE_CSS + CSS.join("\n"); } };
  if (NODE) module.exports = api;
  root.HFKit = api;
})(typeof window !== "undefined" ? window : this);
