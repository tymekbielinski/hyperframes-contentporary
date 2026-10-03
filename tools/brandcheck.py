"""Validate brand folders (brands/<name>/) and the per-video choices a BRIEF makes.

Spec: docs/superpowers/specs/2026-10-03-animation-workflow-design.md section 7.
Usage: python3 tools/brandcheck.py brands/<name>
"""
import json
import re
import sys
from pathlib import Path

PALETTE_ROLES = {
    "ground": ["deep", "centre", "grid", "dots"],
    "surface": ["fill", "fillAlt", "bevel", "halo"],
    "text": ["primary", "secondary"],
    "accent": ["block", "text", "glow", "line"],
    "accentScript": None,
    "status": ["ok", "x"],
}
KIT_COMPONENTS = ["title", "subtitle", "lower-third", "side-text", "cta-youtube", "roadmap"]
KNOWN_MARKS = [
    "highlight-block", "scribble-underline", "underline", "curved-arrow", "connector",
    "status-chip", "script-word", "strike", "ring", "group-outline", "tool-chip",
]
STATUSES = ("draft", "approved")

_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
_RGBA = re.compile(r"^rgba\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*(0|1|0?\.\d+)\s*\)$")


def is_colour(value) -> bool:
    return isinstance(value, str) and bool(_HEX.match(value) or _RGBA.match(value))


def _role_paths():
    for role, subs in PALETTE_ROLES.items():
        if subs is None:
            yield role, (role,)
        else:
            for sub in subs:
                yield f"{role}.{sub}", (role, sub)


def _get(data, keys):
    cur = data
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return None, False
        cur = cur[k]
    return cur, True


def validate_palette(data: dict, label: str) -> list:
    errors = []
    for path, keys in _role_paths():
        value, found = _get(data, keys)
        if not found:
            errors.append(f"{label}: missing {path}")
        elif not is_colour(value):
            errors.append(f"{label}: {path} is not a colour: {value!r}")
    for key, value in (data.get("extras") or {}).items():
        if not is_colour(value):
            errors.append(f"{label}: extras.{key} is not a colour: {value!r}")
    return errors


def load_brand(brand_dir: Path) -> dict:
    brand_dir = Path(brand_dir)
    tokens = json.loads((brand_dir / "tokens.json").read_text())
    palettes = {}
    for name in tokens.get("palettes", []):
        f = brand_dir / "palettes" / f"{name}.json"
        if f.is_file():
            palettes[name] = json.loads(f.read_text())
    return {"tokens": tokens, "palettes": palettes}


def validate_brand(brand_dir: Path) -> list:
    brand_dir = Path(brand_dir)
    folder = brand_dir.name
    if not (brand_dir / "tokens.json").is_file():
        return [f"{folder}: missing tokens.json"]
    brand = load_brand(brand_dir)
    t = brand["tokens"]
    errors = []

    if t.get("name") != folder:
        errors.append(f"{folder}: tokens.name {t.get('name')!r} does not match folder name")
    if t.get("status") not in STATUSES:
        errors.append(f"{folder}: status must be 'draft' or 'approved', got {t.get('status')!r}")

    listed = t.get("palettes") or []
    if not listed:
        errors.append(f"{folder}: palettes must list at least one palette")
    for name in listed:
        if name not in brand["palettes"]:
            errors.append(f"{folder}: palette {name!r} listed but palettes/{name}.json missing")
        else:
            errors += validate_palette(brand["palettes"][name], f"{folder}/palettes/{name}.json")
    if t.get("defaultPalette") not in listed:
        errors.append(f"{folder}: defaultPalette {t.get('defaultPalette')!r} not in palettes")

    fonts = t.get("fonts") or {}
    headline = fonts.get("headline") or {}
    if not headline:
        errors.append(f"{folder}: fonts.headline must define at least one font")
    for key, spec in headline.items():
        for field in ("family", "weight", "source"):
            if field not in spec:
                errors.append(f"{folder}: fonts.headline.{key} missing {field}")
    if fonts.get("defaultHeadline") not in headline:
        errors.append(
            f"{folder}: fonts.defaultHeadline {fonts.get('defaultHeadline')!r} not in fonts.headline")
    for role, fields in (("body", ("family", "weight", "source")), ("script", ("family", "source"))):
        spec = fonts.get(role)
        if not isinstance(spec, dict):
            errors.append(f"{folder}: fonts.{role} missing")
            continue
        for field in fields:
            if field not in spec:
                errors.append(f"{folder}: fonts.{role} missing {field}")

    kit = t.get("kit") or {}
    for comp in KIT_COMPONENTS:
        if not isinstance(kit.get(comp), str) or not kit.get(comp):
            errors.append(f"{folder}: kit missing component {comp!r}")

    marks = t.get("marks") or []
    if not marks:
        errors.append(f"{folder}: marks must list at least one mark")
    for m in marks:
        if m not in KNOWN_MARKS:
            errors.append(f"{folder}: unknown mark {m!r}")
    return errors


def validate_choice(brand_dir: Path, palette: str, font=None, overrides=None) -> list:
    brand_dir = Path(brand_dir)
    brand = load_brand(brand_dir)
    t = brand["tokens"]
    name = t.get("name", brand_dir.name)
    errors = []
    if t.get("status") != "approved":
        errors.append(f"brand {name} is not approved (status: {t.get('status')})")
    listed = t.get("palettes") or []
    if palette not in listed:
        errors.append(f"palette {palette!r} not in brand {name} (have: {', '.join(listed)})")
    headline = (t.get("fonts") or {}).get("headline") or {}
    if font is not None and font not in headline:
        errors.append(f"font {font!r} not in brand {name} (have: {', '.join(headline)})")
    valid_paths = {p for p, _ in _role_paths()}
    for path, value in (overrides or {}).items():
        if path not in valid_paths:
            errors.append(f"override {path!r} is not a palette role")
        elif not is_colour(value):
            errors.append(f"override {path!r} is not a colour: {value!r}")
    return errors


def main(argv) -> int:
    if len(argv) != 2:
        print("usage: python3 tools/brandcheck.py brands/<name>")
        return 2
    brand_dir = Path(argv[1])
    errors = validate_brand(brand_dir)
    for e in errors:
        print(e)
    if errors:
        return 1
    t = load_brand(brand_dir)["tokens"]
    print(f"OK {t['name']} ({t['status']})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
