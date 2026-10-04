import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import sync_lib as sl

ROOT = Path(__file__).resolve().parents[1]


def make_root(base: Path) -> Path:
    root = base / "repo"
    (root / "lib" / "shorts").mkdir(parents=True)
    (root / "lib" / "a.js").write_text("var a = 1;\n")
    (root / "lib" / "shorts" / "w.js").write_text("var w = 2;\n")
    (root / "lib" / "README.md").write_text("docs stay in root\n")
    (root / "lib" / "manifest.json").write_text(json.dumps(
        {"modules": ["shorts/w.js", "a.js"], "loadOrder": ["a.js", "shorts/w.js"]}))
    return root


class ManifestTests(unittest.TestCase):
    def test_real_manifest_lists_existing_modules(self):
        m = sl.load_manifest(ROOT)
        self.assertIn("shorts/wipe.js", m["modules"])
        self.assertEqual(m["loadOrder"][0], "profile.js")
        for rel in m["modules"]:
            self.assertTrue((ROOT / "lib" / rel).is_file(), rel)

    def test_load_order_must_cover_modules(self):
        with tempfile.TemporaryDirectory() as t:
            root = make_root(Path(t))
            (root / "lib" / "manifest.json").write_text(json.dumps(
                {"modules": ["a.js", "shorts/w.js"], "loadOrder": ["a.js"]}))
            with self.assertRaisesRegex(ValueError, "loadOrder must list exactly the modules"):
                sl.load_manifest(root)

    def test_malformed_manifest_is_named(self):
        with tempfile.TemporaryDirectory() as t:
            root = make_root(Path(t))
            (root / "lib" / "manifest.json").write_text("{nope")
            with self.assertRaisesRegex(ValueError, "manifest.json is not valid JSON"):
                sl.load_manifest(root)


class SyncCheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.root = make_root(base)
        self.project = base / "videos" / "demo"
        self.project.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_sync_copies_only_modules_and_writes_lock(self):
        lock = sl.sync(self.project, self.root)
        self.assertEqual((self.project / "lib" / "shorts" / "w.js").read_text(), "var w = 2;\n")
        self.assertFalse((self.project / "lib" / "README.md").exists())
        self.assertFalse((self.project / "lib" / "manifest.json").exists())
        self.assertEqual(sorted(lock["files"]), ["a.js", "shorts/w.js"])
        self.assertTrue(lock["files"]["a.js"].startswith("sha256:"))
        on_disk = json.loads((self.project / "lib.lock").read_text())
        self.assertEqual(on_disk, lock)

    def test_check_clean_after_sync(self):
        sl.sync(self.project, self.root)
        self.assertEqual(sl.check(self.project, self.root), [])

    def test_check_catches_edited_copy(self):
        sl.sync(self.project, self.root)
        (self.project / "lib" / "a.js").write_text("var a = 99;\n")
        self.assertEqual(sl.check(self.project, self.root),
                         ["lib/a.js differs from root lib/a.js (edited copy?) — fix root lib/, then re-sync"])

    def test_check_catches_root_change_after_sync(self):
        sl.sync(self.project, self.root)
        (self.root / "lib" / "a.js").write_text("var a = 3;\n")
        problems = sl.check(self.project, self.root)
        self.assertIn("lib.lock: a.js is stale (root lib/a.js changed since the last sync) — re-run sync", problems)

    def test_check_catches_extra_file_and_sync_never_deletes_it(self):
        (self.project / "lib").mkdir()
        (self.project / "lib" / "house.js").write_text("// local fork\n")
        sl.sync(self.project, self.root)
        self.assertTrue((self.project / "lib" / "house.js").is_file())
        self.assertEqual(sl.check(self.project, self.root),
                         ["lib/house.js is not a root lib/ module (project code belongs in compositions/)"])

    def test_check_missing_and_malformed_lock(self):
        self.assertEqual(sl.check(self.project, self.root),
                         [f"lib.lock missing — run: python3 tools/sync_lib.py {self.project}"])
        (self.project / "lib.lock").write_text("not json")
        self.assertEqual(sl.check(self.project, self.root),
                         ['lib.lock is not valid (expected JSON with a "files" map) — re-run sync'])

    def test_check_catches_missing_copy(self):
        sl.sync(self.project, self.root)
        (self.project / "lib" / "shorts" / "w.js").unlink()
        self.assertEqual(sl.check(self.project, self.root),
                         ["lib/shorts/w.js is missing from the project — re-run sync"])

    def test_cli_exit_codes(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(sl.main(["sync_lib.py"]), 2)
            self.assertEqual(sl.main(["sync_lib.py", str(self.project), "--check"]), 1)
        self.assertIn("lib.lock missing", out.getvalue())


if __name__ == "__main__":
    unittest.main()
