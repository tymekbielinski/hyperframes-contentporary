/* ============================================================================
 * HFText — word entrance, type-on, glow title (multi-scale bloom), backdrop defocus,
 * accent words, odometer count-up, rasterText (bake parity for DOM text)
 * ----------------------------------------------------------------------------
 * From video 09's lib/house.js (words, typewrite, odometer, rasterText), the Shorts
 * prelude (words/riseIn) and lib/deep-glow.js (folded in here; that file is retired).
 * Brand-free: colours come from the brand's CSS variables; fonts are passed in.
 *
 * Every Gaussian this module creates carries data-blur-reason ("focus" or "glow").
 * Binders add tweens at explicit times with profile eases (opts.format is required);
 * anything driven per frame uses one driver tween over a pure function of time.
 * Load after profile.js and motion-blur.js.
 * ==========================================================================*/
(function (root) {
  "use strict";
  var NODE = typeof module !== "undefined" && module.exports;
  var P = NODE ? require("./profile.js") : root.HFProfile;
  function MB() { return NODE ? require("./motion-blur.js") : root.HFMotionBlur; }

  function need(opts, name) { if (!opts || !opts.format) throw new Error("HFText." + name + ": opts.format is required"); return opts; }
  function needH(opts, name) { if (!(opts.frameHeight > 0)) throw new Error("HFText." + name + ": opts.frameHeight is required"); }
  function layoutOk(el) { el.setAttribute("data-layout-allow-overlap", ""); el.setAttribute("data-layout-allow-occlusion", ""); }

  /* ---------- word entrance: word by word, never per character ----------
   * long-form: rise ≈ 7 % of frame height + fade + blur -> sharp, 0.6 s ease.enter, stagger 230–330 ms
   * Shorts: ≈ 200 ms per word. Returns the time until the last word has landed. */
  function words(tl, el, T, opts) {
    need(opts, "words"); needH(opts, "words");
    var w = P.timing(opts.format).words, stagger = opts.stagger == null ? w.stagger : opts.stagger;
    if (w.staggerRange && (stagger < w.staggerRange[0] || stagger > w.staggerRange[1])) {
      throw new Error("HFText.words: " + opts.format + " stagger must be " + w.staggerRange[0] + "–" + w.staggerRange[1] + " s, got " + stagger);
    }
    var parts = el.textContent.split(/\s+/).filter(Boolean);
    el.textContent = "";
    if (!parts.length) return 0;
    var rise = w.riseFrac * opts.frameHeight, blur = (w.blurFrac * opts.frameHeight).toFixed(2);
    var e = P.ease(opts.format, "ease.enter");
    parts.forEach(function (word, i) {
      var s = document.createElement("span");
      s.textContent = word + (i < parts.length - 1 ? " " : "");
      s.style.display = "inline-block"; s.style.whiteSpace = "pre"; s.style.opacity = "0";
      // Build-time style = the full from-state (opacity + rise + blur), so forward and backward seeks agree before T.
      s.style.transform = "translate(0px, " + rise + "px)"; s.style.filter = "blur(" + blur + "px)";
      s.setAttribute("data-blur-reason", "focus"); layoutOk(s);
      el.appendChild(s);
      tl.fromTo(s, { opacity: 0, y: rise, filter: "blur(" + blur + "px)" },
        { opacity: 1, y: 0, filter: "blur(0px)", duration: w.dur, ease: e, immediateRender: false }, T + i * stagger);
    });
    return (parts.length - 1) * stagger + w.dur;
  }

  /* ---------- type-on: hard per-character steps with a caret (Shorts ≈ 67 ms/char) ----------
   * Long-form has no type-on rate (its text is word by word); a recreated-UI type-on there must pass msPerChar. */
  function typeOn(tl, el, T, opts) {
    need(opts, "typeOn");
    var ms = opts.msPerChar || P.timing(opts.format).typeOnMsPerChar;
    if (!ms) throw new Error("HFText.typeOn: " + opts.format + " has no type-on rate; pass opts.msPerChar");
    var wordPause = (opts.wordPauseMs == null ? 90 : opts.wordPauseMs) / 1000, blinks = opts.blinks == null ? 3 : opts.blinks, blinkS = 0.5;
    var text = el.textContent; el.textContent = "";
    var spans = [], carets = [];
    for (var i = 0; i < text.length; i++) {
      var sp = document.createElement("span"); sp.textContent = text[i];
      sp.style.display = "inline-block"; sp.style.position = "relative"; sp.style.whiteSpace = "pre"; sp.style.visibility = "hidden";
      layoutOk(sp);
      var c = document.createElement("span"); c.setAttribute("aria-hidden", "true"); c.setAttribute("data-layout-ignore", "");
      c.style.cssText = "position:absolute;left:100%;top:6%;width:0.07em;height:0.86em;margin-left:0.04em;background:currentColor;visibility:hidden;";
      sp.appendChild(c); el.appendChild(sp); spans.push(sp); carets.push(c);
    }
    el.style.opacity = "1"; layoutOk(el);
    var t = T;
    spans.forEach(function (sp, i) {
      tl.set(sp, { visibility: "visible" }, t);
      tl.set(carets[i], { visibility: "visible" }, t);
      if (i > 0) tl.set(carets[i - 1], { visibility: "hidden" }, t);
      t += ms / 1000 + (text[i] === " " ? wordPause : 0);
    });
    var last = carets[carets.length - 1];
    for (var b = 0; last && b < blinks; b++) {
      tl.set(last, { visibility: "hidden" }, t + b * blinkS + blinkS / 2);
      if (b < blinks - 1) tl.set(last, { visibility: "visible" }, t + (b + 1) * blinkS);
    }
    return t + (blinks - 0.5) * blinkS - T;
  }

  /* ---------- glow filter (was lib/deep-glow.js): bright-pass -> multi-radius blur -> additive bloom ----------
   * Every feGaussianBlur is tagged data-blur-reason="glow". Animate with setGlowIntensity(id, v). */
  var _n = 0;
  var GLOW_DEFAULTS = { threshold: 0.5, intensity: 1.2, levels: [4, 12, 28, 56, 84], weights: [1, 0.85, 0.6, 0.4, 0.22], tint: "source", region: 130 };
  function glowFilter(id, opts) {
    opts = opts || {};
    function o(k) { return opts[k] == null ? GLOW_DEFAULTS[k] : opts[k]; }
    var threshold = o("threshold"), intensity = o("intensity"), levels = o("levels"), weights = o("weights"), tint = o("tint"), region = o("region");
    var p = [];
    p.push('<feColorMatrix in="SourceGraphic" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0.2126 0.7152 0.0722 0 0" result="dg-luma"/>');
    p.push('<feComponentTransfer in="dg-luma" result="dg-mask"><feFuncA type="linear" slope="10" intercept="' + (-10 * threshold) + '"/></feComponentTransfer>');
    if (tint === "source") p.push('<feComposite in="SourceGraphic" in2="dg-mask" operator="in" result="dg-bright"/>');
    else { p.push('<feFlood flood-color="' + tint + '" result="dg-flood"/>'); p.push('<feComposite in="dg-flood" in2="dg-mask" operator="in" result="dg-bright"/>'); }
    var layers = [];
    for (var i = 0; i < levels.length; i++) {
      var w = weights[i] == null ? 0.3 : weights[i];
      p.push('<feGaussianBlur data-blur-reason="glow" in="dg-bright" stdDeviation="' + levels[i] + '" result="dg-b' + i + '"/>');
      p.push('<feComponentTransfer in="dg-b' + i + '" result="dg-w' + i + '"><feFuncR type="linear" slope="' + w + '"/><feFuncG type="linear" slope="' + w +
        '"/><feFuncB type="linear" slope="' + w + '"/><feFuncA type="linear" slope="' + w + '"/></feComponentTransfer>');
      layers.push("dg-w" + i);
    }
    var prev = layers[0];
    for (var j = 1; j < layers.length; j++) {
      var out = j === layers.length - 1 ? "dg-glowraw" : "dg-sum" + j;
      p.push('<feComposite in="' + prev + '" in2="' + layers[j] + '" operator="arithmetic" k1="0" k2="1" k3="1" k4="0" result="' + out + '"/>');
      prev = out;
    }
    p.push('<feComponentTransfer in="' + (layers.length > 1 ? "dg-glowraw" : layers[0]) + '" result="dg-glow"><feFuncR id="' + id + '-r" type="linear" slope="' + intensity +
      '"/><feFuncG id="' + id + '-g" type="linear" slope="' + intensity + '"/><feFuncB id="' + id + '-b" type="linear" slope="' + intensity +
      '"/><feFuncA type="gamma" amplitude="1" exponent="0.9" offset="0"/></feComponentTransfer>');
    p.push('<feMerge><feMergeNode in="dg-glow"/><feMergeNode in="SourceGraphic"/></feMerge>');
    return '<filter id="' + id + '" x="-' + region + '%" y="-' + region + '%" width="' + (100 + region * 2) + '%" height="' + (100 + region * 2) +
      '%" color-interpolation-filters="sRGB">' + p.join("") + "</filter>";
  }
  // Inject a glow filter once (build time, synchronous). Sub-compositions that cannot load lib/ inline glowFilter() instead.
  function injectGlow(opts) {
    opts = opts || {};
    var id = opts.id || "hf-glow-" + (++_n), host = document.getElementById("hf-glow-host");
    if (!host) {
      host = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      host.setAttribute("id", "hf-glow-host"); host.setAttribute("width", "0"); host.setAttribute("height", "0"); host.setAttribute("aria-hidden", "true");
      host.style.position = "absolute"; (document.body || document.documentElement).appendChild(host);
    }
    var defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
    defs.innerHTML = glowFilter(id, opts); host.appendChild(defs);
    return id;
  }
  function setGlowIntensity(id, v) {
    ["r", "g", "b"].forEach(function (ch) { var f = document.getElementById(id + "-" + ch); if (f) f.setAttribute("slope", v); });
  }

  /* ---------- glow title (long-form only: ease.glow is a long-form token) ----------
   * Each word pops to ≈ 70 % brightness the frame after its time, settles 0.4 s on ease.glow, no scale;
   * next word +430 ms. One driver: opacity/bloom are pure functions of t. */
  function glowOpacity(dt, format) {
    var e = P.ease(format, "ease.glow"), g = P.timing(format).glow;
    if (dt <= 0) return 0;
    return g.pop + (1 - g.pop) * e(Math.min(1, dt / g.settle));
  }
  function glowTitle(tl, wordEls, T, opts) {
    need(opts, "glowTitle"); needH(opts, "glowTitle");
    P.ease(opts.format, "ease.glow");   // throws for formats without a glow title
    var g = P.timing(opts.format).glow, els = [].concat(wordEls), k = opts.frameHeight / 1080;
    var id = opts.glowId || injectGlow({ intensity: 0, levels: GLOW_DEFAULTS.levels.map(function (v) { return +(v * k).toFixed(2); }) });
    els.forEach(function (el) {
      el.style.opacity = "0"; el.style.filter = "url(#" + id + ")"; el.setAttribute("data-blur-reason", "glow");
    });
    var end = T + (els.length - 1) * g.nextWord + g.settle, drv = { t: T };
    function apply() {
      els.forEach(function (el, i) { el.style.opacity = glowOpacity(drv.t - (T + i * g.nextWord), opts.format).toFixed(4); });
      setGlowIntensity(id, (GLOW_DEFAULTS.intensity * glowOpacity(drv.t - T, opts.format)).toFixed(4));
    }
    tl.fromTo(drv, { t: T }, { t: end, duration: end - T, ease: "none", immediateRender: false, onUpdate: apply }, T);
    return end - T;
  }

  /* ---------- backdrop defocus behind a title (long-form): blur σ ≈ 4.5 px @1080 + brightness -> 0.6 over 0.5 s ---------- */
  function defocus(tl, el, T, opts) {
    need(opts, "defocus"); needH(opts, "defocus");
    var d = P.timing(opts.format).defocus;
    if (!d) throw new Error("HFText.defocus: the " + opts.format + " profile has no backdrop defocus");
    el.setAttribute("data-blur-reason", "focus"); el.style.filter = "blur(0px) brightness(1)";
    var s = (d.sigmaFrac * opts.frameHeight).toFixed(2);
    tl.fromTo(el, { filter: "blur(0px) brightness(1)" }, { filter: "blur(" + s + "px) brightness(" + d.brightness + ")", duration: d.dur,
      ease: P.ease(opts.format, "ease.enter"), immediateRender: false }, T);
    return d.dur;
  }

  /* ---------- accent word: switches to the accent colour at T (a seek-safe attribute set) ---------- */
  var CSS = '[data-hf-accent="1"]{color:var(--hf-accent-text)}';
  function installCss() {
    if (document.getElementById("hf-text-css")) return;
    var s = document.createElement("style"); s.setAttribute("id", "hf-text-css"); s.textContent = CSS;
    (document.head || document.documentElement).appendChild(s);
  }
  function accentWord(tl, el, T) { tl.set(el, { attr: { "data-hf-accent": "1" } }, T); }

  /* ---------- odometer: a real count-up from a lower start, digits roll with HFMotionBlur ---------- */
  function isD(c) { return c >= "0" && c <= "9"; }
  // Largest one-significant-figure value below the final (150,000 -> 100,000; 14.4 -> 10.0), or 70 % of it
  // when the final already is one significant figure (10 -> 7, 8 -> 5). Always lower than the final.
  function startValue(f, decimals) {
    if (!(f > 0)) return 0;
    var mag = Math.pow(10, Math.floor(Math.log(f) / Math.LN10)), s = Math.floor(f / mag) * mag;
    if (s >= f - 1e-9) s = f * 0.7;
    var q = Math.pow(10, decimals);
    return Math.max(0, Math.floor(s * q) / q);
  }
  // Parse a label into runs of digits ("," or "." between digits stays inside the run).
  function parseRuns(final, startOverride) {
    var chars = final.split(""), runs = [], runOf = new Array(chars.length), cur = null, i;
    for (i = 0; i < chars.length; i++) {
      var c = chars[i];
      if (isD(c)) { if (!cur) { cur = { digits: [], seps: [], text: "" }; runs.push(cur); } cur.digits.push(i); cur.text += c; runOf[i] = cur; }
      else if (cur && (c === "," || c === ".") && i + 1 < chars.length && isD(chars[i + 1])) { cur.seps.push({ index: i, kind: c }); cur.text += c; runOf[i] = cur; }
      else cur = null;
    }
    runs.forEach(function (r) {
      var dot = r.text.indexOf(".");
      r.final = parseFloat(r.text.replace(/,/g, "")) || 0;
      r.decimals = dot === -1 ? 0 : r.text.length - dot - 1;
      if (startOverride != null && isFinite(startOverride)) {
        var q0 = Math.pow(10, r.decimals), s0 = Math.max(0, Math.round(startOverride * q0) / q0);
        r.start = s0 < r.final ? s0 : startValue(r.final, r.decimals);
      } else r.start = startValue(r.final, r.decimals);
      var intCount = r.digits.length - r.decimals;
      r.places = {};
      r.digits.forEach(function (idx, n) { r.places[idx] = n < intCount ? intCount - 1 - n : -(n - intCount + 1); });
      r.minPlace = Math.min.apply(null, r.digits.map(function (idx) { return r.places[idx]; }));
      r.seps.forEach(function (sp) {
        if (sp.kind !== ",") { sp.threshold = 0; return; }
        var right = 0; r.digits.forEach(function (idx) { if (idx > sp.index && r.places[idx] >= 0) right++; });
        sp.threshold = Math.pow(10, right);
      });
    });
    return { chars: chars, runs: runs, runOf: runOf };
  }
  // Wheel position: the lowest place rolls continuously; higher places rest on their integer and only
  // turn during the carry (last 10 % of the place below). Unwrapped = same curve without the mod.
  function wheelUnwrapped(col, v) {
    var d = v / col.p10;
    if (col.place === col.run.minPlace) return d;
    var whole = Math.floor(d), frac = d - whole;
    return whole + Math.max(0, Math.min(1, (frac - 0.9) * 10));
  }
  function wheelPos(col, v) {
    var d = v / col.p10;
    if (col.place === col.run.minPlace) return d % 10;
    var whole = Math.floor(d), frac = d - whole;
    return (whole % 10 + 10) % 10 + Math.max(0, Math.min(1, (frac - 0.9) * 10));
  }

  // opts: {format, hold, start, font: {family, url}}. font.url (a TTF) enables the exact-glyph bake;
  // without it the strip is painted with canvas fillText in the element's computed font.
  function odometer(tl, el, T, dur, final, opts) {
    need(opts, "odometer");
    var roll = MB().profilePreset(opts.format, "roll"), ease = P.ease(opts.format, "ease.enter");
    var hold = Math.max(0, Math.min(opts.hold == null ? 0 : opts.hold, dur * 0.85)), spinT = T + hold, spinDur = Math.max(0.001, dur - hold);
    var CELLS = 24, RES = 2, EXP = roll.shutter / 30, MAX_CELLS = 0.8, CAP = MAX_CELLS / EXP;
    el.setAttribute("data-hf-text", final); layoutOk(el); el.textContent = ""; el.style.opacity = "0";
    var parsed = parseRuns(final, opts.start), runs = parsed.runs, spansAll = [], cols = [], seps = [];
    parsed.chars.forEach(function (ch, idx) {
      var sp = document.createElement("span");
      sp.style.cssText = "display:inline-block;vertical-align:top;font-variant-numeric:tabular-nums;line-height:1;";
      layoutOk(sp); sp.textContent = ch; el.appendChild(sp); spansAll.push(sp);
      var r = parsed.runOf[idx];
      if (r && isD(ch)) cols.push({ el: sp, run: r, place: r.places[idx], p10: Math.pow(10, r.places[idx]) });
      else if (r) seps.push({ el: sp, run: r, threshold: (r.seps.filter(function (s) { return s.index === idx; })[0] || { threshold: 0 }).threshold });
    });
    if (!cols.length) { tl.set(el, { opacity: 1 }, T); return dur; }   // nothing to count ("N/A")
    var win = document.createElement("div"); win.setAttribute("data-layout-ignore", ""); win.setAttribute("aria-hidden", "true");
    win.style.cssText = "position:absolute;left:0;pointer-events:none;overflow:hidden;visibility:hidden;";
    var cv = document.createElement("canvas"); cv.setAttribute("data-layout-ignore", ""); cv.setAttribute("aria-hidden", "true");
    cv.style.cssText = "position:absolute;left:0;pointer-events:none;";
    win.appendChild(cv); el.appendChild(win);
    var geo = null, world = null, blur = null, glFailed = false;
    function measure() {
      var cs = getComputedStyle(el), em = parseFloat(cs.fontSize);
      geo = { em: em, W: el.offsetWidth, H: CELLS * em, pad: em * 0.34,
        cols: cols.map(function (c) { return { x: c.el.offsetLeft, w: c.el.offsetWidth, ls: parseFloat(getComputedStyle(c.el).letterSpacing) || 0 }; }) };
      var winH = em + 2 * geo.pad, a = geo.pad / winH * 100, b = (geo.pad + em) / winH * 100;
      var fade = "linear-gradient(to bottom, rgba(0,0,0,0) 0%, rgba(0,0,0,0.10) " + (a * 0.62).toFixed(1) + "%, #000 " + a.toFixed(1) + "%, #000 " +
        b.toFixed(1) + "%, rgba(0,0,0,0.10) " + (b + (100 - b) * 0.38).toFixed(1) + "%, rgba(0,0,0,0) 100%)";
      win.style.width = geo.W + "px"; win.style.height = winH + "px"; win.style.top = (-geo.pad) + "px";
      win.style.webkitMaskImage = fade; win.style.maskImage = fade;
      cv.style.width = geo.W + "px"; cv.style.height = geo.H + "px"; cv.style.top = geo.pad + "px";
      world = document.createElement("canvas"); world.width = Math.ceil(geo.W * RES); world.height = Math.ceil(geo.H * RES);
      var x = world.getContext("2d"); x.scale(RES, RES);
      x.font = cs.fontStyle + " " + cs.fontWeight + " " + cs.fontSize + " " + cs.fontFamily;
      x.fillStyle = cs.color; x.textAlign = "center"; x.textBaseline = "alphabetic";
      var m = x.measureText("0"), asc = m.fontBoundingBoxAscent || em * 0.8, desc = m.fontBoundingBoxDescent || em * 0.2, base = asc + (em - (asc + desc)) / 2;
      geo.cols.forEach(function (g) { var cx = g.x + (g.w - g.ls) / 2; for (var k = 0; k < CELLS; k++) x.fillText(String(k % 10), cx, k * em + base); });
      if (opts.font && opts.font.url) exactWorld(cs, em);
    }
    function exactWorld(cs, em) {
      Promise.all([fontB64(opts.font.url), document.fonts.ready]).then(function (res) {
        var colsHtml = geo.cols.map(function (g) {
          var cells = ""; for (var k = 0; k < CELLS; k++) cells += '<div style="height:' + em + "px;line-height:" + em + 'px">' + (k % 10) + "</div>";
          return '<div style="position:absolute;left:' + g.x + "px;top:0;width:" + (g.w - g.ls) + 'px;text-align:center">' + cells + "</div>";
        }).join("");
        var svg = '<svg xmlns="http://www.w3.org/2000/svg" width="' + Math.ceil(geo.W * RES) + '" height="' + Math.ceil(geo.H * RES) + '" viewBox="0 0 ' + geo.W + " " + geo.H + '">' +
          '<style>@font-face{font-family:"HFBake";src:url(data:font/ttf;base64,' + res[0] + ') format("truetype");font-weight:100 900;font-style:normal;}</style>' +
          '<foreignObject x="0" y="0" width="' + geo.W + '" height="' + geo.H + '"><div xmlns="http://www.w3.org/1999/xhtml" style="position:relative;width:' + geo.W + "px;height:" + geo.H +
          "px;margin:0;font-family:HFBake;font-weight:" + cs.fontWeight + ";font-style:" + cs.fontStyle + ";font-size:" + cs.fontSize +
          ";font-variant-numeric:tabular-nums;letter-spacing:0;color:" + cs.color + ';white-space:nowrap">' + colsHtml + "</div></foreignObject></svg>";
        var img = new Image();
        img.onload = function () { world = img; if (blur) { try { blur.updateWorld(img); } catch (e) {} } };
        img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
      }).catch(function () {});
    }
    function ensure() {
      if (blur || glFailed || !MB() || !geo) return;
      if (cv.__hfLost) { var fresh = cv.cloneNode(false); fresh.style.cssText = cv.style.cssText; win.replaceChild(fresh, cv); cv = fresh; cv.__hfLost = false; }
      var CW = Math.ceil(geo.W * RES), CH = Math.ceil(geo.H * RES);
      cv.width = CW; cv.height = CH;
      try { blur = MB().createCameraBlur({ canvas: cv, res: [CW, CH], world: world, preset: roll, bg: null }); }
      catch (e) { glFailed = true; blur = null; if (root.console) console.warn("HFText.odometer: blur unavailable, digits shown locked (" + (e && e.message) + ")"); }
    }
    function release() { if (blur) { try { blur.dispose(); } catch (e) {} blur = null; cv.__hfLost = true; } }
    // Which layer shows is decided per frame by whether the GPU pass actually painted — never by a timeline set.
    function show(painting) {
      win.style.visibility = painting ? "visible" : "hidden";
      cols.forEach(function (c) { c.el.style.visibility = painting ? "hidden" : "inherit"; });
      if (!painting) seps.forEach(function (sp) { sp.el.style.visibility = "inherit"; });
    }
    show(false);
    Promise.resolve(document.fonts ? document.fonts.ready : null).then(function () { measure(); }).catch(function () {});
    function prog(tt) { return ease(Math.max(0, Math.min(1, (tt - spinT) / spinDur))); }
    var hh = 1 / 60, drv = { t: T };
    tl.fromTo(drv, { t: T }, { t: T + dur, duration: dur, ease: "none", immediateRender: false, onUpdate: function () {
      var t = drv.t, painted = false, locked = t >= T + dur - 1e-6;
      if (!geo) measure();
      if (geo && !locked) {
        ensure();
        if (blur) {
          var e = prog(t);
          runs.forEach(function (r) { r.v = r.start + (r.final - r.start) * e; });
          var regions = [];
          cols.forEach(function (c, i) {
            var g = geo.cols[i], rv = c.run.v;
            if (c.place > 0 && wheelUnwrapped(c, rv) < 1e-6) return;   // leading slot still resting on zero
            var d = wheelPos(c, rv); if (!(d >= 0)) d = 0;
            var span = c.run.final - c.run.start;
            var vel = (wheelUnwrapped(c, c.run.start + span * prog(t + hh)) - wheelUnwrapped(c, c.run.start + span * prog(t - hh))) / (2 * hh);
            vel = Math.max(-CAP, Math.min(CAP, vel));
            var pos = 10 + d, em = geo.em;
            regions.push({ x: g.x * RES, y: 0, w: g.w * RES, h: em * RES, T: function (tt) { return { tx: 0, ty: -(pos + vel * (tt - t)) * em * RES, s: 1 }; } });
          });
          try { blur.renderRegions(t, regions); painted = true; } catch (e2) { painted = false; }
          if (painted) seps.forEach(function (sp) { sp.el.style.visibility = sp.run.v >= sp.threshold ? "inherit" : "hidden"; });
        }
      }
      if (locked) release();
      show(painted);
    } }, T);
    tl.set(el, { opacity: 1 }, T);
    return dur;
  }

  /* ---------- rasterText: exact bake parity for DOM text (via the browser's own layout) ----------
   * Rasterises el once through an SVG <foreignObject> carrying its computed CSS. opts.font.url (a TTF)
   * embeds the font (an SVG image cannot load external resources); without it only system fonts render.
   * Returns {img, x, y, pad}; img is null until decoded — build at init, well before any blur leg. */
  var _fontCache = {};
  function fontB64(url) {
    if (!_fontCache[url]) _fontCache[url] = fetch(url).then(function (r) { return r.arrayBuffer(); }).then(function (buf) {
      var bytes = new Uint8Array(buf), bin = "";
      for (var i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
      return btoa(bin);
    });
    return _fontCache[url];
  }
  function rasterText(el, opts) {
    opts = opts || {};
    var pad = opts.pad || 48, h = { img: null, x: opts.x != null ? opts.x : el.offsetLeft, y: opts.y != null ? opts.y : el.offsetTop, pad: pad };
    function esc(t) { return t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
    function spanStyle(n) { var c = getComputedStyle(n); return "display:" + (c.display === "inline" ? "inline" : "inline-block") + ";color:" + c.color + ";font-weight:" + c.fontWeight + ";font-style:" + c.fontStyle + ";font-variant-numeric:" + c.fontVariantNumeric + ";letter-spacing:" + c.letterSpacing + ";white-space:pre;opacity:1"; }
    function walk(node) {
      var out = "";
      for (var i = 0; i < node.childNodes.length; i++) {
        var n = node.childNodes[i];
        if (n.nodeType === 3) out += esc(n.textContent);
        else if (n.nodeType === 1 && n.tagName !== "CANVAS") out += '<span style="' + spanStyle(n) + '">' + walk(n) + "</span>";
      }
      return out;
    }
    function body() {
      var plain = el.getAttribute("data-hf-text");
      if (plain == null) return walk(el);
      return plain.split("").map(function (ch) { return '<span style="display:inline-block;vertical-align:top;font-variant-numeric:tabular-nums;line-height:1;white-space:pre">' + esc(ch) + "</span>"; }).join("");
    }
    var url = opts.font && opts.font.url;
    Promise.all([url ? fontB64(url) : null, document.fonts.ready]).then(function (res) {
      var cs = getComputedStyle(el), fs = parseFloat(cs.fontSize) || 16;
      var W = Math.ceil(Math.max(el.offsetWidth * 1.3, el.textContent.length * fs) + 2 * pad), Hh = Math.ceil(Math.max(el.offsetHeight, fs * 1.4) + 2 * pad);
      var face = res[0] ? '<style>@font-face{font-family:"HFBake";src:url(data:font/ttf;base64,' + res[0] + ') format("truetype");font-weight:100 900;font-style:normal;}</style>' : "";
      var css = "margin:0;padding:" + pad + "px 0 0 " + pad + "px;font-family:" + (res[0] ? "HFBake" : cs.fontFamily) + ";font-weight:" + cs.fontWeight + ";font-style:" + cs.fontStyle + ";font-size:" + cs.fontSize +
        ";letter-spacing:" + cs.letterSpacing + ";line-height:" + cs.lineHeight + ";font-variant-numeric:" + cs.fontVariantNumeric + ";white-space:nowrap;color:" + cs.color + ";text-shadow:" + cs.textShadow + ";text-align:" + cs.textAlign;
      var svg = '<svg xmlns="http://www.w3.org/2000/svg" width="' + W + '" height="' + Hh + '">' + face +
        '<foreignObject x="0" y="0" width="' + W + '" height="' + Hh + '"><div xmlns="http://www.w3.org/1999/xhtml" style="' + css + '">' + body() + "</div></foreignObject></svg>";
      var img = new Image(); img.onload = function () { h.img = img; }; img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
    }).catch(function () {});
    return h;
  }

  var api = { words: words, typeOn: typeOn, glowFilter: glowFilter, injectGlow: injectGlow, setGlowIntensity: setGlowIntensity,
    glowOpacity: glowOpacity, glowTitle: glowTitle, defocus: defocus, CSS: CSS, installCss: installCss, accentWord: accentWord,
    startValue: startValue, parseRuns: parseRuns, wheelPos: wheelPos, wheelUnwrapped: wheelUnwrapped, odometer: odometer,
    rasterText: rasterText, GLOW_DEFAULTS: GLOW_DEFAULTS };
  if (NODE) module.exports = api;
  root.HFText = api;
})(typeof window !== "undefined" ? window : this);
