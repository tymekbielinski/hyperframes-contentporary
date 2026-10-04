"use strict";
// Fixtures for tools/lawscan.js — run by tools/test_lib_node.py with the lib/ node suite.
var test = require("node:test");
var assert = require("node:assert/strict");
var L = require("./lawscan.js");

function hits(src) { return L.scan("x.js", src, { ruleset: "lib" }).length; }
function comp(src, format, rel) { return L.scan(rel || "c.html", src, { ruleset: "composition", format: format || "long-form" }); }

test("lib ruleset: catches what its messages claim (fixtures carried from hygiene.test.js)", function () {
  ["a = '#fff';", "a = '#FFFA';", "a = '#12345678';", "a = 'rgba(1,2,3,1)';", "a = 'RGB(1,2,3)';", "a = 'hsl(1,2%,3%)';", "a = 'oklch(1 0 0)';", "a = 'hwb(1 2% 3%)';"]
    .forEach(function (s) { assert.equal(hits(s), 1, s); });
  assert.equal(hits("a = 'rgba(0,0,0,0)'; /* hf-allow: alpha-mask */"), 0);
  assert.equal(hits("a = '#000'; // plain"), 1);
  assert.equal(hits("a = 'rgba(0,0,0,0)'; /* hf-allow: alpha-mask */\nb = '#fff';"), 1);
  assert.equal(hits("a = 'url(#glow-x)'; id = '#glow-x';"), 0);
  ["{ ease: 'back.out(1.7)' }", "{ ease: \"power2.out\" }", "x = Elastic.easeOut", "x = 'bounce.inOut'", "x = Back.easeIn", "{ repeat: Infinity }", "{ repeat: -1 }"]
    .forEach(function (s) { assert.ok(hits(s) >= 1, s); });
  assert.equal(hits("{ ease: 'none' }"), 0);
  assert.equal(hits("{ ease: \"none\" }"), 0);
  assert.equal(hits("// back.out is forbidden\n/* repeat: -1 */"), 0);
  var tagged = "el.setAttribute('data-blur-reason','focus'); el.style.filter = 'blur(2px)';";
  assert.equal(hits(tagged), 0);
  assert.equal(hits(tagged + "\n\n\n\n\nel.style.filter = 'blur(9px)';"), 1);
  assert.equal(hits("a = '<feGaussianBlur in=\"x\"/>';"), 1);
  assert.equal(hits("a = '<feGaussianBlur data-blur-reason=\"glow\"/>';"), 0);
  assert.equal(hits("s.backdropFilter = 'x'; css = 'backdrop-filter: blur(4px)';"), 3);
  assert.equal(hits("a = '#ff0000'; /* hf-allow: alpha-mask */"), 1);
  assert.equal(hits("a = '#000 #f00'; /* hf-allow: alpha-mask */"), 1);
  assert.equal(hits("a = 'rgba(0, 0, 0, .4)'; /* hf-allow: alpha-mask */"), 0);
  assert.equal(hits("a = 'rgb( 0 , 0 , 0 ) #00000000 #0000 #000000'; /* hf-allow: alpha-mask */"), 0);
  assert.equal(hits("a = 'rgba(0,0,0,0)'; b = 'rgba(1,0,0,1)'; /* hf-allow: alpha-mask */"), 1);
  assert.equal(hits("a = '#000 /* hf-allow: alpha-mask */';"), 1);
  assert.equal(hits("a = /\"/g; b = '#fff';"), 1);
  assert.equal(hits("a = 'blur(1px)'; b = 'blur(2px)'; x.setAttribute('data-blur-reason','focus');"), 1);
  assert.equal(hits("x.setAttribute('data-blur-reason','focus');\na = 'blur(1px)';"), 0);
  assert.equal(hits("x.setAttribute('data-blur-reason','focus');\na = 'blur(1px)';\nb = 'blur(2px)';"), 1);
  assert.equal(hits("t(x, 'data-blur-reason');\na = 'blur(1px)';\n\nb = 'blur(2px)';"), 1);
  assert.equal(hits("a = 'blur(1px)';\nx.setAttribute('data-blur-reason','focus');"), 1);
  assert.equal(hits("el.style.backdropFilter = 'x';"), 1);
  assert.equal(L.format(L.scan("x.js", "\n\nb = 'blur(1px)';")[0]).indexOf("x.js:3:"), 0);
});

test("known gaps from the Plan 2 review are closed", function () {
  // quoted keys and template-literal eases
  assert.equal(hits("{ ease: `power2.out` }"), 1);
  assert.equal(hits("{ \"ease\": \"power2.out\" }"), 1);
  assert.equal(hits("{ 'repeat': -1 }"), 1);
  // modern colour functions
  ["a = 'color-mix(in srgb, red, blue)';", "a = 'lab(50% 40 59)';", "a = 'lch(52% 72 50)';", "a = 'oklab(0.5 0.1 0.1)';"]
    .forEach(function (s) { assert.equal(hits(s), 1, s); });
  assert.equal(hits("label(x); vocab(y);"), 0);
  // url(#id) and DOM .blur() are not colours / Gaussians
  assert.equal(hits("f.style.filter = 'url(#fade)'; g = 'url(#beef)';"), 0);
  assert.equal(hits("input.blur(); el.blur();"), 0);
  // a regex literal after `return` (and other keywords) is not division: the quote inside is not a string
  assert.equal(hits("function f(){ return /\"/g; } // back.out is banned"), 0);
  assert.equal(hits("x = typeof /'/; // repeat: -1"), 0);
});

test("composition ruleset: HTML prose is masked, line numbers survive", function () {
  assert.deepEqual(comp("<p>it's a \"test\"</p><script>var t = Date.now();</script>").map(function (f) { return [f.line, f.check]; }), [[1, 4]]);
  assert.deepEqual(comp("<p>don't</p>\n<script>\nvar x = 1;\n</script>\n<style>.a{animation: spin 2s infinite linear}</style>").map(function (f) { return [f.line, f.check]; }), [[5, 4]]);
  assert.deepEqual(comp("<!-- Math.random() is banned -->\n<style>.a { color: #fff }</style>"), []);
  assert.equal(comp("\n\n<script>Math.random()</script>")[0].line, 3);
  assert.deepEqual(comp("<script>tl.to(el, { x: 10, ease: \"power2.out\" });</script>").map(function (f) { return f.check; }), [6]);
  assert.deepEqual(comp("<style>.a { transition: transform 1s cubic-bezier(0.2, 0, 0, 1) }</style>").map(function (f) { return f.check; }), [6]);
});

test("composition ruleset: blur reasons are checked per format", function () {
  assert.deepEqual(comp("<filter><feGaussianBlur stdDeviation=\"4\"/></filter>").map(function (f) { return f.check; }), [5]);
  assert.deepEqual(comp("<feGaussianBlur data-blur-reason=\"glow\" stdDeviation=\"4\"/>"), []);
  assert.deepEqual(comp("<feGaussianBlur\n  data-blur-reason=\"focus\" stdDeviation=\"4\"/>"), [], "tag on the next line of a multi-line SVG tag");
  assert.deepEqual(comp("<div style=\"filter: blur(4px)\" data-blur-reason=\"focus\"></div>"), []);
  var lf = comp("<feGaussianBlur data-blur-reason=\"wipe\" stdDeviation=\"14 0\"/>", "long-form").map(function (f) { return f.message; });
  assert.equal(lf.length, 2);
  assert.match(lf[0], /"wipe" is Shorts-only/);
  assert.match(lf[1], /directional Gaussian/);
  assert.deepEqual(comp("<feGaussianBlur data-blur-reason=\"wipe\" stdDeviation=\"14 0\"/>", "shorts"), []);
  assert.match(comp("<feGaussianBlur data-blur-reason=\"smear\" stdDeviation=\"3\"/>")[0].message, /"smear" is not focus, glow or wipe/);
  assert.match(comp("<script>fe.setAttribute(\"data-blur-reason\", \"haze\"); fe.setAttribute('stdDeviation', 3);</script>")[0].message, /"haze"/);
  assert.deepEqual(comp("<style>.a{color:#fff;background:rgba(1,2,3,1)}</style>"), [], "colours are a lib rule, not a QA check");
  assert.throws(function () { comp("<p></p>", "tiktok"); }, /format must be long-form or shorts/);
});

test("cli: JSON out, exit 1 on findings, 2 on bad usage", function () {
  var fs = require("fs"), os = require("os"), path = require("path");
  var dir = fs.mkdtempSync(path.join(os.tmpdir(), "lawscan-")), f = path.join(dir, "a.html");
  fs.writeFileSync(f, "<script>Math.random()</script>");
  var out = "", err = "";
  var io = { out: function (s) { out += s; }, err: function (s) { err += s; } };
  assert.equal(L.cli(["--ruleset", "composition", "--format", "shorts", f], io), 1);
  assert.equal(JSON.parse(out)[0].check, 4);
  assert.equal(L.cli([], io), 2);
  assert.match(err, /usage/);
  fs.rmSync(dir, { recursive: true });
});
