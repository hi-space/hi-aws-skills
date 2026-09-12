#!/usr/bin/env python3
"""Regression test for scripts/bake_icon_clips.py."""

import re
import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import bake_icon_clips as bic  # noqa: E402
import pathops  # noqa: E402

# One stroked line, clipped by a rect covering only its right half.
SVG = (
    '<svg data-icon-style="preserve-color" viewBox="0 0 20 10" '
    'xmlns="http://www.w3.org/2000/svg">'
    '<defs><clipPath id="clippath"><rect x="10" y="0" width="10" height="10" fill="none"/></clipPath></defs>'
    '<g clip-path="url(#clippath)">'
    '<line x1="0" y1="5" x2="20" y2="5" stroke="#538DF7" stroke-width="2" stroke-linejoin="round"/>'
    '</g>'
    '</svg>'
)


class BakeIconClipsTests(unittest.TestCase):
    def test_stroked_line_clipped_by_rect_bakes_to_one_flat_path(self) -> None:
        new_text, n_leaves = bic.bake_svg_text(SVG)
        self.assertEqual(n_leaves, 1)
        self.assertNotIn("<clipPath", new_text)
        self.assertNotIn("clip-path", new_text)
        self.assertNotIn("<defs>", new_text)
        self.assertNotIn("<g", new_text)
        self.assertEqual(new_text.count("<path"), 1)
        self.assertIn('fill="#538DF7"', new_text)
        # the stroke outline only covers the right half (x=10..20); it must
        # not have grown back to cover the left half that was clipped away.
        self.assertNotIn(">M0 ", new_text)

    def test_rounded_rect_keeps_its_corners_rounded(self) -> None:
        """A stroked <rect rx="4"> clipped by a larger rect must bake to
        geometry whose corners are still rounded, not squared off (round 3
        regression: rx/ry were silently ignored, producing square corners,
        e.g. on the agentcore-identity ID-card pill shapes)."""
        svg = (
            '<svg data-icon-style="preserve-color" viewBox="0 0 100 100" '
            'xmlns="http://www.w3.org/2000/svg">'
            '<defs><clipPath id="clippath"><rect x="0" y="0" width="100" height="100" fill="none"/></clipPath></defs>'
            '<g clip-path="url(#clippath)">'
            '<rect x="10" y="10" width="30" height="20" rx="4" ry="4" '
            'stroke="#538DF7" stroke-width="2" stroke-linejoin="round" fill="none"/>'
            '</g>'
            '</svg>'
        )
        new_text, n_leaves = bic.bake_svg_text(svg)
        self.assertEqual(n_leaves, 1)
        d_match = re.search(r'<path d="([^"]+)"', new_text)
        self.assertIsNotNone(d_match)
        baked_path = bic.path_from_d(d_match.group(1))

        # The un-rounded bounding-box corner must be empty: with rx=ry=4 and
        # stroke-width=2, the rounded arc never comes within ~1.66 units of
        # the corner, well outside the 1-unit stroke half-width.
        self.assertFalse(baked_path.contains((10, 10)), "corner should be rounded away, not filled")
        # A point centred on the flat top edge (away from any corner) must
        # still be covered by the stroke.
        self.assertTrue(baked_path.contains((25, 10)), "the flat edge stroke should still be there")

    def test_file_with_no_clippath_is_left_alone(self) -> None:
        plain = '<svg viewBox="0 0 10 10" xmlns="http://www.w3.org/2000/svg"><rect width="10" height="10"/></svg>'
        new_text, n_leaves = bic.bake_svg_text(plain)
        self.assertIsNone(new_text)
        self.assertEqual(n_leaves, 0)

    def test_bake_is_idempotent(self) -> None:
        new_text, _ = bic.bake_svg_text(SVG)
        second_pass, n_leaves = bic.bake_svg_text(new_text)
        self.assertIsNone(second_pass)
        self.assertEqual(n_leaves, 0)


if __name__ == "__main__":
    unittest.main()
