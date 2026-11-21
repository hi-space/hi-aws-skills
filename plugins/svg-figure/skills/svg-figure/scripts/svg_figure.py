#!/usr/bin/env python3
"""Check, preview and export token-coloured SVG figures.

  python3 svg_figure.py check   fig.svg [page.html ...] [--prefix t1-] [--strict]
  python3 svg_figure.py preview fig.svg [more.svg ...] -o preview.html [--png preview.png]
  python3 svg_figure.py export  fig.src.svg -o fig.svg [--png fig.png] [--theme dark] [--bg paper] [--adaptive]

check   : contract errors (exit 1) and geometry warnings (exit 0, or 1 with --strict).
preview : one HTML page showing every figure in light, dark and at phone width.
export  : the deliverable. Replaces every var(--token) with the theme's hex value (default light)
          so the file looks the same in a browser, README, Word or PowerPoint; --png renders it.
          --adaptive embeds the tokens as a <style> block instead, so the file follows the
          viewer's light/dark setting (only for places whose background follows it too).

All commands take --tokens <css> (default: ../assets/figure-tokens.css) so a page with its own
palette checks and renders against its own values. Standard library only; --png needs Playwright.
"""
from __future__ import annotations

import argparse
import html
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple

DEFAULT_TOKENS = Path(__file__).resolve().parent.parent / "assets" / "figure-tokens.css"
ALLOWED_TAGS = {
    "svg", "g", "path", "rect", "circle", "ellipse", "line", "polyline", "polygon", "text", "tspan",
    "title", "desc", "defs", "marker", "linearGradient", "stop", "clipPath",
}
COLOR_ATTRS = {"fill", "stroke", "stop-color", "color"}
COLOR_KEYWORDS = {"none", "transparent", "currentColor"}
FONT_STACK = '"Pretendard","Apple SD Gothic Neo","Noto Sans KR","Malgun Gothic",system-ui,sans-serif'
SVG_RE = re.compile(r"<svg\b.*?</svg>", re.S)
VAR_RE = re.compile(r"var\(\s*(--[\w-]+)\s*\)")
URL_RE = re.compile(r"url\(\s*['\"]?([^)'\"]*)['\"]?\s*\)")
ROOT_RE = re.compile(r":root\s*\{([^}]*)\}")
DARK_RE = re.compile(r"@media[^{]*prefers-color-scheme\s*:\s*dark")
DECL_RE = re.compile(r"(--[\w-]+)\s*:\s*([^;}]+)")
TRANSLATE_RE = re.compile(r"^\s*translate\(\s*(-?[\d.]+)(?:[\s,]+(-?[\d.]+))?\s*\)\s*$")


# ── tokens ──────────────────────────────────────────────────────────────────────────────────

def load_tokens(path: Path) -> Tuple[Dict[str, str], Dict[str, str]]:
    """(light, dark) token maps from a CSS file with `:root{}` and a dark-scheme `:root{}`."""
    css = re.sub(r"/\*.*?\*/", "", Path(path).read_text(encoding="utf-8"), flags=re.S)
    dark_at = DARK_RE.search(css)
    light: Dict[str, str] = {}
    dark: Dict[str, str] = {}
    for block in ROOT_RE.finditer(css):
        decls = {k: v.strip() for k, v in DECL_RE.findall(block.group(1))}
        if dark_at and block.start() > dark_at.start():
            if not dark:
                dark = decls
        else:
            light.update(decls)
    if not light:
        raise SystemExit(f"{path}: no :root{{}} token block found")
    return light, {**light, **dark}


# ── check ───────────────────────────────────────────────────────────────────────────────────

def min_font_for(width: float) -> float:
    """Smallest font-size (viewBox units) that stays readable once the figure is scaled to its slot."""
    if width >= 900:
        return 15  # full-width figure on desktop
    if width <= 440:
        return 14  # drawn for a phone, shown near 1:1
    return 17      # column figure, shrinks to ~2/3 on a phone


def _num(value: Optional[str], default: float = 0.0) -> float:
    m = re.match(r"\s*(-?\d*\.?\d+)", value or "")
    return float(m.group(1)) if m else default


def _char_units(ch: str) -> float:
    o = ord(ch)
    if ch == " ":
        return 0.3
    if o >= 0x1100 and (o <= 0x11FF or 0x2460 <= o <= 0x24FF or 0x2E80 <= o <= 0xD7FF or 0xF900 <= o <= 0xFAFF
                        or 0xFF00 <= o <= 0xFFEF):
        return 1.0  # Hangul, CJK, circled numbers, full-width forms
    if ch.isupper() or ch.isdigit():
        return 0.62
    return 0.55


def text_width(text: str, size: float, bold: bool = False) -> float:
    return sum(_char_units(c) for c in text) * size * (1.05 if bold else 1.0)


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _crosses(seg: Tuple[float, float, float, float], box: Tuple[float, float, float, float]) -> bool:
    """Does the segment pass through the box? (Liang-Barsky clip.)"""
    x1, y1, x2, y2 = seg
    bx0, by0, bx1, by1 = box
    t0, t1 = 0.0, 1.0
    for p, q in ((x1 - x2, x1 - bx0), (x2 - x1, bx1 - x1), (y1 - y2, y1 - by0), (y2 - y1, by1 - y1)):
        if p == 0:
            if q < 0:
                return False
            continue
        t = q / p
        if p < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
    return t0 < t1


class Report:
    def __init__(self) -> None:
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def error(self, msg: str) -> None:
        if msg not in self.errors:
            self.errors.append(msg)

    def warn(self, msg: str) -> None:
        if msg not in self.warnings:
            self.warnings.append(msg)


def check_svg(src: str, tokens: Dict[str, str], prefix: Optional[str] = None,
              min_font: Optional[float] = None, seen_ids: Optional[set] = None) -> Report:
    rep = Report()
    seen_ids = seen_ids if seen_ids is not None else set()
    if re.search(r"<style\b|<script\b", src, re.I):
        rep.error("<style>/<script> inside the figure: colours come from the page tokens, nothing else")
    if re.search(r"<!DOCTYPE|<!ENTITY", src, re.I):
        rep.error("DOCTYPE/ENTITY declarations are not allowed")
        return rep
    try:
        root = ET.fromstring(re.sub(r'\sxmlns(:\w+)?="[^"]*"', "", src))
    except ET.ParseError as e:
        rep.error(f"not well-formed XML: {e}")
        return rep

    vb = [_num(v) for v in re.split(r"[\s,]+", (root.get("viewBox") or "").strip()) if v]
    if len(vb) != 4 or vb[2] <= 0 or vb[3] <= 0:
        rep.error('<svg> needs viewBox="0 0 W H"')
        vb = [0, 0, 0, 0]
    vx, vy, vw, vh = vb
    floor = min_font if min_font is not None else min_font_for(vw)
    if root.get("role") != "img":
        rep.error('<svg> needs role="img"')
    for attr in ("width", "height", "style"):
        if root.get(attr) is not None:
            rep.error(f'<svg {attr}="…"> fixes the size; the page scales the figure from its viewBox')

    kids = list(root)
    title = kids[0] if kids and _local(kids[0].tag) == "title" else None
    desc = kids[1] if len(kids) > 1 and _local(kids[1].tag) == "desc" else None
    if title is None or not (title.text or "").strip():
        rep.error("first child must be <title> with one sentence saying what the figure shows")
    if desc is None or not (desc.text or "").strip():
        rep.error("second child must be <desc> spelling out the relations the figure draws")
    labelled = (root.get("aria-labelledby") or "").split()
    for node, name in ((title, "title"), (desc, "desc")):
        if node is not None and (not node.get("id") or node.get("id") not in labelled):
            rep.error(f"<{name}> needs an id listed in the <svg> aria-labelledby")

    ids = {el.get("id") for el in root.iter() if el.get("id")}
    for i in sorted(ids):
        if prefix and not i.startswith(prefix):
            rep.error(f'id "{i}" does not start with the figure prefix "{prefix}"')
        if i in seen_ids:
            rep.error(f'id "{i}" is already used by another figure in this file')
    seen_ids |= ids

    rects: List[Tuple[float, float, float, float, bool]] = []  # x, y, w, h, filled
    circles: List[Tuple[float, float, float]] = []  # number badges sit on box edges by design
    segments: List[Tuple[float, float, float, float]] = []
    boxes: List[Tuple[str, float, float, float, float]] = []  # label, x0, y0, x1, y1

    def walk(el: ET.Element, dx: float, dy: float, placed: bool, size: Optional[float], anchor: str, bold: bool,
             in_text: bool) -> None:
        tag = _local(el.tag)
        if tag not in ALLOWED_TAGS:
            rep.error(f"<{tag}> is not allowed (allowed: {' '.join(sorted(ALLOWED_TAGS))})")
        for name, value in el.attrib.items():
            name = _local(name)
            if name.startswith("on") or name in ("href", "style", "font-family") and el is not root:
                rep.error(f'<{tag} {name}="…"> is not allowed')
            elif name == "font-family":
                rep.error("font-family on <svg>: the figure inherits the page font")
            for target in URL_RE.findall(value):
                if not target.startswith("#") or target[1:] not in ids:
                    rep.error(f"<{tag} {name}> points at url({target}); only url(#id) of an id in this figure")
            if name in COLOR_ATTRS and value not in COLOR_KEYWORDS and not URL_RE.fullmatch(value.strip()):
                m = VAR_RE.fullmatch(value.strip())
                if not m:
                    rep.error(f'<{tag} {name}="{value}">: write colours as var(--token), never a literal')
                elif m.group(1) not in tokens:
                    rep.error(f'<{tag} {name}="{value}">: unknown token (known: {" ".join(sorted(tokens))})')
                elif m.group(1) == "--key" and (name == "stroke" or tag in ("text", "tspan")):
                    rep.error(f"<{tag} {name}> uses --key; it is a background fill only (unreadable as ink)")
        tf = el.get("transform")
        if tf:
            m = TRANSLATE_RE.match(tf)
            if m:
                dx, dy = dx + float(m.group(1)), dy + float(m.group(2) or 0)
            else:
                placed = False  # rotated/scaled: positions below are not comparable
        if el.get("font-size"):
            size = _num(el.get("font-size"))
        anchor = el.get("text-anchor", anchor)
        if el.get("font-weight"):
            bold = el.get("font-weight") in ("bold", "bolder") or _num(el.get("font-weight")) >= 600
        if tag == "rect" and placed:
            rects.append((dx + _num(el.get("x")), dy + _num(el.get("y")), _num(el.get("width")), _num(el.get("height")),
                          el.get("fill", "black") != "none"))
        if tag == "circle" and placed:
            circles.append((dx + _num(el.get("cx")), dy + _num(el.get("cy")), _num(el.get("r"))))
        if tag == "line" and placed and el.get("stroke", "none") != "none":
            segments.append((dx + _num(el.get("x1")), dy + _num(el.get("y1")),
                             dx + _num(el.get("x2")), dy + _num(el.get("y2"))))
        if tag == "text":
            measure_text(el, dx, dy, placed and not el.get("rotate"), size, anchor, bold)
        for child in el:
            if in_text or tag == "text":
                if _local(child.tag) != "tspan":
                    rep.error(f"<{_local(child.tag)}> inside <text>")
                walk(child, dx, dy, placed, size, anchor, bold, True)
            else:
                walk(child, dx, dy, placed, size, anchor, bold, False)

    def measure_text(el: ET.Element, dx: float, dy: float, placed: bool, size: Optional[float], anchor: str,
                     bold: bool) -> None:
        middle = el.get("dominant-baseline") in ("middle", "central")
        x, y = _num(el.get("x")), _num(el.get("y"))
        lines: List[List] = [[x, y, (el.text or ""), size, bold]]
        for ts in el.iter():
            if ts is el:
                continue
            ts_size = _num(ts.get("font-size")) if ts.get("font-size") else size
            ts_bold = bold if not ts.get("font-weight") else (
                ts.get("font-weight") in ("bold", "bolder") or _num(ts.get("font-weight")) >= 600)
            if ts.get("x") is not None or ts.get("y") is not None or ts.get("dy") is not None:
                px, py = lines[-1][0], lines[-1][1]
                nx = _num(ts.get("x")) if ts.get("x") is not None else px
                ny = _num(ts.get("y")) if ts.get("y") is not None else py + _num(ts.get("dy"))
                lines.append([nx, ny, ts.text or "", ts_size, ts_bold])
            else:
                lines[-1][2] += ts.text or ""
                if ts_size and (lines[-1][3] is None or ts_size < lines[-1][3]):
                    lines[-1][3] = ts_size
            lines[-1][2] += ts.tail or ""
        for lx, ly, content, fs, fb in lines:
            content = " ".join(content.split())
            if not content:
                continue
            label = content if len(content) <= 24 else content[:23] + "…"
            if not fs:
                rep.error(f'text "{label}" has no font-size')
                continue
            if fs < floor:
                rep.error(f'text "{label}" is {fs:g}px; this {vw:g}-wide figure needs {floor:g}px or more '
                          "(cut labels or add height instead of shrinking type)")
            if not placed:
                continue
            w = text_width(content, fs, fb)
            x0 = dx + lx - (w / 2 if anchor == "middle" else w if anchor == "end" else 0)
            y0 = dy + ly - (fs * 0.5 if middle else fs * 0.82)
            boxes.append((label, x0, y0, x0 + w, y0 + fs * 1.05))

    walk(root, 0.0, 0.0, True, None, "start", False, False)

    for label, x0, y0, x1, y1 in boxes:
        if vw and (x0 < vx - 2 or x1 > vx + vw + 2 or y0 < vy - 2 or y1 > vy + vh + 2):
            rep.warn(f'text "{label}" runs outside the canvas (x {x0:.0f}–{x1:.0f}, y {y0:.0f}–{y1:.0f} '
                     f"in {vw:g}×{vh:g})")
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        holder = min((r for r in rects if r[0] <= cx <= r[0] + r[2] and r[1] <= cy <= r[1] + r[3]),
                     key=lambda r: r[2] * r[3], default=None)
        badge = any((cx - c[0]) ** 2 + (cy - c[1]) ** 2 <= c[2] ** 2 for c in circles)
        if holder and not badge and (x0 < holder[0] + 2 or x1 > holder[0] + holder[2] - 2):
            rep.warn(f'text "{label}" (≈{x1 - x0:.0f} wide) overflows its {holder[2]:g}-wide box; '
                     "widen the box or break the label into two <tspan> lines")
        # a label in a filled pill or chip sits on top of the line it names: the fill hides the line
        covered = holder is not None and holder[4]

        def inside(seg, r=holder):
            return all(r[0] <= seg[i] <= r[0] + r[2] and r[1] <= seg[i + 1] <= r[1] + r[3] for i in (0, 2))

        if any(_crosses(seg, (x0 + 1, y0 + 3, x1 - 1, y1 - 3)) and not (covered and not inside(seg))
               for seg in segments):
            rep.warn(f'a line runs through text "{label}"; move the label beside the line or put it in a pill')
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            if min(a[3], b[3]) - max(a[1], b[1]) > 3 and min(a[4], b[4]) - max(a[2], b[2]) > 3:
                rep.warn(f'text "{a[0]}" overlaps text "{b[0]}"')
    return rep


def find_svgs(path: Path) -> List[str]:
    return SVG_RE.findall(path.read_text(encoding="utf-8"))


def cmd_check(args: argparse.Namespace) -> int:
    tokens, _ = load_tokens(args.tokens)
    failed = False
    for path in args.files:
        svgs = find_svgs(Path(path))
        if not svgs:
            print(f"{path}: FAIL\n  error: no <svg>…</svg> found")
            failed = True
            continue
        seen: set = set()
        for n, src in enumerate(svgs, 1):
            rep = check_svg(src, tokens, args.prefix, args.min_font, seen)
            bad = bool(rep.errors) or (args.strict and bool(rep.warnings))
            failed |= bad
            name = path if len(svgs) == 1 else f"{path} [svg {n}]"
            print(f"{name}: {'FAIL' if bad else 'ok'}"
                  + (f" ({len(rep.warnings)} warning(s) to look at in the preview)" if rep.warnings and not bad else ""))
            for e in rep.errors:
                print(f"  error: {e}")
            for w in rep.warnings:
                print(f"  warning: {w}")
    return 1 if failed else 0


# ── preview ─────────────────────────────────────────────────────────────────────────────────

def _decls(tokens: Dict[str, str]) -> str:
    return "".join(f"{k}:{v};" for k, v in tokens.items())


def build_preview(figures: List[Tuple[str, str]], light: Dict[str, str], dark: Dict[str, str]) -> str:
    rows = []
    for name, svg in figures:
        vb = re.search(r'viewBox="[\d.\-]+[\s,]+[\d.\-]+[\s,]+([\d.]+)', svg)
        width = int(float(vb.group(1))) if vb else 560
        svg = re.sub(r'\sclass="ov-(wide|tall)"', "", svg)
        cells = "".join(
            f'<div class="cell {theme}" style="width:{w + 34}px"><p>{label}</p><figure class="fig">{svg_i}</figure></div>'
            for theme, w, label, svg_i in (
                ("t-light", width, f"light · {width}px", svg),
                ("t-dark", width, f"dark · {width}px", re.sub(r'\bid="', 'id="d-', re.sub(r"url\(#", "url(#d-", re.sub(
                    r'aria-labelledby="([^"]*)"', lambda m: 'aria-labelledby="' + " ".join(
                        "d-" + i for i in m.group(1).split()) + '"', svg)))),
                ("t-light", 326, "phone · 360px", re.sub(r'\bid="', 'id="p-', re.sub(r"url\(#", "url(#p-", re.sub(
                    r'aria-labelledby="([^"]*)"', lambda m: 'aria-labelledby="' + " ".join(
                        "p-" + i for i in m.group(1).split()) + '"', svg)))),
            ) if not (label.startswith("phone") and width <= 440))
        rows.append(f"<h2>{html.escape(name)}</h2><div class=\"row\">{cells}</div>")
    return (
        '<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>figure preview</title><style>'
        f".t-light{{{_decls(light)}}}.t-dark{{{_decls(dark)}}}"
        f"body{{margin:0;padding:24px;background:#fff;font-family:{FONT_STACK};font-size:16px}}"
        "h2{font-size:15px;margin:24px 0 8px;color:#333}.row{display:flex;flex-wrap:wrap;gap:16px;align-items:flex-start}"
        ".cell{background:var(--paper);color:var(--ink);padding:12px;border-radius:8px;box-sizing:content-box}"
        ".cell p{margin:0 0 8px;font-size:12px;color:var(--muted)}"
        "figure{margin:0}figure svg{display:block;width:100%;height:auto}"
        ".fig{background:var(--soft,var(--panel));border:1px solid var(--line);border-radius:8px;padding:16px}"
        f"</style></head><body>{''.join(rows)}</body></html>"
    )


def screenshot(target: Path, out: Path, scale: float = 1.0, selector: Optional[str] = None) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit("--png needs Playwright: pip install playwright && playwright install chromium")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1400, "height": 900}, device_scale_factor=scale)
        page.goto(target.resolve().as_uri())
        if selector:
            page.locator(selector).screenshot(path=str(out), omit_background=True)
        else:
            page.screenshot(path=str(out), full_page=True)
        browser.close()


def cmd_preview(args: argparse.Namespace) -> int:
    light, dark = load_tokens(args.tokens)
    figures = []
    for path in args.files:
        svgs = find_svgs(Path(path))
        figures += [(Path(path).name if len(svgs) == 1 else f"{Path(path).name} [svg {n}]", s)
                    for n, s in enumerate(svgs, 1)]
    if not figures:
        raise SystemExit("no <svg> found in the given files")
    out = Path(args.out)
    out.write_text(build_preview(figures, light, dark), encoding="utf-8")
    print(f"wrote {out} ({len(figures)} figure(s): light, dark, phone)")
    if args.png:
        screenshot(out, Path(args.png))
        print(f"wrote {args.png}; open it and read every label before delivering")
    return 0


# ── export ──────────────────────────────────────────────────────────────────────────────────

def export_svg(src: str, light: Dict[str, str], dark: Dict[str, str], flat: Optional[str] = "light",
               bg: Optional[str] = None) -> str:
    """flat="light"/"dark" resolves tokens to hex; flat=None keeps var() and embeds both themes."""
    head = re.match(r"<svg\b[^>]*>", src)
    if not head:
        raise SystemExit("not an <svg>")
    tag = re.sub(r'\sclass="ov-(wide|tall)"', "", head.group(0))
    if "xmlns=" not in tag:
        tag = tag.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
    tag = tag[:-1] + f" font-family='{FONT_STACK}'>"
    body = src[head.end():]
    vb = re.search(r'viewBox="([\d.\-]+)[\s,]+([\d.\-]+)[\s,]+([\d.]+)[\s,]+([\d.]+)"', tag)
    extra = ""
    if bg and vb:
        x, y, w, h = vb.groups()
        extra = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="var(--{bg.lstrip("-")})"/>'
    if not flat:
        extra = (f"<style>:root{{{_decls(light)}}}@media (prefers-color-scheme:dark){{:root{{{_decls(dark)}}}}}"
                 "</style>") + extra
    at = body.find("</desc>")
    at = at + len("</desc>") if at != -1 else 0
    out = tag + body[:at] + extra + body[at:]
    if flat:
        values = dark if flat == "dark" else light
        missing = sorted({m for m in VAR_RE.findall(out) if m not in values})
        if missing:
            raise SystemExit(f"unknown token(s): {' '.join(missing)}")
        out = VAR_RE.sub(lambda m: values[m.group(1)], out)
    return out


def cmd_export(args: argparse.Namespace) -> int:
    light, dark = load_tokens(args.tokens)
    svgs = find_svgs(Path(args.file))
    if len(svgs) != 1:
        raise SystemExit(f"{args.file}: expected exactly one <svg>, found {len(svgs)}")
    out = Path(args.out)
    flat = None if args.adaptive else args.theme
    out.write_text(export_svg(svgs[0], light, dark, flat, args.bg) + "\n", encoding="utf-8")
    print(f"wrote {out} ({flat + ' theme' if flat else 'adaptive, follows light/dark'})")
    if args.png:
        vb = re.search(r'viewBox="[\d.\-]+[\s,]+[\d.\-]+[\s,]+([\d.]+)', svgs[0])
        width = float(vb.group(1)) if vb else 560
        sheet = out.with_suffix(".png-sheet.html")
        sheet.write_text('<!doctype html><meta charset="utf-8"><body style="margin:0">'
                         f'<img src="{out.name}" style="display:block;width:{width:g}px">', encoding="utf-8")
        try:
            screenshot(sheet, Path(args.png), scale=args.scale, selector="img")
        finally:
            sheet.unlink()
        print(f"wrote {args.png} ({width * args.scale:g}px wide)")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--tokens", type=Path, default=DEFAULT_TOKENS, help="CSS file with the :root token blocks")

    c = sub.add_parser("check", parents=[common], help="contract errors + geometry warnings")
    c.add_argument("files", nargs="+", help=".svg files, or .html pages with inline figures")
    c.add_argument("--prefix", help="every id must start with this (use with one figure per file)")
    c.add_argument("--min-font", type=float, help="override the font floor derived from the viewBox width")
    c.add_argument("--strict", action="store_true", help="warnings fail too")
    c.set_defaults(fn=cmd_check)

    p = sub.add_parser("preview", parents=[common], help="HTML sheet: light, dark, phone")
    p.add_argument("files", nargs="+")
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--png", help="also screenshot the sheet (Playwright)")
    p.set_defaults(fn=cmd_preview)

    e = sub.add_parser("export", parents=[common], help="deliverable .svg with colours resolved, optional .png")
    e.add_argument("file")
    e.add_argument("-o", "--out", required=True)
    e.add_argument("--theme", choices=["light", "dark"], default="light", help="theme to resolve tokens to")
    e.add_argument("--adaptive", action="store_true", help="keep tokens and embed both themes as <style>")
    e.add_argument("--bg", help="token to paint behind the figure, e.g. soft or paper")
    e.add_argument("--png", help="also render a PNG (Playwright)")
    e.add_argument("--scale", type=float, default=2.0, help="PNG pixel ratio (default 2)")
    e.set_defaults(fn=cmd_export)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
