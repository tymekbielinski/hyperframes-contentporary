"""Detect render flicker in a rendered video: the picture jumps away and RETURNS to where it was.

Real motion (a camera move, a mark landing) has a smooth envelope: neighbouring frame steps are of
similar size. Render flicker — parallel workers rendering a block of frames from a wrong seek state —
makes the picture jump away for 1–8 frames and then come back. So a hit needs:
  1. an "out" step that dwarfs its neighbourhood (> MIN_STEP and > max(RATIO × local median, local + MARGIN)),
  2. a "back" step k ≤ MAX_RETURN frames later (≥ MIN_STEP and > RATIO × the out step's local median), and
  3. confirmation from the pixels: the frame after the back step matches the frame before the out step —
     their mean |Δluma| at 320×180 is < MIN_STEP + local median × (k + 1) (the allowance is the scene's own
     motion over those frames, 0 on a still) and < half the distance from the frame before to the last
     "away" frame (the picture is much closer to where it was than to where it went).
Both the out and back frames are reported. A jump that does not return (a hard appear, a snap, an image swap,
staggered pop-ins) is a legitimate edit, not flicker. Ported from video 09's scan-flicker.py (same
thresholds, plus the return rule); frame differences come from ffmpeg (tools/media.py), so no numpy.

A standalone run reports intended hard cuts only if the picture returns within MAX_RETURN frames; the QA
gate (qa.py check 10) also excludes the known cut times.

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
MAX_RETURN = 8      # the back step comes at most this many frames after the out step (0.27 s at 30 fps)
COMPARE_SIZE = (320, 180)   # the scale frame_diffs measures at
SELECT_CHUNK = 100          # frames per ffmpeg select expression


def _local(diffs, i):
    ctx = diffs[max(0, i - WINDOW):i] + diffs[i + 1:i + 1 + WINDOW]
    return statistics.median(ctx) if ctx else None


def find_flicker(diffs, compare) -> list:
    """[(frame, step, local_median)] for every confirmed out-and-back jump, sorted by frame; frame is the 0-based
    index of the frame that differs from its predecessor (diffs[i] compares frame i and i+1, so frame = i + 1).
    compare([(a, b), ...]) -> [mean |Δluma| between frames a and b, ...] (frame_comparer(video) for a file)."""
    locals_ = [_local(diffs, i) for i in range(len(diffs))]
    cands = []
    for i, d in enumerate(diffs):
        local = locals_[i]
        if local is None or not (d > MIN_STEP and d > max(RATIO * local, local + MARGIN)):
            continue
        for k in range(1, MAX_RETURN + 1):
            j = i + k
            if j < len(diffs) and diffs[j] >= MIN_STEP and diffs[j] > RATIO * local:
                cands.append((i, j, local, k))
    if not cands:
        return []
    dists = compare([(i, j + 1) for i, j, _, _ in cands] + [(i, j) for i, j, _, _ in cands])
    back, away = dists[:len(cands)], dists[len(cands):]
    hits, used = {}, set()
    for (i, j, local, k), dist, gone in zip(cands, back, away):   # ordered by i, then k: nearest return first
        if i in used or j in used:
            continue
        if dist < MIN_STEP + local * (k + 1) and dist < 0.5 * gone:
            used.update((i, j))
            hits[i + 1] = (i + 1, round(diffs[i], 1), round(local, 2))
            hits[j + 1] = (j + 1, round(diffs[j], 1), round(locals_[j] if locals_[j] is not None else 0.0, 2))
    return [hits[f] for f in sorted(hits)]


def frame_comparer(path, size=COMPARE_SIZE):
    """compare(pairs) for find_flicker: decodes only the frames the pairs name (gray, `size`), one ffmpeg pass per
    SELECT_CHUNK frames, and returns the mean |Δluma| for each pair."""
    w, h = size
    n = w * h

    def compare(pairs):
        want = sorted({f for pair in pairs for f in pair})
        frames = {}
        for c in range(0, len(want), SELECT_CHUNK):
            chunk = want[c:c + SELECT_CHUNK]
            expr = "+".join(f"eq(n\\,{f})" for f in chunk)
            raw = media.run([media.tool("ffmpeg"), "-v", "error", "-nostdin", "-i", media._need(path), "-an", "-vf",
                             f"select={expr},scale={w}:{h},format=gray", "-fps_mode", "passthrough",
                             "-f", "rawvideo", "-"], binary=True)
            got = [raw[x:x + n] for x in range(0, len(raw) - n + 1, n)]
            if len(got) != len(chunk):
                raise media.MediaError(f"{path}: asked ffmpeg for {len(chunk)} frames to compare, got {len(got)}")
            frames.update(zip(chunk, got))
        return [sum(abs(x - y) for x, y in zip(frames[a], frames[b])) / n for a, b in pairs]
    return compare


def scan(path) -> dict:
    diffs = media.frame_diffs(path)
    return {"file": str(path), "frames": len(diffs) + 1,
            "median": round(statistics.median(diffs), 2) if diffs else 0.0,
            "flicker": find_flicker(diffs, frame_comparer(path))}


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
