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
