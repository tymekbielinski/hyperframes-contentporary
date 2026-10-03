"""Contract test: lib/brand.js maps exactly brandcheck.PALETTE_ROLES to CSS variables, for every brand."""
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

import brandcheck as bc

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which("node")


def var_name(path: str) -> str:
    return "--hf-" + "-".join(re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", p).lower() for p in path.split("."))


def run_brand_js(*args):
    return subprocess.run([NODE, str(ROOT / "lib" / "brand.js"), *args],
                          capture_output=True, text=True, cwd=ROOT)


@unittest.skipUnless(NODE, "node is not installed")
class BrandJsContractTests(unittest.TestCase):
    def test_every_role_of_every_palette_becomes_a_variable(self):
        for brand_dir in sorted((ROOT / "brands").iterdir()):
            if not (brand_dir / "tokens.json").is_file():
                continue
            brand = bc.load_brand(brand_dir)
            for name, palette in brand["palettes"].items():
                r = run_brand_js(str(brand_dir), "--palette", name, "--json")
                self.assertEqual(r.returncode, 0, f"{brand_dir.name}/{name}: {r.stderr}")
                got = json.loads(r.stdout)
                for path, keys in bc._role_paths():
                    value, _ = bc._get(palette, keys)
                    self.assertEqual(got.get(var_name(path)), value, f"{brand_dir.name}/{name} {path}")

    def test_mode_list_and_role_list_match_brandcheck(self):
        r = subprocess.run([NODE, "-e", "const B=require('./lib/brand.js');"
                            "console.log(JSON.stringify({modes:B.MODES,roles:B.ROLES}))"],
                           capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(r.returncode, 0, r.stderr)
        got = json.loads(r.stdout)
        self.assertEqual(got["modes"], list(bc.PALETTE_MODES))
        self.assertEqual(got["roles"], bc.PALETTE_ROLES)
        self.assertNotIn("mode", got["roles"])

    def test_css_variables_named_in_docs_exist(self):
        r = run_brand_js(str(ROOT / "brands" / "contentporary"), "--palette", "red", "--json")
        known = set(json.loads(r.stdout))
        docs = [ROOT / "CLAUDE.md", ROOT / "lib" / "README.md"] + list((ROOT / "standards").rglob("*.md"))
        named = set()
        for f in docs:
            named |= set(re.findall(r"var\((--hf-[a-z0-9-]+)\)", f.read_text()))
            named |= set(re.findall(r'"(--hf-[a-z0-9-]+)"', f.read_text()))
        self.assertTrue(named, "expected at least one brand variable in the docs")
        self.assertEqual(sorted(named - known), [])

    def test_brief_choice_errors_match_brandcheck(self):
        d = ROOT / "brands" / "contentporary"
        self.assertTrue(bc.validate_choice(d, "red", overrides={"accent.blok": "#FFFFFF"}))
        r = run_brand_js(str(d), "--palette", "red", "--override", "accent.blok=#FFFFFF")
        self.assertEqual(r.returncode, 1)
        self.assertIn("accent.blok", r.stderr)


if __name__ == "__main__":
    unittest.main()
