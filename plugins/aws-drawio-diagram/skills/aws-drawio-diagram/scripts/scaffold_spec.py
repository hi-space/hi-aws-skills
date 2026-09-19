#!/usr/bin/env python3
"""Turn a brief into a logical spec for build_diagram.py (no coordinates — layout.py assigns them).

Reads `## Components` (id, "Service (`stencil`)" or "(image `file.svg`)", Group) and `## Relationships`
(`from → to`, What flows, Kind) from `<name>.brief.md` and writes `<name>.json` with nodes, edges and groups. Rows
marked "not drawn" are skipped. Edges whose Kind contains `async`, `aux` or `dashed` are dashed. **The edge text is
the What flows phrase** — every phrase is passed through (unless it is "—"), and build_diagram.py draws it on the
edge, wrapped into at most 3 lines of 24 characters, on the leg with room; a phrase that cannot fit even there (a
word longer than 24 characters, or more than 3 lines) is refused here for a primary relationship, before layout
luck decides. A leftover "Label on diagram" column (briefs from 1.4) is ignored with a warning. Unknown stencil
names are reported and left for you to fix (the builder refuses them anyway). When the brief has a
`Repo: /abs/path` line, every path in the Evidence column is checked to exist there — a missing path is an error
(exit 1): evidence must be a file the Architect opened.

    python3 scaffold_spec.py <name>.brief.md <name>.json
    python3 build_diagram.py <name>.json <name>.drawio          # places nodes automatically, checks the brief
"""
from __future__ import annotations

import json
import hashlib
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_diagram import (_table_rows, EXTRA_ICONS, LABEL_MAX_LINE_CHARS, LABEL_MAX_LINES,  # noqa: E402
                           contract_check, contract_path_for, label_lines)

NO_LABEL = ("", "—", "-", "–")


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
            slug = re.sub(r"[^a-z0-9]+", "_", group.lower()).strip("_")
            if not slug:                                 # non-ASCII group names (e.g. Korean) must not collapse into one id
                slug = "k" + hashlib.md5(group.encode("utf-8")).hexdigest()[:6]
            gid = "g_" + slug
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
    w_i = next((i for i, c in enumerate(header or []) if c.startswith("what")), None)
    if header is not None and any(c.startswith("label") for c in header):
        warnings.append("the Relationships table has a 'Label' column — it is ignored: the edge shows the What flows phrase "
                        "(architecture-brief.md § Edge text). Delete the column")
    if header is not None and w_i is None:
        warnings.append("the Relationships table has no 'What flows' column — the edges will carry no text")
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
        if re.search(r"not drawn", kind, re.I):
            continue                                    # the brief says so; brief_check treats the row as optional
        edge = {"from": pair[0], "to": pair[1]}
        if row and row[0].strip().isdigit():
            edge["num"] = int(row[0].strip())            # the brief's # — the step number in the guide
        if re.search(r"aux|async|dashed", kind, re.I):
            edge["dashed"] = True
        text = " ".join(row[w_i].replace("`", "").split()) if w_i is not None and w_i < len(row) else ""
        if text not in NO_LABEL:
            edge["label"] = text                        # drawn on the edge by build_diagram.py (wrapped, on the leg with room)
            if not edge.get("dashed") and label_lines(text, LABEL_MAX_LINE_CHARS) is None:
                # no edge anywhere can hold it: say so here, before layout luck decides where the edge lands
                warnings.append(f"What flows '{text}' ({len(text)} characters) on primary relationship {pair[0]} → {pair[1]} "
                                f"can never fit an edge (at most {LABEL_MAX_LINES} lines of {LABEL_MAX_LINE_CHARS} characters, "
                                "no word longer than a line) — condense the phrase in the brief or write —")
        edges.append(edge)
    warnings += check_evidence(brief_text, comp_rows)
    spec = {"title": title, "layout": "auto", "groups": [groups[g] for g in order], "nodes": nodes, "edges": edges}
    return spec, warnings


def check_evidence(brief_text: str, comp_rows: list[list[str]]) -> list[str]:
    """When the brief names its repository (`Repo: /abs/path` under the title), every path in the Evidence column
    must exist there. Invented evidence is the failure this guards against; a missing path is reported per row."""
    m = re.search(r"^Repo:\s*(\S+)", brief_text, re.M)
    if not m:
        return []
    root = Path(m.group(1)).expanduser()
    if not root.is_dir():
        return [f"Repo: {root} is not a directory — fix the line under the title"]
    header = None
    hm = re.search(r"^##\s+Components\b.*?$", brief_text, re.M)
    if hm:
        for line in brief_text[hm.end():].splitlines():
            if line.lstrip().startswith("|"):
                header = [c.strip().lower() for c in line.strip().strip("|").split("|")]
                break
    ev_i = next((i for i, c in enumerate(header or []) if c.startswith("evidence")), None)
    if ev_i is None:
        return ["brief has a Repo: line but no Evidence column in Components"]
    out = []
    for row in comp_rows:
        if ev_i >= len(row):
            continue
        cell = row[ev_i]
        for path in re.findall(r"(?<![\w/.-])((?:[\w.-]+/)+[\w.-]+\.[A-Za-z0-9]+)", cell):
            if not (root / path).exists():
                out.append(f"{row[0].strip('`* ')}: evidence path '{path}' does not exist under {root} — cite a file you opened")
    return out


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        print(__doc__)
        return 2
    index = set(json.loads((HERE / "stencil-index.json").read_text())["stencils"])
    brief_path = Path(args[0])
    brief_text = brief_path.read_text(encoding="utf-8")
    # the first run freezes ids and From → To pairs; a later run with changed ones stops here
    c_errors, c_notes = contract_check(brief_text, contract_path_for(brief_path))
    for n in c_notes:
        print(f"  {n}")
    for err in c_errors:
        print(f"ERROR contract: {err}")
    if c_errors:
        return 1
    spec, warnings = scaffold(brief_text, index)
    Path(args[1]).write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {args[1]}: {len(spec['nodes'])} nodes, {len(spec['edges'])} edges, {len(spec['groups'])} groups")
    for w in warnings:
        print(f"  warn: {w}")
    return 1 if any(k in w for w in warnings for k in ("unknown stencil", "no stencil", "does not exist", "Repo:", "can never fit")) else 0


if __name__ == "__main__":
    sys.exit(main())
