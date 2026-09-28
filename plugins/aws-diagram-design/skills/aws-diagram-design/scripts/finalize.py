#!/usr/bin/env python3
"""Finish a standalone diagram SVG: check → embed Amazon Ember → render PNG.

    python3 <skill-dir>/scripts/finalize.py diagram.svg [--scale 2] [--png-dir DIR] [--no-png] [--check-only]

The SVG is the deliverable and the only source of truth (spec 2026-09-28). Steps:
1. check   — well-formed XML, accessible-SVG contract, single-file safety, label-mask geometry
             (self_check.verify_svg + verify-geometry.check). Any failure: file untouched, exit 1.
2. fonts   — embed only the Amazon Ember faces the file uses as base64 woff2 (idempotent).
3. png     — Chromium screenshot of the <svg> at viewBox × scale, via an in-memory HTML shell that
             adds Noto Sans KR only when the text contains Hangul. Missing Playwright: skip with a hint.
"""
from __future__ import annotations

import argparse
import base64
import importlib.util
import re
import sys
from collections import namedtuple
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
FONT_DIR = SKILL_DIR / "assets" / "fonts" / "woff2"
KR_FONTS = "https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap"
FONT_MARKER = "finalize:fonts"

Face = namedtuple("Face", "family weight style locals file")
FACES = [
    Face("Amazon Ember", 300, "normal", ("Amazon Ember Light", "Amazon Ember"), "AmazonEmber_W_Lt.woff2"),
    Face("Amazon Ember", 400, "normal", ("Amazon Ember",), "AmazonEmber_W_Rg.woff2"),
    Face("Amazon Ember", 400, "italic", ("Amazon Ember Italic", "Amazon Ember"), "AmazonEmber_W_RgIt.woff2"),
    Face("Amazon Ember", 600, "normal", ("Amazon Ember Medium", "Amazon Ember"), "AmazonEmber_W_SBd.woff2"),
    Face("Amazon Ember", 700, "normal", ("Amazon Ember Bold", "Amazon Ember"), "AmazonEmber_W_Bd.woff2"),
    Face("Amazon Ember", 800, "normal", ("Amazon Ember Heavy", "Amazon Ember"), "AmazonEmber_W_He.woff2"),
    Face("Amazon Ember Mono", 400, "normal", ("Amazon Ember Mono",), "AmazonEmberMono_W_Rg.woff2"),
    Face("Amazon Ember Mono", 700, "normal", ("Amazon Ember Mono Bold", "Amazon Ember Mono"), "AmazonEmberMono_W_Bd.woff2"),
]
# CSS font matching: 500 falls back down to 400, 600 climbs to 600/700 — embed what the browser will pick.
SANS_SNAP = {100: 300, 200: 300, 300: 300, 400: 400, 500: 400, 600: 600, 700: 700, 800: 800, 900: 800}
WEIGHT_RE = re.compile(r"font-weight\s*[:=]\s*['\"]?\s*(\d{3}|bold|normal|bolder|lighter)", re.I)
SHORTHAND_RE = re.compile(r"\bfont\s*:\s*(?:(italic)\s+)?(?:normal\s+)?(\d{3}|bold)?\b", re.I)
ITALIC_RE = re.compile(r"font-style\s*[:=]\s*['\"]?\s*italic", re.I)
HANGUL_RE = re.compile(r"[가-힣ᄀ-ᇿ㄰-㆏]")


def _load_sibling(name: str):
    """Import a sibling script whose filename may contain a hyphen."""
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), Path(__file__).with_name(f"{name}.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _weight(token: str) -> int:
    t = token.lower()
    return {"bold": 700, "bolder": 700, "normal": 400, "lighter": 300}.get(t) or int(t)


CHUNK_RE = re.compile(r"<[^>]+>|\{[^{}]*\}")  # one element start tag, or one CSS rule body


def _snap(family: str, weight: int) -> int:
    if family == "Amazon Ember Mono":
        return 400 if weight <= 500 else 700
    return SANS_SNAP.get(weight, 400)


def used_faces(svg_text: str) -> list[Face]:
    """Faces the browser will actually pick. Weights are read per element / CSS rule so a bold sans
    label does not drag Mono Bold in; a chunk with a weight but no family applies to every family present."""
    present = [fam for fam in ("Amazon Ember", "Amazon Ember Mono") if fam in svg_text]
    wanted: set[tuple[str, int, str]] = {(fam, 400, "normal") for fam in present}
    for chunk in CHUNK_RE.findall(svg_text):
        weights = {_weight(w) for w in WEIGHT_RE.findall(chunk)}
        italic = bool(ITALIC_RE.search(chunk))
        for it, w in SHORTHAND_RE.findall(chunk):
            if w:
                weights.add(_weight(w))
            if it:
                italic = True
        if not weights and not italic:
            continue
        if "Amazon Ember Mono" in chunk:
            families = ["Amazon Ember Mono"]
        elif "Amazon Ember" in chunk:
            families = ["Amazon Ember"]
        else:
            families = present
        for fam in families:
            wanted |= {(fam, _snap(fam, w), "normal") for w in weights}
            if italic and fam == "Amazon Ember":
                wanted.add((fam, 400, "italic"))
    return [f for f in FACES if (f.family, f.weight, f.style) in wanted]


def _src(face: Face, embed: bool) -> str:
    locals_ = ", ".join(f"local('{name}')" for name in face.locals)
    if not embed:
        return locals_
    data = base64.b64encode((FONT_DIR / face.file).read_bytes()).decode("ascii")
    return f"{locals_}, url(data:font/woff2;base64,{data}) format('woff2')"


def font_face_css(faces: list[Face], embed: bool) -> str:
    return "\n".join(
        f"@font-face {{ font-family: '{f.family}'; font-weight: {f.weight}; font-style: {f.style}; src: {_src(f, embed)}; }}"
        for f in faces
    )


LOCAL_FONT_FACE_CSS = font_face_css(FACES, embed=False)

FONT_FACE_RULE_RE = re.compile(r"\s*@font-face\s*\{[^{}]*Amazon Ember[^{}]*\}", re.I)


def inject_style(svg_text: str, css: str, marker: str) -> str:
    block = f"/* {marker} */\n{css}\n/* /{marker} */"
    marked = re.compile(rf"\s*/\* {re.escape(marker)} \*/.*?/\* /{re.escape(marker)} \*/", re.S)
    if marked.search(svg_text):
        return marked.sub("\n" + block, svg_text, count=1)
    m = re.search(r"<defs\b[^>]*>\s*<style\b[^>]*>(\s*<!\[CDATA\[)?", svg_text)
    if m:
        return svg_text[: m.end()] + "\n" + block + svg_text[m.end() :]
    m = re.search(r"<defs\b[^>]*>", svg_text)
    if m:
        return svg_text[: m.end()] + f"\n    <style>\n{block}\n    </style>" + svg_text[m.end() :]
    m = re.search(r"</desc>", svg_text)
    if not m:
        raise ValueError("svg has no <desc>; cannot place <defs>")
    return svg_text[: m.end()] + f"\n  <defs>\n    <style>\n{block}\n    </style>\n  </defs>" + svg_text[m.end() :]


def embed_fonts(svg_text: str) -> str:
    stripped = FONT_FACE_RULE_RE.sub("", svg_text)
    stripped = re.sub(r"\s*/\* fonts \*/\s*/\* /fonts \*/", "", stripped)  # empty marker left by templates
    return inject_style(stripped, font_face_css(used_faces(stripped), embed=True), FONT_MARKER)


def run_checks(path: Path) -> list[str]:
    errors = _load_sibling("self_check").verify_svg(path)
    if errors:
        return errors  # geometry regexes are meaningless on malformed XML
    return _load_sibling("verify-geometry").check(path)


def has_hangul(text: str) -> bool:
    return bool(HANGUL_RE.search(text))


def viewbox(svg_text: str) -> tuple[float, float]:
    m = re.search(r'viewBox="\s*[-\d.]+\s+[-\d.]+\s+([\d.]+)\s+([\d.]+)\s*"', svg_text)
    if not m:
        raise ValueError("svg has no viewBox")
    return float(m.group(1)), float(m.group(2))


def html_shell(svg_text: str, w: float, h: float) -> str:
    """Minimal in-memory page: fonts come from the SVG's own @font-face; Noto Sans KR only for Hangul."""
    body = svg_text.split("?>", 1)[1] if svg_text.lstrip().startswith("<?xml") else svg_text
    kr = f'<link href="{KR_FONTS}" rel="stylesheet">' if has_hangul(svg_text) else ""
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\">" + kr +
        f"<style>html,body{{margin:0;padding:0;background:transparent}}"
        f"svg{{display:block;width:{w:g}px !important;height:{h:g}px !important;"
        f"min-width:0 !important;max-width:none !important;min-height:0 !important;max-height:none !important}}</style>"
        f"</head><body>{body}</body></html>"
    )


def render_png(svg_text: str, out: Path, scale: float) -> bool:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright isn't installed; SVG written, PNG skipped. To enable PNG:\n  pip install playwright\n  playwright install chromium", file=sys.stderr)
        return False
    w, h = viewbox(svg_text)
    out.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(device_scale_factor=scale, viewport={"width": int(w) + 16, "height": int(h) + 16})
        page.set_content(html_shell(svg_text, w, h), wait_until="load")
        try:
            page.wait_for_load_state("networkidle", timeout=5000)  # Noto Sans KR stylesheet, when present
        except Exception:
            print("warning: webfont request did not settle (offline?); Hangul may use an installed fallback", file=sys.stderr)
        page.evaluate("document.fonts.ready")
        page.locator("svg").first.screenshot(path=str(out), omit_background=True)
        browser.close()
    return True


def png_size(path: Path) -> tuple[int, int]:
    import struct
    with path.open("rb") as fh:
        head = fh.read(24)
    return struct.unpack(">II", head[16:24])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("svg", type=Path)
    ap.add_argument("--scale", type=float, default=2.0, help="PNG device scale factor, 1–4 (fractional allowed)")
    ap.add_argument("--png-dir", type=Path, help="default: next to the SVG")
    ap.add_argument("--no-png", action="store_true")
    ap.add_argument("--check-only", action="store_true")
    a = ap.parse_args(argv)
    if not 1 <= a.scale <= 4:
        ap.error("--scale must be within 1..4 (see references/export.md § Sizing)")
    if a.svg.suffix.lower() != ".svg":
        print(f"finalize.py takes a .svg; for motion .html use references/export.md", file=sys.stderr)
        return 2
    errors = run_checks(a.svg)
    if errors:
        print(f"FAIL {a.svg}")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"OK {a.svg}")
    if a.check_only:
        return 0
    text = a.svg.read_text(encoding="utf-8")
    a.svg.write_text(embed_fonts(text), encoding="utf-8")
    print(f"fonts embedded: {a.svg}")
    if a.no_png:
        return 0
    out = (a.png_dir or a.svg.parent) / (a.svg.stem + ".png")
    if render_png(a.svg.read_text(encoding="utf-8"), out, a.scale):
        w, h = png_size(out)
        print(f"png: {out} ({w}×{h})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
