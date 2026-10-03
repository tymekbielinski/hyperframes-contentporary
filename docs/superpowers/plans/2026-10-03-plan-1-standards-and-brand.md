# Plan 1 — Standards & Brand Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the contradictory `context/` docs with the layered `standards/` + `brands/` structure from the spec, plus a tested validator for brand files and per-video brand choices.

**Architecture:** Rules become markdown in `standards/core/` (every brand and format) and `standards/formats/` (per format). Brand values become JSON (`tokens.json` and `palettes/*.json`) plus prose (`brand.md`) under `brands/<name>/`. `tools/brandcheck.py` validates brand folders and the palette/font/override choices a video BRIEF makes. Plan 3's QA gate and Plan 2's `lib/brand.js` both consume this layer. Old docs are migrated or removed, and `CLAUDE.md` is slimmed.

**Tech Stack:** Markdown, JSON, Python 3 standard library only (`unittest`, `json`, `re`, `pathlib`), matching the repo's existing `tools/test_*.py` convention.

**Spec:** `docs/superpowers/specs/2026-10-03-animation-workflow-design.md` (§4 architecture, §5 core law, §6 formats, §7 brands, §9 QA, §10 pipeline, §11 migration). Roadmap: `docs/superpowers/plans/2026-10-03-animation-workflow-roadmap.md`.

## Global Constraints

- Precedence: core → format profile → brand → video BRIEF. Lower layers supply values and never override a rule above (spec §4).
- Brands supply values and assets, never motion technique (spec §7).
- Palette roles, all required in every palette: `ground` (deep, centre, grid, dots), `surface` (fill, fillAlt, bevel, halo), `text` (primary, secondary), `accent` (block, text, glow, line), `accentScript`, `status` (ok, x) (spec §7).
- Kit components: `title`, `subtitle`, `lower-third`, `side-text`, `cta-youtube`, `roadmap` (spec §8).
- Long-form never has running captions; spoken words appear only as `kit.lower-third` key lines. Shorts captions are a per-project flag (spec §6).
- Gaussian blur is allowed only for reasons `focus`, `glow`, `wipe` (spec §5.5, §9a).
- Python standard library only. No new dependencies.
- `videos/*` is frozen. No task edits anything under `videos/`.
- Work on a branch (`standards-v1`), not `main`. Pull before starting and before pushing (CLAUDE.md sync rule). Push only when Tymek asks.

**Spec clarification — CONFIRMED by Tymek 2026-10-03 (smear allowed in Shorts only):** design-system §8c documents one more Gaussian case: element-level smear on content that is itself animating (card-04 row slams), which `HFMotionBlur` can't texture. The spec's core rule 5 lists only `focus`, `glow` and the Shorts `wipe`. This plan files the element smear under the `wipe` reason as **Shorts-only** (both are masked or feathered card motion the library can't texture) and says so in `shorts.md`. If Tymek disagrees, drop that paragraph from Task 5 and the smear is banned.

## Review Focus

1. **A palette missing a role or sub-key** (e.g. a client palette without `status.x`). Expected: the validator names the exact missing path, e.g. `red.json: missing status.x`, not a crash or a generic failure. Tested in Task 1.
2. **Colour values in an unexpected format** (`#fff`, `red`, `rgb(…)`, lowercase hex). Expected: `#RRGGBB` (any case) and `rgba(r,g,b,a)` are accepted; everything else is rejected with the offending value. Tested in Task 1.
3. **`tokens.json` lists a palette with no file, or `defaultPalette` isn't in the list.** Expected: a named error for each. Tested in Task 1.
4. **A video BRIEF picks a palette, font or override the brand doesn't have** (e.g. `font: geometric` for a client with only one headline font, or an override path like `accent.blok`). Expected: `validate_choice` rejects it and lists the allowed options. Tested in Task 1.
5. **Active docs still pointing at deleted files** (`context/…`, `PIPELINE.md`, `../CLAUDE.md`, `templates/script-template.md`). Expected: none remain in `CLAUDE.md`, `standards/**` or `brands/**` after migration. Tested in Task 7.

---

## File Structure

```
tools/brandcheck.py                         validator: brand folder + per-video choice
tools/test_brandcheck.py                    unit tests for the validator
tools/test_standards_layout.py              layout + content + stale-reference tests
brands/_template/tokens.json                draft skeleton, every required key
brands/_template/palettes/base.json         palette skeleton, every role
brands/_template/brand.md                   visual-language prose skeleton
brands/_template/narrative.md               CTA / offer / pillars skeleton
brands/_template/assets/MANIFEST.md         asset + font provenance skeleton
brands/_template/README.md                  client onboarding steps
brands/contentporary/tokens.json            approved Contentporary tokens
brands/contentporary/palettes/{red,gold,lime,reel-dark,reel-light}.json
brands/contentporary/brand.md               Contentporary visual language
brands/contentporary/narrative.md           moved from context/narrative.md
brands/contentporary/assets/MANIFEST.md     font sources, reference provenance
standards/core/motion.md                    core motion law (spec §5)
standards/core/qa.md                        QA gate definition (spec §9)
standards/core/pipeline.md                  production pipeline (spec §10)
standards/formats/long-form.md              long-form profile (spec §6a + Appendix A)
standards/formats/shorts.md                 Shorts profile (from design-system.md §1, §6–8c, §9b)
standards/reference/motion-waapi.md         moved from context/motion-waapi.md
CLAUDE.md                                   rewritten (slim)
DELETED: context/design-system.md, context/motion-craft.md, context/frame.md,
         context/custom.md, context/voice.md, PIPELINE.md, templates/script-template.md
```

Run all tests with:
`python3 -m unittest discover -s tools -p 'test_*.py' -v`

---

### Task 1: Brand validator (`tools/brandcheck.py`)

**Files:**
- Create: `tools/brandcheck.py`
- Test: `tools/test_brandcheck.py`

**Interfaces:**
- Consumes: nothing.
- Produces (used by Tasks 2, 3, 7 and later by Plan 3's `tools/qa`):
  - `PALETTE_ROLES: dict[str, list[str] | None]`
  - `KIT_COMPONENTS: list[str]`, `KNOWN_MARKS: list[str]`
  - `is_colour(value: str) -> bool`
  - `validate_palette(data: dict, label: str) -> list[str]`
  - `load_brand(brand_dir: Path) -> dict`, returning `{"tokens": dict, "palettes": {name: dict}}`
  - `validate_brand(brand_dir: Path) -> list[str]` (empty list = valid)
  - `validate_choice(brand_dir: Path, palette: str, font: str | None = None, overrides: dict | None = None) -> list[str]`
  - CLI: `python3 tools/brandcheck.py <brand_dir>` → prints errors, exits 1 if there are any, else prints `OK <name> (<status>)` and exits 0.

- [ ] **Step 1: Branch and pull**

```bash
cd /Users/tymek/Desktop/hyperframes-contentporary
git status
git pull
git checkout -b standards-v1
```

- [ ] **Step 2: Write the failing tests**

Create `tools/test_brandcheck.py`:

```python
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
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `python3 -m unittest discover -s tools -p 'test_brandcheck.py' -v`
Expected: ERROR — `ModuleNotFoundError: No module named 'brandcheck'`

- [ ] **Step 4: Write the implementation**

Create `tools/brandcheck.py`:

```python
"""Validate brand folders (brands/<name>/) and the per-video choices a BRIEF makes.

Spec: docs/superpowers/specs/2026-10-03-animation-workflow-design.md section 7.
Usage: python3 tools/brandcheck.py brands/<name>
"""
import json
import re
import sys
from pathlib import Path

PALETTE_ROLES = {
    "ground": ["deep", "centre", "grid", "dots"],
    "surface": ["fill", "fillAlt", "bevel", "halo"],
    "text": ["primary", "secondary"],
    "accent": ["block", "text", "glow", "line"],
    "accentScript": None,
    "status": ["ok", "x"],
}
KIT_COMPONENTS = ["title", "subtitle", "lower-third", "side-text", "cta-youtube", "roadmap"]
KNOWN_MARKS = [
    "highlight-block", "scribble-underline", "underline", "curved-arrow", "connector",
    "status-chip", "script-word", "strike", "ring", "group-outline", "tool-chip",
]
STATUSES = ("draft", "approved")

_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
_RGBA = re.compile(r"^rgba\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*(0|1|0?\.\d+)\s*\)$")


def is_colour(value) -> bool:
    return isinstance(value, str) and bool(_HEX.match(value) or _RGBA.match(value))


def _role_paths():
    for role, subs in PALETTE_ROLES.items():
        if subs is None:
            yield role, (role,)
        else:
            for sub in subs:
                yield f"{role}.{sub}", (role, sub)


def _get(data, keys):
    cur = data
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return None, False
        cur = cur[k]
    return cur, True


def validate_palette(data: dict, label: str) -> list:
    errors = []
    for path, keys in _role_paths():
        value, found = _get(data, keys)
        if not found:
            errors.append(f"{label}: missing {path}")
        elif not is_colour(value):
            errors.append(f"{label}: {path} is not a colour: {value!r}")
    for key, value in (data.get("extras") or {}).items():
        if not is_colour(value):
            errors.append(f"{label}: extras.{key} is not a colour: {value!r}")
    return errors


def load_brand(brand_dir: Path) -> dict:
    brand_dir = Path(brand_dir)
    tokens = json.loads((brand_dir / "tokens.json").read_text())
    palettes = {}
    for name in tokens.get("palettes", []):
        f = brand_dir / "palettes" / f"{name}.json"
        if f.is_file():
            palettes[name] = json.loads(f.read_text())
    return {"tokens": tokens, "palettes": palettes}


def validate_brand(brand_dir: Path) -> list:
    brand_dir = Path(brand_dir)
    folder = brand_dir.name
    if not (brand_dir / "tokens.json").is_file():
        return [f"{folder}: missing tokens.json"]
    brand = load_brand(brand_dir)
    t = brand["tokens"]
    errors = []

    if t.get("name") != folder:
        errors.append(f"{folder}: tokens.name {t.get('name')!r} does not match folder name")
    if t.get("status") not in STATUSES:
        errors.append(f"{folder}: status must be 'draft' or 'approved', got {t.get('status')!r}")

    listed = t.get("palettes") or []
    if not listed:
        errors.append(f"{folder}: palettes must list at least one palette")
    for name in listed:
        if name not in brand["palettes"]:
            errors.append(f"{folder}: palette {name!r} listed but palettes/{name}.json missing")
        else:
            errors += validate_palette(brand["palettes"][name], f"{folder}/palettes/{name}.json")
    if t.get("defaultPalette") not in listed:
        errors.append(f"{folder}: defaultPalette {t.get('defaultPalette')!r} not in palettes")

    fonts = t.get("fonts") or {}
    headline = fonts.get("headline") or {}
    if not headline:
        errors.append(f"{folder}: fonts.headline must define at least one font")
    for key, spec in headline.items():
        for field in ("family", "weight", "source"):
            if field not in spec:
                errors.append(f"{folder}: fonts.headline.{key} missing {field}")
    if fonts.get("defaultHeadline") not in headline:
        errors.append(
            f"{folder}: fonts.defaultHeadline {fonts.get('defaultHeadline')!r} not in fonts.headline")
    for role, fields in (("body", ("family", "weight", "source")), ("script", ("family", "source"))):
        spec = fonts.get(role)
        if not isinstance(spec, dict):
            errors.append(f"{folder}: fonts.{role} missing")
            continue
        for field in fields:
            if field not in spec:
                errors.append(f"{folder}: fonts.{role} missing {field}")

    kit = t.get("kit") or {}
    for comp in KIT_COMPONENTS:
        if not isinstance(kit.get(comp), str) or not kit.get(comp):
            errors.append(f"{folder}: kit missing component {comp!r}")

    marks = t.get("marks") or []
    if not marks:
        errors.append(f"{folder}: marks must list at least one mark")
    for m in marks:
        if m not in KNOWN_MARKS:
            errors.append(f"{folder}: unknown mark {m!r}")
    return errors


def validate_choice(brand_dir: Path, palette: str, font=None, overrides=None) -> list:
    brand_dir = Path(brand_dir)
    brand = load_brand(brand_dir)
    t = brand["tokens"]
    name = t.get("name", brand_dir.name)
    errors = []
    if t.get("status") != "approved":
        errors.append(f"brand {name} is not approved (status: {t.get('status')})")
    listed = t.get("palettes") or []
    if palette not in listed:
        errors.append(f"palette {palette!r} not in brand {name} (have: {', '.join(listed)})")
    headline = (t.get("fonts") or {}).get("headline") or {}
    if font is not None and font not in headline:
        errors.append(f"font {font!r} not in brand {name} (have: {', '.join(headline)})")
    valid_paths = {p for p, _ in _role_paths()}
    for path, value in (overrides or {}).items():
        if path not in valid_paths:
            errors.append(f"override {path!r} is not a palette role")
        elif not is_colour(value):
            errors.append(f"override {path!r} is not a colour: {value!r}")
    return errors


def main(argv) -> int:
    if len(argv) != 2:
        print("usage: python3 tools/brandcheck.py brands/<name>")
        return 2
    brand_dir = Path(argv[1])
    errors = validate_brand(brand_dir)
    for e in errors:
        print(e)
    if errors:
        return 1
    t = load_brand(brand_dir)["tokens"]
    print(f"OK {t['name']} ({t['status']})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python3 -m unittest discover -s tools -p 'test_brandcheck.py' -v`
Expected: all tests PASS (24 tests).

- [ ] **Step 6: Commit**

```bash
git add tools/brandcheck.py tools/test_brandcheck.py
git commit -m "feat(tools): add brand and per-video choice validator

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Brand template (`brands/_template/`)

**Files:**
- Create: `brands/_template/tokens.json`, `brands/_template/palettes/base.json`, `brands/_template/brand.md`, `brands/_template/narrative.md`, `brands/_template/assets/MANIFEST.md`, `brands/_template/README.md`
- Test: `tools/test_standards_layout.py` (created here, extended in later tasks)

**Interfaces:**
- Consumes: `brandcheck.validate_brand`, `brandcheck.load_brand` (Task 1).
- Produces: the onboarding skeleton that Plan 3's `tools/new-video` and future client onboarding copy from. Its `name` is `_template` and its `status` is `draft`.

- [ ] **Step 1: Write the failing test**

Create `tools/test_standards_layout.py`:

```python
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
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 -m unittest discover -s tools -p 'test_standards_layout.py' -v`
Expected: FAIL — `_template: missing tokens.json`

- [ ] **Step 3: Create the template files**

`brands/_template/tokens.json`:

```json
{
  "name": "_template",
  "status": "draft",
  "palettes": ["base"],
  "defaultPalette": "base",
  "fonts": {
    "headline": {
      "primary": { "family": "REPLACE: client headline family", "weight": 700, "source": "REPLACE: licence + where the file lives on the shared drive" }
    },
    "defaultHeadline": "primary",
    "body": { "family": "REPLACE: client body family", "weight": 500, "source": "REPLACE" },
    "script": { "family": "REPLACE: script/handwriting family for accent words", "source": "REPLACE" }
  },
  "kit": {
    "title": "glow-center",
    "subtitle": "glass-pill-script",
    "lower-third": "key-line",
    "side-text": "grid-panel-chips",
    "cta-youtube": "watch-page-dive",
    "roadmap": "wave-nodes"
  },
  "marks": ["highlight-block", "underline", "connector", "status-chip", "script-word"]
}
```

`brands/_template/palettes/base.json`:

```json
{
  "name": "base",
  "ground": { "deep": "#000000", "centre": "#000000", "grid": "#000000", "dots": "#000000" },
  "surface": { "fill": "#000000", "fillAlt": "#000000", "bevel": "#000000", "halo": "rgba(255,255,255,0.06)" },
  "text": { "primary": "#FFFFFF", "secondary": "#000000" },
  "accent": { "block": "#000000", "text": "#000000", "glow": "#000000", "line": "#000000" },
  "accentScript": "#000000",
  "status": { "ok": "#000000", "x": "#000000" }
}
```

`brands/_template/brand.md`:

```markdown
# <Client> — Brand

**Status:** draft. Not usable in a video until `tokens.json` says `"status": "approved"`.
Precedence: `standards/core` → `standards/formats/<format>` → this brand → the video BRIEF.
A brand supplies values and assets, never motion technique.

## Constant visual language
What makes every video feel like this brand, whatever palette it uses. Describe each:
- **Ground:** base tone, texture (grid, dots, noise, none), vignette, light source.
- **Surfaces:** card or glass treatment, border/bevel, halo or shadow.
- **Headline treatment:** glow, gradient, weight.
- **Accent words:** how emphasis is shown (colour block, script word, underline).
- **Marks:** which marks from `tokens.json` → `marks` this brand uses, and any it never uses.

## Palettes
One line per palette in `palettes/`: what it's for, and which video moods it suits.

## Fonts
Which headline fonts a video may pick (`tokens.json` → `fonts.headline`), the body font, the script.

## Kit variants
The variant chosen for each kit component in `tokens.json` → `kit`, and why.

## Never
Things that would break this brand (colours, effects, layouts to avoid).
```

`brands/_template/narrative.md`:

```markdown
# <Client> — Narrative

- **CTA destination:** where viewers are sent (URL) and the exact link text.
- **Offer:** what the CTA sells, in one sentence.
- **Content pillars:** the 2–4 topics the channel covers.
- **Tone:** person (you/we), words to avoid.
- **North-star metric:** what the videos exist to drive.
```

`brands/_template/assets/MANIFEST.md`:

```markdown
# Assets — <Client>

| Asset | File (shared drive path) | Source | Licence / approval | Captured on |
|---|---|---|---|---|
| Logo | | | | |
| Headline font | | | | |
| Body font | | | | |
| Script font | | | | |

## Still to obtain
- 
```

`brands/_template/README.md`:

```markdown
# Onboarding a new brand

1. `cp -R brands/_template brands/<client-slug>` and set `"name": "<client-slug>"` in `tokens.json`.
2. Capture the client's brand guide / website / Figma. Record every source in `assets/MANIFEST.md`.
3. Map their colours onto the palette roles (`ground`, `surface`, `text`, `accent`, `accentScript`,
   `status`). Rename `palettes/base.json` and add more palettes if the brand has distinct moods.
4. Fill `fonts`, choose a variant for each `kit` component, and list the `marks` the brand uses.
5. Fill `brand.md` (constant visual language) and `narrative.md`.
6. Validate: `python3 tools/brandcheck.py brands/<client-slug>`.
7. Render the brand proof sheet (Plan 4 tooling): full-screen title, subtitle, lower third and
   side screen text in every palette.
8. Tymek reviews the proof sheet. On approval set `"status": "approved"`. Only approved brands pass
   the QA gate.
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 -m unittest discover -s tools -p 'test_standards_layout.py' -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add brands/_template tools/test_standards_layout.py
git commit -m "feat(brands): add brand onboarding template

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Contentporary brand (`brands/contentporary/`)

**Files:**
- Create: `brands/contentporary/tokens.json`, `brands/contentporary/palettes/red.json`, `gold.json`, `lime.json`, `reel-dark.json`, `reel-light.json`, `brands/contentporary/brand.md`, `brands/contentporary/assets/MANIFEST.md`
- Move: `context/narrative.md` → `brands/contentporary/narrative.md` (then edit)
- Test: `tools/test_standards_layout.py` (extend)

**Interfaces:**
- Consumes: `brandcheck` (Task 1).
- Produces: brand `contentporary`, status `approved`; palettes `red`, `gold`, `lime`, `reel-dark`, `reel-light`; headline fonts `helvetica`, `geometric`. Plan 2's `lib/brand.js` reads these exact files.

- [ ] **Step 1: Extend the test (failing)**

Append to `tools/test_standards_layout.py`, above the `if __name__` line:

```python
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `python3 -m unittest discover -s tools -p 'test_standards_layout.py' -v`
Expected: FAIL — `contentporary: missing tokens.json`

- [ ] **Step 3: Create tokens and palettes**

`brands/contentporary/tokens.json`:

```json
{
  "name": "contentporary",
  "status": "approved",
  "palettes": ["red", "gold", "lime", "reel-dark", "reel-light"],
  "defaultPalette": "red",
  "fonts": {
    "headline": {
      "helvetica": { "family": "Helvetica Now Display", "weight": 700, "source": "Commercial (Monotype). Team copy on the shared drive: Fonts/HelveticaNowDisplay. Used by the long-form reference and the Shorts reels." },
      "geometric": { "family": "Satoshi", "weight": 700, "source": "Fontshare (Indian Type Foundry), free commercial licence. Used by the template stills and video 09." }
    },
    "defaultHeadline": "helvetica",
    "body": { "family": "SF Pro Display", "weight": 500, "source": "Apple system font. On non-Apple render machines use Inter 500 (Google Fonts)." },
    "script": { "family": "Brittany Signature", "source": "Monoline signature script seen in the long-form reference. Licence to confirm; file on the shared drive: Fonts/" },
    "captions": { "family": "Garet Heavy", "weight": 800, "source": "Shorts burned-in captions only (design-system reels). Shared drive: Fonts/" }
  },
  "kit": {
    "title": "glow-center",
    "subtitle": "glass-pill-script",
    "lower-third": "key-line",
    "side-text": "grid-panel-chips",
    "cta-youtube": "watch-page-dive",
    "roadmap": "wave-nodes"
  },
  "marks": ["highlight-block", "scribble-underline", "underline", "curved-arrow", "connector", "status-chip", "script-word", "strike", "ring", "group-outline", "tool-chip"],
  "layout": {
    "cardRadiusPx1080": 36,
    "statRadiusPx1080": 31,
    "shortsFramePaddingPx1080x1920": 72,
    "shortsScreenshotRotationDeg": [1, 3]
  }
}
```

`brands/contentporary/palettes/red.json` (long-form reference, measured — spec Appendix A):

```json
{
  "name": "red",
  "use": "Long-form default. Measured from the AE reference video HrYMfy6MZtA.",
  "ground": { "deep": "#070707", "centre": "#252525", "grid": "#1F1F1F", "dots": "#2A2A2A" },
  "surface": { "fill": "#1C1B1B", "fillAlt": "#343233", "bevel": "#9A9A9A", "halo": "rgba(255,255,255,0.06)" },
  "text": { "primary": "#F4F4F4", "secondary": "#ACACAC" },
  "accent": { "block": "#F26666", "text": "#D74B50", "glow": "#F96E71", "line": "#EA9EA4" },
  "accentScript": "#D74B50",
  "status": { "ok": "#5C9064", "x": "#975154" },
  "extras": { "glowHalo": "#431D1D", "lineGlow": "#622F31", "roadmapCard": "#341010", "connector": "#777777" }
}
```

`brands/contentporary/palettes/gold.json` (from the template stills — provisional until sampled from source files):

```json
{
  "name": "gold",
  "use": "Warm palette from the template stills (title, step card, side text). Provisional: sampled from stills, re-sample from source files.",
  "ground": { "deep": "#050505", "centre": "#292929", "grid": "#1E1E1E", "dots": "#262626" },
  "surface": { "fill": "#110E0D", "fillAlt": "#2A2623", "bevel": "#A89A88", "halo": "rgba(255,235,210,0.08)" },
  "text": { "primary": "#F2F2F2", "secondary": "#B5ADA4" },
  "accent": { "block": "#FBB560", "text": "#F9D09F", "glow": "#FDCC91", "line": "#FBB560" },
  "accentScript": "#F4F4F4",
  "status": { "ok": "#8FA36A", "x": "#A0605A" },
  "extras": { "ambientGlow": "#542C10" },
  "provisional": ["status", "surface.fillAlt", "surface.bevel", "text.secondary"]
}
```

`brands/contentporary/palettes/lime.json`:

```json
{
  "name": "lime",
  "use": "Lime accent palette from the custom mini animation still. Provisional: sampled from a still.",
  "ground": { "deep": "#070707", "centre": "#252525", "grid": "#1F1F1F", "dots": "#2A2A2A" },
  "surface": { "fill": "#1C1B1B", "fillAlt": "#343233", "bevel": "#9A9A9A", "halo": "rgba(255,255,255,0.06)" },
  "text": { "primary": "#F4F4F4", "secondary": "#ACACAC" },
  "accent": { "block": "#D5FF74", "text": "#DCFD81", "glow": "#DCFD81", "line": "#D5FF74" },
  "accentScript": "#DCFD81",
  "status": { "ok": "#5C9064", "x": "#975154" },
  "extras": { "onBlockText": "#3E5A12" },
  "provisional": ["extras.onBlockText"]
}
```

`brands/contentporary/palettes/reel-dark.json` (Shorts reels, dark-mode screenshots — design-system §3–4):

```json
{
  "name": "reel-dark",
  "use": "Shorts, when the screenshot being annotated is dark-mode. Measured from the two reference reels.",
  "ground": { "deep": "#0C0C0C", "centre": "#161616", "grid": "#1A1A1A", "dots": "#1A1A1A" },
  "surface": { "fill": "#404040", "fillAlt": "#404040", "bevel": "#404040", "halo": "rgba(0,0,0,0)" },
  "text": { "primary": "#FBFBFB", "secondary": "#A8A9AB" },
  "accent": { "block": "#EE4B4A", "text": "#EE4B4A", "glow": "#EE4B4A", "line": "#EE4B4A" },
  "accentScript": "#F0504F",
  "status": { "ok": "#A6FF69", "x": "#EE4B4A" },
  "extras": { "title": "#F9F9F9", "ghostNumeral": "#192012", "emphasisGreen": "#A6FF69", "stateBlue": "#4285F4" }
}
```

`brands/contentporary/palettes/reel-light.json`:

```json
{
  "name": "reel-light",
  "use": "Shorts, when the screenshot being annotated is light-mode. Measured from the two reference reels.",
  "ground": { "deep": "#E5E5E5", "centre": "#ECECEC", "grid": "#E0E0E0", "dots": "#E0E0E0" },
  "surface": { "fill": "#F2F2F2", "fillAlt": "#F2F2F2", "bevel": "#F2F2F2", "halo": "rgba(0,0,0,0.08)" },
  "text": { "primary": "#464646", "secondary": "#6B6B6B" },
  "accent": { "block": "#EE4B4A", "text": "#EE4B4A", "glow": "#EE4B4A", "line": "#EE4B4A" },
  "accentScript": "#F0504F",
  "status": { "ok": "#57A22F", "x": "#EE4B4A" },
  "extras": { "emphasisGreen": "#57A22F", "stateBlue": "#4285F4" },
  "provisional": ["text.secondary", "ground.grid", "ground.dots"]
}
```

- [ ] **Step 4: Create `brand.md` and `assets/MANIFEST.md`**

`brands/contentporary/brand.md`:

```markdown
# Contentporary — Brand

**Status:** approved. Precedence: `standards/core` → `standards/formats/<format>` → this brand →
the video BRIEF. This file supplies values and look, never motion technique.

## Constant visual language
Every Contentporary video keeps these, whatever palette or headline font it picks:
- **Ground:** dark, never flat. A lit centre falling off to near-black corners (vignette edge ≈ 50 %
  of centre brightness), a faint grid (≈ 4 columns per frame) with a dot matrix, and a soft light
  sweep. Shorts may use the light ground (`reel-light`) when the screenshot is light-mode.
- **Surfaces:** dark glass cards with a bevelled 1–2 px light border and a faint light halo.
  Never a dark drop shadow (long-form). Card radius ≈ 36 px, stat cards ≈ 31 px at 1080p;
  highlight blocks are sharp-cornered.
- **Headlines:** white, with a soft glow (halo 60–90 px at 1080p) on dark ground; one or two accent
  words in the palette's `accent.text`.
- **Accent words:** a sharp-cornered `accent.block` behind a key stat or phrase, or a payoff word in
  the signature script (`accentScript`), negative in the accent colour, positive in `status.ok`.
- **Marks:** highlight block, scribble underline, underline, curved arrow, curved/elbow connectors
  that draw, ✕/✓ status chips, script payoff word, strike-through. Shorts also use the reel set:
  ring, group outline, tinted tool chips.
- **Proof assets:** real screenshots or faithful recreations of real platforms (the dark YouTube
  watch page is the house proof asset). In-screenshot UI is never restyled.

## Palettes (one per video, chosen in the BRIEF)
- `red` — long-form default; measured from the AE reference video.
- `gold` — warm amber; from the template stills (title, step card, side text).
- `lime` — lime accent; from the custom mini-animation still. A one-off lime script accent may also
  be added to `red` via a BRIEF override (`accentScript: "#BACE7A"`), as the reference video did.
- `reel-dark` / `reel-light` — Shorts; ground chosen by the screenshot's own UI mode.
A video may override individual palette roles in its BRIEF for a one-off accent. The constant
visual language above must still hold.

## Fonts (headline chosen per video in the BRIEF)
- `helvetica` — Helvetica Now Display Bold (reference video, Shorts reels).
- `geometric` — Satoshi Bold (template stills, video 09).
- Body: SF Pro Display Medium (Inter 500 off Apple machines). Script: monoline signature script
  (Brittany Signature). Shorts burned-in captions, when a Short has them: Garet Heavy.

## Kit variants
`glow-center` title · `glass-pill-script` subtitle ("Step 1" in script over a glowing title in a
glass pill) · `key-line` lower third (one key line, bottom-centre, white→warm gradient) ·
`grid-panel-chips` side text (left-half grid panel, glass number chips, face on the right) ·
`watch-page-dive` CTA · `wave-nodes` chapter roadmap (glowing wavy line, numbered nodes, icon cards).

## Never
- Flat fills, pure-white grounds in long-form, dark drop shadows under cards (long-form).
- More than one script word per line. Accent colours outside the chosen palette and BRIEF overrides.
- Light leaks.
```

`brands/contentporary/assets/MANIFEST.md`:

```markdown
# Assets — Contentporary

| Asset | File (shared drive path) | Source | Licence / approval | Captured on |
|---|---|---|---|---|
| Headline font — helvetica | Fonts/HelveticaNowDisplay | Monotype | commercial; team licence to confirm | 2026-09 |
| Headline font — geometric | Fonts/Satoshi | Fontshare | free commercial | — |
| Body font | system (SF Pro) / Fonts/Inter | Apple / Google Fonts | Apple-only / OFL | — |
| Script font | Fonts/BrittanySignature | identified from reference video | to confirm | — |
| Captions font (Shorts) | Fonts/GaretHeavy | — | to confirm | 2026-09 |

## Reference material (provenance of measured values)
- Long-form: "How to build ULTRA predictable Youtube Sales Funnel for B2B High-Ticket Offer",
  youtube.com/watch?v=HrYMfy6MZtA (AE, by Tymek's editor). Values: `palettes/red.json`,
  `standards/formats/long-form.md`.
- Shorts: `tymek.bielinski_DXPO0upgpDE.mp4` (Reel A), `tymek ad v3.mp4` (Reel B). Values:
  `palettes/reel-dark.json`, `palettes/reel-light.json`, `standards/formats/shorts.md`.
- Template stills (title, step card, lower third, side text, mini animations), shared 2026-10-03.
  Values: `palettes/gold.json`, `palettes/lime.json` (provisional).

## Still to obtain
- Logo file.
- Source files for the gold and lime stills, to replace the provisional values.
- Confirmed licences for Helvetica Now Display, Brittany Signature, Garet Heavy.
```

- [ ] **Step 5: Move and edit `narrative.md`**

```bash
git mv context/narrative.md brands/contentporary/narrative.md
```

Then in `brands/contentporary/narrative.md` replace lines 3–4:

```
Source of truth for tone and structure: the root `CLAUDE.md` (Content Types, Key Principles).
This file translates those rules into beat-level guidance for HyperFrames animation.
```

with:

```
Contentporary's own content rules for its channel: tone, beat structure and CTA treatment. Graphic
density and motion live in `standards/formats/`; this file only says what the story is.

- **CTA destination:** https://contentporary.io/ ("book some time below").
- **Offer:** done-for-you YouTube for B2B high-ticket businesses.
- **North-star metric:** qualified call volume.
```

and replace the line `4. **CTA #1** — placed right after the first body point, written verbatim per the script.` with:

```
4. **CTA #1** — placed right after the first body point, verbatim per the script. Long-form uses the
   `cta-youtube` kit template; every CTA in a video uses the identical treatment.
```

and delete the whole `## Pacing` section (its first bullet conflicts with the long-form ≤30 s body
cadence; pacing now lives in `standards/formats/`).

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python3 -m unittest discover -s tools -p 'test_*.py' -v`
Expected: all PASS. Also run `python3 tools/brandcheck.py brands/contentporary` → `OK contentporary (approved)`.

- [ ] **Step 7: Commit**

```bash
git add brands/contentporary tools/test_standards_layout.py
git commit -m "feat(brands): add Contentporary brand (5 palettes, 2 headline fonts)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Core motion law (`standards/core/motion.md`)

**Files:**
- Create: `standards/core/motion.md`
- Test: `tools/test_standards_layout.py` (extend)

**Interfaces:**
- Consumes: nothing.
- Produces: the named easing vocabulary (`ease.camera`, `ease.enter`, `ease.sweep`, `ease.cut`) and blur reason tags (`focus`, `glow`, `wipe`) that Plans 2–3 implement and lint against. Blur reason attribute: `data-blur-reason`.

- [ ] **Step 1: Extend the test (failing)**

Append to `tools/test_standards_layout.py`:

```python
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `python3 -m unittest discover -s tools -p 'test_standards_layout.py' -v`
Expected: FAIL — `FileNotFoundError` for `standards/core/motion.md`.

- [ ] **Step 3: Create `standards/core/motion.md`**

```markdown
# Core Motion Law

**Applies to every brand and every format.** Precedence: this file → `standards/formats/<format>.md`
→ `brands/<brand>/` → the video BRIEF. A lower layer supplies values (timings, colours, fonts) and
never overrides a rule here. Replaces `context/motion-craft.md` and the brand-agnostic half of
`context/design-system.md`.

## The law

1. **Seek-safe or it doesn't ship.** One paused master timeline; helpers add tweens at explicit
   times. No `Math.random()` / `Date.now()` (seed anything pseudo-random). No `repeat: -1`. Animate
   `transform`, `opacity` and `filter` only — never `width`/`height`/`top`/`left`; for "container
   grows", animate `scaleY` on a wrapper or tween between pre-measured transforms. Technique
   reference: `standards/reference/motion-waapi.md`.
2. **Move → hold → move.** Elements and the camera travel, settle, then rest. During a hold the
   camera may creep at most 0.5 %/s. There is no "bed never stops" rule and no mandatory idle
   animation: stillness is used deliberately as contrast.
3. **No overshoot by default.** No bounce, elastic or `back.out` unless the format profile names the
   exact exception.
4. **Named easing vocabulary.** Every tween uses one of these names, whose values the format profile
   sets. No ad-hoc curves in compositions.
   - `ease.camera` — camera legs, pans, pushes, pulls.
   - `ease.enter` — element entrances (words, cards, chips, counters).
   - `ease.sweep` — highlight blocks, underlines, connectors drawing.
   - `ease.cut` — transitions between scenes inside a graphic (whips, wipes).
   A profile may add named extras (e.g. `ease.camera.slow`).
5. **Blur law.**
   - Blur that represents **movement** — camera legs, whips, fast element travel, odometer digit
     roll — uses `HFMotionBlur` (`lib/motion-blur.js`): directional, along the per-pixel velocity,
     with the shutter set by the format profile.
   - Gaussian blur (`feGaussianBlur`, CSS `blur()`) is allowed only for non-motion purposes, and
     every use carries `data-blur-reason` with one of:
     - `focus` — focus/defocus: backdrop rack-defocus behind a title, words sharpening as they
       enter, depth-of-field on a thumbnail inside a card.
     - `glow` — glow and bloom.
     - `wipe` — the Shorts masked wipe feather (Shorts only; see `standards/formats/shorts.md`).
   - A Gaussian standing in for a camera move is never acceptable.
6. **Graphics sync to speech.** An element lands on its spoken word, up to 0.3 s early. Cards and
   nodes lead their phrase by 0.3–0.5 s. Cuts land on the key word ±0.1 s. On-screen text may
   paraphrase speech instead of quoting it.
7. **Footage ↔ full-frame graphic is a hard cut.** Transitions happen inside graphics, as camera
   travel through one world. Over-footage layouts (lower third, side screen text, mini animations)
   animate on and off over the footage. The long-form CTA template is the other exception: it
   transforms the footage itself (scale into a player and back).
8. **Settle, then hold.** A full-frame graphic is still for its last 0.3–1 s before it cuts out.
9. **Credibility.** UI is a real screenshot or a faithful recreation of a real platform. Diagrams,
   data and illustration are free. Invented UI posing as real is not allowed. Exceptions are
   declared in the BRIEF (`exceptions:`) with a reason.
10. **Two-pass build.** Lay the artifact out first; then annotate it in a visibly different register
    (marks). Pass 2 may reinterpret pass 1 — recolouring existing elements is stronger than
    rebuilding. Which marks and which colours come from the brand.

## Craft notes (apply everywhere)
- Odometers: each digit column rolls vertically with its own motion blur, and digits lock
  right-to-left, leading digit last.
- Budget one real-product micro-detail per UI scene (e.g. a favicon swapping in as the typed text
  becomes a recognisable name).
- A state change across a whole set (recolour) is one global swap, not a stagger.
- Peer sets and chained beats are different rhythms; the format profile gives both values.

## Not in this file (by design)
Timings, colours, fonts, text-reveal mode (per character or per word), graphics density, caption
policy. Those live in `standards/formats/` and `brands/`.
```

- [ ] **Step 4: Run to verify it passes**

Run: `python3 -m unittest discover -s tools -p 'test_standards_layout.py' -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add standards/core/motion.md tools/test_standards_layout.py
git commit -m "docs(standards): add core motion law

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Format profiles (`standards/formats/long-form.md`, `shorts.md`)

**Files:**
- Create: `standards/formats/long-form.md`, `standards/formats/shorts.md`
- Test: `tools/test_standards_layout.py` (extend)

**Interfaces:**
- Consumes: the vocabulary from Task 4.
- Produces: per-format values for `ease.*`, density thresholds (Plan 3 `cadence-scan` reads these numbers: hook ≥ 60 %, hook face gap ≤ 6 s, body gap ≤ 30 s, Shorts ≈ 45 %) and caption policy (Plan 3 QA check 7).

- [ ] **Step 1: Extend the test (failing)**

Append to `tools/test_standards_layout.py`:

```python
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `python3 -m unittest discover -s tools -p 'test_standards_layout.py' -v`
Expected: FAIL — missing `standards/formats/long-form.md`.

- [ ] **Step 3: Create `standards/formats/long-form.md`**

```markdown
# Format Profile — Long-form

Applies to long-form videos (16:9, 1920×1080, 30 fps) for every brand. Inherits
`standards/core/motion.md`; supplies the long-form values. Source: frame-by-frame measurement of
Tymek's editor's After Effects video (youtube.com/watch?v=HrYMfy6MZtA) plus Tymek's corrections —
full numbers in the spec, Appendix A.

The quality bar is **smoothness**. Scenes may run long and need not be very dynamic.

## Placement modes
1. **Full-frame scenes** — the edit hard-cuts from the face to the graphic and back.
2. **Over-footage layouts** — lower third, side screen text, mini animations — animate on and off
   over the face.

## Graphic catalogue

| Kind | Types | Built with |
|---|---|---|
| Templated kit | full-screen title · subtitle / step card · lower third (key lines only) · side screen text (1–6 points) | `lib/kit` (Plan 4); new variants per video allowed |
| Recurring devices | chapter roadmap · CTA template | `lib/kit` |
| Custom | screenshot-focus · diagram/flow · comparison split · proof clip · counter/odometer · mini animations | `camera` / `marks` / `text` primitives + brand |
| Screen recording | full-frame framed card on plain ground | graphics on top **only on request** |

- **Screenshot-focus:** a real (or faithfully recreated) UI card, sharp, on a blurred and dimmed
  backdrop of related UI; a one-line headline beneath; marks on top. The highlight block is usually
  the first beat after the card lands.
- **Chapter roadmap:** introduced once (the system name above a glowing path with numbered nodes);
  at each chapter the edit cuts back to it, the next step card docks onto its node, and the camera
  continues from its last pose.
- **CTA template:** the face scales to 0.80 into a YouTube watch-page player (≈ 0.5 s) → camera
  dives ≈ 2× to the description link → holds ≈ 1.7 s → reverses to the face. Every CTA in the video
  is identical; one may extend into website → booking page → glow title.
- **Proof clip:** client footage in a rounded card; the client's key words appear word by word,
  positive words in `status.ok`; a big figure lands at the end.

## Density
- **Hook (≈ first 80 s):** ≥ 60 % graphics (reference: 71 %), and no face-only gap > 6 s.
- **Body:** at least one graphic, even a short one, every ≤ 30 s. Ranges declared as
  screen-share in the BRIEF are exempt.
- Scenes run 2–18 s (median ≈ 6 s). Long scenes are chains of 3–5 beats joined by camera travel,
  not one static layout.
- **Shared canvas:** a long argument is one composition the face cuts into (2–6 s cut-ins). On
  return, the canvas is where it would have been had it kept running.

## Motion values

| Token | Value |
|---|---|
| `ease.camera` | `cubic-bezier(0.32, 0, 0.18, 1)` — short ease-in, peak velocity ≈ 28 % into the move, long settle |
| `ease.camera.slow` | `sine.inOut` — emphasis pushes only, avg 3–4.5 %/s over 2–5 s |
| `ease.enter` | `power3.out` |
| `ease.sweep` | `cubic-bezier(0.47, 0.15, 0.2, 0.95)`, ≈ 360 px/s at 720p (0.5 s short, 1.0 s long, thin seed for the first ≈ 4 frames) |
| `ease.cut` | whip: `ease.camera` over 0.45–0.8 s |
| camera leg | 1.1–2.5 s; peak 0.75–1.2 frame-widths/s; drifts 3.5–4.5 s, peak 0.1–0.3 fw/s |
| zoom | push/pull avg 5–16 %/s (peak 18–64 %/s) over 1.6–4 s |
| hold | 0.2–4 s; creep ≤ 0.5 %/s |
| word entrance | rise ≈ 7 % of frame height + fade + blur→sharp (`focus`), 0.6 s `ease.enter`, stagger 230–330 ms; word by word, never per character |
| glow title | pops to ≈ 70 % brightness, settles 0.4 s `expo.out`, no scale; halo 60–90 px at 1080p; next word +430 ms; background rack-defocuses behind it |
| card entrance | rise 35–40 px at 720p, 0.43 s, brightens and sharpens |
| chain gap | 450–500 ms between linked beats; peer sets (e.g. three ✕ chips) land together |
| odometer | `ease.enter`, 2.2–7 s, lands on the spoken number |
| motion blur | ordinary legs ≈ none (shutter ≤ 90°); whips ≈ 180° directional `HFMotionBlur` |
| backdrop defocus | blur σ ≈ 4.5 px at 1080p + brightness → 0.6 over 0.5 s, front-loaded (`focus`) |
| screenshots | axis-aligned in bordered cards; light halo; no dark drop shadow |

**Not used in long-form:** light leaks, masked wipes, dissolves/crossfades, overshoot.

## Captions
None. Spoken words appear on screen only as a **lower third for key lines** (`kit.lower-third`).
Proof-clip words are the client's quote, not captions.

## Delivery
- **Full-frame scenes:** silent MP4 clips (1920×1080, 30 fps) named by timeline timecode, plus
  `TIMECODES.csv` and a README for the editor.
- **Over-footage layouts:** ProRes 4444 with alpha (`npx hyperframes render --format=mov`).
- Hand-off to the shared drive; media never goes into Git.

## Checklist (run with `standards/core/qa.md`)
- [ ] Hook ≥ 60 % graphics, no face gap > 6 s; body gaps ≤ 30 s (screen-share exempt)
- [ ] Every motion uses a named `ease.*` token; no overshoot
- [ ] Camera moves → holds → moves; each full-frame scene is still for its last 0.3–1 s
- [ ] Words land on their spoken word; cards lead their phrase by 0.3–0.5 s
- [ ] No captions except key-line lower thirds
- [ ] All CTAs use the identical `cta-youtube` treatment
- [ ] Colours and fonts come from the brand palette/font chosen in the BRIEF (plus declared overrides)
```

- [ ] **Step 4: Build `standards/formats/shorts.md` from design-system.md**

Write the header, then append the measured sections verbatim:

```bash
mkdir -p standards/formats
cat > standards/formats/shorts.md <<'EOF'
# Format Profile — Shorts

Applies to Shorts (9:16, 1080×1920, 30 fps) for every brand. Inherits `standards/core/motion.md`;
supplies the Shorts values. Measured frame-by-frame from Tymek's two reference reels
(`tymek.bielinski_DXPO0upgpDE.mp4` = Reel A, `tymek ad v3.mp4` = Reel B). Colours and fonts are
not in this file: Contentporary's reel values live in `brands/contentporary/palettes/reel-dark.json`
and `reel-light.json`.

**Easing values:** `ease.cut` = the wipe below, `cubic-bezier(0.65, 0, 0.35, 1)`; `ease.camera` =
`cubic-bezier(0.65, 0, 0.35, 1)` (house bezier, solved by bisection); `ease.enter` = per beat sheet
below (chips seed-and-expand; headline type scales down from oversize).
**Presentation:** screenshots are composited slightly rotated (~1–3°) with a soft drop shadow.

EOF
sed -n '15,84p' context/design-system.md  >> standards/formats/shorts.md
echo >> standards/formats/shorts.md
sed -n '181,324p' context/design-system.md >> standards/formats/shorts.md
echo >> standards/formats/shorts.md
sed -n '342,365p' context/design-system.md >> standards/formats/shorts.md
```

Then make these exact edits in `standards/formats/shorts.md`:

1. Replace the paragraph starting `Corollary — **the graphic scene REPLACES the captions too.**`
   (four lines, ending `...removes the subtitle layer for that share of the runtime.`) with:

   ```
   **Captions are a per-project flag** (`captions:` in the BRIEF). If the source footage already
   carries burned-in captions, never re-add them. Either way, no caption appears over a full-frame
   graphic scene: the subtitle layer belongs to the talking head only.
   ```

2. Replace `by a directional `feGaussianBlur`, and the reveal is a` with
   `by a directional `feGaussianBlur` (the named Gaussian exception — tag it `data-blur-reason="wipe"`), and the reveal is a`.

3. Replace `1. **`cp lib/motion-blur.js videos/<slug>/public/lib/`** and load it after GSAP.` with
   `1. **Sync the shared library into the project** (`tools/sync-lib`; never hand-copy or edit the copy) and load `lib/motion-blur.js` after GSAP.`

4. Replace the step-3 block from `3. **The texture must carry the canvas aspect ratio.**` through the
   closing ``` of the `pose(t)` code block with:

   ````
   3. **The texture must carry the canvas aspect ratio.** The shader maps it onto world rect
      `[0,uRes.x] × [0,uRes.y]`, so a texture of any other aspect is silently stretched. For a
      canvas of W × H, pick a blow-up factor `K`, size the texture `W·K × H·K`, place the stage
      origin at `PAD_X = (W/2)(K-1)`, `PAD_Y = (H/2)(K-1)`, and scale the pose by `K`:

      ```js
      function pose(t) {                       // stage point (W/2, cy) -> canvas centre at zoom Z
        var Z = zOf(t), cy = cyOf(t);
        return { tx: W / 2 - Z * (W / 2 + PAD_X), ty: H / 2 - Z * (cy + PAD_Y), s: Z * K };
      }
      ```
   ````

5. Under `### The one place the library does not apply`, directly after the line
   `a licence to approximate a camera move.`, add a blank line and this paragraph:

   ```
   In Shorts this smear is filed under the same named exception as the wipe: tag it
   `data-blur-reason="wipe"`. It does not exist in long-form.
   ```

6. Append the Shorts checklist at the end of the file:

   ```markdown

   ## Density and delivery
   - ≈ 45 % of runtime is full-frame graphics; scenes 1.4–8.8 s; full-frame only, no overlays on the face.
   - Delivery: one finished MP4 (1080×1920, 30 fps).

   ## Checklist (run with `standards/core/qa.md`)
   - [ ] Full-frame scene the edit cuts to, not an overlay; scene ends land on the footage's own cuts
   - [ ] Built on a real screenshot (or faithful recreation), rotated 1–3° with a soft shadow
   - [ ] Ground matches the screenshot's UI mode (`reel-dark` / `reel-light` or the brand's equivalent)
   - [ ] Pass 1 builds plainly; pass 2 annotates with the brand's marks
   - [ ] Peer sets ~125 ms apart; chained beats 300–630 ms with visible dead air; set recolour = one 133 ms swap
   - [ ] Type-on ~67 ms/char; word-by-word ~200 ms/word
   - [ ] Camera travels across document-shaped screenshots (7–16 %/s) and holds while a discrete set builds
   - [ ] Captions match the BRIEF flag and never sit over a graphic scene
   ```

- [ ] **Step 5: Run to verify it passes**

Run: `python3 -m unittest discover -s tools -p 'test_standards_layout.py' -v`
Expected: PASS. Then read `standards/formats/shorts.md` top to bottom once: section numbers jump
(§1, §6, §7, §8, §8b, §8c, §9b) because they keep design-system.md's numbering. That's intended,
since other projects cite those numbers.

- [ ] **Step 6: Commit**

```bash
git add standards/formats tools/test_standards_layout.py
git commit -m "docs(standards): add long-form and Shorts format profiles

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: QA and pipeline docs (`standards/core/qa.md`, `pipeline.md`)

**Files:**
- Create: `standards/core/qa.md`, `standards/core/pipeline.md`
- Test: `tools/test_standards_layout.py` (extend)

**Interfaces:**
- Consumes: Tasks 1, 4, 5.
- Produces: the numbered checks 1–10 (Plan 3's `tools/qa` implements exactly these numbers and names) and the BRIEF field list (Plan 3's `tools/new-video` template uses exactly these keys: `format`, `brand`, `palette`, `font`, `overrides`, `captions`, `screen_share`, `exceptions`, `source`).

- [ ] **Step 1: Extend the test (failing)**

Append to `tools/test_standards_layout.py`:

```python
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
                    "screen_share:", "exceptions:", "source:"]:
            self.assertIn(key, t)
        for s in ["Long-form", "Shorts", "client-ops", "shared drive"]:
            self.assertIn(s, t)
```

- [ ] **Step 2: Run to verify it fails**

Run: `python3 -m unittest discover -s tools -p 'test_standards_layout.py' -v`
Expected: FAIL — missing `standards/core/qa.md`.

- [ ] **Step 3: Create `standards/core/qa.md`**

```markdown
# QA Gate

Two stages: an automated gate that blocks the render, then a human sign-off before delivery.
Automated checks are implemented by `tools/qa` (Plan 3). Until it exists, run each check by hand.

## 1. Automated gate (blocks render)

| # | Check | Method |
|---|---|---|
| 1 | HyperFrames validity | `npx hyperframes check` |
| 2 | No lib fork | the project's `lib.lock` hashes equal root `lib/` |
| 3 | BRIEF complete | `format`, `brand` (status `approved`), `palette`, `font`, `captions` (Shorts) present; `python3 tools/brandcheck.py` passes and the palette/font/overrides choice is valid (`brandcheck.validate_choice`) |
| 4 | Seek-safety | static scan: no `Math.random`, `Date.now`, `repeat: -1`, CSS `infinite` animations |
| 5 | Blur law | every `feGaussianBlur` / `blur()` carries `data-blur-reason` = `focus`, `glow` or `wipe` (`wipe` only in Shorts); camera and whip blur only via `HFMotionBlur` |
| 6 | Easing vocabulary | no raw curves outside the named `ease.*` tokens |
| 7 | Captions | long-form: no caption layer except `kit.lower-third`; Shorts: matches the `captions` flag |
| 8 | Density | long-form: hook ≥ 60 % graphics, no face gap > 6 s, body gaps ≤ 30 s (BRIEF `screen_share` ranges exempt); Shorts ≈ 45 % |
| 9 | Settle before cut | the last 0.3 s of each full-frame scene is still (frame difference) |
| 10 | Render traps | text verified in rendered frames, not only snapshots (`standards/formats/shorts.md` §9b traps apply to every format); seek-flicker scan |

**Exceptions:** declared in the BRIEF under `exceptions:`, each with a reason (e.g. a recreated UI
that has no real screenshot). The gate passes declared exceptions and lists them in the preview pack.

## 2. Human review

1. **Preview pack** (generated): a contact sheet of every graphic, a draft render of the hook plus
   one body scene, the density timeline, and the exceptions list.
2. **Sign-off by whoever ran the build**, using these five questions. Tymek sees the final. Each
   question must be answerable by someone other than Tymek:
   1. **Smooth?** Moves ease in and settle; nothing snaps, jitters or overshoots; scenes hold still
      before they cut.
   2. **On-brand?** Ground, surfaces, headline treatment and marks match `brands/<brand>/brand.md`;
      colours come from the chosen palette.
   3. **Readable?** Every word on screen can be read at normal speed; nothing is cropped, ghosted or
      too small at phone size.
   4. **Synced?** Each graphic lands on the words it illustrates (see the transcript times).
   5. **Earns its place?** Each graphic explains, proves or emphasises something; roughly 80 %
      familiar (screenshot + highlight, whiteboard-style marks), 20 % custom brand moments.
3. Final render and delivery. Client videos then go to the client as V1 via `client-ops`.

**Promotion rule:** a review finding that changes how future videos should be made is written into
`standards/` or `brands/<brand>/` in the same session. Never only into a BRIEF or agent memory.
```

- [ ] **Step 4: Create `standards/core/pipeline.md`**

````markdown
# Production Pipeline

Two production models, both built on real talking-head footage. Entry point: the
`contentporary-video` project skill (Plan 5). Until it exists, follow this file directly.

## Project layout (both formats)
```
videos/<slug>/  BRIEF.md · transcript.json · storyboard.md · assets/captures/MANIFEST.md
                compositions/ · lib/ + lib.lock · deliver/
```

## BRIEF fields
```yaml
format: long-form            # long-form | shorts
brand: contentporary         # folder under brands/, must be status: approved
palette: red                 # one of the brand's palettes
font: helvetica              # one of the brand's headline fonts
overrides:                   # optional one-off palette role overrides
  accentScript: "#BACE7A"
captions: false              # Shorts only: true | false
screen_share:                # long-form only: ranges exempt from the 30 s cadence rule
  - [302.5, 317.0]
exceptions:                  # optional, each with a reason
  - "F09: recreated Google Calendar — no shareable real account"
source: "shared drive path to the basic-edit export / footage"
```

## Long-form
1. **Intake.** `tools/new-video` (Plan 3) scaffolds `videos/<slug>/` and syncs `lib/`. Inputs: the
   basic-edit export (a proxy is fine) and its transcript (`npx hyperframes transcribe`).
2. **Storyboard.** Map graphics to transcript timecodes: kit / device / custom, and placement mode
   (full-frame or over-footage). Check density on the plan before building (hook ≥ 60 %, body gaps
   ≤ 30 s). The runner approves the storyboard.
3. **Capture.** Real screenshots or faithful recreations into `assets/captures/`, each recorded in
   `MANIFEST.md` (URL, UI mode, what's visible, caveats).
4. **Build.** Full-frame scenes as one reel (shared canvases where an argument spans face cut-ins);
   over-footage layouts as separate transparent compositions. Use `lib/kit` and the
   `camera` / `marks` / `text` primitives.
5. **Automated gate** (`standards/core/qa.md` §1).
6. **Preview pack → sign-off** by the runner (`standards/core/qa.md` §2).
7. **Render and slice.** Full-frame: silent MP4 clips + `TIMECODES.csv` + README. Over-footage:
   ProRes 4444 with alpha. Into `deliver/`, then the shared drive (media never goes into Git).
8. **Hand-off.** The editor places the clips on the timeline. Client videos: V1 via `client-ops`.
9. **Feedback.** Apply the promotion rule. Commit and push code and docs only.

## Shorts
1. **Intake** as above, with the vertical footage and the `captions` flag.
2. **Storyboard** with `tools/probe-cuts`: scene ends land on the footage's own cuts
   (`standards/formats/shorts.md` §1).
3. **Capture** as above.
4. **Build** one composition over the footage.
5. **Automated gate.**
6. **Preview pack → sign-off.**
7. **Render** one finished MP4; hand off as above.
8. **Feedback** as above.

## Git
Follow the sync rules in `CLAUDE.md`: pull at session start and before pushing; commit and push
only when asked; footage, audio and renders never go into Git.
````

- [ ] **Step 5: Run to verify it passes**

Run: `python3 -m unittest discover -s tools -p 'test_standards_layout.py' -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add standards/core/qa.md standards/core/pipeline.md tools/test_standards_layout.py
git commit -m "docs(standards): add QA gate and production pipeline

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Migrate old docs and slim `CLAUDE.md`

**Files:**
- Move: `context/motion-waapi.md` → `standards/reference/motion-waapi.md`
- Delete: `context/design-system.md`, `context/motion-craft.md`, `context/frame.md`, `context/custom.md`, `context/voice.md`, `PIPELINE.md`, `templates/script-template.md`
- Modify: `CLAUDE.md` (full rewrite)
- Test: `tools/test_standards_layout.py` (extend)

**Interfaces:**
- Consumes: everything above.
- Produces: the final Plan 1 layout. `lib/README.md` still mentions `demo-transitions.js` and old paths; Plan 2 rewrites it, so it's deliberately not in this task's stale-reference scan.

- [ ] **Step 1: Extend the test (failing)**

Append to `tools/test_standards_layout.py`:

```python
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `python3 -m unittest discover -s tools -p 'test_standards_layout.py' -v`
Expected: FAIL — old files still exist.

- [ ] **Step 3: Move and delete**

```bash
mkdir -p standards/reference
git mv context/motion-waapi.md standards/reference/motion-waapi.md
git rm context/design-system.md context/motion-craft.md context/frame.md context/custom.md context/voice.md PIPELINE.md templates/script-template.md
```

In `standards/reference/motion-waapi.md`:
- line 11: replace `` `videos/users-companies/compositions/examples/waapi-demo.html`. `` with
  `a standalone test composition (the original waapi-demo.html was not carried over from the client pipeline).`
- line 50: replace `compositions/examples/waapi-demo.html` with `compositions/<your-test>.html`.

Then check:

```bash
grep -n "context/\|motion-craft\|waapi-demo.html" standards/reference/motion-waapi.md
```

Expected: exactly one line (line 11, the "was not carried over" phrase).

- [ ] **Step 4: Rewrite `CLAUDE.md`**

Replace the whole file with:

```markdown
# Contentporary — HyperFrames animation pipeline

Graphics for YouTube videos built on real talking-head footage — Contentporary's own channel and
every client. Two formats: **Shorts recut** and **long-form scene clips**. Spec:
`docs/superpowers/specs/2026-10-03-animation-workflow-design.md`.

## Stay in sync with the team — pull first

This repo is shared by the Contentporary team on GitHub
(`https://github.com/tymekbielinski/hyperframes-contentporary`, branch `main`).

- **At the start of every session, before reading or editing anything:** run `git status`, then
  `git pull`. Tell the user what came in (new commits, or "already up to date").
- **If the pull is blocked by local changes:** do not discard them. `git stash`, `git pull`,
  `git stash pop`, and report any conflicts to the user instead of resolving them silently.
- **If `origin` still points at the old `hyperframes` URL:** run
  `git remote set-url origin https://github.com/tymekbielinski/hyperframes-contentporary.git`.
- **Before pushing:** pull again so you push on top of teammates' latest work. Commit and push
  only when the user asks.
- **Not in Git:** footage, audio, renders and edit exports (`*.mp4`, `*.mov`, `*.wav`, `*.mp3`,
  `*.xml`, `*.edl`, `*.srt`, … — see `.gitignore`). A pull will not bring these; if a project
  references media that isn't on disk, tell the user to get it from the team's shared drive.

## Rules for any video task

1. Start with the `/hyperframes` skill for HyperFrames mechanics.
2. **Precedence:** `standards/core/` → `standards/formats/<format>.md` → `brands/<brand>/` → the
   video's `BRIEF.md`. A lower layer supplies values and never overrides a rule above it.
3. Read, in order: `standards/core/motion.md` (core motion law), the format profile
   (`standards/formats/long-form.md` or `shorts.md`), the brand (`brands/<brand>/brand.md`,
   `tokens.json`, the chosen palette), then `standards/core/pipeline.md`.
4. **Motion blur is never a Gaussian.** Movement blur uses `lib/motion-blur.js` (`HFMotionBlur`).
   Gaussian blur only with `data-blur-reason` = `focus`, `glow` or `wipe` (Shorts).
5. Long-form never has running captions (key-line lower thirds only). Shorts captions follow the
   BRIEF's `captions` flag.
6. Every video passes `standards/core/qa.md` (automated gate, then sign-off by whoever ran the build).
7. **Promotion rule:** a finding that changes how future videos are made goes into `standards/` or
   `brands/`, never only into a BRIEF or agent memory.
8. New client → `brands/_template/README.md`. Validate any brand with
   `python3 tools/brandcheck.py brands/<name>`.
9. `videos/*` made before 2026-10-03 are frozen references; don't migrate or restyle them.

## Shared library — `lib/`

Shared by every brand and video; styled only by brand tokens. See `lib/README.md`. Never hand-edit
a project's copy; improvements go into root `lib/` first.

## Tests

`python3 -m unittest discover -s tools -p 'test_*.py' -v`
```

- [ ] **Step 5: Run the full suite**

Run: `python3 -m unittest discover -s tools -p 'test_*.py' -v`
Expected: all PASS, including the pre-existing `test_instantly_*` and `test_repo_perfect_cuts_skill` tests.

Then confirm nothing outside the frozen projects still points at removed files:

```bash
grep -rln "context/\|PIPELINE.md\|script-template" --include='*.md' --include='*.json' --include='*.py' . | grep -v "^videos/\|^docs/\|^lib/README.md\|^tools/test_standards_layout.py"
```

Expected: no output. (`lib/README.md` is rewritten in Plan 2; `docs/` holds the spec and plans,
which name old files on purpose; the layout test names them as the strings it forbids.)

- [ ] **Step 6: Commit**

```bash
git add -A standards CLAUDE.md context PIPELINE.md templates tools/test_standards_layout.py
git commit -m "refactor: migrate context/ docs into standards/ and brands/, slim CLAUDE.md

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 7: Report**

Tell Tymek: the branch name, the test count, and the spec clarification from Global Constraints
(element smear filed under `wipe`, Shorts only). Ask whether to push the branch or open a PR.
Don't push without his go-ahead.
