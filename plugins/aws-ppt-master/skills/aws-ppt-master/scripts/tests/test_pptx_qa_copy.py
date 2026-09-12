#!/usr/bin/env python3
"""Offline tests for qa_validate.py's ai_copy check. Needs python-pptx only.

Run: python3 test_ai_copy.py

The font cases exist because a substring test for monospace ("mono" in name)
silently matched "Monotype Corsiva" and skipped a decorative-serif paragraph
that carried a banned em dash. That is a false negative disabling a critical
check, so the heuristic is token-based and pinned here.

Kept in step with the html-slide sibling's test_check_copy.py: the two
checkers share their pattern set, so a case added there usually belongs here.
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pptx_qa_check as qv  # noqa: E402

from pptx import Presentation  # noqa: E402
from pptx.util import Inches, Pt  # noqa: E402


# ── font heuristic (no file needed) ────────────────────────────────────

class _Run:
    def __init__(self, name):
        self.font = type("F", (), {"name": name})()


class _Para:
    def __init__(self, names):
        self.runs = [_Run(n) for n in names]


FONT_CASES = [
    # (font name, is_mono)
    ("Monotype Corsiva", False),   # the substring trap
    ("Monotype", False),
    ("Monotype Sorts", False),
    ("Times New Roman", False),
    ("Amazon Ember", False),
    ("나눔고딕", False),
    ("Consolas", True),
    ("Courier New", True),
    ("Courier", True),
    ("SF Mono", True),
    ("JetBrains Mono", True),
    ("Roboto Mono", True),
    ("Cascadia Mono", True),
    ("DejaVu Sans Mono", True),
    ("Fira-Code", True),           # separator normalisation
    ("Source_Code_Pro", True),
    ("Lucida Console", True),
    ("Andale Mono", True),
    ("SFMono-Regular", True),
    ("Cascadia Code", True),
    (None, False),                 # inherited face: check as prose (safe side)
    ("", False),
]


# ── end-to-end copy cases ──────────────────────────────────────────────

# (label, text, font, expected level)
COPY_CASES = [
    ("em dash", "유휴 리소스 비용 — 피크 기준으로 산정", None, "critical"),
    ("en dash", "2026년 1월 – 6월", None, "critical"),
    ("meta ko", "왜 중요한가", None, "critical"),
    ("meta en", "Why this matters", None, "critical"),
    ("meta title-case", "Key Takeaway", None, "critical"),
    ("meta once not twice", "핵심 시사점", None, "critical"),
    ("soft bare", "시사점", None, "warning"),
    ("contrast bare", "기술이 아니라 방식을 바꿉니다", None, "warning"),
    ("contrast 단순히", "단순히 비용 절감이 아니라 체질 개선입니다", None, "warning"),
    ("contrast en", "Not just faster, but fundamentally different", None, "warning"),
    ("narration", "이는 운영 효율이 개선된다는 것을 의미합니다", None, "warning"),
    ("spaced hyphen", "연간 절감 - 24억 원", None, "warning"),
    ("nav label", "무엇을 했는가", None, "clean"),
    ("nav label 2", "지금의 문제", None, "clean"),
    ("compounds", "cloud-native, m5.xlarge, 24-7, on-premises", None, "clean"),
    ("tilde range", "2026년 1~6월 실적입니다", None, "clean"),
    ("plain claim", "반기 클라우드 비용을 18% 절감했습니다", None, "clean"),
    ("conditional 아니라면", "대상이 아니라면 건너뛰셔도 됩니다", None, "clean"),
    ("concessive 아니라도", "전문가가 아니라도 쓸 수 있습니다", None, "clean"),
    ("reason 아니라서", "담당자가 아니라서 답변이 어렵습니다", None, "clean"),
    ("quotative 아니라고", "문제가 아니라고 들었습니다", None, "clean"),
    ("additive 뿐만 아니라", "비용뿐만 아니라 속도도 좋아졌습니다", None, "clean"),
    ("meta 무엇을 의미하나", "무엇을 의미하나", None, "critical"),
    ("meta 무엇을 뜻하는가", "무엇을 뜻하는가", None, "critical"),
    # code in a monospace face is not copy
    ("code arithmetic", "budget = total - spent", "Consolas", "clean"),
    ("code shell", "npm run build -- --watch", "Courier New", "clean"),
    # ... but the same string in a prose face is checked
    ("prose separator", "연간 절감 - 24억 원", "Amazon Ember", "warning"),
    # and the substring trap must not buy an exemption
    ("serif em dash", "운영 비용 — 피크 기준", "Monotype Corsiva", "critical"),
]


def build_deck(cases):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.33), Inches(7.5)
    layout = prs.slide_layouts[6] if len(prs.slide_layouts) > 6 else prs.slide_layouts[0]
    for _, text, font, _ in cases:
        s = prs.slides.add_slide(layout)
        tb = s.shapes.add_textbox(Inches(1), Inches(1), Inches(11), Inches(1.2))
        para = tb.text_frame.paragraphs[0]
        run = para.add_run()
        run.text = text
        run.font.size = Pt(18)
        if font:
            run.font.name = font
    return prs


def collect_failures():
    failures = []

    for name, expected in FONT_CASES:
        got = qv._is_mono_run(_Run(name))
        if got != expected:
            failures.append(f"font {name!r}: expected is_mono={expected}, got {got}")

    # Mixed-run paragraph: only the monospace RUN is dropped, and the prose runs
    # around it are still checked. Skipping the whole paragraph was a real bypass
    # of the build-failing dash check, found in independent review: styling one
    # inline identifier in a code face would have taken the em dash with it.
    mixed = _Para([None, "Consolas", None])
    mixed.runs[0].text = "배포 주기는 "
    mixed.runs[1].text = "m5.xlarge"
    mixed.runs[2].text = " 기준 — 하루 단위입니다"
    prose = "".join(r.text for r in mixed.runs if not qv._is_mono_run(r))
    if "—" not in prose:
        failures.append("mixed-run paragraph lost its prose em dash "
                        "(whole-paragraph skip regression)")
    if "m5.xlarge" in prose:
        failures.append("mixed-run paragraph kept its monospace run")
    if "".join(r.text for r in _Para([]).runs):
        failures.append("empty paragraph should yield no text")

    prs = build_deck(COPY_CASES)
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "t.pptx"
        prs.save(path)
        issues = qv.check_ai_copy(qv.Presentation(str(path)))

    by_slide = {}
    for i in issues:
        if i.slide_num == 0:
            continue
        by_slide.setdefault(i.slide_num, set()).add(i.level)

    for n, (label, _, _, expected) in enumerate(COPY_CASES, 1):
        levels = by_slide.get(n, set())
        got = ("critical" if "critical" in levels
               else "warning" if "warning" in levels else "clean")
        if got != expected:
            failures.append(f"copy {label!r}: expected {expected}, got {got}")

    # '핵심 시사점' must not double-report as critical + soft warning
    crit_slide = next(n for n, (l, _, _, _) in enumerate(COPY_CASES, 1)
                      if l == "meta once not twice")
    if "warning" in by_slide.get(crit_slide, set()):
        failures.append("'핵심 시사점' reported both critical and warning "
                        "(soft marker should be suppressed)")

    return failures


class CopyVoiceTests(unittest.TestCase):
    def test_all_cases(self) -> None:
        failures = collect_failures()
        self.assertEqual(failures, [], "\n".join(failures))


if __name__ == "__main__":
    unittest.main()
