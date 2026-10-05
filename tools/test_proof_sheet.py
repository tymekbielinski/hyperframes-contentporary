import html
import io
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import brandcheck
import project as pj
import proof_sheet as ps
import qa
import synth
import test_qa as tq

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class ProofSheetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.videos = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_one_scene_per_palette_in_brand_order(self):
        p = ps.build("contentporary", videos_dir=self.videos)
        self.assertEqual(p.name, "proof-contentporary")
        names = brandcheck.load_brand(ROOT / "brands" / "contentporary")["tokens"]["palettes"]
        slots = pj.composition_slots(p)
        self.assertEqual([s["id"] for s in slots], ["proof-" + n for n in names])
        self.assertEqual([s["start"] for s in slots], [i * ps.SCENE_DUR for i in range(len(names))])
        self.assertEqual(pj.root_attrs(p)["data-duration"], f"{len(names) * ps.SCENE_DUR:g}")
        self.assertEqual(len(pj.read_storyboard(p)), len(names))
        self.assertEqual(pj.validate_brief(pj.read_brief(p)), [])

    def test_each_scene_carries_its_palette_and_mode(self):
        p = ps.build("contentporary", videos_dir=self.videos)
        palettes = brandcheck.load_brand(ROOT / "brands" / "contentporary")["palettes"]
        for name in ("gold", "silver", "paper"):
            text = (p / "compositions" / f"proof-{name}.html").read_text()
            self.assertIn(f'class="proof-scene" data-hf-mode="{palettes[name]["mode"]}"', text)
            want = json.loads(subprocess.run(["node", str(ROOT / "lib" / "brand.js"), str(ROOT / "brands" / "contentporary"),
                                              "--palette", name, "--json"], capture_output=True, text=True).stdout)
            style = html.unescape(re.search(r'class="proof-scene"[^>]*style="([^"]*)"', text).group(1))
            got = dict(kv.split(": ", 1) for kv in style.split("; "))
            self.assertEqual(got, want)
            for call in ("HFKit.title(", "HFKit.subtitle(", "HFKit.lowerThird(", "HFKit.sideText("):
                self.assertIn(call, text)
            self.assertNotRegex(text, r"""(?:id|class)\s*=\s*["'][^"']*caption""", "QA check 7 must not see a caption layer")
            self.assertNotIn("hf-placeholder", text)
            self.assertLess(text.index("HFText.loadFaces("), text.index("HFKit.title("), "faces load before the kit builds")
            self.assertLess(text.index("document.fonts.ready"), text.index("HFText.loadFaces("))

    def test_refuses_unknown_brand_and_existing_project(self):
        with self.assertRaisesRegex(ValueError, "ghost not found"):
            ps.build("ghost", videos_dir=self.videos)
        ps.build("contentporary", videos_dir=self.videos)
        with self.assertRaisesRegex(ValueError, "already exists"):
            ps.build("contentporary", videos_dir=self.videos)

    def test_cli_prints_the_next_commands(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(ps.main(["proof_sheet.py", "contentporary", "--videos-dir", str(self.videos)]), 0)
        text = out.getvalue()
        self.assertIn("7 palettes, 31.5 s", text)
        self.assertIn("python3 tools/qa.py", text)
        self.assertIn("--at 4.3,8.8,13.3,17.8,22.3,26.8,31.3 --no-end", text)

    @unittest.skipUnless(synth.HAVE_FFMPEG, "needs ffmpeg")
    def test_proof_sheet_passes_the_gate(self):
        p = ps.build("contentporary", videos_dir=self.videos)
        fake, reel = self.videos / "fake_hf.py", self.videos / "reel.mp4"
        fake.write_text(tq.FAKE_HF)
        synth._ffmpeg(["-f", "lavfi", "-i", "color=c=0x101418:s=1920x1080:r=30:d=31.5", "-pix_fmt", "yuv420p", str(reel)])
        saved = {k: os.environ.get(k) for k in ("HF_CLI", "FAKE_HF_CHECK", "FAKE_HF_RENDER_SRC")}
        os.environ.update(HF_CLI=f"{shlex.quote(sys.executable)} {shlex.quote(str(fake))}", FAKE_HF_CHECK="0", FAKE_HF_RENDER_SRC=str(reel))
        try:
            r = qa.run_gate(p, probe=tq.clean_probe)
        finally:
            for k, v in saved.items():
                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        self.assertEqual({c["n"]: c["status"] for c in r["checks"]}, {n: "PASS" for n in range(1, 12)}, qa.format_report(r))


if __name__ == "__main__":
    unittest.main()
