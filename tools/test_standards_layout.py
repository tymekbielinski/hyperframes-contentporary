import unittest
from pathlib import Path

import brandcheck as bc

ROOT = Path(__file__).resolve().parents[1]


class TemplateBrandTests(unittest.TestCase):
    def test_template_is_structurally_valid_and_draft(self):
        d = ROOT / "brands" / "_template"
        self.assertEqual(bc.validate_brand(d), [])
        self.assertEqual(bc.load_brand(d)["tokens"]["status"], "draft")

    def test_template_has_prose_files(self):
        d = ROOT / "brands" / "_template"
        for rel in ["brand.md", "narrative.md", "assets/MANIFEST.md", "README.md"]:
            self.assertTrue((d / rel).is_file(), rel)


if __name__ == "__main__":
    unittest.main()
