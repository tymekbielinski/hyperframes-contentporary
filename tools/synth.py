"""Synthetic test videos for the media-tool tests (ffmpeg lavfi sources — never real footage)."""
import shutil
import subprocess

HAVE_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


def _ffmpeg(args):
    subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-y", *args], check=True)


def segments(path, parts, size=(160, 90), fps=30, noise=False):
    """Concatenate solid-colour segments: parts = [("0x808080", 2.0), ("navy", 1.5), ...].
    noise=True adds light temporal grain (deterministic seed) so frames are not bit-identical."""
    w, h = size
    args, labels = [], ""
    for i, (colour, secs) in enumerate(parts):
        args += ["-f", "lavfi", "-i", f"color=c={colour}:s={w}x{h}:r={fps}:d={secs}"]
        labels += f"[{i}:v]"
    chain = f"{labels}concat=n={len(parts)}:v=1:a=0"
    if noise:
        chain += ",noise=alls=6:allf=t:all_seed=7"
    _ffmpeg(args + ["-filter_complex", chain, "-pix_fmt", "yuv420p", "-r", str(fps), str(path)])
    return path


def moving(path, secs, size=(160, 90), fps=30, glitch_frame=None):
    """testsrc2 (smooth, continuous motion); glitch_frame paints one white box on that frame only."""
    w, h = size
    vf = ["-vf", f"drawbox=x=20:y=20:w=60:h=40:color=white:t=fill:enable='eq(n,{glitch_frame})'"] if glitch_frame else []
    _ffmpeg(["-f", "lavfi", "-i", f"testsrc2=s={w}x{h}:r={fps}:d={secs}", *vf, "-pix_fmt", "yuv420p", str(path)])
    return path


def moving_then_still(path, moving_secs, still_secs, size=(160, 90), fps=30, glitch_frame=None):
    """testsrc2 motion, then its last frame held for still_secs — for the settle-before-cut check.
    glitch_frame paints one white box on that frame only (a render flicker)."""
    w, h = size
    vf = f"tpad=stop_mode=clone:stop_duration={still_secs}"
    if glitch_frame:
        vf = f"drawbox=x=20:y=20:w=60:h=40:color=white:t=fill:enable='eq(n,{glitch_frame})'," + vf
    _ffmpeg(["-f", "lavfi", "-i", f"testsrc2=s={w}x{h}:r={fps}:d={moving_secs}",
             "-vf", vf, "-pix_fmt", "yuv420p", str(path)])
    return path


def prores(path, secs, size=(160, 90), fps=30, alpha=True):
    """A ProRes clip: 4444 with alpha (what `hyperframes render --format=mov` delivers) or 422 HQ without."""
    w, h = size
    src = f"color=c=red@0.5:s={w}x{h}:r={fps}:d={secs},format=rgba"   # format in the source keeps the alpha
    codec = ["-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le"] if alpha else \
            ["-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le"]
    _ffmpeg(["-f", "lavfi", "-i", src, *codec, str(path)])
    return path


def concat(path, parts, fps=30):
    """Concatenate existing clips (same size) back to back."""
    args, labels = [], ""
    for i, p in enumerate(parts):
        args += ["-i", str(p)]
        labels += f"[{i}:v]"
    _ffmpeg(args + ["-filter_complex", f"{labels}concat=n={len(parts)}:v=1:a=0", "-pix_fmt", "yuv420p",
                    "-r", str(fps), str(path)])
    return path
