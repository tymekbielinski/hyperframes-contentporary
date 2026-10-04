"use strict";
/* The contract every kit component must keep, run by each lib/test/kit-<name>.test.js:
 *   long-form only · throws without data-hf-mode · deterministic · profile eases only · no two eased
 *   tweens on one property · build-time style = from-state · light ground has no glow.
 * build(tl, host, extra) calls the component with its fixture options merged with `extra`. */
var test = require("node:test");
var assert = require("node:assert/strict");
var h = require("./helpers.js");
var P = require("../profile.js");

function fresh() {
  global.document = h.fakeDocument();
  global.getComputedStyle = function () { return { getPropertyValue: function () { return ""; } }; };
}

function glowFree(host) {
  return h.descendants(host).filter(function (e) {
    return e.getAttribute("data-blur-reason") === "glow" || /url\(/.test(String(e.style.filter || ""));
  }).length === 0 && document.body.children.filter(function (c) { return c.getAttribute("id") === "hf-glow-host"; }).length === 0;
}

function contract(name, build) {
  test(name + ": long-form only, and throws when no ancestor sets data-hf-mode", function () {
    fresh();
    assert.throws(function () { build(h.fakeTimeline(), h.kitHost("dark"), { format: "shorts" }); }, /long-form only/);
    assert.throws(function () { build(h.fakeTimeline(), h.kitHost(null), {}); }, /no data-hf-mode on the host or any ancestor/);
    var bad = h.kitHost("dim");
    assert.throws(function () { build(h.fakeTimeline(), bad, {}); }, /data-hf-mode must be "dark" or "light", got "dim"/);
  });
  ["dark", "light"].forEach(function (mode) {
    test(name + " (" + mode + "): deterministic, profile eases only, no conflicts, build-time style = from-state", function () {
      fresh();
      var a = h.fakeTimeline(), hostA = h.kitHost(mode), ra = build(a, hostA, {});
      fresh();
      var b = h.fakeTimeline(), hostB = h.kitHost(mode);
      build(b, hostB, {});
      assert.equal(h.serialize(a), h.serialize(b), "same inputs, same timeline");
      // glow filter ids count up per page (hf-glow-1, -2 …): equal up to that counter
      function dom(host) { return h.snapshot(h.descendants(host)).replace(/hf-glow-\d+/g, "hf-glow-N"); }
      assert.equal(dom(hostA), dom(hostB), "same inputs, same DOM");
      assert.ok(ra.dur > 0, "returns how long it takes to settle");
      a.eased().forEach(function (tw) { assert.ok(P.isProfileEase(tw.ease), "tween at " + tw.at + " s uses " + (tw.ease && tw.ease.token || tw.ease)); });
      a.drivers().forEach(function (tw) { assert.equal(typeof tw.to.onUpdate, "function", "a linear tween is a driver"); });
      assert.deepEqual(h.conflicts(a), []);
      assert.deepEqual(h.visibleBeforeStart(a), []);
    });
  });
  test(name + " (light): drops every glow", function () {
    fresh();
    var host = h.kitHost("light");
    build(h.fakeTimeline(), host, {});
    assert.ok(glowFree(host), "no glow filter, no glow-tagged element on the light ground");
  });
}

module.exports = { contract: contract, fresh: fresh, glowFree: glowFree };
