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

    def test_profiles_point_at_the_shared_library(self):
        sh, lf = self.SH.read_text(), self.LF.read_text()
        self.assertNotIn("#F4F6F8", sh)
        self.assertIn("var(--hf-text-primary)", sh)
        self.assertIn('profilePreset("shorts", "leg")', sh)
        self.assertIn("HFWipe.wipe", sh)
        self.assertIn("HFCamera.rig", sh)
        self.assertNotIn("s: Z * K", sh)
        self.assertNotIn('preset: "medium"', sh)
        self.assertIn('profilePreset("long-form", "leg")', lf)
        self.assertIn('"whip"', lf)


class QaPipelineTests(unittest.TestCase):
    def test_qa_has_ten_checks_and_signoff(self):
        t = (ROOT / "standards" / "core" / "qa.md").read_text()
        for n in range(1, 12):
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
                  "brands/", "standards/core/qa.md", "Precedence", "lib/README.md", "lib/test/"]:
            self.assertIn(s, t)
        self.assertNotIn("rewritten in Plan 2", t)


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

    @staticmethod
    def contrast(a, b):
        def lum(h):
            cs = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
            cs = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in cs]
            return 0.2126 * cs[0] + 0.7152 * cs[1] + 0.0722 * cs[2]
        la, lb = lum(a), lum(b)
        return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)

    def test_text_contrast_all_brands_and_palettes(self):
        for d in sorted((ROOT / "brands").iterdir()):
            if not (d / "tokens.json").is_file() and not d.is_dir():
                continue
            if not d.is_dir():
                continue
            for name, p in bc.load_brand(d)["palettes"].items():
                txt = p["text"]["primary"]
                for g in ("centre", "deep"):
                    self.assertGreaterEqual(self.contrast(txt, p["ground"][g]), 4.5, (d.name, name, g))
                lt, lc = self.luminance(txt), self.luminance(p["ground"]["centre"])
                if p["mode"] == "light":
                    self.assertLess(lt, lc, (d.name, name))
                else:
                    self.assertGreater(lt, lc, (d.name, name))

    def test_long_form_and_qa_ground_rules(self):
        lf = (ROOT / "standards" / "formats" / "long-form.md").read_text()
        qa = (ROOT / "standards" / "core" / "qa.md").read_text()
        self.assertIn("never a flip", lf)
        self.assertIn("(face punch-ins are not graphics)", qa)

    def test_brand_md_has_two_ground_modes(self):
        t = (self.D / "brand.md").read_text()
        for s in ["Dark ground", "Light ground", "`silver`", "`paper`", "`mode`"]:
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
        for f in list((ROOT / "standards").rglob("*.md")) + [ROOT / "CLAUDE.md"]:
            t = f.read_text()
            self.assertNotIn("automated gate, then sign-off", t, f)
            self.assertNotIn("qa.md` §2) by the runner", t, f)
            self.assertNotIn("Preview pack → sign-off** by the runner (`standards/core/qa.md` §2)", t, f)

    def test_template_readme_reference_step(self):
        t = (ROOT / "brands" / "_template" / "README.md").read_text()
        self.assertIn("Reference → style guide", t)


class ToolsDocsTests(unittest.TestCase):
    DOCS = ["CLAUDE.md", "lib/README.md", "standards/core/qa.md", "standards/core/pipeline.md",
            "standards/formats/long-form.md", "standards/formats/shorts.md"]

    def test_no_plan_3_placeholders_left(self):
        for rel in self.DOCS:
            t = (ROOT / rel).read_text()
            for stale in ["(Plan 3)", "tools/sync-lib", "tools/new-video", "tools/probe-cuts", "`tools/qa`"]:
                self.assertNotIn(stale, t, f"{rel}: {stale}")

    def test_every_documented_tool_exists(self):
        import re
        seen = set()
        for rel in self.DOCS:
            for tool in re.findall(r"python3 tools/([\w-]+\.py)", (ROOT / rel).read_text()):
                seen.add(tool)
                self.assertTrue((ROOT / "tools" / tool).is_file(), f"{rel}: tools/{tool}")
        self.assertTrue({"new_video.py", "sync_lib.py", "cadence_scan.py", "probe_cuts.py", "qa.py",
                         "preview_pack.py", "slice.py"} <= seen, seen)

    def test_qa_doc_names_the_gate_and_waiver_syntax(self):
        t = (ROOT / "standards" / "core" / "qa.md").read_text()
        for s in ["python3 tools/qa.py videos/<slug>", "check <n>: <reason>", "python3 tools/preview_pack.py",
                  "renders/qa-report.json"]:
            self.assertIn(s, t)

    def test_claude_md_has_tools_section(self):
        t = (ROOT / "CLAUDE.md").read_text()
        self.assertIn("## Tools", t)
        for tool in ["new_video.py", "sync_lib.py", "cadence_scan.py", "probe_cuts.py", "qa.py",
                     "preview_pack.py", "slice.py", "scan_flicker.py", "brandcheck.py"]:
            self.assertIn(tool, t)
        self.assertIn("hf-placeholder", t)

    def test_roadmap_marks_plan_4_done_and_plan_5_ready(self):
        t = (ROOT / "docs/superpowers/plans/2026-10-03-animation-workflow-roadmap.md").read_text()
        row3 = [l for l in t.splitlines() if l.startswith("| 3 |")][0]
        row4 = [l for l in t.splitlines() if l.startswith("| 4 |")][0]
        row5 = [l for l in t.splitlines() if l.startswith("| 5 |")][0]
        self.assertIn("**Done** (branch `tools-v1`)", row3)
        self.assertIn("**Done** (branch `kit-v1`)", row4)
        self.assertIn("**Ready to write**", row5)
        self.assertIn("## Notes for Plan 5 (from Plan 4)", t)
        self.assertTrue((ROOT / "docs/superpowers/plans/2026-10-04-plan-4-kit-components.md").is_file())
        self.assertIn("## Notes for Plan 4 (from Plan 3)", t)
        self.assertIn("hf-placeholder", t)

    def test_final_review_docs(self):
        qa = (ROOT / "standards" / "core" / "qa.md").read_text()
        for s in ["compositions/overlays/", "/preview/comp/", "data-hf-id", "STALE", "inputs_hash", "nothing measured",
                  "punch-in", "advisory", "--face-ref", "--threshold", "1920×1080", "600",
                  "may also report cuts where the picture returns"]:
            self.assertIn(s, qa, s)
        self.assertNotIn("also lists intended cuts", qa)
        qa_py = (ROOT / "tools" / "qa.py").read_text()
        self.assertIn('"--face-ref"', qa_py, "qa.md documents --face-ref, so qa.py must accept it")
        self.assertIn('"--threshold"', qa_py)
        self.assertIn("data-hf-id", (ROOT / "CLAUDE.md").read_text())
        flicker = (ROOT / "tools" / "scan_flicker.py").read_text()
        self.assertIn("may also report cuts where the picture returns", flicker)
        self.assertNotIn("reports intended hard cuts too", flicker)
        road = (ROOT / "docs/superpowers/plans/2026-10-03-animation-workflow-roadmap.md").read_text()
        old = road.split("## Notes for Plans 3–4 (from the Plan 2 final review)", 1)[1].split("\n## ", 1)[0]
        plan3 = [l for l in old.splitlines() if l.startswith("- ") and "Plan 3" in l]
        self.assertEqual(len(plan3), 4, plan3)
        self.assertTrue(all("Done in Plan 3" in l for l in plan3), plan3)
        notes4 = road.split("## Notes for Plan 4 (from Plan 3)", 1)[1].split("\n## ", 1)[0]
        self.assertIn("root-relative", notes4)



class KitDocsTests(unittest.TestCase):
    def test_no_plan_4_placeholders_left(self):
        for rel in ToolsDocsTests.DOCS + ["brands/_template/README.md", "brands/contentporary/brand.md"]:
            self.assertNotIn("(Plan 4", (ROOT / rel).read_text(), rel)

    def test_long_form_kit_table_names_every_call_and_variant(self):
        import json
        t = (ROOT / "standards" / "formats" / "long-form.md").read_text()
        self.assertIn("## Kit — `lib/kit`", t)
        kit = json.loads((ROOT / "brands" / "contentporary" / "tokens.json").read_text())["kit"]
        calls = {"title": "HFKit.title", "subtitle": "HFKit.subtitle", "lower-third": "HFKit.lowerThird",
                 "side-text": "HFKit.sideText", "cta-youtube": "HFKit.ctaYoutube", "roadmap": "HFKit.roadmap"}
        for name, variant in kit.items():
            row = [l for l in t.splitlines() if l.startswith(f"| `{calls[name]}` |")]
            self.assertEqual(len(row), 1, name)
            self.assertIn(f"| `{variant}` |", row[0])
            readme = (ROOT / "lib" / "README.md").read_text()
            self.assertTrue([l for l in readme.splitlines() if l.startswith(f"| `{calls[name]}(tl, host, o)` |")], f"README API row for {calls[name]}")
            self.assertIn(f"(`{calls[name]}`", (ROOT / "brands" / "contentporary" / "brand.md").read_text())

    def test_onboarding_and_claude_md_name_the_proof_sheet(self):
        self.assertIn("python3 tools/proof_sheet.py <client-slug>", (ROOT / "brands" / "_template" / "README.md").read_text())
        claude = (ROOT / "CLAUDE.md").read_text()
        self.assertIn("`proof_sheet.py` (", claude)
        self.assertIn("`kit_preview.py` (", claude)
        self.assertTrue((ROOT / "tools" / "proof_sheet.py").is_file())

    def test_lib_readme_documents_the_plan_2_review_hooks(self):
        t = (ROOT / "lib" / "README.md").read_text()
        for s in ["HFProfile.claimTransform", "splitWords", "opts.onSpans", "accentWord` installs its own stylesheet",
                  "lib/kit/kit.js", "data-hf-mode", "proof_sheet.py", "HFText.loadFaces", "measureWidth"]:
            self.assertIn(s, t, s)
        self.assertEqual(t.count("await HFText.loadFaces(root)"), 1)


if __name__ == "__main__":
    unittest.main()
