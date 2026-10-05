"""Fix a reference video's shot list: split, merge, re-extract stills (references/README.md §Analyse).

Usage:
  python3 tools/ref_shots.py <slug> split <shot_id> <t> [<t> …]   # split a shot at the given times
  python3 tools/ref_shots.py <slug> merge <shot_id> <shot_id2>    # merge two adjacent shots (first keeps its id and fields)
  python3 tools/ref_shots.py <slug> stills <shot_id> [<t> …]       # re-extract the shot's stills (default times:
                                                                  # ref_ingest.still_times) from the source video
  options: --video <path>   source video (default: ~/Downloads/<source_file> from source.json)

Operates on references/videos/<slug>/shots.json and keeps shots contiguous. `split` leaves new shots as drafts
and re-extracts stills for the original and every new shot (needs the video).
"""
import argparse
import json
import sys
from pathlib import Path

import media
import ref_ingest
import refs

ROOT = refs.ROOT


class RefShotsError(Exception):
    """A shot that does not exist, a time outside it, or shots that are not adjacent."""


def _load(d: Path) -> dict:
    try:
        return json.loads((Path(d) / "shots.json").read_text())
    except (OSError, ValueError) as e:
        raise RefShotsError(f"cannot read {Path(d) / 'shots.json'}: {e}")


def _save(d: Path, data: dict) -> None:
    (Path(d) / "shots.json").write_text(json.dumps(data, indent=2) + "\n")


def _find(data: dict, shot_id: str) -> int:
    for i, s in enumerate(data["shots"]):
        if s["id"] == shot_id:
            return i
    raise RefShotsError(f"no shot {shot_id}")


def split(d, shot_id: str, times) -> list:
    """Split a shot at `times`; the original keeps its id/fields/stills, new draft shots get fresh ids."""
    data = _load(d)
    i = _find(data, shot_id)
    shot = data["shots"][i]
    ts = sorted(times)
    if not ts:
        raise RefShotsError("give at least one time")
    for t in ts:
        if not shot["t_in"] < t < shot["t_out"]:
            raise RefShotsError(f"t={t} is not strictly inside {shot_id} ({shot['t_in']}–{shot['t_out']})")
    if len(set(ts)) != len(ts):
        raise RefShotsError("duplicate split times")
    top = max(int(s["id"][1:]) for s in data["shots"])
    edges = [shot["t_in"]] + ts + [shot["t_out"]]
    new = [refs.empty_shot(top + k, edges[k], edges[k + 1]) for k in range(1, len(edges) - 1)]
    shot["t_out"] = ts[0]
    data["shots"][i + 1:i + 1] = new
    _save(d, data)
    return [s["id"] for s in new]


def merge(d, a: str, b: str) -> None:
    """Merge shot b (the one right after a) into a."""
    data = _load(d)
    i, j = _find(data, a), _find(data, b)
    if j != i + 1:
        raise RefShotsError(f"{b} is not the shot immediately after {a}")
    sa, sb = data["shots"][i], data["shots"][j]
    sa["t_out"] = sb["t_out"]
    sa["stills"] = sa["stills"] + sb["stills"]
    del data["shots"][j]
    _save(d, data)


def restill(d, shot_id: str, video, times=None) -> list:
    """Delete the shot's stills and extract new ones from the source video."""
    d = Path(d)
    data = _load(d)
    shot = data["shots"][_find(data, shot_id)]
    ts = list(times) if times else ref_ingest.still_times(shot["t_in"], shot["t_out"])
    for rel in shot["stills"]:
        (d / rel).unlink(missing_ok=True)
    (d / "stills").mkdir(exist_ok=True)
    rels = []
    for j, t in enumerate(ts):
        rel = f"stills/{shot_id}-{chr(97 + j)}.jpg"
        ref_ingest.extract_jpeg(video, t, d / rel)
        rels.append(rel)
    shot["stills"] = rels
    _save(d, data)
    return rels


def main(argv, root=ROOT) -> int:
    ap = argparse.ArgumentParser(prog="python3 tools/ref_shots.py")
    ap.add_argument("slug")
    ap.add_argument("command", choices=["split", "merge", "stills"])
    ap.add_argument("args", nargs="+")
    ap.add_argument("--video")
    if len(argv) < 2:
        print(ap.format_usage().strip())
        print(__doc__)
        return 2
    a = ap.parse_args(argv[1:])
    d = Path(root) / "references" / "videos" / a.slug
    try:
        if not (d / "shots.json").is_file():
            raise RefShotsError(f"{d} has no shots.json")
        try:
            nums = [float(x) for x in a.args[1:]] if a.command != "merge" else []
        except ValueError:
            raise RefShotsError("times must be numbers (seconds)")
        sid = a.args[0]

        def video():
            if a.video:
                return Path(a.video)
            src = json.loads((d / "source.json").read_text())["source_file"]
            return Path.home() / "Downloads" / src

        if a.command == "split":
            new = split(d, sid, nums)
            v = video()
            for s in [sid] + new:
                restill(d, s, v)
            print(f"split {sid} → {', '.join([sid] + new)}; stills re-extracted")
        elif a.command == "merge":
            if len(a.args) != 2:
                raise RefShotsError("merge takes exactly two shot ids")
            merge(d, sid, a.args[1])
            print(f"merged {a.args[1]} into {sid}")
        else:
            rels = restill(d, sid, video(), nums or None)
            print(f"{sid}: {len(rels)} stills")
    except (RefShotsError, media.MediaError, OSError) as e:
        print(f"error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
