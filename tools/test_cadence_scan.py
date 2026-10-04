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


@unittest.skipUnless(synth.HAVE_FFMPEG, "ffmpeg/ffprobe not installed")
class ReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.heavy = synth.segments(Path(cls.tmp.name) / "heavy.mp4",
                                   [("navy", 6), ("0x808080", 3)], noise=True)
        cls.mid = synth.segments(Path(cls.tmp.name) / "mid.mp4",
                                 [("0x808080", 3), ("navy", 4), ("0x808080", 3)], noise=True)
        cls.face = synth.segments(Path(cls.tmp.name) / "face.mp4", [("0x808080", 8)], noise=True)
        # a planned graphic 3–7 s, then a face punch-in (a different framing of the face) 8–9 s
        cls.punch = synth.segments(Path(cls.tmp.name) / "punch.mp4",
                                   [("0x808080", 3), ("navy", 4), ("0x808080", 1), ("0x303030", 1), ("0x808080", 2)], noise=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def proj(self, name, rows, fmt="shorts", extra="captions: false\n"):
        d = Path(self.tmp.name) / name
        d.mkdir()
        return make_project(d, fmt, rows, extra_yaml=extra)

    def test_grid_reference_survives_majority_graphics(self):
        p = self.proj("a", [(0, 6, "full-frame")])
        r = cs.report(p, edit=str(self.heavy))
        self.assertEqual(r["reference"], "grid")
        self.assertAlmostEqual(r["results"][0]["value"], 0.667, delta=0.05)
        self.assertFalse(r["ok"])
        self.assertEqual(r["warnings"], [])

    def test_no_grid_falls_back_to_median_with_warning(self):
        p = self.proj("b", [])
        r = cs.report(p, edit=str(self.heavy), duration=9)
        self.assertEqual(r["reference"], "median")
        self.assertTrue(any("median of all frames" in w for w in r["warnings"]), r["warnings"])
        self.assertIn("WARN", cs.format_report(r))

    def test_explicit_face_ref_wins(self):
        p = self.proj("c", [(0, 6, "full-frame")])
        self.assertEqual(cs.report(p, edit=str(self.heavy), face_ref=7.0)["reference"], "face-ref")

    def test_over_footage_rows_are_other_not_graphics(self):
        p = self.proj("d", [(3, 7, "over-footage")], fmt="long-form", extra="")
        r = cs.report(p, edit=str(self.mid))
        self.assertEqual(r["full_frame"], [])
        self.assertEqual(r["over_footage"], [(3.0, 7.0)])

    def test_no_graphics_edit_warns(self):
        p = self.proj("e", [(20, 22, "full-frame")])
        r = cs.report(p, edit=str(self.face))
        self.assertTrue(any("0 %" in w for w in r["warnings"]), r["warnings"])

    def test_punch_ins_never_count_with_a_grid(self):
        p = self.proj("f", [(3, 7, "full-frame")])
        r = cs.report(p, edit=str(self.punch))
        self.assertEqual(len(r["full_frame"]), 1, r["full_frame"])
        a, b = r["full_frame"][0]
        self.assertAlmostEqual(a, 3.0, delta=0.25)
        self.assertAlmostEqual(b, 7.0, delta=0.25)
        self.assertAlmostEqual(r["results"][0]["value"], 4 / 11, delta=0.03)
        hits = [w for w in r["warnings"] if w.startswith("detected change outside any planned graphic")]
        self.assertEqual(len(hits), 1, r["warnings"])
        self.assertIn("punch-in or unplanned graphic?", hits[0])
        self.assertRegex(hits[0], r"at 8\.\d–9\.\d s")
        self.assertFalse(r.get("advisory"))

    def test_detected_span_overlapping_a_row_within_the_margin_is_kept(self):
        p = self.proj("g", [(3.4, 7, "full-frame")])        # the graphic starts 0.4 s before its planned row
        r = cs.report(p, edit=str(self.mid))
        self.assertEqual(len(r["full_frame"]), 1, r["full_frame"])
        self.assertAlmostEqual(r["full_frame"][0][0], 3.0, delta=0.25)
        self.assertFalse([w for w in r["warnings"] if w.startswith("detected change outside")], r["warnings"])

    def test_edit_without_a_grid_is_advisory(self):
        p = self.proj("h", [])
        r = cs.report(p, edit=str(self.punch), duration=11)
        self.assertTrue(r["advisory"])
        self.assertIn("advisory", r["source"])
        self.assertTrue(any("punch-ins may be miscounted" in w for w in r["warnings"]), r["warnings"])
        self.assertEqual(len(r["full_frame"]), 2, r["full_frame"])       # nothing to filter against
        self.assertIn("advisory", cs.format_report(r))
        (p / "storyboard.md").unlink()                                      # no storyboard at all: still advisory
        self.assertTrue(cs.report(p, edit=str(self.punch), duration=11)["advisory"])


if __name__ == "__main__":
    unittest.main()
