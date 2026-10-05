import json
import shutil
import tempfile
import unittest
from pathlib import Path

import refs

ROOT = Path(__file__).resolve().parents[1]


def write_video(root: Path, slug="demo", shots=None, source=None, stills=("stills/s001-a.jpg",)):
    """A minimal valid reference video under <root>/references/videos/<slug>."""
    d = root / "references" / "videos" / slug
    (d / "stills").mkdir(parents=True)
    for s in stills:
        (d / s).write_bytes(b"\xff\xd8jpg")
    src = {"slug": slug, "title": "Demo", "url": "", "format": "long-form", "ground": "dark",
           "made_by": "editor (After Effects)", "brand": "Contentporary", "duration": 10.0, "fps": 30.0,
           "width": 1920, "height": 1080, "source_file": "demo.mp4", "ingested": "2026-10-05"}
    src.update(source or {})
    (d / "source.json").write_text(json.dumps(src))
    if shots is None:
        shots = [graphic_shot("s001", 0.0, 4.0, "A1", list(stills)), face_shot("s002", 4.0, 10.0)]
    (d / "shots.json").write_text(json.dumps({"version": 1, "shots": shots}))
    return d


def graphic_shot(sid, a, b, pattern, stills, **kw):
    s = {"id": sid, "t_in": a, "t_out": b, "status": "reviewed", "kind": "graphic", "pattern": pattern,
         "placement": "full-frame", "stills": stills,
         "layout": {"type_px": 96, "fill": "balanced", "layers": 3},
         "motion": {"entrance": "card 0.9→1 with blur→sharp", "camera": "push 1.6 s", "word_rate_s": 0.2, "hold_s": 0.8},
         "colours": ["#F26666"], "marks": ["highlight-block"], "notes": "",
         "quality": "Sharp card over its own blurred copy; highlight lands after the card settles."}
    s.update(kw)
    return s


def face_shot(sid, a, b):
    return {"id": sid, "t_in": a, "t_out": b, "status": "reviewed", "kind": "face", "pattern": None,
            "placement": None, "stills": [], "layout": None, "motion": None, "colours": [], "marks": [],
            "notes": "", "quality": ""}


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "standards" / "formats").mkdir(parents=True)
        shutil.copy(ROOT / "standards" / "formats" / "long-form.md", self.root / "standards" / "formats")
        self.reg = refs.registry(self.root)

    def tearDown(self):
        self.tmp.cleanup()


class RegistryTests(Fixture):
    def test_catalogue_kit_and_section_ids(self):
        for pid in ["A1", "A6", "B4", "C8", "D5", "E1", "E2"]:
            self.assertIn(pid, self.reg)
        self.assertEqual(self.reg["E1"]["group"], "section")
        self.assertEqual(self.reg["A1"]["group"], "custom")
        for kit in ["title", "subtitle", "lower-third", "side-text", "cta-youtube", "roadmap"]:
            self.assertEqual(self.reg[kit]["group"], "kit", kit)
        self.assertNotIn("ID", self.reg)

    def test_type_ids_ignore_prose_and_catch_typos(self):
        self.assertEqual(refs.type_ids("B3 + C8 (shared canvas)", self.reg), (["B3", "C8"], []))
        self.assertEqual(refs.type_ids("D4 (full-frame card row)", self.reg), (["D4"], []))
        self.assertEqual(refs.type_ids("title", self.reg), (["title"], []))
        self.assertEqual(refs.type_ids("B9", self.reg), ([], ["B9"]))
        self.assertEqual(refs.type_ids("glass tiles", self.reg), ([], []))


class ValidateTests(Fixture):
    def test_valid_video_has_no_findings(self):
        d = write_video(self.root)
        self.assertEqual(refs.validate_video(d, self.reg), [])

    def test_gap_overlap_and_missing_still_are_named(self):
        shots = [graphic_shot("s001", 0.0, 4.0, "A1", ["stills/gone.jpg"]),
                 face_shot("s002", 4.5, 9.0), face_shot("s003", 8.0, 10.0)]
        found = "\n".join(refs.validate_video(write_video(self.root, shots=shots), self.reg))
        self.assertIn("s001: still stills/gone.jpg not found", found)
        self.assertIn("s002: starts at 4.5 but the previous shot ends at 4.0", found)
        self.assertIn("s003: starts at 8.0 but the previous shot ends at 9.0", found)

    def test_reviewed_graphic_needs_pattern_quality_and_layout(self):
        bad = graphic_shot("s001", 0.0, 4.0, "Z9", ["stills/s001-a.jpg"], quality="ok", layout=None)
        found = "\n".join(refs.validate_video(write_video(self.root, shots=[bad, face_shot("s002", 4.0, 10.0)]), self.reg))
        self.assertIn("s001: pattern 'Z9' is not in the registry", found)
        self.assertIn("s001: quality must say why the shot works (≥ 20 characters)", found)
        self.assertIn("s001: layout must be", found)

    def test_new_pattern_candidates_are_allowed(self):
        shots = [graphic_shot("s001", 0.0, 4.0, "new:logo-row", ["stills/s001-a.jpg"]), face_shot("s002", 4.0, 10.0)]
        self.assertEqual(refs.validate_video(write_video(self.root, shots=shots), self.reg), [])

    def test_draft_shots_only_need_structure(self):
        shots = [refs.empty_shot(1, 0.0, 10.0)]
        self.assertEqual(refs.validate_video(write_video(self.root, shots=shots, stills=()), self.reg), [])

    def test_slug_must_match_folder_and_shots_must_reach_the_end(self):
        shots = [graphic_shot("s001", 0.0, 4.0, "A1", ["stills/s001-a.jpg"])]
        found = "\n".join(refs.validate_video(write_video(self.root, shots=shots, source={"slug": "other"}), self.reg))
        self.assertIn("source.json: slug 'other' must equal the folder name 'demo'", found)
        self.assertIn("last shot ends at 4.0 but the video lasts 10.0", found)

    def test_broken_json_is_a_finding_not_a_crash(self):
        d = write_video(self.root)
        (d / "shots.json").write_text("{nope")
        self.assertIn("shots.json is not valid JSON", "\n".join(refs.validate_video(d, self.reg)))

    def test_non_object_source_json_is_a_finding_not_a_crash(self):
        d = write_video(self.root)
        (d / "source.json").write_text("[]")
        findings = refs.validate_video(d, self.reg)
        self.assertIn("source.json: root must be an object", "\n".join(findings))


class LibraryTests(Fixture):
    def test_exemplars_pinned_first_then_by_video_and_time(self):
        a = [graphic_shot("s001", 0.0, 4.0, "A1", ["stills/s001-a.jpg"]),
             graphic_shot("s002", 4.0, 10.0, "A1", ["stills/s001-a.jpg"], exemplar=True)]
        write_video(self.root, "beta", shots=a)
        write_video(self.root, "alpha")
        lib = refs.load_library(self.root)
        got = [(v["source"]["slug"], s["id"]) for v, s in refs.exemplars(lib, "A1")]
        self.assertEqual(got, [("beta", "s002"), ("alpha", "s001"), ("beta", "s001")])
        self.assertEqual(lib["findings"], [])
