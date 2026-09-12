#!/usr/bin/env python3
"""Bake a rect <clipPath> applied to a <g> into real flattened geometry.

    python3 scripts/bake_icon_clips.py <svg_dir_or_files...> [--check]

`aws-ppt-master`'s SVG-to-PPTX exporter only maps `clip-path` natively on
`<image>` (references/shared-standards-core.md §1.2); `clip-path` on a `<g>`
is rejected, and a `<clipPath id="clippath">` def collides when the same
icon is embedded twice on one page. Several bundled AWS "split" icons (the
`agentcore-*` family) rely on such a clip to show only part of a secondary
glyph, and the clip is genuinely visible (pixel-tested, not dead code) — so
it can't just be stripped.

For every local `<clipPath>` containing exactly one `<rect>` (the clip rect
itself has no rx/ry/transform in this icon set) that some
`<g clip-path="url(#id)">` references: walk every
`<line>`/`<circle>`/`<ellipse>`/`<rect>`/`<path>` inside that group (paths
use only absolute M/L/C/Z; a leaf `<rect>` may have `rx`/`ry` -- a rounded
corner, or `transform="matrix(...)"`), turn each into fill geometry — a
stroked shape's outline via `Path.stroke()`, or the shape itself if it is
filled — intersect that geometry with the clip rect using `skia-pathops`,
and emit one flat `<path fill="...">` per leaf in its place. The
`<g clip-path=...>` wrapper and the `<defs><clipPath>...</clipPath></defs>`
are then removed entirely; everything else in the file is left byte-for-byte
untouched.

`--check`: compute the bake in memory (nothing is written) and print the
percentage of differing pixels between the original and baked render at
512px (cairosvg + PIL). A file must be under 0.5% to pass; anything at or
above that writes an outline-only diff mask PNG to --mask-dir (default
/tmp/bake_icon_clips_masks/<name>.mask.png) to inspect -- a thin outline
along shape edges is anti-aliasing, but a filled blob, a squared-off corner,
or a missing segment is a content bug and must not be waved through.
Without `--check`, the same numbers/masks are printed and files that
changed are written to disk.

Requires: skia-pathops (`pip install skia-pathops`), and for `--check`,
cairosvg + Pillow (`pip install cairosvg pillow`).
"""
import argparse
import re
import sys
from pathlib import Path
from xml.etree.ElementTree import Element

import defusedxml.ElementTree as ET

try:
    import pathops
except ImportError:
    sys.exit("skia-pathops is required: pip install skia-pathops")

SVG_NS = "http://www.w3.org/2000/svg"
LEAF_TAGS = {"line", "circle", "ellipse", "rect", "path"}

DEFS_CLIP_RE = re.compile(
    r'<defs><clipPath id="([^"]+)">\s*<rect ([^>]*?)/>\s*</clipPath></defs>'
)
ATTR_RE = re.compile(r'([\w:-]+)="([^"]*)"')
PATH_TOKEN_RE = re.compile(r'[MLCZ]|-?\d*\.?\d+(?:[eE][-+]?\d+)?')
MATRIX_RE = re.compile(r'matrix\(\s*([^)]+?)\s*\)')

CAP_MAP = {
    "butt": pathops.LineCap.BUTT_CAP,
    "round": pathops.LineCap.ROUND_CAP,
    "square": pathops.LineCap.SQUARE_CAP,
}
JOIN_MAP = {
    "miter": pathops.LineJoin.MITER_JOIN,
    "round": pathops.LineJoin.ROUND_JOIN,
    "bevel": pathops.LineJoin.BEVEL_JOIN,
}
KAPPA = 0.5522847498307936  # circle/ellipse 4-cubic-Bezier approximation constant


def parse_attrs(text: str) -> dict:
    return {k: v for k, v in ATTR_RE.findall(text)}


def fmt_num(x: float) -> str:
    r = round(x, 3)
    if r == 0:
        r = 0.0  # normalize -0.0
    if r == int(r):
        return str(int(r))
    return f"{r:.3f}".rstrip("0").rstrip(".")


# ---------------------------------------------------------------- geometry --

def parse_path_d(d: str):
    """Yield ('M'|'L'|'C'|'Z', tuple_of_floats), expanding implicit repeats.

    Per the SVG path grammar, a bare coordinate pair following 'M' (with no
    letter of its own) is an implicit *lineto*, not another moveto -- only
    the very first pair after 'M' actually moves the pen. Getting this wrong
    silently drops line segments (a compound path's inner "hole" subpath,
    e.g. a hollow bar-chart bar, can lose every one of its sides and render
    solid instead of hollow)."""
    tokens = PATH_TOKEN_RE.findall(d)
    argcount = {"M": 2, "L": 2, "C": 6, "Z": 0}
    i, n = 0, len(tokens)
    cur_cmd = None
    while i < n:
        tok = tokens[i]
        if tok in argcount:
            cur_cmd = tok
            i += 1
            if cur_cmd == "Z":
                yield ("Z", ())
                continue
        nargs = argcount[cur_cmd]
        nums = tuple(float(x) for x in tokens[i:i + nargs])
        i += nargs
        yield (cur_cmd, nums)
        if cur_cmd == "M":
            cur_cmd = "L"  # subsequent bare pairs are implicit linetos


def _drop_redundant_closing_segments(cmds):
    """Some source paths spell the close as an explicit L landing exactly on
    the subpath's start point, immediately followed by Z. Z always draws
    that same straight edge itself, so dropping the explicit L is a true
    no-op for *fill* geometry -- but it matters for *stroke* geometry:
    otherwise there are two coincident closing vertices (the explicit L's
    end and Z's own implicit edge), and Skia's round-join stroker can fuse
    a nearby notch into a solid wedge there (seen on the agentcore-gateway
    gear icon). Only L qualifies: every closed contour's *last* segment
    lands on the start point by definition (that's what "closed" means), so
    a C landing there is a normal closing curve, not a redundant one --
    dropping it would replace a curve with Z's straight line and visibly
    deform the shape (seen on the agentcore-browser-tool globe icon)."""
    cleaned = []
    start = None
    for cmd, args in cmds:
        if cmd == "M":
            start = args
        if cmd == "Z" and cleaned and start is not None:
            prev_cmd, prev_args = cleaned[-1]
            if prev_cmd == "L" and all(
                abs(a - b) < 1e-6 for a, b in zip(prev_args[-2:], start)
            ):
                cleaned.pop()
        cleaned.append((cmd, args))
    return cleaned


def path_from_d(d: str) -> "pathops.Path":
    path = pathops.Path()
    for cmd, args in _drop_redundant_closing_segments(list(parse_path_d(d))):
        if cmd == "M":
            path.moveTo(*args)
        elif cmd == "L":
            path.lineTo(*args)
        elif cmd == "C":
            path.cubicTo(*args)
        elif cmd == "Z":
            path.close()
    return path


def rect_path(x: float, y: float, w: float, h: float, rx: float = 0, ry: float = 0) -> "pathops.Path":
    """A <rect>, honouring rx/ry (SVG 7.4: clamp each to half the opposite
    side; a rounded corner is a quarter-ellipse, built the same way as
    ellipse_path's four cubics, one corner at a time)."""
    rx, ry = min(rx, w / 2), min(ry, h / 2)
    if rx <= 0 or ry <= 0:
        path = pathops.Path()
        path.moveTo(x, y)
        path.lineTo(x + w, y)
        path.lineTo(x + w, y + h)
        path.lineTo(x, y + h)
        path.close()
        return path
    k = KAPPA
    path = pathops.Path()
    path.moveTo(x + rx, y)
    path.lineTo(x + w - rx, y)
    path.cubicTo(x + w - rx + k * rx, y, x + w, y + ry - k * ry, x + w, y + ry)
    path.lineTo(x + w, y + h - ry)
    path.cubicTo(x + w, y + h - ry + k * ry, x + w - rx + k * rx, y + h, x + w - rx, y + h)
    path.lineTo(x + rx, y + h)
    path.cubicTo(x + rx - k * rx, y + h, x, y + h - ry + k * ry, x, y + h - ry)
    path.lineTo(x, y + ry)
    path.cubicTo(x, y + ry - k * ry, x + rx - k * rx, y, x + rx, y)
    path.close()
    return path


def ellipse_path(cx: float, cy: float, rx: float, ry: float) -> "pathops.Path":
    path = pathops.Path()
    path.moveTo(cx + rx, cy)
    path.cubicTo(cx + rx, cy + ry * KAPPA, cx + rx * KAPPA, cy + ry, cx, cy + ry)
    path.cubicTo(cx - rx * KAPPA, cy + ry, cx - rx, cy + ry * KAPPA, cx - rx, cy)
    path.cubicTo(cx - rx, cy - ry * KAPPA, cx - rx * KAPPA, cy - ry, cx, cy - ry)
    path.cubicTo(cx + rx * KAPPA, cy - ry, cx + rx, cy - ry * KAPPA, cx + rx, cy)
    path.close()
    return path


def line_path(x1: float, y1: float, x2: float, y2: float) -> "pathops.Path":
    path = pathops.Path()
    path.moveTo(x1, y1)
    path.lineTo(x2, y2)
    return path


def parse_matrix(transform: str):
    m = MATRIX_RE.search(transform)
    if not m:
        raise ValueError(f"unsupported transform (only matrix() is): {transform!r}")
    nums = [float(x) for x in re.split(r"[,\s]+", m.group(1).strip())]
    if len(nums) != 6:
        raise ValueError(f"matrix() needs 6 values, got {transform!r}")
    return tuple(nums)


def leaf_geometry(el: Element) -> "pathops.Path":
    tag = el.tag.split("}")[-1]
    if tag == "line":
        geo = line_path(*(float(el.get(a)) for a in ("x1", "y1", "x2", "y2")))
    elif tag == "circle":
        cx, cy, r = (float(el.get(a)) for a in ("cx", "cy", "r"))
        geo = ellipse_path(cx, cy, r, r)
    elif tag == "ellipse":
        geo = ellipse_path(*(float(el.get(a)) for a in ("cx", "cy", "rx", "ry")))
    elif tag == "rect":
        x, y, w, h = (float(el.get(a)) for a in ("x", "y", "width", "height"))
        rx_raw, ry_raw = el.get("rx"), el.get("ry")
        # SVG 7.4: if only one of rx/ry is given, the other equals it.
        rx = float(rx_raw) if rx_raw is not None else (float(ry_raw) if ry_raw is not None else 0)
        ry = float(ry_raw) if ry_raw is not None else (float(rx_raw) if rx_raw is not None else 0)
        geo = rect_path(x, y, w, h, rx, ry)
    elif tag == "path":
        geo = path_from_d(el.get("d"))
    else:
        raise ValueError(f"unsupported leaf tag <{tag}>")
    transform = el.get("transform")
    if transform:
        geo = geo.transform(*parse_matrix(transform))
    return geo


def leaf_fill_path_and_color(el: Element):
    """Return (fill-region Path, colour) for one leaf: the stroke outline if
    stroked, or the shape itself if filled. Exactly one of fill/stroke is
    ever set (not none) on these bundled icons."""
    geo = leaf_geometry(el)
    fill = el.get("fill")
    if fill and fill != "none":
        return geo, fill
    stroke = el.get("stroke")
    if not stroke or stroke == "none":
        raise ValueError("leaf has neither a real fill nor a real stroke")
    width = float(el.get("stroke-width", "1"))
    cap = CAP_MAP[el.get("stroke-linecap", "butt")]
    join = JOIN_MAP[el.get("stroke-linejoin", "miter")]
    miter = float(el.get("stroke-miterlimit", "4"))
    outline = pathops.Path(geo)
    outline.stroke(width, cap, join, miter)
    # Round joins/caps come back as conics; pathops.op() and .segments both
    # reject CONIC verbs, and SVG/DrawingML paths have no conic primitive.
    outline.convertConicsToQuads()
    # A stroked outline of a path with tight turns (e.g. a gear notch) can
    # self-overlap; resolve that to a simple region *before* intersecting
    # with the clip rect, or op() can fuse a hollow notch into a solid wedge.
    outline.simplify()
    return outline, stroke


def pathops_to_d(path: "pathops.Path") -> str:
    """Serialize to an SVG 'd' string using only M/L/C/Z. Quadratics (round
    stroke joins/caps, after convertConicsToQuads()) are degree-elevated to
    an exactly equivalent cubic: C1 = P0 + 2/3(Q-P0), C2 = P2 + 2/3(Q-P2)."""
    path.convertConicsToQuads()  # defensive: op()/simplify() can reintroduce conics
    parts = []
    cur = (0.0, 0.0)
    subpath_start = (0.0, 0.0)
    pending_moveto = True  # true right after closePath / at the very start
    for verb, points in path.segments:
        if verb == "qCurveTo" and pending_moveto and points[-1] is None:
            # A closed contour made entirely of off-curve points (e.g. a
            # circle reduced to conics-turned-quads) carries no moveTo at
            # all: the implied start/close point is the midpoint of the
            # last and first off-curve points. Emit the missing M ourselves.
            offs = points[:-1]
            mx, my = (offs[-1][0] + offs[0][0]) / 2, (offs[-1][1] + offs[0][1]) / 2
            parts.append(f"M{fmt_num(mx)} {fmt_num(my)}")
            cur = subpath_start = (mx, my)
        pending_moveto = False
        if verb == "moveTo":
            (x, y), = points
            parts.append(f"M{fmt_num(x)} {fmt_num(y)}")
            cur = subpath_start = (x, y)
        elif verb == "lineTo":
            (x, y), = points
            parts.append(f"L{fmt_num(x)} {fmt_num(y)}")
            cur = (x, y)
        elif verb in ("cubicTo", "curveTo"):
            (x1, y1), (x2, y2), (x3, y3) = points
            parts.append(
                f"C{fmt_num(x1)} {fmt_num(y1)} {fmt_num(x2)} {fmt_num(y2)} {fmt_num(x3)} {fmt_num(y3)}"
            )
            cur = (x3, y3)
        elif verb == "qCurveTo":
            # TrueType-style compact spline: N off-curve points then one true
            # on-curve point; an implied on-curve point sits at the midpoint
            # of each consecutive off-curve pair. Expand to N quads, then
            # degree-elevate each quad to an exactly equivalent cubic. A
            # trailing `None` (a contour with *no* real on-curve point, e.g.
            # a circle reduced to all-conic control points) means "closes
            # back to this subpath's start" instead of a literal endpoint.
            offs, end = points[:-1], points[-1]
            if end is None:
                end = subpath_start
            seg_ends = [((offs[i][0] + offs[i + 1][0]) / 2, (offs[i][1] + offs[i + 1][1]) / 2)
                        for i in range(len(offs) - 1)] + [end]
            for (qx, qy), (x, y) in zip(offs, seg_ends):
                x1, y1 = cur[0] + 2 / 3 * (qx - cur[0]), cur[1] + 2 / 3 * (qy - cur[1])
                x2, y2 = x + 2 / 3 * (qx - x), y + 2 / 3 * (qy - y)
                parts.append(f"C{fmt_num(x1)} {fmt_num(y1)} {fmt_num(x2)} {fmt_num(y2)} {fmt_num(x)} {fmt_num(y)}")
                cur = (x, y)
        elif verb in ("closePath", "close"):
            parts.append("Z")
            pending_moveto = True
        elif verb == "endPath":
            pending_moveto = True
        else:
            raise ValueError(f"unhandled path verb: {verb}")
    return "".join(parts)


# ------------------------------------------------------------- file surgery --

def find_g_span(text: str, start: int) -> int:
    """Given the index of the opening '<g clip-path=...>' tag, return the
    index just past its matching '</g>'."""
    depth = 0
    for m in re.finditer(r"<(/?)g\b[^>]*?(/?)>", text[start:]):
        if m.group(1):  # closing tag
            depth -= 1
            if depth == 0:
                return start + m.end()
        elif not m.group(2):  # opening tag, not self-closing
            depth += 1
    raise ValueError("unbalanced <g> tags")


def bake_svg_text(text: str):
    """Return (new_text, num_leaves_baked) or (None, 0) if there is nothing
    to bake (no <clipPath> present)."""
    defs_match = DEFS_CLIP_RE.search(text)
    if defs_match is None:
        return None, 0

    clip_id = defs_match.group(1)
    rect_attrs = parse_attrs(defs_match.group(2))
    clip_path = rect_path(
        float(rect_attrs["x"]), float(rect_attrs["y"]),
        float(rect_attrs["width"]), float(rect_attrs["height"]),
    )

    g_open_re = re.compile(r'<g clip-path="url\(#' + re.escape(clip_id) + r'\)">')
    g_match = g_open_re.search(text)
    if g_match is None:
        raise ValueError(f"no <g clip-path=\"url(#{clip_id})\"> found for its <clipPath>")
    g_start = g_match.start()
    g_end = find_g_span(text, g_start)
    g_span_text = text[g_start:g_end]

    frag = ET.fromstring(f'<root xmlns="{SVG_NS}">{g_span_text}</root>')
    outer_g = frag[0]
    leaves = [el for el in outer_g.iter() if el.tag.split("}")[-1] in LEAF_TAGS]

    baked_paths = []
    for el in leaves:
        shape_path, color = leaf_fill_path_and_color(el)
        clipped = pathops.op(shape_path, pathops.Path(clip_path), pathops.PathOp.INTERSECTION)
        clipped.simplify()
        d = pathops_to_d(clipped)
        if d:
            baked_paths.append(f'<path d="{d}" fill="{color}"/>')

    replacement = "".join(baked_paths)
    new_text = text[:g_start] + replacement + text[g_end:]
    new_text = new_text.replace(defs_match.group(0), "", 1)
    return new_text, len(leaves)


# --------------------------------------------------------------- pixel check --

CHECK_RESOLUTION = 512  # px; the pass bar (0.5%) is measured at this size


def render_diff(before: str, after: str, resolution: int = CHECK_RESOLUTION):
    """Return (diff_pct, PIL.Image outline-only mask) for before/after SVG text."""
    import io
    import cairosvg
    from PIL import Image, ImageChops

    png_before = cairosvg.svg2png(bytestring=before.encode("utf-8"), output_width=resolution, output_height=resolution)
    png_after = cairosvg.svg2png(bytestring=after.encode("utf-8"), output_width=resolution, output_height=resolution)
    img_before = Image.open(io.BytesIO(png_before)).convert("RGBA")
    img_after = Image.open(io.BytesIO(png_after)).convert("RGBA")
    diff = ImageChops.difference(img_before, img_after)
    data = list(diff.getdata())
    differing = sum(1 for px in data if any(px))
    mask = Image.new("L", diff.size)
    mask.putdata([255 if any(px) else 0 for px in data])
    return 100.0 * differing / len(data), mask


def render_diff_pct(before: str, after: str, resolution: int = CHECK_RESOLUTION) -> float:
    return render_diff(before, after, resolution)[0]


# ------------------------------------------------------------------- driver --

def iter_svg_files(paths):
    for p in paths:
        p = Path(p)
        if p.is_dir():
            yield from sorted(p.glob("*.svg"))
        else:
            yield p


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+", help="SVG files or directories to bake")
    ap.add_argument("--check", action="store_true", help="report the pixel diff without writing files")
    ap.add_argument("--mask-dir", default="/tmp/bake_icon_clips_masks",
                     help="where to write outline-only diff masks for files over the 0.5%% bar")
    args = ap.parse_args()

    worst = 0.0
    touched = 0
    for f in iter_svg_files(args.paths):
        text = f.read_text(encoding="utf-8")
        new_text, n_leaves = bake_svg_text(text)
        if new_text is None:
            continue
        pct, mask = render_diff(text, new_text)
        worst = max(worst, pct)
        status = "OK" if pct < 0.5 else "VISIBLE-DIFF"
        print(f"[{status}] {f.name}: {n_leaves} leaf shape(s) baked, diff={pct:.3f}%")
        if pct >= 0.5:
            mask_dir = Path(args.mask_dir)
            mask_dir.mkdir(parents=True, exist_ok=True)
            mask_path = mask_dir / f"{f.stem}.mask.png"
            mask.save(mask_path)
            print(f"        diff mask: {mask_path}")
        if not args.check:
            f.write_text(new_text, encoding="utf-8")
            touched += 1

    if args.check:
        print(f"\n[check] worst diff = {worst:.3f}% ({'PASS' if worst < 0.5 else 'FAIL'})")
    else:
        print(f"\n[bake] {touched} file(s) written; worst diff = {worst:.3f}%")
    return 0 if worst < 0.5 else 1


if __name__ == "__main__":
    sys.exit(main())
