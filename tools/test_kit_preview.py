import io
import re
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import kit_preview as kp
import project as pj
import synth

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("node") and synth.HAVE_FFMPEG, "needs node and ffmpeg")
class KitPreviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.videos = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_every_component_full_frame_scenes_then_overlays(self):
        p, looks = kp.build(videos_dir=self.videos)
        self.assertEqual(p.name, "kit-gold")
        slots = pj.composition_slots(p)
        self.assertEqual([s["id"] for s in slots], ["01-title", "02-subtitle", "03-roadmap", "04-roadmap-2", "05-cta"])
        self.assertEqual([s["start"] for s in slots], [0, 4, 8, 12, 15])
        self.assertEqual(pj.root_attrs(p)["data-duration"], "20.5")
        self.assertEqual(sorted(x.name for x in (p / "compositions" / "overlays").glob("*.html")), ["lower-third.html", "side-text.html"])
        rows = pj.read_storyboard(p)
        self.assertEqual([r["placement"] for r in rows].count("over-footage"), 2)
        self.assertEqual(pj.validate_brief(pj.read_brief(p)), [])
        self.assertTrue((p / "assets" / "captures" / "watch-page.png").is_file())
        self.assertTrue((p / "assets" / "captures" / "face.mp4").is_file())
        self.assertIn(("01-title", "index.html", 3.6), looks)
        self.assertIn(("lower-third", "compositions/overlays/lower-third.html", 3.0), looks)
        self.assertNotIn("hf-placeholder", (p / "index.html").read_text())

    def test_overlay_rows_sit_inside_the_reel_without_overlapping(self):
        for name, comps, want in (("a", None, 20.5), ("o", ["lower-third", "side-text"], 9.0)):
            p, _ = kp.build(comps, videos_dir=self.videos / name)
            reel = float(pj.root_attrs(p)["data-duration"])
            self.assertEqual(reel, want)
            over = sorted((r for r in pj.read_storyboard(p) if r["placement"] == "over-footage"), key=lambda r: r["t_in"])
            self.assertEqual(len(over), 2)
            for r in over:
                self.assertGreaterEqual(r["t_in"], 0)
                self.assertLessEqual(r["t_out"], reel, "an overlay row ends by the reel end")
            self.assertLessEqual(over[0]["t_out"], over[1]["t_in"], "overlay rows do not overlap")

    def test_scene_and_overlay_wiring(self):
        p, _ = kp.build(videos_dir=self.videos)
        cta = (p / "compositions" / "05-cta.html").read_text()
        self.assertIn('<video id="05-cta-face" class="cta-face"', cta, "the footage video has an id (HyperFrames media rule)")
        self.assertIn("""document.querySelector('[data-composition-id="05-cta"] .cta-face')""", cta)
        ov = (p / "compositions" / "overlays" / "side-text.html").read_text()
        self.assertNotIn("<template>", ov)
        self.assertNotIn("../", ov, "overlays use root-relative paths")
        self.assertIn('<script src="lib/kit/kit.js"></script>', ov)
        self.assertIn('<script src="lib/kit/side-text.js"></script>', ov)
        self.assertIn('href="compositions/brand.css"', ov)
        self.assertIn('data-hf-mode="dark"', ov)
        for f in (p / "compositions").rglob("*.html"):
            self.assertNotRegex(f.read_text(), r"""(?:id|class)\s*=\s*["'][^"']*caption""", f.name)
        for f in (p / "compositions").rglob("*.html"):
            t = f.read_text()
            if "HFKit." in t:
                self.assertLess(t.index("document.fonts.ready"), t.index("HFText.loadFaces("), f.name)
                self.assertLess(t.index("HFText.loadFaces("), t.index("HFKit."), f.name + ": faces load before the build")

    def test_light_palette_and_subset(self):
        p, looks = kp.build(["lower-third"], palette="silver", videos_dir=self.videos)
        self.assertEqual(p.name, "kit-silver")
        self.assertEqual(pj.composition_slots(p), [])
        self.assertIn('data-hf-mode="light"', (p / "compositions" / "overlays" / "lower-third.html").read_text())
        self.assertNotIn("hf-placeholder", (p / "index.html").read_text(), "an overlay-only preview drops the scaffold placeholder (QA check 1)")
        self.assertEqual(pj.root_attrs(p)["data-duration"], "4", "the reel is as long as the overlay it carries")
        self.assertFalse((p / "assets" / "captures" / "face.mp4").exists())
        with self.assertRaisesRegex(ValueError, r"unknown kit component\(s\) badge"):
            kp.build(["badge"], videos_dir=self.videos)

    def test_cli_prints_snapshot_and_overlay_commands(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(kp.main(["kit_preview.py", "title", "side-text", "--videos-dir", str(self.videos)]), 0)
        text = out.getvalue()
        self.assertRegex(text, r"npx hyperframes snapshot \S+kit-gold --at 1,3\.6 --no-end -o \S+renders/kit/kit-gold")
        self.assertIn("-c compositions/overlays/side-text.html --format=mov -q draft", text)
        self.assertIn("(look at 3.9 s)", text)
        self.assertIn("python3 tools/sync_lib.py", text)


if __name__ == "__main__":
    unittest.main()
