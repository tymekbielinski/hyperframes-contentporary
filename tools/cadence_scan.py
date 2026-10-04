"""Graphics density — standards/core/qa.md check 8 — on the plan and on the edit.

  python3 tools/cadence_scan.py videos/<slug>                 plan: the storyboard.md beat grid
  python3 tools/cadence_scan.py videos/<slug> --edit CUT.mp4  edit: full-frame graphics measured on the
                                                             edited timeline + over-footage grid rows
  options: --duration S (default: transcript.json) · --face-ref T · --threshold D · --json

Rules (standards/formats/long-form.md, shorts.md):
  long-form  hook (first hook_end s, default 80) ≥ 60 % full-frame graphics, no face-only gap > 6 s;
             body: a graphic (full-frame or over-footage) at least every 30 s; BRIEF screen_share
             ranges are exempt; face punch-ins are not graphics.
  shorts     full-frame graphics 35–55 % of the runtime.
Over-footage layouts leave the face on screen, so they do not count toward the hook share or the
hook face gaps; they do reset the 30 s body clock.

Edit measurement: frames sampled at 5 fps, 32×18 luma. The reference is the per-pixel median frame
(the talking head dominates any edit), or the frame at --face-ref. A frame whose mean distance from
the reference exceeds the threshold (Otsu over all distances, never below 12) is a graphic.
"""
import argparse
import json
import statistics
import sys
from pathlib import Path

import media
import project as pj

HOOK_MIN, HOOK_GAP, BODY_GAP = 0.60, 6.0, 30.0
SHORTS_BAND = (0.35, 0.55)
EDIT_FPS, MIN_DIST = 5, 12.0
GRID_MARGIN, MIN_FACE_FRAMES = 0.5, 5
EPS = 1e-6          # summed float intervals: a hook of exactly 60 % must pass


def merge(intervals) -> list:
    out = []
    for a, b in sorted((float(a), float(b)) for a, b in intervals if b > a):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [tuple(x) for x in out]


def coverage(intervals, a, b) -> float:
    return sum(max(0.0, min(y, b) - max(x, a)) for x, y in merge(intervals))


def gaps(intervals, a, b) -> list:
    """Uncovered stretches of [a, b], in order."""
    out, cur = [], a
    for x, y in merge(intervals):
        if y <= a or x >= b:
            continue
        if x > cur:
            out.append((cur, x))
        cur = max(cur, y)
    if cur < b:
        out.append((cur, b))
    return out


def _result(name, ok, value, detail):
    return {"name": name, "ok": bool(ok), "value": value, "detail": detail}


def evaluate(fmt, full_frame, duration, hook_end=pj.DEFAULT_HOOK_END, screen_share=(), other=()) -> list:
    """Density results for one timeline. full_frame/other/screen_share are [(start, end)] seconds."""
    if duration <= 0:
        raise ValueError("duration must be positive")
    if fmt == "shorts":
        share = coverage(full_frame, 0, duration) / duration
        lo, hi = SHORTS_BAND
        return [_result("full-frame share 35–55 %", lo - EPS <= share <= hi + EPS, round(share, 4),
                        f"{share:.1%} of {duration:.1f} s")]
    hook = min(hook_end, duration)
    share = coverage(full_frame, 0, hook) / hook
    hook_gaps = gaps(full_frame, 0, hook)
    longest = max((b - a for a, b in hook_gaps), default=0.0)
    over = [f"{a:.1f}–{b:.1f}" for a, b in hook_gaps if b - a > HOOK_GAP + EPS]
    covered = list(full_frame) + list(other) + list(screen_share)
    body_gaps = gaps(covered, hook, duration) if duration > hook else []
    body_longest = max((b - a for a, b in body_gaps), default=0.0)
    body_over = [f"{a:.1f}–{b:.1f}" for a, b in body_gaps if b - a > BODY_GAP + EPS]
    return [
        _result("hook graphics ≥ 60 %", share >= HOOK_MIN - EPS, round(share, 4), f"{share:.1%} of 0–{hook:g} s"),
        _result("hook face gaps ≤ 6 s", longest <= HOOK_GAP + EPS, round(longest, 2),
                f"longest {longest:.1f} s" + (f" ({', '.join(over)})" if over else "")),
        _result("body cadence ≤ 30 s", body_longest <= BODY_GAP + EPS, round(body_longest, 2),
                f"longest {body_longest:.1f} s" + (f" ({', '.join(body_over)})" if body_over else "")
                + (" · screen_share exempt" if screen_share else "")),
    ]


# ---------------------------------------------------------------- edit measurement

def otsu(values) -> float:
    hist = [0] * 256
    for v in values:
        hist[min(255, max(0, int(round(v))))] += 1
    total, sum_all = len(values), sum(i * h for i, h in enumerate(hist))
    best, cut, w0, sum0 = -1.0, 0, 0, 0.0
    for t in range(256):
        w0 += hist[t]
        if w0 == 0 or w0 == total:
            continue
        sum0 += t * hist[t]
        m0, m1 = sum0 / w0, (sum_all - sum0) / (total - w0)
        between = w0 * (total - w0) * (m0 - m1) ** 2
        if between > best:
            best, cut = between, t
    return cut + 0.5


def subtract(intervals, cut) -> list:
    """Parts of `intervals` not covered by `cut`."""
    out = []
    for a, b in merge(intervals):
        out.extend(gaps(cut, a, b))
    return out


def face_distances_ex(video, fps=EDIT_FPS, face_ref=None, grid=()):
    """(distances, reference kind): "face-ref" > "grid" (frames outside every grid row ± 0.5 s) > "median"."""
    frames = media.gray_frames(video, fps)
    if not frames:
        raise media.MediaError(f"{video}: no frames decoded")
    kind = "median"
    if face_ref is not None:
        k = min(len(frames) - 1, max(0, int(round(face_ref * fps))))
        ref, kind = list(frames[k]), "face-ref"
    else:
        faces = []
        if grid:
            faces = [f for i, f in enumerate(frames)
                     if all(not (a - GRID_MARGIN <= i / fps <= b + GRID_MARGIN) for a, b in grid)]
        if len(faces) >= MIN_FACE_FRAMES:
            frames_for_ref, kind = faces, "grid"
        else:
            frames_for_ref = frames
        ref = [statistics.median(f[p] for f in frames_for_ref) for p in range(len(frames[0]))]
    n = len(ref)
    return [sum(abs(f[p] - ref[p]) for p in range(n)) / n for f in frames], kind


def face_distances(video, fps=EDIT_FPS, face_ref=None, grid=()) -> list:
    return face_distances_ex(video, fps, face_ref, grid)[0]


def graphic_intervals(distances, fps=EDIT_FPS, threshold=None) -> list:
    """Runs of samples whose distance exceeds the threshold, as [(start, end)] seconds."""
    t = threshold if threshold is not None else max(otsu(distances), MIN_DIST)
    out, start = [], None
    for i, d in enumerate(distances + [-1.0]):
        if d > t and start is None:
            start = i
        elif d <= t and start is not None:
            out.append((round(start / fps, 3), round(i / fps, 3)))
            start = None
    return out


# ---------------------------------------------------------------- reports

def report(project, edit=None, duration=None, face_ref=None, threshold=None) -> dict:
    project = Path(project)
    brief = pj.read_brief(project)
    fmt = brief.get("format")
    if fmt not in pj.FORMATS:
        raise pj.ProjectError(f"BRIEF format must be long-form or shorts, got {fmt!r}")
    rows = pj.read_storyboard(project)
    warnings, reference = [], None
    other = [(r["t_in"], r["t_out"]) for r in rows if r["placement"] == "over-footage"]
    if edit:
        grid = [(r["t_in"], r["t_out"]) for r in rows]
        dist, reference = face_distances_ex(edit, face_ref=face_ref, grid=grid)
        # over-footage rows keep the face on screen: never full-frame graphics
        full = subtract(graphic_intervals(dist, threshold=threshold), other)
        duration = duration or media.video_info(edit)["duration"]
        source = f"edit: {edit}"
        if reference == "median":
            warnings.append("face reference = median of all frames — unreliable if graphics exceed 50 % of the "
                            "edit; pass --face-ref or a storyboard")
        if not full:
            warnings.append("detected graphic share is 0 % — likely an all-graphic or all-face edit")
    else:
        full = [(r["t_in"], r["t_out"]) for r in rows if r["placement"] == "full-frame"]
        duration = duration or pj.transcript_duration(project)
        source = "plan: storyboard.md"
    if not duration:
        raise pj.ProjectError("no runtime: pass --duration or add transcript.json")
    share = pj.screen_share(brief) if fmt == "long-form" else []
    results = evaluate(fmt, full, duration, pj.hook_end(brief), share, other if fmt == "long-form" else ())
    return {"format": fmt, "source": source, "duration": duration, "hook_end": pj.hook_end(brief),
            "full_frame": merge(full), "over_footage": merge(other), "screen_share": share,
            "results": results, "warnings": warnings, "reference": reference, "ok": all(r["ok"] for r in results)}


def format_report(r) -> str:
    lines = [f"density ({r['format']}, {r['source']}, {r['duration']:.1f} s)"]
    for x in r["results"]:
        lines.append(f"  {'PASS' if x['ok'] else 'FAIL'}  {x['name']:<26} {x['detail']}")
    lines += [f"  WARN  {w}" for w in r.get("warnings", [])]
    return "\n".join(lines)


def main(argv) -> int:
    ap = argparse.ArgumentParser(prog="python3 tools/cadence_scan.py")
    ap.add_argument("project")
    ap.add_argument("--edit")
    ap.add_argument("--duration", type=float)
    ap.add_argument("--face-ref", type=float)
    ap.add_argument("--threshold", type=float)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv[1:])
    try:
        r = report(a.project, a.edit, a.duration, a.face_ref, a.threshold)
    except (pj.ProjectError, media.MediaError, ValueError) as e:
        print(e)
        return 2
    print(json.dumps(r) if a.json else format_report(r))
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
