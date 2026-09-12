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
  W4  edge whose endpoints share neither a column nor a lane (needs a bend — realign the nodes)
  W5  straight edge whose corridor passes through an unconnected icon's bounding box

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


ALIGN_TOLERANCE = 4.0  # px; icons on the same column/lane within this are "aligned"


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


def _layout_warnings(cells: dict[str, ET.Element]) -> list[str]:
    warnings: list[str] = []
    geo = _abs_geometry(cells)
    icons = {cid for cid, c in cells.items() if cid in geo and _is_icon(parse_style(c.get("style")))}
    for cid, cell in cells.items():
        if cell.get("edge") != "1":
            continue
        s, t = cell.get("source"), cell.get("target")
        if s not in icons or t not in icons:
            continue
        sx, sy, sw, sh = geo[s]
        tx, ty, tw, th = geo[t]
        scx, scy, tcx, tcy = sx + sw / 2, sy + sh / 2, tx + tw / 2, ty + th / 2
        if abs(scx - tcx) <= ALIGN_TOLERANCE:          # vertical corridor
            y1, y2 = min(sy + sh, ty + th), max(sy, ty)
            blockers = [o for o in icons - {s, t}
                        if geo[o][0] <= scx <= geo[o][0] + geo[o][2] and geo[o][1] < y2 and geo[o][1] + geo[o][3] > y1]
        elif abs(scy - tcy) <= ALIGN_TOLERANCE:        # horizontal corridor
            x1, x2 = min(sx + sw, tx + tw), max(sx, tx)
            blockers = [o for o in icons - {s, t}
                        if geo[o][1] <= scy <= geo[o][1] + geo[o][3] and geo[o][0] < x2 and geo[o][0] + geo[o][2] > x1]
        else:
            warnings.append(f"W4 edge '{cid}': '{s}' and '{t}' share neither a column nor a lane — "
                            f"align them (dx={abs(scx - tcx):.0f}, dy={abs(scy - tcy):.0f}) so the edge is one straight segment")
            continue
        for o in blockers:
            warnings.append(f"W5 edge '{cid}': straight path from '{s}' to '{t}' passes through icon '{o}' — move it off the corridor")
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
