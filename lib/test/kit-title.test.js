"use strict";
var test = require("node:test");
var assert = require("node:assert/strict");
var h = require("./helpers.js");
var P = require("../profile.js");
var c = require("./kit-contract.js");
var K = require("../kit/kit.js");
require("../kit/title.js");

function build(tl, host, extra) {
  return K.title(tl, host, Object.assign({ format: "long-form", at: 0.2, text: "Printing  Prediction System", underline: 1 }, extra));
}
// the contract assumes a baseline of at: 0 (it checks dur == last tween end - at and shifts by 2.5)
c.contract("title", function (tl, host, extra) { return build(tl, host, Object.assign({ at: 0 }, extra)); });

test("title (dark): glow title words 430 ms apart, warm ambience, underline after it settles", function () {
  c.fresh();
  var tl = h.fakeTimeline(), host = h.kitHost("dark"), r = build(tl, host, {});
  assert.deepEqual(r.words.map(function (s) { return s._text; }), ["Printing ", "Prediction ", "System"]);
  assert.equal(r.words[1].children[0].getAttribute("class"), "hf-kit-underline", "the underline lives inside its word");
  r.words.forEach(function (s) { assert.equal(s.getAttribute("data-blur-reason"), "glow"); });
  assert.equal(tl.drivers().length, 1, "one glow driver");
  assert.ok(h.descendants(host).some(function (e) { return e.className === "hf-kit-ground-ambient"; }));
  var draw = tl.eased().filter(function (tw) { return tw.ease.token === "ease.sweep"; })[0];
  var glow = 2 * P.timing("long-form").glow.nextWord + P.timing("long-form").glow.settle;
  assert.ok(Math.abs(draw.at - (0.2 + glow + P.timing("long-form").chainGap)) < 1e-9, "underline starts one chain gap after the title settles");
  assert.ok(Math.abs(r.dur - (draw.at - 0.2 + draw.dur)) < 1e-9);
  assert.deepEqual(h.seekOrderInvariant(tl, [0, 0.2, 0.3, 0.63, 0.9, 1.06, 1.5, 4], r.words), []);
});

test("title (light): words entrance in text.primary, no ambience, same underline", function () {
  c.fresh();
  var tl = h.fakeTimeline(), host = h.kitHost("light"), r = build(tl, host, {});
  assert.equal(tl.drivers().length, 0);
  r.words.forEach(function (s) { assert.equal(s.getAttribute("data-blur-reason"), "focus"); });
  assert.ok(!h.descendants(host).some(function (e) { return e.className === "hf-kit-ground-ambient"; }));
  assert.equal(tl.eased().filter(function (tw) { return tw.ease.token === "ease.sweep"; }).length, 1);
});

test("title: text is required; underline must name a word", function () {
  c.fresh();
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { text: "  " }); }, /opts\.text is required/);
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { underline: 7 }); }, /underline 7 is not a word index \(0–2\)/);
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { at: -1 }); }, /opts\.at must be a time/);
});
