"""Scaffold a video project: videos/<slug>/ with BRIEF, beat grid, critique log, captures manifest,
deliver/, an index.html root, the brand stylesheet and a synced, locked lib/.

Layout: standards/core/pipeline.md. Never overwrites an existing project.
Usage:
  python3 tools/new_video.py <slug> --format long-form|shorts [--brand contentporary]
                             [--palette <name>] [--font <key>] [--videos-dir videos]
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

import brandcheck
import sync_lib

ROOT = Path(__file__).resolve().parents[1]
SLUG = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")
SIZES = {"long-form": (1920, 1080), "shorts": (1080, 1920)}
GSAP = "https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"

BRIEF = """# BRIEF — {slug}

Fields: `standards/core/pipeline.md` (BRIEF fields). `python3 tools/qa.py videos/{slug}` (check 3)
fails until every REQUIRED field is filled. Keep the fields inside the yaml block.

```yaml
format: {format}
film: ""                     # REQUIRED — one line: what this video's graphics must make the viewer feel or believe
direction: ""                # REQUIRED — one line of art direction, e.g. "one canvas per argument; proof first, then the number"
references:                  # optional: reference videos/stills whose grammar to borrow
gotchas:                     # optional: things to avoid in this video specifically
brand: {brand}               # REQUIRED — folder under brands/, must be status: approved
palette: {palette}           # REQUIRED — one of the brand's palettes
font: {font}                 # REQUIRED — one of the brand's headline fonts
overrides:                   # optional one-off palette role overrides, flat dot paths, quoted colours: accentScript: "#BACE7A"
{format_fields}exceptions:                  # optional, each "<what>: <reason>"; "check <n>: <reason>" waives QA check n
source: ""                   # shared-drive path to the basic-edit export / footage
```
"""
LONG_FORM_FIELDS = """hook_end: 80                 # end of the hook in seconds
screen_share:                # ranges exempt from the 30 s cadence rule, e.g. - [302.5, 317.0]
"""
SHORTS_FIELDS = """captions: false              # REQUIRED for Shorts — true | false (never re-add captions the footage already carries)
"""

STORYBOARD = """# Storyboard — {slug}

The beat grid (`standards/core/pipeline.md`): one row per graphic, written from `transcript.json`
and approved by the runner before any code. `placement` is `full-frame` or `over-footage`; `type` is a
kit name or a catalogue ID (`standards/formats/long-form.md`). Times are seconds on the edit timeline.
Check density on this table: `python3 tools/cadence_scan.py videos/{slug}`.
Example row: `| 62.2 | 68.0 | "it's a system that prints…" | full-frame | roadmap | line draws 0–1.2 · node 1 docks 1.4 | ease.camera / ease.enter | — |`

| t_in | t_out | words | placement | type | beats | ease | marks |
|---|---|---|---|---|---|---|---|
"""

CRITIQUE = """# Critique — {slug}

Critique loop: `standards/core/qa.md` §2. One section per round; score every graphic 1–10 on each
dimension with one sentence of evidence in `notes`. Fix anything below 8, re-render, re-score; stop at
all ≥ 8 or after 3 rounds. The preview pack reads the last round's table.

## Round 1

| graphic | smooth | on-brand | readable | synced | purposeful | craft | notes |
|---|---|---|---|---|---|---|---|
"""

MANIFEST = """# Captures — {slug}

Every screenshot or recreation in `assets/captures/` gets one row (`standards/core/pipeline.md`, Capture).

| file | source URL | UI mode | what's visible | caveats |
|---|---|---|---|---|
"""

INDEX = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width={w}, height={h}">
    <script src="{gsap}"></script>
{scripts}
    <link rel="stylesheet" href="compositions/brand.css">
    <style>
      html, body {{ margin: 0; width: {w}px; height: {h}px; overflow: hidden; background: var(--hf-ground-deep); }}
      #root {{ position: relative; width: {w}px; height: {h}px; overflow: hidden; }}
      #root > div[data-composition-src] {{ position: absolute; inset: 0; }}
    </style>
  </head>
  <body>
    <!-- {slug} — {placement_note} -->
    <div id="root" data-composition-id="main" data-hf-mode="{mode}" data-start="0" data-duration="5" data-width="{w}" data-height="{h}">
    </div>
    <script>
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
"""
PLACEMENT_NOTE = {
    "long-form": "full-frame scene reel: one slot per full-frame scene, in timeline order "
                 "(data-composition-src, data-start, data-duration). Over-footage layouts are standalone transparent "
                 "documents (no template wrapper) in compositions/overlays/, each rendered with -c ... --format=mov.",
    "shorts": "one composition over the vertical footage; scene ends land on the footage's own cuts "
              "(python3 tools/probe_cuts.py <footage>).",
}


def scaffold(slug, fmt, brand="contentporary", palette=None, font=None, videos_dir=None, root=ROOT) -> Path:
    """Create the project and return its path. Raises ValueError with the reason on bad input."""
    root = Path(root)
    if not SLUG.fullmatch(slug or ""):
        raise ValueError(f"slug {slug!r} must be lowercase letters, digits and dashes (e.g. 10-youtube-funnel)")
    if fmt not in SIZES:
        raise ValueError(f"format must be long-form or shorts, got {fmt!r}")
    project = Path(videos_dir or root / "videos") / slug
    if project.exists():
        raise ValueError(f"{project} already exists — new_video never overwrites a project")
    brand_dir = root / "brands" / brand
    try:
        tokens = brandcheck.load_brand(brand_dir)["tokens"]
    except brandcheck.BrandError as e:
        raise ValueError(str(e))
    palette = palette or tokens.get("defaultPalette")
    font = font or (tokens.get("fonts") or {}).get("defaultHeadline")
    errors = [e for e in brandcheck.validate_choice(brand_dir, palette, font) if "is not approved" not in e]
    errors += brandcheck.validate_brand(brand_dir)
    if errors:
        raise ValueError("; ".join(errors))
    mode = brandcheck.load_brand(brand_dir)["palettes"][palette]["mode"]
    node = shutil.which("node")
    if not node:
        raise ValueError("node is required (it generates compositions/brand.css from the brand)")
    css = subprocess.run([node, str(root / "lib" / "brand.js"), str(brand_dir), "--palette", palette, "--font", font],
                         capture_output=True, text=True)
    if css.returncode != 0:
        raise ValueError("lib/brand.js failed: " + css.stderr.strip())

    w, h = SIZES[fmt]
    order = [m for m in sync_lib.load_manifest(root)["loadOrder"] if fmt == "shorts" or not m.startswith("shorts/")]
    files = {
        "BRIEF.md": BRIEF.format(slug=slug, format=fmt, brand=brand, palette=palette, font=font,
                                 format_fields=LONG_FORM_FIELDS if fmt == "long-form" else SHORTS_FIELDS),
        "storyboard.md": STORYBOARD.format(slug=slug),
        "critique.md": CRITIQUE.format(slug=slug),
        "assets/captures/MANIFEST.md": MANIFEST.format(slug=slug),
        "compositions/brand.css": css.stdout,
        "deliver/.gitkeep": "",
        "index.html": INDEX.format(w=w, h=h, gsap=GSAP, mode=mode, slug=slug, placement_note=PLACEMENT_NOTE[fmt],
                                   scripts="\n".join(f'    <script src="lib/{m}"></script>' for m in order)),
    }
    if fmt == "long-form":
        files["compositions/overlays/.gitkeep"] = ""
    for rel, text in files.items():
        (project / rel).parent.mkdir(parents=True, exist_ok=True)
        (project / rel).write_text(text)
    sync_lib.sync(project, root)
    return project


def main(argv) -> int:
    ap = argparse.ArgumentParser(prog="python3 tools/new_video.py", description="Scaffold videos/<slug>/.")
    ap.add_argument("slug")
    ap.add_argument("--format", required=True, choices=sorted(SIZES))
    ap.add_argument("--brand", default="contentporary")
    ap.add_argument("--palette")
    ap.add_argument("--font")
    ap.add_argument("--videos-dir")
    a = ap.parse_args(argv[1:])
    try:
        project = scaffold(a.slug, a.format, a.brand, a.palette, a.font, a.videos_dir)
    except ValueError as e:
        print(e)
        return 1
    status = brandcheck.load_brand(ROOT / "brands" / a.brand)["tokens"].get("status")
    if status != "approved":
        print(f"warning: brand {a.brand} is {status} — the QA gate fails until it is approved")
    print(f"created {project} — fill BRIEF.md (film, direction), then write storyboard.md")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
