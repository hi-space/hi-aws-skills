"""aws-ppt-master fork: default typography is Amazon Ember, then Noto Sans.

The exporter must (1) keep both faces as named typefaces instead of remapping
them to Windows stock faces, (2) not flag them as portability-unsafe, and
(3) fall back to the Noto Sans family for Korean text when a stack names no
CJK face.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from pptx_delivery_check import _unsafe_font_faces  # noqa: E402
from svg_to_pptx.drawingml.utils import (  # noqa: E402
    parse_font_family,
    unsafe_exported_font_faces,
)


class AwsDefaultFontStackTests(unittest.TestCase):
    def test_ember_plus_noto_kr_splits_into_latin_and_ea(self) -> None:
        fonts = parse_font_family("Amazon Ember, Noto Sans KR", "ko")
        self.assertEqual(fonts, {"latin": "Amazon Ember", "ea": "Noto Sans KR"})

    def test_noto_sans_fallback_stack_is_kept_verbatim(self) -> None:
        fonts = parse_font_family("Noto Sans, Noto Sans KR", "ko")
        self.assertEqual(fonts, {"latin": "Noto Sans", "ea": "Noto Sans KR"})

    def test_korean_deck_without_cjk_face_falls_back_to_noto_sans_kr(self) -> None:
        self.assertEqual(parse_font_family("Amazon Ember", "ko")["ea"], "Noto Sans KR")
        self.assertEqual(parse_font_family("Amazon Ember", "ko-KR")["ea"], "Noto Sans KR")

    def test_korean_serif_deck_falls_back_to_noto_serif_kr(self) -> None:
        self.assertEqual(parse_font_family("Georgia", "ko")["ea"], "Noto Serif KR")

    def test_other_languages_keep_upstream_defaults(self) -> None:
        self.assertEqual(parse_font_family("Arial", "ja")["ea"], "Yu Gothic")
        self.assertEqual(parse_font_family("Arial", "zh-CN")["ea"], "Microsoft YaHei")


class AwsDefaultFontsArePortableTests(unittest.TestCase):
    def test_export_summary_does_not_flag_ember_or_noto(self) -> None:
        self.assertEqual(unsafe_exported_font_faces("Amazon Ember, Noto Sans KR"), {})
        self.assertEqual(unsafe_exported_font_faces("Noto Sans, Noto Sans KR"), {})
        self.assertEqual(unsafe_exported_font_faces("Amazon Ember, Noto Serif KR"), {})

    def test_delivery_check_does_not_flag_ember_or_noto(self) -> None:
        faces = ["Amazon Ember", "Amazon Ember Display", "Noto Sans", "Noto Sans KR"]
        self.assertEqual(_unsafe_font_faces(faces), [])

    def test_truly_unknown_face_is_still_flagged(self) -> None:
        self.assertEqual(unsafe_exported_font_faces("Comic Neue"), {"latin": "Comic Neue"})
        self.assertEqual(_unsafe_font_faces(["Comic Neue"]), ["Comic Neue"])


if __name__ == "__main__":
    unittest.main()
