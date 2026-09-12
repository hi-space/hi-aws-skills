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
