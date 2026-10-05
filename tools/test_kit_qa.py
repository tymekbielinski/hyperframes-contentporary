"""Every kit component in one long-form project (tools/kit_preview.py), through the QA gate.

Unit run (fast): the HyperFrames CLI is a fake (check passes, renders copy a still clip) and the runtime probe
is a fake; checks 2, 3, 4–7 (static scan), 8 and 9's plan cross-check run for real on the kit's scenes.
Live run (network, ≈ 2 min): HF_LIVE=1 python3 -m unittest discover -s tools -p 'test_kit_qa.py' -v — the real
gate: `npx hyperframes check | preview | render`, the Chrome runtime probe, overlay renders.
"""
import os
import shlex
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import kit_preview
import project as pj
import qa
import synth
import test_qa as tq


def clean_probe(project, fmt):
    """A fake runtime probe: the reel and every overlay probed, no findings."""
    return {"timelines": 5, "tweens": 60, "samples": 40, "findings": [], "errors": [],
            "overlays": [{"file": rel, "samples": 30, "findings": [], "errors": []} for rel in qa.overlay_files(project)]}


@unittest.skipUnless(synth.HAVE_FFMPEG and shutil.which("node"), "needs ffmpeg and node")
class KitGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = {k: os.environ.get(k) for k in ("HF_CLI", "FAKE_HF_CHECK", "FAKE_HF_RENDER_SRC", "FAKE_HF_OVERLAY_SRC")}
        self.p, _ = kit_preview.build(videos_dir=Path(self.tmp.name))

    def tearDown(self):
        for k, v in self.env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self.tmp.cleanup()

    def fake_cli(self):
        d = Path(self.tmp.name)
        (d / "fake_hf.py").write_text(tq.FAKE_HF)
        total = float(pj.root_attrs(self.p)["data-duration"])
        reel, overlay = d / "reel.mp4", d / "overlay.mp4"
        synth._ffmpeg(["-f", "lavfi", "-i", f"color=c=0x101418:s=1920x1080:r=30:d={total:g}", "-pix_fmt", "yuv420p", str(reel)])
        synth._ffmpeg(["-f", "lavfi", "-i", "color=c=0x101418:s=1920x1080:r=30:d=5", "-pix_fmt", "yuv420p", str(overlay)])
        os.environ.update(HF_CLI=f"{shlex.quote(sys.executable)} {shlex.quote(str(d / 'fake_hf.py'))}", FAKE_HF_CHECK="0",
                          FAKE_HF_RENDER_SRC=str(reel), FAKE_HF_OVERLAY_SRC=str(overlay))

    def test_every_kit_component_passes_the_gate(self):
        self.fake_cli()
        r = qa.run_gate(self.p, probe=clean_probe)
        self.assertEqual({c["n"]: c["status"] for c in r["checks"]}, {n: "PASS" for n in range(1, 12)}, qa.format_report(r))
        self.assertEqual(r["probe"]["overlays"], {"compositions/overlays/lower-third.html": 30, "compositions/overlays/side-text.html": 30})

    def test_a_kit_scene_named_caption_fails_check_7(self):
        self.fake_cli()
        f = self.p / "compositions" / "01-title.html"
        f.write_text(f.read_text().replace('<div class="kit-host"></div>', '<div class="kit-host captions"></div>'))
        c7 = qa.run_gate(self.p, probe=clean_probe)["checks"][6]
        self.assertEqual(c7["status"], "FAIL")
        self.assertIn("compositions/01-title.html", c7["findings"][0])

    @unittest.skipUnless(os.environ.get("HF_LIVE") == "1", "live HyperFrames run: set HF_LIVE=1 (network, ≈ 2 min)")
    def test_live_gate(self):
        r = qa.run_gate(self.p)
        self.assertTrue(r["ok"], qa.format_report(r))


if __name__ == "__main__":
    unittest.main()
