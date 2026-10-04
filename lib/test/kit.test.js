"use strict";
var test = require("node:test");
var assert = require("node:assert/strict");
var h = require("./helpers.js");
var P = require("../profile.js");
var c = require("./kit-contract.js");
var fs = require("node:fs");
var path = require("node:path");
var K = require("../kit/kit.js");
// Every component file that exists so far (the kit is built one component per task).
var KIT = require("../../brands/contentporary/tokens.json").kit;
var BUILT = Object.keys(KIT).filter(function (n) { return fs.existsSync(path.join(__dirname, "..", "kit", n + ".js")); });
BUILT.forEach(function (n) { require("../kit/" + n + ".js"); });

test("each built component registers the variant brands/contentporary/tokens.json names, under its camel-case call", function () {
  BUILT.forEach(function (name) {
    assert.deepEqual(K.variants(name), [KIT[name]], name);
    assert.equal(typeof K[name.replace(/-([a-z])/g, function (_, ch) { return ch.toUpperCase(); })], "function", name);
  });
});

test("register(): a component is called through its variant; an unknown variant throws naming the ones that exist", function () {
  c.fresh();
  K.register("zz-probe", "plain", function (tl, host, o) { return { dur: 1, got: o.variant || "plain" }; });
  assert.deepEqual(K.zzProbe(h.fakeTimeline(), h.kitHost("dark"), {}), { dur: 1, got: "plain" });
  assert.throws(function () { K.zzProbe(h.fakeTimeline(), h.kitHost("dark"), { variant: "neon" }); },
    /HFKit\.zzProbe: unknown variant "neon" \(have: plain\)/);
  assert.throws(function () { K.register("zz-probe", "plain", function () {}); }, /zz-probe\/plain registered twice/);
});

test("begin(): long-form only, a host, a time ≥ 0; puts the resolved mode on the host as a class", function () {
  c.fresh();
  var host = h.kitHost("light");
  var b = K.begin("zz-probe", host, { format: "long-form", at: 1.5 });
  assert.deepEqual([b.mode, b.at, b.who, b.lf.frameHeight], ["light", 1.5, "HFKit.zzProbe", 1080]);
  assert.ok(host.classList.contains("hf-kit-host") && host.classList.contains("hf-kit-light"));
  assert.throws(function () { K.begin("zz-probe", host, { format: "shorts" }); }, /long-form only/);
  assert.throws(function () { K.begin("zz-probe", {}, { format: "long-form" }); }, /host must be an element/);
  assert.throws(function () { K.begin("zz-probe", host, { format: "long-form", at: -1 }); }, /opts\.at must be a time/);
  assert.doesNotMatch(K.css(), /data-hf-mode/);
});

test("mode(): the host's own data-hf-mode or the nearest ancestor's, never a default", function () {
  var host = h.kitHost("light");
  assert.equal(K.mode(host, "t"), "light");
  host.setAttribute("data-hf-mode", "dark");
  assert.equal(K.mode(host, "t"), "dark");
  assert.throws(function () { K.mode(h.kitHost(null), "HFKit.x"); }, /HFKit\.x: no data-hf-mode/);
});

test("kit CSS: colours are brand variables only, and every glow is scoped to the dark ground", function () {
  var css = K.css();
  assert.doesNotMatch(css, /#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(|color-mix\(/, "no colour literal in the kit stylesheet");
  css.split("}").forEach(function (rule) {
    if (/text-shadow|drop-shadow/.test(rule)) {
      assert.match(rule, /^\s*\.hf-kit-dark /, "glow outside the dark ground: " + rule.trim().slice(0, 90));
    }
  });
});

test("entrances write their from-state at build and use the profile's card/node/words timings", function () {
  c.fresh();
  var T = P.timing("long-form"), tl = h.fakeTimeline(), card = h.fakeEl("div"), dot = h.fakeEl("div"), panel = h.fakeEl("div"), layout = h.fakeEl("div");
  assert.equal(K.cardIn(tl, card, 1), T.card.dur);
  assert.equal(card.getAttribute("data-blur-reason"), "focus");
  assert.equal(K.pop(tl, dot, 2), T.node.dur);
  assert.equal(K.slideIn(tl, panel, 3, -80), T.words.dur);
  assert.equal(K.fadeOut(tl, layout, 5), T.card.dur, "exits fade the layout's root, never an element an entrance animates");
  assert.deepEqual(h.visibleBeforeStart(tl), []);
  assert.deepEqual(tl.eased().map(function (tw) { return tw.ease.token; }), ["ease.card", "ease.enter", "ease.enter", "ease.enter"]);
  assert.throws(function () { K.cardIn(h.fakeTimeline(), dot, 0); }, /HFKit\.cardIn would overwrite the inline transform that HFKit\.pop animates/);
});
