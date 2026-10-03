"use strict";
var test = require("node:test");
var assert = require("node:assert/strict");
var fs = require("node:fs");
var path = require("node:path");
var B = require("../brand.js");
var h = require("./helpers.js");

var DIR = path.resolve(__dirname, "..", "..", "brands", "contentporary");
var tokens = JSON.parse(fs.readFileSync(path.join(DIR, "tokens.json"), "utf8"));
function pal(n) { return JSON.parse(fs.readFileSync(path.join(DIR, "palettes", n + ".json"), "utf8")); }

test("varName: role paths -> kebab-case CSS variables", function () {
  assert.equal(B.varName("ground.deep"), "--hf-ground-deep");
  assert.equal(B.varName("surface.fillAlt"), "--hf-surface-fill-alt");
  assert.equal(B.varName("accentScript"), "--hf-accent-script");
  assert.equal(B.varName("extras.glowHalo"), "--hf-extras-glow-halo");
  assert.equal(B.rolePaths().length, 17);
});

test("cssVars: every role of every Contentporary palette, plus fonts and layout", function () {
  tokens.palettes.forEach(function (n) {
    var v = B.cssVars(tokens, pal(n));
    B.rolePaths().forEach(function (p) { assert.ok(B.isColour(v[B.varName(p)]), n + " " + p); });
  });
  var red = B.cssVars(tokens, pal("red"));
  assert.equal(red["--hf-accent-block"], "#F26666");
  assert.equal(red["--hf-text-primary"], "#F4F4F4");
  assert.equal(red["--hf-extras-glow-halo"], "#431D1D");
  assert.equal(red["--hf-font-headline"], '"Helvetica Now Display", system-ui, sans-serif');
  assert.equal(red["--hf-card-radius"], "36px");
});

test("cssVars: BRIEF font + override + scale", function () {
  var v = B.cssVars(tokens, pal("red"), { font: "geometric", overrides: { accentScript: "#BACE7A" }, scale: 2 });
  assert.equal(v["--hf-font-headline"], '"Satoshi", system-ui, sans-serif');
  assert.equal(v["--hf-accent-script"], "#BACE7A");
  assert.equal(v["--hf-card-radius"], "72px");
});

test("cssVars: bad choices throw and name the problem", function () {
  assert.throws(function () { B.cssVars(tokens, pal("red"), { font: "comic" }); }, /font "comic" not in brand contentporary \(have: helvetica, geometric\)/);
  assert.throws(function () { B.cssVars(tokens, pal("red"), { overrides: { "accent.blok": "#FFFFFF" } }); }, /override "accent.blok" is not a palette role/);
  assert.throws(function () { B.cssVars(tokens, pal("red"), { overrides: { accentScript: "lime" } }); }, /is not a colour: "lime"/);
  var broken = pal("red"); delete broken.status.x;
  assert.throws(function () { B.cssVars(tokens, broken); }, /red: missing status.x/);
  var other = pal("red"); other.name = "teal";
  assert.throws(function () { B.cssVars(tokens, other); }, /palette "teal" is not listed/);
});

test("toCss + apply", function () {
  var css = B.toCss({ "--hf-a": "#000000", "--hf-b": "1" });
  assert.equal(css, ":root {\n  --hf-a: #000000;\n  --hf-b: 1;\n}\n");
  var el = h.fakeEl("html"); B.apply(el, { "--hf-a": "#000000" });
  assert.equal(el.style["--hf-a"], "#000000");
});

test("toGl: brand colours -> WebGL clear colours", function () {
  assert.deepEqual(B.toGl("#FF0000"), [1, 0, 0, 1]);
  assert.deepEqual(B.toGl(" rgba(0, 0, 255, 0.5) "), [0, 0, 1, 0.5]);
  assert.throws(function () { B.toGl("var(--hf-ground-deep)"); }, /not a colour/);
});

test("cli: prints CSS, JSON, and fails with exit 1 + the reason", function () {
  var out = "", err = "";
  var io = { out: function (s) { out += s; }, err: function (s) { err += s; } };
  assert.equal(B.cli([DIR, "--palette", "reel-dark"], io), 0);
  assert.match(out, /--hf-text-primary: #FBFBFB;/);
  out = ""; assert.equal(B.cli([DIR, "--palette", "red", "--json"], io), 0);
  assert.equal(JSON.parse(out)["--hf-status-ok"], "#5C9064");
  assert.equal(B.cli([DIR, "--palette", "purple"], io), 1);
  assert.match(err, /palette "purple" has no file/);
  assert.equal(B.cli([DIR], io), 2);
});

test("mode: exposed from the palette, validated like brandcheck", function () {
  assert.deepEqual(B.MODES, ["dark", "light"]);
  assert.equal(B.mode(pal("red")), "dark");
  assert.equal(B.mode(pal("paper")), "light");
  assert.equal(B.mode(pal("silver")), "light");
  var noMode = pal("red"); delete noMode.mode;
  assert.throws(function () { B.cssVars(tokens, noMode); }, /red: missing mode/);
  assert.throws(function () { B.mode(noMode); }, /red: missing mode/);
  var bad = pal("red"); bad.mode = "sepia";
  assert.throws(function () { B.cssVars(tokens, bad); }, /red: mode must be 'dark' or 'light', got 'sepia'/);
  assert.throws(function () { B.mode(bad); }, /mode must be 'dark' or 'light', got 'sepia'/);
});

test("mode is not a role or a CSS variable", function () {
  assert.equal(B.rolePaths().indexOf("mode"), -1);
  var v = B.cssVars(tokens, pal("paper"));
  assert.equal(Object.keys(v).some(function (k) { return /mode/.test(k); }), false);
  assert.equal(JSON.parse(JSON.stringify(v))["--hf-mode"], undefined);
});

test("apply sets data-hf-mode on the root", function () {
  var el = h.fakeEl("html");
  B.apply(el, B.cssVars(tokens, pal("paper")));
  assert.equal(el.getAttribute("data-hf-mode"), "light");
  B.apply(el, B.cssVars(tokens, pal("red")));
  assert.equal(el.getAttribute("data-hf-mode"), "dark");
  var plain = h.fakeEl("html"); B.apply(plain, { "--hf-a": "#000000" });
  assert.equal(plain.getAttribute("data-hf-mode"), null);
});
