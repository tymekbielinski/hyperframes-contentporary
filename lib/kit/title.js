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

  // A double-pass scribble (out and back) in a 1000 × 40 box, stretched under its word.
  function scribble(seed) {
    return M.scribblePath(20, 16, 960, seed) + M.scribblePath(985, 26, -950, seed + 2).replace(/^M/, " L");
  }
  function underline(tl, word, T, lf) {
    var box = K.svg("svg", { "class": "hf-kit-underline", viewBox: "0 0 1000 40", preserveAspectRatio: "none" }, word);
    var path = K.svg("path", { d: scribble(3) }, box);
    var dur = M.sweepDuration(word.offsetWidth || 1, lf.frameHeight, lf.format);
    M.draw(tl, path, T, dur, lf);
    return dur;
  }

  function glowCenter(tl, host, opts) {
    var b = K.begin("title", host, opts), T = b.at;
    if (typeof opts.text !== "string" || !opts.text.trim()) throw new Error("HFKit.title: opts.text is required");
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
