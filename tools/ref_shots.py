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
import os
import re
import shutil
import sys
import tempfile
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
    path = Path(d) / "shots.json"
    tmp = path.with_name("shots.json.tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    os.replace(tmp, path)


def _listed_elsewhere(data: dict, shot_id: str) -> set:
    return {rel for s in data["shots"] if s["id"] != shot_id for rel in s["stills"]}


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
    nums = [int(s["id"][1:]) for s in data["shots"]]
    for f in (Path(d) / "stills").glob("s*-*.jpg"):      # a freed id stays taken while its files exist
        m = re.match(r"s(\d{3,})-", f.name)
        if m:
            nums.append(int(m.group(1)))
    top = max(nums)
    edges = [shot["t_in"]] + ts + [shot["t_out"]]
    new = [refs.empty_shot(top + k, edges[k], edges[k + 1]) for k in range(1, len(edges) - 1)]
    shot["t_out"] = ts[0]
    data["shots"][i + 1:i + 1] = new
    _save(d, data)
    return [s["id"] for s in new]


def merge(d, a: str, b: str) -> None:
    """Merge shot b (the one right after a) into a; b's stills are renamed to a's id so names carry their owner."""
    d = Path(d)
    data = _load(d)
    i, j = _find(data, a), _find(data, b)
    if j != i + 1:
        raise RefShotsError(f"{b} is not the shot immediately after {a}")
    sa, sb = data["shots"][i], data["shots"][j]
    allst = [(r, True) for r in sa["stills"]] + [(r, False) for r in sb["stills"]]
    cap = ref_ingest.MAX_STILLS
    if len(allst) > cap:
        keep = {round(k * (len(allst) - 1) / (cap - 1)) for k in range(cap)}
        for k, (rel, _) in enumerate(allst):
            if k not in keep:
                (d / rel).unlink(missing_ok=True)
        allst = [x for k, x in enumerate(allst) if k in keep]
    used = {Path(r).stem[len(a) + 1:] for r, own in allst if own}
    out = []
    for rel, own in allst:
        if not own and (d / rel).is_file():
            letter = next(chr(c) for c in range(97, 123)
                          if chr(c) not in used and not (d / "stills" / f"{a}-{chr(c)}.jpg").exists())
            used.add(letter)
            new = f"stills/{a}-{letter}.jpg"
            os.replace(d / rel, d / new)
            rel = new
        out.append(rel)
    sa["t_out"] = sb["t_out"]
    sa["stills"] = out
    del data["shots"][j]
    _save(d, data)


def restill(d, shot_id: str, video, times=None) -> list:
    """Replace the shot's stills with fresh ones from the source video; on any failure nothing changes."""
    d = Path(d)
    data = _load(d)
    shot = data["shots"][_find(data, shot_id)]
    if times:
        ts = list(times)
        if len(ts) > ref_ingest.MAX_STILLS:
            raise RefShotsError(f"at most {ref_ingest.MAX_STILLS} stills per shot")
        for t in ts:
            if not shot["t_in"] <= t < shot["t_out"]:
                raise RefShotsError(f"t={t} is outside {shot_id} ({shot['t_in']}–{shot['t_out']})")
    else:
        ts = ref_ingest.still_times(shot["t_in"], shot["t_out"])
    (d / "stills").mkdir(exist_ok=True)
    tmp = Path(tempfile.mkdtemp(dir=d / "stills", prefix=".restill-"))
    try:
        rels = []
        for j, t in enumerate(ts):
            ref_ingest.extract_jpeg(video, t, tmp / f"{j}.jpg")
            rels.append(f"stills/{shot_id}-{chr(97 + j)}.jpg")
        elsewhere = _listed_elsewhere(data, shot_id)
        for rel in shot["stills"]:
            if Path(rel).name.startswith(f"{shot_id}-") and rel not in elsewhere:
                (d / rel).unlink(missing_ok=True)
        for j, rel in enumerate(rels):
            os.replace(tmp / f"{j}.jpg", d / rel)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
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
                v = Path(a.video)
            else:
                try:
                    v = Path.home() / "Downloads" / json.loads((d / "source.json").read_text())["source_file"]
                except (KeyError, OSError, ValueError) as e:
                    raise RefShotsError(f"cannot find source_file in source.json ({e!r}); pass --video")
            if not v.is_file():
                raise RefShotsError(f"source video {v} not found; pass --video")
            return v

        if a.command == "split":
            v = video()
            new = split(d, sid, nums)
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
