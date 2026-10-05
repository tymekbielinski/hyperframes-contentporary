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
