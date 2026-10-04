"use strict";
var test = require("node:test");
var assert = require("node:assert/strict");
var h = require("./helpers.js");
var P = require("../profile.js");
var c = require("./kit-contract.js");
var K = require("../kit/kit.js");
require("../kit/lower-third.js");

function build(tl, host, extra) {
  return K.lowerThird(tl, host, Object.assign({ format: "long-form", at: 0.3, text: "and I've helped online entrepreneurs", out: 3.4 }, extra));
}
// the contract assumes at: 0 and no exit (dur == last tween end - at)
c.contract("lower-third", function (tl, host, extra) { return build(tl, host, Object.assign({ at: 0, out: null }, extra)); });

test("lower-third (dark): one line, words with one continuous white→warm gradient, fades out at opts.out", function () {
  c.fresh();
  var tl = h.fakeTimeline(), host = h.kitHost("dark"), r = build(tl, host, {});
  assert.equal(r.words.length, 5);
  r.words.forEach(function (s) {
    assert.ok(s.classList.contains("hf-kit-lt-word"));
    assert.equal(s.style.backgroundSize, "400px 100%", "every word is painted with the whole line's gradient");
  });
  var fade = tl.eased().filter(function (tw) { return tw.to.opacity === 0; })[0];
  assert.ok(Math.abs(fade.at + fade.dur - 3.4) < 1e-9, "gone at opts.out");
  assert.equal(fade.target.className, "hf-kit-lt");
  assert.doesNotMatch(h.descendants(host).map(function (e) { return e.className + " " + (e.getAttribute("id") || ""); }).join(" "), /caption/i, "QA check 7 must not read it as a caption layer");
});

test("lower-third (light): a frosted pill enters first, words 0.15 s later, no gradient", function () {
  c.fresh();
  var tl = h.fakeTimeline(), r = build(tl, h.kitHost("light"), {});
  var first = tl.eased()[0];
  assert.equal(first.ease.token, "ease.card"); assert.equal(first.target.className, "hf-kit-body hf-kit-lt-line");
  assert.ok(Math.abs(tl.eased()[1].at - 0.45) < 1e-9);
  r.words.forEach(function (s) { assert.ok(!s.classList.contains("hf-kit-lt-word")); });
});

test("lower-third: text required; opts.out must leave a hold", function () {
  c.fresh();
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { text: "" }); }, /opts\.text is required/);
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { out: 1.2 }); }, /leaves no hold/);
  var r = build(h.fakeTimeline(), h.kitHost("dark"), { out: null });
  assert.ok(r.dur > 0);
});
