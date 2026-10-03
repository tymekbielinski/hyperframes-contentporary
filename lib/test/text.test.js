"use strict";
var test = require("node:test");
var assert = require("node:assert/strict");
var h = require("./helpers.js");
var P = require("../profile.js");
var X = require("../text.js");

global.document = h.fakeDocument();
document.body = h.fakeEl("body");
var byId = {};
document.getElementById = function (id) { return byId[id] || null; };
var LF = { format: "long-form", frameHeight: 1080 };

test("words (long-form): one span per word, focus-tagged, 7 % rise, profile stagger + ease", function () {
  var tl = h.fakeTimeline(), el = h.fakeEl("h1", { text: "HIT  Prediction works" });
  var d = X.words(tl, el, 2, LF);
  assert.equal(el.children.length, 3);
  el.children.forEach(function (s) { assert.equal(s.getAttribute("data-blur-reason"), "focus"); });
  assert.deepEqual(tl.tweens.map(function (t) { return +t.at.toFixed(3); }), [2, 2.28, 2.56]);
  assert.ok(Math.abs(tl.tweens[0].from.y - 75.6) < 1e-9);
  assert.equal(tl.tweens[0].ease, P.ease("long-form", "ease.enter"));
  assert.ok(Math.abs(d - (2 * 0.28 + 0.6)) < 1e-9);
  assert.deepEqual(h.conflicts(tl), []);
  assert.deepEqual(h.visibleBeforeStart(tl), []);
});

test("words: stagger outside the long-form band throws; Shorts default 200 ms; empty text is a no-op", function () {
  assert.throws(function () { X.words(h.fakeTimeline(), h.fakeEl("p", { text: "a b" }), 0, Object.assign({ stagger: 0.12 }, LF)); }, /stagger must be 0.23–0.33/);
  var tl = h.fakeTimeline();
  X.words(tl, h.fakeEl("p", { text: "We Handle Everything!" }), 26.93, { format: "shorts", frameHeight: 1920 });
  assert.ok(Math.abs(tl.tweens[2].at - 27.33) < 1e-9);
  var tl2 = h.fakeTimeline();
  assert.equal(X.words(tl2, h.fakeEl("p", { text: "   " }), 0, LF), 0);
  assert.equal(tl2.tweens.length, 0);
});

test("typeOn: Shorts 67 ms/char by default; long-form must pass a rate", function () {
  var tl = h.fakeTimeline(), el = h.fakeEl("span", { text: "Meetings" });
  X.typeOn(tl, el, 6.067, { format: "shorts", blinks: 0 });
  var firstChars = tl.tweens.filter(function (t) { return t.vars.visibility === "visible" && t.target.style.position === "relative"; });
  assert.equal(firstChars.length, 8);
  assert.ok(Math.abs(firstChars[1].at - (6.067 + 0.067)) < 1e-9);
  assert.throws(function () { X.typeOn(h.fakeTimeline(), h.fakeEl("span", { text: "x" }), 0, LF); }, /has no type-on rate/);
});

test("glowFilter: five Gaussian levels, every one tagged glow", function () {
  var m = X.glowFilter("g1");
  assert.equal((m.match(/<feGaussianBlur /g) || []).length, 5);
  assert.equal((m.match(/<feGaussianBlur data-blur-reason="glow"/g) || []).length, 5);
  assert.match(m, /id="g1-r"/);
});

test("glowOpacity: hidden until just after its time, pops to 0.7, settles to 1 in 0.4 s", function () {
  assert.equal(X.glowOpacity(-1, "long-form"), 0);
  assert.equal(X.glowOpacity(0, "long-form"), 0);
  assert.ok(X.glowOpacity(0.001, "long-form") >= 0.7);
  assert.equal(X.glowOpacity(0.4, "long-form"), 1);
  assert.throws(function () { X.glowOpacity(0.1, "shorts"); }, /glow/);
});

test("glowTitle: long-form only, one driver, words 430 ms apart, seek-order safe", function () {
  assert.throws(function () { X.glowTitle(h.fakeTimeline(), [h.fakeEl()], 0, { format: "shorts", frameHeight: 1920 }); }, /not in the shorts ease table/);
  var tl = h.fakeTimeline(), w1 = h.fakeEl("span"), w2 = h.fakeEl("span");
  var d = X.glowTitle(tl, [w1, w2], 4, Object.assign({ glowId: "gt" }, LF));
  assert.ok(Math.abs(d - 0.83) < 1e-9);
  assert.equal(tl.drivers().length, 1);
  assert.equal(w1.getAttribute("data-blur-reason"), "glow");
  assert.deepEqual(h.seekOrderInvariant(tl, [3, 4, 4.1, 4.3, 4.43, 4.5, 4.83, 6], [w1, w2]), []);
  tl.seek(4.2); assert.equal(w2.style.opacity, "0.0000");
});

test("defocus: focus-tagged blur + dim on ease.enter; not in Shorts", function () {
  var tl = h.fakeTimeline(), bg = h.fakeEl("div");
  X.defocus(tl, bg, 1, LF);
  assert.equal(bg.getAttribute("data-blur-reason"), "focus");
  assert.equal(tl.tweens[0].to.filter, "blur(4.50px) brightness(0.6)");
  assert.equal(bg.style.filter, tl.tweens[0].from.filter, "pre-start state = from-state");
  assert.throws(function () { X.defocus(h.fakeTimeline(), bg, 1, { format: "shorts", frameHeight: 1920 }); }, /no backdrop defocus/);
});

test("accentWord is a single attribute set (seek-safe), styled by the brand variable", function () {
  var tl = h.fakeTimeline(), el = h.fakeEl("span");
  X.accentWord(tl, el, 3);
  assert.deepEqual(tl.tweens[0].vars, { attr: { "data-hf-accent": "1" } });
  assert.match(X.CSS, /var\(--hf-accent-text\)/);
});

test("odometer math: start values always lower than the final", function () {
  assert.equal(X.startValue(150000, 0), 100000);
  assert.equal(X.startValue(14.4, 1), 10);
  assert.equal(X.startValue(10, 0), 7);
  assert.equal(X.startValue(8, 0), 5);
  assert.equal(X.startValue(0, 0), 0);
  var p = X.parseRuns("$150,000");
  assert.equal(p.runs.length, 1);
  assert.equal(p.runs[0].final, 150000); assert.equal(p.runs[0].start, 100000);
  assert.equal(p.runs[0].seps[0].threshold, 1000);
  assert.equal(X.parseRuns("14.4").runs[0].decimals, 1);
  assert.equal(X.parseRuns("10+", 9).runs[0].start, 9);
  assert.equal(X.parseRuns("10+", 50).runs[0].start, 7);
  assert.deepEqual(X.parseRuns("N/A").runs, []);
});

test("odometer wheels: units roll continuously, higher places only turn during the carry", function () {
  var run = X.parseRuns("19").runs[0];
  var units = { run: run, place: 0, p10: 1 }, tens = { run: run, place: 1, p10: 10 };
  assert.ok(Math.abs(X.wheelPos(units, 12.5) - 2.5) < 1e-9);
  assert.equal(X.wheelPos(tens, 12.5), 1);
  assert.ok(Math.abs(X.wheelPos(tens, 19.5) - 1.5) < 1e-9);
  assert.ok(Math.abs(X.wheelUnwrapped(tens, 29.5) - 2.5) < 1e-9);
  assert.equal(X.wheelUnwrapped(tens, 30), 3);
});

test("odometer: a label without digits just appears", function () {
  var tl = h.fakeTimeline();
  var el = h.fakeEl("span");
  X.odometer(tl, el, 1, 2, "N/A", { format: "long-form" });
  assert.deepEqual(tl.tweens.map(function (t) { return t.kind; }), ["set"]);
  assert.equal(el.style.opacity, "0", "hidden until T");
});

test("words: build-time style equals the tween from-state (opacity, rise, blur)", function () {
  var tl = h.fakeTimeline(), el = h.fakeEl("h1", { text: "one two" });
  X.words(tl, el, 1, LF);
  el.children.forEach(function (s, i) {
    assert.equal(s.style.opacity, "0");
    assert.equal(s.style.transform, "translate(0px, " + tl.tweens[i].from.y + "px)");
    assert.equal(s.style.filter, tl.tweens[i].from.filter);
  });
});
