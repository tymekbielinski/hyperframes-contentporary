"""Brand proof sheet: a long-form project that shows the kit — full-screen title, subtitle, lower third and
side screen text — in EVERY palette of a brand, one scene per palette, for onboarding approval
(brands/_template/README.md). The project is a normal scaffold (tools/new_video.py), so the QA gate runs on it.

Each palette scene carries its own palette as inline CSS variables (from lib/brand.js --json) and its own
data-hf-mode on a wrapper, so the kit reads the right ground mode; index.html keeps the BRIEF palette (QA
check 3). The lower third and side text sit over a neutral footage stand-in.

Usage:
  python3 tools/proof_sheet.py <brand> [--videos-dir videos] [--slug proof-<brand>] [--font <key>]
Then:
  python3 tools/qa.py videos/proof-<brand>              (a draft brand fails check 3 until approved — expected)
  npx hyperframes render videos/proof-<brand> -o videos/proof-<brand>/renders/proof.mp4
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import brandcheck
import new_video

ROOT = Path(__file__).resolve().parents[1]
SCENE_DUR = 4.5        # every kit animation lands by ≈ 3 s; the last 0.3 s is still (QA check 9)
COPY = {"title": "Printing Prediction System", "kicker": "Step 1", "subtitle": "HIT Prediction",
        "key_line": "and I've helped online entrepreneurs",
        "points": ["Video performance", "Retention", "CTR (Click through rate)"]}

SCENE = """<template>
  <style>
    #root {{ position: absolute; inset: 0; overflow: hidden; }}
    .proof-scene {{ position: absolute; inset: 0; background: var(--hf-ground-deep); }}
    .proof-q {{ position: absolute; width: 1920px; height: 1080px; transform: scale(0.5); transform-origin: 0 0; overflow: hidden; }}
    .proof-q.q1 {{ left: 0; top: 0; }} .proof-q.q2 {{ left: 960px; top: 0; }}
    .proof-q.q3 {{ left: 0; top: 540px; }} .proof-q.q4 {{ left: 960px; top: 540px; }}
    .proof-footage {{ position: absolute; inset: 0; background: radial-gradient(ellipse 30% 45% at 62% 46%, #b9a89a 0%, #8c7d72 45%, transparent 70%), linear-gradient(160deg, #9aa3aa 0%, #5d656c 100%); }}
    .proof-label {{ position: absolute; left: 24px; top: 20px; padding: 6px 16px; border-radius: 999px; font: 600 26px system-ui, sans-serif;
      color: var(--hf-text-primary); background: var(--hf-surface-fill); border: 1px solid var(--hf-surface-bevel); z-index: 5; }}
  </style>
  <div id="root" data-composition-id="{id}" data-width="1920" data-height="1080">
    <div class="proof-scene" data-hf-mode="{mode}" style="{vars}">
      <div class="proof-q q1"><div class="kit-host"></div></div>
      <div class="proof-q q2"><div class="kit-host"></div></div>
      <div class="proof-q q3"><div class="proof-footage"></div><div class="kit-host"></div></div>
      <div class="proof-q q4"><div class="proof-footage"></div><div class="kit-host"></div></div>
      <div class="proof-label">{palette} · {mode}</div>
    </div>
  </div>
  <script>
    (async function () {{
      var tl = gsap.timeline({{ paused: true }});
      await document.fonts.ready;
      var hosts = document.querySelectorAll('[data-composition-id="{id}"] .kit-host');
      var LF = {{ format: "long-form" }};
      HFKit.title(tl, hosts[0], Object.assign({{ at: 0.2, text: {title}, underline: 1 }}, LF));
      HFKit.subtitle(tl, hosts[1], Object.assign({{ at: 0.3, kicker: {kicker}, title: {subtitle} }}, LF));
      HFKit.lowerThird(tl, hosts[2], Object.assign({{ at: 0.4, text: {key_line} }}, LF));
      HFKit.sideText(tl, hosts[3], Object.assign({{ at: 0.2, items: {points} }}, LF));
      await HFText.ready();
      window.__timelines["{id}"] = tl;
    }})();
  </script>
</template>
"""


def palette_vars(root, brand_dir, palette, font) -> str:
    """The palette's CSS variables as one inline style string (lib/brand.js --json, sorted)."""
    r = subprocess.run([shutil.which("node") or "node", str(Path(root) / "lib" / "brand.js"), str(brand_dir),
                        "--palette", palette, "--font", font, "--json"], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise ValueError(f"lib/brand.js failed for palette {palette}: {r.stderr.strip()}")
    return "; ".join(f"{k}: {v}" for k, v in sorted(json.loads(r.stdout).items())).replace('"', "&quot;")


def build(brand, videos_dir=None, slug=None, font=None, root=ROOT) -> Path:
    """Scaffold videos/<slug>/ (default proof-<brand>) with one kit scene per palette; return its path."""
    root = Path(root)
    brand_dir = root / "brands" / brand
    try:
        loaded = brandcheck.load_brand(brand_dir)
    except brandcheck.BrandError as e:
        raise ValueError(str(e))
    tokens, palettes = loaded["tokens"], loaded["palettes"]
    font = font or tokens["fonts"]["defaultHeadline"]
    project = new_video.scaffold(slug or f"proof-{brand}", "long-form", brand, None, font, videos_dir, root)
    slots, rows, t = [], [], 0.0
    for name in tokens["palettes"]:
        sid = "proof-" + name
        scene = SCENE.format(id=sid, palette=name, mode=palettes[name]["mode"],
                             vars=palette_vars(root, brand_dir, name, font),
                             **{k: json.dumps(v) for k, v in COPY.items()})
        (project / "compositions" / f"{sid}.html").write_text(scene)
        slots.append(f'<div id="s-{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" '
                     f'data-start="{t:g}" data-duration="{SCENE_DUR:g}" data-track-index="1" data-width="1920" data-height="1080"></div>')
        rows.append(f'| {t:g} | {t + SCENE_DUR:g} | "{name} palette" | full-frame | proof-sheet | '
                    f'title · subtitle · lower-third · side-text | ease.glow / ease.card / ease.enter / ease.sweep | — |')
        t += SCENE_DUR
    index = project / "index.html"
    html = index.read_text()
    html, n = re.subn(r'\n\s*<!-- placeholder[^\n]*-->\n\s*<div id="hf-placeholder"[^\n]*</div>', "\n      " + "\n      ".join(slots), html)
    html, k = re.subn(r'\n\s*tl\.to\("#hf-placeholder"[^\n]*', "", html)
    if (n, k) != (1, 1):
        raise ValueError("new_video's index.html changed shape — update proof_sheet.build()")
    index.write_text(html.replace('data-duration="5"', f'data-duration="{t:g}"', 1))
    brief = (project / "BRIEF.md").read_text()
    brief = brief.replace('film: ""', f'film: "Approve the {brand} brand: every kit layout in every palette"')
    brief = brief.replace('direction: ""', 'direction: "Proof sheet: one scene per palette, kit components only"')
    (project / "BRIEF.md").write_text(brief)
    (project / "storyboard.md").write_text((project / "storyboard.md").read_text().rstrip("\n") + "\n" + "\n".join(rows) + "\n")
    # The proof sheet has no speech; this one segment gives the density check its runtime.
    (project / "transcript.json").write_text(json.dumps([{"text": "(proof sheet, no speech)", "start": 0, "end": t}]) + "\n")
    return project


def main(argv) -> int:
    ap = argparse.ArgumentParser(prog="python3 tools/proof_sheet.py", description="Kit proof sheet in every palette of a brand.")
    ap.add_argument("brand")
    ap.add_argument("--videos-dir")
    ap.add_argument("--slug")
    ap.add_argument("--font")
    a = ap.parse_args(argv[1:])
    try:
        project = build(a.brand, a.videos_dir, a.slug, a.font)
    except ValueError as e:
        print(e)
        return 1
    n = len(brandcheck.load_brand(ROOT / "brands" / a.brand)["tokens"]["palettes"])
    stills = ",".join(f"{i * SCENE_DUR + SCENE_DUR - 0.2:g}" for i in range(n))
    print(f"created {project} — {n} palettes, {n * SCENE_DUR:g} s")
    print(f"  gate:   python3 tools/qa.py {project}")
    print(f"  render: npx hyperframes render {project} -o {project}/renders/proof.mp4")
    print(f"  stills: npx hyperframes snapshot {project} --at {stills} --no-end -o {project}/renders/proof-stills")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
