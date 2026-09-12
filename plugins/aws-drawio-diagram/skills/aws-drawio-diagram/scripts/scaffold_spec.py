#!/usr/bin/env python3
"""Turn a brief into a logical spec for build_diagram.py (no coordinates — layout.py assigns them).

Reads `## Components` (id, "Service (`stencil`)" or "(image `file.svg`)", Group) and `## Relationships`
(`from → to`, Kind, Label) from `<name>.brief.md` and writes `<name>.json` with nodes, edges and groups. Rows
marked "not drawn" are skipped. Edges whose Kind contains `async`, `aux` or `dashed` are dashed; labels come
from the Label column unless it is "—". Unknown stencil names are reported and left for you to fix (the builder
refuses them anyway).

    python3 scaffold_spec.py <name>.brief.md <name>.json
    python3 build_diagram.py <name>.json <name>.drawio          # places nodes automatically, checks the brief
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_diagram import _table_rows, EXTRA_ICONS  # noqa: E402


def scaffold(brief_text: str, index: set[str]) -> tuple[dict, list[str]]:
    warnings: list[str] = []
    title = next((l[2:].strip() for l in brief_text.splitlines() if l.startswith("# ")), "Architecture")
    comp_rows = _table_rows(brief_text, "Components")
    rel_rows = _table_rows(brief_text, "Relationships")
    nodes, groups, order = [], {}, []
    for row in comp_rows:
        if len(row) < 4 or re.search(r"not drawn", " ".join(row), re.I):
            continue
        cid = row[0].strip("`* ")
        service, group = row[1], row[3].strip()
        node = {"id": cid, "label": re.sub(r"\s*\(.*$", "", service).strip() or cid}
        m_img = re.search(r"image\s+`([^`]+\.svg)`", service)
        m_icon = re.search(r"`([a-z0-9_]+)`", service)
        if m_img:
            node["image"] = m_img.group(1)
            if not (EXTRA_ICONS / m_img.group(1)).is_file():
                warnings.append(f"{cid}: image '{m_img.group(1)}' not in assets/extra-icons/")
        elif m_icon:
            node["icon"] = m_icon.group(1)
            if m_icon.group(1) not in index:
                warnings.append(f"{cid}: unknown stencil '{m_icon.group(1)}' — look it up in references/aws-icons-*.md")
        else:
            warnings.append(f"{cid}: no stencil in the Service cell — write `name` or image `file.svg`")
        qual = re.search(r"\)\s*[—–-]\s*(.+)$", service)
        if qual and len(node["label"]) + len(qual.group(1)) <= 30:
            node["label"] = f"{node['label']} ({qual.group(1).strip()})"
        if group.lower() == "outside":
            node["outside"] = True
        else:
            gid = "g_" + re.sub(r"[^a-z0-9]+", "_", group.lower()).strip("_")
            node["group"] = gid
            if gid not in groups:
                groups[gid] = {"id": gid, "label": group}
                order.append(gid)
        nodes.append(node)
    seen_labels = defaultdict(list)
    for n in nodes:
        seen_labels[n["label"]].append(n)
    for label, same in seen_labels.items():
        if len(same) > 1:                               # two "ECS Fargate service" nodes: tell them apart by id
            for n in same:
                n["label"] = f"{label} ({n['id'].replace('_', ' ')})" if len(label) + len(n["id"]) <= 28 else n["id"]
    ids = {n["id"] for n in nodes}
    header = None
    m = re.search(r"^##\s+Relationships\b.*?$", brief_text, re.M)
    if m:
        for line in brief_text[m.end():].splitlines():
            if line.lstrip().startswith("|"):
                header = [c.strip().lower() for c in line.strip().strip("|").split("|")]
                break
    k_i = next((i for i, c in enumerate(header or []) if c.startswith("kind")), None)
    l_i = next((i for i, c in enumerate(header or []) if c.startswith("label")), None)
    edges = []
    for row in rel_rows:
        pair = None
        for cell in row:
            mm = re.search(r"([A-Za-z0-9_\-]+)\s*(?:→|->)\s*([A-Za-z0-9_\-]+)", cell)
            if mm:
                pair = mm.groups()
                break
        if not pair:
            continue
        if pair[0] not in ids or pair[1] not in ids:
            warnings.append(f"relationship {pair[0]} → {pair[1]} names a component that is not drawn — skipped")
            continue
        kind = row[k_i] if k_i is not None and k_i < len(row) else ""
        edge = {"from": pair[0], "to": pair[1]}
        if re.search(r"aux|async|dashed", kind, re.I):
            edge["dashed"] = True
        label = row[l_i].strip() if l_i is not None and l_i < len(row) else ""
        if label and label not in ("—", "-", "–") and len(label) <= 12 and not re.search(r"[(), ]", label):
            edge["label"] = label                       # short, one word: anything longer lands on a border
        edges.append(edge)
    spec = {"title": title, "layout": "auto", "groups": [groups[g] for g in order], "nodes": nodes, "edges": edges}
    return spec, warnings


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        print(__doc__)
        return 2
    index = set(json.loads((HERE / "stencil-index.json").read_text())["stencils"])
    spec, warnings = scaffold(Path(args[0]).read_text(encoding="utf-8"), index)
    Path(args[1]).write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {args[1]}: {len(spec['nodes'])} nodes, {len(spec['edges'])} edges, {len(spec['groups'])} groups")
    for w in warnings:
        print(f"  warn: {w}")
    return 1 if any("unknown stencil" in w or "no stencil" in w for w in warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
