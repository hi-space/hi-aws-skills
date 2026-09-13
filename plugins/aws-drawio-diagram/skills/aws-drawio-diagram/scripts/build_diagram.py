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
its own column clear above/below and stacks its neighbours in the columns around it. Cross-cutting sinks (CloudWatch) still get one representative edge.
Edge `label` is the brief's *What flows* phrase, drawn on the edge: wrapped into at most 3 lines and placed on
the longest leg that has a clear spot (above/below a horizontal leg, beside a vertical one), off every border,
title row, icon, other label and other line — a bent edge carries it on one of its legs. A solid (primary)
edge whose text finds no room stops the build (`ERROR label`); on a dashed edge the text is dropped with a
`note:`. `label_offset` (−1 source … 1 target) pins the position by hand. Node labels longer than 22 characters
break into two lines at the middle space. `icon` names come from scripts/stencil-index.json; `image` names a
file in assets/extra-icons/.

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
OUTSIDE_GAP = 60                                         # px: users / on-prem sit this much further from the cloud than the grid says,
                                                         # so the edge into the cloud has a 121 px pocket for its text (16 characters)
# Edge text (the brief's *What flows* phrase): 11 pt, 6.2 px per character + 2 × 8 px padding, EDGE_LINE_H px per
# line, at most LABEL_MAX_LINES lines of LABEL_MAX_LINE_CHARS characters; the builder slides it along the edge in
# 1/20 steps and keeps LABEL_SLACK_PX from anything it must not touch. Keep in step with validate_drawio.
LABEL_CHAR_PX, LABEL_PAD_PX, LABEL_SLACK_PX = 6.2, 8, 4
EDGE_LINE_H, LABEL_MAX_LINES, LABEL_MAX_LINE_CHARS = 14, 3, 24
LABEL_SIDE_GAP = 4                                       # px between a vertical line and the text beside it (spacingRight/Left)
TITLE_BAND = 28                                          # px: a container's title row — no edge label sits on it (validate_drawio)
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


class LabelError(SpecError):
    """A primary (solid) edge's text has no clear place on the edge it was drawn on."""

    def __init__(self, problems: list[str]):
        super().__init__("; ".join(problems))
        self.problems = problems


def attr(value: str) -> str:
    return escape(value, {'"': "&quot;"})


# ---- edge text ---------------------------------------------------------------------------------
def chars_that_fit(px: float) -> int:
    """Characters of 11 pt text that fit in `px` pixels with the label's padding and the slide slack."""
    return max(0, int((px - 2 * LABEL_PAD_PX - LABEL_SLACK_PX) // LABEL_CHAR_PX))


def wrap_lines(text: str, width: int) -> list[str] | None:
    """Greedy word wrap of `text` to `width` characters per line; None when a single word is wider than that."""
    words = text.split()
    if not words or width <= 0 or max(len(w) for w in words) > width:
        return None
    lines, cur = [], words[0]
    for w in words[1:]:
        if len(cur) + 1 + len(w) <= width:
            cur += " " + w
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def label_lines(text: str, width: int) -> list[str] | None:
    """The lines an edge label takes on a segment that holds `width` characters per line: the fewest lines, then
    re-wrapped at the narrowest width that keeps that count so the lines come out even ('Fetch dynamic' /
    'credentials (optional)' rather than 'Fetch dynamic credentials' / '(optional)'). None when it needs more
    than LABEL_MAX_LINES lines or a word is wider than the segment."""
    width = min(width, LABEL_MAX_LINE_CHARS)
    lines = wrap_lines(text, width)
    if lines is None or len(lines) > LABEL_MAX_LINES:
        return None
    longest_word = max(len(w) for w in text.split())
    for w in range(longest_word, width + 1):
        cand = wrap_lines(text, w)
        if cand is not None and len(cand) <= len(lines):
            return cand
    return lines


def label_box_size(lines: list[str]) -> tuple[float, float]:
    """(half width, half height) of the drawn label box."""
    return (LABEL_CHAR_PX * max(len(l) for l in lines) / 2 + LABEL_PAD_PX, (EDGE_LINE_H * len(lines) + 2) / 2)


class Builder:
    def __init__(self, spec: dict, index: dict):
        self.spec = spec
        self.index = index["stencils"]
        self.font = spec.get("font", "Amazon Ember")
        self.cells: list[str] = []
        self.notes: list[str] = []                           # e.g. a dashed edge whose text found no room
        self.nodes = {n["id"]: n for n in spec.get("nodes", [])}
        self.groups = {g["id"]: g for g in spec.get("groups", [])}
        self._check()
        self.row_breaks = self._row_breaks()

    # ---- grid ---------------------------------------------------------------------------------
    def cx(self, col: int) -> int:
        return COL0 + COL_PITCH * col

    def ly(self, lane: int) -> int:
        return LANE0 + LANE_PITCH * lane + ROW_GAP * sum(1 for b in self.row_breaks if b <= lane)

    def outside_shift(self, n: dict) -> int:
        """Users / on-prem left of every inside column move OUTSIDE_GAP px further left (right of them: further
        right), so the edge into the cloud has room for its text outside the cloud border."""
        if not n.get("outside"):
            return 0
        inside = [m["col"] for m in self.nodes.values() if not m.get("outside")]
        if inside and n["col"] < min(inside):
            return -OUTSIDE_GAP
        if inside and n["col"] > max(inside):
            return OUTSIDE_GAP
        return 0

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
    def edge_path(e, d, kind, node_xy, label_h) -> list[tuple[float, float]]:
        """The polyline draw.io draws for the edge, source port first: two points for a straight edge, three for
        an L (the corner is pinned as a waypoint). Vertical runs start or end under a node's label (the B port)."""
        sx, sy = node_xy[e["from"]]
        tx, ty = node_xy[e["to"]]
        if kind == "straight":
            if d == "right":
                return [(sx + ICON, sy + ICON / 2), (tx, sy + ICON / 2)]
            if d == "left":
                return [(sx, sy + ICON / 2), (tx + ICON, sy + ICON / 2)]
            if d == "down":
                return [(sx + ICON / 2, sy + ICON + label_h[e["from"]]), (sx + ICON / 2, ty)]
            return [(sx + ICON / 2, sy), (sx + ICON / 2, ty + ICON + label_h[e["to"]])]
        if kind == "bend":                                   # vertical first: corner on the source's column
            corner = (sx + ICON / 2, ty + ICON / 2)
            p = (sx + ICON / 2, sy if corner[1] < sy else sy + ICON + label_h[e["from"]])
            q = (tx if corner[0] < tx else tx + ICON, ty + ICON / 2)
        else:                                                # horizontal first: corner on the target's column
            corner = (tx + ICON / 2, sy + ICON / 2)
            p = (sx if corner[0] < sx else sx + ICON, sy + ICON / 2)
            q = (tx + ICON / 2, ty if corner[1] < ty else ty + ICON + label_h[e["to"]])
        return [p, corner, q]

    @staticmethod
    def segments(path):
        """(x1, y1, x2, y2) per leg of a polyline."""
        return [(a[0], a[1], b[0], b[1]) for a, b in zip(path, path[1:])]

    @staticmethod
    def box_is_clear(box, borders, obstacles, segments, slack=LABEL_SLACK_PX) -> bool:
        """No container border or title row under the box, none of the `obstacles` boxes (icons with their labels,
        other edge labels) overlapping it, none of the `segments` (edge legs) running through it — with `slack`
        pixels to spare in each direction (slack / 2 per side), so the validator's exact check agrees after rounding."""
        s = slack / 2
        bx = (box[0] - s, box[1] - s, box[2] + s, box[3] + s)
        for gx, gy, gw, gh in borders:
            hit_v = any(bx[0] <= x <= bx[2] for x in (gx, gx + gw)) and bx[1] < gy + gh and bx[3] > gy
            hit_h = any(bx[1] <= y <= bx[3] for y in (gy, gy + gh)) and bx[0] < gx + gw and bx[2] > gx
            on_title = bx[0] < gx + gw and bx[2] > gx and bx[1] < gy + TITLE_BAND and bx[3] > gy
            if hit_v or hit_h or on_title:
                return False
        for o in obstacles:
            if bx[0] < o[2] and bx[2] > o[0] and bx[1] < o[3] and bx[3] > o[1]:
                return False
        for x1, y1, x2, y2 in segments:
            if y1 == y2:                                     # horizontal leg
                if bx[1] < y1 < bx[3] and min(x1, x2) < bx[2] and max(x1, x2) > bx[0]:
                    return False
            elif bx[0] < x1 < bx[2] and min(y1, y2) < bx[3] and max(y1, y2) > bx[1]:
                return False
        return True

    @staticmethod
    def place_label(text, path, borders, obstacles, segments, offset=None):
        """Where the edge's text goes: (lines, relative x along the edge, place, box) or None when no leg has a
        clear spot. Legs are tried branch before trunk (a leg shared with other edges — a bus — comes last), then
        longest first; on each, the text is wrapped to what the leg holds (≤ 3 lines) and slid from the leg's
        middle outwards in 1/20 steps — above then below a horizontal leg, left then right of a vertical one.
        `offset` (the spec's `label_offset`, −1 source … 1 target) pins the position instead and only picks the
        side."""
        legs = Builder.segments(path)
        lens = [abs(x2 - x1) + abs(y2 - y1) for x1, y1, x2, y2 in legs]
        total = sum(lens) or 1.0

        def shared(leg) -> bool:
            """Is this leg the trunk of a bus — collinear with a leg of another edge? Text there could belong to
            any branch, so the branch leg (unique to this edge) is tried first even when it is shorter."""
            x1, y1, x2, y2 = leg
            for ox1, oy1, ox2, oy2 in segments:
                if y1 == y2 and oy1 == oy2 and abs(y1 - oy1) <= 1 and min(x1, x2) < max(ox1, ox2) and max(x1, x2) > min(ox1, ox2):
                    return True
                if x1 == x2 and ox1 == ox2 and abs(x1 - ox1) <= 1 and min(y1, y2) < max(oy1, oy2) and max(y1, y2) > min(oy1, oy2):
                    return True
            return False

        order = sorted(range(len(legs)), key=lambda i: (shared(legs[i]), -lens[i]))
        for i in order:
            x1, y1, x2, y2 = legs[i]
            horizontal = y1 == y2
            lo, hi = (min(x1, x2), max(x1, x2)) if horizontal else (min(y1, y2), max(y1, y2))
            start = sum(lens[:i])
            # widest wrap first (fewest lines); narrower ones fit the pockets beside a border or a vertical line
            widths = [w for w in (LABEL_MAX_LINE_CHARS, 18, 14, 10, 8, 6) if not horizontal or w <= chars_that_fit(lens[i])]
            if horizontal and chars_that_fit(lens[i]) < LABEL_MAX_LINE_CHARS:
                widths.insert(0, chars_that_fit(lens[i]))
            tried: set[tuple] = set()
            for width in widths:
                lines = label_lines(text, width)
                if lines is None or tuple(lines) in tried:
                    continue
                tried.add(tuple(lines))
                half_w, half_h = label_box_size(lines)
                span = (hi - lo) / 2 - (half_w if horizontal else half_h)
                if span < 0:
                    continue
                if offset is not None:                       # pinned by hand: which leg holds that point?
                    at = total * (offset + 1) / 2
                    if not (start <= at <= start + lens[i]):
                        break
                    along = [x1 + (at - start) * (1 if x2 > x1 else -1)] if horizontal else [y1 + (at - start) * (1 if y2 > y1 else -1)]
                else:
                    mid = (lo + hi) / 2
                    along = [mid] + [mid + s * k / 20 * span for k in range(1, 21) for s in (-1, 1)]
                for place in (("above", "below") if horizontal else ("left", "right")):
                    for c in along:
                        if horizontal:
                            cy = y1 - half_h if place == "above" else y1 + half_h
                            box = (c - half_w, cy - half_h, c + half_w, cy + half_h)
                        else:
                            cx = x1 - half_w - LABEL_SIDE_GAP if place == "left" else x1 + half_w + LABEL_SIDE_GAP
                            box = (cx - half_w, c - half_h, cx + half_w, c + half_h)
                        if offset is None and not Builder.box_is_clear(box, borders, obstacles, segments):
                            continue
                        dist = start + abs(c - (x1 if horizontal else y1))
                        return lines, round(2 * dist / total - 1, 3), place, box
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
        node_xy = {nid: (self.cx(n["col"]) - ICON // 2 + self.outside_shift(n), self.ly(n["lane"]) - ICON // 2)
                   for nid, n in self.nodes.items()}

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
        # geometry of every edge first: the text of one edge must not sit on the line of another
        geom = []
        for i, e in enumerate(edges, 1):
            d, exit_p, entry_p, kind = self.edge_geometry(e)
            geom.append((e.get("id", f"e{i}"), e, d, exit_p, entry_p, kind, self.edge_path(e, d, kind, node_xy, label_h)))
        icon_boxes = [(x, y, x + ICON, y + ICON + label_h[nid]) for nid, (x, y) in node_xy.items()]
        # then the text — the brief's *What flows* phrase — solid (primary) edges first so they get the room
        placed: dict[str, tuple] = {}
        label_boxes: list[tuple] = []
        problems: list[str] = []
        for eid, e, d, exit_p, entry_p, kind, path in sorted(geom, key=lambda g: bool(g[1].get("dashed"))):
            text = " ".join(str(e.get("label", "")).split())
            if not text:
                continue
            other_lines = [seg for g in geom if g[0] != eid for seg in self.segments(g[6])]
            spot = self.place_label(text, path, borders, icon_boxes + label_boxes, other_lines, e.get("label_offset"))
            if spot is None:
                legs = self.segments(path)
                room = max(chars_that_fit(abs(x2 - x1) + abs(y2 - y1)) for x1, y1, x2, y2 in legs)
                why = (f"edge {e['from']} → {e['to']}: '{text}' has no clear place on its "
                       f"{'legs' if len(legs) > 1 else 'line'} (at most {min(room, LABEL_MAX_LINE_CHARS)} characters per line, "
                       f"{LABEL_MAX_LINES} lines; a longer word, a border, an icon or another label is in the way) — condense "
                       "the What flows phrase in the brief, or move a node in the .layout.json so the edge runs inside one "
                       "group box or vertically")
                if e.get("dashed"):
                    self.notes.append("label dropped: " + why)
                else:
                    problems.append(why)
                continue
            placed[eid] = spot
            label_boxes.append(spot[3])
        if problems:
            raise LabelError(problems)

        for eid, e, d, exit_p, entry_p, kind, path in geom:
            style = base_edge + exit_p + entry_p
            if e.get("dashed"):
                style += "dashed=1;"
            if e.get("error"):
                style += "dashed=1;strokeColor=#DD344C;"
            val, geo_x = "", ""
            if eid in placed:
                lines, rel, place, _ = placed[eid]
                style += {"above": "align=center;verticalAlign=bottom;",
                          "below": "align=center;verticalAlign=top;",
                          "left": f"align=right;spacingRight={LABEL_SIDE_GAP};verticalAlign=middle;",
                          "right": f"align=left;spacingLeft={LABEL_SIDE_GAP};verticalAlign=middle;"}[place]
                val = f' value="{attr("<br>".join(lines))}"'
                if rel:
                    geo_x = f' x="{rel}"'
            # A bent edge leaves under the source label, i.e. from a point outside the shape; draw.io's router
            # then picks the first leg's direction itself and may go sideways along the label. Pin the corner.
            pts = ""
            if kind != "straight":
                corner = path[1]
                pts = f'<Array as="points"><mxPoint x="{corner[0]:g}" y="{corner[1]:g}"/></Array>'
            geo = f'<mxGeometry{geo_x} relative="1" as="geometry">{pts}</mxGeometry>' if pts else f'<mxGeometry{geo_x} relative="1" as="geometry"/>'
            self.cells.append(
                f'<mxCell id="{eid}"{val} style="{style}" edge="1" parent="1" source="{e["from"]}" target="{e["to"]}">'
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
            tag = "note" if n.startswith("label dropped") else "unresolved"
            print(f"  {tag}: {n}")
    if brief_path is None and "--no-brief" not in flags:
        candidate = spec_path.with_suffix(".brief.md")
        brief_path = candidate if candidate.exists() else None
    try:
        builder = Builder(spec, json.loads(INDEX.read_text()))
        xml = builder.build()
    except LabelError as exc:
        for p in exc.problems:
            print(f"ERROR label: {p}")
        print(f"NOT CLEAN: {len(exc.problems)} primary relationship text(s) have no room on their edge. The picture shows what "
              "flows on every primary edge — condense the What flows phrase in the brief (then re-run the scaffold) or move a "
              "node in the .layout.json; leaving a solid edge without its text is not an accepted trade-off")
        return 1
    except SpecError as exc:
        print(f"ERROR spec: {exc}")
        return 1
    for n in builder.notes:
        print(f"  note: {n}")
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
