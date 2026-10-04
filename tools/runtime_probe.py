"""Runtime view of a composition for QA checks 5, 6 and 10: serve it with `npx hyperframes preview`
(HyperFrames' own bundler + runtime) and probe it in headless Chrome with tools/qa_probe.mjs.

Chrome: $HF_CHROME, else the chrome-headless-shell HyperFrames downloads for rendering
(~/.cache/puppeteer/chrome-headless-shell/...), else `npx hyperframes browser path`.
"""
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tools" / "qa_probe.mjs"


class ProbeError(Exception):
    """The page could not be probed (no Chrome, preview failed, page never registered a timeline)."""


def hyperframes_cmd() -> list:
    """The HyperFrames CLI prefix; $HF_CLI overrides it (e.g. a pinned version, or a test stub)."""
    return shlex.split(os.environ.get("HF_CLI", "npx --yes hyperframes"))


def run_with_timeout(cmd, timeout_s):
    """subprocess.run with a timeout, in its own process group (the whole group is killed on timeout, so no
    Chrome is orphaned). Every failure to run or finish becomes a ProbeError."""
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    except OSError as e:
        raise ProbeError(f"cannot run {cmd[0]}: {e}")
    try:
        out, err = p.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except OSError:
            p.kill()
        p.communicate()
        raise ProbeError(f"{' '.join(str(c) for c in cmd[:3])} timed out after {timeout_s:.0f} s")
    return subprocess.CompletedProcess(cmd, p.returncode, out, err)


_run = run_with_timeout     # the original private name, kept for existing callers


def _version_key(path):
    """Natural sort key for a .../<platform>-<version>/<dir>/chrome-headless-shell path."""
    return [int(x) for x in re.findall(r"\d+", Path(path).parent.parent.name)], str(path)


def find_chrome(allow_npx=True):
    env = os.environ.get("HF_CHROME")
    if env:
        return env if Path(env).is_file() else None
    cache = Path.home() / ".cache" / "puppeteer" / "chrome-headless-shell"
    found = list(cache.glob("*/*/chrome-headless-shell")) + list(cache.glob("*/*/chrome-headless-shell.exe"))
    if found:     # newest version, compared numerically (131.0 > 99.0 > 9.0)
        return str(max(found, key=_version_key))
    if allow_npx:
        try:
            r = _run(hyperframes_cmd() + ["browser", "path"], 120)
        except ProbeError:
            return None
        lines = [l.strip() for l in r.stdout.splitlines() if l.strip()]
        if r.returncode == 0 and lines and Path(lines[-1]).is_file():
            return lines[-1]
    return None


def probe_url(url, fmt, size, chrome=None, samples=24, timeout_ms=30000, max_samples=600) -> dict:
    """Probe one page. `samples` evenly spaced seeks, plus per slot start+ε / middle / end−ε and every tween's
    start and end, capped at max_samples (the result's "samples" is the count actually seeked)."""
    node = shutil.which("node")
    chrome = chrome or find_chrome()
    if not node or not chrome:
        raise ProbeError("runtime probe needs node ≥ 22 and Chrome (set HF_CHROME or run: npx hyperframes browser ensure)")
    # qa_probe ends itself after 2 × timeout + 30 s + 0.2 s per sample; this is the outer backstop.
    r = _run([node, str(PROBE), "--url", url, "--format", fmt, "--chrome", chrome,
              "--width", str(size[0]), "--height", str(size[1]), "--samples", str(samples),
              "--max-samples", str(max_samples), "--timeout", str(timeout_ms)],
             2 * timeout_ms / 1000 + 0.2 * max_samples + 45)
    if r.returncode != 0:
        raise ProbeError((r.stderr or r.stdout).strip() or f"qa_probe exited {r.returncode}")
    try:
        out = json.loads(r.stdout)
    except ValueError:
        raise ProbeError("qa_probe printed output that is not JSON: " + r.stdout.strip()[:300])
    if not isinstance(out, dict) or not isinstance(out.get("findings"), list):
        raise ProbeError("qa_probe printed JSON without findings: " + r.stdout.strip()[:300])
    return out


def _json_result(text):
    try:
        data = json.loads(text.strip().splitlines()[-1])
        result = data["result"]
        if not isinstance(result, dict):
            raise TypeError
        return result
    except (ValueError, KeyError, IndexError, TypeError):
        return None


COMP_ROUTE = "/comp/"     # HyperFrames studio: /api/projects/<name>/preview/comp/<file> serves one composition file


def overlay_url(preview_url, rel):
    """The studio URL that serves one standalone composition file (an over-footage overlay) with the HyperFrames
    runtime, next to the project preview URL; None when preview_url is not a studio preview URL."""
    base = preview_url.split("?")[0].rstrip("/")
    if not re.search(r"/api/projects/[^/]+/preview$", base):
        return None
    return base + COMP_ROUTE + quote(Path(rel).as_posix())


def probe_overlays(preview_url, overlays, fmt, size, **kw) -> list:
    """Probe each overlay document; one entry per overlay: the probe result plus "file", or {"file", "error"}."""
    out = []
    for rel in overlays:
        url = overlay_url(preview_url, rel)
        if url is None:
            out.append({"file": rel, "error": f"cannot derive a per-file preview URL from {preview_url} "
                                              "(needs a HyperFrames studio URL ending in /api/projects/<name>/preview)"})
            continue
        try:
            out.append(dict(probe_url(url, fmt, size, **kw), file=rel))
        except ProbeError as e:
            out.append({"file": rel, "error": str(e)})
    return out


def probe_project(project, fmt, size, port=3930, overlays=(), **kw) -> dict:
    """Start (or reuse) the project's background preview, probe it — the reel, then each overlay document through
    the studio's per-file route — and stop it if this call started it. Overlay results land in "overlays"."""
    project = Path(project).resolve()
    hf = hyperframes_cmd()
    r = _run(hf + ["preview", str(project), "--background", "--no-open", "--port", str(port), "--json"], 180)
    start = _json_result(r.stdout)
    if start is None:
        raise ProbeError("npx hyperframes preview did not start: " + (r.stderr or r.stdout).strip()[-600:])
    warning = None
    try:
        try:
            url = f"{start['serverUrl']}/api/projects/{start['projectName']}/preview"
        except KeyError as e:
            raise ProbeError(f"npx hyperframes preview gave no {e} (output: {r.stdout.strip()[-300:]})")
        result = probe_url(url, fmt, size, **kw)
        if overlays:
            result["overlays"] = probe_overlays(url, overlays, fmt, size, **kw)
    finally:
        if start.get("state") == "started":
            try:
                s = _run(hf + ["preview", str(project), "--stop", "--json"], 60)
                if s.returncode != 0:
                    warning = "preview --stop failed (a preview server may still be running): " + (s.stderr or s.stdout).strip()[-300:]
            except ProbeError as e:
                warning = f"preview --stop failed (a preview server may still be running): {e}"
            if warning:
                print("runtime_probe: " + warning, file=sys.stderr)
    if warning:
        result.setdefault("warnings", []).append(warning)
    return result
