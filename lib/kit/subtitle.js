/* HFKit.subtitle — variant "glass-pill-script" (template still: step card).
 * A "Step 1" script kicker over a title in a glass pill, centred on the grid ground.
 * Dark ground: dark glass pill (bevelled light rim, faint halo), title in accent.text with
 * HFText.glowTitle. Light ground: frosted white glass, title in dark text.primary (HFText.words)
 * with an accent.block marker sweeping behind it — no glow.
 * Motion: pill card entrance (0.43 s ease.card) → script write-on at +0.3 s (135 ms/letter) →
 * title one chain gap (≈ 0.475 s) after the kicker starts.
 *
 *   HFKit.subtitle(tl, host, { format: "long-form", at: 0.2, kicker: "Step 1", title: "HIT Prediction" })
 *   -> { dur, pill, kicker: [letter span…], words: [span…] }
 * Pill ≥ 40 % of frame width, centred at 50 % / 50 %; kicker 72 px (6.7 % H); title 92 px (8.5 % H). */
(function (root) {
  "use strict";
  var NODE = typeof module !== "undefined" && module.exports;
  var K = NODE ? require("./kit.js") : root.HFKit;
  var P = NODE ? require("../profile.js") : root.HFProfile;
  var X = NODE ? require("../text.js") : root.HFText;
  var M = NODE ? require("../marks.js") : root.HFMarks;

  var KICKER_LEAD = 0.3;   // the kicker starts writing 0.3 s into the card entrance

  function glassPillScript(tl, host, opts) {
    var b = K.begin("subtitle", host, opts), T = b.at, t = P.timing(b.lf.format);
    var titleText = K.text(opts.title, b.who, "title");
    var kickerText = opts.kicker == null || opts.kicker === "" ? null : K.text(opts.kicker, b.who, "kicker");
    K.ground(host, {});
    var row = K.el("div", "hf-kit-sub-row", host);
    var pill = K.el("div", "hf-kit-glass hf-kit-sub-pill", row);
    var kicker = kickerText ? K.el("div", "hf-kit-script hf-kit-sub-kicker", pill, kickerText) : null;
    var title = K.el("div", "hf-kit-headline hf-kit-sub-title", pill, titleText);
    var dur = K.cardIn(tl, pill, T), letters = [], words = [];
    if (kicker) dur = Math.max(dur, KICKER_LEAD + M.scriptWord(tl, kicker, T + KICKER_LEAD, Object.assign({ onSpans: function (s) { letters = s; } }, b.lf)));
    var tT = T + (kicker ? KICKER_LEAD + t.chainGap : t.card.dur);
    if (b.mode === "dark") {
      words = X.splitWords(title);
      dur = Math.max(dur, tT - T + X.glowTitle(tl, words, tT, Object.assign({ intensity: K.GLOW }, b.lf)));
    } else {
      var wd = X.words(tl, title, tT, Object.assign({ onSpans: function (s) { words = s; } }, b.lf));
      var marker = K.el("div", "hf-kit-marker", title);
      var mT = tT + wd + t.chainGap;
      // The empty marker has no box to measure (0 in a display:none scene): size the sweep by the title plus the
      // marker's ±0.12em extension (css .hf-kit-marker left/right -0.12em).
      var fs = (typeof getComputedStyle === "function" && parseFloat(getComputedStyle(title).fontSize)) || 92;
      dur = Math.max(dur, mT - T + M.highlight(tl, marker, mT, Object.assign({ width: X.measureWidth(title) + 0.24 * fs }, b.lf)));
    }
    return { dur: dur, pill: pill, kicker: letters, words: words };
  }

  K.register("subtitle", "glass-pill-script", glassPillScript, [
    ".hf-kit-sub-row{position:absolute;left:0;right:0;top:404px;text-align:center}",
    ".hf-kit-sub-pill{position:relative;display:inline-block;min-width:770px;padding:34px 96px 40px;text-align:center}",
    ".hf-kit-sub-kicker{font-size:72px;line-height:1.15;margin-bottom:2px}",
    ".hf-kit-sub-title{position:relative;font-size:92px;line-height:1.3;z-index:0}",
    ".hf-kit-dark .hf-kit-sub-title{color:var(--hf-accent-text)}"
  ].join("\n"));
})(typeof window !== "undefined" ? window : this);
