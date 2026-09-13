#!/usr/bin/env python3
"""Check a companion guide against its brief (Phase 4 hand-off, review-checklist.md § E).

    python3 check_guide.py <name>.guide.md <name>.brief.md

Three things a guide must get right, all checked mechanically:
  1. Language — the brief's `Language:` line is the language the user wrote in. `ko` → the guide body is Korean
     (Hangul share of letters ≥ 0.3); `en` → not Korean. Service names stay English either way.
  2. Steps — the step-by-step section has one numbered item per Relationships row, numbered like the brief's `#`
     (= the badge on the picture), and each item names both endpoints (component id or its service name).
  3. Services — every Components row (drawn or not) is mentioned somewhere in the guide.
Exit 1 on any error; prints `guide check: …` on success.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_diagram import _table_rows  # noqa: E402

STEP_HEADINGS = ("Step-by-step", "단계별 흐름")
SERVICE_HEADINGS = ("Services", "서비스")
HANGUL = re.compile(r"[가-힣]")
LATIN = re.compile(r"[A-Za-z]")


def _section(text: str, headings: tuple[str, ...]) -> str:
    for h in headings:
        m = re.search(rf"^##\s+{re.escape(h)}\b.*?$", text, re.M)
        if m:
            rest = text[m.end():]
            nxt = re.search(r"^##\s", rest, re.M)
            return rest[:nxt.start()] if nxt else rest
    return ""


def _service_name(cell: str) -> str:
    """'API Gateway (`api_gateway`)' → 'API Gateway'; 'Mobile client (`mobile_client`, resource)' → 'Mobile client'."""
    return re.sub(r"\s*\(.*$", "", cell).strip("`* ").strip()


def check_guide(guide_text: str, brief_text: str) -> tuple[list[str], str]:
    errors: list[str] = []
    lang = (re.search(r"^Language:\s*([A-Za-z-]+)", brief_text, re.M) or [None, "?"])[1].lower()
    letters = len(HANGUL.findall(guide_text)) + len(LATIN.findall(guide_text))
    ratio = len(HANGUL.findall(guide_text)) / letters if letters else 0.0
    if lang == "ko" and ratio < 0.3:
        errors.append(f"guide is not written in Korean (Hangul share of letters {ratio:.2f}) but the brief says "
                      "'Language: ko' — the guide is written in the user's language; only service names stay English")
    elif lang == "en" and ratio > 0.2:
        errors.append(f"guide is written in Korean (Hangul share {ratio:.2f}) but the brief says 'Language: en'")

    comps = {}
    for row in _table_rows(brief_text, "Components"):
        cid = row[0].strip("`* ")
        if cid and len(row) > 1:
            comps[cid] = _service_name(row[1])
    rels = []
    for row in _table_rows(brief_text, "Relationships"):
        num = int(row[0]) if row and row[0].strip().isdigit() else None
        pair = None
        for cell in row:
            mm = re.search(r"([A-Za-z0-9_\-]+)\s*(?:→|->)\s*([A-Za-z0-9_\-]+)", cell)
            if mm:
                pair = (mm.group(1), mm.group(2))
                break
        if pair:
            rels.append((num, pair))

    steps_text = _section(guide_text, STEP_HEADINGS)
    if not steps_text:
        errors.append("guide has no step-by-step section (`## Step-by-step` or `## 단계별 흐름`)")
    steps: dict[int, str] = {}
    for m in re.finditer(r"^\s*(\d+)\.\s+(.*(?:\n(?!\s*\d+\.\s|\s*$).*)*)", steps_text, re.M):
        steps[int(m.group(1))] = m.group(2)

    def mentions(text: str, cid: str) -> bool:
        low = text.lower()
        name = comps.get(cid, "")
        return cid.lower() in low or (bool(name) and name.lower() in low)

    for num, (a, b) in rels:
        if num is None:
            continue
        step = steps.get(num)
        if step is None:
            errors.append(f"no step {num} in the guide for relationship {a} → {b} — one numbered step per relationship, "
                          "numbered like the brief's # (the badge on the picture)")
            continue
        missing = [comps.get(c) or c for c in (a, b) if not mentions(step, c)]
        if missing:
            errors.append(f"step {num} does not name {' / '.join(missing)} (relationship {a} → {b}) — write the hop as "
                          "**From → To** with the brief's names")

    services_text = _section(guide_text, SERVICE_HEADINGS) or guide_text
    for cid, name in comps.items():
        if not mentions(services_text, cid) and not mentions(guide_text, cid):
            errors.append(f"component '{cid}' ({name}) is missing from the guide's Services section — every Components "
                          "row appears there, 'not drawn' ones marked so")

    numbered = sum(1 for n, _ in rels if n is not None)
    summary = (f"guide check: {numbered} relationships → {len([n for n, _ in rels if n in steps])} steps ✓ · "
               f"{len(comps)} components ✓ · language {lang} ✓")
    return errors, summary


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        print(__doc__)
        return 2
    errors, summary = check_guide(Path(args[0]).read_text(encoding="utf-8"), Path(args[1]).read_text(encoding="utf-8"))
    for e in errors:
        print(f"ERROR guide: {e}")
    if errors:
        print(f"guide check: {len(errors)} problem(s) — NOT READY: fix the guide, not the brief")
        return 1
    print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
