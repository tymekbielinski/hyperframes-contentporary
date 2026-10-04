import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import media
import probe_cuts
import scan_flicker
import synth

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(synth.HAVE_FFMPEG, "ffmpeg/ffprobe not installed")
class MediaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        d = Path(cls.tmp.name)
        cls.cuts = synth.segments(d / "cuts.mp4", [("red", 1), ("blue", 1), ("white", 1)])

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_video_info(self):
        info = media.video_info(self.cuts)
        self.assertEqual((info["width"], info["height"], info["fps"], info["frames"]), (160, 90, 30.0, 90))
        self.assertAlmostEqual(info["duration"], 3.0, places=2)

    def test_missing_file_is_a_named_error(self):
        with self.assertRaisesRegex(media.MediaError, "nope.mp4 not found"):
            media.video_info("nope.mp4")

    def test_scene_cuts_at_the_0_20_threshold(self):
        self.assertEqual(media.scene_cuts(self.cuts), [1.0, 2.0])

    def test_frame_diffs_one_per_frame_pair(self):
        d = media.frame_diffs(self.cuts)
        self.assertEqual(len(d), 89)
        self.assertEqual(d[0], 0.0)
        self.assertGreater(d[29], 10)    # red → blue between frames 29 and 30

    def test_extract_frame_flattens_alpha_over_a_backdrop(self):
        with tempfile.TemporaryDirectory() as t:
            mov = synth.prores(Path(t) / "a.mov", 1)            # red at 50 % alpha
            png = media.extract_frame(mov, 0.5, Path(t) / "a.png", width=160, background="0x3a3a3a")
            self.assertEqual(media.video_info(png)["pix_fmt"], "rgb24")
            r, g, b = media.run(["ffmpeg", "-v", "error", "-i", str(png), "-vf", "crop=1:1:80:45", "-f", "rawvideo",
                                 "-pix_fmt", "rgb24", "-"], binary=True)
            self.assertGreater(r, g + 60, (r, g, b))           # red over grey, not grey alone
            self.assertGreater(g, 15, (r, g, b))                # and the grey shows through

    def test_extract_frame_past_the_end_is_a_named_error(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaisesRegex(media.MediaError, "no frame at t=99.000s"):
                media.extract_frame(self.cuts, 99, Path(t) / "x.png")

    def test_video_info_parsing_edge_cases(self):
        good = {"streams": [{"width": 1, "height": 1, "r_frame_rate": "0/0", "avg_frame_rate": "25/1"}],
                "format": {"duration": "2.0"}}
        self.assertEqual(media._parse_info("f", good)["fps"], 25.0)
        with self.assertRaisesRegex(media.MediaError, "unknown duration"):
            media._parse_info("f", {**good, "format": {"duration": "N/A"}})
        bad = {"streams": [{"width": 1, "height": 1, "r_frame_rate": "0/0", "avg_frame_rate": "0/0"}], "format": {}}
        with self.assertRaisesRegex(media.MediaError, "frame rate"):
            media._parse_info("f", bad)

    def test_path_with_spaces_and_unicode(self):
        with tempfile.TemporaryDirectory() as t:
            f = synth.segments(Path(t) / "my clip é日本.mp4", [("red", 1), ("white", 1)])
            self.assertEqual(media.scene_cuts(f), [1.0])
            self.assertEqual(len(media.frame_diffs(f)), 59)
            self.assertEqual(media.extract_frame(f, 0.5, Path(t) / "frame é.png").is_file(), True)

    def test_gray_frames(self):
        frames = media.gray_frames(self.cuts, 2)
        self.assertEqual((len(frames), len(frames[0])), (6, 32 * 18))
        self.assertGreater(frames[5][0], frames[3][0])   # white is brighter than blue


@unittest.skipUnless(synth.HAVE_FFMPEG, "ffmpeg/ffprobe not installed")
class ProbeCutsTests(unittest.TestCase):
    def test_scene_end_is_cut_plus_exit(self):
        self.assertEqual(probe_cuts.scene_ends([1.0, 2.5]), [{"cut": 1.0, "scene_end": 1.36}, {"cut": 2.5, "scene_end": 2.86}])
        self.assertEqual(probe_cuts.scene_ends([1.0], 0.5), [{"cut": 1.0, "scene_end": 1.5}])

    def test_defaults_match_shorts_profile(self):
        md = (ROOT / "standards" / "formats" / "shorts.md").read_text()
        self.assertIn("gt(scene,%.2f)" % probe_cuts.THRESHOLD, md)
        self.assertIn("| duration out | **%.2fs** |" % probe_cuts.EXIT, md)

    def test_cli_json(self):
        with tempfile.TemporaryDirectory() as t:
            f = synth.segments(Path(t) / "c.mp4", [("red", 1), ("white", 1)])
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(probe_cuts.main(["probe_cuts.py", str(f), "--json"]), 0)
            self.assertEqual(json.loads(out.getvalue()), [{"cut": 1.0, "scene_end": 1.36}])
            err = io.StringIO()
            with redirect_stdout(io.StringIO()) as so, redirect_stderr(err):
                self.assertEqual(probe_cuts.main(["probe_cuts.py", str(Path(t) / "missing.mp4")]), 2)
            self.assertEqual(so.getvalue(), "")
            self.assertIn("missing.mp4 not found", err.getvalue())


@unittest.skipUnless(synth.HAVE_FFMPEG, "ffmpeg/ffprobe not installed")
def clip(path, source, boxes, secs=3):
    """A 160×90, 30 fps synthetic clip: lavfi `source` with white 60×40 boxes, each "box@<x>,<y>:<enable expr>"."""
    parts = []
    for b in boxes:
        pos, enable = b[len("box@"):].split(":", 1)
        x, y = pos.split(",")
        parts.append(f"drawbox=x={x}:y={y}:w=60:h=40:color=white:t=fill:enable='{enable}'")
    synth._ffmpeg(["-f", "lavfi", "-i", f"{source}{':' if '=' in source else '='}s=160x90:r=30:d={secs}", "-vf", ",".join(parts), "-pix_fmt", "yuv420p", str(path)])
    return path


class FlickerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        d = Path(cls.tmp.name)
        cls.smooth = synth.moving(d / "smooth.mp4", 3)
        cls.glitch = synth.moving(d / "glitch.mp4", 3, glitch_frame=45)
        cls.appear = clip(d / "appear.mp4", "testsrc2", ["box@20,20:gte(n,45)"])                   # pops in, stays
        cls.block3 = clip(d / "block3.mp4", "testsrc2", ["box@20,20:between(n,45,47)"])            # 3-frame wrong-state block
        cls.block6 = clip(d / "block6.mp4", "testsrc2", ["box@20,20:between(n,45,50)"])            # 6-frame block
        cls.stagger = clip(d / "stagger.mp4", "testsrc2", ["box@10,10:gte(n,45)", "box@90,40:gte(n,49)"])   # 4 frames apart
        cls.stagger_still = clip(d / "stagger_still.mp4", "color=c=0x202020", ["box@10,10:gte(n,45)", "box@90,40:gte(n,49)"])

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_find_flicker_rule(self):
        def pictures(levels):
            """A fake compare: frame f shows picture levels.get(f, 0); distance = |level difference|."""
            return lambda pairs: [abs(levels.get(a, 0) - levels.get(b, 0)) for a, b in pairs]
        smooth = [3.0, 3.2, 3.1, 3.4, 3.3, 3.2, 3.1, 3.0]
        self.assertEqual(scan_flicker.find_flicker(smooth, pictures({})), [])
        spiky = smooth[:4] + [30.0, 28.0] + smooth[4:]          # frame 5 away, frame 6 back: both steps reported
        self.assertEqual(scan_flicker.find_flicker(spiky, pictures({5: 100})), [(5, 30.0, 3.2), (6, 28.0, 3.2)])
        self.assertEqual(scan_flicker.find_flicker(spiky, pictures({5: 100, 6: 200})), [])   # two jumps, no return
        block = smooth[:4] + [30.0] + [3.1] * 7 + [28.0] + smooth[4:]   # frames 5–12 away, back at 13: still counts
        self.assertEqual([h[0] for h in scan_flicker.find_flicker(block, pictures({f: 100 for f in range(5, 13)}))], [5, 13])
        late = smooth[:4] + [30.0] + [3.1] * 8 + [28.0] + smooth[4:]    # 9 frames away: beyond MAX_RETURN
        self.assertEqual(scan_flicker.find_flicker(late, pictures({f: 100 for f in range(5, 14)})), [])
        step = smooth[:4] + [30.0] + smooth[4:]                 # one isolated step: a hard appear, not flicker
        self.assertEqual(scan_flicker.find_flicker(step, pictures({f: 100 for f in range(5, 20)})), [])
        self.assertEqual(scan_flicker.find_flicker([0.0] * 6 + [8.7] + [0.0] * 6, pictures({})), [])
        seen = []
        scan_flicker.find_flicker(smooth[:4] + [30.0, 3.1, 3.1, 28.0] + smooth[4:], lambda pairs: seen.extend(pairs) or [0.0] * len(pairs))
        self.assertEqual(seen, [(4, 8), (4, 7)])               # before-out vs after-back, before-out vs last away frame
        ramp = [1, 2, 4, 8, 12, 16, 12, 8, 4, 2, 1]    # a camera move: big but smooth
        self.assertEqual(scan_flicker.find_flicker([float(x) for x in ramp], pictures({})), [])

    def test_smooth_motion_passes(self):
        self.assertEqual(scan_flicker.scan(self.smooth)["flicker"], [])

    def test_one_frame_glitch_is_reported(self):
        self.assertEqual([hit[0] for hit in scan_flicker.scan(self.glitch)["flicker"]], [45, 46])
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(scan_flicker.main(["scan_flicker.py", str(self.glitch)]), 1)
            self.assertEqual(scan_flicker.main(["scan_flicker.py", str(self.smooth)]), 0)
        self.assertIn("FLICKER=2", out.getvalue())

    def test_single_hard_appear_is_not_flicker(self):
        self.assertEqual(scan_flicker.scan(self.appear)["flicker"], [])

    def test_multi_frame_glitch_blocks_are_reported(self):
        self.assertEqual([hit[0] for hit in scan_flicker.scan(self.block3)["flicker"]], [45, 48])
        self.assertEqual([hit[0] for hit in scan_flicker.scan(self.block6)["flicker"]], [45, 51])

    def test_staggered_pop_ins_are_not_flicker(self):
        self.assertEqual(scan_flicker.scan(self.stagger)["flicker"], [])
        self.assertEqual(scan_flicker.scan(self.stagger_still)["flicker"], [])

    def test_bad_file_does_not_stop_the_scan(self):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = scan_flicker.main(["scan_flicker.py", "nope.mp4", str(self.smooth)])
        self.assertEqual(code, 2)
        self.assertIn("smooth.mp4", out.getvalue())
        self.assertIn("nope.mp4 not found", err.getvalue())


if __name__ == "__main__":
    unittest.main()
