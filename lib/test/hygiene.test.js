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

var RULES = [
  [/Math\.random|Date\.now|performance\.now/, "non-deterministic clock/randomness (core law 1)"],
  [/repeat\s*:\s*-1/, "infinite repeat (core law 1)"],
  [/#[0-9A-Fa-f]{6}\b/, "hard-coded colour — use brand CSS variables"],
  [/\b(back|elastic|bounce)\.(in|out|inOut)\b/, "overshoot ease (core law 3)"],
  [/ease\s*:\s*"(?!none")/, "string ease other than the driver's \"none\" — use HFProfile.ease (core law 4)"]
];

test("no module breaks the motion law", function () {
  var problems = [];
  modules().forEach(function (rel) {
    var raw = fs.readFileSync(path.join(LIB, rel), "utf8");
    var src = raw.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");   // comments may name what they forbid
    RULES.forEach(function (r) { if (r[0].test(src)) problems.push(rel + ": " + r[1]); });
    if (rel !== "profile.js" && /cubic-bezier\(/.test(src)) problems.push(rel + ": raw cubic-bezier outside profile.js");
    if (/[^A-Za-z]blur\(|<feGaussianBlur/.test(src) && src.indexOf("data-blur-reason") === -1) problems.push(rel + ": creates a Gaussian without data-blur-reason");
  });
  assert.deepEqual(problems, []);
});
