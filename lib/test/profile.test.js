"use strict";
var test = require("node:test");
var assert = require("node:assert/strict");
var fs = require("node:fs");
var path = require("node:path");
var P = require("../profile.js");

var ROOT = path.resolve(__dirname, "..", "..");

// Pull `| \`ease.x\` | <cell> |` rows out of profile markdown; the value is the cell's first backticked
// string. A row whose value cell has no backticks fails with a message naming the file and token.
function parseEaseRows(text, label) {
  var out = {};
  text.split("\n").forEach(function (line) {
    var m = /^\| `(ease\.[a-z.]+)` \| ([^|]+)\|/.exec(line);
    if (!m) return;
    var v = /`([^`]+)`/.exec(m[2]);
    assert.ok(v, label + ": the value cell of " + m[1] + " must contain a backticked spec, got: " + m[2].trim());
    out[m[1]] = v[1];
  });
  return out;
}
function tableEases(file) {
  return parseEaseRows(fs.readFileSync(path.join(ROOT, "standards", "formats", file), "utf8"), file);
}

test("ease-row parser fails clearly on a value cell without backticks", function () {
  assert.deepEqual(parseEaseRows("| `ease.enter` | `power3.out` |", "x.md"), { "ease.enter": "power3.out" });
  assert.throws(function () { parseEaseRows("| `ease.enter` | power3.out |", "x.md"); },
    /x\.md: the value cell of ease\.enter must contain a backticked spec, got: power3\.out/);
});

test("ease tables match the profile markdown exactly (no drift)", function () {
  [["long-form", "long-form.md"], ["shorts", "shorts.md"]].forEach(function (pair) {
    var md = tableEases(pair[1]);
    assert.deepEqual(P.tokens(pair[0]).sort(), Object.keys(md).sort(), pair[1] + " token set");
    Object.keys(md).forEach(function (tok) {
      var want = md[tok].indexOf("ease.") === 0 ? P.easeSpec(pair[0], md[tok]) : md[tok];
      assert.equal(P.easeSpec(pair[0], tok), want, pair[1] + " " + tok);
    });
  });
});

test("bezier solver: endpoints, monotonic, deterministic", function () {
  var e = P.bezier(0.65, 0, 0.35, 1);
  assert.equal(e(0), 0); assert.equal(e(1), 1); assert.equal(e(-1), 0); assert.equal(e(2), 1);
  assert.ok(Math.abs(e(0.5) - 0.5) < 1e-6, "symmetric curve passes through the middle");
  var prev = 0;
  for (var i = 1; i <= 100; i++) { var v = e(i / 100); assert.ok(v >= prev); prev = v; }
  assert.equal(e(0.3), P.bezier(0.65, 0, 0.35, 1)(0.3));
});

test("named eases follow GSAP's numbering (power3 = quartic)", function () {
  assert.equal(P.compile("power3.out")(0.5), 0.9375);
  assert.equal(P.compile("power2.out")(0.5), 0.875);
  assert.ok(Math.abs(P.compile("sine.inOut")(0.5) - 0.5) < 1e-12);
  assert.equal(P.compile("expo.out")(1), 1);
});

test("long-form ease.camera peaks early (~28 % into the move)", function () {
  var e = P.ease("long-form", "ease.camera"), best = 0, at = 0;
  for (var i = 1; i < 1000; i++) { var v = (e((i + 1) / 1000) - e((i - 1) / 1000)); if (v > best) { best = v; at = i / 1000; } }
  assert.ok(at > 0.2 && at < 0.36, "peak velocity at " + at);
});

test("closed vocabulary: unknown token or format throws, naming both", function () {
  assert.throws(function () { P.ease("shorts", "ease.glow"); }, /"ease.glow" is not in the shorts ease table/);
  assert.throws(function () { P.ease("tiktok", "ease.camera"); }, /unknown format "tiktok"/);
  assert.throws(function () { P.compile("back.out(1.7)"); }, /cannot compile/);
});

test("aliases resolve and eases are cached + tagged", function () {
  assert.equal(P.easeSpec("long-form", "ease.cut"), "cubic-bezier(0.32, 0, 0.18, 1)");
  var a = P.ease("long-form", "ease.enter");
  assert.equal(a, P.ease("long-form", "ease.enter"));
  assert.ok(P.isProfileEase(a));
  assert.ok(!P.isProfileEase(function (p) { return p; }));
});

test("timing() returns a copy callers cannot mutate", function () {
  var t = P.timing("shorts"); t.swap = 99;
  assert.equal(P.timing("shorts").swap, 0.133);
  assert.equal(P.timing("shorts").wipe.inDur, 0.42);
  assert.equal(P.timing("shorts").wipe.handoff, 0.10);
  assert.equal(P.timing("long-form").glow.nextWord, 0.43);
});

test("claimTransform: one inline-transform owner per element, named in the error", function () {
  var el = {};
  assert.equal(P.claimTransform(el, "HFCamera.push"), el);
  assert.doesNotThrow(function () { P.claimTransform(el, "HFCamera.push"); }, "the same owner may claim again");
  assert.throws(function () { P.claimTransform(el, "HFMarks.highlight"); },
    /HFMarks\.highlight would overwrite the inline transform that HFCamera\.push animates on this element/);
  assert.throws(function () { P.claimTransform(null, "HFText.words"); }, /HFText\.words got no element/);
});

test("kit timings: card entrance, chain gap, roadmap nodes, CTA (long-form only)", function () {
  var T = P.timing("long-form");
  assert.deepEqual(T.card, { dur: 0.43, riseFrac: 37.5 / 720 });
  assert.equal(T.chainGap, 0.475);
  assert.deepEqual(T.node, { dur: 0.48, gap: 0.48 });
  assert.deepEqual(T.cta, { scale: 0.8, scaleDur: 0.5, dive: 2, diveDur: 0.6, hold: 1.7 });
  assert.equal(P.timing("shorts").card, undefined);
});
