"use strict";
// The shared contract proven against throwaway components: one well-behaved, one per violated rule.
var test = require("node:test");
var assert = require("node:assert/strict");
var h = require("./helpers.js");
var P = require("../profile.js");
var c = require("./kit-contract.js");
var K = require("../kit/kit.js");

var counter = 0;
// A component that settles correctly; `flaw(tl, host, b, card, d)` adds one violation (and may return dur).
function fixture(name, flaw) {
  K.register(name, "plain", function (tl, host, o) {
    var b = K.begin(name, host, o), card = K.el("div", "hf-kit-glass", host);
    var d = K.cardIn(tl, card, b.at);
    var state = { p: 0 };   // a linear driver, to give the seek-order check something to seek
    tl.fromTo(state, { p: 0 }, { p: 1, duration: d, ease: "none", onUpdate: function () { card.setAttribute("data-p", state.p.toFixed(3)); } }, b.at);
    var extra = flaw ? flaw(tl, host, b, card, d) : undefined;
    return { dur: extra && extra.dur !== undefined ? extra.dur : d };
  });
  var call = name.replace(/-([a-z])/g, function (_, ch) { return ch.toUpperCase(); });
  return function (tl, host, extra) { return K[call](tl, host, Object.assign({ format: "long-form" }, extra)); };
}
function tags(build) { return c.violations(build).map(function (v) { return /^\[(\w+(?:-\w+)?)\]/.exec(v)[1]; }); }
function enter() { return P.ease("long-form", "ease.enter"); }

test("a well-behaved component passes every rule", function () {
  assert.deepEqual(c.violations(fixture("zz-good")), []);
});
test("a set that already matches the build-time style is a harmless instant", function () {
  var build = fixture("zz-set-ok", function (tl, host, b, card) { card.style.opacity = "0"; tl.set(card, { opacity: 0 }, b.at + 0.2); });
  assert.deepEqual(c.violations(build).filter(function (v) { return /\[set\]/.test(v); }), []);
});

test("a linear or raw-string ease is caught", function () {
  assert.ok(tags(fixture("zz-linear", function (tl, host, b, card) { var e = K.el("div", "", host); e.style.opacity = "0"; tl.fromTo(e, { opacity: 0 }, { opacity: 1, duration: 0.3, ease: "linear" }, b.at); })).indexOf("ease") !== -1);
  assert.ok(tags(fixture("zz-string-ease", function (tl, host, b) { var e = K.el("div", "", host); e.style.opacity = "0"; tl.fromTo(e, { opacity: 0 }, { opacity: 1, duration: 0.3, ease: "power2.out" }, b.at); })).indexOf("ease") !== -1);
});
test("an unprofiled tl.to (no ease at all) is caught", function () {
  assert.ok(tags(fixture("zz-bare-to", function (tl, host, b) { tl.to(K.el("div", "", host), { opacity: 0.5, duration: 0.3 }, b.at); })).indexOf("ease") !== -1);
});
test("a tl.set that changes a visible prop the build-time style does not show is caught", function () {
  assert.ok(tags(fixture("zz-set-bad", function (tl, host, b, card) { tl.set(card, { opacity: 0.5 }, b.at + 0.1); })).indexOf("set") !== -1);
  assert.ok(tags(fixture("zz-set-xform", function (tl, host, b) { var e = K.el("div", "", host); tl.set(e, { y: 30 }, b.at + 0.1); })).indexOf("set") !== -1);
});
test("a set and a tween on one property conflict, sets included", function () {
  var build = fixture("zz-set-conflict", function (tl, host, b, card) { tl.set(card, { opacity: 1 }, b.at + 0.5); });
  assert.ok(tags(build).indexOf("conflict") !== -1);
});
test("an ease:none tween without onUpdate is caught", function () {
  assert.ok(tags(fixture("zz-no-update", function (tl, host, b, card, d) { tl.fromTo({ p: 0 }, { p: 0 }, { p: 1, duration: d, ease: "none" }, b.at); })).indexOf("driver") !== -1);
  assert.ok(tags(fixture("zz-to-none", function (tl, host, b, card, d) { tl.to({ p: 0 }, { p: 1, duration: d, ease: "none" }, b.at); })).indexOf("driver") !== -1);
});
test("a blur without data-blur-reason is caught, tagged or tweened", function () {
  assert.ok(tags(fixture("zz-blur-el", function (tl, host) { K.el("div", "", host).style.filter = "blur(4px)"; })).indexOf("blur") !== -1);
  assert.ok(tags(fixture("zz-blur-tween", function (tl, host, b) {
    var e = K.el("div", "", host); e.style.filter = "blur(8px)";
    tl.fromTo(e, { filter: "blur(8px)" }, { filter: "blur(0px)", duration: 0.3, ease: enter(), immediateRender: false }, b.at);
  })).indexOf("blur") !== -1);
});
test("a returned dur that is not when the timeline settles is caught", function () {
  assert.ok(tags(fixture("zz-dur", function (tl, host, b, card, d) { return { dur: d + 1 }; })).indexOf("dur") !== -1);
});
test("a tween that ignores opts.at is caught", function () {
  assert.ok(tags(fixture("zz-offset", function (tl, host) { var e = K.el("div", "", host); e.style.opacity = "0"; tl.fromTo(e, { opacity: 0 }, { opacity: 1, duration: 0.3, ease: enter(), immediateRender: false }, 0.1); })).indexOf("offset") !== -1);
});
test("a driver whose frame depends on the seek order is caught", function () {
  var build = fixture("zz-history", function (tl, host, b, card, d) {
    var s = { p: 0 }, calls = 0;
    tl.fromTo(s, { p: 0 }, { p: 1, duration: d, ease: "none", onUpdate: function () { calls++; card.setAttribute("data-calls", calls); } }, b.at);
  });
  assert.ok(tags(build).indexOf("seek") !== -1);
});
test("non-deterministic class names or text are caught", function () {
  assert.ok(tags(fixture("zz-class", function (tl, host) { K.el("div", "n" + counter++, host); })).indexOf("determinism") !== -1);
  assert.ok(tags(fixture("zz-text", function (tl, host) { K.el("div", "", host, "t" + counter++); })).indexOf("determinism") !== -1);
});
test("a build-time style that differs from the from-state is caught", function () {
  assert.ok(tags(fixture("zz-before", function (tl, host, b) { var e = K.el("div", "", host); tl.fromTo(e, { opacity: 0 }, { opacity: 1, duration: 0.3, ease: enter(), immediateRender: false }, b.at); })).indexOf("before-start") !== -1);
});
test("a glow on the light ground is caught (url filter, glow tag, text-shadow), the dark ground may keep it", function () {
  ["url", "tag", "shadow"].forEach(function (kind) {
    var build = fixture("zz-glow-" + kind, function (tl, host) {
      var e = K.el("div", "", host);
      if (kind === "url") e.style.filter = "url(#hf-glow-1)";
      else if (kind === "tag") e.setAttribute("data-blur-reason", "glow");
      else e.style.textShadow = "0 0 20px red";
    });
    assert.deepEqual(c.violations(build).filter(function (v) { return !/^\[glow\]/.test(v); }), [], kind + ": only the glow rule fires");
    assert.ok(tags(build).indexOf("glow") !== -1, kind);
  });
});
test("a component that ignores data-hf-mode, or its value, is caught", function () {
  K.register("zz-no-mode", "plain", function (tl, host, o) {
    if (o.format !== "long-form") throw new Error("HFKit.zzNoMode: kit components are long-form only");
    var e = K.el("div", "", host); tl.fromTo(e, { opacity: 1 }, { opacity: 0, duration: 0.3, ease: enter(), immediateRender: false }, 0);
    return { dur: 0.3 };
  });
  var build = function (tl, host, extra) { return K.zzNoMode(tl, host, Object.assign({ format: "long-form" }, extra)); };
  var v = c.violations(build);
  assert.equal(v.filter(function (x) { return /^\[mode\]/.test(x); }).length, 2, "missing and bad mode both reported: " + v.join(" | "));
});
test("a component that is not long-form only is caught", function () {
  K.register("zz-any-format", "plain", function (tl, host, o) { o = Object.assign({}, o, { format: "long-form" }); var b = K.begin("zz-any-format", host, o); K.cardIn(tl, K.el("div", "", host), b.at); return { dur: 0.43 }; });
  assert.ok(tags(function (tl, host, extra) { return K.zzAnyFormat(tl, host, extra); }).indexOf("format") !== -1);
});

// Contract-run on the good fixture too, through the same registration path real components use.
c.contract("zz-contract-run", fixture("zz-contract-run"));
