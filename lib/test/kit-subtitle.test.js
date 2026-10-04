"use strict";
var test = require("node:test");
var assert = require("node:assert/strict");
var h = require("./helpers.js");
var P = require("../profile.js");
var c = require("./kit-contract.js");
var K = require("../kit/kit.js");
require("../kit/subtitle.js");

function build(tl, host, extra) {
  return K.subtitle(tl, host, Object.assign({ format: "long-form", at: 0.2, kicker: "Step 1", title: "HIT Prediction" }, extra));
}
// the contract assumes a baseline of at: 0
c.contract("subtitle", function (tl, host, extra) { return build(tl, host, Object.assign({ at: 0 }, extra)); });

test("subtitle (dark): pill card entrance, script kicker at +0.3 s, glowing title one chain gap later", function () {
  c.fresh();
  var T = P.timing("long-form"), tl = h.fakeTimeline(), r = build(tl, h.kitHost("dark"), {});
  var card = tl.eased()[0];
  assert.equal(card.target, r.pill); assert.equal(card.ease.token, "ease.card"); assert.equal(card.at, 0.2);
  assert.equal(r.kicker.length, 6);
  var sets = tl.tweens.filter(function (tw) { return tw.kind === "set"; });
  assert.ok(Math.abs(sets[0].at - 0.5) < 1e-9 && Math.abs(sets[1].at - (0.5 + T.scriptMsPerChar / 1000)) < 1e-9, "135 ms per letter from +0.3 s");
  var glow = tl.drivers()[0];
  assert.ok(Math.abs(glow.at - (0.5 + T.chainGap)) < 1e-9);
  r.words.forEach(function (s) { assert.equal(s.getAttribute("data-blur-reason"), "glow"); });
});

test("subtitle (light): title words, then an accent.block marker sweeps behind it", function () {
  c.fresh();
  var tl = h.fakeTimeline(), host = h.kitHost("light"), r = build(tl, host, {});
  var sweep = tl.eased().filter(function (tw) { return tw.ease.token === "ease.sweep"; });
  assert.equal(sweep.length, 1);
  assert.equal(sweep[0].target.className, "hf-kit-marker");
  var lastWord = tl.eased().filter(function (tw) { return r.words.indexOf(tw.target) !== -1; }).pop();
  assert.ok(sweep[0].at >= lastWord.at + lastWord.dur, "the marker follows the landed title");
});

test("subtitle: title required; kicker optional", function () {
  c.fresh();
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { title: "" }); }, /opts\.title is required/);
  var r = build(h.fakeTimeline(), h.kitHost("dark"), { kicker: null });
  assert.deepEqual(r.kicker, []);
});

test("subtitle (light): the marker sweep lasts the same in a display:none scene as in a laid-out one", function () {
  function markerDur(visible) {
    h.textRig(visible);
    var tl = h.fakeTimeline();
    build(tl, h.kitHost("light"), { title: "Hidden Layer Prediction Of Every Result" });
    return tl.eased().filter(function (tw) { return tw.target.className === "hf-kit-marker"; })[0].dur;
  }
  var shown = markerDur(true), hidden = markerDur(false);
  var want = require("../marks.js").sweepDuration("Hidden Layer Prediction Of Every Result".length * 10 + 0.24 * 50, 1080, "long-form");
  assert.ok(want > P.timing("long-form").sweep.min, "the fixture title is wide enough to leave the clamp");
  assert.ok(Math.abs(hidden - want) < 1e-9, "sized from the title plus the marker's ±0.12em extension");
  assert.ok(Math.abs(shown - want) < 1e-9);
});
