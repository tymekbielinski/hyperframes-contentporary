"""ffmpeg / ffprobe helpers shared by the media tools (probe_cuts, scan_flicker, cadence_scan, slice,
qa, preview_pack). Standard library only; every measurement is done by ffmpeg filters so long videos
stay fast without numpy.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path


class MediaError(Exception):
    """ffmpeg/ffprobe missing, a file that is not there, or a command that failed (stderr included)."""


def tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise MediaError(f"{name} not found — install ffmpeg (it provides ffmpeg and ffprobe)")
    return path


def run(args, binary=False):
    r = subprocess.run(args, capture_output=True, text=not binary)
    if r.returncode != 0:
        err = r.stderr.decode(errors="replace") if binary else r.stderr
        raise MediaError(f"{Path(args[0]).name} failed ({r.returncode}): {err.strip()[-800:]}")
    return r.stdout


def _need(path) -> str:
    if not Path(path).is_file():
        raise MediaError(f"{path} not found")
    return str(path)


def video_info(path) -> dict:
    """{"duration", "width", "height", "fps", "codec", "profile", "pix_fmt", "frames"} of the first video stream."""
    out = run([tool("ffprobe"), "-v", "error", "-select_streams", "v:0", "-count_packets",
                "-show_entries", "format=duration:stream=codec_name,profile,pix_fmt,width,height,r_frame_rate,avg_frame_rate,nb_read_packets",
                "-of", "json", _need(path)])
    return _parse_info(path, json.loads(out))


def _rate(text) -> float:
    num, _, den = (text or "0/0").partition("/")
    try:
        return float(num) / float(den or 1)
    except (ValueError, ZeroDivisionError):
        return 0.0


def _parse_info(path, data) -> dict:
    if not data.get("streams"):
        raise MediaError(f"{path} has no video stream")
    s = data["streams"][0]
    fps = _rate(s.get("r_frame_rate")) or _rate(s.get("avg_frame_rate"))
    if not fps:
        raise MediaError(f"{path}: cannot determine the frame rate (r_frame_rate {s.get('r_frame_rate')!r})")
    try:
        duration = float(data.get("format", {}).get("duration", 0.0))
    except (TypeError, ValueError):
        raise MediaError(f"{path}: unknown duration ({data.get('format', {}).get('duration')!r})")
    return {"duration": duration, "width": int(s["width"]), "height": int(s["height"]), "fps": fps,
            "codec": s.get("codec_name"), "profile": s.get("profile"), "pix_fmt": s.get("pix_fmt"),
            "frames": int(s.get("nb_read_packets", 0))}


def _metadata_values(text: str, key: str) -> list:
    return [float(v) for v in re.findall(re.escape(key) + r"=([-\d.]+)", text)]


def frame_diffs(path, size=(320, 180)) -> list:
    """Mean absolute luma difference (0–255) between consecutive frames: d[i] = |frame i+1 − frame i|."""
    w, h = size
    out = run([tool("ffmpeg"), "-v", "error", "-nostdin", "-i", _need(path), "-an", "-vf",
                f"scale={w}:{h},format=gray,tblend=all_mode=difference,signalstats,"
                "metadata=print:key=lavfi.signalstats.YAVG:file=-", "-f", "null", "-"])
    return _metadata_values(out, "lavfi.signalstats.YAVG")


def gray_frames(path, fps: float, size=(32, 18)) -> list:
    """Frames sampled at `fps`, downscaled to `size`, as bytes of 8-bit luma (one bytes object per frame)."""
    w, h = size
    raw = run([tool("ffmpeg"), "-v", "error", "-nostdin", "-i", _need(path), "-an", "-vf",
                f"fps={fps},scale={w}:{h},format=gray", "-f", "rawvideo", "-"], binary=True)
    n = w * h
    return [raw[i:i + n] for i in range(0, len(raw) - n + 1, n)]


def scene_cuts(path, threshold: float = 0.20) -> list:
    """Source cut times (s): frames whose ffmpeg scene score exceeds `threshold` (shorts.md §1 uses 0.20)."""
    out = run([tool("ffmpeg"), "-v", "error", "-nostdin", "-i", _need(path), "-an", "-filter_complex",
                f"select='gt(scene,{threshold})',metadata=print:file=-", "-f", "null", "-"])
    return [round(float(t), 3) for t in re.findall(r"pts_time:([\d.]+)", out)]


def extract_frame(path, t: float, out_png, width: int = 480, background=None) -> Path:
    """Write the frame at time t, scaled to `width`, to out_png as 8-bit RGB. With `background`
    (an ffmpeg colour) a clip with alpha is composited over it first, so transparency stays visible."""
    src = [tool("ffmpeg"), "-v", "error", "-nostdin", "-y", "-ss", f"{max(t, 0):.3f}", "-i", _need(path)]
    if background is None:
        graph = f"scale={width}:-2,format=rgb24"
    else:   # the backdrop is painted from the same frame, so both overlay inputs share one timestamp
        graph = (f"scale={width}:-2,format=rgba,split[fg][s];[s]drawbox=x=0:y=0:w=iw:h=ih:color={background}@1:t=fill[bg];"
                 "[bg][fg]overlay=format=auto,format=rgb24")
    run(src + ["-filter_complex", graph, "-frames:v", "1", str(out_png)])
    if not Path(out_png).is_file():
        raise MediaError(f"no frame at t={t:.3f}s in {path}")
    return Path(out_png)
