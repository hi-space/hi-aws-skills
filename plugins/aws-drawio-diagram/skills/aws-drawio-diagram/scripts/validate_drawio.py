#!/usr/bin/env python3
"""Validate .drawio files produced by the aws-drawio-diagram skill.

Errors (exit 1):
  E1  mxgraph.aws4 name (shape / resIcon / prIcon / grIcon) not in stencil-index.json
  E2  service-level icon (resourceIcon/productIcon) without strokeColor=#ffffff,
      or resource-level stencil without strokeColor=none
  E3  edge without source/target, or pointing at a missing cell
  E4  group container (shape=mxgraph.aws4.group*) without container=1
  E5  duplicate cell id
  E6  XML comment, DOCTYPE/ENTITY declaration, or compressed <diagram> payload
Warnings:
  W1  orthogonalEdgeStyle edge without exitX/entryX (routing may wander)
  W2  aws4 icon without fillColor (renders white in PNG export)
  W3  group container without dropTarget=1
  W4  edge whose ports do not form a straight line or a single L (it would need two bends)
  W5  straight or single-bend edge whose path passes through an unconnected icon's bounding box
  W6  icon drawn inside an AWS Cloud group but not a child of a role group
  W7  edge label whose box covers a group/cloud border or title row, an icon, another label or another
      edge's line (shift it along its edge with mxGeometry x, or move a node)
  W8  two edges with overlapping collinear segments — they render as one line (bent edges touching one side of a
      node must leave from different ports, side by side, as build_diagram.py draws them)
  W9  icon with no edge at all (a floating component)
W4–W9 are layout defects: the exit status is 1 when any is present, like an error. W1–W3 are style hints.

Usage: validate_drawio.py FILE [FILE ...]
Adapted from vidanov/aws-architecture-diagram-skill tests/validate_drawio.py (MIT).
"""
from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
INDEX = HERE / "stencil-index.json"

SERVICE_FRAMES = {"resourceIcon", "productIcon"}
GROUP_SHAPES = {"group", "group2", "groupCenter"}
LAYOUT_DEFECTS = {"W4", "W5", "W6", "W7", "W8", "W9"}
RE_AWS4 = re.compile(r"mxgraph\.aws4\.([A-Za-z0-9_]+)")


def load_index(path: Path = INDEX) -> dict:
    data = json.loads(path.read_text())
    return {"names": set(data["stencils"]), "js_shapes": set(data["js_shapes"])}


def parse_style(style: str | None) -> dict[str, str]:
    out: dict[str, str] = {}
    for part in (style or "").split(";"):
        if not part:
            continue
        k, _, v = part.partition("=")
        out[k] = v
    return out


def _aws4_name(value: str) -> str | None:
    m = RE_AWS4.search(value or "")
    return m.group(1) if m else None


ALIGN_TOLERANCE = 4.0
# An L edge may run any distance along its two legs; W5 checks both corridors for icons.


def _abs_geometry(cells: dict[str, ET.Element]) -> dict[str, tuple[float, float, float, float]]:
    """Absolute (x, y, w, h) for every vertex with geometry, resolving container parents."""
    geo: dict[str, tuple[float, float, float, float]] = {}

    def resolve(cid: str, seen: tuple[str, ...] = ()) -> tuple[float, float, float, float] | None:
        if cid in geo:
            return geo[cid]
        cell = cells.get(cid)
        if cell is None or cell.get("vertex") != "1":
            return None
        g = cell.find("mxGeometry")
        if g is None:
            return None
        x, y = float(g.get("x", 0)), float(g.get("y", 0))
        w, h = float(g.get("width", 0)), float(g.get("height", 0))
        parent = cell.get("parent")
        if parent and parent not in ("0", "1") and parent not in seen:
            pg = resolve(parent, seen + (cid,))
            if pg:
                x, y = x + pg[0], y + pg[1]
        geo[cid] = (x, y, w, h)
        return geo[cid]

    for cid in cells:
        resolve(cid)
    return geo


def _is_icon(style: dict[str, str]) -> bool:
    shape = style.get("shape", "")
    if shape == "image":
        return True
    name = _aws4_name(shape)
    return bool(name) and name not in GROUP_SHAPES


def _port(style: dict[str, str], key: str) -> float | None:
    try:
        return float(style[key])
    except (KeyError, ValueError):
        return None


def _blockers(icons, geo, exclude, a, b):
    """Icons (other than `exclude`) whose box intersects the axis-aligned segment a→b."""
    (x1, y1), (x2, y2) = a, b
    out = []
    for o in icons - exclude:
        ox, oy, ow, oh = geo[o]
        if abs(x1 - x2) <= ALIGN_TOLERANCE:                       # vertical segment at x1
            lo, hi = min(y1, y2), max(y1, y2)
            if ox <= x1 <= ox + ow and oy < hi and oy + oh > lo:
                out.append(o)
        else:                                                    # horizontal segment at y1
            lo, hi = min(x1, x2), max(x1, x2)
            if oy <= y1 <= oy + oh and ox < hi and ox + ow > lo:
                out.append(o)
    return out


def _edge_path(style, sg, tg):
    """Return the polyline draw.io will draw for a straight or single-bend (L) edge; None if the
    endpoints need two bends. Straight: aligned
    centers. L: exit side and entry side on different axes, corner in the direction each port faces."""
    sx, sy, sw, sh = sg
    tx, ty, tw, th = tg
    scx, scy, tcx, tcy = sx + sw / 2, sy + sh / 2, tx + tw / 2, ty + th / 2
    ex, ey, nx, ny = (_port(style, k) for k in ("exitX", "exitY", "entryX", "entryY"))
    has_ports = None not in (ex, ey, nx, ny)
    # exitY/entryY above 1 mean "under the node label" (builder ports); the segment starts there
    if abs(scx - tcx) <= ALIGN_TOLERANCE:
        if has_ports:
            return [(scx, sy + ey * sh), (scx, ty + ny * th)]
        return [(scx, sy + sh if ty > sy else sy), (scx, ty if ty > sy else ty + th)]
    if abs(scy - tcy) <= ALIGN_TOLERANCE:
        return [(sx + sw if tx > sx else sx, scy), (tx if tx > sx else tx + tw, scy)]
    if not has_ports:
        return None
    p = (sx + ex * sw, sy + ey * sh)
    q = (tx + nx * tw, ty + ny * th)
    # a port anywhere along the top/bottom edge leaves vertically, anywhere along the left/right edge horizontally
    # (the builder fans bent edges out along the side, so the ratio is rarely exactly 0.5)
    exit_vertical = 0.0 < ex < 1.0 and (ey <= 0.0 or ey >= 1.0)
    exit_horizontal = ex in (0.0, 1.0) and 0.0 < ey < 1.0
    entry_vertical = 0.0 < nx < 1.0 and (ny <= 0.0 or ny >= 1.0)
    entry_horizontal = nx in (0.0, 1.0) and 0.0 < ny < 1.0
    if exit_vertical and entry_horizontal:
        c = (p[0], q[1])
        ok = (c[1] < p[1]) if ey <= 0.0 else (c[1] > p[1])
        ok = ok and ((c[0] < q[0]) if nx == 0.0 else (c[0] > q[0]))
    elif exit_horizontal and entry_vertical:
        c = (q[0], p[1])
        ok = (c[0] > p[0]) if ex == 1.0 else (c[0] < p[0])
        ok = ok and ((c[1] < q[1]) if ny <= 0.0 else (c[1] > q[1]))
    else:
        return None
    return [p, c, q] if ok else None


def _layout_warnings(cells: dict[str, ET.Element]) -> list[str]:
    warnings: list[str] = []
    geo = _abs_geometry(cells)
    icons = {cid for cid, c in cells.items() if cid in geo and _is_icon(parse_style(c.get("style")))}
    paths: dict[str, list] = {}
    for cid, cell in cells.items():
        if cell.get("edge") != "1":
            continue
        s, t = cell.get("source"), cell.get("target")
        if s not in icons or t not in icons:
            continue
        style = parse_style(cell.get("style"))
        path = _edge_path(style, geo[s], geo[t])
        if path is None:
            sx, sy, sw, sh = geo[s]
            tx, ty, tw, th = geo[t]
            dx, dy = abs(sx + sw / 2 - tx - tw / 2), abs(sy + sh / 2 - ty - th / 2)
            warnings.append(f"W4 edge '{cid}': '{s}' and '{t}' share neither a column nor a lane and the ports do not "
                            f"form a single bend — align them (dx={dx:.0f}, dy={dy:.0f}) or use L ports "
                            "(exit top/bottom + enter left/right, or exit left/right + enter top/bottom)")
            continue
        paths[cid] = path
        for a, b in zip(path, path[1:]):
            for o in _blockers(icons, geo, {s, t}, a, b):
                warnings.append(f"W5 edge '{cid}': path from '{s}' to '{t}' passes through icon '{o}' — move it off the corridor")
    warnings.extend(_overlap_warnings(paths))
    touched = set()
    for cid, cell in cells.items():
        if cell.get("edge") == "1":
            touched.update((cell.get("source"), cell.get("target")))
    for o in sorted(icons - touched) if touched else []:        # a file with no edges at all is an icon sheet, not a diagram
        warnings.append(f"W9 icon '{o}' has no edge — every component connects to something; add its relationship or "
                        "remove it (a truly standalone service is a Decisions line, not a floating icon)")
    return warnings


def _overlap_warnings(paths: dict[str, list]) -> list[str]:
    """W8: two edges whose paths contain collinear segments that overlap — they render as one line, and the reader
    cannot tell which arrowhead belongs to which source. Bent edges touching the same side of a node must leave
    from different ports (the builder spaces them 20 px apart); a bus with a shared trunk is not accepted."""

    def segments(path):
        for i, (a, b) in enumerate(zip(path, path[1:])):
            if abs(a[0] - b[0]) <= ALIGN_TOLERANCE:
                yield i, ("v", a[0], min(a[1], b[1]), max(a[1], b[1]))
            else:
                yield i, ("h", a[1], min(a[0], b[0]), max(a[0], b[0]))

    warnings: list[str] = []
    ids = sorted(paths)
    for i, e1 in enumerate(ids):
        for e2 in ids[i + 1:]:
            hit = False
            for _, (k1, c1, lo1, hi1) in segments(paths[e1]):
                for _, (k2, c2, lo2, hi2) in segments(paths[e2]):
                    if k1 == k2 and abs(c1 - c2) <= ALIGN_TOLERANCE and min(hi1, hi2) - max(lo1, lo2) > ALIGN_TOLERANCE:
                        hit = True
                        break
                if hit:
                    break
            if hit:
                warnings.append(f"W8 edges '{e1}' and '{e2}' run on top of each other — give them different ports on the side "
                                "(bent edges 20 px apart, as the builder does), different sides of the node, or different lanes")
    return warnings


LABEL_CHAR_PX = 6.2      # ~11 px Amazon Ember / Helvetica average glyph advance
LABEL_PAD_PX = 8
EDGE_LINE_H = 14         # px per line of an 11 pt edge label (the builder wraps long text with <br>)
NODE_LINE_H, NODE_LABEL_PAD = 18, 4   # node labels: 13 pt bold under the icon (build_diagram LABEL_LINE_H / LABEL_TOP_PAD)
TITLE_BAND = 28          # px: a container's title row (13 pt bold + spacingTop) — an edge label there reads as part of the title


def _point_along(path, rel):
    """(x, y) at relative position rel (-1 source … 1 target) along a polyline, by length."""
    lens = [abs(b[0] - a[0]) + abs(b[1] - a[1]) for a, b in zip(path, path[1:])]
    total = sum(lens)
    target = total * (0.5 + rel / 2)
    for (a, b), ln in zip(zip(path, path[1:]), lens):
        if target <= ln or (a, b) == (path[-2], path[-1]):
            f = min(max(target / ln, 0.0), 1.0) if ln else 0.0
            return a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
        target -= ln
    return path[-1]


def _label_lines(value: str) -> list[str]:
    """Visible lines of an html label: split on <br>, tags stripped."""
    parts = re.split(r"<br\s*/?>", value or "", flags=re.I)
    lines = [re.sub(r"<[^>]+>", "", p).strip() for p in parts]
    return [l for l in lines if l] or [""]


def _label_box(path, rel, lines, style):
    """Box of an edge's text label: centred on the polyline at relative position `rel` (by length), then moved by
    its alignment the way draw.io does — `verticalAlign=bottom` puts it above the point, `top` below;
    `align=right` (+ spacingRight) puts it left of the point, `left` (+ spacingLeft) right of it."""
    half_w = LABEL_CHAR_PX * max(len(l) for l in lines) / 2 + LABEL_PAD_PX
    half_h = (EDGE_LINE_H * len(lines) + 2) / 2
    cx, cy = _point_along(path, rel)
    va, al = style.get("verticalAlign"), style.get("align")
    if va == "bottom":
        cy -= half_h
    elif va == "top":
        cy += half_h
    if al == "right":
        cx -= half_w + float(style.get("spacingRight", 0) or 0)
    elif al == "left":
        cx += half_w + float(style.get("spacingLeft", 0) or 0)
    return (cx - half_w, cy - half_h, cx + half_w, cy + half_h)


def _overlaps(a, b) -> bool:
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


def _segment_through(box, path) -> bool:
    """Does any leg of `path` run through the box (touching its edge does not count)?"""
    for (x1, y1), (x2, y2) in zip(path, path[1:]):
        if abs(y1 - y2) <= ALIGN_TOLERANCE:
            if box[1] < y1 < box[3] and min(x1, x2) < box[2] and max(x1, x2) > box[0]:
                return True
        elif box[0] < x1 < box[2] and min(y1, y2) < box[3] and max(y1, y2) > box[1]:
            return True
    return False


def _hits_container(box, gx, gy, gw, gh, titled):
    """'border' / 'title' / None for a box against one container rectangle."""
    hit_v = any(box[0] <= bx <= box[2] for bx in (gx, gx + gw)) and box[1] < gy + gh and box[3] > gy
    hit_h = any(box[1] <= by <= box[3] for by in (gy, gy + gh)) and box[0] < gx + gw and box[2] > gx
    if hit_v or hit_h:
        return "border"
    if titled and box[0] < gx + gw and box[2] > gx and box[1] < gy + TITLE_BAND and box[3] > gy:
        return "title"
    return None


def _label_warnings(cells: dict[str, ET.Element]) -> list[str]:
    """W7: an edge label whose box covers a container border or title row, an icon (or the node label under it),
    another edge's label, or another edge's line. The label sits on the polyline at the relative mxGeometry x
    (-1 source … 1 target, by length — so a bent edge's label can sit on either leg), moved off the line by its
    alignment (verticalAlign=bottom/top → above/below, align=right/left → left/right, as the builder writes it);
    without alignment flags it is centred on the line. Multi-line labels (<br>) are measured by their longest
    line and their line count."""
    geo = _abs_geometry(cells)
    containers = [cid for cid, c in cells.items()
                  if cid in geo and parse_style(c.get("style")).get("container") == "1"]
    icons = {cid for cid, c in cells.items() if cid in geo and _is_icon(parse_style(c.get("style")))}
    warnings: list[str] = []
    paths: dict[str, list] = {}
    labels: dict[str, tuple] = {}

    def container_hit(box):
        for k in containers:
            gx, gy, gw, gh = geo[k]
            kind = _hits_container(box, gx, gy, gw, gh, bool((cells[k].get("value") or "").strip()))
            if kind:
                return kind, k
        return None, None

    for cid, cell in cells.items():
        if cell.get("edge") != "1":
            continue
        s, t = cell.get("source"), cell.get("target")
        if s not in icons or t not in icons:
            continue
        style = parse_style(cell.get("style"))
        path = _edge_path(style, geo[s], geo[t])
        if not isinstance(path, list):
            continue
        paths[cid] = path
        lines = _label_lines(cell.get("value") or "")
        if lines == [""]:
            continue
        g = cell.find("mxGeometry")
        rel = float(g.get("x", 0) or 0) if g is not None else 0.0
        labels[cid] = (_label_box(path, rel, lines, style), " / ".join(lines))

    icon_boxes = {}
    for o in icons:
        ox, oy, ow, oh = geo[o]
        n_lines = len(_label_lines(cells[o].get("value") or ""))
        icon_boxes[o] = (ox, oy, ox + ow, oy + oh + NODE_LABEL_PAD + NODE_LINE_H * n_lines)   # icon + its label

    for cid, (box, text) in labels.items():
        kind, k = container_hit(box)
        if kind == "border":
            warnings.append(f"W7 edge '{cid}': label '{text}' lands on the border of '{k}' — shift it along the edge "
                            "(mxGeometry x, −1 source … 1 target) into free space, or move a node so the edge has room")
            continue
        if kind == "title":
            warnings.append(f"W7 edge '{cid}': label '{text}' lands on the title of '{k}' — shift it along the edge "
                            "below the title row (mxGeometry x toward the target)")
            continue
        hit_icon = next((o for o, ob in icon_boxes.items() if _overlaps(box, ob)), None)
        if hit_icon:
            warnings.append(f"W7 edge '{cid}': label '{text}' covers icon '{hit_icon}' (or its name) — move it along the edge "
                            "(mxGeometry x) or onto the other side of the line")
            continue
        other = next((o for o, (ob, _) in labels.items() if o != cid and o < cid and _overlaps(box, ob)), None)
        if other:
            warnings.append(f"W7 edges '{other}' and '{cid}': their labels overlap — move one along its edge (mxGeometry x)")
            continue
        crossed = next((o for o, p in paths.items() if o != cid and _segment_through(box, p)), None)
        if crossed:
            warnings.append(f"W7 edge '{cid}': label '{text}' sits on the line of edge '{crossed}' — move it along the edge "
                            "(mxGeometry x) or onto the other side of the line")
    return warnings

def _grouping_warnings(cells: dict[str, ET.Element]) -> list[str]:
    """W6: an icon drawn inside an AWS Cloud badge group but parented to the canvas or to the cloud itself.
    Role groups (any non-badge container) are where icons belong; users/on-prem outside the cloud never warn."""
    geo = _abs_geometry(cells)
    clouds = []
    for cid, cell in cells.items():
        style = parse_style(cell.get("style"))
        if (_aws4_name(style.get("grIcon", "")) or "").startswith("group_aws_cloud") and cid in geo:
            clouds.append(cid)
    if not clouds:
        return []

    def inside(inner, outer) -> bool:
        ix, iy, iw, ih = geo[inner]
        ox, oy, ow, oh = geo[outer]
        return ix >= ox and iy >= oy and ix + iw <= ox + ow and iy + ih <= oy + oh

    warnings: list[str] = []
    for cid, cell in cells.items():
        if cid not in geo or not _is_icon(parse_style(cell.get("style"))):
            continue
        parent = cell.get("parent", "1")
        if parent != "1" and parent not in clouds:
            continue
        for cloud in clouds:
            if cid != cloud and inside(cid, cloud):
                warnings.append(f"W6 cell '{cid}': sits inside AWS Cloud '{cloud}' but is not a child of a role group — "
                                "make it a child of a group (layout-and-style.md §2)")
                break
    return warnings


def validate_text(xml_text: str, index: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    known = index["names"] | index["js_shapes"]

    if "<!--" in xml_text:
        errors.append("E6 XML comment found — remove all <!-- --> blocks")
    if re.search(r"<!(DOCTYPE|ENTITY)", xml_text, re.I):
        # draw.io never writes these; refusing them keeps stdlib ElementTree safe from XXE/billion-laughs.
        errors.append("E6 DOCTYPE/ENTITY declaration found — not a draw.io file")
        return errors, warnings
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        return [f"E6 XML parse error: {exc}"], warnings

    for diagram in root.iter("diagram"):
        if diagram.find("mxGraphModel") is None and (diagram.text or "").strip():
            errors.append(f"E6 diagram '{diagram.get('name', diagram.get('id'))}' is compressed — "
                          "write plain <mxGraphModel> XML")
    if errors:
        return errors, warnings

    cells: dict[str, ET.Element] = {}
    for cell in root.iter("mxCell"):
        cid = cell.get("id")
        if cid is None:
            continue
        if cid in cells:
            errors.append(f"E5 duplicate cell id '{cid}'")
        cells[cid] = cell

    for cid, cell in cells.items():
        style = parse_style(cell.get("style"))
        shape = _aws4_name(style.get("shape", ""))
        if shape is None:
            continue
        res = _aws4_name(style.get("resIcon", "")) or _aws4_name(style.get("prIcon", ""))
        gr = _aws4_name(style.get("grIcon", ""))
        stroke = style.get("strokeColor", "")
        for name in (shape, res, gr):
            if name and name not in known:
                errors.append(f"E1 cell '{cid}': unknown stencil 'mxgraph.aws4.{name}' — look it up in references/")
        if shape in SERVICE_FRAMES:
            if stroke.lower() != "#ffffff":
                errors.append(f"E2 cell '{cid}': service-level icon needs strokeColor=#ffffff (has '{stroke or 'unset'}')")
            if not style.get("fillColor"):
                warnings.append(f"W2 cell '{cid}': icon has no fillColor — renders white in PNG export")
        elif shape in GROUP_SHAPES:
            if style.get("container") != "1":
                errors.append(f"E4 cell '{cid}': group needs container=1")
            if style.get("dropTarget") != "1":
                warnings.append(f"W3 cell '{cid}': group should set dropTarget=1")
        else:
            if stroke.lower() != "none":
                errors.append(f"E2 cell '{cid}': resource-level stencil needs strokeColor=none (has '{stroke or 'unset'}')")
            if not style.get("fillColor"):
                warnings.append(f"W2 cell '{cid}': icon has no fillColor — renders white in PNG export")

    for cid, cell in cells.items():
        if cell.get("edge") != "1":
            continue
        for end in ("source", "target"):
            ref = cell.get(end)
            if not ref:
                errors.append(f"E3 edge '{cid}': missing {end}")
            elif ref not in cells:
                errors.append(f"E3 edge '{cid}': {end}='{ref}' does not exist")
        style = parse_style(cell.get("style"))
        if style.get("edgeStyle") == "orthogonalEdgeStyle" and "exitX" not in style and "entryX" not in style:
            warnings.append(f"W1 edge '{cid}': no exitX/entryX — set explicit ports so routing stays clean")

    warnings.extend(_layout_warnings(cells))
    warnings.extend(_grouping_warnings(cells))
    warnings.extend(_label_warnings(cells))
    return errors, warnings


def validate_file(path: Path, index: dict) -> tuple[list[str], list[str]]:
    return validate_text(path.read_text(encoding="utf-8"), index)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print(__doc__)
        return 2
    index = load_index()
    total_e = total_w = 0
    codes: dict[str, int] = {}
    for f in map(Path, args):
        errors, warnings = validate_file(f, index)
        total_e += len(errors)
        total_w += len(warnings)
        print(f"== {f}")
        for e in errors:
            print(f"  ERROR {e}")
        for w in warnings:
            print(f"  warn  {w}")
            codes[w[:2]] = codes.get(w[:2], 0) + 1
        if not errors and not warnings:
            print("  ok")
    print(f"Summary: {total_e} errors, {total_w} warnings in {len(args)} file(s)")
    defects = {c: n for c, n in codes.items() if c in LAYOUT_DEFECTS}
    if defects:
        print("Layout defects (must be fixed, not style hints): " + ", ".join(f"{c}×{n}" for c, n in sorted(defects.items())))
    return 1 if total_e or defects else 0


if __name__ == "__main__":
    sys.exit(main())
