#!/usr/bin/env python3
"""The fork has no integrity gate: every CLI entry point must start with --help."""

import subprocess
import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SKILL_DIR = SCRIPTS_DIR.parent

ENTRY_POINTS = [
    "console_encoding.py",
    "project_manager.py",
    "project_management/cli.py",
    "svg_quality_checker.py",
    "svg_quality/cli.py",
    "svg_to_pptx.py",
    "svg_to_pptx/pptx_package/cli.py",
    "register_template.py",
    "template_preview_pptx.py",
    "apply_template.py",
    "image_gen.py",
    "icon_sync.py",
]


class NoAttributionGuardTests(unittest.TestCase):
    def test_guard_files_are_gone(self) -> None:
        for name in ("scripts/attribution_guard.py", "SPONSORS.md", "SPONSORS_CN.md",
                     "scripts/prompt_audit.py", "scripts/prompt_audit_manifest.json"):
            self.assertFalse((SKILL_DIR / name).exists(), name)

    def test_no_source_mentions_guard(self) -> None:
        hits = []
        for path in SKILL_DIR.rglob("*"):
            if path.suffix not in {".py", ".md", ".json", ".txt"} or "tests" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "attribution_guard" in text or "require_skill_integrity" in text or "SPONSORS" in text:
                hits.append(str(path.relative_to(SKILL_DIR)))
        self.assertEqual(hits, [])

    def test_entry_points_start_without_exit_78(self) -> None:
        for rel in ENTRY_POINTS:
            with self.subTest(rel):
                proc = subprocess.run([sys.executable, str(SCRIPTS_DIR / rel), "--help"],
                                      capture_output=True, text=True, timeout=120)
                self.assertNotEqual(proc.returncode, 78, proc.stderr)


if __name__ == "__main__":
    unittest.main()
