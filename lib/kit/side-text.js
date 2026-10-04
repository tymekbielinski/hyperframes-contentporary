/* HFKit.sideText — variant "grid-panel-chips" (template still: side screen text).
 * Over-footage layout: a left-half panel with 1–6 numbered points; the face stays on the right.
 * Dark ground: the dark grid panel (ground + grid + dot matrix), dark glass number chips with the
 * number in accent.text, labels in text.primary with a faint halo. Light ground: a frosted white
 * glass panel, frosted chips, dark labels — no glow.
 * Motion: panel slides in 80 px + fades (0.6 s ease.enter); each point lands on its time: chip as a
 * status chip (rise + scale + fade, 0.5 s ease.enter) and its label word by word 0.1 s later.
 * items: ["Video performance", …] or [{ text, at }] — at defaults to one point every 2 chain gaps.
 * opts.out: when the panel has faded out.
 *
 *   HFKit.sideText(tl, host, { format: "long-form", at: 0.2, items: ["Video performance", "Retention", "CTR"] })
 *   -> { dur, chips: [el…], labels: [[span…]…] }
 * Panel 0–928 px (48 % W); chips 90 px at x 115, rows every 145 px from y 140; labels 48 px (4.4 % H) at x 277. */
(function (root) {
  "use strict";
  var NODE = typeof module !== "undefined" && module.exports;
  var K = NODE ? require("./kit.js") : root.HFKit;
  var P = NODE ? require("../profile.js") : root.HFProfile;
  var X = NODE ? require("../text.js") : root.HFText;
  var M = NODE ? require("../marks.js") : root.HFMarks;

  var ROW_TOP = 140, ROW_PITCH = 145, LABEL_LAG = 0.1, PANEL_DX = -80, MAX_ITEMS = 6;

  function gridPanelChips(tl, host, opts) {
    var b = K.begin("side-text", host, opts), T = b.at, t = P.timing(b.lf.format);
    var items = (opts.items || []).map(function (it) { return typeof it === "string" ? { text: it } : it; });
    if (items.length < 1 || items.length > MAX_ITEMS) throw new Error("HFKit.sideText: 1–" + MAX_ITEMS + " items, got " + items.length);
    var rootEl = K.el("div", "hf-kit-st", host);
    var panel = K.el("div", "hf-kit-st-panel", rootEl);
    if (b.mode === "dark") K.ground(panel, {});
    var dur = K.slideIn(tl, panel, T, PANEL_DX), chips = [], labels = [];
    var first = T + dur * 0.5, step = 2 * t.chainGap;
    items.forEach(function (it, i) {
      if (typeof it.text !== "string" || !it.text.trim()) throw new Error("HFKit.sideText: item " + i + " has no text");
      var at = it.at == null ? first + i * step : it.at;
      if (at < T) throw new Error("HFKit.sideText: item " + i + " lands at " + at + " s, before the panel (" + T + " s)");
      var top = ROW_TOP + i * ROW_PITCH;
      var chip = K.el("div", "hf-kit-glass hf-kit-st-chip", rootEl);
      chip.style.top = top + "px";
      K.el("span", "hf-kit-st-num", chip, String(i + 1));
      var label = K.el("div", "hf-kit-body hf-kit-st-label", rootEl, it.text.trim().replace(/\s+/g, " "));
      label.style.top = (top + 16) + "px";
      var cd = M.statusChip(tl, chip, at, b.lf), spans = [];
      var wd = X.words(tl, label, at + LABEL_LAG, Object.assign({ onSpans: function (s) { spans = s; } }, b.lf));
      chips.push(chip); labels.push(spans);
      dur = Math.max(dur, at - T + Math.max(cd, LABEL_LAG + wd));
    });
    if (opts.out != null) {
      if (!(opts.out - t.card.dur >= T + dur)) throw new Error("HFKit.sideText: opts.out (" + opts.out + " s) leaves no hold — the last point lands at " + (T + dur).toFixed(2) + " s");
      K.fadeOut(tl, rootEl, opts.out - t.card.dur);
    }
    return { dur: dur, chips: chips, labels: labels };
  }

  K.register("side-text", "grid-panel-chips", gridPanelChips, [
    ".hf-kit-st{position:absolute;inset:0}",
    ".hf-kit-st-panel{position:absolute;left:0;top:0;width:928px;height:1080px;overflow:hidden}",
    ".hf-kit-dark .hf-kit-st-panel{background:var(--hf-ground-deep)}",
    ".hf-kit-light .hf-kit-st-panel{background:var(--hf-surface-fill);border-right:1px solid var(--hf-surface-bevel);box-shadow:0 0 60px var(--hf-surface-halo)}",
    ".hf-kit-st-chip{left:115px;width:90px;height:90px;border-radius:18px;display:flex;align-items:center;justify-content:center}",
    ".hf-kit-st-num{font-family:var(--hf-font-body);font-weight:var(--hf-font-body-weight);font-size:42px;color:var(--hf-accent-text)}",
    ".hf-kit-st-label{position:absolute;left:277px;width:620px;font-size:48px;line-height:1.2;white-space:nowrap}",
    ".hf-kit-dark .hf-kit-st-label{text-shadow:0 0 22px var(--hf-surface-halo)}"
  ].join("\n"));
})(typeof window !== "undefined" ? window : this);
