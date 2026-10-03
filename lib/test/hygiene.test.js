"use strict";
// Static scan of every shared module: the core motion law, enforced on the library itself.
var test = require("node:test");
var assert = require("node:assert/strict");
var fs = require("node:fs");
var path = require("node:path");

var LIB = path.resolve(__dirname, "..");
var EXPECTED = ["brand.js", "camera.js", "marks.js", "motion-blur.js", "profile.js", "shorts/wipe.js", "text.js"];

function modules() {
  var out = [];
  (function walk(dir) {
    fs.readdirSync(dir, { withFileTypes: true }).forEach(function (d) {
      var p = path.join(dir, d.name);
      if (d.isDirectory()) { if (d.name !== "test" && d.name !== "examples") walk(p); }
      else if (d.name.endsWith(".js")) out.push(path.relative(LIB, p).split(path.sep).join("/"));
    });
  })(LIB);
  return out.sort();
}

test("lib/ holds exactly the Plan 2 modules (retired files stay retired)", function () {
  assert.deepEqual(modules(), EXPECTED);
});

var ALLOW = /\/\*\s*hf-allow:\s*alpha-mask\s*\*\//;
var RULES = [
  [/Math\.random|Date\.now|performance\.now/, "non-deterministic clock/randomness (core law 1)"],
  [/repeat\s*:\s*(-1|Infinity)/, "infinite repeat (core law 1)"],
  [/#(?:[0-9a-f]{3,4}|[0-9a-f]{6}|[0-9a-f]{8})(?![0-9a-z])/i, "hard-coded colour — use brand CSS variables"],
  [/\b(rgba?|hsla?|oklch|hwb)\(/i, "hard-coded colour function — use brand CSS variables"],
  [/\b(back|elastic|bounce)\.(in|out|inout|ease\w*)/i, "overshoot ease (core law 3)"],
  [/ease\s*:\s*["'](?!none["'])/, "string ease other than the driver's \"none\" — use HFProfile.ease (core law 4)"]
];

// Blank comments but keep line structure, so findings carry real line numbers.
function stripComments(raw) {
  return raw.replace(/\/\*[\s\S]*?\*\//g, function (m) { return m.replace(/[^\n]/g, " "); }).replace(/^[ \t]*\/\/.*$/gm, "");
}

// Returns "rel:line: message" for every violation in a module's source.
function scan(rel, raw) {
  var out = [], rawLines = raw.split("\n"), lines = stripComments(raw).split("\n");
  lines.forEach(function (line, i) {
    var allowed = ALLOW.test(rawLines[i]);
    RULES.forEach(function (r) {
      var isColour = /colour/.test(r[1]);
      if (r[0].test(line) && !(isColour && allowed)) out.push(rel + ":" + (i + 1) + ": " + r[1]);
    });
    if (rel !== "profile.js" && /cubic-bezier\(/.test(line)) out.push(rel + ":" + (i + 1) + ": raw cubic-bezier outside profile.js");
    if (/(^|[^A-Za-z])blur\(|<feGaussianBlur|backdrop-filter/.test(line)) {
      var tagged = false;
      for (var k = Math.max(0, i - 3); k <= Math.min(lines.length - 1, i + 3); k++) if (/data-blur-reason/.test(lines[k])) tagged = true;
      if (!tagged) out.push(rel + ":" + (i + 1) + ": Gaussian site without data-blur-reason within 3 lines");
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
  assert.equal(hits("s.backdropFilter = 'x'; css = 'backdrop-filter: blur(4px)';"), 1);
  assert.match(scan("x.js", "\n\nb = 'blur(1px)';")[0], /^x\.js:3:/);
});
