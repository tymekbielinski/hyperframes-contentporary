"use strict";
var test = require("node:test");
var assert = require("node:assert/strict");
var h = require("./helpers.js");
var P = require("../profile.js");
var X = require("../text.js");

global.document = h.fakeDocument();
document.body = h.fakeEl("body");
var byId = {};
document.getElementById = function (id) { return byId[id] || null; };
var LF = { format: "long-form", frameHeight: 1080 };

test("words (long-form): one span per word, focus-tagged, 7 % rise, profile stagger + ease", function () {
  var tl = h.fakeTimeline(), el = h.fakeEl("h1", { text: "HIT  Prediction works" });
  var d = X.words(tl, el, 2, LF);
  assert.equal(el.children.length, 3);
  el.children.forEach(function (s) { assert.equal(s.getAttribute("data-blur-reason"), "focus"); });
  assert.deepEqual(tl.tweens.map(function (t) { return +t.at.toFixed(3); }), [2, 2.28, 2.56]);
  assert.ok(Math.abs(tl.tweens[0].from.y - 75.6) < 1e-9);
  assert.equal(tl.tweens[0].ease, P.ease("long-form", "ease.enter"));
  assert.ok(Math.abs(d - (2 * 0.28 + 0.6)) < 1e-9);
  assert.deepEqual(h.conflicts(tl), []);
  assert.deepEqual(h.visibleBeforeStart(tl), []);
});

test("words: stagger outside the long-form band throws; Shorts default 200 ms; empty text is a no-op", function () {
  assert.throws(function () { X.words(h.fakeTimeline(), h.fakeEl("p", { text: "a b" }), 0, Object.assign({ stagger: 0.05 }, LF)); }, /stagger must be 0.11–0.33/);
  var tl = h.fakeTimeline();
  X.words(tl, h.fakeEl("p", { text: "We Handle Everything!" }), 26.93, { format: "shorts", frameHeight: 1920 });
  assert.ok(Math.abs(tl.tweens[2].at - 27.33) < 1e-9);
  var tl2 = h.fakeTimeline();
  assert.equal(X.words(tl2, h.fakeEl("p", { text: "   " }), 0, LF), 0);
  assert.equal(tl2.tweens.length, 0);
});

test("typeOn: Shorts 67 ms/char by default; long-form must pass a rate", function () {
  var tl = h.fakeTimeline(), el = h.fakeEl("span", { text: "Meetings" });
  X.typeOn(tl, el, 6.067, { format: "shorts", blinks: 0 });
  var firstChars = tl.tweens.filter(function (t) { return t.vars.visibility === "visible" && t.target.style.position === "relative"; });
  assert.equal(firstChars.length, 8);
  assert.ok(Math.abs(firstChars[1].at - (6.067 + 0.067)) < 1e-9);
  assert.throws(function () { X.typeOn(h.fakeTimeline(), h.fakeEl("span", { text: "x" }), 0, LF); }, /has no type-on rate/);
});

test("glowFilter: five Gaussian levels, every one tagged glow", function () {
  var m = X.glowFilter("g1");
  assert.equal((m.match(/<feGaussianBlur /g) || []).length, 5);
  assert.equal((m.match(/<feGaussianBlur data-blur-reason="glow"/g) || []).length, 5);
  assert.match(m, /id="g1-r"/);
});

test("glowOpacity: hidden until just after its time, pops to 0.7, settles to 1 in 0.4 s", function () {
  assert.equal(X.glowOpacity(-1, "long-form"), 0);
  assert.equal(X.glowOpacity(0, "long-form"), 0);
  assert.ok(X.glowOpacity(0.001, "long-form") >= 0.7);
  assert.equal(X.glowOpacity(0.4, "long-form"), 1);
  assert.throws(function () { X.glowOpacity(0.1, "shorts"); }, /glow/);
});

test("glowTitle: long-form only, one driver, words 430 ms apart, seek-order safe", function () {
  assert.throws(function () { X.glowTitle(h.fakeTimeline(), [h.fakeEl()], 0, { format: "shorts", frameHeight: 1920 }); }, /not in the shorts ease table/);
  var tl = h.fakeTimeline(), w1 = h.fakeEl("span"), w2 = h.fakeEl("span");
  var d = X.glowTitle(tl, [w1, w2], 4, Object.assign({ glowId: "gt" }, LF));
  assert.ok(Math.abs(d - 0.83) < 1e-9);
  assert.equal(tl.drivers().length, 1);
  assert.equal(w1.getAttribute("data-blur-reason"), "glow");
  assert.deepEqual(h.seekOrderInvariant(tl, [3, 4, 4.1, 4.3, 4.43, 4.5, 4.83, 6], [w1, w2]), []);
  tl.seek(4.2); assert.equal(w2.style.opacity, "0.0000");
});

test("defocus: focus-tagged blur + dim on ease.enter; not in Shorts", function () {
  var tl = h.fakeTimeline(), bg = h.fakeEl("div");
  X.defocus(tl, bg, 1, LF);
  assert.equal(bg.getAttribute("data-blur-reason"), "focus");
  assert.equal(tl.tweens[0].to.filter, "blur(4.50px) brightness(0.6)");
  assert.equal(bg.style.filter, tl.tweens[0].from.filter, "pre-start state = from-state");
  assert.throws(function () { X.defocus(h.fakeTimeline(), bg, 1, { format: "shorts", frameHeight: 1920 }); }, /no backdrop defocus/);
});

test("accentWord is a single attribute set (seek-safe), styled by the brand variable", function () {
  var tl = h.fakeTimeline(), el = h.fakeEl("span");
  X.accentWord(tl, el, 3);
  assert.deepEqual(tl.tweens[0].vars, { attr: { "data-hf-accent": "1" } });
  assert.match(X.CSS, /var\(--hf-accent-text\)/);
});

test("odometer math: start values always lower than the final", function () {
  assert.equal(X.startValue(150000, 0), 100000);
  assert.equal(X.startValue(14.4, 1), 10);
  assert.equal(X.startValue(10, 0), 7);
  assert.equal(X.startValue(8, 0), 5);
  assert.equal(X.startValue(0, 0), 0);
  var p = X.parseRuns("$150,000");
  assert.equal(p.runs.length, 1);
  assert.equal(p.runs[0].final, 150000); assert.equal(p.runs[0].start, 100000);
  assert.equal(p.runs[0].seps[0].threshold, 1000);
  assert.equal(X.parseRuns("14.4").runs[0].decimals, 1);
  assert.equal(X.parseRuns("10+", 9).runs[0].start, 9);
  assert.equal(X.parseRuns("10+", 50).runs[0].start, 7);
  assert.deepEqual(X.parseRuns("N/A").runs, []);
});

test("odometer wheels: units roll continuously, higher places only turn during the carry", function () {
  var run = X.parseRuns("19").runs[0];
  var units = { run: run, place: 0, p10: 1 }, tens = { run: run, place: 1, p10: 10 };
  assert.ok(Math.abs(X.wheelPos(units, 12.5) - 2.5) < 1e-9);
  assert.equal(X.wheelPos(tens, 12.5), 1);
  assert.ok(Math.abs(X.wheelPos(tens, 19.5) - 1.5) < 1e-9);
  assert.ok(Math.abs(X.wheelUnwrapped(tens, 29.5) - 2.5) < 1e-9);
  assert.equal(X.wheelUnwrapped(tens, 30), 3);
});

test("odometer: a label without digits just appears", function () {
  var tl = h.fakeTimeline();
  var el = h.fakeEl("span");
  X.odometer(tl, el, 1, 2, "N/A", { format: "long-form" });
  assert.deepEqual(tl.tweens.map(function (t) { return t.kind; }), ["set"]);
  assert.equal(el.style.opacity, "0", "hidden until T");
});

test("words: build-time style equals the tween from-state (opacity, rise, blur)", function () {
  var tl = h.fakeTimeline(), el = h.fakeEl("h1", { text: "one two" });
  X.words(tl, el, 1, LF);
  el.children.forEach(function (s, i) {
    assert.equal(s.style.opacity, "0");
    assert.equal(s.style.transform, "translate(0px, " + tl.tweens[i].from.y + "px)");
    assert.equal(s.style.filter, tl.tweens[i].from.filter);
  });
});

test("typeOn: iterates code points, so an emoji is one character (no surrogate split)", function () {
  var tl = h.fakeTimeline(), el = h.fakeEl("span", { text: "hi 👋" });
  X.typeOn(tl, el, 0, { format: "shorts", blinks: 0 });
  assert.equal(el.children.length, 4);
  assert.equal(el.children[3]._text, "👋");   // its own text (the caret child is the only child node)
});

/* ---------- odometer GL lifetime, context loss, HFText.ready() ---------- */
global.getComputedStyle = function () {
  return { fontSize: "40px", fontStyle: "normal", fontWeight: "700", fontFamily: "Inter", color: "currentColor", letterSpacing: "0px" };
};
// Each canvas gets its own fake GL; webgl counts getContext("webgl") calls (context creations).
function odoRig() {
  var made = [], webgl = { n: 0 }, saved = document.createElement;
  document.createElement = function (tag) {
    if (tag !== "canvas") return h.fakeEl(tag);
    var gl = h.fakeGl(), c = h.fakeCanvas(0, 0, gl), get = c.getContext;
    c.getContext = function (kind) { if (kind === "webgl") webgl.n++; return get(kind); };
    c.gl = gl; made.push(c); return c;
  };
  var tl = h.fakeTimeline(), el = h.fakeEl("span");
  X.odometer(tl, el, 1, 2, "150", { format: "long-form" });
  document.createElement = saved;
  var cv = made[0], win = el.children[el.children.length - 1];
  var digits = el.children.filter(function (c) { return c !== win; });
  return { tl: tl, el: el, cv: cv, win: win, digits: digits, webgl: webgl };
}
function loseCount(gl) { return gl.log.filter(function (e) { return e[0] === "loseContext"; }).length; }

test("odometer: context lost after a successful render -> DOM digits, GL window hidden, later seeks safe", function () {
  var o = odoRig();
  o.tl.seek(1.5);
  assert.equal(o.win.style.visibility, "visible", "GL painted inside the window");
  o.cv.gl.getExtension("WEBGL_lose_context").loseContext();   // the browser drops the context
  o.tl.seek(1.6);
  assert.equal(o.win.style.visibility, "hidden");
  o.digits.forEach(function (d) { assert.equal(d.style.visibility, "inherit"); });
  var created = o.webgl.n;
  assert.doesNotThrow(function () { o.tl.seek(1.7); o.tl.seek(1.2); o.tl.seek(2.5); });
  assert.equal(o.webgl.n, created, "failed: stays on the DOM digits, no re-create");
  assert.equal(o.win.style.visibility, "hidden");
});

test("odometer: no live context outside T < t < T + dur (backward seek releases, never re-creates)", function () {
  var o = odoRig();
  o.tl.seek(0.5);
  assert.equal(o.webgl.n, 0, "no context before the window");
  o.tl.seek(1.5);
  assert.equal(o.webgl.n, 1);
  o.tl.seek(0.4);   // the driver clamps to t = T
  assert.equal(loseCount(o.cv.gl), 1, "released on the backward seek");
  assert.equal(o.win.style.visibility, "hidden");
  o.digits.forEach(function (d) { assert.equal(d.style.visibility, "inherit"); });
  o.tl.seek(0.2); o.tl.seek(3.5);
  assert.equal(o.webgl.n, 1, "no create at t <= T or t >= T + dur");
  var opacitySet = o.tl.tweens.filter(function (tw) { return tw.kind === "set" && tw.target === o.el; })[0];
  assert.ok(opacitySet.at > 1, "the label never shows its final DOM digits at exactly t = T");
});

test("odometer: opts.fps sets the exposure (default 30)", function () {
  function exp(fps) {
    var made = [], saved = document.createElement;
    document.createElement = function (tag) { if (tag !== "canvas") return h.fakeEl(tag); var gl = h.fakeGl(), c = h.fakeCanvas(0, 0, gl); c.gl = gl; made.push(c); return c; };
    var tl = h.fakeTimeline();
    X.odometer(tl, h.fakeEl("span"), 0, 2, "90", { format: "long-form", fps: fps });
    document.createElement = saved;
    tl.seek(1);
    return made[0].gl.log.filter(function (e) { return e[0] === "uExp"; })[0][1];
  }
  var roll = require("../motion-blur.js").profilePreset("long-form", "roll");
  assert.ok(Math.abs(exp(undefined) - roll.shutter / 30) < 1e-12);
  assert.ok(Math.abs(exp(60) - roll.shutter / 60) < 1e-12);
});

test("HFText.ready() waits for an async measure, and the re-measure reaches the texture (updateWorld)", async function () {
  var release, fontsReady = new Promise(function (r) { release = r; });
  document.fonts = { ready: fontsReady };
  try {
    var o = odoRig();
    o.tl.seek(1.5);   // first frame before the fonts land: measures synchronously, creates the blur
    var uploads = function () { return o.cv.gl.log.filter(function (e) { return e[0] === "texImage2D"; }).length; };
    assert.equal(uploads(), 1);
    var done = false, p = X.ready().then(function () { done = true; });
    await Promise.resolve(); await Promise.resolve();
    assert.equal(done, false, "still pending while the font load is outstanding");
    release();
    await p;
    assert.equal(uploads(), 2, "the re-measure after fonts load called updateWorld with the new world");
  } finally { delete document.fonts; }
});

test("splitWords keeps nested markup: words inside <b> stay inside it, spaces stay in their words", function () {
  var b = h.fakeMixed("b", [h.fakeText("Prediction")]);
  var el = h.fakeMixed("h1", [h.fakeText("HIT "), b, h.fakeText(" works  now")]);
  var spans = X.splitWords(el);
  assert.deepEqual(spans.map(function (s) { return s.textContent; }), ["HIT ", "Prediction", "works ", "now"]);
  assert.equal(el.childNodes[1], b);
  assert.equal(b.childNodes[0], spans[1], "the word span sits inside the <b>");
  assert.equal(el.childNodes[2].nodeType, 3, "leading whitespace of a text node becomes one space text node");
  var skip = h.fakeMixed("em", [h.fakeText("as is")]); skip.setAttribute("data-hf-nosplit", "");
  var el2 = h.fakeMixed("p", [h.fakeText("a "), skip]);
  assert.equal(X.splitWords(el2).length, 1, "data-hf-nosplit children are left whole");
});

test("words: opts.onSpans receives the word spans; each span is claimed for its transform", function () {
  var tl = h.fakeTimeline(), el = h.fakeEl("h1", { text: "one two three" }), got = null;
  X.words(tl, el, 0, Object.assign({ onSpans: function (s) { got = s; } }, LF));
  assert.equal(got.length, 3);
  assert.equal(got[0], el.children[0]);
  assert.throws(function () { require("../marks.js").highlight(h.fakeTimeline(), got[0], 1, LF); }, /HFMarks\.highlight would overwrite the inline transform that HFText\.words animates/);
});

test("typeOn: opts.onSpans gets the character spans (before carets are added)", function () {
  var tl = h.fakeTimeline(), got = null;
  X.typeOn(tl, h.fakeEl("span", { text: "Hey" }), 0, { format: "shorts", blinks: 0, onSpans: function (s) { got = s.map(function (x) { return x._text; }); } });
  assert.deepEqual(got, ["H", "e", "y"]);
});

test("glowTitle: opts.intensity sets the settled bloom (default 1.2)", function () {
  var slopes = {}, saved = document.getElementById;
  document.getElementById = function (id) { return { setAttribute: function (k, v) { slopes[id] = v; } }; };
  try {
    var tl = h.fakeTimeline();
    X.glowTitle(tl, [h.fakeEl("span")], 0, Object.assign({ glowId: "gi", intensity: 0.6 }, LF));
    tl.seek(5); assert.equal(slopes["gi-r"], "0.6000");
    var tl2 = h.fakeTimeline();
    X.glowTitle(tl2, [h.fakeEl("span")], 0, Object.assign({ glowId: "gd" }, LF));
    tl2.seek(5); assert.equal(slopes["gd-r"], "1.2000");
    assert.throws(function () { X.glowTitle(h.fakeTimeline(), [h.fakeEl("span")], 0, Object.assign({ glowId: "gx", intensity: -1 }, LF)); }, /intensity must be ≥ 0/);
  } finally { document.getElementById = saved; }
});

test("accentWord installs its stylesheet itself, once", function () {
  var appended = [], present = false, savedGet = document.getElementById, savedHead = document.head;
  document.getElementById = function (id) { return id === "hf-text-css" && present ? {} : null; };
  document.head = { appendChild: function (s) { appended.push(s); present = true; } };
  try {
    var tl = h.fakeTimeline();
    X.accentWord(tl, h.fakeEl("span"), 1);
    X.accentWord(tl, h.fakeEl("span"), 2);
    assert.equal(appended.length, 1);
    assert.equal(appended[0].textContent, X.CSS);
  } finally { document.getElementById = savedGet; document.head = savedHead; }
});

test("blurPx tags the element and returns the CSS string; track() is what ready() waits on", async function () {
  var el = h.fakeEl("div");
  assert.equal(X.blurPx(el, "focus", 4), "blur(4px)");
  assert.equal(el.getAttribute("data-blur-reason"), "focus");
  var release, p = new Promise(function (r) { release = r; }), done = false;
  X.track(p);
  var r = X.ready().then(function () { done = true; });
  await Promise.resolve();
  assert.equal(done, false);
  release(); await r;
  assert.equal(done, true);
});

test("splitWords trims edge whitespace like the old words(): padded text node, nested markup", function () {
  var el = h.fakeMixed("h1", [h.fakeText("\n  Hello world\n")]);
  var spans = X.splitWords(el);
  assert.deepEqual(spans.map(function (s) { return s.textContent; }), ["Hello ", "world"]);
  assert.equal(el.childNodes[0], spans[0], "no leading text node");
  var b = h.fakeMixed("b", [h.fakeText("Hello")]);
  var el2 = h.fakeMixed("p", [b, h.fakeText(" world ")]);
  var s2 = X.splitWords(el2);
  assert.deepEqual(s2.map(function (s) { return s.textContent; }), ["Hello", "world"]);
  assert.equal(el2.childNodes[1].nodeType, 3, "the space between the <b> and the next word stays");
});
