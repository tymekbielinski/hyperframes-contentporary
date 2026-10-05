"""Critique boards: a candidate frame above reference stills of the same pattern (standards/core/qa.md §2).

Usage:
  python3 tools/ref_board.py videos/<slug> --render R.mp4 [--row N]
      full-frame storyboard rows, paired with index.html slots (as slice.py pairs them); writes
      renders/critique/row-NN.jpg and renders/critique/boards.md
  python3 tools/ref_board.py --pattern ID [--pattern ID …] --still FRAME.png [--still FRAME2.png] -o OUT.jpg
      any frame — e.g. an over-footage overlay composited over the face — against a pattern's references

Top row: the candidate (middle and settled frame). Bottom row: up to 3 settled stills of reviewed reference
shots of the row's patterns (pinned exemplars first). Look at the gap and score Craft and On-brand against it.
"""
import argparse
import sys
import tempfile
from pathlib import Path

import media
import project as pj
import refs

ROOT = refs.ROOT
TILE_W, TILE_H = 640, 360
BLANK = "0x111111"
SETTLE = 0.35   # s before the slot ends: inside check 9's still window


def ref_stills(lib: dict, pids, n: int = 3) -> list:
    queues = [[v["dir"] / s["stills"][-1] for v, s in refs.exemplars(lib, pid) if s.get("stills")] for pid in pids]
    out = []
    while len(out) < n and any(queues):
        for q in queues:
            if q and len(out) < n:
                out.append(q.pop(0))
    return out


def compose(candidates, references, out) -> Path:
    tiles = (list(candidates)[:3] + [None] * 3)[:3] + (list(references)[:3] + [None] * 3)[:3]
    args, chains = [media.tool("ffmpeg"), "-v", "error", "-nostdin", "-y"], []
    for i, t in enumerate(tiles):
        if t is None:
            args += ["-f", "lavfi", "-i", f"color=c={BLANK}:s={TILE_W}x{TILE_H}:d=1"]
        else:
            args += ["-i", str(t)]
        chains.append(f"[{i}:v]scale={TILE_W}:{TILE_H}:force_original_aspect_ratio=decrease,"
                      f"pad={TILE_W}:{TILE_H}:(ow-iw)/2:(oh-ih)/2:color={BLANK},setsar=1,format=yuvj420p[t{i}]")
    graph = ";".join(chains) + ";[t0][t1][t2]hstack=3[top];[t3][t4][t5]hstack=3[bot];[top][bot]vstack[out]"
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    media.run(args + ["-filter_complex", graph, "-map", "[out]", "-frames:v", "1", "-q:v", "4", str(out)])
    return Path(out)


def project_boards(project, render, row=None, root=ROOT) -> list:
    project = Path(project)
    lib = refs.load_library(root)
    rows = pj.read_storyboard(project)
    fps = media.video_info(render)["fps"]
    pairs, problems = pj.slot_pairing(pj.composition_slots(project), rows, fps)
    if problems:
        raise pj.ProjectError("; ".join(problems))
    out_dir = project / "renders" / "critique"
    boards = []
    with tempfile.TemporaryDirectory() as tmp:
        for slot, r in pairs:
            if row is not None and r["row"] != row:
                continue
            frames = []
            for name, t in (("mid", slot["start"] + slot["dur"] / 2),
                            ("settled", max(slot["start"], slot["start"] + slot["dur"] - SETTLE))):
                frames.append(media.extract_frame(render, t, Path(tmp) / f"{r['row']}-{name}.png", width=960))
            pids, _ = refs.type_ids(r["type"], lib["registry"])
            stills = ref_stills(lib, pids)
            board = compose(frames, stills, out_dir / f"row-{r['row']:02d}.jpg")
            boards.append({"row": r["row"], "type": r["type"], "board": board.name,
                           "refs": [f"{p.parents[1].name} {p.name.split('-')[0]}" for p in stills]})
    lines = ["# Critique boards", "", "Top: candidate (mid, settled). Bottom: reference stills of the row's patterns.", "",
             "| Row | Type | Board | References |", "|---|---|---|---|"]
    lines += [f"| {b['row']} | {b['type']} | [{b['board']}]({b['board']}) | {', '.join(b['refs']) or 'none yet'} |" for b in boards]
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "boards.md").write_text("\n".join(lines) + "\n")
    return boards


def main(argv, root=ROOT) -> int:
    ap = argparse.ArgumentParser(prog="python3 tools/ref_board.py")
    ap.add_argument("project", nargs="?")
    ap.add_argument("--render")
    ap.add_argument("--row", type=int)
    ap.add_argument("--pattern", action="append", default=[])
    ap.add_argument("--still", action="append", default=[])
    ap.add_argument("-o", "--out")
    if len(argv) < 2:
        print(__doc__)
        return 2
    a = ap.parse_args(argv[1:])
    try:
        if a.project:
            if not a.render:
                ap.error("project mode needs --render")
            for b in project_boards(a.project, a.render, a.row, root):
                print(f"row {b['row']:>2} {b['type']}: {b['board']} vs {', '.join(b['refs']) or 'no references yet'}")
            return 0
        if not (a.pattern and a.still and a.out):
            ap.error("frame mode needs --pattern, --still and -o")
        lib = refs.load_library(root)
        unknown = [p for p in a.pattern if p not in lib["registry"]]
        if unknown:
            ap.error(f"unknown pattern ID(s): {', '.join(unknown)}")
        print(compose([Path(s) for s in a.still], ref_stills(lib, a.pattern), Path(a.out)))
        return 0
    except (pj.ProjectError, media.MediaError, refs.RefError) as e:
        print(f"error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
