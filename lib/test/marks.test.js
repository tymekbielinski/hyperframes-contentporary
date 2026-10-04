"use strict";
var test = require("node:test");
var assert = require("node:assert/strict");
var h = require("./helpers.js");
var P = require("../profile.js");
var M = require("../marks.js");

global.document = h.fakeDocument();
var LF = { format: "long-form", frameHeight: 1080 };

test("path generators are deterministic, seed-sensitive and finite", function () {
  [
    function (s) { return M.ringPath(500, 300, 120, 60, s); },
    function (s) { return M.scribblePath(100, 700, 600, s); },
    function (s) { return M.strikePath(100, 400, 500, s); },
    function (s) { return M.outlinePath(80, 90, 400, 200, s); }
  ].forEach(function (gen) {
    assert.equal(gen(3), gen(3));
    assert.notEqual(gen(3), gen(4));
    assert.ok(!/NaN|Infinity/.test(gen(3)));
    assert.match(gen(3), /^M/);
  });
  assert.equal((M.ringPath(0, 0, 10, 10, 1).match(/ C/g) || []).length, 22);
});

test("arrowPath: shaft ends where the head points; elbowPath turns once", function () {
  var a = M.arrowPath(100, 100, 700, 300, 80);
  assert.match(a.shaft, / 700 300$/);
  assert.match(a.head, / L700 300 L/);
  assert.equal(M.elbowPath(0, 0, 400, 200), "M0 0 L376.0 0 Q 400 0 400 24.0 L400 200");
  assert.equal(M.elbowPath(0, 0, 400, 200, { axis: "v", radius: 500 }), "M0 0 L0 100.0 Q 0 200 100.0 200 L400 200");
});

test("sweepDuration: ≈ 360 px/s at 720p, clamped to 0.5–1.0 s, scales with frame height", function () {
  assert.equal(M.sweepDuration(100, 720, "long-form"), 0.5);
  assert.equal(M.sweepDuration(5000, 720, "long-form"), 1.0);
  assert.equal(M.sweepDuration(270, 720, "long-form"), 0.75);
  assert.equal(M.sweepDuration(405, 1080, "long-form"), 0.75);
});

test("draw: dash from full length to 0 on ease.sweep at T", function () {
  var tl = h.fakeTimeline(), p = h.fakeEl("path", { length: 200 });
  M.draw(tl, p, 2, 0.6, { format: "long-form" });
  var tw = tl.tweens[0];
  assert.equal(tw.at, 2); assert.equal(tw.from.strokeDashoffset, 206); assert.equal(tw.to.strokeDashoffset, 0);
  assert.equal(tw.ease, P.ease("long-form", "ease.sweep"));
});

test("highlight: thin seed -> full width, duration from width", function () {
  var tl = h.fakeTimeline(), el = h.fakeEl("div", { width: 540 });
  var d = M.highlight(tl, el, 1, LF);
  assert.equal(d, 1.0);
  assert.equal(tl.tweens[0].from.scaleX, 0);
  assert.equal(el.style.transform, "scaleX(0)", "hidden before T, same as the from-state");
  assert.throws(function () { M.highlight(tl, el, 1, { format: "long-form" }); }, /frameHeight is required/);
});

test("swap is one 133 ms tween over the whole set", function () {
  var tl = h.fakeTimeline(), els = [h.fakeEl(), h.fakeEl(), h.fakeEl()];
  M.swap(tl, els, 7.2, { opacity: 0.4 }, { format: "shorts" });
  assert.equal(tl.tweens.length, 1);
  assert.equal(tl.tweens[0].dur, 0.133); assert.equal(tl.tweens[0].target, els);
});

test("statusChip: peers land together on ease.enter; seedChip needs pill + label", function () {
  var tl = h.fakeTimeline(), chips = [h.fakeEl(), h.fakeEl()];
  M.statusChip(tl, chips, 3, LF);
  assert.equal(tl.tweens.length, 1);
  assert.equal(tl.tweens[0].ease, P.ease("long-form", "ease.enter"));
  assert.deepEqual(h.visibleBeforeStart(tl), []);
  chips.forEach(function (c) { assert.equal(c.style.transform, "translateY(" + (tl.tweens[0].from.y) + "px) scale(" + tl.tweens[0].from.scale + ")"); });
  var tl2 = h.fakeTimeline(), pill = h.fakeEl("div", { width: 300, height: 60 }), label = h.fakeEl("span");
  assert.equal(M.seedChip(tl2, { pill: pill, label: label }, 25.167, { format: "shorts" }), 0.05 + 0.167);
  assert.equal(tl2.tweens[1].from.scaleX, 0.2);
  assert.equal(pill.style.transform, "scaleX(" + tl2.tweens[1].from.scaleX + ")", "build-time pill transform = scaleX from-state");
  assert.deepEqual(h.conflicts(tl2), []);
  assert.deepEqual(h.visibleBeforeStart(tl2), []);
  assert.throws(function () { M.seedChip(tl2, { pill: pill }, 0, { format: "shorts" }); }, /pill, label/);
  assert.throws(function () { M.seedChip(tl2, { pill: pill, label: label }, 0, LF); }, /no chip seed/);
});

test("scriptWord: one stepped set per character at the profile rate", function () {
  var tl = h.fakeTimeline(), el = h.fakeEl("span", { text: "Done" });
  var d = M.scriptWord(tl, el, 10, LF);
  assert.equal(el.children.length, 4);
  assert.deepEqual(tl.tweens.map(function (t) { return t.at; }), [10, 10.135, 10.27, 10.405]);
  assert.ok(Math.abs(d - 0.54) < 1e-9);
  var tl2 = h.fakeTimeline();
  M.scriptWord(tl2, h.fakeEl("span", { text: "ab" }), 0, { format: "shorts" });
  assert.equal(tl2.tweens[1].at, 0.067);
});

test("binders require a format", function () {
  assert.throws(function () { M.draw(h.fakeTimeline(), h.fakeEl("path"), 0, 1); }, /opts.format is required/);
});

test("draw: a path with no length (0 or throwing getTotalLength) fails loudly at build", function () {
  var zero = h.fakeEl("path", {}); zero._len = 0;
  assert.throws(function () { M.draw(h.fakeTimeline(), zero, 0, 1, { format: "long-form" }); }, /HFMarks\.draw: path has no length \(set its d \/ geometry before binding\)/);
  var bad = h.fakeEl("path"); bad.getTotalLength = function () { throw new Error("not rendered"); };
  assert.throws(function () { M.draw(h.fakeTimeline(), bad, 0, 1, { format: "long-form" }); }, /path has no length/);
});

test("scriptWord: iterates code points, so an emoji is one step", function () {
  var tl = h.fakeTimeline(), el = h.fakeEl("span", { text: "ok🔥" });
  var d = M.scriptWord(tl, el, 0, { format: "shorts", msPerChar: 100 });
  assert.equal(el.children.length, 3);
  assert.equal(el.children[2].textContent, "🔥");
  assert.ok(Math.abs(d - 0.3) < 1e-9);
});

test("highlight / statusChip refuse an element another binder transforms", function () {
  var el = h.fakeEl("div");
  M.highlight(h.fakeTimeline(), el, 0, LF);
  assert.throws(function () { M.statusChip(h.fakeTimeline(), el, 0, LF); }, /HFMarks\.statusChip would overwrite the inline transform that HFMarks\.highlight animates/);
});
