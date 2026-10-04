// qa_probe — the runtime half of QA checks 5, 6 and 10. Node ≥ 22 built-ins only (global WebSocket + fetch).
//
//   node tools/qa_probe.mjs --url URL --format long-form|shorts --chrome PATH [--width 1920 --height 1080]
//                           [--samples 24] [--timeout 30000]
//   → prints {"timelines", "tweens", "samples", "findings": [{check, message, t}], "errors": [...]} as JSON.
//   Exit 0 when the page was probed (findings or not), 2 when it could not be (message on stderr).
//
// Why a live page: lib binders set data-blur-reason with setAttribute and pick eases at runtime, so a
// static scan cannot see them. tools/qa.py serves the project through `npx hyperframes preview` (the
// HyperFrames bundler + runtime, so sub-compositions mount and timelines nest exactly as they render),
// and this script drives a headless Chrome over the DevTools protocol: it waits for the timelines to
// register (and HFText.ready()), reads every tween's ease, then seeks through the timeline and
// inspects the DOM at each sample for blur reasons and the two render-only text traps.
import { spawn } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

// Runs inside the page. Must be self-contained (it is serialised with Function.prototype.toString).
async function pageProbe(opts) {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const deadline = Date.now() + opts.timeout;
  let last = -1, stableSince = 0;
  for (;;) {   // timelines register asynchronously (sub-compositions, fonts): wait for a stable count
    const n = Object.keys(window.__timelines || {}).length;
    if (n > 0 && n === last) { if (Date.now() - stableSince > 500) break; } else { last = n; stableSince = Date.now(); }
    if (Date.now() > deadline) return { error: n ? "timelines kept changing until the timeout" : "no timeline registered on window.__timelines" };
    await sleep(100);
  }
  if (window.HFText && typeof window.HFText.ready === "function") await window.HFText.ready();

  const findings = [], keys = new Set();
  const r2 = (x) => Math.round(x * 100) / 100;
  function add(check, message, t) { const k = check + "|" + message; if (!keys.has(k)) { keys.add(k); findings.push({ check, message, t: t == null ? null : r2(t) }); } }
  function describe(el) {
    if (!el || !el.tagName) return String(el);
    let d = (el.localName || el.tagName.toLowerCase()) + (el.id ? "#" + el.id : "");
    if (!el.id && typeof el.className === "string" && el.className.trim()) d += "." + el.className.trim().split(/\s+/)[0];
    const comp = el.closest && el.closest("[data-composition-id]");
    return comp && comp !== el ? comp.getAttribute("data-composition-id") + " " + d : d;
  }
  const tls = window.__timelines, ids = Object.keys(tls);
  const HP = window.HFProfile;

  // Check 6 — every tween with a duration uses an HFProfile.ease token (or "none" on a driver tween).
  const seen = new Set();
  for (const id of ids) {
    const tl = tls[id];
    if (!tl || typeof tl.getChildren !== "function") continue;
    for (const tw of tl.getChildren(true, true, false)) {
      if (seen.has(tw)) continue;
      seen.add(tw);
      if (!(tw.duration() > 0)) continue;
      let ease = tw.vars.ease, p = tw.parent;
      while (ease === undefined && p) { ease = p.vars && p.vars.defaults ? p.vars.defaults.ease : undefined; p = p.parent; }
      const targets = typeof tw.targets === "function" ? tw.targets() : [];
      const label = `${id}: tween on ${describe(targets[0])} at ${r2(tw.startTime())} s`;
      if (ease === undefined) add(6, `${label} has no ease (GSAP's default power1.out is not in the vocabulary)`);
      else if (typeof ease === "function") { if (!(HP && HP.isProfileEase(ease))) add(6, `${label} uses an ease function that is not an HFProfile.ease token`); }
      else if (ease === "none" || ease === "linear") { if (!tw.vars.onUpdate && !(targets[0] && targets[0].id === "hf-placeholder")) add(6, `${label} is linear but is not a driver tween (drivers have onUpdate)`); }
      else add(6, `${label} uses the raw ease ${JSON.stringify(ease)} — use HFProfile.ease(format, token)`);
    }
  }

  // Seek plan: the root composition's timeline drives nested children; timelines outside it are seeked too.
  const rootEl = document.querySelector("[data-composition-id]");
  const rootId = rootEl && rootEl.getAttribute("data-composition-id");
  const rootTl = tls[rootId] || null;
  const nestedIn = (tl, anc) => { for (let p = tl.parent; p; p = p.parent) if (p === anc) return true; return false; };
  const drivers = ids.map((id) => tls[id]).filter((tl) => tl && typeof tl.seek === "function" && (tl === rootTl || !rootTl || !nestedIn(tl, rootTl)));
  const attrDur = rootEl ? parseFloat(rootEl.getAttribute("data-duration")) : NaN;
  const dur = Number.isFinite(attrDur) && attrDur > 0 ? attrDur : Math.max(0, ...drivers.map((tl) => tl.duration()));
  const n = Math.max(2, opts.samples);
  const times = Array.from({ length: n }, (_, i) => Math.min(dur, (dur * i) / (n - 1)));

  const REASONS = ["focus", "glow", "wipe"];
  function reasonProblem(el, why) {
    const r = el.getAttribute("data-blur-reason");
    if (!r) return `${describe(el)}: ${why} without data-blur-reason`;
    if (!REASONS.includes(r)) return `${describe(el)}: data-blur-reason "${r}" is not focus, glow or wipe`;
    if (r === "wipe" && opts.format !== "shorts") return `${describe(el)}: data-blur-reason "wipe" is Shorts-only`;
    return null;
  }
  for (const t of times) {
    for (const tl of drivers) tl.seek(tl === rootTl || !rootTl ? t : Math.min(t, tl.duration()), false);
    for (const el of document.querySelectorAll("*")) {
      if (el.tagName === "feGaussianBlur") {
        const bad = reasonProblem(el, "feGaussianBlur");
        if (bad) add(5, bad, t);
        const sd = String(el.getAttribute("stdDeviation") || "0").trim().split(/[\s,]+/).map(parseFloat);
        if (sd.length === 2 && sd[0] !== sd[1] && !(opts.format === "shorts" && el.getAttribute("data-blur-reason") === "wipe")) {
          add(5, `${describe(el)}: directional Gaussian (stdDeviation "${sd.join(" ")}") is movement blur — use HFMotionBlur`, t);
        }
        continue;
      }
      const cs = getComputedStyle(el);
      for (const prop of ["filter", "backdropFilter"]) {
        if (String(cs[prop] || "").includes("blur(")) { const bad = reasonProblem(el, `CSS ${prop} blur()`); if (bad) add(5, bad, t); }
      }
      if (cs.backgroundClip === "text" || cs.webkitBackgroundClip === "text") {
        const lh = parseFloat(cs.lineHeight), fs = parseFloat(cs.fontSize);
        if (Number.isFinite(lh) && Number.isFinite(fs) && lh < 1.3 * fs - 0.01) {
          add(10, `${describe(el)}: gradient text with line-height ${r2(lh / fs)}× the font size crops its glyphs — keep ≥ 1.3 (shorts.md §9b trap 2)`, t);
        }
        if (cs.textAlign === "center" && [...el.querySelectorAll("*")].some((c) => c.style && c.style.transform)) {
          add(10, `${describe(el)}: centred gradient text with transformed word spans ghosts in the render — use a solid colour (shorts.md §9b trap 1)`, t);
        }
      }
    }
  }
  return { timelines: ids.length, tweens: seen.size, samples: times.length, duration: dur, findings };
}

function args(argv) {
  const a = { samples: 24, timeout: 30000, width: 1920, height: 1080 };
  for (let i = 0; i < argv.length; i++) {
    const k = argv[i].replace(/^--/, "");
    a[k] = ["samples", "timeout", "width", "height"].includes(k) ? Number(argv[++i]) : argv[++i];
  }
  return a;
}

async function waitFor(fn, ms, what) {
  const end = Date.now() + ms;
  for (;;) {
    const v = await fn();
    if (v) return v;
    if (Date.now() > end) throw new Error("timed out waiting for " + what);
    await new Promise((r) => setTimeout(r, 100));
  }
}

async function main() {
  const a = args(process.argv.slice(2));
  if (!a.url || !["long-form", "shorts"].includes(a.format) || !a.chrome) {
    process.stderr.write("usage: node tools/qa_probe.mjs --url URL --format long-form|shorts --chrome PATH [--width W --height H] [--samples N]\n");
    return 2;
  }
  if (typeof WebSocket === "undefined") { process.stderr.write("qa_probe needs node ≥ 22 (global WebSocket)\n"); return 2; }
  if (!existsSync(a.chrome)) { process.stderr.write("chrome not found: " + a.chrome + "\n"); return 2; }
  const profile = mkdtempSync(join(tmpdir(), "hf-qa-probe-"));
  const chrome = spawn(a.chrome, ["--headless", "--remote-debugging-port=0", "--user-data-dir=" + profile, "--no-first-run",
    "--no-default-browser-check", "--hide-scrollbars", "--mute-audio", `--window-size=${a.width},${a.height}`, "about:blank"],
    { stdio: "ignore" });
  let ws;
  try {
    const portFile = join(profile, "DevToolsActivePort");
    const port = await waitFor(() => existsSync(portFile) && readFileSync(portFile, "utf8").split("\n")[0], 15000, "Chrome to start");
    const pages = await waitFor(async () => {
      const list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
      return list.filter((t) => t.type === "page").length ? list : null;
    }, 10000, "a Chrome page");
    ws = new WebSocket(pages.find((t) => t.type === "page").webSocketDebuggerUrl);
    await new Promise((ok, fail) => { ws.onopen = ok; ws.onerror = () => fail(new Error("DevTools connection failed")); });
    let id = 0;
    const pending = new Map(), waiters = [], errors = [];
    ws.onmessage = (ev) => {
      const m = JSON.parse(ev.data);
      if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); return; }
      if (m.method === "Runtime.exceptionThrown") errors.push(m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text);
      waiters.forEach((w) => w(m));
    };
    const send = (method, params = {}) => new Promise((ok) => { const i = ++id; pending.set(i, ok); ws.send(JSON.stringify({ id: i, method, params })); });
    const loaded = new Promise((ok) => waiters.push((m) => { if (m.method === "Page.loadEventFired") ok(); }));
    await send("Page.enable");
    await send("Runtime.enable");
    await send("Emulation.setDeviceMetricsOverride", { width: a.width, height: a.height, deviceScaleFactor: 1, mobile: false });
    const nav = await send("Page.navigate", { url: a.url });
    if (nav.result && nav.result.errorText) throw new Error("navigation failed: " + nav.result.errorText);
    await Promise.race([loaded, new Promise((_, fail) => setTimeout(() => fail(new Error("page load timed out")), a.timeout))]);
    const res = await send("Runtime.evaluate", { expression: `(${pageProbe.toString()})(${JSON.stringify({ format: a.format, samples: a.samples, timeout: a.timeout })})`,
      awaitPromise: true, returnByValue: true });
    if (res.result.exceptionDetails) throw new Error("probe threw: " + (res.result.exceptionDetails.exception?.description || res.result.exceptionDetails.text));
    const out = res.result.result.value;
    if (out.error) throw new Error(out.error);
    out.errors = errors;
    process.stdout.write(JSON.stringify(out) + "\n");
    return 0;
  } catch (e) {
    process.stderr.write("qa_probe: " + e.message + "\n");
    return 2;
  } finally {
    try { ws && ws.close(); } catch (e) { /* closing anyway */ }
    chrome.kill("SIGKILL");
    await new Promise((r) => setTimeout(r, 200));
    rmSync(profile, { recursive: true, force: true });
  }
}

process.exitCode = await main();
