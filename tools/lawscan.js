"use strict";
/* lawscan — the core-motion-law static scanner, shared by lib/test/hygiene.test.js (ruleset "lib")
 * and tools/qa.py (ruleset "composition", QA checks 4, 5 and 6). Node built-ins only.
 *
 *   node tools/lawscan.js [--ruleset lib|composition] [--format long-form|shorts] FILE...
 *   → prints a JSON array of findings {file, line, check, message}; exit 1 if any.
 *
 * Static scanning cannot see what a script decides at runtime (a blur reason set with a computed
 * value, an ease picked from a variable). tools/qa_probe.mjs covers those in the rendered DOM.
 */
var fs = require("fs");

var MARKER = /^\/\*\s*hf-allow:\s*alpha-mask\s*\*\/$/;
var REASONS = ["focus", "glow", "wipe"];

// [pattern, check number, message, rulesets]. Check numbers follow standards/core/qa.md §1.
var RULES = [
  [/Math\.random|Date\.now|performance\.now/, 4, "non-deterministic clock/randomness (core law 1)", "lib composition"],
  [/["'`]?repeat["'`]?\s*:\s*(-1|Infinity)/, 4, "infinite repeat (core law 1)", "lib composition"],
  [/animation(?:-iteration-count)?\s*:[^;{}"'`]*\binfinite\b/i, 4, "CSS infinite animation (core law 1)", "lib composition"],
  [/(?<!url\()#(?:[0-9a-f]{3,4}|[0-9a-f]{6}|[0-9a-f]{8})(?![0-9a-z_-])/i, 0, "hard-coded colour — use brand CSS variables", "lib"],
  [/\b(rgba?|hsla?|oklch|oklab|lab|lch|hwb|color-mix)\(/i, 0, "hard-coded colour function — use brand CSS variables", "lib"],
  [/\b(back|elastic|bounce)\.(in|out|inout|ease\w*)/i, 6, "overshoot ease (core law 3)", "lib composition"],
  [/["'`]?\bease["'`]?\s*:\s*["'`](?!none["'`])/, 6, "string ease other than the driver's \"none\" — use HFProfile.ease (core law 4)", "lib composition"]
];
// Only pure black is excusable on an alpha-mask line: #000 #0000 #000000 #00000000, rgb(0,0,0), rgba(0,0,0,<alpha>).
var BLACK = /#(?:0{3,4}|0{6}|0{8})(?![0-9a-z])|\brgba?\(\s*0\s*,\s*0\s*,\s*0\s*(?:,\s*[0-9.]+\s*)?\)/gi;
// A `/` after one of these keywords starts a regex literal, not a division.
var REGEX_KEYWORD = /(?:^|[^\w$.])(?:return|typeof|case|do|else|in|of|void|yield|await|delete|throw|new)\s*$/;

// Walk JS/CSS source tracking string state, so `/*` inside a string is not a comment.
// Returns the source with comments blanked (newlines kept) and the 0-based lines of real alpha-mask markers.
function lex(raw) {
  var out = "", marks = {}, i = 0, n = raw.length, q = null, line = 0;
  while (i < n) {
    var c = raw[i], d = raw[i + 1];
    if (q) {
      out += c; if (c === "\n") line++;
      if (c === "\\") { out += d || ""; if (d === "\n") line++; i += 2; continue; }
      if (c === q) q = null;
      i++; continue;
    }
    if (c === "'" || c === '"' || c === "`") { q = c; out += c; i++; continue; }
    if (c === "/" && d === "*") {
      var end = raw.indexOf("*/", i + 2); end = end === -1 ? n : end + 2;
      var text = raw.slice(i, end);
      if (MARKER.test(text)) marks[line] = true;
      out += text.replace(/[^\n]/g, " "); line += (text.match(/\n/g) || []).length; i = end; continue;
    }
    if (c === "/" && d === "/") { while (i < n && raw[i] !== "\n") { out += " "; i++; } continue; }
    var before = out.slice(-40);
    if (c === "/" && (/[(,=:\[!&|?{};]\s*$|^\s*$/.test(before) || REGEX_KEYWORD.test(before))) {   // regex literal: skip it so a quote inside is not a string
      var j = i + 1, cls = false;
      while (j < n && raw[j] !== "\n" && (cls || raw[j] !== "/")) { if (raw[j] === "\\") j++; else if (raw[j] === "[") cls = true; else if (raw[j] === "]") cls = false; j++; }
      out += raw.slice(i, j + 1); i = j + 1; continue;
    }
    out += c; if (c === "\n") line++;
    i++;
  }
  return { src: out, marks: marks };
}

// HTML → the same text with HTML comments and the prose between tags blanked (newlines kept), so an
// apostrophe in copy never opens a "string". Tags, <script> and <style> bodies are kept verbatim.
function htmlMask(raw) {
  var re = /<!--[\s\S]*?(?:-->|$)|<(script|style)\b[^>]*>[\s\S]*?(?:<\/\1\s*>|$)|<[^>]*>?/gi, out = "", last = 0, m;
  function blank(s) { return s.replace(/[^\n]/g, " "); }
  while ((m = re.exec(raw))) {
    out += blank(raw.slice(last, m.index));
    out += m[0].indexOf("<!--") === 0 ? blank(m[0]) : m[0];
    last = re.lastIndex;
    if (m[0] === "") re.lastIndex++;
  }
  return out + blank(raw.slice(last));
}

function reasonsOn(line) {
  var out = [], re = /data-blur-reason\W{1,4}([A-Za-z]+)/g, m;
  while ((m = re.exec(line))) out.push(m[1]);
  return out;
}

/* Findings for one file. opts.ruleset: "lib" (default) or "composition"; opts.format: "long-form" |
 * "shorts" (composition only — decides whether a `wipe` reason / directional Gaussian is allowed).
 * Lib rule: a Gaussian site's data-blur-reason is on the same line or the line before. Composition:
 * also the line after (multi-line SVG tags), and literal reason values are checked. */
function scan(rel, raw, opts) {
  opts = opts || {};
  var ruleset = opts.ruleset || "lib", comp = ruleset === "composition", fmt = opts.format || "long-form";
  if (comp && fmt !== "long-form" && fmt !== "shorts") throw new Error("lawscan: format must be long-form or shorts, got " + JSON.stringify(fmt));
  var src = /\.html?$/i.test(rel) ? htmlMask(raw) : raw;
  var out = [], lx = lex(src), lines = lx.src.split("\n"), tagUsed = {};
  function hit(i, check, message) { out.push({ file: rel, line: i + 1, check: check, message: message }); }
  function free(i) { return i < 0 || i >= lines.length ? 0 : (lines[i].match(/data-blur-reason/g) || []).length - (tagUsed[i] || 0); }
  lines.forEach(function (line, i) {
    RULES.forEach(function (r) {
      if (r[3].split(" ").indexOf(ruleset) === -1) return;
      var l = r[1] === 0 && lx.marks[i] ? line.replace(BLACK, "") : line;
      if (r[0].test(l)) hit(i, r[1], r[2]);
    });
    if (rel !== "profile.js" && /cubic-bezier\(/.test(line)) hit(i, 6, "raw cubic-bezier outside profile.js (core law 4)");
    var sites = (line.match(/(^|[^A-Za-z.])blur\(|<feGaussianBlur|backdrop-filter|backdropFilter/g) || []).length;
    for (var s = 0; s < sites; s++) {
      var spot = [i - 1, i].concat(comp ? [i + 1] : []).filter(function (k) { return free(k) > 0; })[0];
      if (spot === undefined) hit(i, 5, "Gaussian site without its own data-blur-reason (same line or line before" + (comp ? " or after" : "") + ")");
      else tagUsed[spot] = (tagUsed[spot] || 0) + 1;
    }
    if (!comp) return;
    reasonsOn(line).forEach(function (r) {
      if (REASONS.indexOf(r) === -1) hit(i, 5, "data-blur-reason \"" + r + "\" is not focus, glow or wipe");
      else if (r === "wipe" && fmt !== "shorts") hit(i, 5, "data-blur-reason \"wipe\" is Shorts-only (wipe feather and element smear)");
    });
    var sd = /stdDeviation\s*=\s*["']\s*([\d.]+)[\s,]+([\d.]+)\s*["']/.exec(line);
    if (sd && fmt === "long-form" && parseFloat(sd[1]) !== parseFloat(sd[2])) {
      hit(i, 5, "directional Gaussian (stdDeviation \"" + sd[1] + " " + sd[2] + "\") is movement blur — use HFMotionBlur");
    }
  });
  return out;
}

function format(f) { return f.file + ":" + f.line + ": " + f.message; }

function cli(argv, io) {
  var opts = { ruleset: "lib" }, files = [];
  for (var i = 0; i < argv.length; i++) {
    if (argv[i] === "--ruleset") opts.ruleset = argv[++i];
    else if (argv[i] === "--format") opts.format = argv[++i];
    else files.push(argv[i]);
  }
  if (!files.length || ["lib", "composition"].indexOf(opts.ruleset) === -1) {
    io.err("usage: node tools/lawscan.js [--ruleset lib|composition] [--format long-form|shorts] FILE...\n");
    return 2;
  }
  var found = [];
  try {
    files.forEach(function (f) { found = found.concat(scan(f, fs.readFileSync(f, "utf8"), opts)); });
  } catch (e) { io.err(e.message + "\n"); return 2; }
  io.out(JSON.stringify(found, null, 1) + "\n");
  return found.length ? 1 : 0;
}

module.exports = { lex: lex, htmlMask: htmlMask, scan: scan, format: format, cli: cli, RULES: RULES, REASONS: REASONS };
if (require.main === module) {
  process.exitCode = cli(process.argv.slice(2), { out: function (s) { process.stdout.write(s); }, err: function (s) { process.stderr.write(s); } });
}
