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

// Before its start time a tween has never rendered, so the element shows its BUILD-TIME style; after a
// backward seek GSAP shows the from-state. Both must look the same: every eased fromTo that fades from 0
// must find style.opacity "0" already written. Returns the offending tweens' indexes; [] means safe.
function visibleBeforeStart(tl) {
  var out = [];
  tl.eased().forEach(function (tw, i) {
    if (tw.kind !== "fromTo" || tw.from.opacity !== 0) return;
    [].concat(tw.target).forEach(function (t) { if (String(t.style.opacity) !== "0") out.push(i); });
  });
  return out;
}

// Snapshot of every style/attr value of the given elements — compare across seek orders.
function snapshot(els) {
  return JSON.stringify(els.map(function (e) { return { style: e.style, attrs: e.attrs }; }));
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
    tagName: (tag || "div").toUpperCase(), style: {}, attrs: {}, children: [], parentNode: null,
    offsetWidth: opts.width || 400, offsetHeight: opts.height || 80, offsetLeft: 0, offsetTop: 0,
    _text: opts.text || "", _len: opts.length || 300,
    setAttribute: function (k, v) { el.attrs[k] = String(v); },
    getAttribute: function (k) { return Object.prototype.hasOwnProperty.call(el.attrs, k) ? el.attrs[k] : null; },
    appendChild: function (c) { el.children.push(c); c.parentNode = el; return c; },
    replaceChild: function (n, o) { el.children[el.children.indexOf(o)] = n; n.parentNode = el; return o; },
    cloneNode: function () { var c = fakeEl(tag, opts); c.style = Object.assign({}, el.style); return c; },
    getTotalLength: function () { return el._len; },
    getContext: opts.getContext || function () { return null; }
  };
  Object.defineProperty(el, "textContent", {
    get: function () { return el.children.length ? el.children.map(function (c) { return c.textContent; }).join("") : el._text; },
    set: function (v) { el.children = []; el._text = String(v); }
  });
  el.style.setProperty = function (k, v) { el.style[k] = v; };
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

function fakeDocument() {
  return {
    createElement: function (tag) {
      if (tag === "canvas") return fakeCanvas(0, 0, fakeGl());
      return fakeEl(tag);
    },
    createElementNS: function (ns, tag) { return fakeEl(tag); },
    getElementById: function () { return null; }
  };
}

module.exports = { fakeTimeline: fakeTimeline, conflicts: conflicts, visibleBeforeStart: visibleBeforeStart, snapshot: snapshot, shuffled: shuffled,
  seekOrderInvariant: seekOrderInvariant, fakeEl: fakeEl, fakeGl: fakeGl, fakeCanvas: fakeCanvas, fakeDocument: fakeDocument };
