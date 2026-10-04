"""Copy the shared library into a video project and pin it with lib.lock (content hashes).

Spec section 8 (distribution) and standards/core/qa.md check 2. Projects never hand-copy lib/:
this tool copies exactly the modules listed in lib/manifest.json and records their hashes.

Usage:
  python3 tools/sync_lib.py videos/<slug>           copy root lib/ modules + write lib.lock
  python3 tools/sync_lib.py videos/<slug> --check   exit 1 (listing every problem) unless the
                                                    project's lib/ and lib.lock equal root lib/
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK_NAME = "lib.lock"
IGNORED = {".DS_Store"}


def load_manifest(root=ROOT) -> dict:
    """Return lib/manifest.json as {"modules": [...sorted], "loadOrder": [...]}; raise ValueError if malformed."""
    path = Path(root) / "lib" / "manifest.json"
    try:
        data = json.loads(path.read_text())
    except FileNotFoundError:
        raise ValueError(f"{path} not found")
    except json.JSONDecodeError as e:
        raise ValueError(f"{path} is not valid JSON ({e.msg} at line {e.lineno})")
    mods, order = data.get("modules"), data.get("loadOrder")
    for key, value in (("modules", mods), ("loadOrder", order)):
        if not isinstance(value, list) or not value or not all(isinstance(m, str) and m for m in value):
            raise ValueError(f"{path}: {key} must be a non-empty list of paths")
    if sorted(mods) != sorted(order) or len(set(mods)) != len(mods):
        raise ValueError(f"{path}: loadOrder must list exactly the modules, once each")
    return {"modules": sorted(mods), "loadOrder": list(order)}


def file_hash(path) -> str:
    return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_lock(lib_dir, modules) -> dict:
    return {"source": "lib/", "files": {m: file_hash(Path(lib_dir) / m) for m in sorted(modules)}}


def sync(project, root=ROOT) -> dict:
    """Copy every manifest module from root lib/ into <project>/lib/ and write <project>/lib.lock.

    Never deletes anything: a file in the project's lib/ that is not a manifest module stays put,
    and check() reports it.
    """
    project, root = Path(project), Path(root)
    modules = load_manifest(root)["modules"]
    src, dst = root / "lib", project / "lib"
    missing = [m for m in modules if not (src / m).is_file()]
    if missing:
        raise FileNotFoundError("root lib/ is missing manifest modules: " + ", ".join(missing))
    for m in modules:
        (dst / m).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src / m, dst / m)
    lock = build_lock(src, modules)
    (project / LOCK_NAME).write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n")
    return lock


def check(project, root=ROOT) -> list:
    """Problems that make the project's lib/ a fork of root lib/; [] means an exact, locked copy."""
    project, root = Path(project), Path(root)
    modules = load_manifest(root)["modules"]
    lock_path = project / LOCK_NAME
    if not lock_path.is_file():
        return [f"{LOCK_NAME} missing — run: python3 tools/sync_lib.py {project}"]
    try:
        locked = json.loads(lock_path.read_text())["files"]
        if not isinstance(locked, dict):
            raise TypeError
    except (ValueError, KeyError, TypeError):
        return [f"{LOCK_NAME} is not valid (expected JSON with a \"files\" map) — re-run sync"]
    want = build_lock(root / "lib", modules)["files"]
    problems = []
    for m in modules:
        if m not in locked:
            problems.append(f"{LOCK_NAME}: {m} is not locked — re-run sync")
        elif locked[m] != want[m]:
            problems.append(f"{LOCK_NAME}: {m} is stale (root lib/{m} changed since the last sync) — re-run sync")
        copy = project / "lib" / m
        if not copy.is_file():
            problems.append(f"lib/{m} is missing from the project — re-run sync")
        elif file_hash(copy) != want[m]:
            problems.append(f"lib/{m} differs from root lib/{m} (edited copy?) — fix root lib/, then re-sync")
    for m in sorted(set(locked) - set(modules)):
        problems.append(f"{LOCK_NAME}: {m} is not a root lib/ module")
    lib_dir = project / "lib"
    if lib_dir.is_dir():
        for p in sorted(lib_dir.rglob("*")):
            rel = p.relative_to(lib_dir).as_posix()
            if p.is_file() and p.name not in IGNORED and rel not in modules:
                problems.append(f"lib/{rel} is not a root lib/ module (project code belongs in compositions/)")
    return problems


def main(argv) -> int:
    args = [a for a in argv[1:] if a != "--check"]
    if len(args) != 1:
        print("usage: python3 tools/sync_lib.py videos/<slug> [--check]")
        return 2
    project = Path(args[0])
    if not project.is_dir():
        print(f"{project}: not a directory")
        return 2
    try:
        if "--check" in argv:
            problems = check(project)
            for p in problems:
                print(p)
            if problems:
                return 1
            print(f"OK {project}/lib matches root lib/ ({LOCK_NAME} current)")
            return 0
        lock = sync(project)
    except (ValueError, FileNotFoundError) as e:
        print(e)
        return 1
    print(f"synced {len(lock['files'])} modules into {project}/lib + {LOCK_NAME}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
