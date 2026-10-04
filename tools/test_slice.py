import csv
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import media
import slice as sl
import synth

HD = (1920, 1080)
HEADER = "| t_in | t_out | words | placement | type | beats | ease | marks |\n|---|---|---|---|---|---|---|---|\n"
INDEX = """<div id="root" data-composition-id="main" data-hf-mode="dark">
  <div data-composition-id="01-hook" data-composition-src="compositions/01-hook.html" data-start="0" data-duration="2"></div>
  <div data-composition-id="02-proof" data-composition-src="compositions/02-proof.html" data-start="2" data-duration="2"></div>
</div>"""
GRID = HEADER + (
    '| 10.0 | 12.0 | "the hook" | full-frame | B1 | — | ease.enter | — |\n'
    '| 20.0 | 21.0 | "key line" | over-footage | lower-third | — | ease.enter | — |\n'
    '| 30.5 | 32.5 | "the proof" | full-frame | A1 | — | ease.enter | highlight-block |\n')


class TimecodeTests(unittest.TestCase):
    def test_tc(self):
        self.assertEqual(sl.tc(96.5, 30), "00:01:36:15")
        self.assertEqual(sl.tc_file(96.5, 30), "01-36-15")
        self.assertEqual(sl.tc_file(3725.0, 30), "01-02-05-00")


@unittest.skipUnless(synth.HAVE_FFMPEG, "ffmpeg/ffprobe not installed")
class SliceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        self.p = d / "10-demo"
        self.p.mkdir()
        (self.p / "BRIEF.md").write_text("```yaml\nformat: long-form\n```\n")
        (self.p / "index.html").write_text(INDEX)
        (self.p / "storyboard.md").write_text(GRID)
        self.reel = synth.segments(d / "reel.mp4", [("red", 2), ("blue", 2)], size=HD)   # solid colours: 1080p encodes stay fast
        self.overlays = d / "overlays"
        self.overlays.mkdir()
        synth.prores(self.overlays / "01-key-line.mov", 1, size=HD)

    def tearDown(self):
        self.tmp.cleanup()

    def test_clips_csv_and_readme(self):
        stale = self.p / "deliver" / "scene-09_00-00-00.mp4"
        stale.parent.mkdir()
        stale.write_text("old")
        rows = sl.slice_project(self.p, self.reel, self.overlays)
        out = self.p / "deliver"
        self.assertEqual([r["file"] for r in rows], ["scene-01_00-10-00.mp4", "scene-02_00-30-15.mp4", "overlay-01_00-20-00.mov"])
        self.assertFalse(stale.exists(), "a re-slice removes stale clips")
        for name in ("scene-01_00-10-00.mp4", "scene-02_00-30-15.mp4"):
            info = media.video_info(out / name)
            self.assertEqual((info["frames"], info["codec"], info["pix_fmt"]), (60, "h264", "yuv420p"), name)
        self.assertEqual(media.video_info(out / "overlay-01_00-20-00.mov")["codec"], "prores")
        with open(out / "TIMECODES.csv") as f:
            csv_rows = list(csv.DictReader(f))
        self.assertEqual(list(csv_rows[0]), sl.COLUMNS)
        self.assertEqual(csv_rows[1]["timeline_in_tc"], "00:00:30:15")
        self.assertEqual(csv_rows[1]["timeline_out_tc"], "00:00:32:15")
        self.assertEqual((csv_rows[1]["in_frame"], csv_rows[1]["out_frame"], csv_rows[1]["title"]), ("915", "975", "the proof"))
        self.assertEqual(csv_rows[2]["kind"], "over-footage")
        readme = (out / "README.txt").read_text()
        self.assertIn("scene-01_00-10-00.mp4  ->  drop at 00:00:10:00", readme)
        self.assertIn("ProRes 4444 with alpha", readme)

    def test_cut_is_frame_exact_at_scene_boundaries(self):
        reel = synth.segments(Path(self.tmp.name) / "two.mp4", [("red", 2), ("blue", 2)], size=HD)
        sl.slice_project(self.p, reel, self.overlays)
        first = media.gray_frames(self.p / "deliver" / "scene-01_00-10-00.mp4", 30)
        second = media.gray_frames(self.p / "deliver" / "scene-02_00-30-15.mp4", 30)
        ref = media.gray_frames(reel, 1)
        red, blue = ref[1][0], ref[3][0]
        self.assertGreater(abs(red - blue), 20)
        self.assertEqual((len(first), len(second)), (60, 60))
        self.assertLess(abs(first[-1][0] - red), 4, "scene 1 ends on its own last frame")
        self.assertLess(abs(second[0][0] - blue), 4, "scene 2 starts on its own first frame")

    def test_failure_leaves_previous_delivery_untouched(self):
        sl.slice_project(self.p, self.reel, self.overlays)
        out = self.p / "deliver"
        before = {f.name: f.read_bytes() for f in out.iterdir()}
        real, calls = sl._cut, []

        def flaky(*a):
            calls.append(1)
            if len(calls) == 2:
                raise sl.SliceError("boom")
            return real(*a)
        sl._cut = flaky
        try:
            with self.assertRaisesRegex(sl.SliceError, "boom"):
                sl.slice_project(self.p, self.reel, self.overlays)
        finally:
            sl._cut = real
        self.assertEqual({f.name: f.read_bytes() for f in out.iterdir()}, before)

    def test_short_reel_is_refused_by_frame_count(self):
        with self.assertRaisesRegex(sl.SliceError, "frames, expected 60"):
            real = sl.plan
            clips = real(self.p, self.reel, self.overlays)
            clips[1]["src_start"] = 3.5   # runs off the end of the 4 s reel
            sl._cut(self.reel, clips[1], Path(self.tmp.name) / "x.mp4", 30.0)

    def test_fps_mismatch(self):
        with self.assertRaisesRegex(sl.SliceError, "reel runs at 30 fps but --fps is 25"):
            sl.plan(self.p, self.reel, self.overlays, fps=25.0)

    def test_clips_are_silent(self):
        reel = Path(self.tmp.name) / "audio.mp4"
        media.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(self.reel), "-f", "lavfi", "-i", "sine=d=4",
                   "-c:v", "copy", "-c:a", "aac", "-shortest", str(reel)])
        probe = lambda f: media.run([media.tool("ffprobe"), "-v", "error", "-select_streams", "a",
                                     "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(f)]).strip()
        self.assertEqual(probe(reel), "audio", "the test reel has audio")
        sl.slice_project(self.p, reel, self.overlays)
        self.assertEqual(probe(self.p / "deliver" / "scene-01_00-10-00.mp4"), "")

    def test_duration_mismatch_names_slot_and_row(self):
        (self.p / "storyboard.md").write_text(GRID.replace("| 30.5 | 32.5 |", "| 30.5 | 33.5 |"))
        with self.assertRaisesRegex(sl.SliceError, r"slot 02-proof lasts 2\.00 s but storyboard row 3 \(line 5\) lasts 3\.00 s"):
            sl.plan(self.p, self.reel, self.overlays)

    def test_count_mismatch(self):
        (self.p / "storyboard.md").write_text(HEADER + '| 10.0 | 12.0 | "x" | full-frame | B1 | — | — | — |\n')
        with self.assertRaisesRegex(sl.SliceError, "2 scene slots but storyboard.md has 1 full-frame rows"):
            sl.plan(self.p, self.reel)

    def test_overlay_must_be_prores_4444_alpha(self):
        (self.overlays / "01-key-line.mov").unlink()
        synth.prores(self.overlays / "01-key-line.mov", 1, size=HD, alpha=False)
        with self.assertRaisesRegex(sl.SliceError, "not ProRes 4444 with alpha"):
            sl.plan(self.p, self.reel, self.overlays)

    def test_missing_overlays_dir(self):
        with self.assertRaisesRegex(sl.SliceError, r"1 over-footage rows but \(no --overlays dir\) has 0 \.mov files"):
            sl.plan(self.p, self.reel)

    def test_reel_and_overlays_must_be_1920x1080(self):
        small = synth.moving(Path(self.tmp.name) / "small.mp4", 4)
        with self.assertRaisesRegex(sl.SliceError, r"the reel is 160×90, expected 1920×1080 \(long-form\)"):
            sl.plan(self.p, small, self.overlays)
        (self.overlays / "01-key-line.mov").unlink()
        synth.prores(self.overlays / "01-key-line.mov", 1)
        with self.assertRaisesRegex(sl.SliceError, r"01-key-line.mov is 160×90, expected 1920×1080 \(long-form\)"):
            sl.plan(self.p, self.reel, self.overlays)

    def test_shorts_are_refused(self):
        (self.p / "BRIEF.md").write_text("```yaml\nformat: shorts\n```\n")
        with self.assertRaisesRegex(sl.SliceError, "one finished MP4"):
            sl.plan(self.p, self.reel)

    def test_cli(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(sl.main(["slice.py", str(self.p), "--reel", str(self.reel), "--overlays", str(self.overlays)]), 0)
            self.assertEqual(sl.main(["slice.py", str(self.p), "--reel", str(self.reel)]), 1)
        self.assertIn("3 clips + TIMECODES.csv + README.txt", out.getvalue())


if __name__ == "__main__":
    unittest.main()
