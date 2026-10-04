import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import cadence_scan as cs
import synth

ROOT = Path(__file__).resolve().parents[1]
HEADER = "| t_in | t_out | words | placement | type | beats | ease | marks |\n|---|---|---|---|---|---|---|---|\n"


def make_project(base: Path, fmt: str, rows, duration=None, extra_yaml="") -> Path:
    p = base / "proj"
    p.mkdir()
    (p / "BRIEF.md").write_text(f"# B\n\n```yaml\nformat: {fmt}\n{extra_yaml}```\n")
    grid = "".join(f"| {a} | {b} | \"w\" | {pl} | A1 | — | ease.enter | — |\n" for a, b, pl in rows)
    (p / "storyboard.md").write_text("# S\n\n" + HEADER + grid)
    if duration:
        (p / "transcript.json").write_text(json.dumps([{"text": "x", "start": 0, "end": duration}]))
    return p


def by_name(results):
    return {r["name"]: r for r in results}


class IntervalTests(unittest.TestCase):
    def test_merge_coverage_gaps(self):
        self.assertEqual(cs.merge([(5, 8), (0, 2), (1, 3), (8, 9)]), [(0.0, 3.0), (5.0, 9.0)])
        self.assertEqual(cs.coverage([(0, 3), (5, 9)], 2, 6), 2.0)
        self.assertEqual(cs.gaps([(2, 3), (5, 9)], 0, 10), [(0, 2.0), (3.0, 5.0), (9.0, 10)])
        self.assertEqual(cs.gaps([], 0, 4), [(0, 4)])


class EvaluateTests(unittest.TestCase):
    def test_long_form_hook_share_boundary(self):
        ok = by_name(cs.evaluate("long-form", [(i * 8, i * 8 + 4.8) for i in range(10)], 100))
        self.assertTrue(ok["hook graphics ≥ 60 %"]["ok"], ok)
        self.assertEqual(ok["hook graphics ≥ 60 %"]["value"], 0.6)
        low = by_name(cs.evaluate("long-form", [(i * 8, i * 8 + 4.7) for i in range(10)], 100))
        self.assertFalse(low["hook graphics ≥ 60 %"]["ok"])

    def test_long_form_hook_face_gap_boundary(self):
        base = [(0, 34), (40, 80)]
        self.assertTrue(by_name(cs.evaluate("long-form", base, 80))["hook face gaps ≤ 6 s"]["ok"])
        r = by_name(cs.evaluate("long-form", [(0, 34), (40.1, 80)], 80))["hook face gaps ≤ 6 s"]
        self.assertFalse(r["ok"])
        self.assertIn("34.0–40.1", r["detail"])

    def test_body_cadence_boundary_and_tail(self):
        hook = [(0, 80)]
        self.assertTrue(by_name(cs.evaluate("long-form", hook + [(110, 112)], 142))["body cadence ≤ 30 s"]["ok"])
        r = by_name(cs.evaluate("long-form", hook + [(111, 112)], 142))["body cadence ≤ 30 s"]
        self.assertFalse(r["ok"])
        self.assertIn("80.0–111.0", r["detail"])
        tail = by_name(cs.evaluate("long-form", hook, 111))["body cadence ≤ 30 s"]
        self.assertFalse(tail["ok"], "the stretch to the end of the video counts")

    def test_screen_share_exempt_and_over_footage_counts_for_body_only(self):
        hook = [(0, 80)]
        r = by_name(cs.evaluate("long-form", hook, 200, screen_share=[(100, 190)]))["body cadence ≤ 30 s"]
        self.assertTrue(r["ok"], r)
        self.assertIn("screen_share exempt", r["detail"])
        body = by_name(cs.evaluate("long-form", hook + [(140, 141)], 141, other=[(105, 110)]))
        self.assertTrue(body["body cadence ≤ 30 s"]["ok"])
        hook_only = by_name(cs.evaluate("long-form", [], 80, other=[(0, 80)]))
        self.assertFalse(hook_only["hook graphics ≥ 60 %"]["ok"], "over-footage layouts leave the face on screen")

    def test_short_long_form_uses_its_runtime_as_the_hook(self):
        r = by_name(cs.evaluate("long-form", [(0, 36)], 60, hook_end=80))
        self.assertEqual(r["hook graphics ≥ 60 %"]["value"], 0.6)
        self.assertEqual(r["body cadence ≤ 30 s"]["value"], 0.0)

    def test_shorts_band_edges(self):
        for secs, ok in ((35, True), (55, True), (34, False), (56, False)):
            self.assertEqual(cs.evaluate("shorts", [(0, secs)], 100)[0]["ok"], ok, secs)

    def test_thresholds_match_the_profiles(self):
        lf = (ROOT / "standards" / "formats" / "long-form.md").read_text()
        sh = (ROOT / "standards" / "formats" / "shorts.md").read_text()
        self.assertIn("default 80", lf)
        self.assertIn("≥ %d %% graphics" % round(cs.HOOK_MIN * 100), lf)
        self.assertIn("no face-only gap > %d s" % cs.HOOK_GAP, lf)
        self.assertIn("every ≤ %d s" % cs.BODY_GAP, lf)
        self.assertIn("QA band: %d–%d %%" % tuple(round(x * 100) for x in cs.SHORTS_BAND), sh)


class PlanReportTests(unittest.TestCase):
    def test_plan_report_from_the_beat_grid(self):
        with tempfile.TemporaryDirectory() as t:
            p = make_project(Path(t), "long-form", [(0, 50, "full-frame"), (52, 80, "full-frame"),
                                                    (100, 103, "over-footage")], duration=130,
                             extra_yaml="screen_share:\n  - [104, 129]\n")
            r = cs.report(p)
            self.assertTrue(r["ok"], cs.format_report(r))
            self.assertEqual(r["full_frame"], [(0.0, 50.0), (52.0, 80.0)])
            self.assertEqual(r["over_footage"], [(100.0, 103.0)])
            self.assertEqual(r["source"], "plan: storyboard.md")
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(cs.main(["cadence_scan.py", str(p)]), 0)
            self.assertIn("PASS  hook graphics ≥ 60 %", out.getvalue())

    def test_needs_a_runtime(self):
        with tempfile.TemporaryDirectory() as t:
            p = make_project(Path(t), "shorts", [(1, 4, "full-frame")], extra_yaml="captions: false\n")
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(cs.main(["cadence_scan.py", str(p)]), 2)
            self.assertIn("pass --duration or add transcript.json", out.getvalue())
            self.assertEqual(cs.report(p, duration=10)["results"][0]["value"], 0.3)


@unittest.skipUnless(synth.HAVE_FFMPEG, "ffmpeg/ffprobe not installed")
class EditMeasurementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.edit = synth.segments(Path(cls.tmp.name) / "edit.mp4",
                                  [("0x808080", 3), ("navy", 4), ("0x808080", 3)], noise=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_graphic_runs_found_by_face_distance(self):
        runs = cs.graphic_intervals(cs.face_distances(self.edit))
        self.assertEqual(len(runs), 1, runs)
        self.assertAlmostEqual(runs[0][0], 3.0, delta=0.2)
        self.assertAlmostEqual(runs[0][1], 7.0, delta=0.2)

    def test_face_ref_frame_gives_the_same_answer(self):
        runs = cs.graphic_intervals(cs.face_distances(self.edit, face_ref=1.0))
        self.assertAlmostEqual(runs[0][0], 3.0, delta=0.2)

    def test_edit_report_for_a_short(self):
        p = make_project(Path(self.tmp.name), "shorts", [(3, 7, "full-frame")], extra_yaml="captions: false\n")
        r = cs.report(p, edit=str(self.edit))
        self.assertTrue(r["ok"], cs.format_report(r))
        self.assertAlmostEqual(r["results"][0]["value"], 0.4, delta=0.03)
        self.assertTrue(r["source"].startswith("edit: "))


if __name__ == "__main__":
    unittest.main()
