#!/usr/bin/env python3
"""Regression tests for the AI-copy signature check in scripts/pptx_qa_check.py.

Covers the middot / bullet-dot inline separator rule (`빠르고 · 저렴하고`), which
must fail the build like the em/en dash rule while a leading list bullet stays
allowed, and the Korean prose rules (actor-less passive, abstract subjects,
figurative language, evaluation words, translated constructions, monotone
endings), which warn on slide text and on speaker notes. Uses lightweight fakes so no real PPTX or python-pptx render is needed.
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


class _NotesSlide:
    def __init__(self, text_frame):
        self.notes_text_frame = text_frame


class _Slide:
    def __init__(self, *shapes, notes=None):
        self.shapes = list(shapes)
        self.has_notes_slide = notes is not None
        self.notes_slide = _NotesSlide(_TextFrame(*[_Para(_Run(ln)) for ln in notes])) if notes else None


class _Prs:
    def __init__(self, *slides):
        self.slides = list(slides)


def _deck(*lines):
    """One slide, one shape, one paragraph per line, each line a single run."""
    shapes = [_Shape(_TextFrame(_Para(_Run(ln)))) for ln in lines]
    return _Prs(_Slide(*shapes))


def _levels(issues, check="ai_copy"):
    return [i.level for i in issues if i.check == check]


def _messages(issues, check="ai_copy"):
    return " || ".join(i.message for i in issues if i.check == check)


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


class KoreanProseTests(unittest.TestCase):
    """Rules 4b-4d of copy-voice.md: subject/voice, figurative language,
    evaluation words, translated constructions, monotone endings. All warnings.
    Example strings are verbatim from the 2026-10-28 baseline runs."""

    # ── Rule 4b: actor-less passive / abstract subject ──
    def test_agentive_passive_warns(self):
        for line in ("인증은 Cognito를 통해 처리됩니다",
                     "이번 수치로 확인된 것은 재실행이 줄었다는 점입니다",
                     "스키마 문서화가 요구됩니다",
                     "배포는 팀에 의해 수행되었습니다",
                     "실패를 설명할 수 있게 됐습니다"):
            issues = pqa.check_ai_copy(_deck(line))
            self.assertIn("warning", _levels(issues), line)
            self.assertIn("passive", _messages(issues).lower(), line)
            self.assertNotIn("critical", _levels(issues), line)

    def test_active_voice_and_unknown_actor_passive_pass(self):
        for line in ("Amazon Cognito가 인증을 처리합니다",
                     "Step Functions가 단계 순서를 관리하고, 각 단계는 Lambda가 실행합니다",
                     "로그는 30일 뒤 삭제됩니다",
                     "배치 온콜 호출은 월 5회에서 0회가 됐습니다"):
            self.assertEqual(pqa.check_ai_copy(_deck(line)), [], line)

    def test_abstract_subject_acting_warns(self):
        for line in ("이 숫자들이 이후 설계를 비교하는 기준선이 됩니다",
                     "기록이 먼저 답해 줍니다",
                     "세 가지 문제가 남습니다"):
            issues = pqa.check_ai_copy(_deck(line))
            self.assertIn("warning", _levels(issues), line)
            self.assertIn("subject", _messages(issues).lower(), line)

    # ── Rule 4c: figurative language ──
    def test_figurative_language_warns(self):
        for line in ("그 호스트가 전체 일정을 쥐고 있었습니다",
                     "단계로 나눌수록 실패가 번지는 범위가 좁아집니다",
                     "cron 한 대에 묶인 정산",
                     "이 숫자들이 전환의 출발점입니다",
                     "서버리스 여정을 시작하세요",
                     "세 가지 축으로 비용을 낮췄습니다",
                     "더 큰 그림을 보면 검색이 제품의 일부가 됐습니다"):
            issues = pqa.check_ai_copy(_deck(line))
            self.assertIn("warning", _levels(issues), line)
            self.assertIn("figurative", _messages(issues).lower(), line)

    def test_literal_technical_words_pass(self):
        for line in ("시간축 기준으로 정렬합니다",
                     "X축은 월, Y축은 비용입니다",
                     "데이터 파이프라인을 S3 버킷으로 옮겼습니다",
                     "Gateway가 인증을 처리합니다",
                     "묶음 배송 주문은 따로 집계합니다"):
            self.assertEqual(pqa.check_ai_copy(_deck(line)), [], line)

    # ── Rule 4d: evaluation words ──
    def test_evaluation_words_warn(self):
        for line in ("숫자보다 중요한 변화는 새벽에 호출을 받지 않는 운영입니다",
                     "이번 전환의 핵심은 기록을 밖으로 뺀 것입니다",
                     "다양한 배치 작업에 적용할 수 있습니다",
                     "성공적으로 전환을 완료했습니다",
                     "이를 통해 운영 효율이 개선됩니다",
                     "원활한 운영을 위한 혁신적인 구조"):
            issues = pqa.check_ai_copy(_deck(line))
            self.assertIn("warning", _levels(issues), line)
            self.assertIn("evaluation", _messages(issues).lower(), line)

    def test_consequence_sentence_passes(self):
        self.assertEqual(pqa.check_ai_copy(_deck("이 차이 때문에 cron 서버를 유지할 이유가 없습니다")), [])

    # ── Rule 4: translated constructions ──
    def test_translated_constructions_warn(self):
        for line in ("비용 관리에 있어 가장 큰 변수입니다",
                     "실시간 집계를 가능하게 합니다",
                     "안정적인 구조라고 볼 수 있습니다",
                     "이번 발표는 배치 전환에 관한 것입니다",
                     "첫째, 실행 상태를 밖에 둡니다"):
            issues = pqa.check_ai_copy(_deck(line))
            self.assertIn("warning", _levels(issues), line)
            self.assertIn("translat", _messages(issues).lower(), line)

    # ── Rule 6: monotone endings ──
    def test_monotone_endings_warn(self):
        issues = pqa.check_ai_copy(_deck("한 번 실행하는 데 6시간이 걸렸습니다",
                                         "월 2회 실패했고, 실패할 때마다 사람이 다시 실행했습니다",
                                         "배치 관련 온콜 호출이 월 5건이었습니다",
                                         "EC2 호스트 한 대에서 cron으로 돌았습니다"))
        self.assertIn("warning", _levels(issues))
        self.assertIn("ending", _messages(issues).lower())

    def test_mixed_endings_pass(self):
        issues = pqa.check_ai_copy(_deck("실행 시간: 6시간 → 48분",
                                         "월 2회 실패했고, 실패할 때마다 사람이 다시 실행했습니다",
                                         "배치 온콜 호출 월 5회",
                                         "EC2 호스트 한 대에서 cron으로 돌았습니다"))
        self.assertEqual(issues, [])

    def test_three_lines_never_monotone(self):
        issues = pqa.check_ai_copy(_deck("6시간이 걸렸습니다", "월 2회 실패했습니다", "월 5건이었습니다"))
        self.assertEqual(issues, [])

    # ── speaker notes are prose and are checked, but never fail the build ──
    def test_notes_prose_rules_warn(self):
        slide = _Slide(_Shape(_TextFrame(_Para(_Run("실행 시간: 6시간 → 48분")))),
                       notes=["그 호스트가 전체 일정을 쥐고 있었습니다.",
                              "인증은 Cognito를 통해 처리됩니다 — 핵심은 여기입니다."])
        issues = pqa.check_ai_copy(_Prs(slide))
        msgs = _messages(issues).lower()
        self.assertIn("figurative", msgs)
        self.assertIn("passive", msgs)
        self.assertIn("notes", msgs)
        # A dash in notes is invisible to the audience: warning, not critical.
        self.assertNotIn("critical", _levels(issues))
        self.assertIn("dash", msgs)

    def test_clean_notes_pass(self):
        slide = _Slide(_Shape(_TextFrame(_Para(_Run("실행 시간: 6시간 → 48분")))),
                       notes=["플랫폼팀이 정산 배치를 Step Functions로 옮겼습니다. 3개월 동안 수동 재실행은 0회였습니다."])
        self.assertEqual(pqa.check_ai_copy(_Prs(slide)), [])

    def test_stale_model_pin_removed_from_messages(self):
        issues = pqa.check_ai_copy(_deck("유휴 리소스 비용 — 피크 기준으로 산정"))
        self.assertNotIn("opus 4.6", _messages(issues).lower())


if __name__ == "__main__":
    unittest.main()
