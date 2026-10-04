"""Detect render flicker in a rendered video: an ISOLATED jump against its local neighbourhood.

Real motion (a camera move, a mark landing) has a smooth envelope: neighbouring frame steps are of
similar size. Render flicker — parallel workers rendering blocks of frames from different seek states —
shows a single frame pair whose step dwarfs its neighbours. Ported from video 09's scan-flicker.py
(same thresholds); frame differences now come from ffmpeg (tools/media.py), so no numpy.

Usage: python3 tools/scan_flicker.py VIDEO [VIDEO...]   (exit 1 if any file flickers)
"""
import statistics
import sys
from pathlib import Path

import media

MIN_STEP = 2.5      # mean |Δluma| (0–255) a step must exceed to count at all
RATIO = 4.0         # ... and exceed RATIO × the local median
MARGIN = 2.0        # ... and the local median + MARGIN
WINDOW = 4          # neighbours on each side


def find_flicker(diffs) -> list:
    """[(frame, step, local_median)] for every isolated jump; frame is the 0-based index of the frame
    that differs from its predecessor (diffs[i] compares frame i and i+1, so frame = i + 1)."""
    hits = []
    for i, d in enumerate(diffs):
        ctx = diffs[max(0, i - WINDOW):i] + diffs[i + 1:i + 1 + WINDOW]
        if not ctx:
            continue
        local = statistics.median(ctx)
        if d > MIN_STEP and d > max(RATIO * local, local + MARGIN):
            hits.append((i + 1, round(d, 1), round(local, 2)))
    return hits


def scan(path) -> dict:
    diffs = media.frame_diffs(path)
    return {"file": str(path), "frames": len(diffs) + 1,
            "median": round(statistics.median(diffs), 2) if diffs else 0.0, "flicker": find_flicker(diffs)}


def main(argv) -> int:
    if len(argv) < 2:
        print("usage: python3 tools/scan_flicker.py VIDEO [VIDEO...]")
        return 2
    bad = 0
    for f in argv[1:]:
        try:
            r = scan(f)
        except media.MediaError as e:
            print(e)
            return 2
        bad += bool(r["flicker"])
        print("%-30s frames=%4d median=%.2f  FLICKER=%d %s" % (
            Path(f).name, r["frames"], r["median"], len(r["flicker"]), r["flicker"][:10]))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
