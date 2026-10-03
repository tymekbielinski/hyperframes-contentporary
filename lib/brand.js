/* ============================================================================
 * HFBrand — brand tokens + chosen palette + chosen headline font -> CSS variables
 * ----------------------------------------------------------------------------
 * Reads the Plan 1 schema (brands/<name>/tokens.json, palettes/<p>.json; validated by
 * tools/brandcheck.py). Every palette role becomes --hf-<role>-<sub> (camelCase -> kebab):
 *   ground.deep -> --hf-ground-deep · surface.fillAlt -> --hf-surface-fill-alt ·
 *   accentScript -> --hf-accent-script · status.ok -> --hf-status-ok · extras.glowHalo -> --hf-extras-glow-halo
 * Mode: palette.mode ("dark" | "light", brandcheck.PALETTE_MODES) is not a role and not a CSS variable;
 *   HFBrand.mode(palette) reads it, apply() writes it to the root as data-hf-mode.
 * Fonts: --hf-font-headline(-weight), --hf-font-body(-weight), --hf-font-script, --hf-font-captions(-weight).
 * Layout: --hf-card-radius, --hf-stat-radius, --hf-frame-padding (px at 1080, times opts.scale).
 *
 * Two ways to use it, both deterministic (no fetch in the render path):
 *   build time:  node lib/brand.js brands/<name> --palette red [--font geometric]
 *                [--override accentScript=#BACE7A] [--scale 1] [--json] > brand.css
 *   in the page: HFBrand.apply(document.documentElement, HFBrand.cssVars(tokens, palette, choice))
 * ==========================================================================*/
(function (root) {
  "use strict";

  // Must equal PALETTE_ROLES in tools/brandcheck.py (tools/test_lib_brand.py enforces it).
  var ROLES = {
    ground: ["deep", "centre", "grid", "dots"],
    surface: ["fill", "fillAlt", "bevel", "halo"],
    text: ["primary", "secondary"],
    accent: ["block", "text", "glow", "line"],
    accentScript: null,
    status: ["ok", "x"]
  };
  // Must equal PALETTE_MODES in tools/brandcheck.py (tools/test_lib_brand.py enforces it).
  var MODES = ["dark", "light"];
  var HEX = /^#[0-9A-Fa-f]{6}$/, RGBA = /^rgba\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*(0|1|0?\.\d+)\s*\)$/;

  function isColour(v) { return typeof v === "string" && (HEX.test(v) || RGBA.test(v)); }
  function kebab(s) { return s.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase(); }
  function varName(path) { return "--hf-" + path.split(".").map(kebab).join("-"); }
  function rolePaths() {
    var out = [];
    Object.keys(ROLES).forEach(function (r) {
      if (ROLES[r] === null) out.push(r); else ROLES[r].forEach(function (s) { out.push(r + "." + s); });
    });
    return out;
  }
  function get(obj, path) {
    return path.split(".").reduce(function (o, k) { return o && Object.prototype.hasOwnProperty.call(o, k) ? o[k] : undefined; }, obj);
  }
  function quote(family) { return '"' + String(family).replace(/"/g, "") + '"'; }

  // Same rule and message shape as brandcheck.validate_palette; returns the mode or throws.
  function modeProblem(palette) {
    var label = palette.name || "palette";
    if (!Object.prototype.hasOwnProperty.call(palette, "mode")) return label + ": missing mode";
    if (MODES.indexOf(palette.mode) === -1) return label + ": mode must be 'dark' or 'light', got '" + palette.mode + "'";
    return null;
  }
  function mode(palette) {
    var p = modeProblem(palette);
    if (p) throw new Error("HFBrand: " + p);
    return palette.mode;
  }

  // choice = { font?: headline key (default tokens.fonts.defaultHeadline), overrides?: {path: colour}, scale?: number }
  function cssVars(tokens, palette, choice) {
    choice = choice || {};
    var name = tokens.name || "brand", errors = [];
    if (palette.name && (tokens.palettes || []).indexOf(palette.name) === -1) errors.push("palette " + JSON.stringify(palette.name) + " is not listed in brand " + name);
    var modeErr = modeProblem(palette);
    if (modeErr) errors.push(modeErr);
    var overrides = choice.overrides || {}, paths = rolePaths();
    Object.keys(overrides).forEach(function (p) {
      if (paths.indexOf(p) === -1) errors.push("override " + JSON.stringify(p) + " is not a palette role");
      else if (!isColour(overrides[p])) errors.push("override " + JSON.stringify(p) + " is not a colour: " + JSON.stringify(overrides[p]));
    });
    var vars = {};
    paths.forEach(function (p) {
      var v = Object.prototype.hasOwnProperty.call(overrides, p) ? overrides[p] : get(palette, p);
      if (v === undefined) errors.push((palette.name || "palette") + ": missing " + p);
      else if (!isColour(v)) errors.push((palette.name || "palette") + ": " + p + " is not a colour: " + JSON.stringify(v));
      else vars[varName(p)] = v;
    });
    Object.keys(palette.extras || {}).forEach(function (k) {
      var v = palette.extras[k];
      if (!isColour(v)) errors.push((palette.name || "palette") + ": extras." + k + " is not a colour: " + JSON.stringify(v));
      else vars[varName("extras." + k)] = v;
    });
    var fonts = tokens.fonts || {}, headline = fonts.headline || {};
    var key = choice.font || fonts.defaultHeadline;
    if (!Object.prototype.hasOwnProperty.call(headline, key)) errors.push("font " + JSON.stringify(key) + " not in brand " + name + " (have: " + Object.keys(headline).join(", ") + ")");
    if (errors.length) throw new Error("HFBrand: " + errors.join("; "));
    vars["--hf-font-headline"] = quote(headline[key].family) + ", system-ui, sans-serif";
    vars["--hf-font-headline-weight"] = String(headline[key].weight);
    if (fonts.body) { vars["--hf-font-body"] = quote(fonts.body.family) + ", system-ui, sans-serif"; vars["--hf-font-body-weight"] = String(fonts.body.weight); }
    if (fonts.script) vars["--hf-font-script"] = quote(fonts.script.family) + ", cursive";
    if (fonts.captions) { vars["--hf-font-captions"] = quote(fonts.captions.family) + ", system-ui, sans-serif"; if (fonts.captions.weight) vars["--hf-font-captions-weight"] = String(fonts.captions.weight); }
    var layout = tokens.layout || {}, scale = choice.scale == null ? 1 : choice.scale;
    [["cardRadiusPx1080", "--hf-card-radius"], ["statRadiusPx1080", "--hf-stat-radius"], ["shortsFramePaddingPx1080x1920", "--hf-frame-padding"]].forEach(function (m) {
      if (typeof layout[m[0]] === "number") vars[m[1]] = +(layout[m[0]] * scale).toFixed(2) + "px";
    });
    // Carried for apply(); non-enumerable so it never shows up as a CSS variable, in toCss or in --json.
    Object.defineProperty(vars, "hfMode", { value: palette.mode, enumerable: false });
    return vars;
  }
  function toCss(vars, selector) {
    return (selector || ":root") + " {\n" + Object.keys(vars).map(function (k) { return "  " + k + ": " + vars[k] + ";"; }).join("\n") + "\n}\n";
  }
  // "#RRGGBB" or "rgb(a)(r,g,b[,a])" -> [r, g, b, a] in 0..1 — the bg format HFMotionBlur / HFCamera take.
  function toGl(colour) {
    var c = String(colour).trim(), m;
    if (HEX.test(c)) return [parseInt(c.slice(1, 3), 16) / 255, parseInt(c.slice(3, 5), 16) / 255, parseInt(c.slice(5, 7), 16) / 255, 1];
    m = /^rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*(?:,\s*([\d.]+)\s*)?\)$/.exec(c);
    if (m) return [m[1] / 255, m[2] / 255, m[3] / 255, m[4] == null ? 1 : +m[4]];
    throw new Error("HFBrand.toGl: not a colour: " + JSON.stringify(colour));
  }
  // Sets every variable on el.style and, when vars came from cssVars(), data-hf-mode="dark|light" on el.
  function apply(el, vars) {
    Object.keys(vars).forEach(function (k) { el.style.setProperty(k, vars[k]); });
    if (vars.hfMode) el.setAttribute("data-hf-mode", vars.hfMode);
    return el;
  }

  // node lib/brand.js <brandDir> --palette <p> [--font <k>] [--override path=value]... [--scale n] [--json]
  function cli(argv, io) {
    var fs = require("fs"), path = require("path");
    var args = { overrides: {} }, rest = [];
    for (var i = 0; i < argv.length; i++) {
      var a = argv[i];
      if (a === "--palette") args.palette = argv[++i];
      else if (a === "--font") args.font = argv[++i];
      else if (a === "--scale") args.scale = parseFloat(argv[++i]);
      else if (a === "--json") args.json = true;
      else if (a === "--override") { var kv = argv[++i], eq = kv.indexOf("="); args.overrides[kv.slice(0, eq)] = kv.slice(eq + 1); }
      else rest.push(a);
    }
    if (rest.length !== 1 || !args.palette) { io.err("usage: node lib/brand.js brands/<name> --palette <p> [--font <k>] [--override path=#RRGGBB] [--scale n] [--json]\n"); return 2; }
    try {
      var dir = rest[0], tokens = JSON.parse(fs.readFileSync(path.join(dir, "tokens.json"), "utf8"));
      var pfile = path.join(dir, "palettes", args.palette + ".json");
      if (!fs.existsSync(pfile)) throw new Error("HFBrand: palette " + JSON.stringify(args.palette) + " has no file " + pfile);
      var vars = cssVars(tokens, JSON.parse(fs.readFileSync(pfile, "utf8")), { font: args.font, overrides: args.overrides, scale: args.scale });
      io.out(args.json ? JSON.stringify(vars, null, 2) + "\n" : toCss(vars));
      return 0;
    } catch (e) { io.err(e.message + "\n"); return 1; }
  }

  var api = { ROLES: ROLES, MODES: MODES, mode: mode, rolePaths: rolePaths, varName: varName, isColour: isColour, cssVars: cssVars, toCss: toCss, toGl: toGl, apply: apply, cli: cli };
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
    if (require.main === module) {
      process.exitCode = cli(process.argv.slice(2), { out: function (s) { process.stdout.write(s); }, err: function (s) { process.stderr.write(s); } });
    }
  }
  root.HFBrand = api;
})(typeof window !== "undefined" ? window : this);
