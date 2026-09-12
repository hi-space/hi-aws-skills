#!/usr/bin/env python3
"""Plugin identity: names, paths and manifests agree."""

import json
import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[2]
PLUGIN_DIR = SKILL_DIR.parents[1]
REPO_DIR = PLUGIN_DIR.parents[1]


class PluginIdentityTests(unittest.TestCase):
    def test_skill_frontmatter(self) -> None:
        head = SKILL_DIR.joinpath("SKILL.md").read_text(encoding="utf-8").split("\n---\n", 1)[0]
        self.assertIn("name: aws-ppt-master", head)
        self.assertIn('version: "1.0.0"', head)
        self.assertNotIn("sponsors", head)
        self.assertNotIn("video", head)

    def test_no_stale_skill_path(self) -> None:
        hits = []
        for path in PLUGIN_DIR.rglob("*"):
            if "tests" in path.parts:
                continue
            if path.is_file() and path.suffix in {".md", ".py", ".json", ".txt", ".html", ".js", ".yaml", ".yml"}:
                if "skills/ppt-master/" in path.read_text(encoding="utf-8", errors="ignore"):
                    hits.append(str(path.relative_to(PLUGIN_DIR)))
        self.assertEqual(hits, [])

    def test_manifests(self) -> None:
        plugin = json.loads((PLUGIN_DIR / ".claude-plugin" / "plugin.json").read_text())
        self.assertEqual(plugin["name"], "aws-ppt-master")
        self.assertEqual(plugin["version"], "1.0.0")
        market = json.loads((REPO_DIR / ".claude-plugin" / "marketplace.json").read_text())
        names = [p["name"] for p in market["plugins"]]
        self.assertIn("aws-ppt-master", names)
        entry = next(p for p in market["plugins"] if p["name"] == "aws-ppt-master")
        self.assertEqual(entry["source"], "./plugins/aws-ppt-master")

    def test_third_party_and_readme_exist(self) -> None:
        tp = (PLUGIN_DIR / "THIRD_PARTY_LICENSES.md").read_text(encoding="utf-8")
        for needle in ("Hugo He", "Jesam Kim", "AWS Architecture Icons"):
            self.assertIn(needle, tp)
        self.assertTrue((PLUGIN_DIR / "README.md").is_file())
        self.assertIn("aws-ppt-master", (REPO_DIR / "README.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
