import io
import json
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import media
import ref_board
import ref_index
import ref_ingest
import ref_shots
import qa
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

    def test_timeline_sheets_written(self):
        with redirect_stdout(io.StringIO()):
            d = ref_ingest.ingest(self.video, META, self.root)
        self.assertTrue((d / "work" / "timeline-01.jpg").is_file())
        self.assertFalse((d / "work" / "timeline-02.jpg").exists())
        txt = (d / "work" / "timeline.txt").read_text()
        self.assertTrue("0–5" in txt or "0.0–5.0" in txt, txt)

    def test_timeline_index_lists_only_existing_sheets(self):
        from unittest import mock
        d = self.root / "refvid"
        d.mkdir()
        with mock.patch.object(ref_ingest.media, "run", return_value=""):    # ffmpeg writes nothing
            self.assertEqual(ref_ingest.timeline_sheets(self.video, d, 5.0), [])
        self.assertEqual((d / "work" / "timeline.txt").read_text().strip(), "")

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


class ShotsTests(Fixture):
    def test_split_makes_contiguous_draft_shots(self):
        d = write_video(self.root, shots=[graphic_shot("s001", 0.0, 10.0, "A1", ["stills/s001-a.jpg"])])
        ids = ref_shots.split(d, "s001", [4, 7])
        self.assertEqual(ids, ["s002", "s003"])
        shots = json.loads((d / "shots.json").read_text())["shots"]
        self.assertEqual([(s["id"], s["t_in"], s["t_out"]) for s in shots],
                         [("s001", 0.0, 4), ("s002", 4, 7), ("s003", 7, 10.0)])
        self.assertEqual(shots[0]["stills"], ["stills/s001-a.jpg"])
        self.assertEqual(shots[1]["status"], "draft")
        self.assertEqual(shots[1]["stills"], [])
        self.assertEqual(refs.validate_video(d, self.reg), [])

    def test_split_outside_the_shot_raises(self):
        d = write_video(self.root)
        for t in (0, 4, 5, -1):
            with self.assertRaises(ref_shots.RefShotsError):
                ref_shots.split(d, "s001", [t])

    def test_merge_adjacent_and_non_adjacent(self):
        d = write_video(self.root, shots=[graphic_shot("s001", 0.0, 4.0, "A1", ["stills/s001-a.jpg"]),
                                          face_shot("s002", 4.0, 7.0), face_shot("s003", 7.0, 10.0)])
        with self.assertRaises(ref_shots.RefShotsError):
            ref_shots.merge(d, "s001", "s003")
        ref_shots.merge(d, "s001", "s002")
        ref_shots.merge(d, "s001", "s003")
        shots = json.loads((d / "shots.json").read_text())["shots"]
        self.assertEqual([(s["id"], s["t_in"], s["t_out"], s["status"]) for s in shots],
                         [("s001", 0.0, 10.0, "reviewed")])
        self.assertEqual(refs.validate_video(d, self.reg), [])

    def test_restill_replaces_stills(self):
        video = synth.segments(self.root / "clip.mp4", [("red", 5.0), ("blue", 5.0)], size=(320, 180))
        d = write_video(self.root, stills=("stills/s001-a.jpg", "stills/s001-b.jpg"))
        out = ref_shots.restill(d, "s001", video, [1.0])
        self.assertEqual(out, ["stills/s001-a.jpg"])
        self.assertTrue((d / "stills/s001-a.jpg").read_bytes().startswith(b"\xff\xd8"))
        self.assertGreater((d / "stills/s001-a.jpg").stat().st_size, 10)
        self.assertFalse((d / "stills/s001-b.jpg").exists())
        shots = json.loads((d / "shots.json").read_text())["shots"]
        self.assertEqual(shots[0]["stills"], ["stills/s001-a.jpg"])

    def _two(self, **kw):
        s1 = graphic_shot("s001", 0.0, 4.0, "A1", ["stills/s001-a.jpg"])
        s2 = graphic_shot("s002", 4.0, 10.0, "A1", ["stills/s002-a.jpg"])
        return write_video(self.root, shots=[s1, s2], stills=("stills/s001-a.jpg", "stills/s002-a.jpg"))

    def _snapshot(self, d):
        return ((d / "shots.json").read_text(), sorted(p.name for p in (d / "stills").iterdir()))

    def test_restill_never_touches_other_shots(self):
        video = synth.segments(self.root / "clip.mp4", [("red", 5.0), ("blue", 5.0)], size=(320, 180))
        d = self._two()
        (d / "stills/s002-a.jpg").write_bytes(b"\xff\xd8keep")
        ref_shots.restill(d, "s001", video, [1.0, 2.0])
        self.assertEqual((d / "stills/s002-a.jpg").read_bytes(), b"\xff\xd8keep")

    def test_restill_missing_video_changes_nothing(self):
        d = self._two()
        before = self._snapshot(d)
        with self.assertRaises(media.MediaError):
            ref_shots.restill(d, "s001", self.root / "nope.mp4", [1.0])
        self.assertEqual(self._snapshot(d), before)

    def test_restill_default_times_and_bad_times(self):
        video = synth.segments(self.root / "clip.mp4", [("red", 5.0), ("blue", 5.0)], size=(320, 180))
        d = self._two()
        rels = ref_shots.restill(d, "s002", video)
        self.assertEqual(len(rels), len(ref_ingest.still_times(4.0, 10.0)))
        self.assertTrue(all((d / r).is_file() for r in rels))
        self.assertEqual(refs.validate_video(d, self.reg), [])
        with self.assertRaises(ref_shots.RefShotsError):
            ref_shots.restill(d, "s001", video, [5.0])

    def test_merge_renames_stills_to_owner(self):
        d = self._two()
        ref_shots.merge(d, "s001", "s002")
        shots = json.loads((d / "shots.json").read_text())["shots"]
        self.assertEqual(shots[0]["stills"], ["stills/s001-a.jpg", "stills/s001-b.jpg"])
        self.assertTrue((d / "stills/s001-b.jpg").is_file())
        self.assertFalse((d / "stills/s002-a.jpg").exists())
        self.assertEqual(refs.validate_video(d, self.reg), [])

    def test_split_after_merge_does_not_reuse_freed_id(self):
        d = self._two()
        ref_shots.merge(d, "s001", "s002")
        (d / "stills/s002-z.jpg").write_bytes(b"x")       # a file still carrying the id keeps it taken
        self.assertEqual(ref_shots.split(d, "s001", [5]), ["s003"])

    def test_cli_split_missing_video_changes_nothing(self):
        d = self._two()
        before = self._snapshot(d)
        with redirect_stdout(io.StringIO()) as out:
            code = ref_shots.main(["ref_shots.py", "demo", "split", "s001", "2", "--video", str(self.root / "no.mp4")], self.root)
        self.assertEqual(code, 1)
        self.assertEqual(self._snapshot(d), before)
        src = json.loads((d / "source.json").read_text())
        del src["source_file"]
        (d / "source.json").write_text(json.dumps(src))
        with redirect_stdout(io.StringIO()):
            self.assertEqual(ref_shots.main(["ref_shots.py", "demo", "split", "s001", "2"], self.root), 1)
        self.assertEqual(self._snapshot(d), before)

    def test_cli_usage_without_arguments(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = ref_shots.main(["ref_shots.py"], self.root)
        self.assertEqual(code, 2)
        self.assertIn("usage: python3 tools/ref_shots.py", out.getvalue())


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

    def test_prune_skips_subdirectories_in_stills(self):
        shots = [graphic_shot("s001", 0.0, 4.0, "A1", ["stills/s001-a.jpg"]), face_shot("s002", 4.0, 10.0)]
        d = write_video(self.root, shots=shots)
        (d / "stills" / "sub").mkdir()
        (d / "stills" / "sub" / "nested.jpg").write_bytes(b"x")
        self.assertEqual(ref_index.prune(self.root), 0)
        self.assertTrue((d / "stills" / "sub" / "nested.jpg").is_file())
        self.assertTrue((d / "stills" / "sub").is_dir())

    def test_stills_must_be_flat_jpg_paths_and_prune_never_leaves_stills(self):
        shots = [graphic_shot("s001", 0.0, 4.0, "A1", ["stills/s001-a.jpg"]), face_shot("s002", 4.0, 10.0)]
        d = write_video(self.root, shots=shots)
        data = json.loads((d / "shots.json").read_text())
        data["shots"][1]["stills"] = ["stills/../shots.json"]
        (d / "shots.json").write_text(json.dumps(data))
        before = (d / "shots.json").read_text()
        findings = refs.validate_video(d, self.reg)
        self.assertTrue(any("still stills/../shots.json must be stills/<name>.jpg" in f for f in findings), findings)
        self.assertEqual(ref_index.prune(self.root), 0)    # invalid video: skipped entirely
        self.assertEqual((d / "shots.json").read_text(), before)
        # and even a valid video never unlinks a listed non-stills path
        data["shots"][1]["stills"] = []
        (d / "shots.json").write_text(json.dumps(data))
        self.assertEqual(ref_index.prune(self.root), 0)
        self.assertTrue((d / "shots.json").is_file())

    def test_prune_skips_malformed_shots_json_and_still_prunes_valid_videos(self):
        shots = [graphic_shot("s001", 0.0, 4.0, "A1", ["stills/s001-a.jpg"]), face_shot("s002", 4.0, 10.0)]
        good = write_video(self.root, "good", shots=shots, stills=("stills/s001-a.jpg", "stills/s002-a.jpg"))
        data = json.loads((good / "shots.json").read_text())
        data["shots"][1]["stills"] = ["stills/s002-a.jpg"]
        (good / "shots.json").write_text(json.dumps(data))
        bad = write_video(self.root, "bad")
        (bad / "shots.json").write_text("{}")
        self.assertEqual(ref_index.prune(self.root), 1)
        self.assertEqual(sorted(p.name for p in (good / "stills").iterdir()), ["s001-a.jpg"])
        self.assertEqual((bad / "shots.json").read_text(), "{}")

    def test_check_reports_orphan_cards(self):
        write_video(self.root)
        ref_index.run(self.root)
        (self.root / "references/patterns/Z9.md").write_text("---\nid: Z9\n---\n")
        findings, _ = ref_index.run(self.root, check=True)
        self.assertIn("orphan pattern card Z9 — its catalogue row is gone; delete or restore the row", findings)

    def test_help_prints_usage_and_exits_zero(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(ref_index.main(["ref_index.py", "--help"], self.root), 0)
        self.assertIn("Usage:", buf.getvalue())
        with redirect_stdout(io.StringIO()):
            self.assertEqual(ref_index.main(["ref_index.py", "--bogus"], self.root), 2)


GRID = "| t_in | t_out | words | placement | type | beats | ease | marks |\n|---|---|---|---|---|---|---|---|\n"


@unittest.skipUnless(synth.HAVE_FFMPEG, "ffmpeg/ffprobe not installed")
class BoardTests(Fixture):
    def setUp(self):
        super().setUp()
        d = write_video(self.root)
        media.extract_frame(synth.segments(self.root / "r.mp4", [("red", 1)], size=(320, 180)), 0.5, d / "stills/s001-a.jpg")

    def test_compose_is_two_rows_of_three(self):
        lib = refs.load_library(self.root)
        refs_ = ref_board.ref_stills(lib, ["A1"])
        self.assertEqual(len(refs_), 1)
        out = ref_board.compose([refs_[0]], refs_, self.root / "b.jpg")
        wh = media.run([media.tool("ffprobe"), "-v", "error", "-show_entries", "stream=width,height",
                        "-of", "csv=p=0", str(out)]).strip()
        self.assertEqual(wh, "1920,720")

    def test_project_boards_pair_rows_with_slots(self):
        p = self.root / "proj"
        (p / "renders").mkdir(parents=True)
        (p / "storyboard.md").write_text("# S\n\n" + GRID + '| 0 | 2 | "w" | full-frame | A1 (card) | — | ease.enter | — |\n')
        (p / "index.html").write_text('<div data-composition-id="root"><div data-composition-src="compositions/a.html" '
                                      'data-composition-id="a" data-start="0" data-duration="2"></div></div>')
        render = synth.segments(p / "renders" / "reel.mp4", [("navy", 2)], size=(320, 180))
        boards = ref_board.project_boards(p, render, root=self.root)
        self.assertEqual([(b["row"], b["refs"]) for b in boards], [(1, ["demo s001"])])
        self.assertTrue((p / "renders/critique/row-01.jpg").is_file())
        self.assertIn("row-01.jpg", (p / "renders/critique/boards.md").read_text())


class PatternCheckTests(Fixture):
    def rows(self, *types):
        return [{"row": i + 1, "line": 10 + i, "type": t} for i, t in enumerate(types)]

    def test_known_ids_pass_and_missing_exemplars_warn(self):
        write_video(self.root)
        r = qa.check_patterns(self.rows("A1 (card)", "title"), "long-form", self.root)
        self.assertEqual(r["status"], "PASS")
        self.assertEqual(r["warnings"], ["storyboard.md line 11: title has no reviewed reference exemplar yet"])

    def test_unknown_or_missing_ids_fail(self):
        r = qa.check_patterns(self.rows("B9", "glass tiles"), "long-form", self.root)
        self.assertEqual(r["status"], "FAIL")
        self.assertIn("storyboard.md line 10: unknown pattern ID(s) B9", r["findings"][0])
        self.assertIn("storyboard.md line 11: type 'glass tiles' cites no kit name or catalogue ID", r["findings"][-1])

    def test_shorts_pass_with_a_note(self):
        r = qa.check_patterns(self.rows("anything"), "shorts", self.root)
        self.assertEqual((r["status"], r["note"]), ("PASS", "shorts: no pattern registry yet"))
