"use strict";
var test = require("node:test");
var assert = require("node:assert/strict");
var h = require("./helpers.js");
var P = require("../profile.js");
var Wp = require("../shorts/wipe.js");

test("wipeState: blur + feather ride speed — none at the ends, max mid-travel", function () {
  assert.deepEqual(Wp.wipeState(0.5, 14, "right"), { std: "14.00 0",
    mask: "linear-gradient(to right, rgba(0,0,0,1) 29.00%, rgba(0,0,0,0) 71.00%)", filterOn: true });
  assert.deepEqual(Wp.wipeState(1, 14, "down"), { std: "0 0.00", mask: "none", filterOn: false });
  var start = Wp.wipeState(0, 14, "up");
  assert.equal(start.std, "0 0.00"); assert.equal(start.filterOn, false);
  assert.match(start.mask, /rgba\(0,0,0,0\) 0%, rgba\(0,0,0,0\) 100%/);
  assert.throws(function () { Wp.wipeState(0.5, 14, "diagonal"); }, /dir must be/);
});

test("wipeProgress: 0.42 s in on ease.cut, hold at 1, 0.36 s out", function () {
  var e = P.ease("shorts", "ease.cut");
  assert.equal(Wp.wipeProgress(2.0, 2, 10).q, 0);
  assert.equal(Wp.wipeProgress(2.21, 2, 10).q, e(0.21 / 0.42));
  assert.equal(Wp.wipeProgress(5, 2, 10).q, 1);
  assert.ok(Math.abs(Wp.wipeProgress(10 - 0.18, 2, 10).q - 0.5) < 1e-6);
  assert.equal(Wp.wipeProgress(10, 2, 10).q, 0);
  assert.equal(Wp.wipeProgress(9.9, 2, 10).blurMax, 12);
});

test("wipe: one driver, tags the blur 'wipe', mask is seek-order safe", function () {
  var tl = h.fakeTimeline(), host = h.fakeEl("div"), fe = h.fakeEl("feGaussianBlur");
  var d = Wp.wipe(tl, { host: host, fe: fe, filterId: "mb-sa", dir: "down", inAt: 2.3, outAt: 13.06 });
  assert.ok(Math.abs(d - 10.76) < 1e-9);
  assert.equal(fe.getAttribute("data-blur-reason"), "wipe");
  assert.equal(host.style.visibility, "hidden", "hidden until the wipe starts");
  assert.equal(tl.drivers().length, 1);
  assert.deepEqual(h.seekOrderInvariant(tl, [2.3, 2.4, 2.5, 2.72, 5, 12.7, 12.8, 12.9, 13.06], [host, fe]), []);
  tl.seek(2.5); assert.equal(host.style.filter, "url(#mb-sa)");
  tl.seek(6); assert.equal(host.style.filter, "none"); assert.equal(host.style.maskImage, "none");
});

test("wipe: rejects a scene shorter than in + out, and a wipe with no times", function () {
  assert.throws(function () { Wp.wipe(h.fakeTimeline(), { host: h.fakeEl(), dir: "left", inAt: 1, outAt: 1.5 }); }, /scene too short/);
  assert.throws(function () { Wp.wipe(h.fakeTimeline(), { host: h.fakeEl(), dir: "left" }); }, /inAt, outAt or both/);
});

test("phase: outgoing wipes out at T, incoming wipes in at T + 0.10", function () {
  var tl = h.fakeTimeline();
  Wp.phase(tl, { host: h.fakeEl() }, { host: h.fakeEl() }, 4, "left");
  var d = tl.drivers();
  assert.equal(d.length, 2);
  assert.equal(d[0].at, 4); assert.equal(d[1].at, 4.1);
});
