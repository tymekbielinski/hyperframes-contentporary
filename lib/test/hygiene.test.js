"use strict";
// Static scan of every shared module: the core motion law, enforced on the library itself.
var test = require("node:test");
var assert = require("node:assert/strict");
var fs = require("node:fs");
var path = require("node:path");

var LIB = path.resolve(__dirname, "..");
// The one machine-readable list of runtime modules — also what tools/sync_lib.py copies and locks.
var EXPECTED = require("../manifest.json").modules.slice().sort();

function modules() {
  var out = [];
  (function walk(dir) {
    fs.readdirSync(dir, { withFileTypes: true }).forEach(function (d) {
      var p = path.join(dir, d.name);
      if (d.isDirectory()) { if (d.name !== "test" && d.name !== "examples") walk(p); }
      else if (/\.[cm]?js$/.test(d.name)) out.push(path.relative(LIB, p).split(path.sep).join("/"));
    });
  })(LIB);
  return out.sort();
}

test("lib/ holds exactly the manifest modules (retired files stay retired)", function () {
  assert.deepEqual(modules(), EXPECTED);
});

var MARKER = /^\/\*\s*hf-allow:\s*alpha-mask\s*\*\/$/;
var RULES = [
  [/Math\.random|Date\.now|performance\.now/, "non-deterministic clock/randomness (core law 1)"],
  [/repeat\s*:\s*(-1|Infinity)/, "infinite repeat (core law 1)"],
  [/#(?:[0-9a-f]{3,4}|[0-9a-f]{6}|[0-9a-f]{8})(?![0-9a-z])/i, "hard-coded colour — use brand CSS variables"],
  [/\b(rgba?|hsla?|oklch|hwb)\(/i, "hard-coded colour function — use brand CSS variables"],
  [/\b(back|elastic|bounce)\.(in|out|inout|ease\w*)/i, "overshoot ease (core law 3)"],
  [/ease\s*:\s*["'](?!none["'])/, "string ease other than the driver's \"none\" — use HFProfile.ease (core law 4)"]
];
// Only pure black is excusable on an alpha-mask line: #000 #0000 #000000 #00000000, rgb(0,0,0), rgba(0,0,0,<alpha>).
var BLACK = /#(?:0{3,4}|0{6}|0{8})(?![0-9a-z])|\brgba?\(\s*0\s*,\s*0\s*,\s*0\s*(?:,\s*[0-9.]+\s*)?\)/gi;

// Walk the source tracking string state, so `/*` inside a string is not a comment.
// Returns the source with comments blanked (newlines kept) and the line numbers (0-based) of real alpha-mask markers.
function lex(raw) {
  var out = "", marks = {}, i = 0, n = raw.length, q = null, line = 0;
  while (i < n) {
    var c = raw[i], d = raw[i + 1];
    if (q) {
      out += c; if (c === "\n") line++;
      if (c === "\\") { out += d || ""; if (d === "\n") line++; i += 2; continue; }
      if (c === q) q = null;
      i++; continue;
    }
    if (c === "'" || c === '"' || c === "`") { q = c; out += c; i++; continue; }
    if (c === "/" && d === "*") {
      var end = raw.indexOf("*/", i + 2); end = end === -1 ? n : end + 2;
      var text = raw.slice(i, end);
      if (MARKER.test(text)) marks[line] = true;
      out += text.replace(/[^\n]/g, " "); line += (text.match(/\n/g) || []).length; i = end; continue;
    }
    if (c === "/" && d === "/") { while (i < n && raw[i] !== "\n") { out += " "; i++; } continue; }
    if (c === "/" && /[(,=:\[!&|?{};]\s*$|^\s*$/.test(out.slice(-40))) {   // regex literal: skip it so a quote inside is not a string
      var j = i + 1, cls = false;
      while (j < n && raw[j] !== "\n" && (cls || raw[j] !== "/")) { if (raw[j] === "\\") j++; else if (raw[j] === "[") cls = true; else if (raw[j] === "]") cls = false; j++; }
      out += raw.slice(i, j + 1); i = j + 1; continue;
    }
    out += c; if (c === "\n") line++;
    i++;
  }
  return { src: out, marks: marks };
}

// Returns "rel:line: message" for every violation in a module's source.
function scan(rel, raw) {
  var out = [], lx = lex(raw), lines = lx.src.split("\n"), tagUsed = {};
  lines.forEach(function (line, i) {
    RULES.forEach(function (r) {
      var isColour = /colour/.test(r[1]), l = isColour && lx.marks[i] ? line.replace(BLACK, "") : line;
      if (r[0].test(l)) out.push(rel + ":" + (i + 1) + ": " + r[1]);
    });
    if (rel !== "profile.js" && /cubic-bezier\(/.test(line)) out.push(rel + ":" + (i + 1) + ": raw cubic-bezier outside profile.js");
    // Gaussian sites: each needs its own data-blur-reason, on the same line or the line just before; a tag serves one site.
    var sites = (line.match(/(^|[^A-Za-z])blur\(|<feGaussianBlur|backdrop-filter|backdropFilter/g) || []).length;
    for (var s = 0; s < sites; s++) {
      var here = (line.match(/data-blur-reason/g) || []).length - (tagUsed[i] || 0);
      var prev = i > 0 ? (lines[i - 1].match(/data-blur-reason/g) || []).length - (tagUsed[i - 1] || 0) : 0;
      if (prev > 0) tagUsed[i - 1] = (tagUsed[i - 1] || 0) + 1;
      else if (here > 0) tagUsed[i] = (tagUsed[i] || 0) + 1;
      else out.push(rel + ":" + (i + 1) + ": Gaussian site without its own data-blur-reason (same line or line before)");
    }
  });
  return out;
}

test("no module breaks the motion law", function () {
  var problems = [];
  modules().forEach(function (rel) { problems = problems.concat(scan(rel, fs.readFileSync(path.join(LIB, rel), "utf8"))); });
  assert.deepEqual(problems, []);
});

test("scanner catches what its messages claim (fixtures)", function () {
  function hits(src) { return scan("x.js", src).length; }
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
  // per-site Gaussian rule: a tag excuses only its own neighbourhood
  var tagged = "el.setAttribute('data-blur-reason','focus'); el.style.filter = 'blur(2px)';";
  assert.equal(hits(tagged), 0);
  assert.equal(hits(tagged + "\n\n\n\n\nel.style.filter = 'blur(9px)';"), 1);
  assert.equal(hits("a = '<feGaussianBlur in=\"x\"/>';"), 1);
  assert.equal(hits("a = '<feGaussianBlur data-blur-reason=\"glow\"/>';"), 0);
  assert.equal(hits("s.backdropFilter = 'x'; css = 'backdrop-filter: blur(4px)';"), 3);
  // allow-marker: black alpha only, and only as a real comment
  assert.equal(hits("a = '#ff0000'; /* hf-allow: alpha-mask */"), 1);
  assert.equal(hits("a = '#000 #f00'; /* hf-allow: alpha-mask */"), 1);
  assert.equal(hits("a = 'rgba(0, 0, 0, .4)'; /* hf-allow: alpha-mask */"), 0);
  assert.equal(hits("a = 'rgb( 0 , 0 , 0 ) #00000000 #0000 #000000'; /* hf-allow: alpha-mask */"), 0);
  assert.equal(hits("a = 'rgba(0,0,0,0)'; b = 'rgba(1,0,0,1)'; /* hf-allow: alpha-mask */"), 1);
  assert.equal(hits("a = '#000 /* hf-allow: alpha-mask */';"), 1);
  assert.equal(hits("a = /\"/g; b = '#fff';"), 1);
  // one tag serves one Gaussian site
  assert.equal(hits("a = 'blur(1px)'; b = 'blur(2px)'; x.setAttribute('data-blur-reason','focus');"), 1);
  assert.equal(hits("x.setAttribute('data-blur-reason','focus');\na = 'blur(1px)';"), 0);
  assert.equal(hits("x.setAttribute('data-blur-reason','focus');\na = 'blur(1px)';\nb = 'blur(2px)';"), 1);
  assert.equal(hits("t(x, 'data-blur-reason');\na = 'blur(1px)';\n\nb = 'blur(2px)';"), 1);
  assert.equal(hits("a = 'blur(1px)';\nx.setAttribute('data-blur-reason','focus');"), 1);
  assert.equal(hits("el.style.backdropFilter = 'x';"), 1);
  assert.match(scan("x.js", "\n\nb = 'blur(1px)';")[0], /^x\.js:3:/);
});
