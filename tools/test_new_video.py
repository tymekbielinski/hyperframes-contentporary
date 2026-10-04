import io
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import new_video as nv
import project as pj
import sync_lib

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class ScaffoldTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.videos = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_long_form_layout(self):
        p = nv.scaffold("10-demo", "long-form", videos_dir=self.videos)
        for rel in ["BRIEF.md", "storyboard.md", "critique.md", "assets/captures/MANIFEST.md",
                    "compositions/brand.css", "compositions/overlays/.gitkeep", "deliver/.gitkeep",
                    "index.html", "lib.lock", "lib/profile.js"]:
            self.assertTrue((p / rel).is_file(), rel)
        self.assertTrue((p / "lib" / "shorts" / "wipe.js").is_file(), "every manifest module is synced")
        self.assertEqual(sync_lib.check(p), [])

    def test_brief_template_fails_only_on_required_direction_and_film(self):
        p = nv.scaffold("10-demo", "long-form", videos_dir=self.videos)
        brief = pj.read_brief(p)
        self.assertEqual((brief["format"], brief["palette"], brief["font"], brief["hook_end"]),
                         ("long-form", "red", "helvetica", 80))
        self.assertEqual(pj.validate_brief(brief), [
            "film is required (one line: what the graphics must make the viewer feel or believe)",
            "direction is required (one line of art direction)"])
        text = (p / "BRIEF.md").read_text()
        self.assertIn('film: ""                     # REQUIRED', text)
        self.assertIn('direction: ""                # REQUIRED', text)

    def test_index_root_and_scripts_follow_format_and_palette(self):
        lf = (nv.scaffold("10-demo", "long-form", videos_dir=self.videos) / "index.html").read_text()
        self.assertIn('data-hf-mode="dark"', lf)
        self.assertIn('data-width="1920" data-height="1080"', lf)
        self.assertNotIn("lib/shorts/wipe.js", lf)
        self.assertIn('<div id="hf-placeholder" aria-hidden="true"', lf)
        self.assertIn('tl.to("#hf-placeholder", { x: 1, duration: 5, ease: "none" }, 0);', lf)
        self.assertLess(lf.index("lib/profile.js"), lf.index("lib/camera.js"))
        sh = (nv.scaffold("s9-demo", "shorts", palette="reel-light", videos_dir=self.videos) / "index.html").read_text()
        self.assertIn('data-hf-mode="light"', sh)
        self.assertIn('data-width="1080" data-height="1920"', sh)
        self.assertIn('<script src="lib/shorts/wipe.js"></script>', sh)
        brief = pj.read_brief(self.videos / "s9-demo")
        self.assertIs(brief["captions"], False)
        self.assertNotIn("hook_end", brief)

    def test_brand_css_comes_from_the_chosen_palette(self):
        css = (nv.scaffold("10-demo", "long-form", palette="paper", font="geometric", videos_dir=self.videos)
               / "compositions" / "brand.css").read_text()
        self.assertTrue(css.startswith("/* hf-mode: light"))
        self.assertIn('--hf-font-headline: "Satoshi"', css)

    def test_storyboard_and_critique_templates_parse(self):
        p = nv.scaffold("10-demo", "long-form", videos_dir=self.videos)
        self.assertEqual(pj.read_storyboard(p), [])
        self.assertIn("| graphic | smooth | on-brand | readable | synced | purposeful | craft | notes |",
                      (p / "critique.md").read_text())

    def test_refuses_bad_input_and_never_overwrites(self):
        nv.scaffold("10-demo", "long-form", videos_dir=self.videos)
        with self.assertRaisesRegex(ValueError, "already exists"):
            nv.scaffold("10-demo", "long-form", videos_dir=self.videos)
        with self.assertRaisesRegex(ValueError, "slug 'Bad Slug'"):
            nv.scaffold("Bad Slug", "long-form", videos_dir=self.videos)
        with self.assertRaisesRegex(ValueError, "palette 'neon' not in brand contentporary"):
            nv.scaffold("11-demo", "long-form", palette="neon", videos_dir=self.videos)
        with self.assertRaisesRegex(ValueError, "brand folder .*ghost not found"):
            nv.scaffold("12-demo", "long-form", brand="ghost", videos_dir=self.videos)
        self.assertFalse((self.videos / "11-demo").exists())

    def test_cli(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(nv.main(["new_video.py", "13-demo", "--format", "shorts", "--videos-dir", str(self.videos)]), 0)
            self.assertEqual(nv.main(["new_video.py", "13-demo", "--format", "shorts", "--videos-dir", str(self.videos)]), 1)
        self.assertIn("created", out.getvalue())
        self.assertIn("already exists", out.getvalue())


if __name__ == "__main__":
    unittest.main()
