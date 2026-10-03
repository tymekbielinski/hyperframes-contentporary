"use strict";
var test = require("node:test");
var assert = require("node:assert/strict");
var h = require("./helpers.js");
var P = require("../profile.js");
var C = require("../camera.js");

global.document = h.fakeDocument();
global.console = Object.assign({}, console, { warn: function () {} });

var KEYS = [
  { t: 0, cx: 540, cy: 640, z: 1.2 }, { t: 1.5, cx: 540, cy: 640, z: 1.2 },
  { t: 2.1, cx: 540, cy: 1500, z: 1.2 }, { t: 4, cx: 540, cy: 1500, z: 1.25, ease: "ease.camera" }
];
var TIMES = [0, 0.4, 1.5, 1.6, 1.8, 2.0, 2.1, 2.5, 3.3, 4, 4.5];

test("track: holds between equal keys, eases on the profile curve, clamps outside", function () {
  var pose = C.track(KEYS, "shorts");
  assert.deepEqual(pose(-1), { cx: 540, cy: 640, z: 1.2 });
  assert.deepEqual(pose(1.0), { cx: 540, cy: 640, z: 1.2 });
  var f = P.ease("shorts", "ease.camera")((1.8 - 1.5) / (2.1 - 1.5));
  assert.ok(Math.abs(pose(1.8).cy - (640 + (1500 - 640) * f)) < 1e-9);
  assert.deepEqual(pose(9), { cx: 540, cy: 1500, z: 1.25 });
  assert.throws(function () { C.track([{ t: 0, cx: 0, cy: 0, z: 1, ease: "ease.glow" }], "shorts"); }, /not in the shorts ease table/);
  assert.throws(function () { C.track([], "shorts"); }, /at least one pose/);
});

test("glPose maps a design point to texture px PAD + p for any aspect", function () {
  [[1920, 1080], [1080, 1920], [704, 1080]].forEach(function (wh) {
    var W = wh[0], H = wh[1], K = 2.1, p = { cx: 300, cy: 900, z: 1.3 };
    var g = C.glPose(p, W, H, K), d = C.domTransform(p, W, H);
    var design = { x: 123, y: 456 };
    var sx = d.dx + d.z * design.x, sy = d.dy + d.z * design.y;          // where the DOM draws it
    var texX = (sx - g.tx) / g.s, texY = (sy - g.ty) / g.s;              // what the shader samples
    assert.ok(Math.abs(texX - ((K - 1) / 2 * W + design.x)) < 1e-9);
    assert.ok(Math.abs(texY - ((K - 1) / 2 * H + design.y)) < 1e-9);
  });
});

test("DOM-only rig (absorbed cameraLeg): stage transform is a pure function of t, any seek order", function () {
  var tl = h.fakeTimeline(), stage = h.fakeEl("div");
  C.rig(tl, { format: "shorts", width: 1080, height: 1920, stage: stage, keys: KEYS, dur: 4.5 });
  assert.equal(tl.drivers().length, 1);
  assert.deepEqual(h.seekOrderInvariant(tl, TIMES, [stage]), []);
  tl.seek(0);
  assert.equal(stage.style.transform, "translate(-108.00px,192.00px) scale(1.2000)");
});

test("rig requires an explicit frame size and format", function () {
  var tl = h.fakeTimeline();
  assert.throws(function () { C.rig(tl, { format: "shorts", stage: h.fakeEl(), keys: KEYS, dur: 1 }); }, /width and height are required/);
  assert.throws(function () { C.rig(tl, { width: 10, height: 10, stage: h.fakeEl(), keys: KEYS, dur: 1 }); }, /unknown format/);
});

test("blur legs: canvas shows only inside a leg, context released outside, any seek order", function () {
  var tl = h.fakeTimeline(), stage = h.fakeEl("div"), gl = h.fakeGl();
  var canvas = h.fakeCanvas(1080, 1920, gl), parent = h.fakeEl("div"); parent.appendChild(canvas);
  var baked = 0;
  C.rig(tl, { format: "shorts", width: 1080, height: 1920, stage: stage, keys: KEYS, dur: 4.5,
    canvas: canvas, legs: [[1.5, 2.1]], bake: function () { baked++; }, bg: [0, 0, 0, 1], K: 2.1 });
  tl.seek(1.8);
  var shown = parent.children[0];
  assert.equal(shown.style.visibility, "visible");
  tl.seek(3);
  assert.equal(parent.children[0].style.visibility, "hidden");
  assert.ok(gl.log.some(function (e) { return e[0] === "loseContext"; }), "context released after the leg");
  assert.equal(baked, 1, "static world baked once");
  assert.deepEqual(h.seekOrderInvariant(tl, TIMES, [stage, canvas, parent.children[0]]), []);
});

test("blur legs validate at build: bg, bake, and a kind the profile defines", function () {
  var base = { format: "shorts", width: 1080, height: 1920, stage: h.fakeEl(), keys: KEYS, dur: 4.5, canvas: h.fakeCanvas(1080, 1920, h.fakeGl()) };
  assert.throws(function () { C.rig(h.fakeTimeline(), Object.assign({}, base, { legs: [[1, 2]], bake: function () {} })); }, /bg is required/);
  assert.throws(function () { C.rig(h.fakeTimeline(), Object.assign({}, base, { legs: [[1, 2]], bg: null })); }, /bake/);
  assert.throws(function () { C.rig(h.fakeTimeline(), Object.assign({}, base, { legs: [{ from: 1, to: 2, kind: "whip" }], bg: null, bake: function () {} })); }, /shorts has no "whip"/);
});

test("context loss mid-render falls back to the DOM pose instead of throwing", function () {
  var tl = h.fakeTimeline(), stage = h.fakeEl("div");
  var canvas = h.fakeCanvas(1920, 1080, h.fakeGl({ lost: true })); h.fakeEl("div").appendChild(canvas);
  C.rig(tl, { format: "long-form", width: 1920, height: 1080, stage: stage, keys: [{ t: 0, cx: 960, cy: 540, z: 1 }, { t: 2, cx: 1500, cy: 540, z: 1 }],
    dur: 2, canvas: canvas, legs: [[0, 2]], bake: function () {}, bg: [0, 0, 0, 1] });
  tl.seek(1);
  assert.equal(canvas.style.visibility, "hidden");
  assert.match(stage.style.transform, /^translate\(/);
});

test("push: one driver for all segments, seek-order safe, rejects a second call and overlaps", function () {
  var tl = h.fakeTimeline(), el = h.fakeEl("div");
  var scaleAt = C.push(tl, el, [{ T: 5, dur: 1, from: 1.075, to: 1.105 }, { T: 1, dur: 2, from: 1, to: 1.1 }], { format: "long-form" });
  assert.equal(tl.drivers().length, 1);
  assert.equal(scaleAt(0), 1); assert.equal(scaleAt(4), 1.1); assert.equal(scaleAt(9), 1.105);
  assert.equal(scaleAt(2), 1 + 0.1 * P.ease("long-form", "ease.camera.slow")(0.5));
  assert.deepEqual(h.seekOrderInvariant(tl, [0, 1, 1.5, 2.9, 3.5, 5.2, 6, 7], [el]), []);
  assert.throws(function () { C.push(tl, el, [{ T: 8, dur: 1, from: 1, to: 1.1 }], { format: "long-form" }); }, /already has pushes/);
  assert.throws(function () { C.push(tl, h.fakeEl(), [{ T: 0, dur: 2, from: 1, to: 1.1 }, { T: 1, dur: 1, from: 1, to: 1.1 }], { format: "shorts" }); }, /overlap/);
});

test("context lost AFTER a successful render (mid-leg) falls back to the DOM pose", function () {
  var tl = h.fakeTimeline(), stage = h.fakeEl("div"), gl = h.fakeGl();
  var canvas = h.fakeCanvas(1080, 1920, gl), parent = h.fakeEl("div"); parent.appendChild(canvas);
  C.rig(tl, { format: "shorts", width: 1080, height: 1920, stage: stage, keys: KEYS, dur: 4.5,
    canvas: canvas, legs: [[1.5, 2.1]], bake: function () {}, bg: [0, 0, 0, 1], K: 2.1 });
  tl.seek(1.7);
  assert.equal(parent.children[0].style.visibility, "visible");
  gl.getExtension("WEBGL_lose_context").loseContext();      // context dies after the first good render
  tl.seek(1.9);
  assert.equal(parent.children[0].style.visibility, "hidden");
  assert.equal(parent.children[0].style.opacity, "0");
  assert.match(stage.style.transform, /^translate\(/);
  tl.seek(1.95);                                             // stays on the DOM pose, no throw
  assert.equal(parent.children[0].style.visibility, "hidden");
});

test("a second leg with a detached canvas falls back to the DOM instead of throwing", function () {
  var tl = h.fakeTimeline(), stage = h.fakeEl("div"), gl = h.fakeGl();
  var canvas = h.fakeCanvas(1080, 1920, gl), parent = h.fakeEl("div"); parent.appendChild(canvas);
  C.rig(tl, { format: "shorts", width: 1080, height: 1920, stage: stage, keys: KEYS, dur: 4.5,
    canvas: canvas, legs: [[0.5, 1], [2, 3]], bake: function () {}, bg: [0, 0, 0, 1], K: 2.1 });
  tl.seek(0.7); tl.seek(1.5);
  parent.children[0].parentNode = null;   // detach
  tl.seek(2.5);
  assert.match(stage.style.transform, /^translate\(/);
});
