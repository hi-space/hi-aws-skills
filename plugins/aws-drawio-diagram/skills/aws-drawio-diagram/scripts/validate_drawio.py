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
  W4  edge that needs two bends, or a single bend to a non-adjacent cell
  W5  straight or single-bend edge whose path passes through an unconnected icon's bounding box
  W6  icon drawn inside an AWS Cloud group but not a child of a role group
  W7  edge label whose box covers a group/cloud border (drop it or shift it with mxGeometry x)
  W8  two edges with overlapping collinear segments (one edge per node side)

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
MAX_BEND_DX, MAX_BEND_DY = 260.0, 240.0   # one bend reaches the adjacent column / lane only (240 / 170+50 grid)  # px; icons on the same column/lane within this are "aligned"


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
    endpoints need two bends; "far" if a bend would reach beyond the adjacent cell. Straight: aligned
    centers. L: exit side and entry side on different axes, corner in the direction each port faces."""
    sx, sy, sw, sh = sg
    tx, ty, tw, th = tg
    scx, scy, tcx, tcy = sx + sw / 2, sy + sh / 2, tx + tw / 2, ty + th / 2
    if abs(scx - tcx) <= ALIGN_TOLERANCE:
        return [(scx, sy + sh if ty > sy else sy), (scx, ty if ty > sy else ty + th)]
    if abs(scy - tcy) <= ALIGN_TOLERANCE:
        return [(sx + sw if tx > sx else sx, scy), (tx if tx > sx else tx + tw, scy)]
    ex, ey, nx, ny = (_port(style, k) for k in ("exitX", "exitY", "entryX", "entryY"))
    if None in (ex, ey, nx, ny):
        return None
    p = (sx + ex * sw, sy + ey * sh)
    q = (tx + nx * tw, ty + ny * th)
    exit_vertical = abs(ex - 0.5) < 0.01 and ey in (0.0, 1.0)
    exit_horizontal = abs(ey - 0.5) < 0.01 and ex in (0.0, 1.0)
    entry_vertical = abs(nx - 0.5) < 0.01 and ny in (0.0, 1.0)
    entry_horizontal = abs(ny - 0.5) < 0.01 and nx in (0.0, 1.0)
    if abs(scx - tcx) > MAX_BEND_DX or abs(scy - tcy) > MAX_BEND_DY:
        return "far"
    if exit_vertical and entry_horizontal:
        c = (p[0], q[1])
        ok = (c[1] < p[1]) if ey == 0.0 else (c[1] > p[1])
        ok = ok and ((c[0] < q[0]) if nx == 0.0 else (c[0] > q[0]))
    elif exit_horizontal and entry_vertical:
        c = (q[0], p[1])
        ok = (c[0] > p[0]) if ex == 1.0 else (c[0] < p[0])
        ok = ok and ((c[1] < q[1]) if ny == 0.0 else (c[1] > q[1]))
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
        if path is None or path == "far":
            sx, sy, sw, sh = geo[s]
            tx, ty, tw, th = geo[t]
            dx, dy = abs(sx + sw / 2 - tx - tw / 2), abs(sy + sh / 2 - ty - th / 2)
            if path == "far":
                warnings.append(f"W4 edge '{cid}': '{s}' → '{t}' is not aligned and the target is not in an adjacent cell "
                                f"(dx={dx:.0f}, dy={dy:.0f}) — a single bend only reaches the next column and lane; "
                                "move the target, or route through an intermediate node")
            else:
                warnings.append(f"W4 edge '{cid}': '{s}' and '{t}' share neither a column nor a lane and the ports do not "
                                f"form a single bend — align them (dx={dx:.0f}, dy={dy:.0f}) or use the fan-out ports "
                                "(exit top/bottom, enter left/right)")
            continue
        paths[cid] = path
        for a, b in zip(path, path[1:]):
            for o in _blockers(icons, geo, {s, t}, a, b):
                warnings.append(f"W5 edge '{cid}': path from '{s}' to '{t}' passes through icon '{o}' — move it off the corridor")
    warnings.extend(_overlap_warnings(paths))
    return warnings


def _overlap_warnings(paths: dict[str, list]) -> list[str]:
    """W8: two edges whose paths contain collinear segments that overlap (they render as one line)."""
    def segments(path):
        for a, b in zip(path, path[1:]):
            if abs(a[0] - b[0]) <= ALIGN_TOLERANCE:
                yield ("v", a[0], min(a[1], b[1]), max(a[1], b[1]))
            else:
                yield ("h", a[1], min(a[0], b[0]), max(a[0], b[0]))

    warnings: list[str] = []
    ids = sorted(paths)
    for i, e1 in enumerate(ids):
        for e2 in ids[i + 1:]:
            for k1, c1, lo1, hi1 in segments(paths[e1]):
                hit = False
                for k2, c2, lo2, hi2 in segments(paths[e2]):
                    if k1 == k2 and abs(c1 - c2) <= ALIGN_TOLERANCE and min(hi1, hi2) - max(lo1, lo2) > ALIGN_TOLERANCE:
                        hit = True
                        break
                if hit:
                    warnings.append(f"W8 edges '{e1}' and '{e2}' run on top of each other — give them different sides of the "
                                    "node or different lanes (one edge per node side)")
                    break
    return warnings


LABEL_CHAR_PX = 6.2      # ~11 px Amazon Ember / Helvetica average glyph advance
LABEL_PAD_PX = 8
LABEL_HALF_H = 8


def _label_warnings(cells: dict[str, ET.Element]) -> list[str]:
    """W7: an edge label whose box covers a container border (group or cloud). Straight edges: the label
    sits at the segment midpoint, shifted by the relative mxGeometry x (-1 source … 1 target); horizontal
    labels are drawn above the line, vertical labels to its left (align=right). Bent edges: at half length."""
    geo = _abs_geometry(cells)
    containers = [cid for cid, c in cells.items()
                  if cid in geo and parse_style(c.get("style")).get("container") == "1"]
    if not containers:
        return []
    icons = {cid for cid, c in cells.items() if cid in geo and _is_icon(parse_style(c.get("style")))}
    warnings: list[str] = []
    for cid, cell in cells.items():
        text = re.sub(r"<[^>]+>", "", cell.get("value") or "").strip()
        if cell.get("edge") != "1" or not text:
            continue
        s, t = cell.get("source"), cell.get("target")
        if s not in icons or t not in icons:
            continue
        style = parse_style(cell.get("style"))
        path = _edge_path(style, geo[s], geo[t])
        if not isinstance(path, list):
            continue
        g = cell.find("mxGeometry")
        rel = float(g.get("x", 0) or 0) if g is not None else 0.0
        half_w = LABEL_CHAR_PX * len(text) / 2 + LABEL_PAD_PX
        if len(path) == 2:
            (x1, y1), (x2, y2) = path
            if abs(y1 - y2) <= ALIGN_TOLERANCE:                     # horizontal edge
                cx = (x1 + x2) / 2 + rel * (x2 - x1) / 2
                cy = y1 - LABEL_HALF_H
            else:                                                   # vertical edge, label left of line
                cx = x1 - half_w - 4
                cy = (y1 + y2) / 2 + rel * (y2 - y1) / 2
        else:                                                       # bent edge: label centred at half length
            lens = [abs(b[0] - a[0]) + abs(b[1] - a[1]) for a, b in zip(path, path[1:])]
            target = sum(lens) * (0.5 + rel / 2)
            cx, cy = path[0]
            for (a, b), ln in zip(zip(path, path[1:]), lens):
                if target <= ln or (a, b) == (path[-2], path[-1]):
                    f = min(max(target / ln, 0.0), 1.0) if ln else 0.0
                    cx, cy = a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
                    break
                target -= ln
        box = (cx - half_w, cy - LABEL_HALF_H, cx + half_w, cy + LABEL_HALF_H)
        for k in containers:
            gx, gy, gw, gh = geo[k]
            hit_v = any(box[0] <= bx <= box[2] for bx in (gx, gx + gw)) and box[1] < gy + gh and box[3] > gy
            hit_h = any(box[1] <= by <= box[3] for by in (gy, gy + gh)) and box[0] < gx + gw and box[2] > gx
            if hit_v or hit_h:
                warnings.append(f"W7 edge '{cid}': label '{text}' lands on the border of '{k}' — drop the label or "
                                "shift it along the edge (mxGeometry x=-0.4 toward the source) into free space")
                break
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
    for f in map(Path, args):
        errors, warnings = validate_file(f, index)
        total_e += len(errors)
        total_w += len(warnings)
        print(f"== {f}")
        for e in errors:
            print(f"  ERROR {e}")
        for w in warnings:
            print(f"  warn  {w}")
        if not errors and not warnings:
            print("  ok")
    print(f"Summary: {total_e} errors, {total_w} warnings in {len(args)} file(s)")
    return 1 if total_e else 0


if __name__ == "__main__":
    sys.exit(main())
