# Plan 1b — Standards Update from Research Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fold two research results into the Plan 1 standards: the custom-animation catalogue from 6 of Tymek's long-form videos (including light ground as an official second look), and the techniques from the "Insane Motion Graphics With Opus 5.5" video (anti-generic ban list, beat grid, director's brief, critique loop, model/effort, reference → style procedure).

**Architecture:** Doc edits to `standards/` and `brands/`, plus one schema addition: every palette declares `"mode": "dark" | "light"`, which `tools/brandcheck.py` validates. The ground look follows the palette chosen in the BRIEF. Tests extend `tools/test_brandcheck.py` and `tools/test_standards_layout.py`.

**Tech Stack:** Markdown, JSON, Python 3 standard library (`unittest`).

**Spec:** `docs/superpowers/specs/2026-10-03-animation-workflow-design.md` (§12 deferred items: the custom-animation catalogue and the Opus 5.5 video are resolved by this plan). Research: `docs/research/2026-10-03-custom-animation-catalogue.md`.

## Global Constraints

- Tymek's decisions (2026-10-03), binding:
  - **Light ground is an official second look**, chosen per video via the palette (`mode: light`).
  - Graphics stay **silent** and speech-synced; the editor owns music and SFX. No beat grid to music, no SFX stems.
  - **Face punch-ins do not count** toward the long-form ≤ 30 s body cadence.
  - Recorded **section formats** (board walkthrough, slide deck with a face PiP) are **out of scope** and treated like screen-share: exempt from cadence, graphics only on request.
- Precedence: core → format profile → brand → BRIEF. Brands supply values, never motion technique.
- `PALETTE_ROLES` in `tools/brandcheck.py` does **not** change (Plan 2's `lib/brand.js` contract test mirrors it). `mode` is a separate required key.
- Python standard library only. Never touch `videos/`.
- Branch `standards-v1`. Stage only the files each task names — never `git add -A` or `git add .` (other sessions may have work in this tree). Commit trailer: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Test command: `python3 -m unittest discover -s tools -p 'test_*.py' -v`. Baseline: `test_instantly_*` show exactly 14 pre-existing ERRORs (missing gitignored media); that count must stay 14; everything else passes.
- New test classes go above the `if __name__ == "__main__":` block.

## Review Focus

1. **A palette without `mode`, or with `mode: "Light"` / `"grey"`.** Expected: `brandcheck` names the file and the bad value (`… mode must be 'dark' or 'light', got 'grey'`). Tested in Task 1.
2. **A light palette whose text has too little contrast against its ground** (e.g. white text left over from a dark palette). Expected: the layout test asserts that the light palettes' `text.primary` is darker than their `ground.centre`. Tested in Task 1.
3. **The client template not declaring a mode**, so new clients fail validation. Expected: `brands/_template/palettes/base.json` has `"mode": "dark"` and validates. Tested in Task 1.
4. **Renumbering `qa.md` (new critique-loop section) leaves stale section references** in `pipeline.md` or elsewhere. Expected: no file says "`qa.md` §2" for sign-off; pipeline references §2 for the critique loop and §3 for human review. Tested in Task 3.
5. **The ban list or catalogue contradicting existing rules** (e.g. banning a dissolve the catalogue then uses). Expected: the catalogue names no dissolve, crossfade, light leak or overshoot as a technique to copy. Tested in Task 2.

---

## File Structure

```
tools/brandcheck.py                      MODIFY  validate palette "mode"
tools/test_brandcheck.py                 MODIFY  mode tests (+ good_palette gains mode)
tools/test_standards_layout.py           MODIFY  light-palette, catalogue, ban-list, QA/pipeline tests
brands/_template/palettes/base.json      MODIFY  + "mode": "dark"
brands/_template/README.md               MODIFY  + reference → style step
brands/contentporary/palettes/*.json     MODIFY  + "mode" on all 5; NEW silver.json, paper.json
brands/contentporary/tokens.json         MODIFY  palettes list += silver, paper
brands/contentporary/brand.md            MODIFY  two ground modes; palettes; Never
standards/core/motion.md                 MODIFY  + "The look — banned generic output"
standards/formats/long-form.md           MODIFY  + custom catalogue; section formats; sound
standards/core/qa.md                     MODIFY  + §2 critique loop (human review → §3)
standards/core/pipeline.md               MODIFY  model/effort, beat grid, director fields, critique step, reference → style
docs/superpowers/specs/2026-10-03-animation-workflow-design.md  MODIFY §12 resolved items
docs/research/2026-10-03-custom-animation-catalogue.md          ADD (already written, untracked)
```

---

### Task 1: Palette `mode` + light palettes + brand ground modes

**Files:**
- Modify: `tools/brandcheck.py`, `tools/test_brandcheck.py`, `tools/test_standards_layout.py`, `brands/_template/palettes/base.json`, `brands/contentporary/palettes/{red,gold,lime,reel-dark,reel-light}.json`, `brands/contentporary/tokens.json`, `brands/contentporary/brand.md`
- Create: `brands/contentporary/palettes/silver.json`, `brands/contentporary/palettes/paper.json`

**Interfaces:**
- Consumes: `brandcheck.validate_palette(data, label)` (Plan 1).
- Produces: `brandcheck.PALETTE_MODES = ("dark", "light")`; every palette JSON has `"mode"`. Plan 2/4 can read `palette["mode"]` to choose the ground treatment.

- [ ] **Step 1: Write the failing tests**

In `tools/test_brandcheck.py`, add `"mode": "dark",` as the second key of the dict returned by `good_palette()` (after `"name": name,`). Then add to `class PaletteTests`:

```python
    def test_mode_required(self):
        p = good_palette()
        del p["mode"]
        self.assertIn("red.json: missing mode", bc.validate_palette(p, "red.json"))

    def test_mode_must_be_dark_or_light(self):
        p = good_palette()
        p["mode"] = "grey"
        self.assertIn("red.json: mode must be 'dark' or 'light', got 'grey'",
                      bc.validate_palette(p, "red.json"))
```

In `tools/test_standards_layout.py`, add above `if __name__`:

```python
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
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m unittest discover -s tools -p 'test_brandcheck.py' -v` → the two new mode tests FAIL.
Run: `python3 -m unittest discover -s tools -p 'test_standards_layout.py' -v` → the `GroundModeTests` FAIL (KeyError `mode`, or `silver` missing).

- [ ] **Step 3: Implement `mode` validation**

In `tools/brandcheck.py`, below `STATUSES = ("draft", "approved")` add:

```python
PALETTE_MODES = ("dark", "light")
```

and at the top of `validate_palette`, after `errors = []`, add:

```python
    if "mode" not in data:
        errors.append(f"{label}: missing mode")
    elif data["mode"] not in PALETTE_MODES:
        errors.append(f"{label}: mode must be 'dark' or 'light', got {data['mode']!r}")
```

- [ ] **Step 4: Add `mode` to existing palettes**

Insert `"mode": "<value>",` as the line directly after `"name": …,` in each file:
- `brands/_template/palettes/base.json` → `"dark"`
- `brands/contentporary/palettes/red.json` → `"dark"`
- `brands/contentporary/palettes/gold.json` → `"dark"`
- `brands/contentporary/palettes/lime.json` → `"dark"`
- `brands/contentporary/palettes/reel-dark.json` → `"dark"`
- `brands/contentporary/palettes/reel-light.json` → `"light"`

- [ ] **Step 5: Create the light palettes**

`brands/contentporary/palettes/silver.json` (Clay.com + Liam Ottley videos):

```json
{
  "name": "silver",
  "mode": "light",
  "use": "Light long-form look: silver radial ground, frosted white glass, dark text without glow, coral/red marks. Sampled from 'The Problem With Clay.com' and the Liam Ottley breakdown (compressed 720p, ±6).",
  "ground": { "deep": "#D2D2D2", "centre": "#F4F4F4", "grid": "#E6E6E6", "dots": "#E6E6E6" },
  "surface": { "fill": "#FAFAFA", "fillAlt": "#EDEDED", "bevel": "#FFFFFF", "halo": "rgba(0,0,0,0.08)" },
  "text": { "primary": "#3A3A3A", "secondary": "#6E6E6E" },
  "accent": { "block": "#F0BCBE", "text": "#E8605F", "glow": "#F78065", "line": "#EB7B7F" },
  "accentScript": "#D17251",
  "status": { "ok": "#C1DB3E", "x": "#E8605F" },
  "extras": { "coralLine": "#F78065", "tagBlock": "#E8626E", "secondLine": "#2FA4C9", "terminal": "#2B2B2B", "terminalBorder": "#643C28" },
  "provisional": ["ground.grid", "ground.dots", "text.secondary", "surface.fillAlt"]
}
```

`brands/contentporary/palettes/paper.json` (Stupidly Simple video):

```json
{
  "name": "paper",
  "mode": "light",
  "use": "Light long-form look: white→grey vertical gradient, dark-brown headline on an orange highlight block, lime stats, red annotations. Sampled from 'The Stupidly Simple YouTube Strategy' (compressed 720p, ±6).",
  "ground": { "deep": "#E0E0E0", "centre": "#FFFFFF", "grid": "#EEEEEE", "dots": "#EEEEEE" },
  "surface": { "fill": "#FFFFFF", "fillAlt": "#F2F2F2", "bevel": "#E6E6E6", "halo": "rgba(0,0,0,0.06)" },
  "text": { "primary": "#482818", "secondary": "#7A5A48" },
  "accent": { "block": "#FFCA89", "text": "#D84848", "glow": "#FFCA89", "line": "#D84848" },
  "accentScript": "#D84848",
  "status": { "ok": "#98C868", "x": "#D84848" },
  "extras": { "statLime": "#A8E878", "darkScene": "#181818", "punchVignette": "#341709" },
  "provisional": ["ground.grid", "ground.dots", "text.secondary", "accentScript", "surface.bevel"]
}
```

In `brands/contentporary/tokens.json`, change the `palettes` list to:

```json
  "palettes": ["red", "gold", "lime", "silver", "paper", "reel-dark", "reel-light"],
```

and update the existing `test_palettes_and_fonts_per_spec` assertion in `tools/test_standards_layout.py` to:

```python
        self.assertEqual(sorted(t["palettes"]),
                         ["gold", "lime", "paper", "red", "reel-dark", "reel-light", "silver"])
```

- [ ] **Step 6: Rewrite the ground in `brand.md`**

In `brands/contentporary/brand.md`, replace the `- **Ground:** …` bullet (3 lines) and the `- **Surfaces:** …` bullet (3 lines) and the `- **Headlines:** …` bullet (3 lines) with:

```markdown
- **Two ground modes, chosen per video by the palette's `mode`** (never flat in either):
  - **Dark ground** (`red`, `gold`, `lime`, `reel-dark`): a lit centre falling off to near-black
    corners (vignette edge ≈ 50 % of centre brightness), a faint grid (≈ 4 columns per frame) with a
    dot matrix, a soft light sweep. Dark glass cards with a bevelled 1–2 px light border and a faint
    light halo — never a dark drop shadow. Headlines white with a soft glow (halo 60–90 px at 1080p).
  - **Light ground** (`silver`, `paper`, `reel-light`): a silver or white radial/vertical gradient
    with a soft vignette (no grid on `paper`). Frosted white glass cards with a hairline border and a
    soft neutral shadow (`surface.halo`). Headlines in `text.primary` (dark), **no glow**; emphasis by
    marker/highlight block, scribble underline, or white text on an `accent.block` / tag block.
  - Card radius ≈ 36 px, stat cards ≈ 31 px at 1080p in both modes; highlight blocks are sharp-cornered.
- **Accent-word count:** one or two accent words in long-form; exactly one accent word per headline
  in Shorts — in the palette's `accent.text`.
```

In the `## Palettes` section, add these two bullets after the `lime` bullet:

```markdown
- `silver` — light: silver radial + frosted white glass, dark text, coral/red marks (Clay.com, Ottley).
- `paper` — light: white→grey gradient, dark-brown headline on an orange highlight block, lime stats
  (Stupidly Simple).
```

In the `## Never` section, replace the line
`- Flat fills, pure-white grounds in long-form, dark drop shadows under cards (long-form).`
with:
`- Flat fills in either mode; dark drop shadows under cards on the dark ground; glow on light-ground headlines.`

- [ ] **Step 7: Run all tests**

Run: `python3 -m unittest discover -s tools -p 'test_*.py' -v`
Expected: all pass except the 14 baseline `test_instantly_*` ERRORs. Also `python3 tools/brandcheck.py brands/contentporary` → `OK contentporary (approved)` and `python3 tools/brandcheck.py brands/_template` → `OK _template (draft)`.

- [ ] **Step 8: Commit**

```bash
git add tools/brandcheck.py tools/test_brandcheck.py tools/test_standards_layout.py brands/_template/palettes/base.json brands/contentporary/palettes brands/contentporary/tokens.json brands/contentporary/brand.md
git commit -m "feat(brands): light ground as second look — palette mode, silver + paper palettes

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Ban list (core) + custom catalogue, section formats and sound (long-form)

**Files:**
- Modify: `standards/core/motion.md`, `standards/formats/long-form.md`, `tools/test_standards_layout.py`
- Add: `docs/research/2026-10-03-custom-animation-catalogue.md` (already on disk, untracked — commit it in this task)

**Interfaces:**
- Consumes: Task 1 palette names (`silver`, `paper`).
- Produces: the catalogue IDs A1–A6, B1–B4, C1–C8, D1–D5 that Plan 4 (kit) and future custom builds cite.

- [ ] **Step 1: Write the failing tests**

Add above `if __name__` in `tools/test_standards_layout.py`:

```python
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
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m unittest discover -s tools -p 'test_standards_layout.py' -v` → `LookAndCatalogueTests` FAIL.

- [ ] **Step 3: Add the ban list to `standards/core/motion.md`**

Insert this section immediately before the line `## Craft notes (apply everywhere)`:

```markdown
## The look — banned generic output

The prompt is a small part of the result; these bans are the rest of the harness. A scene that does
any of these fails review, in every format and for every brand:
- A whole scene that is **centred text on a gradient** or flat colour, with nothing real in it.
- **fade in → hold → fade out** on a flat ground as the only motion.
- **everything at once** — all elements appearing on the same frame, or one uniform stagger applied
  to unrelated elements (use the profile's peer-set and chain-gap rhythms).
- **stock icons**, emoji or clip-art where a real screenshot, real logo or brand icon exists; generic
  illustrations standing in for UI.
- Headlines of **more than two lines**, or paragraphs of on-screen text.
- Default/library eases, bounce, elastic, spins, glitch, 3D flips, push slides, light leaks.
- Glows, gradients or colours that are not in the brand palette chosen in the BRIEF.
- A graphic that restates the speech without adding proof, structure or emphasis.
```

- [ ] **Step 4: Add catalogue, section formats and sound to `standards/formats/long-form.md`**

Insert the following immediately before the line `## Density`:

```markdown
## Custom catalogue

Built per moment from `camera` / `marks` / `text` primitives, in the chosen palette (dark or light
ground). Measured from 6 of Tymek's editor-animated videos plus the reference
(`docs/research/2026-10-03-custom-animation-catalogue.md`). Pick the simplest type that proves the
point: A and B first, C for structure, D when the face should stay on screen.

**A. Proof on real UI**

| ID | Type | Layout and motion | Use for |
|---|---|---|---|
| A1 | Screenshot focus + highlight | sharp card ≈ 55–60 % W on a blurred, faded copy (≈ 35 %) of the same screenshot; enters 0.9 → 1 with blur→sharp over 0.25 s; highlight/marker sweeps 0.3 s after landing; optional key-text recolour; hold 0.6–1 s | a claim or quote that is real |
| A2 | Screenshot camera pass | page at 150–250 % (flat) or tilted 45–60° in 3D; 2–3 camera legs ≈ 2 s with readable stops; marks land at the stops; optional synthetic cursor arriving 0.3 s before its mark; may end dimmed and hand off to B1 | prices, pages, tools, long documents |
| A3 | Counter on screenshot | push-in ≈ 0.8 s; the real number counts with deceleration (odometer, `ease.enter`); underline under its label | growth numbers |
| A4 | Proof clip in framed card | rounded card ≈ 56 % W pushing to ≈ 72 %; the client's own words appear word by word beneath (positive words `status.ok`); big figure lands at the end | client results |
| A5 | Case-study card stack | centred card ≈ 55–62 % W, 1–2 cards peeking behind; ≈ 1 s per card; the front card steps away (3D tilt) to reveal the next; metric chip per card | several results in a row |
| A6 | Channel flash montage | blurred channel pages 0.7–1.3 s each, hard-cut back to back | breadth of proof |

**B. Headline scenes**

| ID | Type | Layout and motion | Use for |
|---|---|---|---|
| B1 | Backdrop headline | a screenshot or clip appears sharp ≈ 1 s, then dims to ≈ 15 % and blurs (0.5 s, `focus`); a 1–2 line headline builds word by word; an underline/marker lands on the emphasis phrase — red/accent = problem, `status.ok` = positive; list variant adds a bullet ≈ every 1.3 s | the house device for a key line |
| B2 | Headline + labelled callouts | headline mid-frame; 3 callouts in a triangle, each a curved arrow then an icon + script label, 0.75–1.2 s apart | a method with named parts |
| B3 | Big stat / counter title | a huge number counts up (≈ 1.2–1.4 s) — ghost word behind it, or over the source clip / a cutout; hand-drawn arrow + script subtitle | the one number to remember |
| B4 | Punch word | a single word full-frame on a vignette | a hard "no" / turn |

**C. Diagram canvases** — usually one persistent canvas the face cuts into; on return it resumes

| ID | Type | Layout and motion | Use for |
|---|---|---|---|
| C1 | Flow strip | A → dashed line (swap glyph or arrow) → B, icons ≈ 12 % W; caption word by word; canvas pans as nodes arrive | substitution, cause → effect |
| C2 | Tree | vertical tree; connectors draw top → bottom; camera glides down 2–3 s or tours column by column | comparison, org, formula |
| C3 | Funnel / bands | 3-band shape builds; camera steps band to band; bullets per band | funnels, tiers |
| C4 | Orbit / flywheel | nodes on a ring around a title; camera visits each node while a dashed segment draws to the next; pull back | loops, systems |
| C5 | Card roster | 3–4 glass or tinted cards ("#n" script labels or coloured tiles); camera pushes into one card, its bullets type one per spoken phrase (≈ 2.5–3 s), then pans to the next | numbered lists, components |
| C6 | Range line / annotated chart | line with two dots, colour shifts from `status.x` to `status.ok` as labels land; charts take a strike-through mark | ranges, before/after |
| C7 | Avatar + escalating ticker | avatar on a vertical line; a chip slides out; the number jumps odometer-style; camera lifts up the line | costs or results climbing |
| C8 | Focus card, dim siblings | one card ≈ 38 % W, neighbours ≈ 20 % opacity + blur (`focus`), ✕/✓ badge | picking one option |

**D. Mini animations over the face** — the face stays visible; animate on and off over the footage

| ID | Type | Layout and motion | Use for |
|---|---|---|---|
| D1 | Tiles flanking the face | glass tiles at ≈ 9–38 % and 62–91 % of frame width (logo or 3D icon + label/stat, ✕/✓), 0.7 s apart | platforms, two numbers |
| D2 | Side screenshot + script + highlight | screenshot on the empty side (≈ 60 % W) with an alpha fade toward the face; script word + words build; `accent.block` wipes behind the key phrase | a claim with its proof |
| D3 | Caption bar | semi-transparent bar fading at its outer edge, `status.ok` or `status.x` tint, upper corner; face punched in to clear it | a positive/negative claim |
| D4 | Tool chip stack | 2–4 stacked glass pills with app logos, one after another; may hand off to the CTA | tools, deliverables |
| D5 | Name lower third | script first name + bold surname + curved arrow, beside the speaker, ≈ 2.7 s | introductions |

Recurring across all types: real screenshots as proof (often over a blurred copy of themselves),
word-by-word text, meaning-coded emphasis colour, a script accent word, hand-drawn marks, camera stops
where marks land. 3D icons and a synthetic cursor are allowed when sourced from a real asset
(record them in `assets/captures/MANIFEST.md`).

## Section formats

Recorded sections — a board walkthrough or a slide deck with the face in a corner picture-in-picture —
are not built in this pipeline. Treat them like screen-share: declare their ranges in the BRIEF under
`screen_share`, they are exempt from the cadence rule, and graphics go on top only on request.

## Sound

Graphics are **silent** and timed to speech. The editor owns music and sound effects; nothing is
scored to a beat grid here.
```

Then in the `## Density` section, replace the bullet that starts `- **Body:** at least one graphic` with:

```markdown
- **Body:** at least one graphic, even a short one, every ≤ 30 s. Ranges declared as
  screen-share in the BRIEF are exempt. Face punch-ins do not count as graphics.
```

and append `- [ ] No face-only stretch > 30 s in the body (punch-ins do not count)` as the last line of the `## Checklist` section.

Note: the catalogue must not name dissolves, crossfades, light leaks, overshoot or bounce (the test enforces this).

- [ ] **Step 5: Run tests**

Run: `python3 -m unittest discover -s tools -p 'test_standards_layout.py' -v` → PASS.

- [ ] **Step 6: Commit**

```bash
git add standards/core/motion.md standards/formats/long-form.md tools/test_standards_layout.py docs/research/2026-10-03-custom-animation-catalogue.md
git commit -m "docs(standards): add custom catalogue, anti-generic ban list, section formats and sound

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Critique loop, beat grid, director's brief, model/effort, reference → style

**Files:**
- Modify: `standards/core/qa.md`, `standards/core/pipeline.md`, `brands/_template/README.md`, `docs/superpowers/specs/2026-10-03-animation-workflow-design.md`, `tools/test_standards_layout.py`

**Interfaces:**
- Consumes: catalogue IDs from Task 2.
- Produces: `qa.md` sections §1 automated gate, **§2 critique loop**, §3 human review; BRIEF keys `film`, `direction`, `references`, `gotchas`; the storyboard beat-grid columns (Plan 3's `tools/new-video` template uses them): `t_in`, `t_out`, `words`, `placement`, `type`, `beats`, `ease`, `marks`; the critique file `videos/<slug>/critique.md`.

- [ ] **Step 1: Write the failing tests**

Add above `if __name__` in `tools/test_standards_layout.py`:

```python
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
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m unittest discover -s tools -p 'test_standards_layout.py' -v` → `HarnessTests` FAIL.

- [ ] **Step 3: Add the critique loop to `standards/core/qa.md`**

Change the intro's first sentence from `Two stages: an automated gate that blocks the render, then a human sign-off before delivery.` to
`Three stages: an automated gate that blocks the render, an agent critique loop, then a human sign-off before delivery.`

Rename the heading `## 2. Human review` to `## 3. Human review`, and insert before it:

```markdown
## 2. Critique loop (agent, before the human sees anything)

The agent that built the video reviews its own render and fixes what scores low. A good result
usually takes several rounds, not one shot.

1. Render the preview material: a contact sheet of every graphic, three full-res frames per graphic
   (entrance, mid, settled), and a 10 fps strip of every camera move.
2. Score **every graphic** 1–10 on six dimensions, each with one sentence of evidence:
   - **Smooth** — eases in and settles, holds before the cut, no snap, jitter or overshoot.
   - **On-brand** — ground mode, surfaces, headline treatment and marks match the brand and palette.
   - **Readable** — every word legible at phone size and normal speed; nothing cropped or ghosted.
   - **Synced** — lands on the words it illustrates (check against `transcript.json` times).
   - **Purposeful** — proves, structures or emphasises something; nothing from the ban list in
     `standards/core/motion.md`.
   - **Craft** — real UI detail, depth (backdrop, halo, focus), a micro-detail; not generic.
3. Fix every graphic scoring **below 8** on any dimension, re-render it, and re-score.
4. Stop when all scores are 8 or higher, or after **3 rounds**. Anything still below 8 is listed at
   the top of the preview pack for the runner.
5. Record every round's scores and fixes in `videos/<slug>/critique.md`.
```

In `## 3. Human review`, change the first list item to:
`1. **Preview pack** (generated): a contact sheet of every graphic, a draft render of the hook plus one body scene, the density timeline, the exceptions list, and the final critique scores (any graphic still below 8 first).`

- [ ] **Step 4: Update `standards/core/pipeline.md`**

(a) After the `## Project layout (both formats)` code block, add:

```markdown
**Model and effort:** build with Claude Opus 5.5 at **high effort**; use max effort for custom
diagram canvases (catalogue group C) and for critique-loop fixes. Always build in HyperFrames: a model
left without a named framework writes its own renderer.
```

and in the layout code block change the first line to
`videos/<slug>/  BRIEF.md · transcript.json · storyboard.md · critique.md · assets/captures/MANIFEST.md`.

(b) In the BRIEF YAML block, add these lines directly after `format: long-form            # long-form | shorts`:

```yaml
film: "One line: what this video's graphics must make the viewer feel or believe."
direction: "One line of art direction, e.g. 'one canvas per argument; proof first, then the number'."
references:                  # optional: reference videos/stills whose grammar to borrow
  - "youtube.com/watch?v=HrYMfy6MZtA — camera travel, backdrop headlines"
gotchas:                     # things to avoid in this video specifically
  - "No lime on this one — the client's competitor uses it"
```

(c) Insert this section after the override-keys sentence (before `## Long-form`):

```markdown
## Beat grid (the storyboard format)

`storyboard.md` is a table, one row per graphic, written from `transcript.json` and approved by the
runner before any code:

| t_in | t_out | words | placement | type | beats | ease | marks |
|---|---|---|---|---|---|---|---|
| 62.2 | 68.0 | "it's a system that prints…" | full-frame | kit roadmap (C-canvas) | line draws 0–1.2 · node 1 docks 1.4 · push to node 2.4 | ease.camera / ease.enter | — |
| 74.1 | 79.4 | "1.2 million views" | full-frame | A1 | card lands 0.0 · highlight 0.3 · headline words 1.0–2.4 · hold | ease.enter / ease.sweep | highlight-block, script-word |

`type` is a kit name or a catalogue ID from `standards/formats/long-form.md`. Density is checked on
this table before building.
```

(d) In `## Long-form`, replace step 2's text with:
`2. **Beat grid.** Write `storyboard.md` (see Beat grid) from the transcript: every graphic with its kit name or catalogue ID, placement, beats, ease tokens and marks. Check density on the table (hook ≥ 60 %, body gaps ≤ 30 s, punch-ins don't count). The runner approves it.`

and replace steps 5–6 with:

```markdown
5. **Automated gate** (`standards/core/qa.md` §1).
6. **Critique loop** (`standards/core/qa.md` §2) — scores and fixes into `critique.md`.
7. **Preview pack → sign-off** by the runner (`standards/core/qa.md` §3).
```

renumbering the following steps to 8 (Render and slice), 9 (Hand-off), 10 (Feedback).

In `## Shorts`, replace `5. **Automated gate.**` and `6. **Preview pack → sign-off.**` with
`5. **Automated gate.**`, `6. **Critique loop.**`, `7. **Preview pack → sign-off.**`, and renumber the
rest to 8 (Render) and 9 (Feedback). Change step 2 to start with `2. **Beat grid** with `tools/probe-cuts`:`.

(e) Insert before `## Git`:

```markdown
## Reference → style guide

To adopt a new look (a client's reference video, a new house variant), turn the reference into
rules before building:
1. Extract a frame every 0.5 s (plus 10 fps strips around every transition and camera move).
2. Write a style guide: palette (sampled hex), type, shot lengths, transition types, camera moves,
   texture/grain, how text enters and exits, recurring layouts.
3. Write the shot list / beat grid for the new video in that style, using real screenshots.
4. Take the grammar of the reference, never its content — no logos, characters, footage or copy.
5. Promote the result into `brands/<brand>/` (values) or `standards/` (technique), per the promotion
   rule. This is how `standards/formats/` and the custom catalogue were built.
```

- [ ] **Step 5: Template README + spec**

In `brands/_template/README.md`, insert a new step after step 2 and renumber the rest (3→4 … 8→9):

```markdown
3. If the client has reference videos or an existing channel look, run the **Reference → style guide**
   procedure in `standards/core/pipeline.md` and map its findings onto the palette roles below.
```

In `docs/superpowers/specs/2026-10-03-animation-workflow-design.md` §12, replace the two bullets
starting `- Custom-animation catalogue and layouts` and `- Opus 5.5 animation video` with:

```markdown
- ~~Custom-animation catalogue~~ — resolved in Plan 1b: catalogue in `standards/formats/long-form.md`
  (research: `docs/research/2026-10-03-custom-animation-catalogue.md`); light ground added as a second
  look (palette `mode`).
- ~~Opus 5.5 animation video~~ — resolved in Plan 1b: ban list (core), beat grid, director's-brief
  BRIEF fields, critique loop (QA §2), model/effort, reference → style procedure. Sound stays out of
  scope (graphics are silent; the editor scores).
```

- [ ] **Step 6: Run all tests**

Run: `python3 -m unittest discover -s tools -p 'test_*.py' -v`
Expected: all pass except the 14 baseline `test_instantly_*` ERRORs. Also run
`grep -rn "qa.md\` §2" standards brands CLAUDE.md` and confirm every hit refers to the critique loop.

- [ ] **Step 7: Commit**

```bash
git add standards/core/qa.md standards/core/pipeline.md brands/_template/README.md docs/superpowers/specs/2026-10-03-animation-workflow-design.md tools/test_standards_layout.py
git commit -m "docs(standards): add critique loop, beat grid, director's brief, reference-to-style procedure

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```
