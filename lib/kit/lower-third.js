/* HFKit.lowerThird — variant "key-line" (template still: lower third key line).
 * Over-footage layout: ONE key line, bottom-centre, word by word (the long-form word entrance).
 * This is the only on-screen text for spoken words in long-form (no captions — standards/formats/long-form.md).
 * Dark ground: white→warm gradient text (text.primary → accent.text, continuous across the words).
 * Light ground: dark text.primary on a frosted white glass pill (card entrance) — no gradient, no glow.
 * opts.out: when the line has faded out (fade 0.43 s on ease.enter ends at opts.out).
 *
 *   HFKit.lowerThird(tl, host, { format: "long-form", at: 0.3, text: "and I've helped online entrepreneurs", out: 3.2 })
 *   -> { dur, words: [span…] }
 * Type: 50 px body font (4.6 % H); baseline ≈ 95 % of frame height, centred. */
(function (root) {
  "use strict";
  var NODE = typeof module !== "undefined" && module.exports;
  var K = NODE ? require("./kit.js") : root.HFKit;
  var P = NODE ? require("../profile.js") : root.HFProfile;
  var X = NODE ? require("../text.js") : root.HFText;

  var PILL_LEAD = 0.15;   // light ground: words start 0.15 s after the pill starts entering

  function keyLine(tl, host, opts) {
    var b = K.begin("lower-third", host, opts), T = b.at;
    if (typeof opts.text !== "string" || !opts.text.trim()) throw new Error("HFKit.lowerThird: opts.text is required");
    var rootEl = K.el("div", "hf-kit-lt", host);
    var line = K.el("div", "hf-kit-body hf-kit-lt-line", rootEl, opts.text.trim().replace(/\s+/g, " "));
    var words = [], dur = 0, wT = T;
    if (b.mode === "light") { K.cardIn(tl, line, T); wT = T + PILL_LEAD; }
    dur = wT - T + X.words(tl, line, wT, Object.assign({ onSpans: function (s) { words = s; } }, b.lf));
    if (b.mode === "dark") {
      // One gradient across the whole line: each word shows its own slice (positions re-measured once fonts land).
      var paint = function (known) {
        var W = known || X.measureWidth(line, paint) || 1;
        words.forEach(function (s) { s.style.backgroundSize = W + "px 100%"; s.style.backgroundPosition = (-(s.offsetLeft || 0)) + "px 0px"; });
      };
      words.forEach(function (s) { s.classList.add("hf-kit-lt-word"); });
      paint();
      if (typeof document !== "undefined" && document.fonts && document.fonts.ready) X.track(document.fonts.ready.then(function () { paint(); }));
    }
    if (opts.out != null) {
      var fade = P.timing(b.lf.format).card.dur;
      if (!(opts.out - fade >= T + dur)) throw new Error("HFKit.lowerThird: opts.out (" + opts.out + " s) leaves no hold — the line lands at " + (T + dur).toFixed(2) + " s and fades for " + fade + " s");
      K.fadeOut(tl, rootEl, opts.out - fade);
    }
    return { dur: dur, words: words };
  }

  K.register("lower-third", "key-line", keyLine, [
    ".hf-kit-lt{position:absolute;left:0;right:0;top:962px;text-align:center}",
    ".hf-kit-lt-line{position:relative;display:inline-block;font-size:50px;line-height:1.3;letter-spacing:0.01em;white-space:nowrap}",
    ".hf-kit-lt-word{background-image:linear-gradient(90deg,var(--hf-text-primary) 0%,var(--hf-text-primary) 45%,var(--hf-accent-text) 100%);" +
      "-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;color:transparent}",
    ".hf-kit-light .hf-kit-lt-line{padding:12px 40px 14px;border-radius:var(--hf-card-radius);background:var(--hf-surface-fill);" +
      "border:1px solid var(--hf-surface-bevel);box-shadow:0 14px 40px var(--hf-surface-halo)}"
  ].join("\n"));
})(typeof window !== "undefined" ? window : this);
