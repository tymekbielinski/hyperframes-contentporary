"""Runs the lib/ node test suite (node built-ins only) as part of the repo's unittest run."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which("node")


@unittest.skipUnless(NODE, "node is not installed")
class LibNodeSuite(unittest.TestCase):
    def test_node_suite_passes(self):
        # Expand the glob here: node < 21 does not expand globs passed to --test.
        files = [str(p) for p in sorted((ROOT / "lib" / "test").glob("*.test.js"))]
        self.assertTrue(files, "no lib/test/*.test.js files found")
        r = subprocess.run([NODE, "--test", *files], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, (r.stdout + r.stderr)[-6000:])


if __name__ == "__main__":
    unittest.main()
