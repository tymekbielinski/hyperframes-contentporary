import io
import json
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import ref_index
import ref_ingest
import refs
import synth

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


META = {"slug": "clip", "title": "Clip", "url": "", "format": "long-form", "ground": "dark",
        "made_by": "test", "brand": "Test"}


class SpanTests(unittest.TestCase):
    def test_spans_tile_the_video_and_drop_flash_cuts(self):
        self.assertEqual(ref_ingest.shot_spans([1.0, 1.1, 2.0], 3.0), [(0.0, 1.0), (1.0, 2.0), (2.0, 3.0)])

    def test_no_cuts_is_one_shot(self):
        self.assertEqual(ref_ingest.shot_spans([], 42.0), [(0.0, 42.0)])

    def test_still_times_short_normal_long(self):
        self.assertEqual(ref_ingest.still_times(0.0, 0.6), [0.3])
        self.assertEqual(ref_ingest.still_times(10.0, 14.0), [10.25, 12.0, 13.7])
        long = ref_ingest.still_times(0.0, 120.0)
        self.assertEqual(len(long), 8)
        self.assertEqual((long[0], long[-1]), (0.25, 119.7))


@unittest.skipUnless(synth.HAVE_FFMPEG, "ffmpeg/ffprobe not installed")
class IngestTests(Fixture):
    def setUp(self):
        super().setUp()
        self.video = synth.segments(self.root / "clip.mp4", [("red", 1.5), ("blue", 2.0), ("white", 1.5)], size=(320, 180))

    def test_ingest_writes_a_valid_draft(self):
        with redirect_stdout(io.StringIO()):
            d = ref_ingest.ingest(self.video, META, self.root)
        data = json.loads((d / "shots.json").read_text())
        self.assertEqual([(s["t_in"], s["t_out"]) for s in data["shots"]], [(0.0, 1.5), (1.5, 3.5), (3.5, 5.0)])
        self.assertTrue(all(s["status"] == "draft" and s["stills"] for s in data["shots"]))
        self.assertEqual(json.loads((d / "source.json").read_text())["source_file"], "clip.mp4")
        self.assertTrue(list((d / "work").glob("contact-*.jpg")))
        self.assertEqual(refs.validate_video(d, self.reg), [])

    def test_existing_slug_is_refused(self):
        with redirect_stdout(io.StringIO()):
            ref_ingest.ingest(self.video, META, self.root)
        (self.root / "references/videos/clip/shots.json").write_text('{"version": 1, "shots": ["analysed"]}')
        with self.assertRaisesRegex(ref_ingest.IngestError, "already ingested"):
            ref_ingest.ingest(self.video, META, self.root)
        self.assertIn("analysed", (self.root / "references/videos/clip/shots.json").read_text())

    def test_cli_usage_without_arguments(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = ref_ingest.main(["ref_ingest.py"], self.root)
        self.assertEqual(code, 2)
        self.assertIn("usage: python3 tools/ref_ingest.py", out.getvalue())


class IndexTests(Fixture):
    def test_run_creates_cards_index_and_check_is_clean(self):
        write_video(self.root)
        findings, _ = ref_index.run(self.root)
        self.assertEqual(findings, [])
        card = (self.root / "references/patterns/A1.md").read_text()
        self.assertIn("**1 exemplar** from 1 video", card)
        self.assertIn("../videos/demo/stills/s001-a.jpg", card)
        self.assertTrue((self.root / "references/patterns/E2.md").is_file())
        idx = json.loads((self.root / "references/index.json").read_text())
        self.assertEqual(idx["videos"][0]["graphics_pct"], 40.0)
        self.assertEqual(ref_index.run(self.root, check=True)[0], [])

    def test_quality_bar_survives_regeneration(self):
        write_video(self.root)
        ref_index.run(self.root)
        p = self.root / "references/patterns/A1.md"
        p.write_text(p.read_text().replace(refs.STUB + " — write it from the exemplars below (references/README.md §Quality bar)._",
                                           "- Card ≥ 55 % W, backdrop is its own blurred copy."))
        write_video(self.root, "second")
        ref_index.run(self.root)
        text = p.read_text()
        self.assertIn("Card ≥ 55 % W", text)
        self.assertIn("**2 exemplars** from 2 videos", text)
        self.assertEqual(ref_index.card_status(text), "ready")

    def test_check_reports_stale_index_and_drafts(self):
        write_video(self.root)
        ref_index.run(self.root)
        write_video(self.root, "fresh", shots=[refs.empty_shot(1, 0.0, 10.0)], stills=())
        findings, _ = ref_index.run(self.root, check=True)
        text = "\n".join(findings)
        self.assertIn("references/index.json is stale", text)
        self.assertIn("fresh: 1 draft shot", text)

    def test_prune_removes_face_stills_and_orphans(self):
        shots = [graphic_shot("s001", 0.0, 4.0, "A1", ["stills/s001-a.jpg"]), face_shot("s002", 4.0, 10.0)]
        d = write_video(self.root, shots=shots, stills=("stills/s001-a.jpg", "stills/s002-a.jpg"))
        data = json.loads((d / "shots.json").read_text())
        data["shots"][1]["stills"] = ["stills/s002-a.jpg"]
        (d / "shots.json").write_text(json.dumps(data))
        (d / "stills" / "orphan.jpg").write_bytes(b"x")
        self.assertEqual(ref_index.prune(self.root), 2)
        self.assertEqual(sorted(p.name for p in (d / "stills").iterdir()), ["s001-a.jpg"])
        self.assertEqual(json.loads((d / "shots.json").read_text())["shots"][1]["stills"], [])

    def test_candidates_are_listed(self):
        shots = [graphic_shot("s001", 0.0, 4.0, "new:logo-row", ["stills/s001-a.jpg"]), face_shot("s002", 4.0, 10.0)]
        write_video(self.root, shots=shots)
        ref_index.run(self.root)
        idx = json.loads((self.root / "references/index.json").read_text())
        self.assertEqual(idx["candidates"], {"new:logo-row": [{"video": "demo", "shot": "s001"}]})
