#!/usr/bin/env python3
"""The bundled AWS icon library is complete, well-formed, and syncable."""

import re
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import icon_sync  # noqa: E402

AWS_DIR = SCRIPTS_DIR.parent / "templates" / "icons" / "aws"


class AwsIconLibraryTests(unittest.TestCase):
    def test_count_and_names(self) -> None:
        files = sorted(AWS_DIR.glob("*.svg"))
        self.assertEqual(len(files), 304)
        for f in files:
            self.assertRegex(f.stem, r"^[a-z0-9]+(-[a-z0-9]+)*$", f.name)
        for required in ("lambda", "s3", "ec2", "eks", "sagemaker", "bedrock",
                         "agentcore-runtime-blue-light", "agentcore-gateway-purple-dark"):
            self.assertTrue((AWS_DIR / f"{required}.svg").is_file(), required)

    def test_every_file_is_svg_with_viewbox(self) -> None:
        for f in AWS_DIR.glob("*.svg"):
            text = f.read_text(encoding="utf-8")
            self.assertIn("<svg", text, f.name)
            self.assertRegex(text, r'viewBox="[^"]+"', f.name)

    def test_every_file_has_preserve_color_marker(self) -> None:
        root_svg_re = re.compile(r'^<svg\b[^>]*>', re.DOTALL)
        for f in AWS_DIR.glob("*.svg"):
            text = f.read_text(encoding="utf-8")
            match = root_svg_re.match(text)
            self.assertIsNotNone(match, f.name)
            self.assertIn('data-icon-style="preserve-color"', match.group(0), f.name)

    def test_sync_allows_aws_with_one_stylistic_library(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            copied, missing = icon_sync.sync_icons(Path(d), ["aws/lambda", "tabler-outline/home"])
        self.assertEqual(missing, [])
        self.assertEqual(copied, ["aws/lambda", "tabler-outline/home"])

    def test_readme_lists_aws(self) -> None:
        readme = (SCRIPTS_DIR.parent / "templates" / "icons" / "README.md").read_text(encoding="utf-8")
        self.assertIn("| `aws` |", readme)

    def test_no_clippath_or_ids(self) -> None:
        """No Illustrator id="..." clutter, and no <clipPath> at all: the exporter
        rejects clip-path on a <g> (references/shared-standards-core.md §1.2), and a
        shared id collides when the same icon is used twice on one page. The 38
        agentcore-* "split" icons that used to carry a live (pixel-tested, not dead)
        rect clip have had it baked into flattened <path> geometry by
        scripts/bake_icon_clips.py instead of stripped -- see UPSTREAM.md."""
        for f in sorted(AWS_DIR.glob("*.svg")):
            text = f.read_text(encoding="utf-8")
            self.assertNotIn("<clipPath", text, f.name)
            self.assertNotIn(' id="', text, f.name)
            self.assertNotIn("url(#", text, f.name)
            self.assertNotIn('href="#', text, f.name)


if __name__ == "__main__":
    unittest.main()
