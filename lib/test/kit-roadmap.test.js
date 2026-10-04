"use strict";
var test = require("node:test");
var assert = require("node:assert/strict");
var h = require("./helpers.js");
var P = require("../profile.js");
var c = require("./kit-contract.js");
var K = require("../kit/kit.js");
require("../kit/roadmap.js");

var STEPS = [{ label: "Predictive Idea Selection", icon: "bulb" }, { label: "Retention Based Editing", icon: "sliders" }, { label: "Qualified Sales Calls", icon: "target" }];
function build(tl, host, extra) {
  return K.roadmap(tl, host, Object.assign({ format: "long-form", at: 0.2, visit: 1, title: "Printing Prediction System", steps: STEPS }, extra));
}
c.contract("roadmap", function (tl, host, extra) { return build(tl, host, Object.assign({ at: 0 }, extra)); });
c.contract("roadmap intro", function (tl, host, extra) { return build(tl, host, Object.assign({ at: 0, visit: 0 }, extra)); });

test("roadmap geometry: nodes every 640 px alternating low/high, world widens past 3 steps", function () {
  var g3 = K.roadmapGeometry(3), g5 = K.roadmapGeometry(5);
  assert.deepEqual(g3.nodes, [{ x: 320, y: 700 }, { x: 960, y: 520 }, { x: 1600, y: 700 }]);
  assert.equal(g3.width, 1920);
  assert.equal(g5.width, 3200);
  assert.equal(g3.d, K.roadmapGeometry(3).d, "pure");
  assert.match(g3.d, /^M-400 610 C/);
});

test("roadmap intro: path draws on ease.sweep, each node pops when the line reaches it", function () {
  c.fresh();
  var tl = h.fakeTimeline(), host = h.kitHost("dark"), r = build(tl, host, { visit: 0 });
  var draw = tl.eased().filter(function (tw) { return tw.ease.token === "ease.sweep"; })[0];
  assert.equal(draw.at, 0.5); assert.equal(draw.dur, 1.2);
  var e = P.ease("long-form", "ease.sweep");
  var pops = r.nodes.map(function (n) { return tl.eased().filter(function (tw) { return tw.target === n; })[0]; });
  pops.forEach(function (tw, i) {
    var f = (K.roadmapGeometry(3).nodes[i].x + 400) / (1920 + 800);
    assert.ok(Math.abs(e((tw.at - draw.at) / draw.dur) - f) < 1e-5, "node " + (i + 1) + " pops as the line reaches it");
    assert.equal(tw.dur, P.timing("long-form").node.dur);
  });
  r.cards.forEach(function (card) { assert.equal(card.style.visibility, "hidden"); });
  assert.equal(r.pose.z, 1);
});

test("roadmap visit k opens exactly where visit k-1 ended (camera + docked cards)", function () {
  c.fresh();
  var prev = build(h.fakeTimeline(), h.kitHost("dark"), { visit: 1 });
  c.fresh();
  var tl = h.fakeTimeline(), host = h.kitHost("dark"), r = build(tl, host, { visit: 2 });
  var stage = h.descendants(host).filter(function (e) { return e.className === "hf-kit-rm-stage"; })[0];
  var d0 = require("../camera.js").domTransform(prev.pose, 1920, 1080);
  var want = "translate(" + d0.dx.toFixed(2) + "px," + d0.dy.toFixed(2) + "px) scale(" + d0.z.toFixed(4) + ")";
  assert.equal(stage.style.transform, want, "pose before any seek");
  tl.seek(0);
  assert.equal(stage.style.transform, want, "pose at seek 0");
  assert.deepEqual(r.cards.map(function (e) { return e.style.visibility || "visible"; }), ["visible", "visible", "hidden"]);
  assert.equal(tl.eased()[0].target, r.cards[1], "card 2 docks");
  assert.equal(tl.eased()[0].ease.token, "ease.card");
  assert.deepEqual(h.seekOrderInvariant(tl, [0, 0.2, 0.6, 1.0, 1.4, 1.8, 3], [stage]), []);
});

test("roadmap: 3–6 steps, visit within range, known icons, a title", function () {
  c.fresh();
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { steps: STEPS.slice(0, 2) }); }, /3–6 steps, got 2/);
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { visit: 4 }); }, /visit must be 0 \(intro\) … 3, got 4/);
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { steps: [{ label: "a", icon: "rocket" }, STEPS[1], STEPS[2]] }); }, /icon "rocket" \(have: bulb, sliders, chart, target\)/);
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { title: "" }); }, /opts\.title is required/);
});

function parts(host) {
  var all = h.descendants(host);
  return {
    title: all.filter(function (e) { return /hf-kit-rm-title/.test(e.className); })[0],
    path: all.filter(function (e) { return e.tagName && e.tagName.toLowerCase() === "path" && e.parentNode && /hf-kit-rm-path/.test(e.parentNode.getAttribute("class") || ""); })[0]
  };
}
function sig(title) { return title.children.map(function (c) { return [c.textContent, c.style.display, c.style.whiteSpace].join("|"); }).join("/"); }

test("roadmap: title word spans and the settled path match between the intro and every visit", function () {
  c.fresh();
  var h0 = h.kitHost("dark"); build(h.fakeTimeline(), h0, { visit: 0 });
  var p0 = parts(h0);
  assert.ok(p0.title.children.length > 1, "intro title is split into word spans");
  [1, 2, 3].forEach(function (v) {
    c.fresh();
    var hv = h.kitHost("dark"); build(h.fakeTimeline(), hv, { visit: v });
    var pv = parts(hv);
    assert.equal(sig(pv.title), sig(p0.title), "visit " + v + " title structure");
    assert.ok(!pv.path.style.strokeDasharray, "visit " + v + " path is not dashed");
  });
});

test("roadmap: both ends of the wave are off-frame at every visit's hold, and the card renders ≈ 450 px", function () {
  [3, 5].forEach(function (n) {
    var g = K.roadmapGeometry(n), start = -g.ext, end = g.width + g.ext;
    for (var k = 1; k <= n; k++) {
      var p = K.roadmapPose(g, k), half = 960 / p.z;
      assert.ok(start < p.cx - half - 100, "n=" + n + " visit " + k + ": start off-frame with margin");
      assert.ok(end > p.cx + half + 100, "n=" + n + " visit " + k + ": end off-frame with margin");
      assert.ok(Math.abs(250 * p.z - 450) < 5, "card ≈ 450 px");
    }
  });
});

test("roadmap: icon names are own keys; steps must be an array", function () {
  c.fresh();
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { steps: [{ label: "a", icon: "constructor" }, STEPS[1], STEPS[2]] }); }, /icon "constructor"/);
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { steps: "abc" }); }, /3–6 steps, got 0/);
});
