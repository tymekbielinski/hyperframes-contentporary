"use strict";
/* The contract every kit component must keep, run by each lib/test/kit-<name>.test.js:
 *   long-form only · throws without (or with a bad) data-hf-mode · deterministic (timeline, DOM classes, text) ·
 *   profile eases or ease:"none" drivers with onUpdate only · no two tweens on one property (drivers
 *   included) · no tl.set inside another tween's window on the same property (a set is an instant,
 *   deterministic step, so it is otherwise allowed whatever its value) · build-time style = from-state ·
 *   every blur tagged data-blur-reason · returned dur = last tween end − at · opts.at shifts every tween ·
 *   seek order never changes a frame · light ground has no glow.
 * build(tl, host, extra) calls the component with its fixture options merged with `extra`.
 * violations(build) returns the broken rules as "[tag] message" strings, so the contract itself can be
 * tested against fixtures that break one rule each (kit-contract.test.js). */
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
    return e.getAttribute("data-blur-reason") === "glow" || /url\(/.test(String(e.style.filter || "")) ||
      (e.style.textShadow && e.style.textShadow !== "none") || (e.style["text-shadow"] && e.style["text-shadow"] !== "none");
  }).length === 0 && document.body.children.filter(function (c) { return c.getAttribute("id") === "hf-glow-host"; }).length === 0;
}

function attempt(fn) { try { fn(); return null; } catch (e) { return e && e.message || String(e); } }
function guard(problems, tag, build, host, extra, re, label) {
  var msg = attempt(function () { build(h.fakeTimeline(), host, extra); });
  if (msg === null) problems.push("[" + tag + "] " + label + ": did not throw");
  else if (!re.test(msg)) problems.push("[" + tag + "] " + label + ": threw the wrong error: " + msg);
}

// The rules that need no ground mode: format and data-hf-mode guards.
function guards(build) {
  var problems = [];
  fresh();
  guard(problems, "format", build, h.kitHost("dark"), { format: "shorts" }, /long-form only/, "format shorts");
  guard(problems, "mode", build, h.kitHost(null), {}, /no data-hf-mode on the host or any ancestor/, "no data-hf-mode");
  guard(problems, "mode", build, h.kitHost("dim"), {}, /data-hf-mode must be "dark" or "light", got "dim"/, "bad data-hf-mode");
  return problems;
}

function tweenEnd(tl) {
  return tl.tweens.reduce(function (m, tw) { return typeof tw.at === "number" ? Math.max(m, tw.at + (tw.dur || 0)) : m; }, 0);
}
// A tl.set landing inside another tween's [at, at + dur] window on the same element and property.
function setConflicts(tl) {
  var SKIP = ["duration", "ease", "immediateRender", "onUpdate", "stagger"], out = [];
  tl.tweens.forEach(function (s, i) {
    if (s.kind !== "set" || typeof s.at !== "number") return;
    tl.tweens.forEach(function (tw) {
      if (tw.kind === "set" || typeof tw.at !== "number" || s.at < tw.at - 1e-9 || s.at > tw.at + (tw.dur || 0) + 1e-9) return;
      [].concat(s.target).forEach(function (t) {
        if ([].concat(tw.target).indexOf(t) === -1) return;
        Object.keys(s.vars || {}).forEach(function (k) {
          if (SKIP.indexOf(k) === -1 && k in (tw.to || {})) out.push("set #" + i + " " + k + " inside the tween at " + tw.at + " s");
        });
      });
    });
  });
  return out;
}
function blurTagged(e) { var r = e.getAttribute("data-blur-reason"); return r === "focus" || r === "glow"; }

// Everything a built timeline must satisfy in one ground mode.
function modeRules(build, mode) {
  var problems = [];
  function note(tag, msg) { problems.push("[" + tag + "] " + msg); }
  fresh();
  var a = h.fakeTimeline(), hostA = h.kitHost(mode), ra = build(a, hostA, {});
  fresh();
  var b = h.fakeTimeline(), hostB = h.kitHost(mode);
  build(b, hostB, {});
  if (h.serialize(a) !== h.serialize(b)) note("determinism", mode + ": same inputs gave different timelines");
  // glow filter ids count up per page (hf-glow-1, -2 …): equal up to that counter
  function dom(host) { return h.snapshot(h.descendants(host)).replace(/hf-glow-\d+/g, "hf-glow-N"); }
  if (dom(hostA) !== dom(hostB)) note("determinism", mode + ": same inputs gave different DOM (style, attributes, class names or text)");
  if (!ra || !(ra.dur > 0)) note("dur", "must return { dur } > 0, got " + JSON.stringify(ra && ra.dur));
  // every tween: a profile ease, or a linear driver with onUpdate
  a.tweens.forEach(function (tw, i) {
    if (tw.kind === "set") return;
    var to = tw.to || {};
    if (tw.ease === "none") {
      if (typeof to.onUpdate !== "function") note("driver", "tween #" + i + " at " + tw.at + " s is ease:\"none\" without onUpdate");
    } else if (!P.isProfileEase(tw.ease)) {
      note("ease", "tween #" + i + " at " + tw.at + " s uses " + JSON.stringify(tw.ease && tw.ease.token || (typeof tw.ease === "function" ? "a raw function" : tw.ease)) + ", not an HFProfile ease");
    }
  });
  var conflicting = h.allConflicts({ tweens: a.tweens.filter(function (tw) { return tw.kind !== "set"; }) }).concat(setConflicts(a));
  if (conflicting.length) note("conflict", "two tweens animate " + conflicting.join(", "));
  var before = attempt(function () { var bad = h.visibleBeforeStart(a); if (bad.length) throw new Error("tweens " + bad.join(", ") + " differ from the build-time style"); });
  if (before) note("before-start", before);
  // a blur is a tagged Gaussian: the build-time element and every tweened filter
  h.descendants(hostA).forEach(function (e) {
    if (/blur\(/.test(String(e.style.filter || "")) && !blurTagged(e)) note("blur", "an element shows " + e.style.filter + " without data-blur-reason focus|glow");
  });
  a.tweens.forEach(function (tw, i) {
    var vals = [tw.from, tw.to, tw.vars].filter(Boolean).map(function (o) { return String(o.filter || ""); }).join(" ");
    if (/blur\(/.test(vals)) [].concat(tw.target).forEach(function (t) { if (t && t.getAttribute && !blurTagged(t)) note("blur", "tween #" + i + " blurs an element without data-blur-reason focus|glow"); });
  });
  // settle: dur is what the timeline actually takes
  if (ra && Math.abs(tweenEnd(a) - 0 - ra.dur) > 1e-6) note("dur", "returned dur " + ra.dur + " but the last tween ends " + tweenEnd(a) + " s after at");
  // offset: opts.at moves every tween by exactly that much
  fresh();
  var c = h.fakeTimeline(), rc = build(c, h.kitHost(mode), { at: 2.5 });
  if (c.tweens.length !== a.tweens.length) note("offset", "at: 2.5 built " + c.tweens.length + " tweens, at: 0 built " + a.tweens.length);
  else {
    c.tweens.forEach(function (tw, i) {
      if (!(Math.abs(tw.at - a.tweens[i].at - 2.5) <= 1e-6)) note("offset", "tween #" + i + " moved " + (tw.at - a.tweens[i].at) + " s for at: 2.5");
    });
    if (rc && ra && Math.abs(rc.dur - ra.dur) > 1e-6) note("offset", "dur changed with at (" + ra.dur + " vs " + rc.dur + ")");
  }
  // seek order: the same frame whichever way the playhead got there
  var end = tweenEnd(a), times = [0, 0.1, 0.25, end / 2, Math.max(0, end - 0.01), end, end + 1].filter(function (t, i, l) { return l.indexOf(t) === i; });
  var order = h.seekOrderInvariant(a, times, h.descendants(hostA));
  if (order.length) note("seek", "frame at t = " + order.join(", ") + " depends on the seek order");
  return problems;
}

// Light ground: no glow of any kind.
function lightRules(build) {
  fresh();
  var host = h.kitHost("light");
  build(h.fakeTimeline(), host, {});
  return glowFree(host) ? [] : ["[glow] light ground has a glow filter, glow-tagged element or text-shadow"];
}

function violations(build) { return guards(build).concat(modeRules(build, "dark"), modeRules(build, "light"), lightRules(build)); }

function contract(name, build) {
  test(name + ": long-form only, and throws when no ancestor sets data-hf-mode", function () {
    assert.deepEqual(guards(build), []);
  });
  ["dark", "light"].forEach(function (mode) {
    test(name + " (" + mode + "): deterministic, profile eases only, no conflicts, build-time style = from-state, dur settles, at shifts, seek-order safe", function () {
      assert.deepEqual(modeRules(build, mode), []);
    });
  });
  test(name + " (light): drops every glow", function () {
    assert.deepEqual(lightRules(build), []);
  });
}

module.exports = { contract: contract, fresh: fresh, glowFree: glowFree, violations: violations };
