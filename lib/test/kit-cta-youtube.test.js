"use strict";
var test = require("node:test");
var assert = require("node:assert/strict");
var h = require("./helpers.js");
var P = require("../profile.js");
var c = require("./kit-contract.js");
var K = require("../kit/kit.js");
require("../kit/cta-youtube.js");

var PAGE = { src: "assets/captures/watch-page.png", width: 2560, height: 1440, player: [112, 150, 1600, 900], link: [150, 1235, 560, 44] };
function build(tl, host, extra) {
  return K.ctaYoutube(tl, host, Object.assign({ format: "long-form", at: 0, footage: h.fakeEl("video"), page: PAGE }, extra));
}
c.contract("cta-youtube", function (tl, host, extra) { return build(tl, host, Object.assign({ at: 0 }, extra)); });

test("cta poses: the player fills the frame, then 0.80 of it, then 2× onto the link", function () {
  var p = K.ctaPoses(PAGE, K.FRAME, P.timing("long-form").cta);
  assert.deepEqual(p.face, { cx: 912, cy: 600, z: 1.2 });
  assert.ok(Math.abs(p.player.z - 0.96) < 1e-12);
  assert.deepEqual([p.link.cx, p.link.cy], [430, 1257]);
  assert.ok(Math.abs(p.link.z - 1.92) < 1e-12);
});

test("cta: one DOM camera over 4.9 s — scale 0.5, hold 0.5, dive 0.6, hold 1.7, back 0.6, hold 0.5, up 0.5", function () {
  c.fresh();
  var tl = h.fakeTimeline(), host = h.kitHost("dark"), face = h.fakeEl("video"), r = build(tl, host, { footage: face, at: 1 });
  assert.ok(Math.abs(r.dur - 4.9) < 1e-9);
  assert.equal(tl.drivers().length, 1);
  assert.equal(tl.drivers()[0].at, 1);
  var stage = h.descendants(host).filter(function (e) { return e.className === "hf-kit-cta-stage"; })[0];
  assert.equal(face.parentNode.className, "hf-kit-cta-player", "the footage sits in the player slot");
  function zoom(t) { tl.seek(t); return parseFloat(/scale\(([\d.]+)\)/.exec(stage.style.transform)[1]); }
  assert.equal(zoom(1), 1.2); assert.equal(zoom(1.75), 0.96); assert.equal(zoom(3.5), 1.92); assert.equal(zoom(5.2), 0.96); assert.equal(zoom(6), 1.2);
  assert.deepEqual(h.seekOrderInvariant(tl, [0, 1, 1.25, 1.5, 2, 2.3, 2.6, 4, 4.6, 5, 5.4, 5.9, 7], [stage]), []);
});

test("cta: a real page screenshot and the footage element are required", function () {
  c.fresh();
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { page: { width: 10, height: 10 } }); }, /page needs src, width and height/);
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { footage: null }); }, /opts\.footage must be/);
  assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { page: Object.assign({}, PAGE, { link: [1, 2, 3] }) }); }, /page\.link must be \[x, y, w, h\]/);
});
