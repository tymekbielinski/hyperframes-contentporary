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
  [/["'`]?(?:repeat|iterations)["'`]?\s*:\s*(-1|Infinity)/, 4, "infinite repeat (core law 1)", "lib composition"],
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
function lex(raw, mode) {
  var css = mode === "css";   // CSS: only /* */ comments, no `//` and no regex literals
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
    if (!css && c === "/" && d === "/") { while (i < n && raw[i] !== "\n") { out += " "; i++; } continue; }
    var before = out.slice(-40);
    if (!css && c === "/" && (/[(,=:\[!&|?{};]\s*$|^\s*$/.test(before) || REGEX_KEYWORD.test(before))) {   // regex literal: skip it so a quote inside is not a string
      var j = i + 1, cls = false;
      while (j < n && raw[j] !== "\n" && (cls || raw[j] !== "/")) { if (raw[j] === "\\") j++; else if (raw[j] === "[") cls = true; else if (raw[j] === "]") cls = false; j++; }
      out += raw.slice(i, j + 1); i = j + 1; continue;
    }
    out += c; if (c === "\n") line++;
    i++;
  }
  return { src: out, marks: marks };
}

// HTML → segments {kind: "prose"|"comment"|"tag"|"script"|"style", text}. Tags are matched quote-aware
// (a `>` inside an attribute value does not end the tag). A <script>/<style> body ends at the first
// `</script`/`</style` even inside a JS string — that is how browsers parse it, so what follows is prose.
function htmlSegments(raw) {
  var Q = "(?:\"[^\"]*\"|'[^']*'|[^'\">])*";
  var re = new RegExp("<!--[\\s\\S]*?(?:-->|$)|(<(script|style)\\b" + Q + ">)([\\s\\S]*?)(<\\/\\2\\s*>|$)|<" + Q + ">?", "gi");
  var segs = [], last = 0, m;
  while ((m = re.exec(raw))) {
    if (m.index > last) segs.push({ kind: "prose", text: raw.slice(last, m.index) });
    if (m[0].indexOf("<!--") === 0) segs.push({ kind: "comment", text: m[0] });
    else if (m[2]) {
      segs.push({ kind: "tag", text: m[1] }, { kind: m[2].toLowerCase(), text: m[3] });
      if (m[4]) segs.push({ kind: "tag", text: m[4] });
    } else segs.push({ kind: "tag", text: m[0] });
    last = re.lastIndex;
    if (m[0] === "") re.lastIndex++;
  }
  if (last < raw.length) segs.push({ kind: "prose", text: raw.slice(last) });
  return segs;
}

function blank(s) { return s.replace(/[^\n]/g, " "); }

// HTML → the same text with HTML comments and the prose between tags blanked (newlines kept), so an
// apostrophe in copy never opens a "string". Tags, <script> and <style> bodies are kept verbatim.
function htmlMask(raw) {
  return htmlSegments(raw).map(function (g) { return g.kind === "prose" || g.kind === "comment" ? blank(g.text) : g.text; }).join("");
}

// Mask + lex an HTML document: `//` comments and regex literals exist only in <script> bodies;
// <style> bodies get CSS comments only; tags and attributes are kept verbatim.
function lexHtml(raw) {
  var out = "", marks = {}, line = 0;
  htmlSegments(raw).forEach(function (g) {
    var t = g.text;
    if (g.kind === "prose" || g.kind === "comment") out += blank(t);
    else if (g.kind === "script" || g.kind === "style") {
      var lx = lex(t, g.kind === "style" ? "css" : "js");
      out += lx.src;
      Object.keys(lx.marks).forEach(function (k) { marks[line + Number(k)] = true; });
    } else out += t;
    line += (t.match(/\n/g) || []).length;
  });
  return { src: out, marks: marks };
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
  var out = [], lx = /\.(html?|svg)$/i.test(rel) ? lexHtml(raw) : lex(raw), lines = lx.src.split("\n"), tagUsed = {};
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

module.exports = { lex: lex, htmlMask: htmlMask, lexHtml: lexHtml, scan: scan, format: format, cli: cli, RULES: RULES, REASONS: REASONS };
if (require.main === module) {
  process.exitCode = cli(process.argv.slice(2), { out: function (s) { process.stdout.write(s); }, err: function (s) { process.stderr.write(s); } });
}
