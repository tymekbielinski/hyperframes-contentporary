"""Runtime view of a composition for QA checks 5, 6 and 10: serve it with `npx hyperframes preview`
(HyperFrames' own bundler + runtime) and probe it in headless Chrome with tools/qa_probe.mjs.

Chrome: $HF_CHROME, else the chrome-headless-shell HyperFrames downloads for rendering
(~/.cache/puppeteer/chrome-headless-shell/...), else `npx hyperframes browser path`.
"""
import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tools" / "qa_probe.mjs"


class ProbeError(Exception):
    """The page could not be probed (no Chrome, preview failed, page never registered a timeline)."""


def hyperframes_cmd() -> list:
    """The HyperFrames CLI prefix; $HF_CLI overrides it (e.g. a pinned version, or a test stub)."""
    return shlex.split(os.environ.get("HF_CLI", "npx --yes hyperframes"))


def _run(cmd, timeout_s):
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


def find_chrome(allow_npx=True):
    env = os.environ.get("HF_CHROME")
    if env:
        return env if Path(env).is_file() else None
    cache = Path.home() / ".cache" / "puppeteer" / "chrome-headless-shell"
    found = sorted(cache.glob("*/*/chrome-headless-shell")) + sorted(cache.glob("*/*/chrome-headless-shell.exe"))
    if found:
        return str(found[-1])
    if allow_npx:
        try:
            r = _run(hyperframes_cmd() + ["browser", "path"], 120)
        except ProbeError:
            return None
        lines = [l.strip() for l in r.stdout.splitlines() if l.strip()]
        if r.returncode == 0 and lines and Path(lines[-1]).is_file():
            return lines[-1]
    return None


def probe_url(url, fmt, size, chrome=None, samples=24, timeout_ms=30000) -> dict:
    node = shutil.which("node")
    chrome = chrome or find_chrome()
    if not node or not chrome:
        raise ProbeError("runtime probe needs node ≥ 22 and Chrome (set HF_CHROME or run: npx hyperframes browser ensure)")
    # qa_probe ends itself after 2 × timeout + 30 s; this is the outer backstop.
    r = _run([node, str(PROBE), "--url", url, "--format", fmt, "--chrome", chrome,
              "--width", str(size[0]), "--height", str(size[1]), "--samples", str(samples),
              "--timeout", str(timeout_ms)], 2 * timeout_ms / 1000 + 45)
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


def probe_project(project, fmt, size, port=3930, **kw) -> dict:
    """Start (or reuse) the project's background preview, probe it, stop it if this call started it."""
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
