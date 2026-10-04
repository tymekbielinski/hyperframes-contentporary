"""Detect render flicker in a rendered video: an OUT-AND-BACK jump against its local neighbourhood.

Real motion (a camera move, a mark landing) has a smooth envelope: neighbouring frame steps are of
similar size. Render flicker — parallel workers rendering blocks of frames from different seek states —
makes the picture jump away and come back: a frame step that dwarfs its neighbours, answered by a
comparable step within 2 frames. Both steps are reported. A single isolated step (a hard appear, a snap,
an image swap) is a legitimate edit, not flicker. Ported from video 09's scan-flicker.py (same
thresholds, plus the out-and-back rule); frame differences come from ffmpeg (tools/media.py), so no numpy.

A standalone run reports intended hard cuts (scene changes) too: a cut is one huge frame step, exactly
like a glitch. The QA gate (qa.py check 10) excludes the known cut times.

Usage: python3 tools/scan_flicker.py VIDEO [VIDEO...]   (exit 1 if any file flickers, 2 on a bad file)
"""
import statistics
import sys
from pathlib import Path

import media

MIN_STEP = 2.5      # mean |Δluma| (0–255) a step must exceed to count at all
RATIO = 4.0         # ... and exceed RATIO × the local median
MARGIN = 2.0        # ... and the local median + MARGIN
WINDOW = 4          # neighbours on each side
RETURN = 2          # the answering step must come within this many frames (before or after)


def find_flicker(diffs) -> list:
    """[(frame, step, local_median)] for every out-and-back jump; frame is the 0-based index of the frame
    that differs from its predecessor (diffs[i] compares frame i and i+1, so frame = i + 1).
    A step counts when it dwarfs its neighbourhood (> MIN_STEP and > max(RATIO × local median, local + MARGIN))
    AND a comparable step (≥ MIN_STEP and > RATIO × the same local median) lies within RETURN frames of it."""
    hits = []
    for i, d in enumerate(diffs):
        ctx = diffs[max(0, i - WINDOW):i] + diffs[i + 1:i + 1 + WINDOW]
        if not ctx:
            continue
        local = statistics.median(ctx)
        if not (d > MIN_STEP and d > max(RATIO * local, local + MARGIN)):
            continue
        partners = [diffs[j] for j in range(i - RETURN, i + RETURN + 1) if j != i and 0 <= j < len(diffs)]
        if any(x >= MIN_STEP and x > RATIO * local for x in partners):
            hits.append((i + 1, round(d, 1), round(local, 2)))
    return hits


def scan(path) -> dict:
    diffs = media.frame_diffs(path)
    return {"file": str(path), "frames": len(diffs) + 1,
            "median": round(statistics.median(diffs), 2) if diffs else 0.0, "flicker": find_flicker(diffs)}


def main(argv) -> int:
    if len(argv) < 2:
        print("usage: python3 tools/scan_flicker.py VIDEO [VIDEO...]  (reports intended hard cuts too; qa.py excludes them)")
        return 2
    bad = errors = 0
    for f in argv[1:]:
        try:
            r = scan(f)
        except media.MediaError as e:
            print(e, file=sys.stderr)
            errors += 1
            continue
        bad += bool(r["flicker"])
        print("%-30s frames=%4d median=%.2f  FLICKER=%d %s" % (
            Path(f).name, r["frames"], r["median"], len(r["flicker"]), r["flicker"][:10]))
    return 2 if errors else (1 if bad else 0)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
