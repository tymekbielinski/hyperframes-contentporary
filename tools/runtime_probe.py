"""Runtime view of a composition for QA checks 5, 6 and 10: serve it with `npx hyperframes preview`
(HyperFrames' own bundler + runtime) and probe it in headless Chrome with tools/qa_probe.mjs.

Chrome: $HF_CHROME, else the chrome-headless-shell HyperFrames downloads for rendering
(~/.cache/puppeteer/chrome-headless-shell/...), else `npx hyperframes browser path`.
"""
import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tools" / "qa_probe.mjs"


class ProbeError(Exception):
    """The page could not be probed (no Chrome, preview failed, page never registered a timeline)."""


def hyperframes_cmd() -> list:
    """The HyperFrames CLI prefix; $HF_CLI overrides it (e.g. a pinned version, or a test stub)."""
    return shlex.split(os.environ.get("HF_CLI", "npx --yes hyperframes"))


def find_chrome(allow_npx=True):
    env = os.environ.get("HF_CHROME")
    if env:
        return env if Path(env).is_file() else None
    cache = Path.home() / ".cache" / "puppeteer" / "chrome-headless-shell"
    found = sorted(cache.glob("*/*/chrome-headless-shell")) + sorted(cache.glob("*/*/chrome-headless-shell.exe"))
    if found:
        return str(found[-1])
    if allow_npx:
        r = subprocess.run(hyperframes_cmd() + ["browser", "path"], capture_output=True, text=True)
        lines = [l.strip() for l in r.stdout.splitlines() if l.strip()]
        if r.returncode == 0 and lines and Path(lines[-1]).is_file():
            return lines[-1]
    return None


def probe_url(url, fmt, size, chrome=None, samples=24, timeout_ms=30000) -> dict:
    node = shutil.which("node")
    chrome = chrome or find_chrome()
    if not node or not chrome:
        raise ProbeError("runtime probe needs node ≥ 22 and Chrome (set HF_CHROME or run: npx hyperframes browser ensure)")
    r = subprocess.run([node, str(PROBE), "--url", url, "--format", fmt, "--chrome", chrome,
                        "--width", str(size[0]), "--height", str(size[1]), "--samples", str(samples),
                        "--timeout", str(timeout_ms)], capture_output=True, text=True)
    if r.returncode != 0:
        raise ProbeError((r.stderr or r.stdout).strip() or f"qa_probe exited {r.returncode}")
    return json.loads(r.stdout)


def probe_project(project, fmt, size, port=3930, **kw) -> dict:
    """Start (or reuse) the project's background preview, probe it, stop it if this call started it."""
    project = Path(project).resolve()
    hf = hyperframes_cmd()
    r = subprocess.run(hf + ["preview", str(project), "--background", "--no-open", "--port", str(port), "--json"],
                       capture_output=True, text=True)
    try:
        start = json.loads(r.stdout.strip().splitlines()[-1])["result"]
        url = f"{start['serverUrl']}/api/projects/{start['projectName']}/preview"
    except (ValueError, KeyError, IndexError):
        raise ProbeError("npx hyperframes preview did not start: " + (r.stderr or r.stdout).strip()[-600:])
    try:
        return probe_url(url, fmt, size, **kw)
    finally:
        if start.get("state") == "started":
            subprocess.run(hf + ["preview", str(project), "--stop", "--json"], capture_output=True, text=True)
