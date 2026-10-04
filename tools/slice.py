"""Package a long-form graphics render for the editor: clips named by timeline timecode + TIMECODES.csv + README.

Full-frame scenes: the rendered reel (index.html, one slot per scene in timeline order) is cut into
frame-exact silent MP4s. Over-footage layouts: each is its own composition rendered as ProRes 4444
with alpha (`npx hyperframes render -c compositions/overlays/<name>.html --format=mov -o
renders/overlays/<name>.mov`); slice verifies and renames them. Timeline placement comes from the
storyboard.md beat grid: full-frame rows pair with reel slots in order, over-footage rows with the
overlay files in name order, and every pairing must agree on duration (±1.5 frames).
Ported from video 09's scripts/slice.mjs. Delivery rules: standards/formats/long-form.md.

Usage: python3 tools/slice.py videos/<slug> --reel renders/reel.mp4 [--overlays renders/overlays]
                              [--out deliver] [--fps 30]
"""
import argparse
import csv
import shutil
import sys
from pathlib import Path

import media
import project as pj

COLUMNS = ["kind", "scene", "file", "timeline_in_tc", "timeline_out_tc", "timeline_in_s", "timeline_out_s",
           "in_frame", "out_frame", "duration_s", "frames", "title"]
TOLERANCE_FRAMES = pj.PAIR_TOLERANCE_FRAMES
SIZE = (1920, 1080)     # long-form delivery


class SliceError(Exception):
    """A pairing or input that would produce wrong clips. Nothing is written when this is raised."""


def tc(seconds: float, fps: float) -> str:
    f = round(seconds * fps)
    ifps = round(fps)
    s = f // ifps
    return f"{s // 3600:02d}:{s // 60 % 60:02d}:{s % 60:02d}:{f % ifps:02d}"


def tc_file(seconds: float, fps: float) -> str:
    t = tc(seconds, fps).replace(":", "-")
    return t[3:] if t.startswith("00-") else t


def _title(words: str) -> str:
    return words.strip().strip('"“”').strip()


def _check_size(what, info):
    if (info["width"], info["height"]) != SIZE:
        raise SliceError(f"{what} is {info['width']}×{info['height']}, expected {SIZE[0]}×{SIZE[1]} (long-form) — re-render it")


def plan(project, reel, overlays_dir=None, fps=30.0) -> list:
    """Every clip to write, as dicts (one per TIMECODES.csv row plus the cut/copy source). Raises SliceError."""
    project = Path(project)
    if pj.read_brief(project).get("format") != "long-form":
        raise SliceError("slice is for long-form; a Short is delivered as one finished MP4 (render it to deliver/<slug>.mp4)")
    rows = pj.read_storyboard(project)
    over = sorted((r for r in rows if r["placement"] == "over-footage"), key=lambda r: r["t_in"])
    slots = pj.composition_slots(project)
    pairs, problems = pj.slot_pairing(slots, rows, fps, TOLERANCE_FRAMES)
    if problems and not pairs:          # a count mismatch: nothing to pair
        raise SliceError(problems[0])
    reel_info = media.video_info(reel)
    _check_size("the reel", reel_info)
    if abs(reel_info["fps"] - fps) > 0.01:
        raise SliceError(f"the reel runs at {reel_info['fps']:g} fps but --fps is {fps:g} — re-render or pass --fps")
    if problems:
        raise SliceError(problems[0])
    clips, tol = [], TOLERANCE_FRAMES / fps
    for n, (slot, row) in enumerate(pairs, 1):
        if slot["start"] + slot["dur"] > reel_info["duration"] + tol:
            raise SliceError(f"slot {slot['id']} ends at {slot['start'] + slot['dur']:.2f} s, after the reel ({reel_info['duration']:.2f} s) — re-render")
        clips.append({"kind": "full-frame", "scene": slot["id"], "n": n, "t_in": row["t_in"],
                      "frames": round(slot["dur"] * fps), "src_start": slot["start"], "title": _title(row["words"]),
                      "file": f"scene-{n:02d}_{tc_file(row['t_in'], fps)}.mp4"})
    movs = sorted(Path(overlays_dir).glob("*.mov")) if overlays_dir else []
    if len(movs) != len(over):
        raise SliceError(f"storyboard.md has {len(over)} over-footage rows but "
                         f"{overlays_dir or '(no --overlays dir)'} has {len(movs)} .mov files")
    for n, (mov, row) in enumerate(zip(movs, over), 1):
        info = media.video_info(mov)
        _check_size(mov.name, info)
        if info["codec"] != "prores" or "4444" not in str(info["profile"]) or not str(info["pix_fmt"]).startswith("yuva"):
            raise SliceError(f"{mov.name} is {info['codec']} {info['profile']} {info['pix_fmt']}, not ProRes 4444 with alpha "
                             "— render it with npx hyperframes render --format=mov")
        if abs(info["fps"] - fps) > 0.01:
            raise SliceError(f"{mov.name} runs at {info['fps']:g} fps but --fps is {fps:g}")
        want = row["t_out"] - row["t_in"]
        if abs(info["duration"] - want) > tol:
            raise SliceError(f"{mov.name} lasts {info['duration']:.2f} s but storyboard row {row['row']} "
                             f"(line {row['line']}) lasts {want:.2f} s")
        clips.append({"kind": "over-footage", "scene": mov.stem, "n": n, "t_in": row["t_in"],
                      "frames": round(info["duration"] * fps), "src": mov, "title": _title(row["words"]),
                      "file": f"overlay-{n:02d}_{tc_file(row['t_in'], fps)}.mov"})
    return clips


def _cut(reel, clip, out, fps):
    start = round(clip["src_start"] * fps) / fps
    media.run([media.tool("ffmpeg"), "-nostdin", "-v", "error", "-y", "-ss", f"{start:.6f}", "-i", str(reel),
                "-frames:v", str(clip["frames"]), "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "14",
                "-pix_fmt", "yuv420p", "-r", f"{fps:g}", "-movflags", "+faststart", str(out)])
    got = media.video_info(out)["frames"]
    if got != clip["frames"]:
        raise SliceError(f"{clip['file']} has {got} frames, expected {clip['frames']} — the reel is shorter than its slot; re-render")


def _readme(slug, clips, fps):
    full = [c for c in clips if c["kind"] == "full-frame"]
    over = [c for c in clips if c["kind"] == "over-footage"]
    example = (f"      {full[0]['file']}  ->  drop at {tc(full[0]['t_in'], fps)}\n" if full else "")
    return (f"{slug} — graphics for the basic-edit timeline\n"
            f"{len(full)} full-screen scene clip(s), {len(over)} over-footage layout(s).\n\n"
            "HOW TO USE\n"
            "  Each file is named with the timecode it goes at on your basic-edit timeline:\n"
            f"{example}"
            "  scene-*.mp4: full-screen graphics, silent, hard cut in and out. Drop each on a video track\n"
            "  above the talking head at its timecode. Keep your edit audio underneath.\n"
            "  overlay-*.mov: ProRes 4444 with alpha. Place above the talking head at its timecode; the\n"
            "  footage shows through everywhere outside the layout.\n\n"
            "  TIMECODES.csv has the same information for every clip: in/out timecode, in/out frame,\n"
            f"  duration and frame count ({fps:g} fps).\n")


def slice_project(project, reel, overlays_dir=None, out_dir=None, fps=30.0) -> list:
    project = Path(project)
    clips = plan(project, reel, overlays_dir, fps)
    out = Path(out_dir) if out_dir else project / "deliver"
    out.mkdir(parents=True, exist_ok=True)
    tmp = out / ".slice-tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir()
    try:
        rows = []
        for c in clips:
            if c["kind"] == "full-frame":
                _cut(reel, c, tmp / c["file"], fps)
            else:
                shutil.copyfile(c["src"], tmp / c["file"])
            in_f = round(c["t_in"] * fps)
            out_f = in_f + c["frames"]
            rows.append({"kind": c["kind"], "scene": c["scene"], "file": c["file"], "timeline_in_tc": tc(c["t_in"], fps),
                         "timeline_out_tc": tc(out_f / fps, fps), "timeline_in_s": f"{c['t_in']:.2f}",
                         "timeline_out_s": f"{out_f / fps:.2f}", "in_frame": in_f, "out_frame": out_f,
                         "duration_s": f"{c['frames'] / fps:.2f}", "frames": c["frames"], "title": c["title"]})
        with open(tmp / "TIMECODES.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS)
            w.writeheader()
            w.writerows(rows)
        (tmp / "README.txt").write_text(_readme(project.name, clips, fps))
        # everything succeeded: only now replace the old delivery (slice owns these names)
        for old in list(out.glob("scene-*.mp4")) + list(out.glob("overlay-*.mov")):
            old.unlink()
        for new in tmp.iterdir():
            new.replace(out / new.name)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return rows


def main(argv) -> int:
    ap = argparse.ArgumentParser(prog="python3 tools/slice.py")
    ap.add_argument("project")
    ap.add_argument("--reel", required=True)
    ap.add_argument("--overlays")
    ap.add_argument("--out")
    ap.add_argument("--fps", type=float, default=30.0)
    a = ap.parse_args(argv[1:])
    try:
        rows = slice_project(a.project, a.reel, a.overlays, a.out, a.fps)
    except (SliceError, pj.ProjectError, media.MediaError) as e:
        print(e)
        return 1
    for r in rows:
        print(f"{r['file']:<28} -> timeline {r['timeline_in_tc']}  ({r['frames']} frames)")
    print(f"{len(rows)} clips + TIMECODES.csv + README.txt -> {a.out or Path(a.project) / 'deliver'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
