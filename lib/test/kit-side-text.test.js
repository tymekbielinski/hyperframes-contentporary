"use strict";
var test = require("node:test");
var assert = require("node:assert/strict");
var h = require("./helpers.js");
var P = require("../profile.js");
var c = require("./kit-contract.js");
var K = require("../kit/kit.js");
require("../kit/side-text.js");

var ITEMS = ["Video performance", "Retention", "CTR (Click through rate)"];
function build(tl, host, extra) {
  return K.sideText(tl, host, Object.assign({ format: "long-form", at: 0.2, items: ITEMS, out: 4.4 }, extra));
}
// the contract assumes at: 0 and no exit (dur == last tween end - at)
c.contract("side-text", function (tl, host, extra) { return build(tl, host, Object.assign({ at: 0, out: null }, extra)); });

test("side-text: panel slides in, each point = chip (status chip) + label words 0.1 s later, rows 145 px apart", function () {
  c.fresh();
  var T = P.timing("long-form"), tl = h.fakeTimeline(), r = build(tl, h.kitHost("dark"), {});
  assert.equal(r.chips.length, 3);
  assert.deepEqual(r.chips.map(function (e) { return e.style.top; }), ["140px", "285px", "430px"]);
  assert.deepEqual(r.chips.map(function (e) { return e.children[0].textContent; }), ["1", "2", "3"]);
  var chipAt = r.chips.map(function (e) { return tl.eased().filter(function (tw) { return [].concat(tw.target).indexOf(e) !== -1; })[0].at; });
  var first = 0.2 + T.words.dur / 2;
  chipAt.forEach(function (a, i) { assert.ok(Math.abs(a - (first + i * 2 * T.chainGap)) < 1e-9, "point " + i); });
  var label0 = tl.eased().filter(function (tw) { return tw.target === r.labels[0][0]; })[0];
  assert.ok(Math.abs(label0.at - (chipAt[0] + 0.1)) < 1e-9);
});

test("side-text: explicit item times, 1–6 points, a point before the panel throws", function () {
  c.fresh();
  var tl = h.fakeTimeline(), r = build(tl, h.kitHost("dark"), { items: [{ text: "One", at: 1 }, { text: "Two", at: 2.5 }], out: null });
  assert.equal(r.chips.length, 2);
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { items: [] }); }, /1–6 items, got 0/);
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { items: ["a", "b", "c", "d", "e", "f", "g"] }); }, /1–6 items, got 7/);
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { items: [{ text: "x", at: 0.1 }] }); }, /before the panel/);
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { out: 2 }); }, /leaves no hold/);
});

test("side-text (light): frosted panel, no grid ground inside it", function () {
  c.fresh();
  var host = h.kitHost("light");
  build(h.fakeTimeline(), host, {});
  assert.ok(!h.descendants(host).some(function (e) { return e.className === "hf-kit-ground"; }));
});

test("side-text: a bad item leaves no partial DOM (all items validated before the first element)", function () {
  c.fresh();
  var host = h.kitHost("dark");
  assert.throws(function () { build(h.fakeTimeline(), host, { items: ["fine", { text: "late", at: 0.1 }] }); }, /before the panel/);
  assert.throws(function () { build(h.fakeTimeline(), host, { items: ["fine", { text: "  " }] }); }, /item 1 has no text/);
  assert.equal(host.children.length, 0);
});
