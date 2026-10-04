"""Kit preview: a long-form project holding chosen kit components with fixture copy, for render-and-compare
against the template stills and for the kit QA test (tools/test_kit_qa.py).

Full-frame components become reel scenes, in this order: title, subtitle, roadmap (intro + visit 1),
cta-youtube; over-footage ones become standalone documents compositions/overlays/<name>.html. The CTA gets a
synthetic watch-page screenshot and a still face clip (ffmpeg) — real projects use real captures.

Usage:
  python3 tools/kit_preview.py [component ...] [--palette gold] [--font geometric] [--videos-dir renders/kit-preview] [--slug kit-<palette>]
Default: every component. Prints the snapshot / overlay-render commands and the times worth looking at.
After a lib change, re-sync instead of rebuilding: python3 tools/sync_lib.py <project>.
"""
import argparse
import json
import re
import sys
from pathlib import Path

import new_video
import project as pj
import synth

ROOT = Path(__file__).resolve().parents[1]
ORDER = ["title", "subtitle", "roadmap", "cta-youtube", "lower-third", "side-text"]
STEPS = ('[{ label: "Predictive Idea Selection", icon: "bulb" }, { label: "Retention Based Editing", icon: "sliders" }, '
         '{ label: "Qualified Sales Calls", icon: "target" }]')
PAGE = ('{ src: "assets/captures/watch-page.png", width: 2560, height: 1440, '
        'player: [112, 150, 1600, 900], link: [150, 1235, 560, 44] }')
# component -> [(scene key, duration s, kit call, extra markup in the scene root, times to look at (scene-local s))]
FIXTURES = {
    "title": [("title", 4, 'HFKit.title(tl, host, { format: "long-form", at: 0.2, text: "Printing Prediction System", underline: 1 });', "", [1.0, 3.6])],
    "subtitle": [("subtitle", 4, 'HFKit.subtitle(tl, host, { format: "long-form", at: 0.2, kicker: "Step 1", title: "HIT Prediction" });', "", [0.5, 3.6])],
    "roadmap": [
        ("roadmap", 4, 'HFKit.roadmap(tl, host, { format: "long-form", at: 0.2, visit: 0, title: "Printing Prediction System", steps: ' + STEPS + ' });', "", [1.2, 3.6]),
        ("roadmap-2", 3, 'HFKit.roadmap(tl, host, { format: "long-form", at: 0.2, visit: 1, title: "Printing Prediction System", steps: ' + STEPS + ' });', "", [0.1, 2.8]),
    ],
    "cta-youtube": [("cta", 5.5, 'HFKit.ctaYoutube(tl, host, { format: "long-form", at: 0, page: ' + PAGE +
                     ', footage: document.querySelector(\'[data-composition-id="{id}"] .cta-face\') });',
                     '<video id="{id}-face" class="cta-face" src="assets/captures/face.mp4" data-start="0" data-duration="5.5" muted playsinline></video>',
                     [0.3, 1.2, 2.5, 5.3])],
    "lower-third": [("lower-third", 4, 'HFKit.lowerThird(tl, host, { format: "long-form", at: 0.3, text: "and I\'ve helped online entrepreneurs", out: 3.4 });', "", [3.0])],
    "side-text": [("side-text", 5, 'HFKit.sideText(tl, host, { format: "long-form", at: 0.2, items: ["Video performance", "Retention", "CTR (Click through rate)"], out: 4.4 });', "", [3.9])],
}
OVER_FOOTAGE = {"lower-third", "side-text"}
SCENE = """<template>
  <style>#root {{ position: absolute; inset: 0; overflow: hidden; }}</style>
  <div id="root" data-composition-id="{id}" data-width="1920" data-height="1080"><div class="kit-host"></div>{extra}</div>
  <script>
    (async function () {{
      var tl = gsap.timeline({{ paused: true }});
      await document.fonts.ready;
      var host = document.querySelector('[data-composition-id="{id}"] .kit-host');
      {call}
      await HFText.ready();
      window.__timelines["{id}"] = tl;
    }})();
  </script>
</template>
"""
OVERLAY = """<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=1920, height=1080">
  <script src="{gsap}"></script>
{scripts}
  <link rel="stylesheet" href="compositions/brand.css">
  <style>
    html, body {{ margin: 0; width: 1920px; height: 1080px; overflow: hidden; background: transparent; }}
    #{id}-root {{ position: relative; width: 1920px; height: 1080px; overflow: hidden; }}
  </style>
</head>
<body>
  <div id="{id}-root" data-composition-id="{id}" data-hf-mode="{mode}" data-start="0" data-duration="{dur:g}" data-width="1920" data-height="1080"><div class="kit-host"></div></div>
  <script>
    (async function () {{
      var tl = gsap.timeline({{ paused: true }});
      await document.fonts.ready;
      var host = document.querySelector("#{id}-root .kit-host");
      {call}
      await HFText.ready();
      window.__timelines["{id}"] = tl;
    }})();
  </script>
</body>
</html>
"""


def write_media(project):
    """A stand-in watch-page screenshot (player + description link) and a still face clip."""
    cap = Path(project) / "assets" / "captures"
    synth._ffmpeg(["-f", "lavfi", "-i", "color=c=0x0f0f0f:s=2560x1440,drawbox=x=112:y=150:w=1600:h=900:color=0x272727:t=fill,"
                   "drawbox=x=112:y=1170:w=1600:h=220:color=0x222222:t=fill,drawbox=x=150:y=1235:w=560:h=44:color=0x3ea6ff:t=fill",
                   "-frames:v", "1", str(cap / "watch-page.png")])
    synth._ffmpeg(["-f", "lavfi", "-i", "color=c=0x8a7d72:s=1920x1080:r=30:d=6", "-pix_fmt", "yuv420p", str(cap / "face.mp4")])


def build(components=None, palette="gold", font="geometric", videos_dir=None, slug=None, root=ROOT):
    """Scaffold and fill the preview project. Returns (project, looks): looks = [(label, reel or overlay rel, t)]."""
    components = components or ORDER
    unknown = [c for c in components if c not in FIXTURES]
    if unknown:
        raise ValueError(f"unknown kit component(s) {', '.join(unknown)} (have: {', '.join(ORDER)})")
    project = new_video.scaffold(slug or f"kit-{palette}", "long-form", "contentporary", palette, font,
                                 videos_dir or Path(root) / "renders" / "kit-preview", root)
    mode = pj.root_attrs(project)["data-hf-mode"]
    scripts = re.findall(r'    <script src="lib/[^"]+"></script>', (project / "index.html").read_text())
    slots, rows, looks, t, n, overlays = [], [], [], 0.0, 0, []
    for comp in [c for c in ORDER if c in components]:
        for key, dur, call, extra, at in FIXTURES[comp]:
            if comp in OVER_FOOTAGE:
                rel = f"compositions/overlays/{key}.html"
                (project / rel).write_text(OVERLAY.format(id=key, dur=dur, call=call, mode=mode, gsap=new_video.GSAP, scripts="\n".join(scripts)))
                overlays.append((key, dur, comp))
                looks += [(key, rel, a) for a in at]
                continue
            n += 1
            sid = f"{n:02d}-{key}"
            (project / "compositions" / f"{sid}.html").write_text(
                SCENE.format(id=sid, call=call.replace("{id}", sid), extra=extra.replace("{id}", sid)))
            slots.append(f'<div id="s-{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" '
                         f'data-start="{t:g}" data-duration="{dur:g}" data-track-index="1" data-width="1920" data-height="1080"></div>')
            rows.append(f'| {t:g} | {t + dur:g} | "{key}" | full-frame | {comp} | — | ease.camera | — |')
            looks += [(sid, "index.html", round(t + a, 3)) for a in at]
            t += dur
    # over-footage rows sit inside the reel, one after another from 0 (never overlapping, never past the reel end);
    # the reel runs at least as long as they do, so an overlay-only preview gets a reel of that length
    o = 0.0
    for key, dur, comp in overlays:
        rows.append(f'| {o:g} | {o + dur:g} | "{key}" | over-footage | {comp} | — | ease.enter | — |')
        o += dur
    t = max(t, o)
    # the scaffold placeholder goes whenever the project has any scene or overlay (QA check 1)
    index = project / "index.html"
    html = re.sub(r'\n\s*<!-- placeholder[^\n]*-->\n\s*<div id="hf-placeholder"[^\n]*</div>', "\n      " + "\n      ".join(slots), index.read_text())
    html = re.sub(r'\n\s*tl\.to\("#hf-placeholder"[^\n]*', "", html)
    index.write_text(html.replace('data-duration="5"', f'data-duration="{t:g}"', 1))
    brief = (project / "BRIEF.md").read_text().replace('film: ""', 'film: "Every kit component, as the template stills show it"')
    (project / "BRIEF.md").write_text(brief.replace('direction: ""', 'direction: "Kit preview: one scene or overlay per component"'))
    (project / "storyboard.md").write_text((project / "storyboard.md").read_text().rstrip("\n") + "\n" + "\n".join(rows) + "\n")
    (project / "transcript.json").write_text(json.dumps([{"text": "(kit preview)", "start": 0, "end": max(t, 5.0)}]) + "\n")
    if "cta-youtube" in components:
        write_media(project)
    return project, looks


def main(argv) -> int:
    ap = argparse.ArgumentParser(prog="python3 tools/kit_preview.py", description="Preview project for lib/kit components.")
    ap.add_argument("components", nargs="*")
    ap.add_argument("--palette", default="gold")
    ap.add_argument("--font", default="geometric")
    ap.add_argument("--videos-dir")
    ap.add_argument("--slug")
    a = ap.parse_args(argv[1:])
    try:
        project, looks = build(a.components or None, a.palette, a.font, a.videos_dir, a.slug)
    except ValueError as e:
        print(e)
        return 1
    out = ROOT / "renders" / "kit" / project.name
    reel = [t for _, rel, t in looks if rel == "index.html"]
    print(f"created {project}")
    if reel:
        print(f"  stills:  npx hyperframes snapshot {project} --at {','.join(f'{t:g}' for t in reel)} --no-end -o {out}")
    for key in sorted({k for k, rel, _ in looks if rel != "index.html"}):
        ts = ",".join(f"{t:g}" for k, _, t in looks if k == key)
        print(f"  overlay: npx hyperframes render {project} -c compositions/overlays/{key}.html --format=mov -q draft -o {out}/{key}.mov"
              f"   (look at {ts} s)")
    print(f"  after a lib change: python3 tools/sync_lib.py {project}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
