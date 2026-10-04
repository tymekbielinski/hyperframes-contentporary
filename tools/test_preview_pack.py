import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import media
import preview_pack as pp
import synth

HEADER = "| t_in | t_out | words | placement | type | beats | ease | marks |\n|---|---|---|---|---|---|---|---|\n"
CRITIQUE = """# Critique — demo

## Round 1

| graphic | smooth | on-brand | readable | synced | purposeful | craft | notes |
|---|---|---|---|---|---|---|---|
| 01-hook | 5 | 9 | 9 | 9 | 9 | 9 | snapped |

## Round 2

| graphic | smooth | on-brand | readable | synced | purposeful | craft | notes |
|---|---|---|---|---|---|---|---|
| 01-hook | 9 | 9 | 9 | 9 | 9 | 9 | eased now |
| 02-proof | 9 | 7 | 9 | 9 | ? | 9 | palette drift |
"""


class CritiqueTests(unittest.TestCase):
    def test_last_round_low_scorers_first(self):
        c = pp.parse_critique(CRITIQUE)
        self.assertEqual(c["round"], 2)
        self.assertEqual([r["graphic"] for r in c["rows"]], ["02-proof", "01-hook"])
        self.assertEqual(c["rows"][0]["low"], ["on-brand", "purposeful"])
        self.assertIsNone(c["rows"][0]["scores"]["purposeful"])
        self.assertEqual(c["rows"][1]["low"], [])

    def test_no_rounds(self):
        self.assertEqual(pp.parse_critique("# nothing yet"), {"round": None, "rows": []})


@unittest.skipUnless(synth.HAVE_FFMPEG, "ffmpeg/ffprobe not installed")
class BuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        self.p = d / "10-demo"
        self.p.mkdir()
        (self.p / "BRIEF.md").write_text('```yaml\nformat: long-form\nhook_end: 80\nexceptions:\n  - "F09: recreated calendar"\n```\n')
        (self.p / "index.html").write_text(
            '<div id="root" data-composition-id="main">'
            '<div data-composition-id="01-hook" data-composition-src="compositions/01.html" data-start="0" data-duration="2"></div>'
            '<div data-composition-id="02-proof" data-composition-src="compositions/02.html" data-start="2" data-duration="2"></div></div>')
        (self.p / "storyboard.md").write_text(HEADER + '| 10.0 | 12.0 | "hook" | full-frame | B1 | — | — | — |\n'
                                              '| 100.0 | 102.0 | "proof" | full-frame | A1 | — | — | — |\n')
        (self.p / "transcript.json").write_text(json.dumps([{"text": "x", "start": 0, "end": 120}]))
        (self.p / "critique.md").write_text(CRITIQUE)
        self.reel = synth.segments(d / "reel.mp4", [("red", 2), ("blue", 2)])
        self.overlays = d / "overlays"
        self.overlays.mkdir()
        synth.prores(self.overlays / "01-key-line.mov", 1)

    def tearDown(self):
        self.tmp.cleanup()

    def test_pack_contents(self):
        index = pp.build(self.p, self.reel, self.overlays)
        out = index.parent
        self.assertEqual(out, self.p / "renders" / "preview")
        self.assertEqual(sorted(p.name for p in (out / "frames").iterdir()), ["001.png", "002.png", "003.png"])
        for f in sorted((out / "frames").iterdir()):
            self.assertEqual(media.video_info(f)["pix_fmt"], "rgb24", f.name)   # alpha flattened: tile needs one format
        sheet = media.video_info(out / "contact-sheet.png")
        self.assertEqual(sheet["width"], 4 * 480 + 5 * 8)
        rgb = media.run(["ffmpeg", "-v", "error", "-i", str(out / "contact-sheet.png"), "-vf", "scale=4:1",
                         "-pix_fmt", "rgb24", "-f", "rawvideo", "-"], binary=True)
        r, g = rgb[6], rgb[7]                                    # third tile: the 50 % red overlay over grey
        self.assertGreater(r, g + 20, "the overlay tile shows the layout, not just the backdrop")
        self.assertAlmostEqual(media.video_info(out / "hook.mp4")["duration"], 2.0, delta=0.1)
        self.assertAlmostEqual(media.video_info(out / "body.mp4")["duration"], 2.0, delta=0.1)
        page = index.read_text()
        self.assertLess(page.index("02-proof"), page.index("eased now"), "low scorers listed first")
        self.assertIn("1 graphic(s) below 8", page)
        self.assertIn("F09: recreated calendar", page)
        self.assertIn('aria-label="density timeline"', page)
        self.assertIn("No renders/qa-report.json", page)
        self.assertIn("over-footage · 01-key-line", page)

    def test_qa_report_is_summarised_and_rebuild_replaces_the_pack(self):
        (self.p / "renders").mkdir()
        (self.p / "renders" / "qa-report.json").write_text(json.dumps(
            {"ok": False, "checks": [{"n": 9, "name": "Settle before cut", "status": "FAIL", "findings": ["02-proof: still moving"]}]}))
        pp.build(self.p, self.reel)
        stray = self.p / "renders" / "preview" / "frames" / "999.png"
        stray.write_text("old")
        page = pp.build(self.p, self.reel).read_text()
        self.assertFalse(stray.exists())
        self.assertIn("Automated gate — <span class='fail'>FAIL</span>", page)
        self.assertIn("02-proof: still moving", page)

    def test_clip_shorter_than_the_graphic_gets_a_named_placeholder_tile(self):
        import synth as sy
        clip = sy.segments(Path(self.tmp.name) / "short.mp4", [("red", 1)])
        page = pp.build(self.p, clip).read_text()
        self.assertIn("FRAME MISSING", page)
        self.assertEqual(len(list((self.p / "renders" / "preview" / "frames").iterdir())), 2)

    def test_unreadable_qa_report_is_not_a_pass(self):
        (self.p / "renders").mkdir()
        (self.p / "renders" / "qa-report.json").write_text("{nope")
        page = pp.build(self.p, self.reel).read_text()
        self.assertIn("UNKNOWN", page)
        self.assertNotIn("<span class='pass'>PASS</span>", page.split("<h2>Drafts")[0].split("Automated gate")[1])

    def test_qa_warnings_are_shown(self):
        (self.p / "renders").mkdir()
        (self.p / "renders" / "qa-report.json").write_text(json.dumps({"ok": True, "checks": [], "warnings": ["probe skipped"]}))
        self.assertIn("probe skipped", pp.build(self.p, self.reel).read_text())

    def test_suffixed_round_heading_is_the_latest(self):
        text = CRITIQUE + "\n## Round 3 (after fixes)\n\n| graphic | smooth | on-brand | readable | synced | purposeful | craft | notes |\n|---|---|---|---|---|---|---|---|\n| 03-x | 9 | 9 | 9 | 9 | 9 | 9 | ok |\n"
        c = pp.parse_critique(text)
        self.assertEqual((c["round"], [r["graphic"] for r in c["rows"]]), (3, ["03-x"]))
        c = pp.parse_critique("## Round two\n| a | 9 | 9 | 9 | 9 | 9 | 9 | x |\n")
        self.assertIsNone(c["round"])
        self.assertIn("unparseable round heading", c["warnings"][0])

    def test_seven_cells_and_malformed_rows_are_never_dropped(self):
        head = "## Round 1\n\n| graphic | s |\n|---|---|\n"
        c = pp.parse_critique(head + "| 01-a | 9 | 9 | 9 | 9 | 9 | 9 |\n| 02-b | 9 | 9 |\n| junk <b> |\n")
        by = {r["graphic"]: r for r in c["rows"]}
        self.assertEqual(by["01-a"]["low"], [])
        self.assertEqual(by["01-a"]["notes"], "")
        self.assertEqual(len(by["02-b"]["low"]), 6)
        self.assertIn("malformed row", by["02-b"]["notes"])
        self.assertIn("junk <b>", by["junk <b>"]["graphic"])
        self.assertEqual(len(c["warnings"]), 2)

    def test_out_of_range_scores_are_unknown(self):
        c = pp.parse_critique("## Round 1\n| g | 0 | 11 | 99 | 9 | 9 | 9 | n |\n")
        r = c["rows"][0]
        self.assertEqual(r["low"], ["smooth", "on-brand", "readable"])
        self.assertIsNone(r["scores"]["readable"])

    def test_undecodable_files_are_named_not_tracebacks(self):
        (self.p / "critique.md").write_bytes(b"\xff\xfe\x00bad")
        (self.p / "renders").mkdir()
        (self.p / "renders" / "qa-report.json").write_bytes(b"\xff\xfe")
        page = pp.build(self.p, self.reel).read_text()
        self.assertIn("critique.md is unreadable", page)
        self.assertIn("UNKNOWN", page)

    def test_body_skip_is_visible_and_odd_checks_are_tolerated(self):
        (self.p / "storyboard.md").write_text(HEADER + '| 10.0 | 12.0 | "hook" | full-frame | B1 | — | — | — |\n')
        (self.p / "renders").mkdir()
        (self.p / "renders" / "qa-report.json").write_text(json.dumps(
            {"ok": False, "checks": ["oops", {"n": "<b>", "name": "x", "status": "FAIL", "findings": None}]}))
        page = pp.build(self.p, self.reel).read_text()
        self.assertIn("body draft skipped", page)
        self.assertIn("unreadable check entry", page)
        self.assertNotIn("<b>", page)

    def test_html_is_escaped(self):
        evil = "<script>alert(1)</script>&"
        (self.p / "BRIEF.md").write_text('```yaml\nformat: long-form\nhook_end: 80\nexceptions:\n  - "<script>x</script> & y"\n```\n')
        (self.p / "critique.md").write_text(CRITIQUE.replace("snapped", evil).replace("eased now", evil))
        evil_dir = Path(self.tmp.name) / "<i>&slug"
        self.p.rename(evil_dir)
        page = pp.build(evil_dir, self.reel).read_text()
        self.assertNotIn("<script>", page)
        self.assertNotIn("<i>", page)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;&amp;", page)
        self.assertIn("&lt;script&gt;x&lt;/script&gt; &amp; y", page)

    def test_cli_missing_render(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(pp.main(["preview_pack.py", str(self.p)]), 1)
        self.assertIn("qa-draft.mp4 not found", out.getvalue())


if __name__ == "__main__":
    unittest.main()
