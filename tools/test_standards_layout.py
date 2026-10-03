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
        self.assertEqual(sorted(t["palettes"]),
                         ["gold", "lime", "paper", "red", "reel-dark", "reel-light", "silver"])
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


class GroundModeTests(unittest.TestCase):
    D = ROOT / "brands" / "contentporary"

    @staticmethod
    def luminance(hex_colour):
        r, g, b = (int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    def test_light_palettes_exist_and_validate(self):
        brand = bc.load_brand(self.D)
        self.assertEqual(bc.validate_brand(self.D), [])
        modes = {name: p["mode"] for name, p in brand["palettes"].items()}
        self.assertEqual(modes["silver"], "light")
        self.assertEqual(modes["paper"], "light")
        self.assertEqual(modes["red"], "dark")
        self.assertEqual(modes["reel-light"], "light")

    def test_light_text_is_darker_than_ground(self):
        for name, p in bc.load_brand(self.D)["palettes"].items():
            if p["mode"] == "light":
                self.assertLess(self.luminance(p["text"]["primary"]),
                                self.luminance(p["ground"]["centre"]), name)

    def test_template_declares_mode(self):
        d = ROOT / "brands" / "_template"
        self.assertEqual(bc.load_brand(d)["palettes"]["base"]["mode"], "dark")

    def test_brand_md_has_two_ground_modes(self):
        t = (self.D / "brand.md").read_text()
        for s in ["Dark ground", "Light ground", "`silver`", "`paper`", "mode"]:
            self.assertIn(s, t)
        self.assertNotIn("pure-white grounds", t)


class LookAndCatalogueTests(unittest.TestCase):
    def test_core_ban_list(self):
        t = (ROOT / "standards" / "core" / "motion.md").read_text()
        self.assertIn("## The look — banned generic output", t)
        for s in ["centred text on a gradient", "fade in → hold → fade out", "everything at once",
                  "stock icons", "more than two lines"]:
            self.assertIn(s, t)

    def test_long_form_catalogue(self):
        t = (ROOT / "standards" / "formats" / "long-form.md").read_text()
        self.assertIn("## Custom catalogue", t)
        for cid in ["A1", "A2", "A3", "A4", "A5", "A6", "B1", "B2", "B3", "B4",
                    "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "D1", "D2", "D3", "D4", "D5"]:
            self.assertIn(f"| {cid} |", t, cid)
        for s in ["## Section formats", "## Sound", "silent", "punch-ins do not count"]:
            self.assertIn(s, t)

    def test_catalogue_copies_no_banned_technique(self):
        t = (ROOT / "standards" / "formats" / "long-form.md").read_text()
        cat = t.split("## Custom catalogue", 1)[1].split("\n## ", 1)[0].lower()
        for banned in ["dissolve", "crossfade", "cross-fade", "light leak", "overshoot", "bounce"]:
            self.assertNotIn(banned, cat, banned)


class HarnessTests(unittest.TestCase):
    QA = ROOT / "standards" / "core" / "qa.md"
    PL = ROOT / "standards" / "core" / "pipeline.md"

    def test_qa_critique_loop(self):
        t = self.QA.read_text()
        for s in ["## 2. Critique loop", "## 3. Human review", "critique.md", "below 8",
                  "3 rounds", "Smooth", "On-brand", "Readable", "Synced", "Purposeful", "Craft"]:
            self.assertIn(s, t)

    def test_pipeline_harness(self):
        t = self.PL.read_text()
        for s in ["film:", "direction:", "references:", "gotchas:", "## Beat grid",
                  "| t_in | t_out | words | placement | type | beats | ease | marks |",
                  "Opus 5.5", "high effort", "## Reference → style guide", "critique.md",
                  "never its content"]:
            self.assertIn(s, t)

    def test_no_stale_signoff_section_refs(self):
        for f in [self.PL] + list((ROOT / "standards").rglob("*.md")):
            t = f.read_text()
            self.assertNotIn("qa.md` §2) by the runner", t, f)
            self.assertNotIn("Preview pack → sign-off** by the runner (`standards/core/qa.md` §2)", t, f)

    def test_template_readme_reference_step(self):
        t = (ROOT / "brands" / "_template" / "README.md").read_text()
        self.assertIn("Reference → style guide", t)


if __name__ == "__main__":
    unittest.main()
