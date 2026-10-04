"""List the footage's own cuts so Shorts scene ends land on them (standards/formats/shorts.md §1).

Scene threshold 0.20 (ffmpeg `select='gt(scene,0.20)'`). Place every scene end so the exit wipe finishes
just AFTER the nearest source cut: end = cut + exit duration (the 0.36 s wipe out by default).

Usage: python3 tools/probe_cuts.py FOOTAGE [--threshold 0.20] [--exit 0.36] [--json]
"""
import argparse
import json
import sys

import media

THRESHOLD = 0.20    # shorts.md §1
EXIT = 0.36         # shorts.md wipe "duration out" (HFProfile timing("shorts").wipe.outDur)


def scene_ends(cuts, exit_dur=EXIT) -> list:
    """[{"cut": t, "scene_end": t + exit}] — the latest a graphic may end so its exit covers the cut."""
    return [{"cut": c, "scene_end": round(c + exit_dur, 3)} for c in cuts]


def main(argv) -> int:
    ap = argparse.ArgumentParser(prog="python3 tools/probe_cuts.py")
    ap.add_argument("footage")
    ap.add_argument("--threshold", type=float, default=THRESHOLD)
    ap.add_argument("--exit", type=float, default=EXIT, dest="exit_dur")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv[1:])
    try:
        rows = scene_ends(media.scene_cuts(a.footage, a.threshold), a.exit_dur)
    except media.MediaError as e:
        print(e)
        return 2
    if a.json:
        print(json.dumps(rows))
    else:
        print(f"{len(rows)} source cuts (scene > {a.threshold}); scene end = cut + {a.exit_dur} s exit")
        for r in rows:
            print(f"  cut {r['cut']:8.3f}  ->  scene end {r['scene_end']:8.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
