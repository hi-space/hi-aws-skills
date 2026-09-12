#!/usr/bin/env python3
"""Build a .drawio file from a small JSON layout spec (grid cells, groups, edges).

The spec names *where* things go on the grid; this script does the arithmetic the layout rules in
references/layout-and-style.md demand: icon coordinates, group rectangles, ports for straight and
single-bend edges, node labels (always below the icon; edges that leave or enter the bottom attach below
the label so no line crosses text), the AWS Cloud box, the canvas size, and the font on every cell. It then runs validate_drawio on the result.

Spec (JSON):
{
  "title": "Agentic RAG Chat — Serverless on AWS",
  "subtitle": "team · 2026-09-12 · v1",           # optional
  "font": "Amazon Ember",                          # optional (default); e.g. "Noto Sans"
  "cloud": "AWS Cloud",                            # optional label; false → no cloud box
  "groups": [ {"id": "g_front", "label": "Frontend", "cols": [1], "lanes": [0, 1]} ],
  "nodes": [
    {"id": "users", "label": "Users", "icon": "users", "col": 0, "lane": 1, "outside": true},
    {"id": "cf", "label": "CloudFront", "icon": "cloudfront", "col": 1, "lane": 1, "group": "g_front"},
    {"id": "mem", "label": "AgentCore Memory", "image": "Res_Amazon-Bedrock-AgentCore_Memory_48.svg",
     "col": 3, "lane": 0, "group": "g_agent"},
    {"id": "apigw", "label": "API Gateway", "icon": "api_gateway", "col": 2, "lane": 1, "group": "g_api"}
  ],
  "edges": [ {"from": "users", "to": "cf", "label": "HTTPS"},
             {"from": "apigw", "to": "cognito", "dashed": true} ]
}

Grid: column i center x = 140 + 240·i; lane j center y = 260 + 170·j, plus 50 px for every group row
boundary above lane j (derived from the groups: a lane where one group ends and another begins).
Icons are 78 px. Groups are 200 px per column (40 px gaps), 60 px above the first icon, 46 px below
the last. Edges between cells in the same column/lane are straight; an edge to the diagonally adjacent
cell leaves the source top/bottom and enters the target left/right (one bend — the fan-out pattern);
anything else is a spec error (move a node). Each side of a node carries at most one edge, so a node has
at most four edges and at most two of them bend — plan hubs and shared sinks (CloudWatch) with one
representative edge, or put a queue/topic in between. Only straight edges may carry a label. Node labels
longer than 22 characters break into two lines at the middle space. `icon`
names come from scripts/stencil-index.json; `image` names a file in assets/extra-icons/.

Usage: build_diagram.py SPEC.json OUT.drawio [--no-validate]
"""
from __future__ import annotations

import base64
import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
INDEX = HERE / "stencil-index.json"
EXTRA_ICONS = HERE.parent / "assets" / "extra-icons"

ICON = 78
COL0, COL_PITCH = 140, 240
LANE0, LANE_PITCH, ROW_GAP = 260, 170, 50
GROUP_HALF_W, GROUP_GAP = 100, 40
GROUP_ABOVE, GROUP_BELOW = 60, 46
CLOUD_PAD = 40
LABEL_CHAR_PX, LABEL_PAD_PX, LABEL_HALF_H = 6.2, 8, 8   # keep in step with validate_drawio
LABEL_LINE_H, LABEL_TOP_PAD, LABEL_WRAP = 18, 4, 22       # node label: px per line, gap under the icon, chars per line
TITLE_Y = 32
LEGEND_W = 300
MARGIN = 80

PTS = ("points=[[0,0,0],[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0,0],[0,1,0],[0.25,1,0],[0.5,1,0],[0.75,1,0],"
       "[1,1,0],[0,0.25,0],[0,0.5,0],[0,0.75,0],[1,0.25,0],[1,0.5,0],[1,0.75,0]];")
GROUP_PTS = ("points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[0,1],[0.25,1],[0.5,1],[0.75,1],[1,1],[0,0.25],"
             "[0,0.5],[0,0.75],[1,0.25],[1,0.5],[1,0.75]];")
LABEL_STYLE = "verticalLabelPosition=bottom;verticalAlign=top;align=center;"
# {B} is the bottom port ratio of the node whose bottom the edge touches: (icon + label height) / icon, so a
# vertical edge starts or ends under the label instead of running through it.
PORTS = {
    "right": ("exitX=1;exitY=0.5;exitDx=0;exitDy=0;", "entryX=0;entryY=0.5;entryDx=0;entryDy=0;"),
    "left": ("exitX=0;exitY=0.5;exitDx=0;exitDy=0;", "entryX=1;entryY=0.5;entryDx=0;entryDy=0;"),
    "up": ("exitX=0.5;exitY=0;exitDx=0;exitDy=0;", "entryX=0.5;entryY={B};entryDx=0;entryDy=0;entryPerimeter=0;"),
    "down": ("exitX=0.5;exitY={B};exitDx=0;exitDy=0;exitPerimeter=0;", "entryX=0.5;entryY=0;entryDx=0;entryDy=0;"),
}
# side of the node an edge touches, per direction (source side, target side)
SIDES = {"right": ("R", "L"), "left": ("L", "R"), "up": ("T", "B"), "down": ("B", "T")}


class SpecError(ValueError):
    pass


def attr(value: str) -> str:
    return escape(value, {'"': "&quot;"})


class Builder:
    def __init__(self, spec: dict, index: dict):
        self.spec = spec
        self.index = index["stencils"]
        self.font = spec.get("font", "Amazon Ember")
        self.cells: list[str] = []
        self.nodes = {n["id"]: n for n in spec.get("nodes", [])}
        self.groups = {g["id"]: g for g in spec.get("groups", [])}
        self._check()
        self.row_breaks = self._row_breaks()

    # ---- grid ---------------------------------------------------------------------------------
    def cx(self, col: int) -> int:
        return COL0 + COL_PITCH * col

    def ly(self, lane: int) -> int:
        return LANE0 + LANE_PITCH * lane + ROW_GAP * sum(1 for b in self.row_breaks if b <= lane)

    def _row_breaks(self) -> list[int]:
        """A lane starts a new group row when some group ends on the lane above it and another begins on it;
        the extra 50 px keeps the lower group's title row clear of the upper group's bottom padding."""
        tops = {min(g["lanes"]) for g in self.groups.values()}
        bottoms = {max(g["lanes"]) for g in self.groups.values()}
        return sorted(j for j in tops if j - 1 in bottoms)

    def group_rect(self, g: dict) -> tuple[int, int, int, int]:
        cols, lanes = sorted(g["cols"]), sorted(g["lanes"])
        x = self.cx(cols[0]) - GROUP_HALF_W
        w = self.cx(cols[-1]) - self.cx(cols[0]) + 2 * GROUP_HALF_W
        y = self.ly(lanes[0]) - ICON // 2 - GROUP_ABOVE
        h = self.ly(lanes[-1]) - self.ly(lanes[0]) + ICON + GROUP_ABOVE + GROUP_BELOW
        return x, y, w, h

    def _check(self) -> None:
        if not self.nodes:
            raise SpecError("spec has no nodes")
        seen = set()
        for nid, n in self.nodes.items():
            if nid in seen:
                raise SpecError(f"duplicate node id '{nid}'")
            seen.add(nid)
            for k in ("col", "lane"):
                if not isinstance(n.get(k), int) or n[k] < 0:
                    raise SpecError(f"node '{nid}': '{k}' must be a non-negative integer")
            if "icon" in n:
                if n["icon"] not in self.index:
                    raise SpecError(f"node '{nid}': unknown stencil '{n['icon']}' — look it up in references/aws-icons-*.md")
            elif "image" in n:
                if not (EXTRA_ICONS / n["image"]).is_file():
                    raise SpecError(f"node '{nid}': image '{n['image']}' not found in assets/extra-icons/")
            else:
                raise SpecError(f"node '{nid}': needs 'icon' or 'image'")
            g = n.get("group")
            if g is None and not n.get("outside") and self.spec.get("cloud", "AWS Cloud"):
                raise SpecError(f"node '{nid}': inside the cloud but has no 'group' (set \"outside\": true for users/on-prem)")
            if g is not None:
                if g not in self.groups:
                    raise SpecError(f"node '{nid}': group '{g}' is not defined")
                grp = self.groups[g]
                if n["col"] not in grp["cols"] or n["lane"] not in grp["lanes"]:
                    raise SpecError(f"node '{nid}': cell ({n['col']},{n['lane']}) is outside group '{g}' cells")
        occupied: dict[tuple[int, int], str] = {}
        for nid, n in self.nodes.items():
            cell = (n["col"], n["lane"])
            if cell in occupied:
                raise SpecError(f"nodes '{occupied[cell]}' and '{nid}' share cell {cell}")
            occupied[cell] = nid
        self.occupied = occupied
        gcells: dict[tuple[int, int], str] = {}
        for gid, g in self.groups.items():
            for c in g["cols"]:
                for l in g["lanes"]:
                    if (c, l) in gcells:
                        raise SpecError(f"groups '{gcells[(c, l)]}' and '{gid}' overlap at cell ({c},{l})")
                    gcells[(c, l)] = gid
        for e in self.spec.get("edges", []):
            for k in ("from", "to"):
                if e.get(k) not in self.nodes:
                    raise SpecError(f"edge {e}: '{k}' must name a node")

    # ---- edges --------------------------------------------------------------------------------
    def edge_geometry(self, e: dict) -> tuple[str, str, str, str]:
        """(direction, exit ports, entry ports, kind) — kind is 'straight' or 'bend'."""
        s, t = self.nodes[e["from"]], self.nodes[e["to"]]
        ports = lambda d, n: tuple(p.replace("{B}", str(self.bottom_ratio(n))) for p in PORTS[d])
        if s["col"] == t["col"]:
            d = "up" if t["lane"] < s["lane"] else "down"
            return d, *ports(d, t if d == "up" else s), "straight"
        if s["lane"] == t["lane"]:
            d = "right" if t["col"] > s["col"] else "left"
            return d, *ports(d, s), "straight"
        if abs(t["col"] - s["col"]) != 1 or abs(t["lane"] - s["lane"]) != 1:
            raise SpecError(f"edge {e['from']}→{e['to']}: cells ({s['col']},{s['lane']})→({t['col']},{t['lane']}) are neither "
                            "aligned nor adjacent; a single bend only reaches the next column and lane. Move the target "
                            "onto the source's column or lane, into the adjacent diagonal cell, or route via a node in between")
        vertical = "up" if t["lane"] < s["lane"] else "down"
        horizontal = "right" if t["col"] > s["col"] else "left"
        return f"{vertical}-{horizontal}", ports(vertical, s)[0], PORTS[horizontal][1], "bend"

    def incident_sides(self) -> dict[str, set[str]]:
        """Sides of each node touched by edges. One edge per side: two edges on the same side of a node
        leave through the same port and render on top of each other (validator W8)."""
        sides: dict[str, set[str]] = {nid: set() for nid in self.nodes}
        owner: dict[tuple[str, str], str] = {}
        for i, e in enumerate(self.spec.get("edges", []), 1):
            d, _, _, kind = self.edge_geometry(e)
            if kind == "straight":
                ss, ts = SIDES[d]
            else:
                v, h = d.split("-")
                ss, ts = SIDES[v][0], SIDES[h][1]
            eid = e.get("id", f"e{i}")
            for nid, side in ((e["from"], ss), (e["to"], ts)):
                if (nid, side) in owner:
                    name = {"T": "top", "B": "bottom", "L": "left", "R": "right"}[side]
                    raise SpecError(f"node '{nid}': edges {owner[(nid, side)]} and {eid} both use its {name} side — they would "
                                    "overlap. Move one neighbour to another lane/column so each side carries one edge")
                owner[(nid, side)] = eid
                sides[nid].add(side)
        return sides

    # ---- labels -------------------------------------------------------------------------------
    @staticmethod
    def wrap(label: str) -> str:
        """Labels longer than LABEL_WRAP characters break into two lines at the space nearest the middle,
        so a label never reaches the neighbouring column (240 px pitch, ~7 px per bold character)."""
        if "<br>" in label or len(label) <= LABEL_WRAP or " " not in label:
            return label
        words = label.split(" ")
        best, best_diff = 1, 10 ** 6
        for i in range(1, len(words)):
            diff = abs(len(" ".join(words[:i])) - len(" ".join(words[i:])))
            if diff < best_diff:
                best, best_diff = i, diff
        return " ".join(words[:best]) + "<br>" + " ".join(words[best:])

    def label_h(self, n: dict) -> int:
        """Height of the label block under the icon (gap + lines)."""
        return LABEL_TOP_PAD + LABEL_LINE_H * (self.wrap(n["label"]).count("<br>") + 1)

    def bottom_ratio(self, n: dict) -> float:
        """exitY/entryY that puts the port under the label rather than on the icon's bottom edge."""
        return round((ICON + self.label_h(n)) / ICON, 3)

    @staticmethod
    def free_label_offset(e, d, label, node_xy, borders, label_h) -> float:
        """Relative position (-1 source … 1 target) along a straight edge where the label box covers no
        container border; the position nearest the midpoint wins, 0 if none is free (W7 will say so)."""
        sx, sy = node_xy[e["from"]]
        tx, ty = node_xy[e["to"]]
        half_w = LABEL_CHAR_PX * len(label) / 2 + LABEL_PAD_PX
        if d in ("right", "left"):
            x1, x2 = (sx + ICON, tx) if d == "right" else (tx + ICON, sx)
            line_y = sy + ICON / 2
            def box(k):
                cx = (x1 + x2) / 2 + k * (x2 - x1) / 2 * (1 if d == "right" else -1)
                return (cx - half_w, line_y - 2 * LABEL_HALF_H, cx + half_w, line_y), (x1 + half_w <= cx <= x2 - half_w)
        else:
            y1, y2 = (sy + ICON + label_h[e["from"]], ty) if d == "down" else (ty + ICON + label_h[e["to"]], sy)
            line_x = sx + ICON / 2
            def box(k):
                cy = (y1 + y2) / 2 + k * (y2 - y1) / 2 * (1 if d == "down" else -1)
                cx = line_x - half_w - 4
                return (cx - half_w, cy - LABEL_HALF_H, cx + half_w, cy + LABEL_HALF_H), (y1 + LABEL_HALF_H <= cy <= y2 - LABEL_HALF_H)

        def clear(b):
            for gx, gy, gw, gh in borders:
                hit_v = any(b[0] <= bx <= b[2] for bx in (gx, gx + gw)) and b[1] < gy + gh and b[3] > gy
                hit_h = any(b[1] <= by <= b[3] for by in (gy, gy + gh)) and b[0] < gx + gw and b[2] > gx
                if hit_v or hit_h:
                    return False
            return True

        for step in range(0, 20):
            for k in ((0.0,) if step == 0 else (-step / 20, step / 20)):
                b, inside = box(k)
                if inside and clear(b):
                    return round(k, 2)
        return 0.0

    # ---- emit ---------------------------------------------------------------------------------
    def vertex(self, cid, value, style, x, y, w, h, parent="1"):
        self.cells.append(
            f'<mxCell id="{cid}" value="{attr(value)}" style="{style}" vertex="1" parent="{parent}">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')

    def node_style(self, n: dict) -> str:
        # labelBackgroundColor matches the container so the label reads as part of the node and hides
        # nothing unless a line strays under it (which the port ratios prevent)
        label = f"{LABEL_STYLE}labelBackgroundColor={'#F7F8FA' if n.get('group') else '#FFFFFF'};"
        base = (f"sketch=0;{PTS}outlineConnect=0;fontColor=#232F3E;dashed=0;html=1;fontSize=13;fontStyle=1;"
                f"fontFamily={self.font};aspect=fixed;{label}")
        if "icon" in n:
            st = self.index[n["icon"]]
            fill = st.get("fillColor") or "#232F3E"
            if st["kind"] == "service":
                return base + f"fillColor={fill};strokeColor=#ffffff;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.{n['icon']};"
            if st["kind"] == "resource":
                return base + f"fillColor={fill};strokeColor=none;shape=mxgraph.aws4.{n['icon']};"
            raise SpecError(f"node '{n['id']}': '{n['icon']}' is a group badge, not an icon")
        b64 = base64.b64encode((EXTRA_ICONS / n["image"]).read_bytes()).decode()
        return (f"shape=image;aspect=fixed;imageAspect=0;html=1;fontColor=#232F3E;fontSize=13;fontStyle=1;fontFamily={self.font};"
                f"{label}image=data:image/svg+xml,{b64};")

    def build(self) -> str:
        spec, font = self.spec, self.font
        cloud_label = spec.get("cloud", "AWS Cloud")
        rects = {gid: self.group_rect(g) for gid, g in self.groups.items()}
        ids = list(rects)
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                ax, ay, aw, ah = rects[a]
                bx, by, bw, bh = rects[b]
                if ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah:
                    raise SpecError(f"groups '{a}' and '{b}' overlap once padded — give them different lanes or columns")
        node_xy = {nid: (self.cx(n["col"]) - ICON // 2, self.ly(n["lane"]) - ICON // 2) for nid, n in self.nodes.items()}

        # cloud box around the groups (and any grouped node)
        cloud = None
        if cloud_label and rects:
            xs = [r[0] for r in rects.values()] + [r[0] + r[2] for r in rects.values()]
            ys = [r[1] for r in rects.values()] + [r[1] + r[3] for r in rects.values()]
            cloud = (min(xs) - CLOUD_PAD, min(ys) - CLOUD_PAD, max(xs) - min(xs) + 2 * CLOUD_PAD, max(ys) - min(ys) + 2 * CLOUD_PAD)

        right = max([x + ICON for x, _ in node_xy.values()] + ([cloud[0] + cloud[2]] if cloud else []) + [r[0] + r[2] for r in rects.values()])
        label_h = {nid: self.label_h(n) for nid, n in self.nodes.items()}
        bottom = max([y + ICON + label_h[nid] + 30 for nid, (_, y) in node_xy.items()] + ([cloud[1] + cloud[3]] if cloud else []) + [r[1] + r[3] for r in rects.values()])
        W = int(-(-(right + MARGIN) // 10) * 10)
        H = int(-(-(bottom + 45) // 10) * 10)

        self.vertex("bg", "", "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=none;", 0, 0, W, H)
        title = f'<font style="font-size:20px"><b>{spec.get("title", "Architecture")}</b></font>'
        if spec.get("subtitle"):
            title += f'<br><font color="#5A6C86">{spec["subtitle"]}</font>'
        self.vertex("title", title,
                    f"text;html=1;align=left;verticalAlign=top;whiteSpace=wrap;rounded=0;fontFamily={font};fontSize=12;fontColor=#232F3E;spacing=0;",
                    40, TITLE_Y, W - LEGEND_W - 80, 60)

        edges = spec.get("edges", [])
        if any(e.get("dashed") for e in edges) and any(not e.get("dashed") for e in edges):
            lx, ly = W - LEGEND_W, TITLE_Y + 12
            text = f"text;html=1;align=left;verticalAlign=middle;fontFamily={font};fontSize=11;fontColor=#5A6C86;"
            self.vertex("lg1", "", "shape=line;strokeWidth=2;strokeColor=#232F3E;html=1;", lx, ly, 40, 10)
            self.vertex("lg1t", spec.get("legend_solid", "request / data flow"), text, lx + 48, ly - 6, 200, 22)
            self.vertex("lg2", "", "shape=line;strokeWidth=2;strokeColor=#232F3E;dashed=1;html=1;", lx, ly + 24, 40, 10)
            self.vertex("lg2t", spec.get("legend_dashed", "async / auxiliary"), text, lx + 48, ly + 18, 200, 22)

        if cloud:
            self.vertex("cloud", cloud_label,
                        f"{GROUP_PTS}outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontFamily={font};fontSize=14;fontStyle=1;"
                        "verticalAlign=top;align=left;spacingLeft=30;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_aws_cloud_alt;"
                        "strokeColor=#232F3E;fontColor=#232F3E;fillColor=none;container=1;dropTarget=1;", *cloud)
        ox, oy = (cloud[0], cloud[1]) if cloud else (0, 0)
        gstyle = (f"rounded=0;whiteSpace=wrap;html=1;fillColor=#F7F8FA;strokeColor=#C9D1D9;strokeWidth=1;fontColor=#232F3E;"
                  f"fontFamily={font};fontSize=13;fontStyle=1;verticalAlign=top;align=left;spacingLeft=12;spacingTop=4;container=1;dropTarget=1;")
        for gid, (x, y, w, h) in rects.items():
            self.vertex(gid, self.groups[gid]["label"], gstyle, x - ox, y - oy, w, h, "cloud" if cloud else "1")

        self.incident_sides()                                   # raises on a shared side
        for nid, n in self.nodes.items():
            x, y = node_xy[nid]
            parent = n.get("group") or "1"
            if parent != "1":
                gx, gy = rects[parent][0], rects[parent][1]
                x, y = x - gx, y - gy
            self.vertex(nid, self.wrap(n["label"]), self.node_style(n), x, y, ICON, ICON, parent)

        borders = list(rects.values()) + ([cloud] if cloud else [])
        base_edge = (f"edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=2;strokeColor=#232F3E;"
                     f"fontFamily={font};fontSize=11;fontColor=#232F3E;labelBackgroundColor=#FFFFFF;endArrow=block;endFill=1;")
        for i, e in enumerate(edges, 1):
            d, exit_p, entry_p, kind = self.edge_geometry(e)
            style = base_edge + exit_p + entry_p
            if e.get("dashed"):
                style += "dashed=1;"
            if e.get("error"):
                style += "dashed=1;strokeColor=#DD344C;"
            label = e.get("label", "")
            geo_x = ""
            if label and kind == "bend":
                raise SpecError(f"edge {e['from']}→{e['to']}: a bent edge cannot carry a label (draw.io centres it on the "
                                "corner). Drop the label or put the target on the source's lane/column")
            if label:
                if kind == "straight" and d in ("right", "left"):
                    style += "verticalAlign=bottom;"
                elif kind == "straight":
                    style += "align=right;spacingRight=4;"
                offset = e.get("label_offset")
                if offset is None and kind == "straight":
                    offset = self.free_label_offset(e, d, label, node_xy, borders, label_h)
                if offset:
                    geo_x = f' x="{offset}"'
            val = f' value="{attr(label)}"' if label else ""
            # A bent edge leaves under the source label, i.e. from a point outside the shape; draw.io's router
            # then picks the first leg's direction itself and may go sideways along the label. Pin the corner.
            pts = ""
            if kind == "bend":
                cx = node_xy[e["from"]][0] + ICON // 2
                cy = node_xy[e["to"]][1] + ICON // 2
                pts = f'<Array as="points"><mxPoint x="{cx}" y="{cy}"/></Array>'
            geo = f'<mxGeometry{geo_x} relative="1" as="geometry">{pts}</mxGeometry>' if pts else f'<mxGeometry{geo_x} relative="1" as="geometry"/>'
            self.cells.append(
                f'<mxCell id="{e.get("id", f"e{i}")}"{val} style="{style}" edge="1" parent="1" source="{e["from"]}" target="{e["to"]}">'
                f'{geo}</mxCell>')

        name = spec.get("page", spec.get("title", "Page-1"))
        return ('<mxfile host="app.diagrams.net">'
                f'<diagram id="{attr(spec.get("id", "page1"))}" name="{attr(name)}">'
                f'<mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" '
                f'page="1" pageScale="1" pageWidth="{W}" pageHeight="{H}" math="0" shadow="0"><root>'
                '<mxCell id="0"/><mxCell id="1" parent="0"/>' + "".join(self.cells) +
                '</root></mxGraphModel></diagram></mxfile>')


def build(spec: dict, index_path: Path = INDEX) -> str:
    return Builder(spec, json.loads(index_path.read_text())).build()


def hints(spec: dict) -> list[str]:
    """Non-blocking layout hints: groups with more empty cells than icons, lanes with a single icon."""
    out: list[str] = []
    nodes = spec.get("nodes", [])
    for g in spec.get("groups", []):
        cells = len(g["cols"]) * len(g["lanes"])
        used = sum(1 for n in nodes if n.get("group") == g["id"])
        if cells - used > max(used, 1):
            out.append(f"hint: group '{g['id']}' has {used} icon(s) in {cells} cells ({cells - used} empty) — shrink it or "
                       "move icons in (review-checklist.md § Grouping)")
    lanes = {}
    for n in nodes:
        lanes.setdefault(n["lane"], []).append(n["id"])
    for lane, ids in sorted(lanes.items()):
        if len(ids) == 1 and len(nodes) > 4:
            out.append(f"hint: lane {lane} holds only '{ids[0]}' — a whole lane for one icon leaves an empty band; "
                       "consider another lane or sharing this one")
    return out


def main(argv: list[str] | None = None) -> int:
    args = [a for a in (sys.argv[1:] if argv is None else argv) if not a.startswith("--")]
    flags = {a for a in (sys.argv[1:] if argv is None else argv) if a.startswith("--")}
    if len(args) != 2:
        print(__doc__)
        return 2
    spec_path, out_path = Path(args[0]), Path(args[1])
    try:
        xml = build(json.loads(spec_path.read_text(encoding="utf-8")))
    except SpecError as exc:
        print(f"ERROR spec: {exc}")
        return 1
    out_path.write_text(xml, encoding="utf-8")
    print(f"wrote {out_path}")
    for h in hints(json.loads(spec_path.read_text(encoding="utf-8"))):
        print(f"  {h}")
    if "--no-validate" in flags:
        return 0
    sys.path.insert(0, str(HERE))
    import validate_drawio  # noqa: E402

    return validate_drawio.main([str(out_path)])


if __name__ == "__main__":
    sys.exit(main())
