/* ============================================================================
 * HFProfile — the format profiles' closed easing tables and timing values, as code
 * ----------------------------------------------------------------------------
 * Source of truth: standards/formats/long-form.md and standards/formats/shorts.md.
 * lib/test/profile.test.js fails if a value here drifts from those tables.
 *
 * Every ease is a PURE function p -> eased p (no GSAP needed, so node tests can run
 * it). GSAP accepts an ease function directly: { ease: HFProfile.ease("long-form", "ease.camera") }.
 * Asking for a token the format does not define throws: the vocabulary is closed.
 * ==========================================================================*/
(function (root) {
  "use strict";

  // Deterministic cubic-bezier solver: bisection on x (24 iterations), then y. Pure function of p.
  function bezier(x1, y1, x2, y2) {
    function bx(u) { return 3 * u * (1 - u) * (1 - u) * x1 + 3 * u * u * (1 - u) * x2 + u * u * u; }
    function by(u) { return 3 * u * (1 - u) * (1 - u) * y1 + 3 * u * u * (1 - u) * y2 + u * u * u; }
    return function (p) {
      if (p <= 0) return 0; if (p >= 1) return 1;
      var lo = 0, hi = 1, u;
      for (var i = 0; i < 24; i++) { u = (lo + hi) / 2; if (bx(u) < p) lo = u; else hi = u; }
      return by((lo + hi) / 2);
    };
  }

  // GSAP's named eases as pure functions. NB GSAP numbering: power2 = cubic, power3 = quartic.
  var NAMED = {
    "power2.out": function (p) { return 1 - Math.pow(1 - p, 3); },
    "power3.out": function (p) { return 1 - Math.pow(1 - p, 4); },
    "sine.inOut": function (p) { return -(Math.cos(Math.PI * p) - 1) / 2; },
    "expo.out": function (p) { return p >= 1 ? 1 : 1 - Math.pow(2, -10 * p); }
  };
  var CUBIC = /^cubic-bezier\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)$/;

  function compile(spec) {
    var m = CUBIC.exec(spec);
    if (m) return bezier(+m[1], +m[2], +m[3], +m[4]);
    if (NAMED[spec]) return NAMED[spec];
    throw new Error("HFProfile: cannot compile ease spec " + JSON.stringify(spec));
  }

  // Closed ease tables, copied from the profiles. A value starting with "ease." is an alias.
  var EASES = {
    "long-form": {
      "ease.camera": "cubic-bezier(0.32, 0, 0.18, 1)",
      "ease.camera.slow": "sine.inOut",
      "ease.enter": "power3.out",
      "ease.sweep": "cubic-bezier(0.47, 0.15, 0.2, 0.95)",
      "ease.cut": "ease.camera",
      "ease.glow": "expo.out",
      "ease.card": "power2.out"
    },
    "shorts": {
      "ease.camera": "cubic-bezier(0.65, 0, 0.35, 1)",
      "ease.cut": "cubic-bezier(0.65, 0, 0.35, 1)",
      "ease.enter": "power3.out",
      "ease.sweep": "cubic-bezier(0.47, 0.15, 0.2, 0.95)"
    }
  };

  // Timing values the lib binders use. Measured values cite the profile; "lib default" = not measured.
  var TIMING = {
    "long-form": {
      words: { dur: 0.6, stagger: 0.28, staggerRange: [0.23, 0.33], riseFrac: 0.07, blurFrac: 8 / 1080 },  // blurFrac: lib default
      glow: { pop: 0.7, settle: 0.4, nextWord: 0.43, haloFrac: 84 / 1080 },
      defocus: { sigmaFrac: 4.5 / 1080, brightness: 0.6, dur: 0.5 },
      sweep: { pxPerSecPerH: 360 / 720, min: 0.5, max: 1.0 },
      chip: { dur: 0.5, riseFrac: 0.03 },
      swap: 0.133,
      scriptMsPerChar: 135,
      typeOnMsPerChar: null          // long-form text is word by word; a UI type-on must pass msPerChar
    },
    "shorts": {
      words: { dur: 0.26, stagger: 0.2, staggerRange: null, riseFrac: 16 / 1920, blurFrac: 6 / 1920 },
      glow: null,                    // glow title is long-form only
      defocus: null,
      sweep: { pxPerSecPerH: 360 / 720, min: 0.5, max: 1.0 },   // provisional, carried from long-form
      chip: { dur: 0.3, riseFrac: 34 / 1920, seed: 0.05, expand: 0.167 },
      swap: 0.133,
      scriptMsPerChar: 67,
      typeOnMsPerChar: 67,
      wipe: { inDur: 0.42, outDur: 0.36, blurIn: 14, blurOut: 12, featherMin: 8, featherGain: 34 }
    }
  };

  var FORMATS = Object.keys(EASES);
  var cache = {};

  function checkFormat(format) {
    if (!EASES[format]) throw new Error("HFProfile: unknown format " + JSON.stringify(format) + " (have: " + FORMATS.join(", ") + ")");
  }
  function easeSpec(format, token) {
    checkFormat(format);
    var seen = {}, name = token;
    while (true) {
      if (!Object.prototype.hasOwnProperty.call(EASES[format], name)) {
        throw new Error("HFProfile: " + JSON.stringify(token) + " is not in the " + format + " ease table (have: " + Object.keys(EASES[format]).join(", ") + ")");
      }
      var v = EASES[format][name];
      if (v.indexOf("ease.") !== 0) return v;
      if (seen[v]) throw new Error("HFProfile: alias loop at " + v);
      seen[name] = true; name = v;
    }
  }
  // Same (format, token) -> the same function object, tagged so tests can tell profile eases apart.
  function ease(format, token) {
    var key = format + "|" + token;
    if (!cache[key]) {
      var fn = compile(easeSpec(format, token));
      var tagged = function (p) { return fn(p); };
      tagged.format = format; tagged.token = token; tagged.spec = easeSpec(format, token);
      cache[key] = tagged;
    }
    return cache[key];
  }
  function tokens(format) { checkFormat(format); return Object.keys(EASES[format]); }
  function timing(format) { checkFormat(format); return JSON.parse(JSON.stringify(TIMING[format])); }
  function isProfileEase(fn) { return typeof fn === "function" && !!fn.token && cache[fn.format + "|" + fn.token] === fn; }

  var api = { FORMATS: FORMATS, bezier: bezier, compile: compile, ease: ease, easeSpec: easeSpec,
    tokens: tokens, timing: timing, isProfileEase: isProfileEase };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  root.HFProfile = api;
})(typeof window !== "undefined" ? window : this);
