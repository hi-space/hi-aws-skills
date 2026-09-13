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
the last. Edges between cells in the same column/lane are straight (empty corridor). Any other pair is
joined with ONE bend: first along the source's column to the target's lane, then across ("v", the fan-out
pattern), or first across on the source's lane, then along the target's column ("h") — whichever route
crosses no icon (the builder picks "v" when both are free; `"route": "h"` forces the other). Both legs must
be empty of icons, else it is a spec error naming the blockers. A node side carries one straight edge, or
a *bus* of bent edges that all leave (or all arrive) there and share the first/last leg — so a hub keeps
its own column clear above/below and stacks its neighbours in the columns around it. Cross-cutting sinks (CloudWatch) still get one representative edge. Only straight
edges may carry a label. Node labels longer than 22 characters break into two lines at the middle space.
`icon` names come from scripts/stencil-index.json; `image` names a file in assets/extra-icons/.

Exit status: 0 only when the validator reports 0 errors and no W4–W9 layout defect; 1 otherwise (do not
ship the file — change the spec).

Auto layout: nodes without `col`/`lane` (or `"layout": "auto"`) are placed by scripts/layout.py — columns from the
request flow, lanes by search under the rules above; groups become one or more rectangles per role. The placed
spec is saved as `<spec stem>.layout.json` for hand adjustments. Start from `scaffold_spec.py <name>.brief.md
<name>.json`, which writes that coordinate-free spec straight from the brief.

Brief check: when `<spec stem>.brief.md` exists next to the spec (or `--brief PATH` is given) the builder compares
the spec with the brief — every Components row is a node (rows marked "not drawn" excepted), every Relationships
row is an edge with the same direction (rows whose Kind says "aux" may be left out), and nothing exists in the
spec that the brief does not list. A mismatch is an error: the diagram must be as detailed as the brief.
`--no-brief` skips the check (say why in Decisions).

Usage: build_diagram.py SPEC.json OUT.drawio [--brief BRIEF.md | --no-brief] [--no-validate]
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
TITLE_BAND = 28                                          # px: a container's title row — no edge label sits on it (validate_drawio)
BADGE_H = 18                                             # px: edge number badge (11 pt bold on a dark pill); width 10 + 7/digit
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
            if e["from"] == e["to"]:
                raise SpecError(f"edge {e['from']}→{e['to']}: a node cannot connect to itself (draw.io draws a box around "
                                "the icon). A retry/loop is a note in the brief's Flow, not an edge")

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
        vertical = "up" if t["lane"] < s["lane"] else "down"
        horizontal = "right" if t["col"] > s["col"] else "left"
        route = e.get("route") or self.bend_route(s, t)
        if route == "v":                                  # trunk down/up the source's column, then across on the target's lane
            return f"{vertical}-{horizontal}", ports(vertical, s)[0], PORTS[horizontal][1], "bend"
        if route == "h":                                  # across on the source's lane, then down/up the target's column
            return f"{horizontal}-{vertical}", PORTS[horizontal][0], ports(vertical, t)[1], "bend-h"
        bv, bh = self.bend_blockers(s, t, "v"), self.bend_blockers(s, t, "h")
        raise SpecError(f"edge {e['from']}→{e['to']}: cells ({s['col']},{s['lane']})→({t['col']},{t['lane']}) cannot be joined "
                        f"with one bend: the vertical-first route runs through {', '.join(bv)}; the horizontal-first route "
                        f"through {', '.join(bh)}. Move one of them, or route via a node in between")

    def bend_blockers(self, s: dict, t: dict, route: str) -> list[str]:
        """Nodes sitting on the two legs of an L from s to t. 'v': trunk in s's column to t's lane, then across.
        'h': across on s's lane to t's column, then trunk to t."""
        corner = (s["col"], t["lane"]) if route == "v" else (t["col"], s["lane"])
        cells = []
        step = 1 if t["lane"] > s["lane"] else -1
        cstep = 1 if t["col"] > s["col"] else -1
        if route == "v":
            cells += [(s["col"], l) for l in range(s["lane"] + step, t["lane"] + step, step)]
            cells += [(c, t["lane"]) for c in range(s["col"] + cstep, t["col"], cstep)]
        else:
            cells += [(c, s["lane"]) for c in range(s["col"] + cstep, t["col"] + cstep, cstep)]
            cells += [(t["col"], l) for l in range(s["lane"] + step, t["lane"], step)]
        return [f"'{self.occupied[c]}' at {c}" for c in cells if c in self.occupied]

    def bend_route(self, s: dict, t: dict) -> str | None:
        """'v' when the vertical-first L is free of icons, else 'h' when the horizontal-first one is, else None."""
        if not self.bend_blockers(s, t, "v"):
            return "v"
        if not self.bend_blockers(s, t, "h"):
            return "h"
        return None

    def incident_sides(self) -> dict[str, set[str]]:
        """Sides of each node touched by edges. A side carries either one straight edge or a *bus* of bent
        edges that all leave (or all arrive) there: those share their first (last) leg and read as one trunk with
        branches. A straight edge next to a bend, or leaving and arriving bends on one side, would draw two
        arrows on the same line (validator W8) — refused."""
        sides: dict[str, set[str]] = {nid: set() for nid in self.nodes}
        owner: dict[tuple[str, str], tuple[str, str, str]] = {}   # (node, side) -> (edge id, kind, role)
        names = {"T": "top", "B": "bottom", "L": "left", "R": "right"}
        for i, e in enumerate(self.spec.get("edges", []), 1):
            d, _, _, kind = self.edge_geometry(e)
            if kind == "straight":
                ss, ts = SIDES[d]
            else:
                first, second = d.split("-")
                ss, ts = SIDES[first][0], SIDES[second][1]
            eid = e.get("id", f"e{i}")
            for nid, side, role in ((e["from"], ss, "out"), (e["to"], ts, "in")):
                prev = owner.get((nid, side))
                if prev is not None:
                    pid, pkind, prole = prev
                    if kind == "straight" or pkind == "straight":
                        raise SpecError(f"node '{nid}': edges {pid} and {eid} both use its {names[side]} side and one of them is "
                                        "straight — they would overlap. Only bent edges may share a side (as a bus); move one "
                                        "neighbour to another lane/column")
                    if prole != role:
                        raise SpecError(f"node '{nid}': edges {pid} and {eid} both use its {names[side]} side but one arrives and "
                                        "one leaves — two arrowheads on one trunk. Put the arriving edge on another side")
                owner[(nid, side)] = (eid, kind, role)
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
    def badge_x_at_corner(leg1: float, leg2: float) -> float:
        """draw.io relative x (-1 source … 1 target, measured by length) of the corner of an L edge."""
        total = leg1 + leg2
        return round(2 * leg1 / total - 1, 3) if total else 0.0

    @staticmethod
    def edge_run(e, d, node_xy, label_h):
        """(a, b, line, horizontal): the free run of a straight edge between its two icons — x-range a..b on a
        horizontal edge (line = its y), y-range on a vertical one (line = its x); the vertical run starts under
        the upper node's label."""
        sx, sy = node_xy[e["from"]]
        tx, ty = node_xy[e["to"]]
        if d in ("right", "left"):
            a, b = (sx + ICON, tx) if d == "right" else (tx + ICON, sx)
            return a, b, sy + ICON / 2, True
        a, b = (sy + ICON + label_h[e["from"]], ty) if d == "down" else (ty + ICON + label_h[e["to"]], sy)
        return a, b, sx + ICON / 2, False

    @staticmethod
    def box_at(e, d, k, half_w, half_h, place, node_xy, label_h):
        """Box of a label-like thing at relative position k along a straight edge: `above` the line (text on a
        horizontal edge), `left` of it (text on a vertical edge) or `on` it (a number badge). Also whether its
        centre still lies within the free run."""
        a, b, line, horizontal = Builder.edge_run(e, d, node_xy, label_h)
        sign = 1 if d in ("right", "down") else -1
        c = (a + b) / 2 + k * (b - a) / 2 * sign
        if horizontal:
            cy = line - half_h if place == "above" else line
            return (c - half_w, cy - half_h, c + half_w, cy + half_h), a + half_w <= c <= b - half_w
        cx = line - half_w - 4 if place == "left" else line
        return (cx - half_w, c - half_h, cx + half_w, c + half_h), a + half_h <= c <= b - half_h

    @staticmethod
    def free_offset(e, d, half_w, half_h, place, node_xy, borders, label_h, avoid=(), prefer=None):
        """Relative position along a straight edge where the box covers no container border or title row and none
        of the `avoid` boxes: `prefer` first, then the midpoint, then outwards in 1/20 steps. None if nothing is
        free (the validator's W7 will say so)."""
        def clear(bx):
            for gx, gy, gw, gh in borders:
                hit_v = any(bx[0] <= x <= bx[2] for x in (gx, gx + gw)) and bx[1] < gy + gh and bx[3] > gy
                hit_h = any(bx[1] <= y <= bx[3] for y in (gy, gy + gh)) and bx[0] < gx + gw and bx[2] > gx
                on_title = bx[0] < gx + gw and bx[2] > gx and bx[1] < gy + TITLE_BAND and bx[3] > gy
                if hit_v or hit_h or on_title:
                    return False
            for o in avoid:
                if bx[0] < o[2] and bx[2] > o[0] and bx[1] < o[3] and bx[3] > o[1]:
                    return False
            return True

        candidates = ([prefer] if prefer is not None else []) + [0.0] + [s * k / 20 for k in range(1, 20) for s in (-1, 1)]
        for k in candidates:
            bx, inside = Builder.box_at(e, d, k, half_w, half_h, place, node_xy, label_h)
            if inside and clear(bx):
                return round(k, 2)
        return None

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
            eid = e.get("id", f"e{i}")
            d, exit_p, entry_p, kind = self.edge_geometry(e)
            style = base_edge + exit_p + entry_p
            if e.get("dashed"):
                style += "dashed=1;"
            if e.get("error"):
                style += "dashed=1;strokeColor=#DD344C;"
            label = e.get("label", "")
            geo_x, text_box = "", None
            if label and kind != "straight":
                raise SpecError(f"edge {e['from']}→{e['to']}: a bent edge cannot carry a label (draw.io centres it on the "
                                "corner). Drop the label or put the target on the source's lane/column")
            if label:
                place = "above" if d in ("right", "left") else "left"
                style += "verticalAlign=bottom;" if place == "above" else "align=right;spacingRight=4;"
                half_w = LABEL_CHAR_PX * len(label) / 2 + LABEL_PAD_PX
                offset = e.get("label_offset")
                if offset is None:
                    offset = self.free_offset(e, d, half_w, LABEL_HALF_H, place, node_xy, borders, label_h)
                    if offset is None:
                        offset = 0.0                                 # nothing free: W7 will name it
                if offset:
                    geo_x = f' x="{offset}"'
                text_box, _ = self.box_at(e, d, offset, half_w, LABEL_HALF_H, place, node_xy, label_h)
            val = f' value="{attr(label)}"' if label else ""
            # A bent edge leaves under the source label, i.e. from a point outside the shape; draw.io's router
            # then picks the first leg's direction itself and may go sideways along the label. Pin the corner.
            pts, corner = "", None
            sx, sy = node_xy[e["from"]]
            tx, ty = node_xy[e["to"]]
            if kind == "bend":                                   # corner on the source's column, target's lane
                corner = (sx + ICON // 2, ty + ICON // 2)
            elif kind == "bend-h":                               # corner on the source's lane, target's column
                corner = (tx + ICON // 2, sy + ICON // 2)
            if corner:
                pts = f'<Array as="points"><mxPoint x="{corner[0]}" y="{corner[1]}"/></Array>'
            geo = f'<mxGeometry{geo_x} relative="1" as="geometry">{pts}</mxGeometry>' if pts else f'<mxGeometry{geo_x} relative="1" as="geometry"/>'
            self.cells.append(
                f'<mxCell id="{eid}"{val} style="{style}" edge="1" parent="1" source="{e["from"]}" target="{e["to"]}">'
                f'{geo}</mxCell>')

            # the relationship number as a badge on the line — the link between the picture and the guide's steps
            num = e.get("num")
            if num is None:
                continue
            badge_hw = (10 + 7 * len(str(num))) / 2
            if kind == "straight":
                prefer = None
                if text_box is not None:                         # beside the text: before it in reading order
                    a, b, line, horizontal = self.edge_run(e, d, node_xy, label_h)
                    sign = 1 if d in ("right", "down") else -1
                    mid, half_run = (a + b) / 2, (b - a) / 2
                    if horizontal:
                        centre = (text_box[0] + text_box[2]) / 2 - ((text_box[2] - text_box[0]) / 2 + badge_hw + 4)
                    else:
                        centre = (text_box[1] + text_box[3]) / 2 - (LABEL_HALF_H + BADGE_H / 2 + 2)
                    prefer = round((centre - mid) / half_run / sign, 2) if half_run else None
                bx = self.free_offset(e, d, badge_hw, BADGE_H / 2, "on", node_xy, borders, label_h,
                                      avoid=[text_box] if text_box else (), prefer=prefer)
                if bx is None:
                    bx = 0.0
            else:                                                # at the corner of the L
                if kind == "bend":
                    p = (sx + ICON // 2, sy if corner[1] < sy else sy + ICON + label_h[e["from"]])
                    q = (tx if corner[0] < tx else tx + ICON, ty + ICON // 2)
                else:
                    p = (sx if corner[0] < sx else sx + ICON, sy + ICON // 2)
                    q = (tx + ICON // 2, ty if corner[1] < ty else ty + ICON + label_h[e["to"]])
                leg1 = abs(corner[0] - p[0]) + abs(corner[1] - p[1])
                leg2 = abs(q[0] - corner[0]) + abs(q[1] - corner[1])
                bx = self.badge_x_at_corner(leg1, leg2)
            self.cells.append(
                f'<mxCell id="{eid}_n" value="{num}" style="edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;'
                f'points=[];fontFamily={font};fontSize=11;fontStyle=1;fontColor=#FFFFFF;labelBackgroundColor=#232F3E;'
                f'labelBorderColor=#232F3E;" vertex="1" connectable="0" parent="{eid}">'
                f'<mxGeometry x="{bx}" y="0" relative="1" as="geometry"><mxPoint as="offset"/></mxGeometry></mxCell>')

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


def _table_rows(text: str, heading: str) -> list[list[str]]:
    """Cells of every body row of the first markdown table under `## <heading>` (header and rule skipped)."""
    import re
    m = re.search(rf"^##\s+{re.escape(heading)}\b.*?$", text, re.M)
    if not m:
        return []
    section = text[m.end():]
    nxt = re.search(r"^##\s", section, re.M)
    if nxt:
        section = section[:nxt.start()]
    rows = []
    for line in section.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
        if all(set(c) <= set("-: ") for c in cells):
            continue
        rows.append(cells)
    return rows[1:] if rows else []


def _kind_column(brief_text: str) -> int | None:
    """Index of the Kind column in the Relationships table header, if any."""
    import re
    m = re.search(r"^##\s+Relationships\b.*?$", brief_text, re.M)
    if not m:
        return None
    for line in brief_text[m.end():].splitlines():
        if line.lstrip().startswith("|"):
            cells = [c.strip().lower() for c in line.strip().strip("|").split("|")]
            return next((i for i, c in enumerate(cells) if c.startswith("kind")), None)
    return None


def brief_contract(brief_text: str) -> dict:
    """The part of a brief the Drawer may never change: component ids and `From → To` pairs, each with its
    drawn / aux / not-drawn status (statuses may only move towards 'drawn' without a note)."""
    import re
    comps = {}
    for row in _table_rows(brief_text, "Components"):
        cid = row[0].strip("`* ")
        if cid:
            comps[cid] = "not drawn" if re.search(r"not drawn", " ".join(row), re.I) else "drawn"
    rels, k_i = {}, _kind_column(brief_text)
    for row in _table_rows(brief_text, "Relationships"):
        pair = None
        for cell in row:
            mm = re.search(r"([A-Za-z0-9_\-]+)\s*(?:→|->)\s*([A-Za-z0-9_\-]+)", cell)
            if mm:
                pair = f"{mm.group(1)} → {mm.group(2)}"
                break
        if not pair:
            continue
        kind = row[k_i] if k_i is not None and k_i < len(row) else " ".join(row)
        rels[pair] = ("not drawn" if re.search(r"not drawn", kind, re.I)
                      else "aux" if re.search(r"\baux\b", kind, re.I) else "primary")
    return {"components": comps, "relationships": rels}


def contract_path_for(brief_path: Path) -> Path:
    name = brief_path.name
    return brief_path.with_name(name[:-len(".brief.md")] + ".contract.json") if name.endswith(".brief.md") \
        else brief_path.with_suffix(".contract.json")


def contract_check(brief_text: str, contract_path: Path) -> tuple[list[str], list[str]]:
    """Freeze the brief's ids and pairs on the first Phase 3 run; afterwards refuse a brief whose ids or
    `From → To` pairs changed (the Drawer edits Label text and 'not drawn' markers, nothing else) and report
    rows that were newly marked aux / not drawn so the Reviewer sees the shrinkage. Returns (errors, notes)."""
    now = brief_contract(brief_text)
    if not contract_path.exists():
        contract_path.write_text(json.dumps(now, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return [], [f"contract written: {contract_path.name} ({len(now['components'])} components, "
                    f"{len(now['relationships'])} relationships) — ids and From → To pairs are frozen from here; only the "
                    "Architect deletes this file, when the architecture itself changed, and says so under Decisions"]
    old = json.loads(contract_path.read_text(encoding="utf-8"))
    errors, notes = [], []
    hint = (f" — the Drawer does not edit ids or From → To; if the Architect changed the architecture, delete "
            f"{contract_path.name} and record the change under Decisions")
    removed_c = sorted(set(old["components"]) - set(now["components"]))
    added_c = sorted(set(now["components"]) - set(old["components"]))
    if removed_c or added_c:
        errors.append(f"brief contract: components changed since {contract_path.name}"
                      + (f" — removed: {', '.join(removed_c)}" if removed_c else "")
                      + (f" — added: {', '.join(added_c)}" if added_c else "") + hint)
    removed_r = [p for p in old["relationships"] if p not in now["relationships"]]
    added_r = [p for p in now["relationships"] if p not in old["relationships"]]
    hard_removed = [p for p in removed_r if old["relationships"][p] == "primary"]
    soft_removed = [p for p in removed_r if old["relationships"][p] != "primary"]
    if hard_removed or added_r:
        errors.append(f"brief contract: relationships changed since {contract_path.name}"
                      + (f" — removed: {'; '.join(hard_removed)}" if hard_removed else "")
                      + (f" — added: {'; '.join(added_r)}" if added_r else "") + hint)
    if soft_removed:
        notes.append(f"note: aux relationships removed from the brief since the contract: {'; '.join(soft_removed)} "
                     "(the Reviewer's trim — record it under Decisions)")
    rank = {"drawn": 0, "primary": 0, "aux": 1, "not drawn": 2}
    shrunk = [f"{k} ({old['components'][k]} → {v})" for k, v in now["components"].items()
              if k in old["components"] and rank[v] > rank[old["components"][k]]]
    shrunk += [f"{k} ({old['relationships'][k]} → {v})" for k, v in now["relationships"].items()
               if k in old["relationships"] and rank[v] > rank[old["relationships"][k]]]
    if shrunk:
        notes.append(f"note: {len(shrunk)} row(s) newly marked aux / not drawn since the contract: {'; '.join(shrunk)} — "
                     "the Reviewer checks each is something the picture cannot show, not a layout shortcut")
    return errors, notes


def fill_nums(spec: dict, brief_text: str) -> None:
    """Give edges that have no `num` the brief's # for their From → To pair (hand-written specs; scaffolded ones
    carry it already). The number becomes the badge on the edge and the step number in the guide."""
    import re
    nums: dict[tuple[str, str], int] = {}
    for row in _table_rows(brief_text, "Relationships"):
        if not (row and row[0].strip().isdigit()):
            continue
        for cell in row:
            mm = re.search(r"([A-Za-z0-9_\-]+)\s*(?:→|->)\s*([A-Za-z0-9_\-]+)", cell)
            if mm:
                nums[(mm.group(1), mm.group(2))] = int(row[0])
                break
    for e in spec.get("edges", []):
        if "num" not in e and (e["from"], e["to"]) in nums:
            e["num"] = nums[(e["from"], e["to"])]


def brief_check(brief_text: str, spec: dict) -> tuple[list[str], str]:
    """Compare a brief with a spec. Returns (errors, one-line summary)."""
    import re
    comp_rows = _table_rows(brief_text, "Components")
    rel_rows = _table_rows(brief_text, "Relationships")
    if not comp_rows:
        return ["brief has no `## Components` table"], ""
    comps, not_drawn = [], []
    for row in comp_rows:
        cid = row[0].strip("`* ")
        if not cid:
            continue
        (not_drawn if re.search(r"not drawn", " ".join(row), re.I) else comps).append(cid)
    header_kind = None
    m = re.search(r"^##\s+Relationships\b.*?$", brief_text, re.M)
    if m:
        for line in brief_text[m.end():].splitlines():
            if line.lstrip().startswith("|"):
                cells = [c.strip().lower() for c in line.strip().strip("|").split("|")]
                header_kind = next((i for i, c in enumerate(cells) if c.startswith("kind")), None)
                break
    required, optional = [], []
    for row in rel_rows:
        pair = None
        for cell in row:
            mm = re.search(r"([A-Za-z0-9_\-]+)\s*(?:→|->)\s*([A-Za-z0-9_\-]+)", cell)
            if mm:
                pair = (mm.group(1), mm.group(2))
                break
        if not pair:
            continue
        kind = row[header_kind] if header_kind is not None and header_kind < len(row) else " ".join(row)
        aux = bool(re.search(r"\baux\b|not drawn", kind, re.I))
        (optional if aux else required).append(pair)
    nodes = {n["id"] for n in spec.get("nodes", [])}
    edges = {(e["from"], e["to"]) for e in spec.get("edges", [])}
    errors = []
    declared = re.search(r"Components:\s*(\d+)\b.*?Relationships:\s*(\d+)", brief_text, re.S)
    if declared:                                          # the Architect's own count — a shrunken table cannot hide
        dc, dr = int(declared.group(1)), int(declared.group(2))
        if dc != len(comps) + len(not_drawn) or dr != len(required) + len(optional):
            errors.append(f"the brief declares 'Components: {dc}' / 'Relationships: {dr}' but its tables hold "
                          f"{len(comps) + len(not_drawn)} / {len(required) + len(optional)} rows — the tables were cut "
                          "after Phase 1; restore them (the Drawer never edits the brief)")
    missing = [c for c in comps if c not in nodes]
    extra = sorted(nodes - set(comps) - set(not_drawn))
    if missing:
        errors.append(f"brief components with no node in the spec: {', '.join(missing)} — every component is drawn "
                      "(mark a row 'not drawn' in the brief only for things the picture cannot show)")
    if extra:
        errors.append(f"spec nodes the brief does not list: {', '.join(extra)} — add them to the brief's Components "
                      "table (with evidence) or remove them")
    missing_e = [f"{a} → {b}" for a, b in required if (a, b) not in edges]
    if missing_e:
        errors.append(f"brief relationships with no edge in the spec: {'; '.join(missing_e)} — primary relationships are "
                      "never dropped (only rows whose Kind says 'aux' may be left out)")
    known = set(required) | set(optional)
    extra_e = [f"{a} → {b}" for a, b in sorted(edges) if (a, b) not in known and (b, a) not in known]
    if extra_e:
        errors.append(f"spec edges the brief does not list: {'; '.join(extra_e)} — add them to the brief or remove them")
    drawn_opt = sum(1 for p in optional if p in edges)
    summary = (f"brief check: {len(comps)} components → {len(nodes)} nodes"
               f"{' (' + str(len(not_drawn)) + ' marked not drawn)' if not_drawn else ''}; "
               f"{len(required) + len(optional)} relationships → {len(edges)} edges "
               f"({len(optional) - drawn_opt} aux not drawn)")
    return errors, summary


def main(argv: list[str] | None = None) -> int:
    raw = sys.argv[1:] if argv is None else argv
    flags, args, brief_path = set(), [], None
    i = 0
    while i < len(raw):
        a = raw[i]
        if a == "--brief" and i + 1 < len(raw):
            brief_path, i = Path(raw[i + 1]), i + 2
            continue
        (flags.add(a) if a.startswith("--") else args.append(a))
        i += 1
    if len(args) != 2:
        print(__doc__)
        return 2
    spec_path, out_path = Path(args[0]), Path(args[1])
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    sys.path.insert(0, str(HERE))
    import layout  # noqa: E402

    if layout.needs_layout(spec):
        spec, notes = layout.plan(spec)
        planned = spec_path.with_suffix(".layout.json")
        planned.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"auto layout: placed {len(spec['nodes'])} nodes in {max(n['col'] for n in spec['nodes']) + 1} columns × "
              f"{max(n['lane'] for n in spec['nodes']) + 1} lanes, {len(spec['groups'])} group boxes → {planned.name} "
              "(edit that file and rebuild from it to adjust)")
        for n in notes:
            tag = "note" if n.startswith("label dropped") else "ERROR label" if n.startswith("label too long") else "unresolved"
            print(f"  {tag}: {n}")
        too_long = [n for n in notes if n.startswith("label too long")]
        if too_long:
            print(f"NOT CLEAN: {len(too_long)} primary relationship label(s) do not fit — shorten each in the brief's Label "
                  "column to the limit named, or write — when the pair explains itself, then re-run the scaffold. A primary "
                  "edge without its label is not an accepted trade-off; the placed spec is in the .layout.json for inspection")
            return 1
    if brief_path is None and "--no-brief" not in flags:
        candidate = spec_path.with_suffix(".brief.md")
        brief_path = candidate if candidate.exists() else None
    if brief_path is not None:
        fill_nums(spec, brief_path.read_text(encoding="utf-8"))
    try:
        xml = build(spec)
    except SpecError as exc:
        print(f"ERROR spec: {exc}")
        return 1
    if brief_path is not None:
        brief_text = brief_path.read_text(encoding="utf-8")
        c_errors, c_notes = contract_check(brief_text, contract_path_for(brief_path))
        for n in c_notes:
            print(f"  {n}")
        for err in c_errors:
            print(f"ERROR contract: {err}")
        if c_errors:
            print("NOT CLEAN: the brief's ids or From → To pairs changed after the contract was written — restore the brief")
            return 1
        errors, summary = brief_check(brief_text, spec)
        for err in errors:
            print(f"ERROR brief: {err}")
        if errors:
            print(f"{summary} — NOT CLEAN: the spec is smaller (or other) than the brief; fix the spec, not the brief")
            return 1
        print(f"{summary} ✓ ({brief_path.name})")
    elif "--no-brief" not in flags:
        print(f"note: no {spec_path.with_suffix('.brief.md').name} next to the spec — brief check skipped (pass --brief PATH). "
              "A diagram built without its brief check is not deliverable.")
    else:
        print("brief check SKIPPED (--no-brief) — test builds only; a deliverable diagram is always built next to its brief")
    out_path.write_text(xml, encoding="utf-8")
    print(f"wrote {out_path}")
    for h in hints(spec):
        print(f"  {h}")
    if "--no-validate" in flags:
        return 0
    sys.path.insert(0, str(HERE))
    import validate_drawio  # noqa: E402

    rc = validate_drawio.main([str(out_path)])
    if rc:
        print("NOT CLEAN — fix the spec and rebuild; do not export or hand this file to the Reviewer")
    return rc


if __name__ == "__main__":
    sys.exit(main())
