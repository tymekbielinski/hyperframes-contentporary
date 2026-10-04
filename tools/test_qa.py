import io
import json
import os
import re
import shlex
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import new_video
import qa
import synth

ROOT = Path(__file__).resolve().parents[1]
FAKE_HF = """import os, shutil, sys, time
args = sys.argv[1:]
time.sleep(float(os.environ.get("FAKE_HF_SLEEP", "0")))
if args[0] == "check":
    print("fake hyperframes check: " + os.environ.get("FAKE_HF_CHECK_MSG", "ok"))
    sys.exit(int(os.environ.get("FAKE_HF_CHECK", "0")))
if args[0] == "render":
    shutil.copyfile(os.environ["FAKE_HF_RENDER_SRC"], args[args.index("-o") + 1])
    sys.exit(0)
sys.exit(3)
"""
HEADER = "| t_in | t_out | words | placement | type | beats | ease | marks |\n|---|---|---|---|---|---|---|---|\n"
GOOD_GRID = HEADER + (
    '| 0.0 | 50.0 | "hook" | full-frame | B1 | — | ease.enter | — |\n'
    '| 52.0 | 80.0 | "proof" | full-frame | A1 | — | ease.enter | — |\n'
    '| 100.0 | 104.0 | "key line" | over-footage | lower-third | — | ease.enter | — |\n')
SCENE = """<template>
<div id="root" data-composition-id="01-hook" data-width="1920" data-height="1080"><div id="h1">Proof first</div>
<svg><filter id="g"><feGaussianBlur data-blur-reason="glow" stdDeviation="6"/></filter></svg></div>
<script>
  var tl = gsap.timeline({ paused: true });
  HFText.words(tl, document.querySelector("#h1"), 0.5, { format: "long-form", frameHeight: 1080 });
  window.__timelines["01-hook"] = tl;
</script>
</template>
"""
SLOTS = ('<div id="s01" data-composition-id="01-hook" data-composition-src="compositions/01-hook.html" data-start="0" data-duration="2"></div>\n'
         '      <div id="s02" data-composition-id="02-proof" data-composition-src="compositions/02-proof.html" data-start="2" data-duration="2"></div>\n')


PLACEHOLDER = re.compile(r'\n\s*<!-- placeholder[^\n]*-->\n\s*<div id="hf-placeholder"[^\n]*</div>\n(\s*</div>)')
PLACEHOLDER_TWEEN = re.compile(r'\n\s*tl\.to\("#hf-placeholder"[^\n]*')


def with_slots(index):
    """The scaffold's index.html with its #hf-placeholder (and its tween) replaced by the two scene slots."""
    out, n = PLACEHOLDER.subn(lambda m: "\n      " + SLOTS + m.group(1).lstrip("\n"), index)
    out, k = PLACEHOLDER_TWEEN.subn("", out)
    assert (n, k) == (1, 1), "scaffold index.html changed — update with_slots()"
    return out


def clean_probe(project, fmt):
    return {"timelines": 2, "tweens": 4, "samples": 24, "findings": []}


@unittest.skipUnless(synth.HAVE_FFMPEG and shutil.which("node"), "needs ffmpeg and node")
class GateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.media = tempfile.TemporaryDirectory()
        d = Path(cls.media.name)
        settled = synth.moving_then_still(d / "settled.mp4", 1.5, 0.5)
        moving = synth.moving(d / "moving.mp4", 2)
        glitched = synth.moving_then_still(d / "glitched.mp4", 1.5, 0.5, glitch_frame=20)
        cls.good_reel = synth.concat(d / "good.mp4", [settled, settled])          # two scenes, both settle
        cls.unsettled_reel = synth.concat(d / "unsettled.mp4", [settled, moving])  # scene 2 moves into its cut
        cls.glitch_reel = synth.concat(d / "glitch.mp4", [settled, glitched])      # one-frame glitch at reel frame 80
        cls.title_pop = d / "title_pop.mp4"                                         # a 1000×120 title pops in at 1 s and stays
        synth._ffmpeg(["-f", "lavfi", "-i", "color=c=0x101418:s=1920x1080:r=30:d=4", "-vf",
                       "drawbox=x=460:y=480:w=1000:h=120:color=0xF2F2F2:t=fill:enable='gte(n,30)'",
                       "-pix_fmt", "yuv420p", str(cls.title_pop)])
        fake = d / "fake_hf.py"
        fake.write_text(FAKE_HF)
        cls.hf_cli = f"{shlex.quote(sys.executable)} {shlex.quote(str(fake))}"

    @classmethod
    def tearDownClass(cls):
        cls.media.cleanup()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = {k: os.environ.get(k) for k in ("HF_CLI", "FAKE_HF_CHECK", "FAKE_HF_RENDER_SRC", "FAKE_HF_SLEEP")}
        os.environ["HF_CLI"] = self.hf_cli
        os.environ["FAKE_HF_CHECK"] = "0"
        self.p = new_video.scaffold("10-demo", "long-form", videos_dir=Path(self.tmp.name))
        brief = (self.p / "BRIEF.md").read_text()
        brief = brief.replace('film: ""', 'film: "Believe the system is predictable"')
        brief = brief.replace('direction: ""', 'direction: "One canvas per argument"')
        (self.p / "BRIEF.md").write_text(brief)
        (self.p / "storyboard.md").write_text(GOOD_GRID)
        (self.p / "transcript.json").write_text(json.dumps([{"text": "x", "start": 0, "end": 110}]))
        (self.p / "index.html").write_text(with_slots((self.p / "index.html").read_text()))
        (self.p / "compositions" / "01-hook.html").write_text(SCENE)

    def tearDown(self):
        for k, v in self.env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self.tmp.cleanup()

    def gate(self, **kw):
        kw.setdefault("render", self.good_reel)
        kw.setdefault("probe", clean_probe)
        return qa.run_gate(self.p, **kw)

    def status(self, report):
        return {c["n"]: c["status"] for c in report["checks"]}

    def test_good_project_passes_all_ten(self):
        r = self.gate()
        self.assertEqual(self.status(r), {n: "PASS" for n in range(1, 11)}, qa.format_report(r))
        self.assertTrue(r["ok"])
        self.assertTrue((self.p / "renders" / "qa-report.json").is_file())
        self.assertIn("RESULT: PASS", qa.format_report(r))

    def test_check_1_hyperframes_check_failure(self):
        os.environ["FAKE_HF_CHECK"] = "1"
        c = self.gate()["checks"][0]
        self.assertEqual(c["status"], "FAIL")
        self.assertIn("fake hyperframes check: ok", c["findings"][-1])

    def test_check_2_edited_lib_copy(self):
        (self.p / "lib" / "camera.js").write_text("// forked\n")
        c = self.gate()["checks"][1]
        self.assertEqual(c["findings"], ["lib/camera.js differs from root lib/camera.js (edited copy?) — fix root lib/, then re-sync"])

    def test_check_3_incomplete_brief_and_stale_brand_css(self):
        text = (self.p / "BRIEF.md").read_text()
        (self.p / "BRIEF.md").write_text(text.replace('direction: "One canvas per argument"', 'direction: ""'))
        self.assertIn("direction is required (one line of art direction)", self.gate()["checks"][2]["findings"])
        (self.p / "BRIEF.md").write_text(text.replace("palette: red", "palette: silver"))
        found = self.gate()["checks"][2]["findings"]
        self.assertIn("index.html root data-hf-mode is 'dark', palette silver is 'light'", found)
        self.assertTrue(any(f.startswith("compositions/brand.css does not match") and "--palette silver" in f for f in found), found)

    def test_checks_4_5_6_static_findings(self):
        (self.p / "compositions" / "02-proof.html").write_text(
            "<template><div id=\"root\" data-composition-id=\"02-proof\"><svg><filter><feGaussianBlur stdDeviation=\"3\"/></filter></svg></div>\n"
            "<script>var x = Math.random(); tl.to('#a', { x: 1, duration: 1, ease: \"power2.out\" });</script></template>\n")
        st = self.status(self.gate())
        self.assertEqual((st[4], st[5], st[6]), ("FAIL", "FAIL", "FAIL"))
        r = self.gate()
        self.assertTrue(r["checks"][3]["findings"][0].startswith("compositions/02-proof.html:2: non-deterministic"), r["checks"][3])

    def test_runtime_findings_merge_into_their_checks(self):
        def probe(project, fmt):
            return {"findings": [{"check": 5, "message": "main div#x: CSS filter blur() without data-blur-reason", "t": 1.5},
                                 {"check": 6, "message": "main: tween on div#y at 2 s has no ease", "t": None},
                                 {"check": 10, "message": "p#g: centred gradient text ...", "t": 0.5}]}
        r = self.gate(probe=probe)
        self.assertEqual(r["checks"][4]["findings"], ["runtime @ 1.5 s: main div#x: CSS filter blur() without data-blur-reason"])
        self.assertEqual(r["checks"][5]["findings"], ["runtime: main: tween on div#y at 2 s has no ease"])
        self.assertEqual(r["checks"][9]["status"], "FAIL")

    def test_probe_failure_fails_5_6_10(self):
        def probe(project, fmt):
            raise qa.runtime_probe.ProbeError("no timeline registered on window.__timelines")
        st = self.status(self.gate(probe=probe))
        self.assertEqual((st[5], st[6], st[10]), ("FAIL", "FAIL", "FAIL"))

    def test_probe_failure_message_and_empty_probe(self):
        def probe(project, fmt):
            raise qa.runtime_probe.ProbeError("probe saw 0 tweens — nothing to check (empty composition?)")
        r = self.gate(probe=probe)
        for i in (4, 5, 9):
            self.assertEqual(r["checks"][i]["status"], "FAIL")
            self.assertIn("runtime probe failed: probe saw 0 tweens — nothing to check (empty composition?)", r["checks"][i]["findings"])
        st = self.status(self.gate(probe=probe, render=None, skip_render=True))
        self.assertEqual(st[10], "FAIL")   # a probe failure is a FAIL, never a SKIP

    def test_probe_warnings_are_listed(self):
        def probe(project, fmt):
            return {"timelines": 1, "tweens": 3, "samples": 24, "findings": [],
                    "warnings": ["preview --stop failed (a preview server may still be running): boom"]}
        r = self.gate(probe=probe)
        self.assertTrue(r["ok"], qa.format_report(r))
        self.assertEqual(r["warnings"], ["runtime probe: preview --stop failed (a preview server may still be running): boom"])
        self.assertIn("warning: runtime probe: preview --stop failed", qa.format_report(r))

    def test_check_8_surfaces_cadence_warnings(self):
        real = qa.cadence_scan.report
        warn = "face reference = median of all frames — unreliable if graphics exceed 50 % of the edit; pass --face-ref or a storyboard"

        def fake(project, edit=None, **kw):
            r = real(project)
            return dict(r, source=f"edit: {edit}", warnings=[warn]) if edit else r
        with mock.patch.object(qa.cadence_scan, "report", side_effect=fake):
            r = self.gate(edit="cut.mp4")
        c = r["checks"][7]
        self.assertEqual(c["status"], "PASS", c)
        self.assertEqual(c["warnings"], ["edit: cut.mp4: " + warn])
        self.assertIn("check 8: edit: cut.mp4: " + warn, r["warnings"])
        self.assertIn("warning: edit: cut.mp4: face reference = median", qa.format_report(r))

    def test_placeholder_left_in_once_scenes_exist_fails_check_1(self):
        index = (self.p / "index.html").read_text()
        (self.p / "index.html").write_text(index.replace('<div id="s01"', '<div id="hf-placeholder" style="width:1px"></div>\n      <div id="s01"'))
        c = self.gate()["checks"][0]
        self.assertEqual(c["status"], "FAIL")
        self.assertEqual(c["findings"], ["index.html: remove the scaffold placeholder #hf-placeholder now that scenes exist"])

    def test_placeholder_is_fine_in_a_fresh_scaffold_only(self):
        fresh = new_video.scaffold("10-fresh", "long-form", videos_dir=Path(self.tmp.name))
        self.assertEqual(qa.placeholder_findings(fresh), [])
        self.assertEqual(qa.run_gate(fresh, skip_render=True, probe=clean_probe)["checks"][0]["status"], "PASS")
        msg = ["index.html: remove the scaffold placeholder #hf-placeholder now that scenes exist"]
        (fresh / "storyboard.md").write_text(GOOD_GRID)                      # a beat-grid row
        self.assertEqual(qa.placeholder_findings(fresh), msg)
        (fresh / "storyboard.md").write_text(HEADER)
        (fresh / "compositions" / "01-hook.html").write_text(SCENE)          # a scene file
        self.assertEqual(qa.placeholder_findings(fresh), msg)
        (fresh / "compositions" / "01-hook.html").unlink()
        index = (fresh / "index.html").read_text()
        (fresh / "index.html").write_text(index.replace('<div id="hf-placeholder"', SLOTS + '      <div id="hf-placeholder"'))  # a slot
        self.assertEqual(qa.placeholder_findings(fresh), msg)

    def test_title_pop_in_mid_scene_passes_check_10(self):
        r = self.gate(render=self.title_pop)
        self.assertEqual(self.status(r)[10], "PASS", qa.format_report(r))

    def test_static_scan_failure_fans_out_and_report_is_written(self):
        fake_root = Path(self.tmp.name) / "fake-root"          # no tools/lawscan.js there: node prints no JSON
        (fake_root / "tools").mkdir(parents=True)
        with mock.patch.object(qa, "ROOT", fake_root):
            r = self.gate()
        for n in (4, 5, 6, 10):
            c = r["checks"][n - 1]
            self.assertEqual(c["status"], "FAIL", c)
            self.assertTrue(any(f.startswith("static scan failed: RuntimeError: lawscan") for f in c["findings"]), c)
        self.assertEqual(json.loads((self.p / "renders" / "qa-report.json").read_text())["ok"], False)

    def test_missing_hf_cli_is_a_named_fail(self):
        os.environ["HF_CLI"] = "/nonexistent/hyperframes-cli"
        r = self.gate(render=None)
        st = self.status(r)
        self.assertEqual((st[1], st[9], st[10]), ("FAIL", "FAIL", "FAIL"))
        self.assertTrue(r["checks"][0]["findings"][-1].startswith("npx hyperframes check: cannot run /nonexistent/hyperframes-cli"), r["checks"][0])
        self.assertTrue(r["checks"][8]["findings"][0].startswith("draft render failed: cannot run /nonexistent/hyperframes-cli"), r["checks"][8])

    def test_hyperframes_check_timeout_is_a_named_fail(self):
        os.environ["FAKE_HF_SLEEP"] = "5"
        with mock.patch.object(qa, "CHECK_TIMEOUT", 0.5):
            c = self.gate()["checks"][0]
        self.assertEqual(c["status"], "FAIL")
        self.assertIn("timed out after", c["findings"][-1])

    def test_non_utf8_composition_is_a_named_fail(self):
        (self.p / "compositions" / "03-bad.html").write_bytes(b"<div>caf\xe9</div>\n")
        r = self.gate()
        self.assertFalse(r["ok"])
        for n in (4, 7):
            c = r["checks"][n - 1]
            self.assertEqual(c["status"], "FAIL")
            self.assertTrue(any("compositions/03-bad.html is not UTF-8 text" in f for f in c["findings"]), c)

    def test_crashing_run_leaves_no_stale_pass(self):
        out = self.p / "renders" / "qa-report.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"ok": True}))
        with mock.patch.object(qa, "apply_waivers", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                self.gate()
        self.assertFalse(out.exists())

    def test_infrastructure_findings_are_not_waivable(self):
        text = (self.p / "BRIEF.md").read_text()
        (self.p / "BRIEF.md").write_text(text.replace("exceptions:                  #",
            'exceptions:\n  - "check 5: blur reviewed by hand"\n  - "check 10 [runtime]: reviewed"\n  - "check 1: placeholder is fine"\n#'))
        index = (self.p / "index.html").read_text()
        (self.p / "index.html").write_text(index.replace('<div id="s01"', '<div id="hf-placeholder"></div>\n      <div id="s01"'))

        def probe(project, fmt):
            raise qa.runtime_probe.ProbeError("no timeline registered on window.__timelines")
        r = self.gate(probe=probe)
        st = self.status(r)
        self.assertEqual((st[1], st[5], st[10]), ("FAIL", "FAIL", "FAIL"))
        self.assertEqual(r["checks"][0]["findings"], [qa.PLACEHOLDER_MSG])
        self.assertEqual(r["checks"][4]["findings"], ["runtime probe failed: no timeline registered on window.__timelines"])
        checks = [qa.result(n) for n in range(1, 11)]
        checks[8] = qa.result(9, [qa.internal(ValueError("x")), "02-proof: still moving…"])
        checks[9] = qa.result(10, [qa.Infra("draft render failed: exit 1")])
        qa.apply_waivers(checks, ["check 9: by design", "check 10: by design"])
        self.assertEqual((checks[8]["status"], checks[8]["findings"]), ("FAIL", ["internal error: ValueError: x"]))
        self.assertEqual((checks[9]["status"], checks[9]["findings"]), ("FAIL", ["draft render failed: exit 1"]))

    def test_scoped_waiver_matches_whole_tokens_only(self):
        checks = [qa.result(n) for n in range(1, 11)]
        found = ["compositions/data.html:1: Gaussian site without…", "compositions/a.html:2: Gaussian site without…",
                 "compositions/a.html.bak:3: Gaussian site without…"]
        checks[4] = qa.result(5, list(found))
        qa.apply_waivers(checks, ["check 5 [a.html]: legacy recreation"])
        self.assertEqual(checks[4]["findings"], [found[0], found[2]])
        self.assertEqual(checks[4]["waived"], ["1 finding(s): legacy recreation"])

    def test_check_7_caption_layer_in_long_form(self):
        (self.p / "compositions" / "03-caps.html").write_text('<div class="captions word-layer">hi</div>\n<!-- class="captions" in a comment is fine -->\n')
        c = self.gate()["checks"][6]
        self.assertEqual(c["findings"], ['compositions/03-caps.html:1: caption layer (class="captions word-layer")'])

    def test_check_8_density_on_the_plan(self):
        (self.p / "storyboard.md").write_text(HEADER + '| 0.0 | 30.0 | "hook" | full-frame | B1 | — | — | — |\n')
        c = self.gate()["checks"][7]
        self.assertEqual(c["status"], "FAIL")
        self.assertTrue(any("hook graphics ≥ 60 %" in f for f in c["findings"]), c["findings"])

    def test_check_9_scene_still_moving_at_its_cut(self):
        c = self.gate(render=self.unsettled_reel)["checks"][8]
        self.assertEqual(len(c["findings"]), 1, c)
        self.assertTrue(c["findings"][0].startswith("02-proof: still moving in its last 0.3 s"), c["findings"])

    def test_check_10_flicker_but_not_the_scene_cut(self):
        c = self.gate(render=self.glitch_reel)["checks"][9]
        self.assertEqual([f.split(" (")[0] for f in c["findings"]], ["flicker at frame 80", "flicker at frame 81"], c["findings"])

    def test_waivers_and_listed_exceptions(self):
        text = (self.p / "BRIEF.md").read_text()
        (self.p / "BRIEF.md").write_text(text.replace("exceptions:                  #", 'exceptions:\n  - "check 9: hold-push into the CTA by design"\n  - "F09: recreated Google Calendar — no real account"\n#'))
        r = self.gate(render=self.unsettled_reel)
        c9 = r["checks"][8]
        self.assertEqual(c9["status"], "WAIVED")
        self.assertEqual(c9["waived"], ["1 finding(s): hold-push into the CTA by design"])
        self.assertEqual(r["exceptions"], ["F09: recreated Google Calendar — no real account"])
        self.assertTrue(r["ok"], qa.format_report(r))

    def test_scoped_waiver_keeps_other_findings(self):
        checks = [qa.result(n) for n in range(1, 11)]
        checks[4] = qa.result(5, ["compositions/a.html:3: Gaussian site without…", "compositions/b.html:9: Gaussian site without…"])
        listed = qa.apply_waivers(checks, ["check 5 [a.html]: legacy recreation", "check 12: nonsense"])
        self.assertEqual(checks[4]["status"], "FAIL")
        self.assertEqual(checks[4]["findings"], ["compositions/b.html:9: Gaussian site without…"])
        self.assertEqual(listed, ["check 12: nonsense"])

    def test_skip_render_cannot_pass(self):
        r = self.gate(render=None, skip_render=True)
        self.assertEqual((self.status(r)[9], self.status(r)[10]), ("SKIP", "SKIP"))
        self.assertFalse(r["ok"])

    def test_draft_render_through_hyperframes(self):
        os.environ["FAKE_HF_RENDER_SRC"] = str(self.good_reel)
        r = self.gate(render=None)
        self.assertEqual(self.status(r)[9], "PASS", qa.format_report(r))
        self.assertTrue((self.p / "renders" / "qa-draft.mp4").is_file())

    def test_cli(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(qa.main(["qa.py", str(Path(self.tmp.name) / "nope")]), 2)
        self.assertIn("not a directory", out.getvalue())


@unittest.skipUnless(synth.HAVE_FFMPEG and shutil.which("node"), "needs ffmpeg and node")
class ShortsGateTests(unittest.TestCase):
    def test_shorts_captions_flag_and_settle_before_the_wipe(self):
        with tempfile.TemporaryDirectory() as t:
            p = new_video.scaffold("s1-demo", "shorts", palette="reel-dark", videos_dir=Path(t))
            brief = (p / "BRIEF.md").read_text().replace('film: ""', 'film: "x"').replace('direction: ""', 'direction: "y"')
            (p / "BRIEF.md").write_text(brief.replace("captions: false", "captions: true"))
            rows = [{"row": 1, "line": 3, "t_in": 1.0, "t_out": 4.0, "placement": "full-frame", "type": "A1"}]
            self.assertEqual(qa.scene_windows(p, "shorts", rows), [("row 1 (1–4 s)", 4.0 - 0.36 - 0.3, 4.0 - 0.36)])
            c = qa.check_captions(p, qa.pj.read_brief(p), [])
            self.assertEqual(c["findings"], ["captions: true but no caption layer found (id/class 'captions' or data-captions)"])


if __name__ == "__main__":
    unittest.main()
