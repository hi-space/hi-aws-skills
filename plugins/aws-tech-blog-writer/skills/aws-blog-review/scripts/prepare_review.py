#!/usr/bin/env python3
"""Prepare a review work directory from a Markdown or Word draft.

    python3 prepare_review.py <draft.md | draft.docx> [--slug <name>] [--dir <parent>]
    python3 prepare_review.py <work>/04-draft.md --in-place

Creates <parent>/<slug>/ (default parent ./blog-review, slug from the file name) with:
  draft.md        the draft as Markdown (.docx converted with pandoc; headings, code blocks, placeholder
                  spans and figures written by build_docx.js are recovered, see preprocess_docx)
  images/         every local image the draft references, copied next to it; paths rewritten
  05-claims.md    the claims table template (filled by blog-fact-checker)
  review-report.md the report template (filled by the main agent)
Existing files are never overwritten. Prints the paths and a summary (headings, images, code blocks).
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
WRITER_DIR = SKILL_DIR.parent / "aws-tech-blog-writer"
IMAGE_RE = re.compile(r"(!\[[^\]]*\]\()([^)\s]+)((?:\s+\"[^\"]*\")?\))")


# Placeholder shading colours written by build_docx.js (references/placeholders.md), and the character
# style names injected so pandoc can see them
PH_FILLS = {
    "FFF2CC": ("작성자 확인", "background-color:#FFF2CC;color:#7F6000;padding:1px 4px;"),
    "F8CECC": ("기술 검증 필요", "background-color:#F8CECC;color:#9F0000;padding:1px 4px;"),
    "DAE8FC": ("이미지 필요", "background-color:#DAE8FC;color:#0B3D91;padding:1px 4px;"),
    "D5E8D4": ("인용 승인 필요", "background-color:#D5E8D4;color:#1E5631;padding:1px 4px;"),
}
PH_STYLE_ID = {fill: f"BlogPh{i}" for i, fill in enumerate(PH_FILLS)}
CODE_FILL = "F5F5F5"  # paragraph shading build_docx.js gives code lines


def preprocess_docx(src: Path, dst: Path) -> None:
    """Rewrite a Word file so pandoc recovers what the builder encoded with formatting only.

    pandoc maps paragraph styles to headings by Word's lowercase built-in names (`heading 1`); docx-js
    writes `Heading 1`, so those paragraphs come back as bold text. The builder maps Markdown H1 to
    Title and H2 to Heading1, so the names are shifted one level while being lowercased. Code lines
    are paragraphs shaded F5F5F5 with no style (given the `Source Code` style pandoc turns into a code
    block), and placeholder runs are shaded with their category colour (given a character style that
    `-f docx+styles` exposes as a span). Word files written by Word already use lowercase names and are
    left as they are."""
    zin = zipfile.ZipFile(src)
    zout = zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED)
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename == "word/styles.xml":
            x = data.decode("utf-8")
            seen = set()

            def dedupe(m):
                sid = re.search(r'w:styleId="([^"]*)"', m.group(0)).group(1)
                if sid in seen:
                    return ""
                seen.add(sid)
                return m.group(0)
            x = re.sub(r"<w:style\b.*?</w:style>", dedupe, x, flags=re.S)
            if 'w:val="Heading 1"' in x:  # docx-js names: shift and lowercase
                for lvl in range(6, 0, -1):
                    x = x.replace(f'<w:name w:val="Heading {lvl}"/>', f'<w:name w:val="heading {lvl + 1}"/>')
                x = x.replace('<w:name w:val="Title"/>', '<w:name w:val="heading 1"/>')
            extra = ""
            if 'w:styleId="Normal"' not in x:
                # docx-js omits the Normal style; pandoc drops every style whose basedOn it cannot resolve,
                # which is how the builder's headings came back as bold paragraphs
                extra += '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>'
            extra += '<w:style w:type="paragraph" w:styleId="BlogSourceCode"><w:name w:val="Source Code"/></w:style>'
            extra += "".join(f'<w:style w:type="character" w:styleId="{sid}"><w:name w:val="{sid}"/></w:style>'
                             for sid in PH_STYLE_ID.values())
            data = x.replace("</w:styles>", extra + "</w:styles>").encode("utf-8")
        elif item.filename == "word/document.xml":
            x = data.decode("utf-8")

            def tag_code(m):
                para = m.group(0)
                if f'w:fill="{CODE_FILL}"' not in para:
                    return para
                if "<w:pPr>" in para:
                    return para.replace("<w:pPr>", '<w:pPr><w:pStyle w:val="BlogSourceCode"/>', 1)
                return para.replace(">", '><w:pPr><w:pStyle w:val="BlogSourceCode"/></w:pPr>', 1)
            x = re.sub(r"<w:p\b[^>]*>.*?</w:p>", tag_code, x, flags=re.S)

            def tag_placeholder(m):
                run = m.group(0)
                for fill, sid in PH_STYLE_ID.items():
                    if f'w:fill="{fill}"' in run:
                        if "<w:rPr>" in run:
                            return run.replace("<w:rPr>", f'<w:rPr><w:rStyle w:val="{sid}"/>', 1)
                        return run.replace(">", f'><w:rPr><w:rStyle w:val="{sid}"/></w:rPr>', 1)
                return run
            x = re.sub(r"<w:r\b[^>]*>.*?</w:r>", tag_placeholder, x, flags=re.S)
            data = x.encode("utf-8")
        zout.writestr(item, data)
    zout.close()


def guess_language(first_line: str) -> str:
    l = first_line.strip()
    if re.search(r"\.py\b", l) or l.startswith(("def ", "import ", "from ")):
        return "python"
    if re.search(r"\.(sh|bash)\b", l) or l.startswith(("$ ", "aws ", "#!/")):
        return "bash"
    if re.search(r"\.(ya?ml)\b", l):
        return "yaml"
    if re.search(r"\.json\b", l) or l.startswith(("{", "[")):
        return "json"
    if re.search(r"\.tf\b", l):
        return "hcl"
    return "text"


def postprocess_markdown(text: str) -> str:
    # placeholder spans: <span custom-style="BlogPhN">**\[태그\]** 요청</span> -> house HTML span
    for fill, sid in PH_STYLE_ID.items():
        tag, style = PH_FILLS[fill]
        text = re.sub(rf'</span> ?<span custom-style="{sid}">', "", text)  # merge adjacent runs, same paragraph

        def to_span(m):
            inner = m.group(1)
            inner = re.sub(r"\*\*\\?\[([^\]]*)\\?\]\*\*", r"[\1]", inner)
            inner = inner.replace("\\[", "[").replace("\\]", "]").strip()
            return f'<span style="{style}">{inner}</span>'
        text = re.sub(rf'<span custom-style="{sid}">(.*?)</span>', to_span, text, flags=re.S)
    # code: consecutive <div custom-style="Source Code"> blocks -> one fenced block
    div = re.compile(r'<div custom-style="Source Code">\n(.*?)\n</div>\n*', re.S)
    lines: list[str] = []

    def collect(m):
        lines.append(m.group(1).replace("\\", ""))
        return "\x00CODE\x00\n"
    text = div.sub(collect, text)
    it = iter(lines)
    out, block = [], []

    def flush():
        nonlocal block
        if block:
            out.append("```" + guess_language(block[0]) + "\n" + "\n".join(block) + "\n```\n")
            block = []
    for line in text.split("\n"):
        if line == "\x00CODE\x00":
            block.append(next(it))
            continue
        if line.strip() == "" and block:
            continue
        flush()
        out.append(line)
    flush()
    text = "\n".join(out)
    # images: pandoc emits <img> when width/height are set
    text = re.sub(r'<img src="([^"]+)"[^>]*?alt="([^"]*)"[^>]*/?>', r"![\2](\1)", text)
    text = re.sub(r"!\[\]\(", "![그림](", text)
    # the builder writes heading runs in bold; a heading is not bold in Markdown
    text = re.sub(r"^(#{1,6}) \*\*(.+?)\*\*\s*$", r"\1 \2", text, flags=re.M)
    # the builder's appendix is not part of the post
    text = re.split(r"^#{1,6} \**남은 placeholder.*$", text, maxsplit=1, flags=re.M)[0]
    return text.rstrip() + "\n"


def docx_to_markdown(src: Path, work: Path) -> str:
    if not shutil.which("pandoc"):
        sys.exit("pandoc is required to read a .docx draft (apt install pandoc)")
    tmp = work / "_pandoc_input.docx"
    preprocess_docx(src, tmp)
    try:
        r = subprocess.run(
            ["pandoc", str(tmp), "-f", "docx+styles", "-t", "gfm", "--wrap=none", f"--extract-media={work}"],
            capture_output=True, text=True, check=True)
    finally:
        tmp.unlink(missing_ok=True)
    return postprocess_markdown(r.stdout)


def copy_images(text: str, src_dir: Path, work: Path) -> tuple[str, list[str], list[str]]:
    images_dir = work / "images"
    images_dir.mkdir(exist_ok=True)
    copied, missing = [], []

    def repl(m):
        p = m.group(2)
        if p.startswith("http"):
            return m.group(0)
        candidates = [src_dir / p, work / p, Path(p)]
        found = next((c for c in candidates if c.exists()), None)
        if found is None:
            missing.append(p)
            return m.group(0)
        dst = images_dir / found.name
        if not dst.exists():
            shutil.copyfile(found, dst)
        copied.append(found.name)
        return f"{m.group(1)}images/{found.name}{m.group(3)}"

    return IMAGE_RE.sub(repl, text), copied, missing


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("draft")
    ap.add_argument("--slug")
    ap.add_argument("--dir", default="blog-review")
    ap.add_argument("--in-place", action="store_true",
                    help="review inside the draft's own directory (a writer work dir): draft.md is copied "
                         "next to the source, images/ is used where it is, nothing else moves")
    args = ap.parse_args()

    src = Path(args.draft).resolve()
    if not src.exists():
        sys.exit(f"not found: {src}")
    if args.in_place:
        if src.suffix.lower() == ".docx":
            sys.exit("--in-place takes a Markdown draft; a Word file needs its own work dir")
        if src.name == "draft.md":
            sys.exit("--in-place needs a source other than draft.md (it writes draft.md next to the source)")
        work = src.parent
    else:
        slug = args.slug or re.sub(r"[^a-z0-9]+", "-", src.stem.lower()).strip("-") or "draft"
        work = Path(args.dir) / slug
        work.mkdir(parents=True, exist_ok=True)

    draft = work / "draft.md"
    if draft.exists():
        print(f"kept existing {draft}")
        text = draft.read_text(encoding="utf-8")
    else:
        if src.suffix.lower() == ".docx":
            text = docx_to_markdown(src, work)
        elif src.suffix.lower() in (".md", ".markdown", ".txt"):
            text = src.read_text(encoding="utf-8")
        else:
            sys.exit(f"unsupported draft type {src.suffix}; give .md or .docx")
        text, copied, missing = copy_images(text, src.parent, work)
        if (work / "media").is_dir():
            shutil.rmtree(work / "media")
        draft.write_text(text, encoding="utf-8")
        print(f"wrote {draft} ({len(text)} chars)")
        if copied:
            print(f"images copied: {', '.join(sorted(set(copied)))}")
        if missing:
            print(f"images NOT found (lint will flag them): {', '.join(missing)}")

    for tpl, name in ((WRITER_DIR / "templates" / "claims.md", "05-claims.md"),
                      (SKILL_DIR / "templates" / "review-report.md", "review-report.md")):
        target = work / name
        if target.exists():
            continue
        shutil.copyfile(tpl, target)
        print(f"created {target}")

    headings = len(re.findall(r"^#{2,3} ", text, flags=re.M))
    images = len(re.findall(r"^!\[", text, flags=re.M))
    fences = len(re.findall(r"^```", text, flags=re.M)) // 2
    body = re.sub(r"```.*?```", "", text, flags=re.S)
    korean = len(re.findall(r"[가-힣]", body))
    print(f"summary: {headings} headings, {images} images, {fences} code blocks, {korean} Korean characters")
    print(f"work: {work.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
