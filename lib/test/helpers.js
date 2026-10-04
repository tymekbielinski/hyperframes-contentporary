/* Test doubles for lib/ node tests: a recording GSAP timeline, a tiny DOM, a fake WebGL context.
 * Node built-ins only — no test dependencies. */
"use strict";

// Records what a binder schedules. seek(t) drives every `ease: "none"` driver tween the way GSAP
// does on a seek (progress clamped to [0, 1]) and fires its onUpdate.
function fakeTimeline() {
  var tweens = [];
  var tl = {
    tweens: tweens,
    set: function (target, vars, at) { tweens.push({ kind: "set", target: target, vars: vars, at: at }); return tl; },
    to: function (target, vars, at) { tweens.push({ kind: "to", target: target, to: vars, at: at, dur: vars.duration || 0, ease: vars.ease }); return tl; },
    fromTo: function (target, from, to, at) { tweens.push({ kind: "fromTo", target: target, from: from, to: to, at: at, dur: to.duration || 0, ease: to.ease }); return tl; },
    seek: function (t) {
      tweens.forEach(function (tw) {
        if (tw.kind !== "fromTo" || tw.ease !== "none" || !tw.to.onUpdate) return;
        var f = tw.dur > 0 ? Math.max(0, Math.min(1, (t - tw.at) / tw.dur)) : 1;
        Object.keys(tw.from).forEach(function (k) {
          if (typeof tw.from[k] === "number") tw.target[k] = tw.from[k] + (tw.to[k] - tw.from[k]) * f;
        });
        tw.to.onUpdate();
      });
      return tl;
    },
    drivers: function () { return tweens.filter(function (tw) { return tw.kind === "fromTo" && tw.ease === "none"; }); },
    eased: function () { return tweens.filter(function (tw) { return (tw.kind === "fromTo" || tw.kind === "to") && tw.ease !== "none"; }); }
  };
  return tl;
}

// Two non-driver tweens animating the same property of the same target are seek-order dependent
// (the push-flicker bug). Returns a list of "<prop> on <target index>" strings; [] means safe.
function conflicts(tl) {
  var seen = [], out = [];
  tl.eased().forEach(function (tw) {
    [].concat(tw.target).forEach(function (target) {
      Object.keys(tw.to).forEach(function (prop) {
        if (["duration", "ease", "immediateRender", "onUpdate", "stagger"].indexOf(prop) !== -1) return;
        var hit = seen.filter(function (s) { return s.target === target && s.prop === prop; });
        if (hit.length) out.push(prop + " on target #" + seen.indexOf(hit[0]));
        else seen.push({ target: target, prop: prop });
      });
    });
  });
  return out;
}

// The GSAP transform shorthand a CSS transform string amounts to: translate/translateX/translateY (px),
// scale/scaleX/scaleY, rotate (deg), in any order. Anything else — another function, another unit, text
// left over — THROWS: a contract helper that skips what it cannot read would pass what it cannot check.
var UNITS = { translate: "px", translateX: "px", translateY: "px", rotate: "deg", scale: "", scaleX: "", scaleY: "" };
function parseTransform(str) {
  var src = String(str || "").trim(), t = { x: 0, y: 0, scaleX: 1, scaleY: 1, rotation: 0 };
  if (src === "" || src === "none") return t;
  var re = /([A-Za-z][A-Za-z0-9]*)\(([^)]*)\)/g, m, rest = src;
  while ((m = re.exec(src))) {
    var fn = m[1];
    if (!Object.prototype.hasOwnProperty.call(UNITS, fn)) throw new Error("parseTransform: unsupported transform function \"" + fn + "\" in \"" + src + "\"");
    var v = m[2].split(",").map(function (p) {
      p = p.trim();
      var num = /^(-?(?:\d+\.?\d*|\.\d+)(?:e-?\d+)?)([a-z%]*)$/i.exec(p);
      if (!num || (num[2] !== UNITS[fn] && !(num[2] === "" && parseFloat(num[1]) === 0 && UNITS[fn] !== ""))) {
        throw new Error("parseTransform: unsupported unit in " + fn + "(" + m[2] + ") — expected " + (UNITS[fn] || "a unitless number"));
      }
      return parseFloat(num[1]);
    });
    if (fn === "translate") { t.x += v[0]; t.y += v.length > 1 ? v[1] : 0; }
    else if (fn === "translateX") t.x += v[0];
    else if (fn === "translateY") t.y += v[0];
    else if (fn === "scale") { t.scaleX *= v[0]; t.scaleY *= v.length > 1 ? v[1] : v[0]; }
    else if (fn === "scaleX") t.scaleX *= v[0];
    else if (fn === "scaleY") t.scaleY *= v[0];
    else t.rotation += v[0];
    rest = rest.replace(m[0], "");
  }
  if (rest.trim() !== "") throw new Error("parseTransform: unparsed text \"" + rest.trim() + "\" in \"" + src + "\"");
  return t;
}
var TRANSFORM_KEYS = ["x", "y", "scale", "scaleX", "scaleY", "rotation"];
// GSAP transform properties this checker cannot compare: a from-state using one must not pass silently.
var UNSUPPORTED_KEYS = ["xPercent", "yPercent", "skewX", "skewY", "skew", "rotate", "rotationX", "rotationY", "rotationZ", "z", "scaleZ", "transform", "autoAlpha"];
// A from-state number: NaN for anything that is not a finite number ("50%", undefined, NaN).
function num(v, dflt) { return v === undefined || v === null ? dflt : typeof v === "number" ? v : NaN; }
function differs(a, b) { return !(Math.abs(a - b) <= 1e-6); }

// Before its start time a tween has never rendered, so the element shows its BUILD-TIME style; after a
// backward seek GSAP shows the from-state. Both must look the same: for every eased fromTo on an element,
// the build-time opacity (unset = 1), transform (x, y, scale, scaleX, scaleY, rotation) and filter must
// equal the tween's from-values. NaN counts as a mismatch. Returns the offending tweens' indexes; [] means safe.
function styleMismatch(t, f) {
  var bad = false;
  UNSUPPORTED_KEYS.forEach(function (k) {
    if (k in f) throw new Error("visibleBeforeStart: from-state key \"" + k + "\" is a transform property this check cannot compare — use x, y, scale, scaleX, scaleY or rotation");
  });
  if (f.opacity !== undefined) {
    var op = t.style.opacity === undefined || t.style.opacity === "" ? 1 : Number(t.style.opacity);
    if (differs(op, num(f.opacity, 1))) bad = true;
  }
  if (TRANSFORM_KEYS.some(function (k) { return k in f; })) {
    var have = parseTransform(t.style.transform);
    var sx = f.scaleX != null ? f.scaleX : f.scale != null ? f.scale : 1, sy = f.scaleY != null ? f.scaleY : f.scale != null ? f.scale : 1;
    var want = { x: num(f.x, 0), y: num(f.y, 0), scaleX: num(sx, 1), scaleY: num(sy, 1), rotation: num(f.rotation, 0) };
    if (Object.keys(want).some(function (k) { return differs(have[k], want[k]); })) bad = true;
  }
  if (f.filter !== undefined && String(t.style.filter || "") !== String(f.filter)) bad = true;
  return bad;
}

function visibleBeforeStart(tl) {
  var out = [];
  tl.eased().forEach(function (tw, i) {
    if (tw.kind !== "fromTo") return;
    var f = tw.from;
    [].concat(tw.target).forEach(function (t) {
      if (!t || !t.style) return;   // a plain state object, not an element
      var bad = styleMismatch(t, f);
      if (bad && out.indexOf(i) === -1) out.push(i);
    });
  });
  return out;
}

// A tl.set that animates opacity / transform / filter is only safe when the element already shows that
// value at build time (then the set is a no-op instant, identical before the tween and after a backward
// seek). Returns the offending sets' indexes into tl.tweens; [] means safe.
function setsVisible(tl) {
  var out = [], VISIBLE = TRANSFORM_KEYS.concat(["opacity", "filter"]).concat(UNSUPPORTED_KEYS);
  tl.tweens.forEach(function (tw, i) {
    if (tw.kind !== "set") return;
    var f = tw.vars || {};
    if (!VISIBLE.some(function (k) { return k in f; })) return;
    [].concat(tw.target).forEach(function (t) {
      if (!t || !t.style) return;
      if (styleMismatch(t, f) && out.indexOf(i) === -1) out.push(i);
    });
  });
  return out;
}

// conflicts() over EVERY tween — sets and ease:"none" drivers included, not just the eased ones.
function allConflicts(tl) {
  var seen = [], out = [], SKIP = ["duration", "ease", "immediateRender", "onUpdate", "stagger"];
  tl.tweens.forEach(function (tw) {
    var props = tw.kind === "set" ? tw.vars : tw.to;
    [].concat(tw.target).forEach(function (target) {
      Object.keys(props || {}).forEach(function (prop) {
        if (SKIP.indexOf(prop) !== -1) return;
        var hit = seen.filter(function (s) { return s.target === target && s.prop === prop; });
        if (hit.length) out.push(prop + " on target #" + seen.indexOf(hit[0]));
        else seen.push({ target: target, prop: prop });
      });
    });
  });
  return out;
}

// Snapshot of every style/attr value of the given elements — compare across seek orders.
function snapshot(els) {
  return JSON.stringify(els.map(function (e) { return { style: e.style, attrs: e.attrs, cls: e.className, text: e.textContent }; }));
}

// Deterministic shuffle (no Math.random in tests either).
function shuffled(list) {
  var a = list.slice(), seed = 7;
  for (var i = a.length - 1; i > 0; i--) { seed = (seed * 9301 + 49297) % 233280; var j = seed % (i + 1); var tmp = a[i]; a[i] = a[j]; a[j] = tmp; }
  return a;
}

// Assert that state(t) is the same whether the playhead reached t forwards or in shuffled order.
function seekOrderInvariant(tl, times, els) {
  var forward = {};
  times.forEach(function (t) { tl.seek(t); forward[t] = snapshot(els); });
  var bad = [];
  shuffled(times).forEach(function (t) { tl.seek(t); if (snapshot(els) !== forward[t]) bad.push(t); });
  return bad;
}

function fakeEl(tag, opts) {
  opts = opts || {};
  var el = {
    tagName: (tag || "div").toUpperCase(), style: {}, attrs: {}, children: [], parentNode: null, className: "",
    offsetWidth: opts.width || 400, offsetHeight: opts.height || 80, offsetLeft: 0, offsetTop: 0,
    _text: opts.text || "", _len: opts.length || 300,
    setAttribute: function (k, v) { el.attrs[k] = String(v); },
    getAttribute: function (k) { return Object.prototype.hasOwnProperty.call(el.attrs, k) ? el.attrs[k] : null; },
    hasAttribute: function (k) { return Object.prototype.hasOwnProperty.call(el.attrs, k); },
    // Only "[attr]" selectors — what the kit's ground-mode lookup uses.
    closest: function (sel) {
      var m = /^\[([\w-]+)\]$/.exec(sel);
      if (!m) throw new Error("fakeEl.closest: only [attr] selectors, got " + sel);
      for (var e = el; e; e = e.parentNode) if (e.attrs && Object.prototype.hasOwnProperty.call(e.attrs, m[1])) return e;
      return null;
    },
    appendChild: function (c) { el.children.push(c); c.parentNode = el; return c; },
    replaceChild: function (n, o) { el.children[el.children.indexOf(o)] = n; n.parentNode = el; return o; },
    cloneNode: function () { var c = fakeEl(tag, opts); c.style = Object.assign({}, el.style); return c; },
    getTotalLength: function () { return el._len; },
    getContext: opts.getContext || function () { return null; }
  };
  Object.defineProperty(el, "textContent", {
    get: function () { return el.children.length ? el.children.map(function (c) { return c.textContent; }).join("") : el._text; },
    set: function (v) { el.children = []; el._text = String(v); },
    configurable: true   // fakeMixed redefines it over childNodes
  });
  el.style.setProperty = function (k, v) { el.style[k] = v; };
  el.classList = {
    add: function () { [].slice.call(arguments).forEach(function (c) { if (!el.classList.contains(c)) el.className = (el.className + " " + c).trim(); }); },
    contains: function (c) { return (" " + el.className + " ").indexOf(" " + c + " ") !== -1; }
  };
  return el;
}

// A text node and a mixed-content element (childNodes holding text nodes and elements) for the
// splitWords / splitChars markup tests; fakeEl itself has no childNodes (it models a plain-text node).
function fakeText(s) { return { nodeType: 3, nodeValue: s, get textContent() { return this.nodeValue; } }; }
function fakeMixed(tag, nodes) {
  var el = fakeEl(tag);
  el.nodeType = 1; el.childNodes = [];
  function adopt(n) { n.parentNode = el; return n; }
  nodes.forEach(function (n) { el.childNodes.push(adopt(n)); });
  el.appendChild = function (c) { el.childNodes.push(adopt(c)); return c; };
  el.replaceChild = function (n, o) {
    var i = el.childNodes.indexOf(o), add = n.isFragment ? n.children : [n];
    el.childNodes.splice.apply(el.childNodes, [i, 1].concat(add.map(adopt)));
    return o;
  };
  el.hasAttribute = function (k) { return Object.prototype.hasOwnProperty.call(el.attrs, k); };
  Object.defineProperty(el, "textContent", { get: function () { return el.childNodes.map(function (c) { return c.textContent; }).join(""); } });
  return el;
}

function fake2d() {
  var noop = function () {};
  return { fillRect: noop, clearRect: noop, save: noop, restore: noop, translate: noop, scale: noop, drawImage: noop,
    fillText: noop, measureText: function () { return { fontBoundingBoxAscent: 8, fontBoundingBoxDescent: 2 }; } };
}

// A WebGL context that records every uniform/draw call. opts.lost / opts.nullShader simulate failures.
function fakeGl(opts) {
  opts = opts || {};
  var log = [], lost = !!opts.lost;
  var gl = {
    log: log,
    VERTEX_SHADER: 1, FRAGMENT_SHADER: 2, COMPILE_STATUS: 3, ARRAY_BUFFER: 4, STATIC_DRAW: 5, FLOAT: 6,
    TEXTURE_2D: 7, TEXTURE_WRAP_S: 8, TEXTURE_WRAP_T: 9, CLAMP_TO_EDGE: 10, TEXTURE_MIN_FILTER: 11,
    TEXTURE_MAG_FILTER: 12, LINEAR: 13, UNPACK_FLIP_Y_WEBGL: 14, RGBA: 15, UNSIGNED_BYTE: 16,
    COLOR_BUFFER_BIT: 17, BLEND: 18, ONE: 19, ONE_MINUS_SRC_ALPHA: 20, SCISSOR_TEST: 21, TRIANGLE_STRIP: 22,
    createShader: function () { return opts.nullShader ? null : {}; }, shaderSource: function () {}, compileShader: function () {},
    getShaderParameter: function () { return true; }, getShaderInfoLog: function () { return ""; },
    createProgram: function () { return {}; }, attachShader: function () {}, linkProgram: function () {}, useProgram: function () {},
    createBuffer: function () { return {}; }, bindBuffer: function () {}, bufferData: function () {},
    getAttribLocation: function () { return 0; }, enableVertexAttribArray: function () {}, vertexAttribPointer: function () {},
    createTexture: function () { return {}; }, bindTexture: function () {}, texParameteri: function () {}, pixelStorei: function () {},
    texImage2D: function (a, b, c, d, e, src) { log.push(["texImage2D", src.width, src.height]); },
    getUniformLocation: function (p, name) { return name; },
    viewport: function (x, y, w, h) { log.push(["viewport", w, h]); },
    uniform1i: function (n, a) { log.push([n, a]); }, uniform1f: function (n, a) { log.push([n, a]); },
    uniform2f: function (n, a, b) { log.push([n, a, b]); }, uniform4f: function (n, a, b, c, d) { log.push([n, a, b, c, d]); },
    clearColor: function () {}, clear: function () {}, enable: function (c) { log.push(["enable", c]); }, disable: function (c) { log.push(["disable", c]); },
    blendFunc: function () {}, scissor: function (x, y, w, h) { log.push(["scissor", x, y, w, h]); },
    drawArrays: function () { log.push(["draw"]); },
    isContextLost: function () { return lost; },
    getExtension: function () { return { loseContext: function () { lost = true; log.push(["loseContext"]); } }; }
  };
  return gl;
}

function fakeCanvas(w, h, gl) {
  var c = fakeEl("canvas", { getContext: function (kind) { return kind === "2d" ? fake2d() : gl; } });
  c.width = w; c.height = h;
  return c;
}

// A host inside a root carrying data-hf-mode (mode null = no attribute anywhere), as a kit component sees it.
function kitHost(mode) {
  var root = fakeEl("div"), host = fakeEl("div");
  if (mode) root.setAttribute("data-hf-mode", mode);
  root.appendChild(host);
  return host;
}
// Every element under (and including) el.
function descendants(el) {
  var out = [el];
  (el.children || []).forEach(function (c) { out = out.concat(descendants(c)); });
  return out;
}
// The timeline as plain data (eases by token), to compare two builds for determinism.
function serialize(tl) {
  function clean(v) {
    var o = {};
    Object.keys(v || {}).forEach(function (k) {
      if (typeof v[k] === "function") o[k] = v[k].token || (k === "onUpdate" ? "fn" : "fn?");
      else if (k !== "immediateRender") o[k] = v[k];
    });
    return o;
  }
  var seen = [];
  function idx(t) { var i = seen.indexOf(t); if (i === -1) { seen.push(t); i = seen.length - 1; } return i; }
  return JSON.stringify(tl.tweens.map(function (tw) {
    return { kind: tw.kind, target: [].concat(tw.target).map(idx), at: tw.at, dur: tw.dur, from: clean(tw.from), to: clean(tw.to || tw.vars), ease: tw.ease && tw.ease.token || tw.ease };
  }));
}

function fakeDocument() {
  var byId = {}, head = fakeEl("head"), body = fakeEl("body");
  [head, body].forEach(function (parent) {   // getElementById finds what was appended with that id
    var append = parent.appendChild;
    parent.appendChild = function (c) { if (c.attrs && c.attrs.id) byId[c.attrs.id] = c; return append(c); };
  });
  return {
    createElement: function (tag) {
      if (tag === "canvas") return fakeCanvas(0, 0, fakeGl());
      return fakeEl(tag);
    },
    createElementNS: function (ns, tag) { return fakeEl(tag); },
    createTextNode: function (s) { return fakeText(s); },
    createDocumentFragment: function () { var f = fakeEl("#fragment"); f.isFragment = true; return f; },
    getElementById: function (id) { return byId[id] || null; },
    head: head,
    body: body
  };
}

module.exports = { fakeTimeline: fakeTimeline, conflicts: conflicts, visibleBeforeStart: visibleBeforeStart, snapshot: snapshot, shuffled: shuffled,
  seekOrderInvariant: seekOrderInvariant, setsVisible: setsVisible, allConflicts: allConflicts, fakeEl: fakeEl, fakeGl: fakeGl, fakeCanvas: fakeCanvas, fakeDocument: fakeDocument,
  fakeText: fakeText, fakeMixed: fakeMixed, parseTransform: parseTransform, kitHost: kitHost, descendants: descendants, serialize: serialize };
