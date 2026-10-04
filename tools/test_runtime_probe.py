import functools
import http.server
import shutil
import tempfile
import threading
import unittest
from pathlib import Path

import runtime_probe as rp

ROOT = Path(__file__).resolve().parents[1]
CHROME = rp.find_chrome(allow_npx=False)

# A stand-in for GSAP with exactly the API qa_probe reads: getChildren / vars / duration / startTime /
# targets / parent / seek. seek(t) fires every onUpdate, the way a driver tween renders.
FAKE_GSAP = """
function Tween(target, vars, at, parent) { this._t = [target]; this.vars = vars; this._at = at; this.parent = parent; }
Tween.prototype.duration = function () { return this.vars.duration || 0; };
Tween.prototype.startTime = function () { return this._at; };
Tween.prototype.targets = function () { return this._t; };
function TL(vars) { this.vars = vars || {}; this.kids = []; this.parent = null; }
TL.prototype.to = function (target, vars, at) { this.kids.push(new Tween(target, vars, at, this)); return this; };
TL.prototype.set = function (target, vars, at) { return this.to(target, Object.assign({ duration: 0 }, vars), at); };
TL.prototype.getChildren = function () { return this.kids; };
TL.prototype.duration = function () { return Math.max.apply(null, [0].concat(this.kids.map(function (k) { return k._at + k.duration(); }))); };
TL.prototype.seek = function (t) { this.kids.forEach(function (k) { if (k.vars.onUpdate) k.vars.onUpdate(t); }); return this; };
"""

PAGE = """<!doctype html><html><head><meta charset="utf-8">
<script src="profile.js"></script><script>%s</script>
<style>
  .grad { background: linear-gradient(90deg, #fff, #888); -webkit-background-clip: text; background-clip: text;
          color: transparent; font-size: 40px; line-height: 1.0; }
  .centred { text-align: center; line-height: 1.4; }
</style></head><body>
<div id="root" data-composition-id="main" data-duration="4">
  <svg width="0" height="0"><filter id="f1"><feGaussianBlur id="bare" stdDeviation="3"/></filter>
    <filter id="f2"><feGaussianBlur id="glow" data-blur-reason="glow" stdDeviation="3"/></filter>
    <filter id="f3"><feGaussianBlur id="smear" data-blur-reason="wipe" stdDeviation="8 0"/></filter></svg>
  <div id="late"></div><div id="tagged"></div>
  <p id="cropped" class="grad">Cropped</p>
  <p id="ghost" class="grad centred"><span style="transform: translateY(4px)">Ghost</span></p>
</div>
<script>
  var E = function (t) { return HFProfile.ease("long-form", t); };
  var tl = new TL();
  tl.to("#a", { x: 1, duration: 1, ease: E("ease.enter") }, 0);            // ok
  tl.to("#b", { x: 1, duration: 1 }, 0.5);                                 // no ease
  tl.to("#c", { x: 1, duration: 1, ease: "power2.out" }, 1);               // raw string
  tl.to("#d", { x: 1, duration: 1, ease: function (p) { return p; } }, 1); // foreign function
  tl.to("#e", { x: 1, duration: 1, ease: "none" }, 2);                     // linear, not a driver
  tl.set("#f", { x: 0 }, 0);                                               // set: nothing to ease
  var late = document.getElementById("late"), tagged = document.getElementById("tagged");
  tagged.setAttribute("data-blur-reason", "focus");                       // set at runtime, like lib does
  tl.to({ t: 0 }, { t: 1, duration: 4, ease: "none", onUpdate: function (t) {   // a driver: allowed
    late.style.filter = t > 1.5 ? "blur(4px)" : "none";                   // untagged blur appears mid-timeline
    tagged.style.filter = "blur(2px)";
  } }, 0);
  var withDefaults = new TL({ defaults: { ease: E("ease.camera") } });
  withDefaults.to("#g", { x: 1, duration: 1 }, 0);                         // inherits the profile ease
  window.__timelines = { main: tl, other: withDefaults };
</script></body></html>""" % FAKE_GSAP


PLACEHOLDER_PAGE = """<!doctype html><html><head><meta charset="utf-8"><script src="profile.js"></script><script>%s</script></head><body>
<div id="root" data-composition-id="main" data-duration="2"><div id="hf-placeholder"></div><div id="other"></div></div>
<script>var tl = new TL();
tl.to(document.getElementById("hf-placeholder"), { x: 1, duration: 2, ease: "none" }, 0);
tl.to(document.getElementById("other"), { x: 1, duration: 2, ease: "none" }, 0);
window.__timelines = { main: tl };</script></body></html>""" % FAKE_GSAP

NO_TWEENS_PAGE = """<!doctype html><html><head><meta charset="utf-8"><script>%s</script></head><body>
<div id="root" data-composition-id="main"></div><script>window.__timelines = { main: new TL() };</script></body></html>""" % FAKE_GSAP

NOT_GSAP_PAGE = """<!doctype html><html><body><div id="root" data-composition-id="main"></div>
<script>window.__timelines = { main: { duration: function () { return 3; } } };</script></body></html>"""


@unittest.skipUnless(CHROME and shutil.which("node"), "needs node and chrome-headless-shell (npx hyperframes browser ensure)")
class ProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        d = Path(cls.tmp.name)
        shutil.copyfile(ROOT / "lib" / "profile.js", d / "profile.js")
        (d / "index.html").write_text(PAGE)
        (d / "empty.html").write_text("<!doctype html><p>no timelines</p>")
        (d / "placeholder.html").write_text(PLACEHOLDER_PAGE)
        (d / "notweens.html").write_text(NO_TWEENS_PAGE)
        (d / "notgsap.html").write_text(NOT_GSAP_PAGE)
        handler = functools.partial(QuietHandler, directory=str(d))
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        cls.result = rp.probe_url(cls.base + "/index.html", "long-form", (1920, 1080), samples=9, timeout_ms=10000)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.tmp.cleanup()

    def messages(self, check):
        return [f["message"] for f in self.result["findings"] if f["check"] == check]

    def test_counts(self):
        self.assertEqual(self.result["timelines"], 2)
        self.assertEqual(self.result["tweens"], 8)
        self.assertEqual(self.result["samples"], 9)

    def test_eases(self):
        m = self.messages(6)
        self.assertEqual(len(m), 4, m)
        self.assertTrue(any("#b" in x and "has no ease" in x for x in m), m)
        self.assertTrue(any('raw ease "power2.out"' in x for x in m), m)
        self.assertTrue(any("not an HFProfile.ease token" in x for x in m), m)
        self.assertTrue(any("#e" in x and "is linear but is not a driver" in x for x in m), m)

    def test_blur_reasons_seen_at_runtime(self):
        m = self.messages(5)
        self.assertIn("main feGaussianBlur#bare: feGaussianBlur without data-blur-reason", m)
        self.assertIn('main feGaussianBlur#smear: data-blur-reason "wipe" is Shorts-only', m)
        late = [f for f in self.result["findings"] if "div#late" in f["message"]]
        self.assertEqual(len(late), 1, self.result["findings"])
        self.assertGreater(late[0]["t"], 1.5, "found by seeking, not in the load-time DOM")
        self.assertFalse([x for x in m if "#tagged" in x or "#glow" in x], m)
        self.assertTrue(any("directional Gaussian" in x for x in m), m)

    def test_render_traps(self):
        m = self.messages(10)
        self.assertTrue(any("p#cropped" in x and "line-height 1" in x for x in m), m)
        self.assertTrue(any("p#ghost" in x and "ghosts in the render" in x for x in m), m)

    def test_page_without_timelines_is_an_error(self):
        with self.assertRaisesRegex(rp.ProbeError, "no timeline registered"):
            rp.probe_url(self.base + "/empty.html", "long-form", (640, 360), samples=2, timeout_ms=1500)

    def test_placeholder_is_exempt_but_other_linear_tweens_are_not(self):
        r = rp.probe_url(self.base + "/placeholder.html", "long-form", (640, 360), samples=2, timeout_ms=10000)
        m = [f["message"] for f in r["findings"] if f["check"] == 6]
        self.assertEqual(len(m), 1, m)
        self.assertIn("div#other", m[0])

    def test_page_without_tweens_is_an_error(self):
        with self.assertRaisesRegex(rp.ProbeError, "no tweens"):
            rp.probe_url(self.base + "/notweens.html", "long-form", (640, 360), samples=2, timeout_ms=10000)

    def test_non_gsap_timeline_is_an_error(self):
        with self.assertRaisesRegex(rp.ProbeError, "not a GSAP timeline"):
            rp.probe_url(self.base + "/notgsap.html", "long-form", (640, 360), samples=2, timeout_ms=10000)

    def test_fast_page_returns_well_before_the_timeout(self):
        import time
        t0 = time.time()
        rp.probe_url(self.base + "/placeholder.html", "long-form", (640, 360), samples=2, timeout_ms=60000)
        self.assertLess(time.time() - t0, 15, "the race timer must not hold the process open")


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class CliPrefixTests(unittest.TestCase):
    def test_hf_cli_override(self):
        import os
        old = os.environ.get("HF_CLI")
        os.environ["HF_CLI"] = "npx --yes hyperframes@0.8.29"
        try:
            self.assertEqual(rp.hyperframes_cmd(), ["npx", "--yes", "hyperframes@0.8.29"])
        finally:
            if old is None:
                del os.environ["HF_CLI"]
            else:
                os.environ["HF_CLI"] = old


class FailurePathTests(unittest.TestCase):
    def setUp(self):
        self.old = rp._run
        self.calls = []

    def tearDown(self):
        rp._run = self.old

    def fake(self, start_stdout, start_rc=0, stop_rc=0):
        def run(cmd, timeout_s):
            self.calls.append(cmd)
            if "--stop" in cmd:
                return subprocess_result(cmd, stop_rc, "", "boom" if stop_rc else "")
            return subprocess_result(cmd, start_rc, start_stdout, "")
        rp._run = run

    def test_missing_binary_is_a_probe_error(self):
        with self.assertRaisesRegex(rp.ProbeError, "cannot run"):
            rp._run(["/nonexistent/binary-xyz"], 5)

    def test_timeout_is_a_probe_error_and_kills_the_group(self):
        with self.assertRaisesRegex(rp.ProbeError, "timed out"):
            rp._run(["sleep", "30"], 0.3)

    def test_garbled_and_non_dict_start_output(self):
        for out in ("", "not json", "[1, 2]", '{"result": 5}'):
            self.fake(out)
            with self.assertRaisesRegex(rp.ProbeError, "did not start"):
                rp.probe_project("/tmp", "long-form", (1920, 1080))

    def test_started_server_missing_fields_is_stopped(self):
        self.fake('{"result": {"state": "started"}}')
        with self.assertRaisesRegex(rp.ProbeError, "serverUrl"):
            rp.probe_project("/tmp", "long-form", (1920, 1080))
        self.assertTrue(any("--stop" in c for c in self.calls), self.calls)

    def test_reused_server_is_not_stopped(self):
        self.fake('{"result": {"state": "running"}}')
        with self.assertRaises(rp.ProbeError):
            rp.probe_project("/tmp", "long-form", (1920, 1080))
        self.assertFalse(any("--stop" in c for c in self.calls), self.calls)

    def test_failed_stop_becomes_a_warning(self):
        self.fake('{"result": {"state": "started", "serverUrl": "http://x", "projectName": "p"}}', stop_rc=1)
        old = rp.probe_url
        rp.probe_url = lambda *a, **k: {"findings": []}
        try:
            import contextlib, io
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                r = rp.probe_project("/tmp", "long-form", (1920, 1080))
        finally:
            rp.probe_url = old
        self.assertEqual(len(r["warnings"]), 1)
        self.assertIn("preview --stop failed", err.getvalue())


def subprocess_result(cmd, rc, out, err):
    import subprocess
    return subprocess.CompletedProcess(cmd, rc, out, err)


if __name__ == "__main__":
    unittest.main()
