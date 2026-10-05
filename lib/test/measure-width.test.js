"use strict";
var test = require("node:test");
var assert = require("node:assert/strict");
var h = require("./helpers.js");
var X = require("../text.js");
var M = require("../marks.js");
var K = require("../kit/kit.js");
require("../kit/lower-third.js");

// Run fn with fake document/getComputedStyle globals; restore them in finally.
// (Awaits fn's result, so async bodies keep the globals until they finish.)
async function withGlobals(extra, fn) {
  var saved = { document: global.document, getComputedStyle: global.getComputedStyle };
  global.document = Object.assign(h.fakeDocument(), extra || {});
  global.getComputedStyle = function () { return { fontFamily: "Inter", fontSize: "50px", fontWeight: "700", fontStyle: "normal", letterSpacing: "1px" }; };
  try { return await fn(); } finally {
    Object.keys(saved).forEach(function (k) { if (saved[k] === undefined) delete global[k]; else global[k] = saved[k]; });
  }
}
// Every created element reports `width` from getBoundingClientRect unless its parent is display:none (width 0).
function rigProbes(width, log) {
  var make = global.document.createElement;
  global.document.createElement = function (tag) {
    var e = make(tag);
    e.getBoundingClientRect = function () {
      log.push({ parent: e.parentNode, style: e.style });
      return { width: e.parentNode && e.parentNode.hidden ? 0 : width };
    };
    return e;
  };
}
function hiddenEl(parentHidden) {
  var parent = h.fakeEl("div"), el = h.fakeEl("span", { text: "Prediction" });
  parent.hidden = !!parentHidden; el.offsetWidth = 0;
  parent.appendChild(el);
  return { parent: parent, el: el };
}

test("measureWidth: a laid-out element returns offsetWidth, no probe", async function () {
  await withGlobals(null, function () {
    var log = []; rigProbes(99, log);
    var el = h.fakeEl("span"); el.offsetWidth = 321;
    assert.equal(X.measureWidth(el), 321);
    assert.equal(log.length, 0);
  });
});

test("measureWidth: probe lives in el.parentNode (not body), is hidden/absolute/pre, copies the font, and is removed", async function () {
  await withGlobals(null, function () {
    var log = []; rigProbes(250, log);
    var t = hiddenEl(false);
    assert.equal(X.measureWidth(t.el), 250);
    assert.equal(log.length, 1);
    assert.equal(log[0].parent, t.parent, "measured while parented to el.parentNode");
    var st = log[0].style;
    assert.match(st.cssText, /visibility:hidden/); assert.match(st.cssText, /position:absolute/); assert.match(st.cssText, /white-space:pre/);
    ["fontFamily", "fontSize", "fontWeight", "letterSpacing"].forEach(function (k) { assert.ok(st[k], k + " is copied"); });
    assert.equal(t.parent.children.filter(function (e) { return e !== t.el; }).length, 0, "probe removed from the parent");
    assert.equal(document.body.children.length, 0);
  });
});

test("measureWidth: a display:none parent falls back to a body probe, removed afterwards; 0 when nothing works", async function () {
  await withGlobals(null, function () {
    var log = []; rigProbes(180, log);
    var t = hiddenEl(true);
    assert.equal(X.measureWidth(t.el), 180);
    assert.equal(log.length, 2, "parent probe (0) then body probe");
    assert.equal(log[1].parent, document.body);
    assert.equal(document.body.children.length, 0, "body probe removed");
    rigProbes(0, []);
    assert.equal(X.measureWidth(hiddenEl(true).el), 0, "caller picks the fallback");
    assert.equal(document.body.children.length, 0);
  });
});

test("measureWidth: probe is removed even when measuring throws", async function () {
  await withGlobals(null, function () {
    var make = document.createElement;
    document.createElement = function (tag) { var e = make(tag); e.getBoundingClientRect = function () { throw new Error("boom"); }; return e; };
    var t = hiddenEl(false);
    assert.equal(X.measureWidth(t.el), 0);
    assert.equal(t.parent.children.length, 1);
    assert.equal(document.body.children.length, 0);
  });
});

test("measureWidth: an unloaded font re-measures after fonts.load; HFText.ready() waits for the callback", async function () {
  var loaded = false, loadedArgs = null;
  var fonts = { check: function () { return loaded; }, load: function (face, text) { loadedArgs = [face, text]; return new Promise(function (r) { setTimeout(function () { loaded = true; r(); }, 5); }); } };
  await withGlobals({ fonts: fonts }, async function () {
    var width = 100;
    var t = hiddenEl(false);
    var make = document.createElement;
    document.createElement = function (tag) { var e = make(tag); e.getBoundingClientRect = function () { return { width: width }; }; return e; };
    var got = [];
    assert.equal(X.measureWidth(t.el, function (w) { got.push(w); }), 100, "first measure is returned at once");
    width = 140;   // the real font is wider
    assert.deepEqual(got, [], "not called before the font loads");
    await X.ready();
    assert.deepEqual(got, [140], "re-measured after the load, awaited by ready()");
    assert.match(loadedArgs[0], /700 50px Inter/); assert.equal(loadedArgs[1], "Prediction");
    got = [];
    X.measureWidth(t.el, function (w) { got.push(w); });   // font now loaded: no callback
    await X.ready();
    assert.deepEqual(got, []);
  });
});

test("marks.highlight and the lower third measure through HFText.measureWidth", async function () {
  var calls = [], real = X.measureWidth;
  X.measureWidth = function (el) { calls.push(el); return 321; };
  try {
    var tl = h.fakeTimeline(), el = h.fakeEl("span");
    M.highlight(tl, el, 0, { format: "long-form", frameHeight: 1080 });
    assert.deepEqual(calls, [el], "highlight");
    calls.length = 0;
    await withGlobals(null, function () {
      var host = h.kitHost("dark");
      K.lowerThird(h.fakeTimeline(), host, { format: "long-form", at: 0, text: "and I helped" });
      assert.ok(calls.length >= 1 && calls[0].children !== undefined, "lower third key line");
    });
  } finally { X.measureWidth = real; }
});

test("loadFaces: collects the faces of hidden elements, dedupes, loads declared faces, never rejects", async function () {
  var loads = [], declared = 0;
  var fonts = {
    load: function (face, text) { loads.push([face, text]); return Promise.resolve(); },
    forEach: function (fn) { fn({ load: function () { declared++; return Promise.reject(new Error("bad face")); } }); }
  };
  await withGlobals({ fonts: fonts }, async function () {
    var saved = global.getComputedStyle, warn = console.warn, warned = 0;
    console.warn = function () { warned++; };
    global.getComputedStyle = function (el) {
      return el.hidden ? { fontStyle: "normal", fontWeight: "900", fontSize: "104px", fontFamily: "Satoshi" }
        : { fontStyle: "normal", fontWeight: "400", fontSize: "50px", fontFamily: "Inter" };
    };
    try {
      var root = h.fakeEl("div", { text: "root" }), a = h.fakeEl("div", { text: "Title" }), b = h.fakeEl("span", { text: "Other" }), c = h.fakeEl("span", { text: "Body" });
      a.hidden = true; b.hidden = true;   // display:none elements still get a computed style
      a.appendChild(b); root.appendChild(a); root.appendChild(c);
      await X.loadFaces(root);
      var faces = loads.map(function (l) { return l[0]; }).sort();
      assert.deepEqual(faces, ["normal 400 50px Inter", "normal 900 104px Satoshi"], "two distinct faces, hidden one included, deduped");
      assert.equal(loads.filter(function (l) { return /Satoshi/.test(l[0]); })[0][1], "Other", "sample text is the first hidden element's own text");
      assert.equal(declared, 1, "declared @font-face loaded too");
      assert.ok(warned >= 1, "a rejected load is a warning, not a rejection");
    } finally { global.getComputedStyle = saved; console.warn = warn; }
  });
});

test("loadFaces: resolves at once without document.fonts", async function () {
  await withGlobals(null, async function () {
    assert.equal(await X.loadFaces(h.fakeEl("div")), undefined);
  });
});
