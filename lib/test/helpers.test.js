"use strict";
// The test doubles themselves: visibleBeforeStart must catch a transform or filter that differs from a
// tween's from-state (the Plan 2 review gap), not only an opacity.
var test = require("node:test");
var assert = require("node:assert/strict");
var h = require("./helpers.js");

test("parseTransform reads translate/scale/rotate in any order", function () {
  assert.deepEqual(h.parseTransform("translate(0px, 75.6px)"), { x: 0, y: 75.6, scaleX: 1, scaleY: 1, rotation: 0 });
  assert.deepEqual(h.parseTransform("translateY(12px) scale(0.6)"), { x: 0, y: 12, scaleX: 0.6, scaleY: 0.6, rotation: 0 });
  assert.deepEqual(h.parseTransform("scaleX(0)"), { x: 0, y: 0, scaleX: 0, scaleY: 1, rotation: 0 });
  assert.deepEqual(h.parseTransform(""), { x: 0, y: 0, scaleX: 1, scaleY: 1, rotation: 0 });
});

test("visibleBeforeStart flags opacity, transform and filter that differ from the from-state", function () {
  function one(style, from) {
    var tl = h.fakeTimeline(), el = h.fakeEl("div");
    Object.assign(el.style, style);
    tl.fromTo(el, from, { duration: 1, ease: function () {} }, 1);
    return h.visibleBeforeStart(tl);
  }
  assert.deepEqual(one({ opacity: "0", transform: "translate(0px, 40px)" }, { opacity: 0, y: 40 }), []);
  assert.deepEqual(one({ opacity: "0" }, { opacity: 0, y: 40 }), [0], "rise missing at build");
  assert.deepEqual(one({ transform: "scale(0.5)" }, { scale: 0 }), [0], "wrong scale at build");
  assert.deepEqual(one({ opacity: "0", filter: "blur(8px)" }, { opacity: 0, filter: "blur(0px)" }), [0], "filter differs");
  assert.deepEqual(one({}, { opacity: 1 }), [], "an unset opacity is 1");
  assert.deepEqual(one({}, { opacity: 0 }), [0]);
});

test("parseTransform is strict: unknown functions and units throw, translate(a, b) equals translateX + translateY", function () {
  assert.deepEqual(h.parseTransform("translate(0px, 5px)"), h.parseTransform("translateY(5px)"));
  assert.deepEqual(h.parseTransform("none"), { x: 0, y: 0, scaleX: 1, scaleY: 1, rotation: 0 });
  assert.throws(function () { h.parseTransform("translate3d(0px, 5px, 0px)"); }, /unsupported transform function "translate3d"/);
  assert.throws(function () { h.parseTransform("matrix(1, 0, 0, 1, 0, 5)"); }, /unsupported transform function "matrix"/);
  assert.throws(function () { h.parseTransform("skewX(5deg)"); }, /unsupported transform function "skewX"/);
  assert.throws(function () { h.parseTransform("translateX(50%)"); }, /unsupported unit/);
  assert.throws(function () { h.parseTransform("rotate(0.5turn)"); }, /unsupported unit/);
  assert.throws(function () { h.parseTransform("translateX(5px) garbage"); }, /unparsed/);
});

test("visibleBeforeStart: NaN never passes, unsupported from-state transform keys fail loudly", function () {
  function one(style, from) {
    var tl = h.fakeTimeline(), el = h.fakeEl("div");
    Object.assign(el.style, style);
    tl.fromTo(el, from, { duration: 1, ease: function () {} }, 1);
    return h.visibleBeforeStart(tl);
  }
  assert.deepEqual(one({ transform: "translateX(999px)" }, { x: "50%" }), [0], "a percent from-value is flagged, not ignored");
  assert.deepEqual(one({ opacity: "0" }, { opacity: NaN }), [0], "a NaN opacity is a mismatch");
  assert.deepEqual(one({ transform: "translate(0px, 5px)" }, { y: 5 }), [], "translate(a, b) is translateY");
  assert.throws(function () { one({ transform: "translate3d(0px, 5px, 0px)" }, { y: 5 }); }, /unsupported transform function/);
  ["xPercent", "yPercent", "skewX", "skewY", "rotationZ", "z"].forEach(function (k) {
    var from = {}; from[k] = 10;
    assert.throws(function () { one({}, from); }, new RegExp("from-state key \"" + k + "\""), k);
  });
});
