/* HFKit.title — variant "glow-center" (template still: full-screen title, gold).
 * A centred one-line headline on the full-frame ground; the grid rack-defocuses behind it.
 * Dark ground: HFText.glowTitle (pop to 70 %, settle 0.4 s ease.glow, next word +430 ms), warm
 * ambient glow at the top. Light ground: no glow — HFText.words in dark text.primary.
 * Optional scribble underline (accent.line) under one word, drawn on ease.sweep once the title
 * has settled — the glow-center still's underline; on the light ground it is the emphasis mark.
 *
 *   HFKit.title(tl, host, { format: "long-form", at: 0.2, text: "Printing Prediction System", underline: 1 })
 *   -> { dur, words: [span…] }
 * Type: 104 px (9.6 % of frame height; long-form glow titles are 9–12 % H). */
(function (root) {
  "use strict";
  var NODE = typeof module !== "undefined" && module.exports;
  var K = NODE ? require("./kit.js") : root.HFKit;
  var P = NODE ? require("../profile.js") : root.HFProfile;
  var X = NODE ? require("../text.js") : root.HFText;
  var M = NODE ? require("../marks.js") : root.HFMarks;

  // A double-pass scribble (out and back), drawn in screen pixels: the svg's viewBox is the word's own
  // pixel box (user unit == screen px), so getTotalLength() is the on-screen length and the dash
  // sweep (HFMarks.draw) covers the whole tween. No vector-effect, no stretched viewBox.
  function scribble(w, h, seed) {
    return M.scribblePath(0.02 * w, 0.4 * h, 0.96 * w, seed) + M.scribblePath(0.985 * w, 0.65 * h, -0.95 * w, seed + 2).replace(/^M/, " L");
  }
  // The word's laid-out width. A scene that starts later in the reel is still display:none while the
  // timeline is built (offsetWidth 0): measure an off-screen clone with the same type instead, or the
  // viewBox collapses to 1 px and the scribble stretches into a full-width bar.
  function wordWidth(word) {
    if (word.offsetWidth) return word.offsetWidth;
    if (typeof document === "undefined" || !document.body || typeof getComputedStyle !== "function") return 1;
    var cs = getComputedStyle(word), probe = document.createElement("span");
    probe.textContent = word.textContent;
    ["fontFamily", "fontSize", "fontWeight", "fontStyle", "letterSpacing", "textTransform"].forEach(function (k) { probe.style[k] = cs[k]; });
    probe.style.cssText += ";position:absolute;left:-9999px;top:0;visibility:hidden;white-space:pre";
    document.body.appendChild(probe);
    var w = (probe.getBoundingClientRect && probe.getBoundingClientRect().width) || 1;
    if (probe.parentNode && probe.parentNode.removeChild) probe.parentNode.removeChild(probe);
    return w;
  }
  function underline(tl, word, T, lf) {
    var fs = (typeof getComputedStyle === "function" && parseFloat(getComputedStyle(word).fontSize)) || 104;
    var ww = wordWidth(word), w = Math.round(ww * 1.04), h = Math.round(0.32 * fs);   // css: left -2 %, width 104 %, height 0.32 em
    var box = K.svg("svg", { "class": "hf-kit-underline", viewBox: "0 0 " + w + " " + h, preserveAspectRatio: "none" }, word);
    var path = K.svg("path", { d: scribble(w, h, 3) }, box);
    var dur = M.sweepDuration(ww, lf.frameHeight, lf.format);
    M.draw(tl, path, T, dur, lf);
    return dur;
  }

  function glowCenter(tl, host, opts) {
    var b = K.begin("title", host, opts), T = b.at;
    if (typeof opts.text !== "string" || !opts.text.trim()) throw new Error("HFKit.title: opts.text is required");
    var nWords = opts.text.trim().split(/\s+/).length;
    if (opts.underline != null && !(Number.isInteger(opts.underline) && opts.underline >= 0 && opts.underline < nWords))
      throw new Error("HFKit.title: underline " + opts.underline + " is not a word index (0–" + (nWords - 1) + ")");
    var g = K.ground(host, { ambient: b.mode === "dark", quiet: true });
    var line = K.el("div", "hf-kit-title hf-kit-headline", host, opts.text.trim().replace(/\s+/g, " "));
    var spans, dur;
    if (b.mode === "dark") {
      spans = X.splitWords(line);
      X.defocus(tl, g.grid, T, b.lf);
      dur = X.glowTitle(tl, spans, T, Object.assign({ intensity: K.GLOW }, b.lf));
    } else {
      dur = X.words(tl, line, T, Object.assign({ onSpans: function (s) { spans = s; } }, b.lf));
    }
    spans.forEach(function (s) { s.classList.add("hf-kit-word"); });
    if (opts.underline != null) {
      var w = spans[opts.underline];
      if (!w) throw new Error("HFKit.title: underline " + opts.underline + " is not a word index (0–" + (spans.length - 1) + ")");
      var gap = P.timing(b.lf.format).chainGap;
      dur += gap + underline(tl, w, T + dur + gap, b.lf);
    }
    return { dur: dur, words: spans };
  }

  K.register("title", "glow-center", glowCenter, [
    ".hf-kit-title{position:absolute;left:0;right:0;top:478px;text-align:center;font-size:104px;line-height:1.2;letter-spacing:0.005em}"
  ].join("\n"));
})(typeof window !== "undefined" ? window : this);
