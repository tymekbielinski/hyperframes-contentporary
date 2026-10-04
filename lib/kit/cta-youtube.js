/* HFKit.ctaYoutube — variant "watch-page-dive" (the long-form CTA template).
 * The face footage scales to 0.80 into a YouTube watch-page player (0.5 s) → the camera dives 2× to
 * the description link (0.6 s) → holds 1.7 s → reverses: back to the player (0.6 s), holds 0.5 s,
 * scales back up to the full-frame face (0.5 s). Every CTA in a video is identical (long-form.md).
 * Core law 7: this is the one long-form graphic that transforms the footage instead of cutting.
 * Core law 9: the watch page is a REAL screenshot (the brand's own channel page, recorded in
 * assets/captures/MANIFEST.md) — the kit never draws or restyles platform UI.
 * The camera is a DOM camera (HFCamera.rig without a blur canvas): live footage cannot be baked into
 * a blur texture yet, and long-form ordinary legs read as no blur.
 * Both grounds look the same (no glow to drop); data-hf-mode is still required.
 *
 *   HFKit.ctaYoutube(tl, host, { format: "long-form", at: 0, footage: videoEl,
 *     page: { src: "assets/captures/watch-page.png", width: 2560, height: 1440,
 *             player: [x, y, w, h], link: [x, y, w, h] } })          // rects in page pixels
 *   -> { dur, poses: { face, player, link } }  */
(function (root) {
  "use strict";
  var NODE = typeof module !== "undefined" && module.exports;
  var K = NODE ? require("./kit.js") : root.HFKit;
  var P = NODE ? require("../profile.js") : root.HFProfile;
  var C = NODE ? require("../camera.js") : root.HFCamera;
  var X = NODE ? require("../text.js") : root.HFText;

  var PLAYER_HOLD = 0.5;   // hold at 0.80 before the dive and after the return (measured 0.5 s)

  function rect(r, name, page) {
    if (!Array.isArray(r) || r.length !== 4 || !r.every(function (v) { return typeof v === "number" && isFinite(v); }) || !(r[2] > 0 && r[3] > 0)) {
      throw new Error("HFKit.ctaYoutube: page." + name + " must be [x, y, w, h] in page pixels");
    }
    if (page && !(r[0] >= 0 && r[1] >= 0 && r[0] + r[2] <= page.width && r[1] + r[3] <= page.height)) {
      throw new Error("HFKit.ctaYoutube: page." + name + " must lie inside the page");
    }
    return { x: r[0], y: r[1], w: r[2], h: r[3] };
  }

  // The four camera poses, in page pixels. Pure: tests and later CTAs reuse it.
  function poses(page, frame, c) {
    var pl = rect(page.player, "player", page), ln = rect(page.link, "link", page);
    var zFace = Math.max(frame.width / pl.w, frame.height / pl.h);
    var face = { cx: pl.x + pl.w / 2, cy: pl.y + pl.h / 2, z: zFace };
    var player = { cx: face.cx, cy: face.cy, z: zFace * c.scale };
    var link = { cx: ln.x + ln.w / 2, cy: ln.y + ln.h / 2, z: player.z * c.dive };
    return { face: face, player: player, link: link };
  }

  function watchPageDive(tl, host, opts) {
    var b = K.begin("cta-youtube", host, opts), T = b.at, c = P.timing(b.lf.format).cta;
    var page = opts.page || {};
    if (typeof page.src !== "string" || !(page.width > 0 && page.height > 0)) throw new Error("HFKit.ctaYoutube: page needs src, width and height (a real watch-page screenshot)");
    if (!opts.footage || typeof opts.footage.appendChild !== "function") throw new Error("HFKit.ctaYoutube: opts.footage must be the face <video> (or a still) element");
    var p = poses(page, K.FRAME, c), pl = rect(page.player, "player", page);
    var stage = K.el("div", "hf-kit-cta-stage", host);
    stage.style.width = page.width + "px"; stage.style.height = page.height + "px";
    stage.setAttribute("data-layout-allow-overflow", "");   // the page is larger than the frame on purpose
    var img = K.el("img", "hf-kit-cta-page", stage);
    img.setAttribute("src", page.src); img.setAttribute("alt", "");
    img.style.width = page.width + "px"; img.style.height = page.height + "px";
    var slot = K.el("div", "hf-kit-cta-player", stage);
    slot.style.left = pl.x + "px"; slot.style.top = pl.y + "px"; slot.style.width = pl.w + "px"; slot.style.height = pl.h + "px";
    slot.appendChild(opts.footage);
    opts.footage.classList.add("hf-kit-cta-footage");
    [img, slot].forEach(function (e) { e.setAttribute("data-layout-allow-overlap", ""); e.setAttribute("data-layout-allow-occlusion", ""); });
    if (typeof img.decode === "function") X.track(img.decode());
    var t1 = c.scaleDur, t2 = t1 + PLAYER_HOLD, t3 = t2 + c.diveDur, t4 = t3 + c.hold, t5 = t4 + c.diveDur, t6 = t5 + PLAYER_HOLD, t7 = t6 + c.scaleDur;
    function key(t, q) { return { t: t, cx: q.cx, cy: q.cy, z: q.z }; }
    C.rig(tl, { format: b.lf.format, width: K.FRAME.width, height: K.FRAME.height, stage: stage, at: T, dur: t7,
      keys: [key(0, p.face), key(t1, p.player), key(t2, p.player), key(t3, p.link), key(t4, p.link), key(t5, p.player), key(t6, p.player), key(t7, p.face)] });
    return { dur: t7, poses: p };
  }

  K.register("cta-youtube", "watch-page-dive", watchPageDive, [
    ".hf-kit-cta-stage{position:absolute;left:0;top:0}",
    ".hf-kit-cta-page{position:absolute;left:0;top:0;display:block}",
    ".hf-kit-cta-player{position:absolute;overflow:hidden}",
    ".hf-kit-cta-footage{position:absolute;left:0;top:0;width:100%;height:100%;object-fit:cover}"
  ].join("\n"));
  K.ctaPoses = poses;
})(typeof window !== "undefined" ? window : this);
