#!/usr/bin/env python3
"""Regression tests for the AI-copy signature check in scripts/pptx_qa_check.py.

Focus: the middot / bullet-dot inline separator rule (`빠르고 · 저렴하고`), which
must fail the build like the em/en dash rule, while a leading list bullet stays
allowed. Uses lightweight fakes so no real PPTX or python-pptx render is needed.
"""

import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "skills" / "aws-ppt-master" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import pptx_qa_check as pqa  # noqa: E402


# ── Lightweight stand-ins for the python-pptx object graph ────────────────
# check_ai_copy only touches: prs.slides -> slide.shapes -> shape.has_text_frame
# / shape.text_frame.paragraphs -> para.runs -> run.text / run.font.name.


class _Font:
    def __init__(self, name=None):
        self.name = name


class _Run:
    def __init__(self, text, font_name=None):
        self.text = text
        self.font = _Font(font_name)


class _Para:
    def __init__(self, *runs):
        self.runs = list(runs)


class _TextFrame:
    def __init__(self, *paras):
        self.paragraphs = list(paras)


class _Shape:
    def __init__(self, text_frame):
        self.has_text_frame = text_frame is not None
        self.text_frame = text_frame


class _Slide:
    def __init__(self, *shapes):
        self.shapes = list(shapes)


class _Prs:
    def __init__(self, *slides):
        self.slides = list(slides)


def _deck(*lines):
    """One slide, one shape, one paragraph per line, each line a single run."""
    shapes = [_Shape(_TextFrame(_Para(_Run(ln)))) for ln in lines]
    return _Prs(_Slide(*shapes))


def _levels(issues, check="ai_copy"):
    return [i.level for i in issues if i.check == check]


class MiddotSeparatorTests(unittest.TestCase):
    def test_regex_matches_inline_separators_only(self):
        rx = pqa._BANNED_MIDDOT_SEP
        # Inline separators between phrases: the AI tell.
        self.assertTrue(rx.search("빠르고 · 저렴하고 · 안전한"))
        self.assertTrue(rx.search("자동화·관측·회수"))
        self.assertTrue(rx.search("A • B • C"))
        # A leading list bullet is not a separator.
        self.assertIsNone(rx.search("· 유휴 리소스 비용을 줄였습니다"))
        self.assertIsNone(rx.search("• 배포가 하루 단위로 바뀌었습니다"))
        # Clean copy has no dot at all.
        self.assertIsNone(rx.search("장애 대응이 4시간에서 20분으로 줄었습니다"))

    def test_middot_separator_fails_the_build(self):
        issues = pqa.check_ai_copy(_deck("빠르고 · 저렴하고 · 안전한"))
        self.assertIn("critical", _levels(issues))
        # There is a deck-wide summary line too (slide 0).
        self.assertTrue(any(i.slide_num == 0 and i.level == "critical"
                            for i in issues if i.check == "ai_copy"))

    def test_leading_bullet_is_allowed(self):
        issues = pqa.check_ai_copy(_deck("• 배포가 하루 단위로 바뀌었습니다",
                                         "• 장애 대응이 20분으로 줄었습니다"))
        self.assertNotIn("critical", _levels(issues))

    def test_clean_copy_has_no_findings(self):
        issues = pqa.check_ai_copy(_deck("장애 대응이 4시간에서 20분으로 줄었습니다"))
        self.assertEqual(issues, [])

    def test_em_dash_still_fails(self):
        # Regression: the existing dash rule is untouched.
        issues = pqa.check_ai_copy(_deck("유휴 리소스 비용 — 피크 기준으로 산정"))
        self.assertIn("critical", _levels(issues))


if __name__ == "__main__":
    unittest.main()
