#!/usr/bin/env python3
"""Create the blog work directory and copy templates into it.

    python3 init_workspace.py <slug> [--dir <parent>]

Creates <parent>/<slug>/ (default parent: ./blog-work) with:
  00-brief.md 01-facts.md 02-plan.md 03-research.md 05-claims.md
(04-draft.md is not pre-created: the Stage 4 drafter subagent writes it from templates/blog-post.md)
  sources/ sources/text/ diagrams/manifest.md images/
Existing files are never overwritten.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_DIR / "templates"

COPIES = {
    "brief.md": "00-brief.md",
    "facts.md": "01-facts.md",
    "plan.md": "02-plan.md",
    "research.md": "03-research.md",
    "claims.md": "05-claims.md",
    "diagram-manifest.md": "diagrams/manifest.md",
}
DIRS = ["sources", "sources/text", "diagrams", "images"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug", help="short kebab-case name for the post, e.g. ks-agent-platform")
    ap.add_argument("--dir", default="blog-work", help="parent directory (default ./blog-work)")
    args = ap.parse_args()

    work = Path(args.dir) / args.slug
    work.mkdir(parents=True, exist_ok=True)
    for d in DIRS:
        (work / d).mkdir(parents=True, exist_ok=True)

    created, skipped = [], []
    for src, dst in COPIES.items():
        target = work / dst
        if target.exists():
            skipped.append(dst)
            continue
        shutil.copyfile(TEMPLATES / src, target)
        created.append(dst)

    # Digest template is copied per source later; leave a pointer.
    pointer = work / "sources" / "README.md"
    if not pointer.exists():
        pointer.write_text(
            "Put every reference file here (or a .url file containing the link).\n"
            "Run ingest_sources.py to convert PDF/DOCX/PPTX/drawio into text/.\n"
            f"Digest each source into <SID>.digest.md using {TEMPLATES / 'source-digest.md'}\n",
            encoding="utf-8",
        )
        created.append("sources/README.md")

    print(f"work dir: {work.resolve()}")
    for c in created:
        print(f"  created  {c}")
    for s in skipped:
        print(f"  kept     {s} (already existed)")
    print("next: fill 00-brief.md, drop sources into sources/, run ingest_sources.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
