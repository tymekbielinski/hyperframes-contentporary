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


class ContentporaryBrandTests(unittest.TestCase):
    D = ROOT / "brands" / "contentporary"

    def test_valid_and_approved(self):
        self.assertEqual(bc.validate_brand(self.D), [])
        self.assertEqual(bc.load_brand(self.D)["tokens"]["status"], "approved")

    def test_palettes_and_fonts_per_spec(self):
        t = bc.load_brand(self.D)["tokens"]
        self.assertEqual(sorted(t["palettes"]), ["gold", "lime", "red", "reel-dark", "reel-light"])
        self.assertEqual(sorted(t["fonts"]["headline"]), ["geometric", "helvetica"])

    def test_reference_values_kept(self):
        p = bc.load_brand(self.D)["palettes"]
        self.assertEqual(p["red"]["accent"]["block"], "#F26666")
        self.assertEqual(p["red"]["accent"]["text"], "#D74B50")
        self.assertEqual(p["reel-dark"]["accent"]["block"], "#EE4B4A")
        self.assertEqual(p["reel-dark"]["ground"]["deep"], "#0C0C0C")

    def test_choice_from_spec_example_is_valid(self):
        self.assertEqual(bc.validate_choice(self.D, "red", "geometric",
                                            {"accentScript": "#BACE7A"}), [])

    def test_prose_files(self):
        for rel in ["brand.md", "narrative.md", "assets/MANIFEST.md"]:
            self.assertTrue((self.D / rel).is_file(), rel)
        self.assertNotIn("../CLAUDE.md", (self.D / "narrative.md").read_text())


class CoreMotionTests(unittest.TestCase):
    F = ROOT / "standards" / "core" / "motion.md"

    def test_ten_rules_and_vocabulary(self):
        text = self.F.read_text()
        for n in range(1, 11):
            self.assertIn(f"\n{n}. **", text, f"rule {n}")
        for token in ["ease.camera", "ease.enter", "ease.sweep", "ease.cut",
                      "data-blur-reason", "`focus`", "`glow`", "`wipe`", "HFMotionBlur"]:
            self.assertIn(token, text)

    def test_dropped_rules_absent(self):
        text = self.F.read_text().lower()
        self.assertNotIn("bed never stops", text.replace("no \"bed never stops\"", ""))
        self.assertNotIn("110–170 ms. always", text)


class FormatProfileTests(unittest.TestCase):
    LF = ROOT / "standards" / "formats" / "long-form.md"
    SH = ROOT / "standards" / "formats" / "shorts.md"

    def test_long_form_values(self):
        t = self.LF.read_text()
        for s in ["cubic-bezier(0.32, 0, 0.18, 1)", "power3.out", "≥ 60 %", "≤ 30 s",
                  "lower third", "ProRes 4444", "TIMECODES.csv", "chapter roadmap",
                  "screen-share"]:
            self.assertIn(s, t)
        self.assertIn("**Not used in long-form:** light leaks", t)
        self.assertEqual(t.lower().count("light leak"), 1)

    def test_shorts_values(self):
        t = self.SH.read_text()
        for s in ["cubic-bezier(0.65, 0, 0.35, 1)", "0.42s", "0.36s", "gt(scene,0.20)",
                  "data-blur-reason=\"wipe\"", "captions", "W·K"]:
            self.assertIn(s, t)
        self.assertNotIn("1080K × 1920K", t)
        self.assertNotIn("public/lib/", t)


class QaPipelineTests(unittest.TestCase):
    def test_qa_has_ten_checks_and_signoff(self):
        t = (ROOT / "standards" / "core" / "qa.md").read_text()
        for n in range(1, 11):
            self.assertIn(f"| {n} |", t)
        for s in ["whoever ran the build", "Promotion rule", "exceptions:", "lib.lock"]:
            self.assertIn(s, t)

    def test_pipeline_brief_fields(self):
        t = (ROOT / "standards" / "core" / "pipeline.md").read_text()
        for key in ["format:", "brand:", "palette:", "font:", "overrides:", "captions:",
                    "hook_end:", "screen_share:", "exceptions:", "source:"]:
            self.assertIn(key, t)
        for s in ["Long-form", "Shorts", "client-ops", "shared drive"]:
            self.assertIn(s, t)


class MigrationTests(unittest.TestCase):
    STALE = ["context/", "PIPELINE.md", "../CLAUDE.md", "script-template.md",
             "motion-craft.md", "design-system.md", "frame.md"]

    def active_docs(self):
        files = [ROOT / "CLAUDE.md"]
        for d in ["standards", "brands"]:
            files += [p for p in (ROOT / d).rglob("*.md")]
        return files

    def test_old_files_gone(self):
        for rel in ["context/design-system.md", "context/motion-craft.md", "context/frame.md",
                    "context/custom.md", "context/voice.md", "context/narrative.md",
                    "context/motion-waapi.md", "PIPELINE.md", "templates/script-template.md"]:
            self.assertFalse((ROOT / rel).exists(), rel)
        self.assertTrue((ROOT / "standards" / "reference" / "motion-waapi.md").is_file())

    def test_no_stale_references_in_active_docs(self):
        allowed = {  # provenance lines that name the old file on purpose
            ("standards/core/motion.md", "context/"),
            ("standards/core/motion.md", "context/motion-craft.md"),
            ("standards/core/motion.md", "context/design-system.md"),
            ("standards/core/motion.md", "motion-craft.md"),
            ("standards/core/motion.md", "design-system.md"),
        }
        problems = []
        for f in self.active_docs():
            rel = str(f.relative_to(ROOT))
            text = f.read_text()
            for s in self.STALE:
                if s in text and (rel, s) not in allowed:
                    problems.append(f"{rel}: {s}")
        self.assertEqual(problems, [])

    def test_claude_md_points_at_new_layout(self):
        t = (ROOT / "CLAUDE.md").read_text()
        for s in ["git pull", "standards/core/motion.md", "standards/formats/",
                  "brands/", "standards/core/qa.md", "Precedence"]:
            self.assertIn(s, t)


class EasingTableTests(unittest.TestCase):
    def test_profiles_define_core_tokens_in_table_rows(self):
        import re
        for name in ("long-form.md", "shorts.md"):
            t = (ROOT / "standards" / "formats" / name).read_text()
            for tok in ("ease.camera", "ease.enter", "ease.sweep", "ease.cut"):
                self.assertTrue(re.search(r"^\| `%s` " % re.escape(tok), t, re.M),
                                f"{name}: {tok} missing from a table row")


if __name__ == "__main__":
    unittest.main()
