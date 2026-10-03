import json
import tempfile
import unittest
from pathlib import Path

import brandcheck as bc


def good_palette(name="red"):
    return {
        "name": name,
        "ground": {"deep": "#070707", "centre": "#252525", "grid": "#1F1F1F", "dots": "#2A2A2A"},
        "surface": {"fill": "#1C1B1B", "fillAlt": "#343233", "bevel": "#9A9A9A",
                    "halo": "rgba(255,255,255,0.06)"},
        "text": {"primary": "#F4F4F4", "secondary": "#ACACAC"},
        "accent": {"block": "#F26666", "text": "#D74B50", "glow": "#F96E71", "line": "#EA9EA4"},
        "accentScript": "#D74B50",
        "status": {"ok": "#5C9064", "x": "#975154"},
    }


def good_tokens(name="acme"):
    return {
        "name": name,
        "status": "approved",
        "palettes": ["red"],
        "defaultPalette": "red",
        "fonts": {
            "headline": {"helvetica": {"family": "Helvetica Now Display", "weight": 700,
                                       "source": "shared drive"}},
            "defaultHeadline": "helvetica",
            "body": {"family": "Inter", "weight": 500, "source": "Google Fonts"},
            "script": {"family": "Brittany Signature", "source": "shared drive"},
        },
        "kit": {k: "v1" for k in bc.KIT_COMPONENTS},
        "marks": ["highlight-block", "connector"],
    }


def make_brand(root: Path, tokens=None, palettes=None, name="acme"):
    d = root / name
    (d / "palettes").mkdir(parents=True)
    (d / "tokens.json").write_text(json.dumps(tokens or good_tokens(name)))
    for pname, pdata in (palettes or {"red": good_palette()}).items():
        (d / "palettes" / f"{pname}.json").write_text(json.dumps(pdata))
    return d


class ColourTests(unittest.TestCase):
    def test_accepts_hex_and_rgba(self):
        for v in ["#F26666", "#f26666", "rgba(255,255,255,0.06)", "rgba(0, 0, 0, 1)"]:
            self.assertTrue(bc.is_colour(v), v)

    def test_rejects_other_formats(self):
        for v in ["#fff", "red", "rgb(1,2,3)", "F26666", "#F2666", "", None, 12]:
            self.assertFalse(bc.is_colour(v), v)


class PaletteTests(unittest.TestCase):
    def test_good_palette_is_valid(self):
        self.assertEqual(bc.validate_palette(good_palette(), "red.json"), [])

    def test_missing_subkey_is_named(self):
        p = good_palette()
        del p["status"]["x"]
        self.assertIn("red.json: missing status.x", bc.validate_palette(p, "red.json"))

    def test_missing_role_is_named(self):
        p = good_palette()
        del p["accentScript"]
        self.assertIn("red.json: missing accentScript", bc.validate_palette(p, "red.json"))

    def test_bad_colour_is_named_with_value(self):
        p = good_palette()
        p["accent"]["block"] = "#fff"
        errs = bc.validate_palette(p, "red.json")
        self.assertIn("red.json: accent.block is not a colour: '#fff'", errs)

    def test_optional_extras_must_be_colours(self):
        p = good_palette()
        p["extras"] = {"roadmapCard": "#341010", "bad": "maroon"}
        errs = bc.validate_palette(p, "red.json")
        self.assertEqual(errs, ["red.json: extras.bad is not a colour: 'maroon'"])


class BrandTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_good_brand_is_valid(self):
        self.assertEqual(bc.validate_brand(make_brand(self.root)), [])

    def test_missing_tokens_file(self):
        d = self.root / "ghost"
        d.mkdir()
        self.assertEqual(bc.validate_brand(d), ["ghost: missing tokens.json"])

    def test_name_must_match_folder(self):
        t = good_tokens("other")
        errs = bc.validate_brand(make_brand(self.root, tokens=t, name="acme"))
        self.assertIn("acme: tokens.name 'other' does not match folder name", errs)

    def test_listed_palette_without_file(self):
        t = good_tokens()
        t["palettes"] = ["red", "gold"]
        errs = bc.validate_brand(make_brand(self.root, tokens=t))
        self.assertIn("acme: palette 'gold' listed but palettes/gold.json missing", errs)

    def test_default_palette_must_be_listed(self):
        t = good_tokens()
        t["defaultPalette"] = "gold"
        errs = bc.validate_brand(make_brand(self.root, tokens=t))
        self.assertIn("acme: defaultPalette 'gold' not in palettes", errs)

    def test_status_must_be_known(self):
        t = good_tokens()
        t["status"] = "final"
        errs = bc.validate_brand(make_brand(self.root, tokens=t))
        self.assertIn("acme: status must be 'draft' or 'approved', got 'final'", errs)

    def test_every_kit_component_required(self):
        t = good_tokens()
        del t["kit"]["roadmap"]
        errs = bc.validate_brand(make_brand(self.root, tokens=t))
        self.assertIn("acme: kit missing component 'roadmap'", errs)

    def test_unknown_mark_rejected(self):
        t = good_tokens()
        t["marks"] = ["highlight-block", "sparkles"]
        errs = bc.validate_brand(make_brand(self.root, tokens=t))
        self.assertIn("acme: unknown mark 'sparkles'", errs)

    def test_default_headline_must_exist(self):
        t = good_tokens()
        t["fonts"]["defaultHeadline"] = "geometric"
        errs = bc.validate_brand(make_brand(self.root, tokens=t))
        self.assertIn("acme: fonts.defaultHeadline 'geometric' not in fonts.headline", errs)

    def test_palette_errors_bubble_up(self):
        p = good_palette()
        del p["ground"]["dots"]
        errs = bc.validate_brand(make_brand(self.root, palettes={"red": p}))
        self.assertIn("acme/palettes/red.json: missing ground.dots", errs)


class ChoiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.brand = make_brand(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_valid_choice(self):
        self.assertEqual(bc.validate_choice(self.brand, "red", "helvetica",
                                            {"accentScript": "#BACE7A"}), [])

    def test_font_optional(self):
        self.assertEqual(bc.validate_choice(self.brand, "red"), [])

    def test_unknown_palette_lists_options(self):
        self.assertEqual(bc.validate_choice(self.brand, "gold"),
                         ["palette 'gold' not in brand acme (have: red)"])

    def test_unknown_font_lists_options(self):
        self.assertEqual(bc.validate_choice(self.brand, "red", "geometric"),
                         ["font 'geometric' not in brand acme (have: helvetica)"])

    def test_override_path_must_exist(self):
        self.assertEqual(bc.validate_choice(self.brand, "red", None, {"accent.blok": "#FFFFFF"}),
                         ["override 'accent.blok' is not a palette role"])

    def test_override_value_must_be_colour(self):
        self.assertEqual(bc.validate_choice(self.brand, "red", None, {"accent.block": "lime"}),
                         ["override 'accent.block' is not a colour: 'lime'"])

    def test_draft_brand_cannot_be_used(self):
        t = good_tokens("draftco")
        t["status"] = "draft"
        d = make_brand(Path(self.tmp.name), tokens=t, name="draftco")
        self.assertEqual(bc.validate_choice(d, "red"),
                         ["brand draftco is not approved (status: draft)"])


if __name__ == "__main__":
    unittest.main()
