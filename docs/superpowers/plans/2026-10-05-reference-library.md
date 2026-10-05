# Animation Reference Library Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Git-committed, brand-agnostic library of analysed reference videos (timed shot logs with stills, tagged with catalogue pattern IDs) plus one pattern card per catalogue ID. Wire it into the storyboard, the critique loop and the QA gate, and seed it with Tymek's 7 After Effects reference videos.

**Architecture:** `tools/refs.py` is the library module (registry parsed from `standards/formats/long-form.md`, schema validation, exemplar lookup). Three CLIs sit on top of it:
- `ref_ingest.py`: video → draft shot log and stills
- `ref_index.py`: validate, generate `references/index.json` and the evidence blocks of the pattern cards
- `ref_board.py`: side-by-side critique boards

`qa.py` gains check 11. The analysis itself is agent work driven by `references/README.md`.

**Tech Stack:** Python 3 standard library only (repo rule), ffmpeg/ffprobe through `tools/media.py`, `unittest` with `tools/synth.py` clips.

**Spec:** `docs/superpowers/specs/2026-10-05-reference-library-design.md`

## Global Constraints

- Standard library only in `tools/*.py` (no PyYAML, Pillow or numpy). All media work goes through ffmpeg via `media.run` / `media.tool`.
- Stills are JPEG, 960 px wide, `-q:v 6`. The installed ffmpeg has no `libwebp` encoder.
- Per-video stills budget is 10 MB (`refs.STILLS_BUDGET = 10 * 1024 * 1024`).
- Media (`*.mp4`, `*.mov`, …) never goes into Git. `source.json` stores the file's basename only.
- `references/videos/*/work/` is gitignored.
- Rules stay in `standards/`, while `references/` holds evidence plus quality bars. Pattern IDs are read from `standards/formats/long-form.md`.
- Every tool prints its usage when run with no arguments (CLAUDE.md "Tools").
- The test command is `python3 -m unittest discover -s tools -p 'test_*.py' -v`. New tests go in `tools/test_refs.py`.
- Commit only when the plan says so. Pull before pushing (CLAUDE.md). Never commit `videos/startup-youtube-lessons-intro/` as part of this plan.
- Commit trailer: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

## Review Focus

1. **A video with no hard cuts at all** (one long canvas, or a screen recording). The ingest must produce one shot covering 0…duration with capped stills, not crash or emit zero shots. The test is in Task 2.
2. **A shot log edited by hand during analysis** (merged shots, a gap left, overlapping times, a still file deleted). Validation must name the shot and the problem, not raise a KeyError. The tests are in Task 1.
3. **A storyboard `type` cell with free text** such as `B3 + C8 (shared canvas)`, `D4 (full-frame card row)` or `title`. The IDs must be extracted and the prose ignored, and a typo such as `B9` must fail. The tests are in Task 1 and Task 5.
4. **Re-running `ref_index.py` after a second video is added.** Hand-written quality bars must survive and only the generated block may change, so `--check` must be clean right after a run. The test is in Task 3.
5. **Ingesting a slug that already exists.** It must refuse and never overwrite reviewed analysis. The test is in Task 2.

---

## File structure

| File | Responsibility |
|---|---|
| `tools/refs.py` (create) | registry, `type_ids`, load/validate one video, `load_library`, `exemplars`, card read/write helpers |
| `tools/ref_ingest.py` (create) | `shot_spans`, `still_times`, `extract_jpeg`, `ingest`, contact sheets, CLI |
| `tools/ref_index.py` (create) | `build_index`, `evidence_block`, `stub_card`, `prune`, `run` (write or check), CLI |
| `tools/ref_board.py` (create) | `ref_stills`, `compose`, `project_boards`, CLI |
| `tools/qa.py` (modify) | check 11 `Reference patterns` |
| `tools/test_refs.py` (create) | all tests for the four new modules |
| `tools/test_qa.py`, `tools/test_kit_qa.py`, `tools/test_standards_layout.py` (modify) | 10 → 11 checks |
| `standards/formats/long-form.md` (modify) | E1/E2 rows; pointer to `references/patterns/` |
| `standards/core/qa.md`, `standards/core/pipeline.md` (modify) | check 11; boards in the critique loop; ingest replaces the manual "Reference → style guide" step |
| `references/README.md` (create) | adding a video, analyst brief, schema, quality-bar procedure |
| `references/patterns/*.md`, `references/index.json` (generated, then hand-edited quality bars) | cards and index |
| `references/videos/<slug>/…` (generated, then analysed) | 7 corpus videos |
| `.gitignore`, `CLAUDE.md`, `docs/research/2026-10-03-custom-animation-catalogue.md` (modify) | ignore `work/`; tools list; superseded note |

---

### Task 1: Pattern registry and shot-log validation (`tools/refs.py`)

**Files:**
- Modify: `standards/formats/long-form.md` (section `## Section formats`)
- Create: `tools/refs.py`
- Test: `tools/test_refs.py`

**Interfaces:**
- Produces:
  - `refs.ROOT: Path`
  - `refs.RefError(Exception)`
  - `refs.registry(root=ROOT) -> dict[str, {"name": str, "group": "custom"|"section"|"kit"}]`
  - `refs.type_ids(cell: str, reg: dict) -> tuple[list[str], list[str]]` returns `(known, unknown)`
  - `refs.validate_video(d: Path, reg: dict) -> list[str]`
  - `refs.load_video(d: Path) -> {"dir": Path, "source": dict, "shots": list[dict]}`
  - `refs.video_dirs(root=ROOT) -> list[Path]`
  - `refs.load_library(root=ROOT) -> {"registry": dict, "videos": list[video], "findings": list[str]}`
  - `refs.exemplars(lib, pid) -> list[tuple[video, shot]]`
  - constants: `KINDS`, `STATUSES`, `GROUNDS`, `FILLS`, `NEW_PREFIX = "new:"`, `STILLS_BUDGET`, `GEN_START`, `GEN_END`, `STUB`, `empty_shot(i, t_in, t_out) -> dict`

- [ ] **Step 1: Give the section formats catalogue IDs in long-form.md**

In `standards/formats/long-form.md`, replace the body of `## Section formats` (the paragraph that starts "Recorded sections — a board walkthrough…") with:

```markdown
## Section formats

Recorded sections are not built in this pipeline. Treat them like screen-share: declare their ranges in
the BRIEF under `screen_share`, they are exempt from the cadence rule, and graphics go on top only on
request. They carry IDs so reference analysis can tag them:

| ID | Type | Notes | Use for |
|---|---|---|---|
| E1 | Board walkthrough + face PiP | recorded Miro board; PiP ≈ 25 % W bottom-right, rounded, soft shadow; zoom out to overview between sections | long structured walkthroughs |
| E2 | Slide deck + round face-cam | recorded slides; face circle ≈ 17 % W bottom-right | lecture-style sections |
```

- [ ] **Step 2: Write the failing tests**

Create `tools/test_refs.py`:

```python
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
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `cd tools && python3 -m unittest test_refs -v`
Expected: ERROR `ModuleNotFoundError: No module named 'refs'`

- [ ] **Step 4: Implement `tools/refs.py`**

```python
"""The animation reference library — references/ (see references/README.md).

references/videos/<slug>/source.json + shots.json + stills/   one analysed reference video each
references/patterns/<id>.md                                   one card per pattern ID
references/index.json                                         generated by tools/ref_index.py

Pattern IDs come from standards/formats/long-form.md: the catalogue rows (A1–E2) and the kit table
(HFKit.title → "title", HFKit.lowerThird → "lower-third"). The rules stay there; this library is the
evidence. Standard library only.
"""
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORMATS = ("long-form", "shorts")
PLACEMENTS = ("full-frame", "over-footage")
KINDS = ("face", "graphic", "section", "other")
STATUSES = ("draft", "reviewed")
GROUNDS = ("dark", "light", "mixed")
FILLS = ("sparse", "balanced", "dense")
NEW_PREFIX = "new:"
STILLS_BUDGET = 10 * 1024 * 1024
GEN_START, GEN_END = "<!-- generated:start -->", "<!-- generated:end -->"
STUB = "_Not written yet"
CATALOGUE_ROW = re.compile(r"^\|\s*([A-E]\d)\s*\|\s*([^|]+?)\s*\|", re.M)
KIT_ROW = re.compile(r"^\|\s*`HFKit\.(\w+)`\s*\|", re.M)
ID_TOKEN = re.compile(r"(?<![\w-])([A-Z]\d{1,2})(?![\w-])")
WORD_TOKEN = re.compile(r"(?<![\w-])([a-z]+(?:-[a-z]+)*)(?![\w-])")
HEX = re.compile(r"#[0-9A-Fa-f]{6}")
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
SHOT_ID = re.compile(r"s\d{3,}")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
SOURCE_KEYS = ("slug", "title", "url", "format", "ground", "made_by", "brand", "duration", "fps",
               "width", "height", "source_file", "ingested")


class RefError(Exception):
    """A reference file that is missing or cannot be parsed."""


def kebab(name: str) -> str:
    return re.sub(r"(?<!^)([A-Z])", r"-\1", name).lower()


def registry(root=ROOT) -> dict:
    """{id: {"name", "group"}} — catalogue/section IDs and kit components from the long-form profile."""
    text = (Path(root) / "standards" / "formats" / "long-form.md").read_text()
    reg = {}
    for m in CATALOGUE_ROW.finditer(text):
        pid = m.group(1)
        reg[pid] = {"name": m.group(2).strip("* ").strip(), "group": "section" if pid[0] == "E" else "custom"}
    for m in KIT_ROW.finditer(text):
        reg[kebab(m.group(1))] = {"name": f"HFKit.{m.group(1)}", "group": "kit"}
    return reg


def type_ids(cell: str, reg: dict):
    """Pattern IDs cited by a storyboard `type` cell: (known, unknown). Prose words are ignored;
    an ID-shaped token (letter + digits) that is not in the registry is unknown."""
    known, unknown = [], []
    for t in ID_TOKEN.findall(cell):
        (known if t in reg else unknown).append(t)
    known += [t for t in WORD_TOKEN.findall(cell) if t in reg and reg[t]["group"] == "kit"]
    return known, unknown


def empty_shot(i: int, t_in: float, t_out: float) -> dict:
    return {"id": f"s{i:03d}", "t_in": t_in, "t_out": t_out, "status": "draft", "kind": None, "pattern": None,
            "placement": None, "stills": [], "layout": None, "motion": None, "colours": [], "marks": [],
            "notes": "", "quality": ""}


def _num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _read_json(path: Path, findings: list, label: str):
    if not path.is_file():
        findings.append(f"{label}: {path.name} not found")
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        findings.append(f"{label}: {path.name} is not valid JSON ({e.msg} at line {e.lineno})")
        return None


def load_video(d) -> dict:
    d = Path(d)
    findings = []
    source = _read_json(d / "source.json", findings, d.name)
    shots = _read_json(d / "shots.json", findings, d.name)
    if findings:
        raise RefError("; ".join(findings))
    return {"dir": d, "source": source, "shots": shots.get("shots", []) if isinstance(shots, dict) else []}


def _check_source(src, d: Path) -> list:
    out = []
    if not isinstance(src, dict):
        return ["source.json: root must be an object"]
    missing = [k for k in SOURCE_KEYS if k not in src]
    if missing:
        out.append(f"source.json: missing {', '.join(missing)}")
    if src.get("slug") != d.name:
        out.append(f"source.json: slug {src.get('slug')!r} must equal the folder name {d.name!r}")
    if not SLUG.fullmatch(d.name):
        out.append(f"folder name {d.name!r} must be a kebab-case slug")
    if src.get("format") not in FORMATS:
        out.append(f"source.json: format must be one of {', '.join(FORMATS)}")
    if src.get("ground") not in GROUNDS:
        out.append(f"source.json: ground must be one of {', '.join(GROUNDS)}")
    for k in ("title", "made_by", "brand", "source_file"):
        if not (isinstance(src.get(k), str) and src.get(k).strip()):
            out.append(f"source.json: {k} must be a non-empty string")
    for k in ("duration", "fps"):
        if not (_num(src.get(k)) and src.get(k) > 0):
            out.append(f"source.json: {k} must be a positive number")
    for k in ("width", "height"):
        if not (isinstance(src.get(k), int) and src.get(k) > 0):
            out.append(f"source.json: {k} must be a positive integer")
    if not (isinstance(src.get("ingested"), str) and DATE.fullmatch(src["ingested"])):
        out.append("source.json: ingested must be YYYY-MM-DD")
    if "/" in str(src.get("source_file", "")):
        out.append("source.json: source_file is the file name only, never a path")
    return out


def _check_reviewed(s: dict, reg: dict, sid: str) -> list:
    out = []
    kind, pattern = s.get("kind"), s.get("pattern")
    if kind not in KINDS:
        return [f"{sid}: kind must be one of {', '.join(KINDS)}"]
    if kind in ("face", "other"):
        if pattern is not None:
            out.append(f"{sid}: a {kind} shot has no pattern (set null)")
        return out
    candidate = isinstance(pattern, str) and pattern.startswith(NEW_PREFIX) and SLUG.fullmatch(pattern[len(NEW_PREFIX):])
    if not (candidate or (isinstance(pattern, str) and pattern in reg)):
        out.append(f"{sid}: pattern {pattern!r} is not in the registry (an ID from standards/formats/long-form.md, or new:<slug>)")
    elif kind == "section" and not candidate and reg[pattern]["group"] != "section":
        out.append(f"{sid}: a section shot needs a section pattern (E1, E2 or new:<slug>), got {pattern}")
    if s.get("placement") not in PLACEMENTS:
        out.append(f"{sid}: placement must be full-frame or over-footage")
    if not (isinstance(s.get("quality"), str) and len(s["quality"].strip()) >= 20):
        out.append(f"{sid}: quality must say why the shot works (≥ 20 characters)")
    lay = s.get("layout")
    if not (isinstance(lay, dict) and isinstance(lay.get("type_px"), int) and lay["type_px"] >= 0
            and lay.get("fill") in FILLS and isinstance(lay.get("layers"), int) and lay["layers"] >= 1):
        out.append(f"{sid}: layout must be {{type_px: int ≥ 0, fill: {'|'.join(FILLS)}, layers: int ≥ 1}}")
    mo = s.get("motion")
    if not (isinstance(mo, dict) and isinstance(mo.get("entrance"), str) and mo["entrance"].strip()
            and isinstance(mo.get("camera"), str)
            and all(mo.get(k) is None or (_num(mo.get(k)) and mo[k] >= 0) for k in ("word_rate_s", "hold_s"))):
        out.append(f"{sid}: motion must be {{entrance: text, camera: text, word_rate_s: s|null, hold_s: s|null}}")
    if not (isinstance(s.get("colours"), list) and all(isinstance(c, str) and HEX.fullmatch(c) for c in s["colours"])):
        out.append(f"{sid}: colours must be a list of #RRGGBB")
    if not (isinstance(s.get("marks"), list) and all(isinstance(m, str) for m in s["marks"])):
        out.append(f"{sid}: marks must be a list of strings")
    if not s.get("stills"):
        out.append(f"{sid}: a reviewed {kind} shot keeps at least one still")
    return out


def validate_video(d, reg: dict) -> list:
    """Findings for one reference video folder; [] when valid. Never raises on bad content."""
    d = Path(d)
    label = f"references/videos/{d.name}"
    findings = []
    src = _read_json(d / "source.json", findings, label)
    data = _read_json(d / "shots.json", findings, label)
    if findings:
        return findings
    findings += [f"{label}/{f}" for f in _check_source(src, d)]
    shots = data.get("shots") if isinstance(data, dict) else None
    if not isinstance(shots, list) or not shots:
        return findings + [f"{label}/shots.json: needs a non-empty \"shots\" list"]
    fps = src.get("fps") if _num(src.get("fps")) and src.get("fps") > 0 else 30.0
    tol = 2 / fps + 1e-6
    seen, prev_out = set(), 0.0
    for i, s in enumerate(shots):
        sid = s.get("id") if isinstance(s, dict) else None
        where = f"{label}/shots.json {sid or f'#{i + 1}'}"
        if not isinstance(s, dict) or not (isinstance(sid, str) and SHOT_ID.fullmatch(sid)):
            findings.append(f"{where}: each shot is an object with an id like s001")
            continue
        if sid in seen:
            findings.append(f"{where}: duplicate id")
        seen.add(sid)
        a, b = s.get("t_in"), s.get("t_out")
        if not (_num(a) and _num(b) and b > a):
            findings.append(f"{where}: t_in/t_out must be numbers with t_out > t_in")
            continue
        if abs(a - prev_out) > tol:
            findings.append(f"{where}: starts at {a} but the previous shot ends at {prev_out}")
        prev_out = b
        if s.get("status") not in STATUSES:
            findings.append(f"{where}: status must be draft or reviewed")
        stills = s.get("stills")
        if not isinstance(stills, list):
            findings.append(f"{where}: stills must be a list")
            stills = []
        for p in stills:
            if not (isinstance(p, str) and p.startswith("stills/") and (d / p).is_file()):
                findings.append(f"{where}: still {p} not found")
        if s.get("status") == "reviewed":
            findings += [f"{label}/shots.json {f}" for f in _check_reviewed(s, reg, sid)]
        if s.get("exemplar") and s.get("kind") not in ("graphic", "section"):
            findings.append(f"{where}: only graphic or section shots can be exemplars")
    if _num(src.get("duration")) and abs(prev_out - src["duration"]) > tol:
        findings.append(f"{label}/shots.json: last shot ends at {prev_out} but the video lasts {src['duration']}")
    return findings


def video_dirs(root=ROOT) -> list:
    base = Path(root) / "references" / "videos"
    return sorted(p for p in base.iterdir() if p.is_dir() and (p / "source.json").is_file()) if base.is_dir() else []


def load_library(root=ROOT) -> dict:
    """Every valid video plus the findings of the invalid ones (which are left out of the library)."""
    reg = registry(root)
    videos, findings = [], []
    for d in video_dirs(root):
        f = validate_video(d, reg)
        if f:
            findings += f
            continue
        videos.append(load_video(d))
    return {"registry": reg, "videos": videos, "findings": findings}


def exemplars(lib: dict, pid: str) -> list:
    """Reviewed shots tagged `pid`: pinned exemplars first, then by video slug and time."""
    hits = [(v, s) for v in lib["videos"] for s in v["shots"]
            if s.get("status") == "reviewed" and s.get("pattern") == pid]
    return sorted(hits, key=lambda vs: (not vs[1].get("exemplar"), vs[0]["source"]["slug"], vs[1]["t_in"]))
```

Note that `exemplars` sorts pinned shots first and then by `(slug, t_in)`. The test therefore expects beta/s002 (pinned) first, then alpha/s001, then beta/s001.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd tools && python3 -m unittest test_refs -v`
Expected: all tests in `RegistryTests`, `ValidateTests` and `LibraryTests` PASS.

- [ ] **Step 6: Commit**

```bash
git add tools/refs.py tools/test_refs.py standards/formats/long-form.md
git commit -m "feat(refs): pattern registry and reference shot-log validation

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Ingest a reference video (`tools/ref_ingest.py`)

**Files:**
- Create: `tools/ref_ingest.py`
- Modify: `.gitignore`
- Test: `tools/test_refs.py` (append)

**Interfaces:**
- Consumes: `refs.empty_shot`, `refs.SLUG`, `refs.FORMATS`, `refs.GROUNDS`, `refs.validate_video`, `refs.registry`, `media.video_info`, `media.scene_cuts`, `media.run`, `media.tool`, `media.MediaError`
- Produces:
  - `ref_ingest.shot_spans(cuts, duration, min_shot=0.3) -> list[tuple[float, float]]`
  - `ref_ingest.still_times(t_in, t_out) -> list[float]`
  - `ref_ingest.extract_jpeg(video, t, out) -> Path`
  - `ref_ingest.ingest(video, meta: dict, root=ROOT, threshold=0.20) -> Path` (the video folder)
  - `ref_ingest.main(argv, root=ROOT) -> int`

- [ ] **Step 1: Write the failing tests** (append to `tools/test_refs.py`)

```python
import io
from contextlib import redirect_stdout

import ref_ingest
import synth

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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd tools && python3 -m unittest test_refs -v`
Expected: ERROR `No module named 'ref_ingest'`

- [ ] **Step 3: Implement `tools/ref_ingest.py`**

```python
"""Ingest a reference video into the animation reference library (references/README.md).

Usage:
  python3 tools/ref_ingest.py <video> --slug <slug> --title "<title>" --brand "<channel>"
                              --made-by "<who animated it>" --ground dark|light|mixed
                              [--url URL] [--format long-form|shorts] [--threshold 0.20]

Detects hard cuts (ffmpeg scene score > threshold), then writes references/videos/<slug>/ with:
  source.json   what the video is (file name only, never a path: media stays out of Git)
  shots.json    one draft shot per cut-to-cut span, together covering 0…duration
  stills/       JPEG stills per shot (960 px wide): entrance, middle, settled, + every 3 s on long shots
  work/         contact sheets (gitignored) for the analyst
An analyst then reviews every shot (references/README.md §Analyse) and runs tools/ref_index.py.
Refuses a slug that already exists — delete the folder to re-ingest.
"""
import argparse
import json
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path

import media
import refs

ROOT = refs.ROOT
MIN_SHOT = 0.3          # s — cuts closer than this to the previous edge are merged (flash frames)
STILL_WIDTH = 960
STILL_Q = 6             # ffmpeg -q:v for JPEG (2 best … 31 worst); ≈ 50–80 KB at 960 px
MAX_STILLS = 8
LONG_STEP = 3.0         # s — extra still spacing inside shots longer than 6 s
SHEET_COLS, SHEET_ROWS = 6, 6


class IngestError(Exception):
    """Bad arguments, an existing slug, or a media failure."""


def shot_spans(cuts, duration: float, min_shot: float = MIN_SHOT) -> list:
    edges = [0.0]
    for c in sorted(cuts):
        if c - edges[-1] >= min_shot and duration - c >= min_shot:
            edges.append(c)
    edges.append(duration)
    return [(round(a, 3), round(b, 3)) for a, b in zip(edges, edges[1:])]


def still_times(t_in: float, t_out: float) -> list:
    length = t_out - t_in
    if length < 1.0:
        return [round(t_in + length / 2, 3)]
    ts = {round(t_in + 0.25, 3), round(t_in + length / 2, 3), round(t_out - 0.3, 3)}
    if length > 6:
        k = 1
        while t_in + k * LONG_STEP < t_out - 0.3:
            ts.add(round(t_in + k * LONG_STEP, 3))
            k += 1
    ts = sorted(ts)
    if len(ts) > MAX_STILLS:
        ts = [ts[round(i * (len(ts) - 1) / (MAX_STILLS - 1))] for i in range(MAX_STILLS)]
    return ts


def extract_jpeg(video, t: float, out) -> Path:
    media.run([media.tool("ffmpeg"), "-v", "error", "-nostdin", "-y", "-ss", f"{max(t, 0):.3f}", "-i", str(video),
               "-frames:v", "1", "-vf", f"scale={STILL_WIDTH}:-2", "-q:v", str(STILL_Q), str(out)])
    if not Path(out).is_file():
        raise media.MediaError(f"no frame at t={t:.3f}s in {video}")
    return Path(out)


def contact_sheets(d: Path, shots: list) -> list:
    """work/contact-NN.jpg: the middle still of every shot, 6×6 per sheet, in shot order; work/contact.txt maps them."""
    work = d / "work"
    work.mkdir(exist_ok=True)
    picks = [(s["id"], d / s["stills"][len(s["stills"]) // 2]) for s in shots if s["stills"]]
    per = SHEET_COLS * SHEET_ROWS
    sheets, index = [], []
    for n, start in enumerate(range(0, len(picks), per), 1):
        chunk = picks[start:start + per]
        with tempfile.TemporaryDirectory() as tmp:
            for i, (_, p) in enumerate(chunk):
                (Path(tmp) / f"{i:04d}.jpg").symlink_to(p.resolve())
            out = work / f"contact-{n:02d}.jpg"
            media.run([media.tool("ffmpeg"), "-v", "error", "-nostdin", "-y", "-framerate", "1",
                       "-i", str(Path(tmp) / "%04d.jpg"), "-vf",
                       f"scale=320:-2,tile={SHEET_COLS}x{SHEET_ROWS}:padding=4:color=0x202020",
                       "-frames:v", "1", "-q:v", "4", str(out)])
        sheets.append(out)
        index += [f"{out.name} #{i + 1}: {sid}" for i, (sid, _) in enumerate(chunk)]
    (work / "contact.txt").write_text("\n".join(index) + "\n")
    return sheets


def ingest(video, meta: dict, root=ROOT, threshold: float = 0.20) -> Path:
    video = Path(video)
    slug = meta["slug"]
    if not refs.SLUG.fullmatch(slug):
        raise IngestError(f"slug {slug!r} must be kebab-case (a-z, 0-9, -)")
    if meta["format"] not in refs.FORMATS or meta["ground"] not in refs.GROUNDS:
        raise IngestError(f"format must be one of {refs.FORMATS}, ground one of {refs.GROUNDS}")
    d = Path(root) / "references" / "videos" / slug
    if d.exists():
        raise IngestError(f"{d} already ingested — delete the folder to re-ingest (this discards its analysis)")
    info = media.video_info(video)
    spans = shot_spans(media.scene_cuts(video, threshold), round(info["duration"], 3))
    (d / "stills").mkdir(parents=True)
    try:
        shots = []
        for i, (a, b) in enumerate(spans, 1):
            s = refs.empty_shot(i, a, b)
            for j, t in enumerate(still_times(a, b)):
                rel = f"stills/{s['id']}-{chr(97 + j)}.jpg"
                extract_jpeg(video, t, d / rel)
                s["stills"].append(rel)
            shots.append(s)
        source = {"slug": slug, "title": meta["title"], "url": meta.get("url") or "", "format": meta["format"],
                  "ground": meta["ground"], "made_by": meta["made_by"], "brand": meta["brand"],
                  "duration": round(info["duration"], 3), "fps": info["fps"], "width": info["width"],
                  "height": info["height"], "source_file": video.name, "ingested": date.today().isoformat()}
        (d / "source.json").write_text(json.dumps(source, indent=2) + "\n")
        (d / "shots.json").write_text(json.dumps({"version": 1, "shots": shots}, indent=2) + "\n")
        sheets = contact_sheets(d, shots)
    except Exception:
        shutil.rmtree(d, ignore_errors=True)     # never leave a half-ingested folder that blocks a retry
        raise
    size = sum(p.stat().st_size for p in (d / "stills").iterdir())
    print(f"{len(shots)} shots, {sum(len(s['stills']) for s in shots)} stills ({size / 1e6:.1f} MB), "
          f"{len(sheets)} contact sheets → {d}")
    print("next: analyse every shot (references/README.md §Analyse), then python3 tools/ref_index.py --prune")
    return d


def main(argv, root=ROOT) -> int:
    ap = argparse.ArgumentParser(prog="python3 tools/ref_ingest.py")
    ap.add_argument("video")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--brand", required=True)
    ap.add_argument("--made-by", required=True)
    ap.add_argument("--ground", required=True, choices=refs.GROUNDS)
    ap.add_argument("--url", default="")
    ap.add_argument("--format", default="long-form", choices=refs.FORMATS)
    ap.add_argument("--threshold", type=float, default=0.20)
    if len(argv) < 2:
        print(ap.format_usage().strip())
        print(__doc__)
        return 2
    a = ap.parse_args(argv[1:])
    meta = {"slug": a.slug, "title": a.title, "url": a.url, "format": a.format, "ground": a.ground,
            "made_by": a.made_by, "brand": a.brand}
    try:
        ingest(a.video, meta, root, a.threshold)
    except (IngestError, media.MediaError) as e:
        print(f"error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

Append to `.gitignore` (after the `**/work-*/` line):

```
references/videos/*/work/
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd tools && python3 -m unittest test_refs -v`
Expected: PASS, including `IngestTests` (skipped only when ffmpeg is missing).

If `test_ingest_writes_a_valid_draft` fails on the span list because the synthetic cuts land on frame boundaries, print `media.scene_cuts(self.video)`. The cut times must be exactly 1.5 and 3.5 (`test_media_tools` already pins `scene_cuts` to exact segment boundaries). Fix the implementation, not the expected spans.

- [ ] **Step 5: Commit**

```bash
git add tools/ref_ingest.py tools/test_refs.py .gitignore
git commit -m "feat(refs): ingest a reference video into a draft shot log with stills

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Index, pattern cards and pruning (`tools/ref_index.py`)

**Files:**
- Create: `tools/ref_index.py`
- Test: `tools/test_refs.py` (append)

**Interfaces:**
- Consumes: `refs.load_library`, `refs.exemplars`, `refs.registry`, `refs.video_dirs`, `refs.load_video`, `refs.GEN_START`, `refs.GEN_END`, `refs.STUB`, `refs.STILLS_BUDGET`, `refs.NEW_PREFIX`
- Produces:
  - `ref_index.build_index(lib) -> dict` (deterministic, no timestamps)
  - `ref_index.evidence_block(lib, pid) -> str` (text between and including the markers)
  - `ref_index.stub_card(pid, info) -> str`
  - `ref_index.card_status(text) -> "ready" | "draft"`
  - `ref_index.prune(root=ROOT) -> int` (files removed)
  - `ref_index.run(root=ROOT, check=False) -> tuple[list[str] findings, list[str] warnings]`
  - `ref_index.main(argv, root=ROOT) -> int`
  - index JSON shape:
    - `{"videos": [{"slug", "title", "ground", "format", "duration", "shots", "reviewed", "graphics_pct", "stills_bytes"}],`
    - `"patterns": {pid: {"name", "group", "card", "exemplars": [{"video", "shot", "t_in", "t_out", "stills"}], "stats": {...}}},`
    - `"candidates": {"new:x": [{"video", "shot"}]}}`

- [ ] **Step 1: Write the failing tests** (append to `tools/test_refs.py`)

```python
import ref_index


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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd tools && python3 -m unittest test_refs -v`
Expected: ERROR `No module named 'ref_index'`

- [ ] **Step 3: Implement `tools/ref_index.py`**

```python
"""Validate the animation reference library and regenerate its index and pattern-card evidence.

Usage:
  python3 tools/ref_index.py [--check] [--prune]

  (no flags)  validate every references/videos/<slug>/, write references/index.json, create a stub card
              references/patterns/<id>.md for every registry ID without one, and rewrite the generated
              evidence block of every card (the hand-written quality bar is never touched)
  --prune     first delete stills of reviewed face/other shots and stills no shot references
  --check     write nothing; exit 1 on any invalid video, draft shot, stills budget overrun, stale index or
              stale card. Cards whose quality bar is not written yet are warnings.
Pattern IDs come from standards/formats/long-form.md (tools/refs.py).
"""
import json
import statistics
import sys
from pathlib import Path

import refs

ROOT = refs.ROOT
MAX_TABLE = 8


def _ts(t: float) -> str:
    m, s = divmod(t, 60)
    return f"{int(m)}:{s:04.1f}"


def _median(values):
    vals = [v for v in values if isinstance(v, (int, float))]
    return round(statistics.median(vals), 2) if vals else None


def _spread(values):
    vals = sorted(v for v in values if isinstance(v, (int, float)))
    if len(vals) < 4:
        return None
    q = statistics.quantiles(vals, n=4)
    return [round(q[0], 2), round(q[2], 2)]


def _stats(hits) -> dict:
    durs = [s["t_out"] - s["t_in"] for _, s in hits]
    return {"count": len(hits), "videos": len({v["source"]["slug"] for v, _ in hits}),
            "duration_median": _median(durs), "duration_p25_p75": _spread(durs),
            "type_px_median": _median([(s.get("layout") or {}).get("type_px") for _, s in hits]),
            "word_rate_s_median": _median([(s.get("motion") or {}).get("word_rate_s") for _, s in hits]),
            "hold_s_median": _median([(s.get("motion") or {}).get("hold_s") for _, s in hits])}


def card_status(text: str) -> str:
    head = text.split(refs.GEN_START)[0]
    bar = head.split("## Quality bar", 1)[1] if "## Quality bar" in head else ""
    return "ready" if bar.strip() and refs.STUB not in bar else "draft"


def _card_path(root, pid) -> Path:
    return Path(root) / "references" / "patterns" / f"{pid}.md"


def build_index(lib: dict, root=ROOT) -> dict:
    videos = []
    for v in lib["videos"]:
        src, shots = v["source"], v["shots"]
        graphic = sum(s["t_out"] - s["t_in"] for s in shots if s.get("status") == "reviewed" and s.get("kind") == "graphic")
        videos.append({"slug": src["slug"], "title": src["title"], "ground": src["ground"], "format": src["format"],
                       "duration": src["duration"], "shots": len(shots),
                       "reviewed": sum(s.get("status") == "reviewed" for s in shots),
                       "graphics_pct": round(100 * graphic / src["duration"], 1),
                       "stills_bytes": sum(p.stat().st_size for p in (v["dir"] / "stills").glob("*"))})
    patterns = {}
    for pid, info in sorted(lib["registry"].items()):
        hits = refs.exemplars(lib, pid)
        card = _card_path(root, pid)
        patterns[pid] = {"name": info["name"], "group": info["group"],
                         "card": card_status(card.read_text()) if card.is_file() else "draft",
                         "exemplars": [{"video": v["source"]["slug"], "shot": s["id"], "t_in": s["t_in"],
                                        "t_out": s["t_out"], "stills": s["stills"]} for v, s in hits],
                         "stats": _stats(hits)}
    candidates = {}
    for v in lib["videos"]:
        for s in v["shots"]:
            p = s.get("pattern")
            if s.get("status") == "reviewed" and isinstance(p, str) and p.startswith(refs.NEW_PREFIX):
                candidates.setdefault(p, []).append({"video": v["source"]["slug"], "shot": s["id"]})
    return {"videos": videos, "patterns": patterns, "candidates": dict(sorted(candidates.items()))}


def evidence_block(lib: dict, pid: str) -> str:
    hits = refs.exemplars(lib, pid)
    st = _stats(hits)
    lines = [refs.GEN_START, "## Evidence (generated by tools/ref_index.py — do not edit)", ""]
    if not hits:
        lines += ["No reviewed reference shot uses this pattern yet.", refs.GEN_END]
        return "\n".join(lines)
    noun = "exemplar" if st["count"] == 1 else "exemplars"
    vids = "video" if st["videos"] == 1 else "videos"
    facts = [f"**{st['count']} {noun}** from {st['videos']} {vids}",
             f"duration median {st['duration_median']} s" + (f" (p25–p75 {st['duration_p25_p75'][0]}–{st['duration_p25_p75'][1]} s)" if st["duration_p25_p75"] else "")]
    if st["type_px_median"] is not None:
        facts.append(f"largest text median {st['type_px_median']} px at 1080")
    if st["word_rate_s_median"] is not None:
        facts.append(f"word build {st['word_rate_s_median']} s/word")
    if st["hold_s_median"] is not None:
        facts.append(f"hold {st['hold_s_median']} s")
    lines += [" · ".join(facts), "", "| Video | Time | Stills | Why it works |", "|---|---|---|---|"]
    for v, s in hits[:MAX_TABLE]:
        slug = v["source"]["slug"]
        pick = list(dict.fromkeys([s["stills"][len(s["stills"]) // 2], s["stills"][-1]]))
        imgs = " ".join(f"![{slug} {s['id']}](../videos/{slug}/{p})" for p in pick)
        why = " ".join(s.get("quality", "").split()).replace("|", "\\|")
        star = " ★" if s.get("exemplar") else ""
        lines.append(f"| {slug} {s['id']}{star} | {_ts(s['t_in'])}–{_ts(s['t_out'])} | {imgs} | {why} |")
    if len(hits) > MAX_TABLE:
        lines.append(f"\n…and {len(hits) - MAX_TABLE} more in references/index.json.")
    lines.append(refs.GEN_END)
    return "\n".join(lines)


def stub_card(pid: str, info: dict) -> str:
    return (f"---\nid: {pid}\nname: {info['name']}\ngroup: {info['group']}\n---\n"
            f"# {pid} — {info['name']}\n\n"
            f"Rule: `standards/formats/long-form.md` ({'kit table' if info['group'] == 'kit' else f'catalogue row {pid}'}). "
            "This card holds the evidence and the quality bar; the rule stays in the format profile.\n\n"
            f"## Quality bar\n\n{refs.STUB} — write it from the exemplars below (references/README.md §Quality bar)._\n\n"
            f"{refs.GEN_START}\n{refs.GEN_END}\n")


def _with_block(text: str, block: str, path: Path) -> str:
    if refs.GEN_START not in text or refs.GEN_END not in text:
        raise refs.RefError(f"{path}: missing {refs.GEN_START} / {refs.GEN_END} markers — restore them")
    head, rest = text.split(refs.GEN_START, 1)
    tail = rest.split(refs.GEN_END, 1)[1]
    return head + block + tail


def prune(root=ROOT) -> int:
    removed = 0
    for d in refs.video_dirs(root):
        path = d / "shots.json"
        data = json.loads(path.read_text())
        keep = set()
        for s in data["shots"]:
            if s.get("status") == "reviewed" and s.get("kind") in ("face", "other") and s.get("stills"):
                for p in s["stills"]:
                    (d / p).unlink(missing_ok=True)
                    removed += 1
                s["stills"] = []
            keep.update(s.get("stills") or [])
        for p in (d / "stills").glob("*"):
            if f"stills/{p.name}" not in keep:
                p.unlink()
                removed += 1
        path.write_text(json.dumps(data, indent=2) + "\n")
    return removed


def run(root=ROOT, check=False):
    lib = refs.load_library(root)
    findings, warnings = list(lib["findings"]), []
    for v in lib["videos"]:
        slug = v["source"]["slug"]
        drafts = sum(s.get("status") == "draft" for s in v["shots"])
        if drafts:
            findings.append(f"{slug}: {drafts} draft shot{'s' if drafts > 1 else ''} — analyse them (references/README.md §Analyse)")
        faces = [s["id"] for s in v["shots"] if s.get("kind") in ("face", "other") and s.get("stills") and s.get("status") == "reviewed"]
        if faces:
            findings.append(f"{slug}: reviewed face/other shots still have stills ({', '.join(faces[:5])}…) — run --prune")
    index = build_index(lib, root)
    for row in index["videos"]:
        if row["stills_bytes"] > refs.STILLS_BUDGET:
            findings.append(f"{row['slug']}: stills are {row['stills_bytes'] / 1e6:.1f} MB, over the "
                            f"{refs.STILLS_BUDGET / 1e6:.0f} MB budget — drop stills of weak shots")
    want_index = json.dumps(index, indent=2) + "\n"
    index_path = Path(root) / "references" / "index.json"
    cards = {}
    for pid, info in lib["registry"].items():
        path = _card_path(root, pid)
        text = path.read_text() if path.is_file() else stub_card(pid, info)
        cards[path] = _with_block(text, evidence_block(lib, pid), path)
        if card_status(cards[path]) == "draft" and refs.exemplars(lib, pid):
            warnings.append(f"{pid}: quality bar not written yet ({len(refs.exemplars(lib, pid))} exemplars available)")
    if check:
        if not index_path.is_file() or index_path.read_text() != want_index:
            findings.append("references/index.json is stale — run python3 tools/ref_index.py")
        stale = [p.stem for p, t in cards.items() if not p.is_file() or p.read_text() != t]
        if stale:
            findings.append(f"pattern cards stale: {', '.join(sorted(stale))} — run python3 tools/ref_index.py")
        return findings, warnings
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(want_index)
    for path, text in cards.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return findings, warnings


def main(argv, root=ROOT) -> int:
    args = argv[1:]
    unknown = [a for a in args if a not in ("--check", "--prune")]
    if unknown:
        print(__doc__)
        return 2
    try:
        if "--prune" in args and "--check" not in args:
            print(f"pruned {prune(root)} still files")
        findings, warnings = run(root, check="--check" in args)
    except (refs.RefError, json.JSONDecodeError) as e:
        print(f"error: {e}")
        return 1
    for w in warnings:
        print(f"warning: {w}")
    for f in findings:
        print(f"- {f}")
    lib_videos = len(refs.video_dirs(root))
    print(("FAIL" if findings else "OK") + f" — {lib_videos} reference videos")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

The CLI deliberately takes no required arguments: the bare command is the everyday "regenerate" action, so it prints the docstring only for unknown flags. Add one line to the module docstring saying so, since CLAUDE.md says tools print their usage with no arguments: `Run with no flags to regenerate; any unknown flag prints this help.`

The `graphics_pct` in the first test is 40.0 because the fixture has a 4 s graphic in a 10 s video.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd tools && python3 -m unittest test_refs -v`
Expected: PASS (all IndexTests).

- [ ] **Step 5: Commit**

```bash
git add tools/ref_index.py tools/test_refs.py
git commit -m "feat(refs): index, pattern-card evidence blocks and still pruning

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Critique boards (`tools/ref_board.py`)

**Files:**
- Create: `tools/ref_board.py`
- Test: `tools/test_refs.py` (append)

**Interfaces:**
- Consumes: `refs.load_library`, `refs.exemplars`, `refs.type_ids`, `project.read_storyboard`, `project.composition_slots`, `project.slot_pairing`, `media.video_info`, `media.extract_frame`, `media.run`, `media.tool`
- Produces:
  - `ref_board.ref_stills(lib, pids, n=3) -> list[Path]`, the settled still of each exemplar, round-robin across `pids`
  - `ref_board.compose(candidates: list[Path], references: list[Path], out: Path) -> Path`, a 1920×720 JPEG with the candidate row on top and the reference row below (3 tiles of 640×360 each, dark blanks)
  - `ref_board.project_boards(project, render, row=None, root=ROOT) -> list[dict]` writes `renders/critique/row-NN.jpg` + `boards.md`. Each dict is `{"row", "type", "board", "refs"}`.
  - `ref_board.main(argv, root=ROOT) -> int`

- [ ] **Step 1: Write the failing tests** (append to `tools/test_refs.py`)

```python
import media
import ref_board

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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd tools && python3 -m unittest test_refs -v`
Expected: ERROR `No module named 'ref_board'`

- [ ] **Step 3: Implement `tools/ref_board.py`**

```python
"""Critique boards: a candidate frame above reference stills of the same pattern (standards/core/qa.md §2).

Usage:
  python3 tools/ref_board.py videos/<slug> --render R.mp4 [--row N]
      full-frame storyboard rows, paired with index.html slots (as slice.py pairs them); writes
      renders/critique/row-NN.jpg and renders/critique/boards.md
  python3 tools/ref_board.py --pattern ID [--pattern ID …] --still FRAME.png [--still FRAME2.png] -o OUT.jpg
      any frame — e.g. an over-footage overlay composited over the face — against a pattern's references

Top row: the candidate (middle and settled frame). Bottom row: up to 3 settled stills of reviewed reference
shots of the row's patterns (pinned exemplars first). Look at the gap and score Craft and On-brand against it.
"""
import argparse
import sys
import tempfile
from pathlib import Path

import media
import project as pj
import refs

ROOT = refs.ROOT
TILE_W, TILE_H = 640, 360
BLANK = "0x111111"
SETTLE = 0.35   # s before the slot ends: inside check 9's still window


def ref_stills(lib: dict, pids, n: int = 3) -> list:
    queues = [[v["dir"] / s["stills"][-1] for v, s in refs.exemplars(lib, pid) if s.get("stills")] for pid in pids]
    out = []
    while len(out) < n and any(queues):
        for q in queues:
            if q and len(out) < n:
                out.append(q.pop(0))
    return out


def compose(candidates, references, out) -> Path:
    tiles = (list(candidates)[:3] + [None] * 3)[:3] + (list(references)[:3] + [None] * 3)[:3]
    args, chains = [media.tool("ffmpeg"), "-v", "error", "-nostdin", "-y"], []
    for i, t in enumerate(tiles):
        if t is None:
            args += ["-f", "lavfi", "-i", f"color=c={BLANK}:s={TILE_W}x{TILE_H}:d=1"]
        else:
            args += ["-i", str(t)]
        chains.append(f"[{i}:v]scale={TILE_W}:{TILE_H}:force_original_aspect_ratio=decrease,"
                      f"pad={TILE_W}:{TILE_H}:(ow-iw)/2:(oh-ih)/2:color={BLANK},setsar=1,format=yuvj420p[t{i}]")
    graph = ";".join(chains) + ";[t0][t1][t2]hstack=3[top];[t3][t4][t5]hstack=3[bot];[top][bot]vstack[out]"
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    media.run(args + ["-filter_complex", graph, "-map", "[out]", "-frames:v", "1", "-q:v", "4", str(out)])
    return Path(out)


def project_boards(project, render, row=None, root=ROOT) -> list:
    project = Path(project)
    lib = refs.load_library(root)
    rows = pj.read_storyboard(project)
    fps = media.video_info(render)["fps"]
    pairs, problems = pj.slot_pairing(pj.composition_slots(project), rows, fps)
    if problems:
        raise pj.ProjectError("; ".join(problems))
    out_dir = project / "renders" / "critique"
    boards = []
    with tempfile.TemporaryDirectory() as tmp:
        for slot, r in pairs:
            if row is not None and r["row"] != row:
                continue
            frames = []
            for name, t in (("mid", slot["start"] + slot["dur"] / 2),
                            ("settled", max(slot["start"], slot["start"] + slot["dur"] - SETTLE))):
                frames.append(media.extract_frame(render, t, Path(tmp) / f"{r['row']}-{name}.png", width=960))
            pids, _ = refs.type_ids(r["type"], lib["registry"])
            stills = ref_stills(lib, pids)
            board = compose(frames, stills, out_dir / f"row-{r['row']:02d}.jpg")
            boards.append({"row": r["row"], "type": r["type"], "board": board.name,
                           "refs": [f"{p.parents[1].name} {p.name.split('-')[0]}" for p in stills]})
    lines = ["# Critique boards", "", "Top: candidate (mid, settled). Bottom: reference stills of the row's patterns.", "",
             "| Row | Type | Board | References |", "|---|---|---|---|"]
    lines += [f"| {b['row']} | {b['type']} | [{b['board']}]({b['board']}) | {', '.join(b['refs']) or 'none yet'} |" for b in boards]
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "boards.md").write_text("\n".join(lines) + "\n")
    return boards


def main(argv, root=ROOT) -> int:
    ap = argparse.ArgumentParser(prog="python3 tools/ref_board.py")
    ap.add_argument("project", nargs="?")
    ap.add_argument("--render")
    ap.add_argument("--row", type=int)
    ap.add_argument("--pattern", action="append", default=[])
    ap.add_argument("--still", action="append", default=[])
    ap.add_argument("-o", "--out")
    if len(argv) < 2:
        print(__doc__)
        return 2
    a = ap.parse_args(argv[1:])
    try:
        if a.project:
            if not a.render:
                ap.error("project mode needs --render")
            for b in project_boards(a.project, a.render, a.row, root):
                print(f"row {b['row']:>2} {b['type']}: {b['board']} vs {', '.join(b['refs']) or 'no references yet'}")
            return 0
        if not (a.pattern and a.still and a.out):
            ap.error("frame mode needs --pattern, --still and -o")
        lib = refs.load_library(root)
        unknown = [p for p in a.pattern if p not in lib["registry"]]
        if unknown:
            ap.error(f"unknown pattern ID(s): {', '.join(unknown)}")
        print(compose([Path(s) for s in a.still], ref_stills(lib, a.pattern), Path(a.out)))
        return 0
    except (pj.ProjectError, media.MediaError, refs.RefError) as e:
        print(f"error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

The `refs` label in a board dict is `"<video slug> <shot id>"`. For `.../videos/demo/stills/s001-a.jpg`, `parents[1].name` is `demo` and the stem prefix is `s001`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd tools && python3 -m unittest test_refs -v`
Expected: PASS (BoardTests). Tiles are converted to `yuvj420p` because `hstack` needs one pixel format and the MJPEG encoder wants full-range YUV.

- [ ] **Step 5: Commit**

```bash
git add tools/ref_board.py tools/test_refs.py
git commit -m "feat(refs): critique boards — candidate frames above reference stills

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: QA check 11, "Reference patterns"

**Files:**
- Modify: `tools/qa.py` (docstring line 1, `NAMES`, a new `check_patterns`, its call in `run_gate`)
- Modify: `standards/core/qa.md` ("ten checks" → "eleven checks"; table row 11; critique-loop step 1)
- Modify: `tools/test_qa.py`, `tools/test_kit_qa.py`, `tools/test_standards_layout.py` (every `range(1, 11)` that enumerates gate checks becomes `range(1, 12)`)
- Test: `tools/test_refs.py` (append)

**Interfaces:**
- Consumes: `refs.load_library(root)`, `refs.type_ids`, `refs.exemplars`
- Produces: `qa.check_patterns(rows, fmt, root=ROOT) -> dict` (a `qa.result(11, …)` with an optional `"warnings"` list)

- [ ] **Step 1: Write the failing tests** (append to `tools/test_refs.py`)

```python
import qa


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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd tools && python3 -m unittest test_refs.PatternCheckTests -v`
Expected: FAIL/ERROR `module 'qa' has no attribute 'check_patterns'`

- [ ] **Step 3: Implement check 11 in `tools/qa.py`**

1. Change the first docstring line to `"""The automated QA gate — standards/core/qa.md §1: all 11 checks, PASS / FAIL per check.`
2. Add `import refs` after `import project as pj`.
3. Extend `NAMES`: append `11: "Reference patterns"` to the dict literal.
4. Add after `check_captions`:

```python
def check_patterns(rows, fmt, root=ROOT):
    """Check 11: every long-form storyboard row cites a kit name or catalogue ID (references/README.md);
    an ID-shaped token that is not in the registry fails; a pattern with no reviewed exemplar warns."""
    if fmt != "long-form":
        return result(11, [], "shorts: no pattern registry yet")
    lib = refs.load_library(root)
    findings, warnings = [], []
    for r in rows:
        where = f"storyboard.md line {r['line']}"
        known, unknown = refs.type_ids(r["type"], lib["registry"])
        if unknown:
            findings.append(f"{where}: unknown pattern ID(s) {', '.join(unknown)} — use an ID from standards/formats/long-form.md")
        if not known and not unknown:
            findings.append(f"{where}: type {r['type']!r} cites no kit name or catalogue ID")
        warnings += [f"{where}: {pid} has no reviewed reference exemplar yet" for pid in known if not refs.exemplars(lib, pid)]
    out = result(11, findings, "type column → standards/formats/long-form.md IDs; evidence in references/patterns/")
    out["warnings"] = warnings
    return out
```

5. In `run_gate`, after the `checks[8] = …` statement, add:

```python
    checks[11] = result(11, [rows_error]) if rows_error else guarded(11, check_patterns, rows, fmt, root)
```

`ordered = [checks[n] for n in sorted(checks)]` already sorts, so 11 lands last. `format_report` already prints `warnings`.

- [ ] **Step 4: Update the check-count tests and qa.md**

Run: `grep -n "range(1, 11)" tools/test_qa.py tools/test_kit_qa.py tools/test_standards_layout.py`

Change each one that enumerates gate checks (or qa.md table rows) to `range(1, 12)`. Read each hit's context first. In `test_qa.py` around lines 325, 333 and 373, `qa.result(n) for n in range(1, 11)` builds check lists for waiver tests; switch those to `range(1, 12)` too so `NAMES` coverage stays complete.

In `standards/core/qa.md`:
- Replace "for each of the ten checks below" with "for each of the eleven checks below".
- Append a row to the §1 table:

```markdown
| 11 | Reference patterns | long-form: every storyboard `type` cites a kit name or catalogue ID from `standards/formats/long-form.md`; an unknown ID fails; a cited pattern with no reviewed exemplar in `references/` is a warning (Shorts: pass, no registry yet) |
```

- Replace critique-loop step 1 with:

```markdown
1. Render the preview material: a contact sheet of every graphic, three full-res frames per graphic
   (entrance, mid, settled), a 10 fps strip of every camera move, and the reference boards
   (`python3 tools/ref_board.py videos/<slug> --render <reel.mp4>`; over-footage layouts with
   `--pattern <ID> --still <frame> -o <board.jpg>`). Each board puts the candidate above settled stills of
   the same pattern from `references/` — open the pattern card (`references/patterns/<ID>.md`) and score
   **On-brand** and **Craft** against its quality bar and those stills, not against an imagined bar.
```

- [ ] **Step 5: Run the full suite**

Run: `python3 -m unittest discover -s tools -p 'test_*.py' -v 2>&1 | tail -5`
Expected: `OK` (skips allowed for missing chrome-headless-shell / ffmpeg). Fixture storyboards in `test_qa.py` use `A1` and `make_project` in `test_cadence_scan.py` uses `A1`, which is a known ID, so check 11 passes with an exemplar warning. If a qa fixture row uses a non-ID type, update the fixture row to a catalogue ID.

- [ ] **Step 6: Commit**

```bash
git add tools/qa.py tools/test_refs.py tools/test_qa.py tools/test_kit_qa.py tools/test_standards_layout.py standards/core/qa.md
git commit -m "feat(qa): check 11 — storyboard rows cite reference pattern IDs

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Library docs, stub cards and pipeline wiring

**Files:**
- Create: `references/README.md`
- Generate: `references/patterns/*.md` (31 stubs), `references/index.json`
- Modify: `standards/core/pipeline.md` (`## Reference → style guide`, Long-form steps 2 and 6), `standards/formats/long-form.md` (one line under `## Custom catalogue`), `CLAUDE.md` (Tools list + one rule), `docs/research/2026-10-03-custom-animation-catalogue.md` (superseded note)
- Test: `tools/test_standards_layout.py` (append)

- [ ] **Step 1: Write the failing test** (append a class to `tools/test_standards_layout.py`)

```python
class ReferenceLibraryTests(unittest.TestCase):
    def test_every_registry_id_has_a_card_and_the_library_checks_clean(self):
        import ref_index
        import refs
        for pid in refs.registry(ROOT):
            self.assertTrue((ROOT / "references" / "patterns" / f"{pid}.md").is_file(), pid)
        self.assertEqual(ref_index.run(ROOT, check=True)[0], [])

    def test_docs_point_at_the_library(self):
        self.assertIn("tools/ref_ingest.py", (ROOT / "references" / "README.md").read_text())
        self.assertIn("references/patterns/", (ROOT / "standards" / "formats" / "long-form.md").read_text())
        self.assertIn("tools/ref_ingest.py", (ROOT / "standards" / "core" / "pipeline.md").read_text())
        self.assertIn("ref_board.py", (ROOT / "CLAUDE.md").read_text())
```

Run: `cd tools && python3 -m unittest test_standards_layout.ReferenceLibraryTests -v`
Expected: FAIL (no cards, no README).

- [ ] **Step 2: Write `references/README.md`**

````markdown
# Animation Reference Library

Every brand and every video borrows its motion grammar from here. **Rules** live in
`standards/formats/<format>.md`. This folder holds the **evidence**: real reference videos broken down shot
by shot, and one card per pattern with a quality bar and the best stills. Agents look at these stills
before building and compare their renders against them in the critique loop (`standards/core/qa.md` §2).

```
references/
  index.json               generated — per-video stats, per-pattern exemplars, new-pattern candidates
  patterns/<id>.md         one card per pattern ID in standards/formats/long-form.md (A1…E2 + kit names)
  videos/<slug>/
    source.json            what the video is (file name only — the media stays on the shared drive)
    shots.json             contiguous shots covering 0…duration, each draft → reviewed
    stills/*.jpg           960 px stills of graphic and section shots (committed)
    work/                  contact sheets and scratch (gitignored)
```

## Add a reference video (stackable — repeat for every new video)

1. **Ingest:**
   ```bash
   python3 tools/ref_ingest.py "<video file>" --slug <kebab-slug> --title "<YouTube title>" \
     --brand "<whose channel>" --made-by "<who animated it>" --ground dark|light|mixed [--url <youtube url>]
   ```
   It writes a draft `shots.json`: one shot per hard cut, stills per shot and contact sheets in `work/`.
2. **Analyse** every shot (below). Draft shots block `ref_index.py --check`.
3. **Prune and index:** `python3 tools/ref_index.py --prune`. This deletes stills of face shots, regenerates
   `index.json` and every card's evidence block, and creates a card for any new catalogue ID.
4. **Quality bars:** update the bar of every pattern the video touched (below).
5. **Check and commit:** `python3 tools/ref_index.py --check` must print `OK`. Commit `references/`
   (stills included). Stay within the 10 MB stills budget per video.

## Analyse

Work through `work/contact-NN.jpg` (with `work/contact.txt` mapping tiles to shot ids), then each shot's
stills. When motion matters (camera legs, word builds, holds), cut a 10 fps strip from the source video
into `work/`:

```bash
ffmpeg -ss <t_in> -to <t_out> -i "<video>" -vf fps=10,scale=480:-2 "references/videos/<slug>/work/<id>-%03d.jpg"
```

For every shot, set `"status": "reviewed"` and fill in:

| Field | What to write |
|---|---|
| `kind` | `face` (talking head, punch-ins included), `graphic` (full-frame or over-footage animation), `section` (recorded board/deck), `other` (b-roll, screen recording without graphics) |
| `pattern` | graphic/section only: an ID from `standards/formats/long-form.md` (A1…E2, or a kit name such as `title`, `lower-third`, `roadmap`). Nothing fits → `new:<kebab-name>` (it shows up under `candidates` in `index.json`; promote it by adding a catalogue row). |
| `placement` | `full-frame` or `over-footage` |
| `layout` | `{"type_px": <cap height of the largest text, in px at 1080 p; 0 = no text>, "fill": "sparse"\|"balanced"\|"dense", "layers": <depth layers: ground, backdrop, cards, marks…>}` |
| `motion` | `{"entrance": "<how it arrives>", "camera": "<legs and stops, or none>", "word_rate_s": <s per word or null>, "hold_s": <still hold before the cut or null>}` |
| `colours` | the 1–4 dominant non-neutral colours as `#RRGGBB` |
| `marks` | hand-drawn marks used: `underline`, `scribble`, `arrow`, `circle`, `strike`, `highlight-block`, `check`, `cross`, `script-word` |
| `quality` | one or two sentences: **why this looks expensive** — the specific craft (depth, real UI, the micro-detail, timing), not a description of the content |
| `notes` | anything else: what is said, a variant, a bug |
| `exemplar` | `true` on the best 1–2 shots of a pattern in this video (pinned first on the card) |

Face and other shots need only `kind` (pattern `null`). You may **merge** shots (one canvas the detector split
on a camera move: extend `t_out`, delete the next shot, keep its stills if useful) or **split** one (copy it,
adjust the times, give it a new id `s<NNN>` above the highest existing; ids need not be consecutive). Shots must
stay contiguous: each `t_in` equals the previous `t_out`.

Take the grammar, never the content: logos, faces and copy in the stills are evidence, not assets.

## Quality bar

The top of each card (`patterns/<id>.md`, above the generated block) is hand-written and survives
regeneration. Write **4–8 checkable bullets** a reviewer can verify on a still or a 10 fps strip, drawn
from what the exemplars share. For example:

- Focus card ≥ 55 % of frame width; the backdrop is the same screenshot blurred and dimmed to ≈ 35 %.
- Headline cap height ≥ 70 px at 1080; never more than 2 lines.
- Highlight lands only after the card has settled (≥ 0.3 s), sweeping left → right in ≈ 0.3 s.

Where a bullet contradicts the rule row in `standards/formats/long-form.md`, change the rule in the same
commit (promotion rule) and say so in the commit message.

## Use it when building a video

- **Storyboard:** every row's `type` cites a pattern ID (QA check 11). Before building a pattern, open
  its card and look at the stills.
- **Critique loop:** `python3 tools/ref_board.py videos/<slug> --render <reel.mp4>` puts each full-frame
  graphic above reference stills of its pattern. For over-footage layouts, use
  `--pattern <ID> --still <frame.png> -o <board.jpg>`. Score Craft and On-brand against the card.
````

- [ ] **Step 3: Generate the stub cards and index**

Run: `python3 tools/ref_index.py`
Expected: `OK — 0 reference videos`, plus 31 files in `references/patterns/` (A1–A6, B1–B4, C1–C8, D1–D5, E1, E2, title, subtitle, lower-third, side-text, cta-youtube, roadmap) and `references/index.json`.

- [ ] **Step 4: Wire the docs**

`standards/core/pipeline.md`. Replace the five numbered steps under `## Reference → style guide` with:

```markdown
To adopt a new look (a client's reference video, a new house variant), add the reference to the library
first (`references/README.md`): `python3 tools/ref_ingest.py <video> --slug … --title … --brand … --made-by …
--ground …`, analyse every shot, `python3 tools/ref_index.py --prune`, write the quality bars. Then:
1. Promote what is new into `standards/formats/` (a catalogue row → a pattern card appears) or
   `brands/<brand>/` (values), per the promotion rule.
2. Write the beat grid for the new video citing those pattern IDs.
3. Take the grammar of the reference, never its content — no logos, characters, footage or copy.
```

In `## Long-form`:
- Step 2: after "every graphic with its kit name or catalogue ID", insert ` (QA check 11) — open each pattern's card in `references/patterns/` and look at its stills first`.
- Step 6: change it to `6. **Critique loop** (`standards/core/qa.md` §2) with reference boards (`python3 tools/ref_board.py`) — scores and fixes into `critique.md`.`

`standards/formats/long-form.md`. Directly under the `## Custom catalogue` heading's first paragraph, add:

```markdown
Evidence for every ID (and every kit component) — reference stills, measured ranges and a quality bar —
is in `references/patterns/<ID>.md`; look at it before building the pattern.
```

`CLAUDE.md`:
- In `## Tools — tools/`, append to the tool list sentence: `` · `ref_ingest.py` / `ref_index.py` / `ref_board.py` (animation reference library — `references/README.md`) ``.
- Add rule 10 to `## Rules for any video task`:

```markdown
10. **Look before building.** Every storyboard row cites a pattern ID (QA check 11); open its card in
    `references/patterns/` and study the stills first, and run `tools/ref_board.py` in the critique loop.
    New reference videos are added with `tools/ref_ingest.py` (`references/README.md`).
```

`docs/research/2026-10-03-custom-animation-catalogue.md`. Insert after the title line:

```markdown
> **Superseded 2026-10-05** by the reference library (`references/`): the same videos with committed stills,
> per-shot measurements and pattern cards. This draft is kept for history; edit the library, not this file.
```

- [ ] **Step 5: Run the tests**

Run: `python3 -m unittest discover -s tools -p 'test_*.py' 2>&1 | tail -3`
Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add references standards/core/pipeline.md standards/formats/long-form.md CLAUDE.md docs/research/2026-10-03-custom-animation-catalogue.md tools/test_standards_layout.py
git commit -m "docs(refs): reference library README, pattern card stubs, pipeline wiring

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Pilot — the measured reference video, then Tymek reviews

The pilot proves the analyst brief before six more videos repeat any mistake in it.

**Files:**
- Generate and analyse: `references/videos/ultra-predictable-funnel/…`
- Modify: the quality bar of every card this video touches; `references/index.json`

- [ ] **Step 1: Ingest**

```bash
python3 tools/ref_ingest.py "/Users/tymek/Downloads/How to build ULTRA predictable Youtube Sales Funnel for B2B High-Ticket Offer.mp4" \
  --slug ultra-predictable-funnel --title "How to build ULTRA predictable Youtube Sales Funnel for B2B High-Ticket Offer" \
  --brand "Contentporary (Tymek Bielinski)" --made-by "Tymek's editor (After Effects)" --ground dark \
  --url "https://www.youtube.com/watch?v=HrYMfy6MZtA"
```

Expected: about 100–250 shots, stills ≤ 40 MB before pruning, and contact sheets in `work/`. If a file is missing from `~/Downloads`, stop and ask Tymek for it (it comes from the shared drive).

- [ ] **Step 2: Analyse every shot**, following `references/README.md` §Analyse. The analyst runs on Opus 5.5 at max effort: this is the judgement step. Use `docs/research/2026-10-03-custom-animation-catalogue.md` and the spec Appendix A in `docs/superpowers/specs/2026-10-03-animation-workflow-design.md` as cross-checks for pattern assignment and timings. Do not copy their numbers without looking.

- [ ] **Step 3: Prune, index, check**

```bash
python3 tools/ref_index.py --prune
python3 tools/ref_index.py --check
```

Expected: `OK — 1 reference videos`. Warnings list cards whose quality bar isn't written yet. `index.json` graphics_pct should be close to the research table's ≈ 29 % for this video. A large difference means a `kind` error; recheck it.

- [ ] **Step 4: Write the quality bars** of every pattern with exemplars (README §Quality bar). Rerun `python3 tools/ref_index.py` and confirm `--check` is OK with no warnings for those patterns.

- [ ] **Step 5: Commit**

```bash
git add references
git commit -m "refs: analyse the reference video (HrYMfy6MZtA) — pilot

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 6: Checkpoint with Tymek.** Show him three pattern cards (rendered markdown with stills) and the `index.json` video row. Ask him: does the tagging match how he'd describe the shots, and do the quality bars capture what makes them good? Apply his corrections to `references/README.md` and this video before Task 8.

---

### Task 8: The other six videos, then promote findings

**Files:**
- Generate and analyse: `references/videos/<slug>/…` ×6
- Modify: pattern cards' quality bars, `references/index.json`, and possibly `standards/formats/long-form.md` (promotions)

- [ ] **Step 1: Ingest all six** (sequential commands, each is a few minutes):

```bash
D=/Users/tymek/Downloads
python3 tools/ref_ingest.py "$D/I Spent \$10,000 on Mentors So You Don't Have To (Free YouTube Selling Course).mp4" --slug spent-10k-on-mentors --title "I Spent \$10,000 on Mentors So You Don't Have To (Free YouTube Selling Course)" --brand "Contentporary (Tymek Bielinski)" --made-by "Tymek's editor (After Effects)" --ground dark
python3 tools/ref_ingest.py "$D/How Alex Hormozi creates 100 viral posts a day (blueprint for b2b founders).mp4" --slug hormozi-100-posts --title "How Alex Hormozi creates 100 viral posts a day (blueprint for b2b founders)" --brand "Contentporary (Tymek Bielinski)" --made-by "Tymek's editor (After Effects)" --ground dark
python3 tools/ref_ingest.py "$D/How Instantly Built a \$1M ARR YouTube Channel.mp4" --slug instantly-1m-arr-channel --title "How Instantly Built a \$1M ARR YouTube Channel" --brand "Contentporary (Tymek Bielinski)" --made-by "Tymek's editor (After Effects)" --ground dark
python3 tools/ref_ingest.py "$D/How Liam Ottley outsmarted the smma gurus and built a \$540,000 _ mo business.mp4" --slug liam-ottley-540k --title "How Liam Ottley outsmarted the smma gurus and built a \$540,000 / mo business" --brand "Contentporary (Tymek Bielinski)" --made-by "Tymek's editor (After Effects)" --ground light
python3 tools/ref_ingest.py "$D/The Problem With Clay.com for Agency Owners.mp4" --slug problem-with-clay --title "The Problem With Clay.com for Agency Owners" --brand "Contentporary (Tymek Bielinski)" --made-by "Tymek's editor (After Effects)" --ground light
python3 tools/ref_ingest.py "$D/The Stupidly Simple YouTube Strategy Making Businesses Rich.mp4" --slug stupidly-simple-youtube-strategy --title "The Stupidly Simple YouTube Strategy Making Businesses Rich" --brand "Contentporary (Tymek Bielinski)" --made-by "Tymek's editor (After Effects)" --ground light
```

If Tymek corrected any channel or ground value at the pilot checkpoint, use his values. The brand field is whose channel the video sits on; ask him if unsure for the Instantly and Clay videos.

- [ ] **Step 2: Analyse each video**, one subagent per video in parallel. Each runs on Opus 5.5 at max effort and gets: `references/README.md`, the pilot video's `shots.json` as a worked example, and its own slug. The subagents touch disjoint folders, so they can run concurrently. They must NOT run `ref_index.py` (the controller does that once). For Hormozi (E2) and Instantly (E1), mark the long recorded section as `section` shots and analyse only the graphics around them in detail.

- [ ] **Step 3: Prune and index; resolve findings**

```bash
python3 tools/ref_index.py --prune
python3 tools/ref_index.py --check
```

Fix every finding in the owning video's `shots.json`. Compare each video's `graphics_pct` with the research table: Mentors 31.5, Hormozi 77, Instantly 96, Ottley 23, Clay 36, Simple 57. The table counted section formats as graphics, so for Hormozi and Instantly compare graphic + section.

- [ ] **Step 4: Quality bars and promotions**

1. Update the bar of every card with exemplars, so that no `--check` warnings remain for patterns with ≥ 1 exemplar.
2. Go through `candidates` in `index.json`. Any `new:<name>` with ≥ 2 shots across ≥ 2 videos becomes a catalogue row in `standards/formats/long-form.md` with the next free ID in its group. Retag its shots, then rerun `ref_index.py` so the new card appears. Write its quality bar. A candidate with fewer uses stays listed.
3. Where measured ranges contradict a `long-form.md` rule row (e.g. sizes, durations), update the row in the same commit.

- [ ] **Step 5: Full verification**

```bash
python3 tools/ref_index.py --check
python3 -m unittest discover -s tools -p 'test_*.py' 2>&1 | tail -3
du -sh references
```

Expected: `OK — 7 reference videos`, tests `OK`, `references/` ≤ 70 MB.

- [ ] **Step 6: Commit and report**

```bash
git add references standards/formats/long-form.md
git commit -m "refs: analyse the remaining six reference videos; quality bars; promoted patterns

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

Report to Tymek:
- shots and graphics % per video
- patterns with the most evidence, and patterns with none
- the candidates and the promotions made
- the total size of `references/`

Do not push until he asks; pull first when he does.
