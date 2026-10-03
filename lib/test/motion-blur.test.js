"use strict";
var test = require("node:test");
var assert = require("node:assert/strict");
var MB = require("../motion-blur.js");
var h = require("./helpers.js");

function pan(t) { return { tx: -400 * t, ty: 0, s: 1 }; }   // 400 px/s pan

function make(opts) {
  opts = opts || {};
  var gl = h.fakeGl(opts.gl);
  var canvas = h.fakeCanvas(opts.w == null ? 1080 : opts.w, opts.h == null ? 1920 : opts.h, gl);
  var cfg = Object.assign({ canvas: canvas, world: { width: 3000, height: 1600 }, camera: { T: pan }, fps: 30,
    preset: MB.profilePreset("shorts", "leg"), bg: [0, 0, 0, 1] }, opts.cfg || {});
  return { gl: gl, canvas: canvas, blur: MB.createCameraBlur(cfg) };
}
function uniform(log, name) { var hits = log.filter(function (e) { return e[0] === name; }); return hits[hits.length - 1]; }

test("render(t) is a pure function of t: same calls, same sample count", function () {
  var m = make(), start = m.gl.log.length;
  var n1 = m.blur.render(0.5), first = m.gl.log.slice(start);
  var mid = m.gl.log.length; m.blur.render(0.9);
  var again = m.gl.log.length; var n2 = m.blur.render(0.5);
  assert.equal(n1, n2);
  assert.deepEqual(m.gl.log.slice(again), first);
});

test("aspect-agnostic: a 1080x1920 canvas over a 3000x1600 texture uses both sizes as given", function () {
  var m = make(); m.blur.render(0.2);
  assert.deepEqual(uniform(m.gl.log, "uRes"), ["uRes", 1080, 1920]);
  assert.deepEqual(uniform(m.gl.log, "uWorld"), ["uWorld", 3000, 1600]);
  assert.deepEqual(m.blur.size(), { width: 1080, height: 1920, worldWidth: 3000, worldHeight: 1600 });
});

test("worldSize pins world units regardless of texture size", function () {
  var m = make({ cfg: { worldSize: [1080, 1920] } }); m.blur.render(0.2);
  assert.deepEqual(uniform(m.gl.log, "uWorld"), ["uWorld", 1080, 1920]);
});

test("no hard-coded 1920x1080: an unsized canvas without res throws", function () {
  assert.throws(function () { make({ w: 0, h: 0 }); }, /canvas has no size/);
  var m = make({ w: 0, h: 0, cfg: { res: [704, 1080] } });
  assert.equal(m.canvas.width, 704); assert.equal(m.canvas.height, 1080);
});

test("WebGL context loss surfaces as a clear error, and dispose() loses the context", function () {
  assert.throws(function () { make({ gl: { lost: true } }); }, /could not create a WebGL context/);
  assert.throws(function () { make({ gl: { nullShader: true } }); }, /context lost/);
  var m = make(); m.blur.dispose();
  assert.deepEqual(m.gl.log[m.gl.log.length - 1], ["loseContext"]);
});

test("a still camera uses one sample; a fast pan uses more, capped at maxN", function () {
  var still = make({ cfg: { camera: { T: function () { return { tx: 0, ty: 0, s: 1 }; } } } });
  assert.equal(still.blur.render(1), 1);
  var fast = make({ cfg: { camera: { T: function (t) { return { tx: -1e6 * t, ty: 0, s: 1 }; } } } });
  assert.equal(fast.blur.render(1), MB.profilePreset("shorts", "leg").maxN);
});

test("sampleCount checks all four corners of the rect", function () {
  // zoom about the top-left: the far corner moves fastest
  var n = MB.sampleCount({ tx: 0, ty: 0, s: 1 }, { tx: 0, ty: 0, s: 1 }, 0, 0, 1000, 10, 0.5 / 30, 1, 999);
  assert.equal(n, Math.ceil(Math.hypot(1000, 10) * 0.5 / 30));
});

test("renderRegions scissors each region (GL y flipped) with its own velocity", function () {
  var m = make({ w: 200, h: 100 }), start = m.gl.log.length;
  var N = m.blur.renderRegions(0.5, [
    { x: 0, y: 0, w: 50, h: 40, T: function () { return { tx: 0, ty: 0, s: 1 }; } },
    { x: 50, y: 0, w: 50, h: 40, T: function (t) { return { tx: 0, ty: -900 * t, s: 1 }; } }
  ]);
  var calls = m.gl.log.slice(start);
  assert.deepEqual(calls.filter(function (e) { return e[0] === "scissor"; }), [["scissor", 0, 60, 50, 40], ["scissor", 50, 60, 50, 40]]);
  assert.ok(N > 1);
  assert.equal(calls.filter(function (e) { return e[0] === "uWorld"; }).length, 2);
});

test("no camera = identity pose", function () {
  var m = make({ cfg: { camera: null } });
  assert.equal(m.blur.render(3), 1);
  assert.deepEqual(m.blur.motionVector(3), { tx: 0, ty: 0, s: 0, rot: 0 });
});

test("profile presets match the profiles: long-form legs <= 90°, whips 180°, Shorts have no whip", function () {
  assert.ok(MB.profilePreset("long-form", "leg").angle <= 90);
  assert.equal(MB.profilePreset("long-form", "whip").angle, 180);
  assert.equal(MB.profilePreset("shorts", "roll").angle, 144);
  assert.throws(function () { MB.profilePreset("shorts", "whip"); }, /shorts has no "whip" blur/);
  assert.throws(function () { MB.profilePreset("vlog", "leg"); }, /unknown format/);
  Object.keys(MB.PRESETS).forEach(function (k) { assert.ok(!("ease" in MB.PRESETS[k]), k + " must not recommend an ease"); });
});

test("sample count never exceeds the shader's 128-iteration cap, even when maxN asks for more", function () {
  assert.equal(MB.MAX_SAMPLES, 128);
  assert.ok(MB.sampleCount({ tx: 0, ty: 0, s: 1 }, { tx: 1e7, ty: 0, s: 0 }, 0, 0, 100, 100, 0.03, 1, 500) <= 128);
  var fast = make({ cfg: { maxN: 400, camera: { T: function (t) { return { tx: -1e7 * t, ty: 0, s: 1 }; } } } });
  var n = fast.blur.render(1);
  assert.equal(n, 128);
  assert.deepEqual(uniform(fast.gl.log, "uN"), ["uN", 128]);
});
