"""Read a video project's files: BRIEF.md, storyboard.md (beat grid), index.html slots, transcript.json.

Field rules: standards/core/pipeline.md (BRIEF fields, beat grid) and standards/core/qa.md check 3.
Standard library only — the BRIEF's YAML is a small subset parsed here (no PyYAML).
"""
import json
import re
from pathlib import Path

import brandcheck

ROOT = Path(__file__).resolve().parents[1]
FORMATS = ("long-form", "shorts")
PLACEMENTS = ("full-frame", "over-footage")
GRID_COLUMNS = ["t_in", "t_out", "words", "placement", "type", "beats", "ease", "marks"]
REASON_HINT = "each entry is '<what>: <reason>'"
FIELDS = {"format", "film", "direction", "references", "gotchas", "brand", "palette", "font",
          "overrides", "captions", "hook_end", "screen_share", "exceptions", "source"}
DEFAULT_HOOK_END = 80.0


class ProjectError(Exception):
    """A project file that is missing or cannot be parsed. The message names the file and line."""


# ---------------------------------------------------------------- YAML subset (the BRIEF block)

def _strip_comment(s: str) -> str:
    q = None
    for i, c in enumerate(s):
        if q:
            if c == q:
                q = None
        elif c in "\"'":
            q = c
        elif c == "#" and (i == 0 or s[i - 1] in " \t"):
            return s[:i].rstrip()
    return s.rstrip()


def _scalar(s: str, where: str):
    s = s.strip()
    if s == "" or s in ("null", "~"):
        return None
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    if s[0] in "\"'":
        raise ProjectError(f"{where}: unterminated quote in {s!r}")
    if s.startswith("["):
        if not s.endswith("]"):
            raise ProjectError(f"{where}: unterminated list {s!r}")
        inner = s[1:-1].strip()
        return [_scalar(x, where) for x in inner.split(",")] if inner else []
    if s in ("true", "false"):
        return s == "true"
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        return s


def parse_yaml_subset(text: str, label: str = "BRIEF.md") -> dict:
    """`key: scalar`, `key:` + indented `- item` lines, or `key:` + indented `sub: scalar` lines.

    Scalars: quoted strings, numbers, true/false, null, flow lists `[a, b]`. `#` starts a comment
    after whitespace (quote colours: `"#BACE7A"`). Anything else raises ProjectError with the line.
    """
    out, key, line_no = {}, None, 0
    for line_no, raw in enumerate(text.splitlines(), 1):
        where = f"{label} line {line_no}"
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            raise ProjectError(f"{where}: indent with spaces, not tabs")
        line = _strip_comment(raw)
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        body = line.strip()
        if indent == 0:
            m = re.fullmatch(r"([A-Za-z_][\w.-]*)\s*:(.*)", body)
            if not m:
                raise ProjectError(f"{where}: expected 'key: value', got {body!r}")
            key = m.group(1)
            if key in out:
                raise ProjectError(f"{where}: duplicate key {key!r}")
            out[key] = _scalar(m.group(2), where)
            continue
        if key is None or (out[key] is not None and not isinstance(out[key], (list, dict))):
            raise ProjectError(f"{where}: unexpected indented line {body!r}")
        if body.startswith("- ") or body == "-":
            if out[key] is None:
                out[key] = []
            if not isinstance(out[key], list):
                raise ProjectError(f"{where}: {key} mixes list items and keys")
            out[key].append(_scalar(body[1:], where))
            continue
        m = re.fullmatch(r"([A-Za-z_][\w.-]*)\s*:(.*)", body)
        if not m:
            raise ProjectError(f"{where}: expected '- item' or 'sub: value' under {key}, got {body!r}")
        if out[key] is None:
            out[key] = {}
        if not isinstance(out[key], dict):
            raise ProjectError(f"{where}: {key} mixes list items and keys")
        out[key][m.group(1)] = _scalar(m.group(2), where)
    return out


# ---------------------------------------------------------------- BRIEF

def read_brief(project) -> dict:
    """Parse the first ```yaml block of <project>/BRIEF.md."""
    path = Path(project) / "BRIEF.md"
    if not path.is_file():
        raise ProjectError(f"{path} not found")
    text = path.read_text()
    m = re.search(r"^```ya?ml[ \t]*\n(.*?)^```", text, re.S | re.M)
    if not m:
        raise ProjectError(f"{path}: no ```yaml block (the BRIEF fields live in one fenced yaml block)")
    offset = text[: m.start(1)].count("\n")
    try:
        return parse_yaml_subset(m.group(1), "BRIEF.md")
    except ProjectError as e:
        # report file line numbers, not block line numbers
        msg = re.sub(r"BRIEF\.md line (\d+)", lambda g: f"BRIEF.md line {int(g.group(1)) + offset}", str(e))
        raise ProjectError(msg)


def _nonempty_str(v) -> bool:
    return isinstance(v, str) and v.strip() != ""


def _num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def validate_brief(brief: dict, root=ROOT) -> list:
    """QA check 3: every error that makes the BRIEF incomplete or its brand choice invalid."""
    errors = []
    for k in sorted(set(brief) - FIELDS):
        errors.append(f"unknown BRIEF field {k!r} (fields: {', '.join(sorted(FIELDS))})")
    fmt = brief.get("format")
    if fmt not in FORMATS:
        errors.append(f"format must be long-form or shorts, got {fmt!r}")
    for k, what in (("film", "one line: what the graphics must make the viewer feel or believe"),
                    ("direction", "one line of art direction")):
        if not _nonempty_str(brief.get(k)):
            errors.append(f"{k} is required ({what})")
    for k in ("brand", "palette", "font"):
        if not _nonempty_str(brief.get(k)):
            errors.append(f"{k} is required")
    for k in ("references", "gotchas"):
        v = brief.get(k)
        if v is not None and not (isinstance(v, list) and all(_nonempty_str(x) for x in v)):
            errors.append(f"{k} must be a list of strings")
    overrides = brief.get("overrides")
    if overrides is not None and not isinstance(overrides, dict):
        errors.append("overrides must be a map of palette role paths to colours")
        overrides = None
    captions = brief.get("captions")
    if fmt == "shorts" and not isinstance(captions, bool):
        errors.append("captions is required for Shorts (true or false)")
    if fmt == "long-form":
        if captions is True:
            errors.append("captions: long-form has no running captions (key-line lower thirds only)")
        hook = brief.get("hook_end")
        if hook is not None and not (_num(hook) and hook > 0):
            errors.append(f"hook_end must be a positive number of seconds, got {hook!r}")
        ranges = brief.get("screen_share")
        if ranges is not None and not isinstance(ranges, list):
            errors.append("screen_share must be a list of [start, end] ranges")
        for r in ranges if isinstance(ranges, list) else []:
            if not (isinstance(r, list) and len(r) == 2 and all(_num(x) for x in r) and r[0] < r[1]):
                errors.append(f"screen_share range {r!r} must be [start, end] seconds with start < end")
    exceptions = brief.get("exceptions")
    if exceptions is not None:
        if not isinstance(exceptions, list):
            errors.append(f"exceptions must be a list ({REASON_HINT})")
        else:
            for e in exceptions:
                if not (isinstance(e, str) and re.fullmatch(r"\s*\S[^:]*:\s*\S.*", e)):
                    errors.append(f"exception {e!r} has no reason ({REASON_HINT})")
    if _nonempty_str(brief.get("brand")) and _nonempty_str(brief.get("palette")):
        brand_dir = Path(root) / "brands" / brief["brand"]
        if not brand_dir.is_dir():
            errors.append(f"brand {brief['brand']!r}: no folder brands/{brief['brand']}/")
        else:
            errors += brandcheck.validate_brand(brand_dir)
            errors += brandcheck.validate_choice(brand_dir, brief["palette"], brief.get("font"), overrides)
    return list(dict.fromkeys(errors))


def hook_end(brief: dict) -> float:
    v = brief.get("hook_end")
    return float(v) if _num(v) else DEFAULT_HOOK_END


def screen_share(brief: dict) -> list:
    return [(float(a), float(b)) for a, b in (brief.get("screen_share") or [])]


# ---------------------------------------------------------------- storyboard (beat grid)

def _cells(line: str) -> list:
    parts = re.split(r"(?<!\\)\|", line.strip())
    return [p.strip().replace("\\|", "|") for p in parts[1:-1]]


def parse_storyboard(text: str, label: str = "storyboard.md") -> list:
    """Rows of the beat-grid table (header exactly the pipeline.md columns), in file order.

    Each row: {"row": n, "line": file line, "t_in", "t_out" (floats), and the other columns as text}.
    """
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip().startswith("|") and _cells(line) == GRID_COLUMNS:
            start = i
            break
    if start is None:
        raise ProjectError(f"{label}: no beat-grid table (header: | {' | '.join(GRID_COLUMNS)} |)")
    rows = []
    for i in range(start + 2, len(lines)):
        line = lines[i]
        if not line.strip().startswith("|"):
            break
        cells = _cells(line)
        where = f"{label} line {i + 1}"
        if len(cells) != len(GRID_COLUMNS):
            raise ProjectError(f"{where}: expected {len(GRID_COLUMNS)} cells, got {len(cells)}")
        row = dict(zip(GRID_COLUMNS, cells))
        try:
            row["t_in"], row["t_out"] = float(row["t_in"]), float(row["t_out"])
        except ValueError:
            raise ProjectError(f"{where}: t_in and t_out must be seconds, got {cells[0]!r}, {cells[1]!r}")
        if row["t_out"] <= row["t_in"]:
            raise ProjectError(f"{where}: t_out {row['t_out']} must be after t_in {row['t_in']}")
        if row["placement"] not in PLACEMENTS:
            raise ProjectError(f"{where}: placement must be full-frame or over-footage, got {row['placement']!r}")
        row["row"], row["line"] = len(rows) + 1, i + 1
        rows.append(row)
    return rows


def read_storyboard(project) -> list:
    path = Path(project) / "storyboard.md"
    if not path.is_file():
        raise ProjectError(f"{path} not found")
    return parse_storyboard(path.read_text())


# ---------------------------------------------------------------- index.html slots, transcript

def _attrs(tag: str) -> dict:
    return dict(re.findall(r'([\w:-]+)\s*=\s*"([^"]*)"', tag))


def composition_slots(project) -> list:
    """Sub-composition slots of <project>/index.html, sorted by data-start:
    [{"id", "src", "start", "dur"}]. These are the full-frame scenes of a long-form reel."""
    path = Path(project) / "index.html"
    if not path.is_file():
        raise ProjectError(f"{path} not found")
    slots = []
    for tag in re.findall(r"<[a-zA-Z][^>]*\bdata-composition-src\s*=[^>]*>", path.read_text()):
        a = _attrs(tag)
        try:
            slots.append({"id": a.get("data-composition-id") or a["data-composition-src"],
                          "src": a["data-composition-src"],
                          "start": float(a["data-start"]), "dur": float(a["data-duration"])})
        except (KeyError, ValueError):
            raise ProjectError(f"{path}: slot {tag[:80]!r} needs numeric data-start and data-duration")
    return sorted(slots, key=lambda s: s["start"])


def root_attrs(project) -> dict:
    """Attributes of the root composition element (the first tag with data-composition-id)."""
    path = Path(project) / "index.html"
    m = re.search(r"<[a-zA-Z][^>]*\bdata-composition-id\s*=[^>]*>", path.read_text()) if path.is_file() else None
    return _attrs(m.group(0)) if m else {}


def transcript_duration(project):
    """End time of the last word in <project>/transcript.json, or None if there is no transcript."""
    path = Path(project) / "transcript.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise ProjectError(f"{path} is not valid JSON ({e.msg} at line {e.lineno})")
    words = data if isinstance(data, list) else (data.get("words") or data.get("segments") or [])
    ends = [w["end"] for w in words if isinstance(w, dict) and _num(w.get("end"))]
    return max(ends) if ends else None
