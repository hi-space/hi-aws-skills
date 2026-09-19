#!/usr/bin/env python3
"""Validate <work>/05-claims.md and cross-check it against the draft.

    python3 check_claims.py <work> [--draft <file>]

Checks:
  - every claim row has an ID (Cnn), a status in {verified, corrected, unverified, out-of-scope}
  - verified / corrected / out-of-scope rows have an http(s) URL and non-empty evidence
  - every unverified claim has a [기술 검증 필요] placeholder in the draft that mentions its ID
  - corrected claims: the original sentence no longer appears verbatim in the draft
  - the draft has no more code blocks than claim rows of type 'code' (warning)
Exit 1 on any failure.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

STATUSES = {"verified", "corrected", "unverified", "out-of-scope"}
ROW_RE = re.compile(r"^\|\s*(C\d+)\s*\|")
URL_RE = re.compile(r"https?://\S+")
PH_TECH_RE = re.compile(r"\[기술 검증 필요\](.*?)</span>", re.S)


def parse_rows(md: str):
    rows = []
    for ln, line in enumerate(md.splitlines(), 1):
        if not ROW_RE.match(line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        # ID | sentence | section | type | basis | status | url | evidence | note
        while len(cells) < 9:
            cells.append("")
        rows.append({
            "line": ln, "id": cells[0], "sentence": cells[1], "section": cells[2], "type": cells[3].lower(),
            "basis": cells[4], "status": cells[5].lower(), "url": cells[6], "evidence": cells[7], "note": cells[8],
        })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("work")
    ap.add_argument("--draft", help="draft file (default: 06-final.md if present, else 04-draft.md)")
    args = ap.parse_args()
    work = Path(args.work)
    claims_path = work / "05-claims.md"
    if not claims_path.exists():
        print(f"missing {claims_path}", file=sys.stderr)
        return 2
    draft_path = Path(args.draft) if args.draft else (
        work / "06-final.md" if (work / "06-final.md").exists() else work / "04-draft.md")
    if not draft_path.exists():
        print(f"missing draft {draft_path}", file=sys.stderr)
        return 2

    rows = parse_rows(claims_path.read_text(encoding="utf-8"))
    draft = draft_path.read_text(encoding="utf-8")
    problems = []
    warnings = []

    if not rows:
        problems.append("no claim rows (| Cnn | ...) found in 05-claims.md")

    tech_placeholders = [m.group(1) for m in PH_TECH_RE.finditer(draft)]
    counts = {s: 0 for s in STATUSES}
    for r in rows:
        tag = f"{r['id']} (L{r['line']})"
        if r["status"] not in STATUSES:
            problems.append(f"{tag}: status '{r['status']}' not in {sorted(STATUSES)}")
            continue
        counts[r["status"]] += 1
        if r["status"] in ("verified", "corrected", "out-of-scope"):
            if not URL_RE.search(r["url"]):
                problems.append(f"{tag}: {r['status']} without an opened URL")
            if len(r["evidence"]) < 10:
                problems.append(f"{tag}: {r['status']} without evidence (quote or paraphrase of the page)")
        if r["status"] == "unverified":
            if not any(r["id"] in p for p in tech_placeholders):
                problems.append(f"{tag}: unverified but no [기술 검증 필요] placeholder mentioning {r['id']} in {draft_path.name}")
        if r["status"] == "corrected":
            sent = r["sentence"].strip()
            if len(sent) > 20 and sent in draft:
                problems.append(f"{tag}: corrected, but the original sentence still appears verbatim in the draft")
            if len(r["note"]) < 5:
                warnings.append(f"{tag}: corrected without a note of old vs new wording")

    code_blocks = len(re.findall(r"^\s*```[^\n]*\S", draft, flags=re.M))
    code_rows = sum(1 for r in rows if r["type"] == "code")
    if code_blocks > code_rows:
        warnings.append(f"draft has {code_blocks} code blocks but only {code_rows} claim rows of type 'code'")

    for p in problems:
        print(f"FAIL  {p}")
    for w in warnings:
        print(f"WARN  {w}")
    print()
    print(f"claims: {len(rows)}  " + "  ".join(f"{k}: {v}" for k, v in sorted(counts.items())))
    print(f"draft checked: {draft_path}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
