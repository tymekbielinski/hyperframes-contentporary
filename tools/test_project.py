import json
import tempfile
import unittest
from pathlib import Path

import project as pj

ROOT = Path(__file__).resolve().parents[1]

GOOD_LF = {
    "format": "long-form", "film": "Make the viewer believe the system is predictable.",
    "direction": "One canvas per argument; proof first, then the number.",
    "brand": "contentporary", "palette": "red", "font": "helvetica",
    "hook_end": 80, "screen_share": [[302.5, 317.0]],
    "exceptions": ["F09: recreated Google Calendar — no shareable real account"],
}

BRIEF_MD = """# BRIEF — demo

Free prose above the block is fine.

```yaml
format: shorts          # long-form | shorts
film: "One line: it's about trust."
direction: 'Hard cuts; tall camera worlds'
references:
  - "youtube.com/watch?v=HrYMfy6MZtA — camera travel"
brand: contentporary
palette: reel-dark
font: geometric
overrides:
  accentScript: "#BACE7A"   # quoted: a bare # starts a comment
captions: false
screen_share:
  - [302.5, 317.0]
exceptions:
```
"""

GRID = """# Storyboard

| t_in | t_out | words | placement | type | beats | ease | marks |
|---|---|---|---|---|---|---|---|
| 62.2 | 68.0 | "it's a system \\| that prints…" | full-frame | roadmap | line draws 0–1.2 | ease.camera | — |
| 74.1 | 79.4 | "1.2 million views" | over-footage | lower-third | lands 0.0 | ease.enter | highlight-block |

Notes after the table are ignored.
"""


class YamlSubsetTests(unittest.TestCase):
    def test_brief_block_parses(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / "BRIEF.md").write_text(BRIEF_MD)
            b = pj.read_brief(t)
        self.assertEqual(b["format"], "shorts")
        self.assertEqual(b["film"], "One line: it's about trust.")
        self.assertEqual(b["direction"], "Hard cuts; tall camera worlds")
        self.assertEqual(b["overrides"], {"accentScript": "#BACE7A"})
        self.assertIs(b["captions"], False)
        self.assertEqual(b["screen_share"], [[302.5, 317.0]])
        self.assertIsNone(b["exceptions"])
        self.assertEqual(b["references"], ["youtube.com/watch?v=HrYMfy6MZtA — camera travel"])

    def test_bad_line_names_the_file_line(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / "BRIEF.md").write_text("# B\n\n```yaml\nformat: shorts\nthis is not yaml\n```\n")
            with self.assertRaisesRegex(pj.ProjectError, r"BRIEF\.md line 5: expected 'key: value'"):
                pj.read_brief(t)

    def test_missing_block_and_file(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaisesRegex(pj.ProjectError, "BRIEF.md not found"):
                pj.read_brief(t)
            (Path(t) / "BRIEF.md").write_text("format: shorts\n")
            with self.assertRaisesRegex(pj.ProjectError, "no ```yaml block"):
                pj.read_brief(t)

    def test_duplicate_key_and_tabs_rejected(self):
        with self.assertRaisesRegex(pj.ProjectError, "duplicate key 'font'"):
            pj.parse_yaml_subset("font: a\nfont: b\n")
        with self.assertRaisesRegex(pj.ProjectError, "spaces, not tabs"):
            pj.parse_yaml_subset("gotchas:\n\t- x\n")


class ValidateBriefTests(unittest.TestCase):
    def test_good_long_form_brief(self):
        self.assertEqual(pj.validate_brief(dict(GOOD_LF), ROOT), [])

    def test_required_fields_named(self):
        errs = pj.validate_brief({"format": "long-form"}, ROOT)
        for field in ("film", "direction", "brand", "palette", "font"):
            self.assertTrue(any(e.startswith(f"{field} is required") for e in errs), (field, errs))

    def test_shorts_needs_captions_flag(self):
        b = dict(GOOD_LF, format="shorts", palette="reel-dark")
        del b["hook_end"], b["screen_share"]
        self.assertIn("captions is required for Shorts (true or false)", pj.validate_brief(b, ROOT))
        b["captions"] = True
        self.assertEqual(pj.validate_brief(b, ROOT), [])

    def test_long_form_rejects_captions_and_bad_ranges(self):
        b = dict(GOOD_LF, captions=True, screen_share=[[317.0, 302.5]], hook_end=-5)
        errs = pj.validate_brief(b, ROOT)
        self.assertIn("captions: long-form has no running captions (key-line lower thirds only)", errs)
        self.assertIn("screen_share range [317.0, 302.5] must be [start, end] seconds with start < end", errs)
        self.assertIn("hook_end must be a positive number of seconds, got -5", errs)
        self.assertIn("screen_share must be a list of [start, end] ranges",
                      pj.validate_brief(dict(GOOD_LF, screen_share="302-317"), ROOT))

    def test_unknown_field_catches_typos(self):
        errs = pj.validate_brief(dict(GOOD_LF, palete="red"), ROOT)
        self.assertTrue(errs[0].startswith("unknown BRIEF field 'palete'"), errs)

    def test_unquoted_colour_is_a_comment_and_a_named_error(self):
        b = pj.parse_yaml_subset("overrides:\n  accentScript: #BACE7A\n")
        self.assertEqual(b, {"overrides": {"accentScript": None}})
        self.assertIn("override 'accentScript' is not a colour: None",
                      pj.validate_brief(dict(GOOD_LF, overrides=b["overrides"]), ROOT))

    def test_exception_needs_a_reason(self):
        errs = pj.validate_brief(dict(GOOD_LF, exceptions=["F09", "check 6:   "]), ROOT)
        self.assertIn("exception 'F09' has no reason (each entry is '<what>: <reason>')", errs)
        self.assertIn("exception 'check 6:   ' has no reason (each entry is '<what>: <reason>')", errs)

    def test_brand_choice_flows_through_brandcheck(self):
        errs = pj.validate_brief(dict(GOOD_LF, palette="neon", font="comic"), ROOT)
        self.assertTrue(any(e.startswith("palette 'neon' not in brand contentporary") for e in errs), errs)
        self.assertTrue(any(e.startswith("font 'comic' not in brand contentporary") for e in errs), errs)
        self.assertIn("brand 'ghost': no folder brands/ghost/", pj.validate_brief(dict(GOOD_LF, brand="ghost"), ROOT))

    def test_draft_brand_fails_check_3(self):
        with tempfile.TemporaryDirectory() as t:
            src = ROOT / "brands" / "contentporary"
            dst = Path(t) / "brands" / "contentporary"
            (dst / "palettes").mkdir(parents=True)
            tokens = json.loads((src / "tokens.json").read_text())
            tokens["status"] = "draft"
            (dst / "tokens.json").write_text(json.dumps(tokens))
            for p in (src / "palettes").glob("*.json"):
                (dst / "palettes" / p.name).write_text(p.read_text())
            self.assertIn("brand contentporary is not approved (status: draft)", pj.validate_brief(dict(GOOD_LF), t))

    def test_wrong_format_fields_are_named(self):
        sh = dict(GOOD_LF, format="shorts", palette="reel-dark", captions=True)
        errs = pj.validate_brief(sh, ROOT)
        self.assertIn("hook_end is long-form-only", errs)
        self.assertIn("screen_share is long-form-only", errs)
        self.assertIn("captions is Shorts-only", pj.validate_brief(dict(GOOD_LF, captions=False), ROOT))

    def test_hook_end_default(self):
        self.assertEqual(pj.hook_end({}), 80.0)
        self.assertEqual(pj.hook_end({"hook_end": 45}), 45.0)


class StoryboardTests(unittest.TestCase):
    def test_parses_rows_and_escaped_pipes(self):
        rows = pj.parse_storyboard(GRID)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["t_in"], 62.2)
        self.assertEqual(rows[0]["words"], '"it\'s a system | that prints…"')
        self.assertEqual(rows[1]["placement"], "over-footage")
        self.assertEqual((rows[1]["row"], rows[1]["line"]), (2, 6))

    def test_errors_name_the_line(self):
        with self.assertRaisesRegex(pj.ProjectError, "no beat-grid table"):
            pj.parse_storyboard("| a | b |\n|---|---|\n")
        bad = GRID.replace("| 74.1 | 79.4 |", "| 74.1 | 70.0 |")
        with self.assertRaisesRegex(pj.ProjectError, r"storyboard\.md line 6: t_out 70\.0 must be after t_in 74\.1"):
            pj.parse_storyboard(bad)
        with self.assertRaisesRegex(pj.ProjectError, "placement must be full-frame or over-footage, got 'overlay'"):
            pj.parse_storyboard(GRID.replace("over-footage", "overlay"))

    def test_separator_gap_nonfinite_negative(self):
        no_sep = GRID.replace("|---|---|---|---|---|---|---|---|\n", "")
        with self.assertRaisesRegex(pj.ProjectError, r"line 4: expected the \|---\| separator"):
            pj.parse_storyboard(no_sep)
        gap = GRID.replace("\n| 74.1", "\n\n| 74.1")
        with self.assertRaisesRegex(pj.ProjectError, r"line 6: blank line inside the beat grid"):
            pj.parse_storyboard(gap)
        with self.assertRaisesRegex(pj.ProjectError, "finite seconds"):
            pj.parse_storyboard(GRID.replace("| 62.2 |", "| nan |"))
        with self.assertRaisesRegex(pj.ProjectError, "finite seconds"):
            pj.parse_storyboard(GRID.replace("| 68.0 |", "| inf |"))
        with self.assertRaisesRegex(pj.ProjectError, "t_in -1.0 must not be negative"):
            pj.parse_storyboard(GRID.replace("| 62.2 |", "| -1.0 |"))

    def test_empty_grid_is_empty(self):
        self.assertEqual(pj.parse_storyboard("| " + " | ".join(pj.GRID_COLUMNS) + " |\n|---|---|---|---|---|---|---|---|\n"), [])


class SlotsTranscriptTests(unittest.TestCase):
    def test_slots_sorted_and_root_attrs(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / "index.html").write_text(
                '<div id="root" data-composition-id="main" data-hf-mode="dark" data-width="1920">\n'
                '<div data-composition-id="b" data-start="4" data-duration="3" data-composition-src="compositions/b.html"></div>\n'
                '<div data-composition-src="compositions/a.html" data-composition-id="a" data-start="0" data-duration="4"></div>\n'
                '</div>')
            self.assertEqual([s["id"] for s in pj.composition_slots(t)], ["a", "b"])
            self.assertEqual(pj.composition_slots(t)[1], {"id": "b", "src": "compositions/b.html", "start": 4.0, "dur": 3.0})
            self.assertEqual(pj.root_attrs(t)["data-hf-mode"], "dark")

    def test_transcript_duration(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertIsNone(pj.transcript_duration(t))
            (Path(t) / "transcript.json").write_text("42")
            with self.assertRaisesRegex(pj.ProjectError, "root must be a list"):
                pj.transcript_duration(t)
            (Path(t) / "transcript.json").write_text(json.dumps([{"text": "a", "start": 0.1, "end": 0.4}, {"text": "b", "start": 0.5, "end": 61.25}]))
            self.assertEqual(pj.transcript_duration(t), 61.25)
            (Path(t) / "transcript.json").write_text(json.dumps({"words": [{"text": "a", "start": 0, "end": 9.5}]}))
            self.assertEqual(pj.transcript_duration(t), 9.5)


class PairingAndHashTests(unittest.TestCase):
    ROWS = [{"row": 1, "line": 3, "t_in": 10.0, "t_out": 12.0, "placement": "full-frame"},
            {"row": 2, "line": 4, "t_in": 20.0, "t_out": 21.0, "placement": "over-footage"},
            {"row": 3, "line": 5, "t_in": 30.5, "t_out": 32.5, "placement": "full-frame"}]
    SLOTS = [{"id": "01-hook", "src": "a", "start": 0.0, "dur": 2.0}, {"id": "02-proof", "src": "b", "start": 2.0, "dur": 2.0}]

    def test_pairing_ok_within_one_and_a_half_frames(self):
        slots = [dict(self.SLOTS[0]), dict(self.SLOTS[1], dur=2.0 + 1.4 / 30)]
        pairs, problems = pj.slot_pairing(slots, self.ROWS, 30)
        self.assertEqual(problems, [])
        self.assertEqual([(s["id"], r["row"]) for s, r in pairs], [("01-hook", 1), ("02-proof", 3)])

    def test_pairing_names_duration_and_count_mismatches(self):
        slots = [dict(self.SLOTS[0]), dict(self.SLOTS[1], dur=3.0)]
        _, problems = pj.slot_pairing(slots, self.ROWS, 30)
        self.assertEqual(problems, ["slot 02-proof lasts 3.00 s but storyboard row 3 (line 5) lasts 2.00 s — fix one so they agree"])
        _, problems = pj.slot_pairing(self.SLOTS[:1], self.ROWS, 30)
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith("index.html has 1 scene slots but storyboard.md has 2 full-frame rows"), problems)
        self.assertIn("row 3 (line 5, 30.5–32.5 s) has no slot", problems[0])
        _, problems = pj.slot_pairing(self.SLOTS + [{"id": "03-x", "src": "c", "start": 4.0, "dur": 1.0}], self.ROWS, 30)
        self.assertIn("slot 03-x has no row", problems[0])

    def test_inputs_hash_tracks_every_input(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "BRIEF.md").write_text("```yaml\nformat: long-form\nbrand: contentporary\n```\n")
            (p / "storyboard.md").write_text("s")
            (p / "index.html").write_text("i")
            (p / "lib.lock").write_text("l")
            (p / "compositions" / "overlays").mkdir(parents=True)
            (p / "compositions" / "overlays" / "lt.html").write_text("o")
            (p / "renders").mkdir()
            h = pj.inputs_hash(p, ROOT)
            self.assertRegex(h, r"^[0-9a-f]{64}$")
            (p / "renders" / "qa-draft.mp4").write_text("render output is not an input")
            self.assertEqual(pj.inputs_hash(p, ROOT), h)
            for rel in ("storyboard.md", "index.html", "lib.lock", "compositions/overlays/lt.html", "BRIEF.md"):
                before = pj.inputs_hash(p, ROOT)
                (p / rel).write_text((p / rel).read_text() + " ")
                self.assertNotEqual(pj.inputs_hash(p, ROOT), before, rel)
            fake_root = p / "root"
            (fake_root / "brands" / "contentporary").mkdir(parents=True)
            (fake_root / "brands" / "contentporary" / "tokens.json").write_text("{}")
            before = pj.inputs_hash(p, fake_root)
            (fake_root / "brands" / "contentporary" / "tokens.json").write_text("{ }")
            self.assertNotEqual(pj.inputs_hash(p, fake_root), before, "a referenced brand file changed")


if __name__ == "__main__":
    unittest.main()
