"use strict";
// Drift guards: HFProfile TIMING and HFMotionBlur PROFILE_PRESETS must say what the profile markdown says.
// When a profile value changes, change lib/ in the same commit — these tests name the value that drifted.
var test = require("node:test");
var assert = require("node:assert/strict");
var fs = require("node:fs");
var path = require("node:path");
var P = require("../profile.js");
var MB = require("../motion-blur.js");

var ROOT = path.resolve(__dirname, "..", "..");
var FILES = {
  "long-form.md": path.join(ROOT, "standards", "formats", "long-form.md"),
  "shorts.md": path.join(ROOT, "standards", "formats", "shorts.md"),
  "spec": path.join(ROOT, "docs", "superpowers", "specs", "2026-10-03-animation-workflow-design.md")
};
var cache = {};
function text(file) { return cache[file] || (cache[file] = fs.readFileSync(FILES[file], "utf8")); }

// The numbers captured by `re` in `file`; fails naming the pattern when the markdown no longer matches.
function nums(file, re) {
  var m = re.exec(text(file));
  assert.ok(m, file + " no longer matches " + re + " — update the profile and lib/ together");
  return m.slice(1).map(parseFloat);
}
function num(file, re) { return nums(file, re)[0]; }
function close(lib, md, what) { assert.ok(Math.abs(lib - md) < 1e-9, what + ": lib " + lib + " vs markdown " + md); }

test("long-form TIMING matches long-form.md (and the spec appendix for the script rate)", function () {
  var T = P.timing("long-form");
  close(T.words.dur, num("long-form.md", /\| word entrance \|[^|\n]*?, ([\d.]+) s `ease\.enter`/), "words.dur");
  close(T.words.riseFrac, num("long-form.md", /\| word entrance \| rise ≈ (\d+) % of frame height/) / 100, "words.riseFrac");
  var st = nums("long-form.md", /\| word entrance \|[^|\n]*stagger (\d+)–(\d+) ms/);
  close(T.words.staggerRange[0], st[0] / 1000, "words.staggerRange[0]");
  close(T.words.staggerRange[1], st[1] / 1000, "words.staggerRange[1]");
  assert.ok(T.words.stagger >= T.words.staggerRange[0] && T.words.stagger <= T.words.staggerRange[1], "words.stagger inside its range");
  close(T.glow.pop, num("long-form.md", /\| glow title \| pops to ≈ (\d+) % brightness/) / 100, "glow.pop");
  close(T.glow.settle, num("long-form.md", /\| glow title \|[^|\n]*settles ([\d.]+) s `ease\.glow`/), "glow.settle");
  close(T.glow.nextWord, num("long-form.md", /\| glow title \|[^|\n]*next word \+(\d+) ms/) / 1000, "glow.nextWord");
  var halo = nums("long-form.md", /\| glow title \|[^|\n]*halo (\d+)–(\d+) px at 1080p/);
  assert.ok(T.glow.haloFrac * 1080 >= halo[0] && T.glow.haloFrac * 1080 <= halo[1], "glow.haloFrac inside " + halo.join("–") + " px");
  close(T.defocus.sigmaFrac * 1080, num("long-form.md", /\| backdrop defocus \| blur σ ≈ ([\d.]+) px at 1080p/), "defocus.sigmaFrac");
  close(T.defocus.brightness, num("long-form.md", /\| backdrop defocus \|[^|\n]*brightness → ([\d.]+)/), "defocus.brightness");
  close(T.defocus.dur, num("long-form.md", /\| backdrop defocus \|[^|\n]*over ([\d.]+) s/), "defocus.dur");
  var sw = nums("long-form.md", /\| `ease\.sweep` \|[^|\n]*≈ (\d+) px\/s at (\d+)p \(([\d.]+) s short, ([\d.]+) s long/);
  close(T.sweep.pxPerSecPerH, sw[0] / sw[1], "sweep.pxPerSecPerH");
  close(T.sweep.min, sw[2], "sweep.min");
  close(T.sweep.max, sw[3], "sweep.max");
  close(T.scriptMsPerChar, num("spec", /Script word: ≈ (\d+) ms\/letter/), "scriptMsPerChar");
});

test("Shorts TIMING matches shorts.md", function () {
  var T = P.timing("shorts");
  close(T.typeOnMsPerChar, num("shorts.md", /≈ (\d+) ms\/char/), "typeOnMsPerChar");
  close(T.swap, num("shorts.md", /(\d+) ms — a hard global swap/) / 1000, "swap");
  close(T.words.stagger, num("shorts.md", /~(\d+) ms per word/) / 1000, "words.stagger");
  close(T.chip.expand, num("shorts.md", /expands horizontally ~(\d+) ms/) / 1000, "chip.expand");
  close(T.wipe.inDur, num("shorts.md", /\| duration in \| \*\*([\d.]+)s\*\*/), "wipe.inDur");
  close(T.wipe.outDur, num("shorts.md", /\| duration out \| \*\*([\d.]+)s\*\*/), "wipe.outDur");
  var blur = nums("shorts.md", /\| blur \| `(\d+)px` in \/ `(\d+)px` out/);
  close(T.wipe.blurIn, blur[0], "wipe.blurIn");
  close(T.wipe.blurOut, blur[1], "wipe.blurOut");
  var fe = nums("shorts.md", /\| mask feather \| `(\d+) \+ (\d+) · 4q\(1-q\)`/);
  close(T.wipe.featherMin, fe[0], "wipe.featherMin");
  close(T.wipe.featherGain, fe[1], "wipe.featherGain");
  close(T.wipe.handoff, num("shorts.md", /\| phase handoff \| \*\*([\d.]+)s\*\*/), "wipe.handoff");
});

test("motion-blur shutters match both profiles (and Shorts has no whip)", function () {
  function angle(format, kind) { return MB.profilePreset(format, kind).angle; }
  close(angle("long-form", "leg"), num("long-form.md", /ordinary legs (\d+)°/), "long-form leg");
  close(angle("long-form", "whip"), num("long-form.md", /whips (\d+)°/), "long-form whip");
  close(angle("long-form", "roll"), num("long-form.md", /odometer digit roll (\d+)°/), "long-form roll");
  close(angle("shorts", "leg"), num("shorts.md", /camera legs (\d+)°/), "shorts leg");
  close(angle("shorts", "roll"), num("shorts.md", /odometer digit roll (\d+)°/), "shorts roll");
  assert.match(text("shorts.md"), /Shorts have no whips/);
  assert.deepEqual(Object.keys(MB.PROFILE_PRESETS.shorts).sort(), ["leg", "roll"]);
  assert.deepEqual(Object.keys(MB.PROFILE_PRESETS["long-form"]).sort(), ["leg", "roll", "whip"]);
});
