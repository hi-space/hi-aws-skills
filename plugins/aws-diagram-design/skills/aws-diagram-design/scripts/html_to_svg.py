#!/usr/bin/env python3
"""Lift the diagram <svg> out of a 1.x aws-diagram-design HTML page into a standalone .svg.

    python3 <skill-dir>/scripts/html_to_svg.py page.html [more.html …] [--out DIR] [--delete-source] [--no-font-face]

Keeps: the outer <svg> (nested icon <svg>s included), the page CSS rules that style SVG content
(class/id selectors used inside the svg, svg-element selectors, :root when var() is used), a local()
@font-face block. Drops: header/cards/footer, body/page CSS, @font-face/@keyframes from the page.
<foreignObject> field values become single-line <text>. Run finalize.py on the result to check,
embed fonts, and render PNG.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import finalize  # noqa: E402

XML_HEADER = '<?xml version="1.0" encoding="UTF-8"?>\n'
SVG_ELEMENTS = {"svg", "g", "text", "tspan", "rect", "path", "circle", "ellipse", "line", "polyline", "polygon", "use", "marker", "defs", "symbol", "image", "title", "desc", "textPath", "clipPath", "mask", "pattern", "filter"}
FOREIGN_RE = re.compile(
    r'<foreignObject x="(?P<x>[\d.]+)" y="(?P<y>[\d.]+)" width="[\d.]+" height="[\d.]+">\s*'
    r'<div[^>]*class="(?P<cls>[^"]*)"[^>]*>(?P<text>.*?)</div>\s*</foreignObject>',
    re.S,
)


def extract_svg(html_text: str) -> str:
    start = None
    for m in re.finditer(r"<!--.*?-->|<svg\b", html_text, re.S):
        if m.group(0).startswith("<svg"):
            start = m
            break
    if start is None:
        raise ValueError("no <svg> block in source")
    depth = 0
    for m in re.finditer(r"<svg\b|</svg\s*>", html_text[start.start():]):
        depth += 1 if m.group(0).startswith("<svg") else -1
        if depth == 0:
            return html_text[start.start(): start.start() + m.end()]
    raise ValueError("unterminated <svg> block")


def _rules(css: str) -> list[tuple[str, str]]:
    """Flatten CSS into (selector, body); @media bodies are recursed, other at-rules dropped."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    rules: list[tuple[str, str]] = []
    depth, start, body_start, sel = 0, 0, 0, ""
    for j, ch in enumerate(css):
        if ch == "{":
            if depth == 0:
                sel, body_start = css[start:j].strip(), j + 1
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                body = css[body_start:j]
                if sel.startswith("@media"):
                    rules.extend(_rules(body))
                elif not sel.startswith("@"):
                    rules.append((sel, " ".join(body.split())))
                start = j + 1
    return rules


def _selector_applies(selector: str, classes: set[str], ids: set[str]) -> bool:
    if selector == ":root" or selector.startswith(":root"):
        return False  # :root retention is decided separately in relevant_css, once kept rules are known
    elements = [t for t in re.split(r"[\s>+~]+", re.sub(r"[.#:\[][^\s>+~]*", "", selector)) if t]
    if elements == ["svg"]:
        return False  # bare root-svg selector (e.g. "svg", "svg:root") is page layout, not content styling
    if re.search(r"\bsvg\b", selector):
        return True
    if any(re.search(rf"\.{re.escape(c)}(?![\w-])", selector) for c in classes):
        return True
    if any(re.search(rf"#{re.escape(i)}(?![\w-])", selector) for i in ids):
        return True
    return bool(elements) and all(e in SVG_ELEMENTS for e in elements)


def relevant_css(css: str, svg: str) -> str:
    classes = {c for group in re.findall(r'class="([^"]+)"', svg) for c in group.split()}
    ids = set(re.findall(r'id="([^"]+)"', svg))
    rules = _rules(css)
    kept_bodies: list[tuple[str, str]] = []
    kept: list[str] = []
    for selector, body in rules:
        parts = [p.strip() for p in selector.split(",") if _selector_applies(p.strip(), classes, ids)]
        if parts:
            kept_bodies.append((selector, body))
            kept.append(f"{', '.join(parts)} {{ {body} }}")
    uses_var = "var(" in svg or any("var(" in body for _, body in kept_bodies)
    if uses_var:
        roots = [f"{selector} {{ {body} }}" for selector, body in rules if selector == ":root" or selector.startswith(":root")]
        kept = roots + kept
    return "\n".join(kept)


def replace_foreign_objects(svg: str) -> str:
    def to_text(m: re.Match) -> str:
        text = " ".join(re.sub(r"<[^>]+>", "", m.group("text")).split())
        y = float(m.group("y")) + 16  # 24px box, 1.25 line-height → first baseline
        return f'<text x="{m.group("x")}" y="{y:g}" class="{m.group("cls")}">{text}</text>'

    out = FOREIGN_RE.sub(to_text, svg)
    if "<foreignObject" in out:
        raise ValueError("a <foreignObject> did not match the field-value shape; convert it by hand")
    return out


def convert(html_text: str, *, font_face: bool = True) -> str:
    svg = replace_foreign_objects(extract_svg(html_text))
    page_css = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html_text, re.S))
    css = relevant_css(page_css, svg)
    block = "\n".join(part for part in ((finalize.LOCAL_FONT_FACE_CSS if font_face else ""), css) if part)
    if block:
        svg = finalize.inject_style(svg, block, "page-css")
    open_tag_end = svg.index(">")
    if "xmlns=" not in svg[:open_tag_end]:
        svg = svg[:4] + ' xmlns="http://www.w3.org/2000/svg"' + svg[4:]
    return XML_HEADER + svg.strip() + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, help="default: next to each source")
    ap.add_argument("--delete-source", action="store_true")
    ap.add_argument("--no-font-face", action="store_true")
    a = ap.parse_args(argv)
    failed = False
    for src in a.files:
        try:
            text = convert(src.read_text(encoding="utf-8"), font_face=not a.no_font_face)
        except ValueError as exc:
            print(f"FAIL {src}: {exc}", file=sys.stderr)
            failed = True
            continue
        out = (a.out or src.parent) / (src.stem + ".svg")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        if a.delete_source:
            src.unlink()
        print(f"svg {out}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
