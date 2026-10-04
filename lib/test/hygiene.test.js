"use strict";
// Static scan of every shared module: the core motion law, enforced on the library itself.
// The scanner lives in tools/lawscan.js (shared with the QA gate); its fixtures are tools/lawscan.test.js.
var test = require("node:test");
var assert = require("node:assert/strict");
var fs = require("node:fs");
var path = require("node:path");
var lawscan = require("../../tools/lawscan.js");

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

test("no module breaks the motion law", function () {
  var problems = [];
  modules().forEach(function (rel) {
    problems = problems.concat(lawscan.scan(rel, fs.readFileSync(path.join(LIB, rel), "utf8"), { ruleset: "lib" }).map(lawscan.format));
  });
  assert.deepEqual(problems, []);
});
