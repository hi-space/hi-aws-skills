#!/usr/bin/env python3
"""Automatic grid placement for build_diagram.py specs.

Give it a spec whose nodes have `group` (or `outside`) and edges but no `col`/`lane`, and it assigns every node
a cell and every group a rectangle such that the builder's rules hold: every edge straight (same column or same
lane, empty corridor) or a single bend into the adjacent column (empty trunk in the source's column), a node
side holding one straight edge or up to MAX_PER_SIDE bends drawn side by side, groups as non-overlapping
rectangles, users and external systems outside the cloud. Columns come from longest-path layering along the edges; lanes from a
simulated-annealing search over the builder's own constraints.

    python3 layout.py logical.json placed.json        # standalone
    build_diagram.py runs it automatically when a node has no col/lane and writes <spec>.layout.json

The search is deterministic (fixed seed). When it cannot reach zero hard violations it still writes the best
placement and lists what is left — usually the sign that the diagram wants splitting by request path.
"""
from __future__ import annotations

import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_diagram import (BOUNDARY_INSET, CLOUD_PAD, COL0, COL_PITCH, GROUP_HALF_W, ICON, MAX_PER_SIDE,  # noqa: E402
                           OUTSIDE_GAP, chars_that_fit, label_lines)

HARD = 1000.0
# A service boundary (nodes sharing `boundary` inside one group — AgentCore Runtime + Memory, Glue crawler + catalog) is
# drawn by the builder only when its members form a clean rectangle inside one group box. The planner prefers that
# with a soft cost, never a hard one: keeping two members together typically costs two bends instead of two straight
# edges (2 × 3 − 2 × 1) plus a shared side (3) and a step of distance (1) — about 10 — so the price of a split boundary
# sits above that and a little above a split group (12). Nudged, not forced: when only a sprawl would join them, the
# search still prefers the compact picture and the builder prints a hint instead of a box.
BOUNDARY_SPLIT_COST = 14.0

# Edge text is the brief's *What flows* phrase; the builder wraps it (≤ 3 lines) and puts it on the longest leg
# of the edge that has a clear spot (build_diagram.py § edge text). The planner estimates that room the same way,
# so a labelled edge is placed where its text will fit:
#   horizontal leg  the pixels between the two icons (or a corner and an icon), cut by every group / cloud border
#                   it crosses — the widest stretch sets the characters per line: 162 px on one lane → 22, the
#                   61 px pocket beside a border → 6, the 121 px pocket outside the cloud → 16, the 201 px leg
#                   of a bend → 24 (the cap)
#   vertical leg    the text hangs beside the line, 96 px to the box border → 12 characters per line
# The estimate only steers the search (LABEL_ROOM_COST per primary edge whose text would not fit — less than a
# spine break, more than a bend, so the planner trades a little shape for a label but never sprawls for one); the
# builder measures exactly and refuses a primary edge whose text has no room (`ERROR label`). Keep in step with
# layout-and-style.md §5.
LABEL_VERTICAL_CHARS = 12
LABEL_ROOM_COST = 20.0


def layering(nodes: dict, edges: list) -> dict[str, int]:
    """Longest path from any source, ignoring back edges found by DFS so cycles do not matter."""
    succ = defaultdict(list)
    for e in edges:
        succ[e["from"]].append(e["to"])
    order, state = [], {}

    def dfs(u):
        state[u] = 1
        for v in succ[u]:
            if state.get(v) == 0 or v not in state:
                dfs(v)
        state[u] = 2
        order.append(u)

    for n in nodes:
        if n not in state:
            dfs(n)
    order.reverse()                                   # topological (back edges dropped)
    col = {n: 0 for n in nodes}
    for u in order:
        for v in succ[u]:
            if order.index(v) > order.index(u):       # forward edge only
                col[v] = max(col[v], col[u] + 1)
    inside = [n for n in nodes if not nodes[n].get("outside")]
    if inside:
        shift = 1 - min(col[n] for n in inside)       # first inside column is 1; column 0 is for outside sources
        for n in nodes:
            col[n] += shift
        for n in nodes:
            if nodes[n].get("outside") and col[n] < 1:
                col[n] = 0
    return col


class Placement:
    def __init__(self, spec: dict, seed: int = 7):
        self.spec = spec
        self.nodes = {n["id"]: n for n in spec["nodes"]}
        self.edges = spec.get("edges", [])
        self.groups = {g["id"]: g for g in spec.get("groups", [])}
        self.boundaries: dict[tuple[str, str], list[str]] = defaultdict(list)   # (group, boundary stencil) -> members
        for nid, n in self.nodes.items():
            if n.get("boundary") and n.get("group"):
                self.boundaries[(n["group"], n["boundary"])].append(nid)
        self.rng = random.Random(seed)
        self.layer = layering(self.nodes, self.edges)
        self.max_col = max(self.layer.values()) + 1
        self.col, self.lane = self._construct()
        self.lanes_n = max(6, max(self.lane.values()) + 2, len(self.nodes) // 3 + 2)

    # ---- constructive placement: spine + fan-outs stacked beside each hub ----------------------------
    def _construct(self) -> tuple[dict, dict]:
        out = defaultdict(list)
        inc = defaultdict(list)
        for e in self.edges:
            out[e["from"]].append(e["to"])
            inc[e["to"]].append(e["from"])
        # longest path to a sink: the spine follows the longest chain from the first outside source
        memo: dict[str, int] = {}

        def depth(u, seen=()):
            if u in memo:
                return memo[u]
            best = 0
            for v in out[u]:
                if v not in seen:
                    best = max(best, 1 + depth(v, seen + (u,)))
            memo[u] = best
            return best

        col, lane, occupied = {}, {}, {}

        def free(c, l):
            return (c, l) not in occupied

        def put(n, c, l):
            col[n], lane[n], occupied[(c, l)] = c, l, n

        self.spine: set[tuple[str, str]] = set()
        sources = [n for n in self.nodes if not inc[n]]
        start = max(sources or list(self.nodes), key=lambda n: (self.nodes[n].get("outside", False), depth(n)))
        inside = lambda v: not self.nodes[v].get("outside")
        # spine: greedy longest chain from the start on lane 0. A spine node with other neighbours gets a spare
        # column to its right for them, so the next spine node's own column stays clear for its trunks
        n, c = start, 0 if self.nodes[start].get("outside") else 1
        while True:
            put(n, c, 0)
            nxt = [v for v in out[n] if v not in col and inside(v)]
            if not nxt:
                break
            m = max(nxt, key=depth)
            self.spine.add((n, m))
            stacked = [v for v in out[n] + inc[n] if v not in col and v != m and inside(v)]
            n, c = m, c + (2 if stacked else 1)
        park_col, out_col = c + 1, c + 2                    # inside nodes with no cell beside their hub; outside sinks
        # fan-outs: for each placed node (BFS order), stack its unplaced inside neighbours in the next column,
        # same-group neighbours together, alternating above/below, keeping the node's own column clear; then its
        # outside sinks in the outside column, on the nearest lane the edge can actually reach
        queue = [start] + [x for x in col if x != start]
        seen = set(queue)
        while queue:
            u = queue.pop(0)
            cu, lu = col[u], lane[u]
            pend = [v for v in out[u] if v not in col] + [v for v in inc[u] if v not in col]
            pend.sort(key=lambda v: (not inside(v), self.nodes[v].get("group") or "", self.nodes[v].get("boundary") or "", v))
            side, k_up, k_dn = 1, 1, 1
            prev_boundary = None
            for v in pend:
                if v in col:
                    continue
                # members of one service boundary stack on the same side, consecutively, so they start adjacent
                # (the search only has to keep them there; see BOUNDARY_SPLIT_COST)
                this_boundary = (self.nodes[v].get("group"), self.nodes[v].get("boundary")) if self.nodes[v].get("boundary") else None
                if this_boundary is not None and this_boundary == prev_boundary:
                    side = -side                                          # undo the flip the previous member caused
                prev_boundary = this_boundary
                if not inside(v):
                    cv = 0 if v in inc[u] else out_col
                    between = range(min(cu, cv) + 1, max(cu, cv))

                    def reachable(l: int) -> bool:
                        """Straight on the hub's lane, or one bend whose two legs cross no placed node."""
                        if not free(cv, l):
                            return False
                        if l == lu:
                            return all(free(x, lu) for x in between)
                        rows = range(min(lu, l) + 1, max(lu, l))
                        v_ok = all(free(x, l) for x in between) and all(free(cu, k) for k in rows)
                        h_ok = all(free(x, lu) for x in list(between) + [cv]) and all(free(cv, k) for k in rows)
                        return v_ok or h_ok

                    lv = next((l for l in [lu] + [lu + d * k for k in range(1, 12) for d in (1, -1)] if reachable(l)), None)
                    if lv is None:
                        lv = lu
                        while not free(cv, lv):
                            lv += 1
                    put(v, cv, lv)
                else:
                    placed = False
                    for _ in range(40):
                        if side > 0:
                            cv, lv, k_dn = cu + 1, lu + k_dn, k_dn + 1
                        else:
                            cv, lv, k_up = cu + 1, lu - k_up, k_up + 1
                        side = -side
                        trunk_clear = all(free(cu, l) for l in range(min(lu, lv), max(lu, lv) + 1) if l != lu)
                        if cv >= 1 and free(cv, lv) and trunk_clear:
                            put(v, cv, lv)
                            placed = True
                            break
                    if not placed:                                       # park it right of everything inside
                        cv, lv = park_col, 0
                        while not free(cv, lv):
                            lv += 1
                        put(v, cv, lv)
                if v not in seen:
                    seen.add(v)
                    queue.append(v)
            for v in out[u] + inc[u]:
                if v not in seen:
                    seen.add(v)
                    queue.append(v)
        for v in self.nodes:                                          # isolated nodes
            if v not in col:
                cv, lv = park_col, 0
                while not free(cv, lv):
                    lv += 1
                put(v, cv, lv)
        lo = min(lane.values())
        lane = {k: v - lo for k, v in lane.items()}
        self.max_col = max(self.max_col, max(col.values()))
        return col, lane

    # ---- constraint evaluation (mirrors build_diagram rules) ---------------------------------------
    def cost(self, col=None, lane=None) -> tuple[float, list[str]]:
        col = col or self.col
        lane = lane or self.lane
        cells = {}
        self_eval = col is self.col and lane is self.lane
        hard, soft, notes = 0, 0.0, []
        for nid in self.nodes:
            c = (col[nid], lane[nid])
            if c in cells:
                hard += 1
                notes.append(f"'{cells[c]}' and '{nid}' share cell {c}")
            cells[c] = nid
        # the rectangles the groups will be drawn as (see boxes()); a label's room depends on them, not on the
        # logical group — one group split into two boxes puts a border between two of its own members
        boxes = self.boxes(col, lane)
        inside_cols = [col[n] for n, d in self.nodes.items() if not d.get("outside")]
        # service boundaries: members together in a clean rectangle inside one group box (see module comment)
        bcuts: list[tuple[int, int, float, float]] = []                 # (l0, l1, x_left, x_right) of drawn boundaries
        for (gid, _), members in self.boundaries.items():
            if len(members) < 2:
                continue
            c0, c1 = min(col[m] for m in members), max(col[m] for m in members)
            l0, l1 = min(lane[m] for m in members), max(lane[m] for m in members)
            inside_box = {cells.get((c, l)) for c in range(c0, c1 + 1) for l in range(l0, l1 + 1)} - {None}
            own_boxes = {next((i for i, b in enumerate(boxes) if b[0] == gid and b[1] <= col[m] <= b[2] and b[3] <= lane[m] <= b[4]), None)
                         for m in members}
            if inside_box - set(members) or len(own_boxes) > 1:
                soft += BOUNDARY_SPLIT_COST
            else:
                soft += 1.0 * ((c1 - c0 + 1) * (l1 - l0 + 1) - len(members))
                bcuts.append((l0, l1, COL0 + COL_PITCH * c0 - GROUP_HALF_W + BOUNDARY_INSET,
                              COL0 + COL_PITCH * c1 + GROUP_HALF_W - BOUNDARY_INSET))

        def x_of(nid: str) -> float:                                # icon centre x as the builder draws it
            x = COL0 + COL_PITCH * col[nid]
            if self.nodes[nid].get("outside") and inside_cols:
                x += -OUTSIDE_GAP if col[nid] < min(inside_cols) else OUTSIDE_GAP if col[nid] > max(inside_cols) else 0
            return x

        cloud_x = ()
        if boxes:
            cloud_x = (COL0 + COL_PITCH * min(b[1] for b in boxes) - GROUP_HALF_W - CLOUD_PAD,
                       COL0 + COL_PITCH * max(b[2] for b in boxes) + GROUP_HALF_W + CLOUD_PAD)

        def h_room(lane_: int, xa: float, xb: float) -> int:
            """Characters per line on a horizontal leg from xa to xb on `lane_`: its widest stretch between borders."""
            cuts = list(cloud_x)
            for _, c0, c1, l0, l1 in boxes:
                if l0 <= lane_ <= l1:
                    cuts += [COL0 + COL_PITCH * c0 - GROUP_HALF_W, COL0 + COL_PITCH * c1 + GROUP_HALF_W]
            for l0, l1, xl, xr in bcuts:                              # a boundary border cuts the room like a group border
                if l0 <= lane_ <= l1:
                    cuts += [xl, xr]
            xs = [xa] + sorted(x for x in cuts if xa < x < xb) + [xb]
            return chars_that_fit(max(b - a for a, b in zip(xs, xs[1:])))

        sides: dict[tuple[str, str], list[tuple[str, str]]] = defaultdict(list)   # (node, side) -> [(kind, role)]
        segs: list[tuple[str, float, float, float, str, str, str]] = []           # (orient, coord, lo, hi, leg, s, t)
        # bends are routed after every straight edge is known: a bend may go vertical-first (corner on the source's
        # column) or horizontal-first (corner on the target's column), and the choice decides which sides of the
        # two nodes it uses — see route_bends()
        pending: list[tuple[int, dict[str, dict], str | None]] = []               # (edge index, options, forced route)
        label_checks: list[tuple[dict, list[int]]] = []                           # (edge, characters per line per leg)
        for ei, e in enumerate(self.edges):
            s, t = e["from"], e["to"]
            sc, sl, tc, tl = col[s], lane[s], col[t], lane[t]
            soft += abs(sc - tc) + abs(sl - tl)
            solid = not e.get("dashed")
            if (s, t) in self.spine and sl != tl:
                soft += 80.0                                        # the request path stays on one lane
            xs_, xt_ = x_of(s), x_of(t)
            rooms: list[int] = []                                   # characters per line, per leg of the drawn edge
            if sc == tc:                                            # vertical straight
                soft += 1.0 if solid else 0.0
                rooms = [LABEL_VERTICAL_CHARS]
                segs.append(("v", sc, min(sl, tl), max(sl, tl), "only", s, t))
                step = 1 if tl > sl else -1
                for l in range(sl + step, tl, step):
                    if (sc, l) in cells:
                        hard += 1
                        notes.append(f"edge {s}→{t}: '{cells[(sc, l)]}' sits on the vertical corridor")
                sides[(s, "B" if step > 0 else "T")].append(("straight", "out"))
                sides[(t, "T" if step > 0 else "B")].append(("straight", "in"))
            elif sl == tl:                                          # horizontal straight
                rooms = [h_room(sl, min(xs_, xt_) + ICON / 2, max(xs_, xt_) - ICON / 2)]
                segs.append(("h", sl, min(sc, tc), max(sc, tc), "only", s, t))
                step = 1 if tc > sc else -1
                if (s, t) in self.spine and step < 0:
                    soft += 80.0
                for c in range(sc + step, tc, step):
                    if (c, sl) in cells:
                        hard += 1
                        notes.append(f"edge {s}→{t}: '{cells[(c, sl)]}' sits on the horizontal corridor")
                sides[(s, "R" if step > 0 else "L")].append(("straight", "out"))
                sides[(t, "L" if step > 0 else "R")].append(("straight", "in"))
            else:                                                   # one bend, either orientation
                soft += 3.0 if solid else 0.0
                step = 1 if tl > sl else -1
                cstep = 1 if tc > sc else -1
                v_cells = [(sc, l) for l in range(sl + step, tl + step, step)] + [(c, tl) for c in range(sc + cstep, tc, cstep)]
                h_cells = [(c, sl) for c in range(sc + cstep, tc + cstep, cstep)] + [(tc, l) for l in range(sl + step, tl, step)]
                v_block = [cells[c] for c in v_cells if c in cells]
                h_block = [cells[c] for c in h_cells if c in cells]
                opts: dict[str, dict] = {}
                if not v_block:                                     # corner on the source's column, target's lane
                    t_edge = xt_ - ICON / 2 if xt_ > xs_ else xt_ + ICON / 2
                    opts["v"] = {"sides": [((s, "B" if step > 0 else "T"), ("bend", "out")),
                                           ((t, "L" if cstep > 0 else "R"), ("bend", "in"))],
                                 "segs": [("v", sc, min(sl, tl), max(sl, tl), "first", s, t),
                                          ("h", tl, min(sc, tc), max(sc, tc), "last", s, t)],
                                 "rooms": [LABEL_VERTICAL_CHARS, h_room(tl, min(xs_, t_edge), max(xs_, t_edge))], "soft": 0.0}
                if not h_block:                                     # corner on the source's lane, target's column
                    s_edge = xs_ + ICON / 2 if xt_ > xs_ else xs_ - ICON / 2
                    opts["h"] = {"sides": [((s, "R" if cstep > 0 else "L"), ("bend", "out")),
                                           ((t, "T" if step > 0 else "B"), ("bend", "in"))],
                                 "segs": [("h", sl, min(sc, tc), max(sc, tc), "first", s, t),
                                          ("v", tc, min(sl, tl), max(sl, tl), "last", s, t)],
                                 "rooms": [h_room(sl, min(s_edge, xt_), max(s_edge, xt_)), LABEL_VERTICAL_CHARS], "soft": 1.0}
                if opts:
                    pending.append((ei, opts, e.get("route")))
                else:
                    hard += 1
                    notes.append(f"edge {s}→{t}: both L routes are blocked ('{v_block[0]}' / '{h_block[0]}')")
                soft += 2.0 * (abs(tc - sc) - 1)                     # long legs are allowed, short ones look better
            if rooms:
                label_checks.append((e, rooms))
        routes = self.route_bends(pending, sides)
        for ei, opts, _ in pending:
            opt = opts[routes[ei]]
            for key, use in opt["sides"]:
                sides[key].append(use)
            segs.extend(opt["segs"])
            soft += opt["soft"]
            label_checks.append((self.edges[ei], opt["rooms"]))
        if self_eval:
            self.routes = routes                                    # apply() writes the horizontal-first choices into the spec
        for e, rooms in label_checks:
            label = e.get("label")
            if label and not any(label_lines(label, r) for r in rooms):
                # the text has no room on this edge as placed: a strong nudge, not a hard rule — a compact picture
                # beats a spare column, and the builder refuses a primary edge whose text still has no room
                # (`ERROR label`), so the Drawer condenses the phrase; a dashed edge just loses its text (note)
                soft += LABEL_ROOM_COST if not e.get("dashed") else LABEL_ROOM_COST / 5
        def anchor(seg):
            """The node whose side a bend's leg touches (first leg: its source; last leg: its target). Legs of
            different edges that touch the same node in the same corridor are drawn side by side by the builder
            (TRUNK_GAP px apart), so they do not overlap; any other collinear pair renders as one line (W8)."""
            leg, s_, t_ = seg[4], seg[5], seg[6]
            return s_ if leg == "first" else t_ if leg == "last" else None

        for i, a in enumerate(segs):                               # W8: collinear overlapping legs of different edges
            for b in segs[i + 1:]:
                if a[0] != b[0] or a[1] != b[1] or (a[5], a[6]) == (b[5], b[6]):
                    continue
                if min(a[3], b[3]) - max(a[2], b[2]) <= 0:
                    continue
                if anchor(a) is None or anchor(a) != anchor(b):
                    hard += 1
                    notes.append(f"edges {a[5]}→{a[6]} and {b[5]}→{b[6]} run on top of each other")
        for (nid, side), uses in sides.items():
            kinds = {k for k, _ in uses}
            if len(uses) > 1 and "straight" in kinds:
                hard += 1
                notes.append(f"node '{nid}': {len(uses)} edges on its {side} side that cannot share it (one is straight)")
            elif len(uses) > MAX_PER_SIDE:
                hard += 1
                notes.append(f"node '{nid}': {len(uses)} bent edges on its {side} side — at most {MAX_PER_SIDE} fit side by side; "
                             "move some neighbours to the opposite side")
            elif len(uses) > 1:
                soft += 3.0 * (len(uses) - 1)                       # spread a hub's lines over its sides: two lines side by side read
                                                                    # more clearly than three, so pay a little for every extra one
        # groups are drawn as one or more rectangles that hold only their own members (see boxes());
        # fewer rectangles per group is better
        for gid in self.groups:
            n_boxes = sum(1 for b in boxes if b[0] == gid)
            soft += 12.0 * max(0, n_boxes - 1)
            members = sum(1 for d in self.nodes.values() if d.get("group") == gid)
            area = sum((c1 - c0 + 1) * (l1 - l0 + 1) for g, c0, c1, l0, l1 in boxes if g == gid)
            soft += 2.0 * max(0, area - members)                     # an empty cell inside a card is cheaper than a split card
        gcols = [c for _, c0, c1, _, _ in boxes for c in (c0, c1)]
        if gcols:
            gc0, gc1 = min(gcols), max(gcols)
            for nid, d in self.nodes.items():
                if d.get("outside") and gc0 <= col[nid] <= gc1:
                    hard += 1
                    notes.append(f"outside node '{nid}' would sit inside the cloud (col {col[nid]})")
        soft += 4.0 * (max(lane.values()) - min(lane.values()))
        per_col = defaultdict(int)
        for nid in self.nodes:
            per_col[col[nid]] += 1
        soft += sum(2.0 * (k - 4) for k in per_col.values() if k > 4)   # spread: more than four icons in a column is a wall
        return HARD * hard + soft, notes

    def route_bends(self, pending, sides) -> dict[int, str]:
        """Pick 'v' (vertical-first) or 'h' (horizontal-first) for every bend. Vertical-first is the default (the
        builder's too); a bend moves to the other orientation when a side it would use is full — MAX_PER_SIDE bends
        already, or a straight edge that owns the side — and the other orientation's two sides have room. That is
        what lets a hub use its left and right for bends once top and bottom hold three lines each. A `route` given
        in the spec is kept when that route exists."""
        chosen = {ei: (forced if forced in opts else "v" if "v" in opts else "h") for ei, opts, forced in pending}
        load: dict[tuple[str, str], int] = defaultdict(int)
        owned = {key for key, uses in sides.items() if any(kind == "straight" for kind, _ in uses)}
        for ei, opts, _ in pending:
            for key, _ in opts[chosen[ei]]["sides"]:
                load[key] += 1
        changed = True
        while changed:
            changed = False
            for ei, opts, forced in pending:
                if forced in opts or len(opts) < 2:
                    continue
                cur, alt = chosen[ei], ("h" if chosen[ei] == "v" else "v")
                cur_keys = [key for key, _ in opts[cur]["sides"]]
                alt_keys = [key for key, _ in opts[alt]["sides"]]
                if not any(load[k] > MAX_PER_SIDE or k in owned for k in cur_keys):
                    continue
                if all(load[k] < MAX_PER_SIDE and k not in owned for k in alt_keys):
                    for k in cur_keys:
                        load[k] -= 1
                    for k in alt_keys:
                        load[k] += 1
                    chosen[ei], changed = alt, True
        return chosen

    def boxes(self, col, lane) -> list[tuple[str, int, int, int, int]]:
        """(group, c0, c1, l0, l1) rectangles per group. First choice: the members' bounding box as ONE rectangle,
        empty cells included, when no other node sits inside it and no other group's box would overlap it (an
        L-shaped group of three is one card with an empty corner, not two cards with a 40 px gap between them —
        the gap costs every edge that crosses it its text room). Otherwise: per column, maximal runs of lanes
        whose cells are members or empty; runs in neighbouring columns with identical lane ranges merge."""
        owner = {(col[n], lane[n]): d.get("group") for n, d in self.nodes.items() if d.get("group")}
        occupied = {(col[n], lane[n]) for n in self.nodes}
        bbox: dict[str, tuple[int, int, int, int]] = {}
        for gid in self.groups:
            cells = [(col[n], lane[n]) for n, d in self.nodes.items() if d.get("group") == gid]
            if not cells:
                continue
            c0, c1 = min(c for c, _ in cells), max(c for c, _ in cells)
            l0, l1 = min(l for _, l in cells), max(l for _, l in cells)
            if all(owner.get((c, l), gid) == gid and ((c, l) not in occupied or (c, l) in cells)
                   for c in range(c0, c1 + 1) for l in range(l0, l1 + 1)):
                bbox[gid] = (c0, c1, l0, l1)
        whole = set(bbox)
        for a in list(bbox):
            for b in list(bbox):
                if a < b and bbox[a][0] <= bbox[b][1] and bbox[b][0] <= bbox[a][1] and bbox[a][2] <= bbox[b][3] and bbox[b][2] <= bbox[a][3]:
                    whole.discard(a)
                    whole.discard(b)
        out = [(gid, *bbox[gid]) for gid in self.groups if gid in whole]
        for gid in self.groups:
            if gid in whole:
                continue
            cells = sorted((col[n], lane[n]) for n, d in self.nodes.items() if d.get("group") == gid)
            if not cells:
                continue
            runs = []
            by_col = defaultdict(list)
            for c, l in cells:
                by_col[c].append(l)
            for c, ls in by_col.items():
                ls.sort()
                start = prev = ls[0]
                for l in ls[1:]:
                    gap_ok = all((c, k) not in occupied for k in range(prev + 1, l))
                    if gap_ok:
                        prev = l
                    else:
                        runs.append((c, c, start, prev))
                        start = prev = l
                runs.append((c, c, start, prev))
            merged = True
            while merged:
                merged = False
                for i in range(len(runs)):
                    for j in range(i + 1, len(runs)):
                        a, b = runs[i], runs[j]
                        if a[2] == b[2] and a[3] == b[3] and (a[1] + 1 == b[0] or b[1] + 1 == a[0]):
                            runs[i] = (min(a[0], b[0]), max(a[1], b[1]), a[2], a[3])
                            runs.pop(j)
                            merged = True
                            break
                    if merged:
                        break
            out.extend((gid, *r) for r in runs)
        return out

    # ---- search ------------------------------------------------------------------------------------
    def solve(self, steps: int = 20000) -> None:
        cur, _ = self.cost()
        best, best_lane, best_col = cur, dict(self.lane), dict(self.col)
        T0 = 60.0
        ids = list(self.nodes)
        for i in range(steps):
            T = T0 * (1 - i / steps) ** 2 + 0.5
            lane, col = dict(self.lane), dict(self.col)
            nid = self.rng.choice(ids)
            r = self.rng.random()
            if r < 0.6:                                             # move to a random cell next to a neighbour
                col[nid] = self.rng.choice(self.candidate_cols(nid, col))
                lane[nid] = self.rng.randrange(0, self.lanes_n)
            elif r < 0.9:                                           # swap two nodes
                other = self.rng.choice(ids)
                if bool(self.nodes[nid].get("outside")) == bool(self.nodes[other].get("outside")):
                    lane[nid], lane[other] = lane[other], lane[nid]
                    col[nid], col[other] = col[other], col[nid]
            else:                                                   # shift a whole group's lanes
                gid = self.nodes[nid].get("group")
                if gid:
                    d = self.rng.choice((-1, 1))
                    for m, dd in self.nodes.items():
                        if dd.get("group") == gid:
                            lane[m] = min(self.lanes_n - 1, max(0, lane[m] + d))
            lo = min(lane.values())
            if lo > 0:
                lane = {k: v - lo for k, v in lane.items()}
            new, _ = self.cost(col, lane)
            if new <= cur or self.rng.random() < math.exp((cur - new) / T):
                self.lane, self.col, cur = lane, col, new
                if new < best:
                    best, best_lane, best_col = new, dict(lane), dict(col)
        self.lane, self.col = best_lane, best_col

    def candidate_cols(self, nid: str, col: dict) -> list[int]:
        """Columns where nid could connect: its own, its layer, and every column adjacent to a neighbour's."""
        if self.nodes[nid].get("outside"):
            return [col[nid]]
        cands = {col[nid], self.layer[nid]}
        for e in self.edges:
            other = e["to"] if e["from"] == nid else e["from"] if e["to"] == nid else None
            if other:
                cands.update((col[other] - 1, col[other], col[other] + 1))
        return sorted(c for c in cands if 1 <= c <= self.max_col)

    def descent(self, passes: int = 10) -> None:
        """Steepest descent: move each node in turn to the best cell (any lane, its layer ±1 columns); stop when
        no single move improves the cost. Repairs what annealing left over and tightens the picture."""
        cur, _ = self.cost()
        ids = list(self.nodes)
        for _ in range(passes):
            improved = False
            self.rng.shuffle(ids)
            for nid in ids:
                outside = self.nodes[nid].get("outside")
                cols = self.candidate_cols(nid, self.col)
                best_move, best_cost = None, cur
                for c in cols:
                    for l in range(0, self.lanes_n):
                        if (c, l) == (self.col[nid], self.lane[nid]):
                            continue
                        col, lane = dict(self.col), dict(self.lane)
                        col[nid], lane[nid] = c, l
                        occupant = next((o for o in ids if o != nid and (col[o], lane[o]) == (c, l)), None)
                        if occupant is not None:
                            if bool(self.nodes[occupant].get("outside")) != bool(outside):
                                continue
                            col[occupant], lane[occupant] = self.col[nid], self.lane[nid]     # swap
                        new, _ = self.cost(col, lane)
                        if new < best_cost - 1e-9:
                            best_move, best_cost = (col, lane), new
                if best_move:
                    self.col, self.lane = best_move
                    cur, improved = best_cost, True
            lo = min(self.lane.values())
            if lo:
                self.lane = {k: v - lo for k, v in self.lane.items()}
            if not improved:
                break

    def compact_columns(self) -> None:
        """Close columns nobody uses: the constructive pass parks stragglers at `max_col + 1`, which can leave an
        empty 240 px band in the middle of the picture. Removing an empty column only shortens edges — corridors
        stay empty, sides keep their edges and their order — so it cannot add a hard violation."""
        used = sorted(set(self.col.values()))
        remap = {c: i for i, c in enumerate(used)}
        if used and used[0] == 0 and any(self.nodes[n].get("outside") for n in self.nodes if self.col[n] == 0):
            pass                                                     # column 0 stays the outside column
        elif used and not any(self.nodes[n].get("outside") and self.col[n] == used[0] for n in self.nodes):
            remap = {c: i + 1 for i, c in enumerate(used)}           # no outside source: inside starts at 1
        self.col = {n: remap[c] for n, c in self.col.items()}
        self.max_col = max(self.col.values())

    # ---- output --------------------------------------------------------------------------------------
    def apply(self) -> dict:
        spec = json.loads(json.dumps(self.spec))
        for n in spec["nodes"]:
            n["col"], n["lane"] = self.col[n["id"]], self.lane[n["id"]]
        self.cost()                                                 # routes for the final placement
        for ei, e in enumerate(spec["edges"]):
            if getattr(self, "routes", {}).get(ei) == "h" and "route" not in e:
                e["route"] = "h"                                    # the builder would pick vertical-first; this side is full
        groups_out, counter = [], defaultdict(int)
        for gid, c0, c1, l0, l1 in self.boxes(self.col, self.lane):
            counter[gid] += 1
            bid = gid if counter[gid] == 1 else f"{gid}_{counter[gid]}"
            groups_out.append({"id": bid, "label": self.groups[gid].get("label", gid),
                               "cols": list(range(c0, c1 + 1)), "lanes": list(range(l0, l1 + 1))})
            for n in spec["nodes"]:
                if n.get("group") == gid and c0 <= n["col"] <= c1 and l0 <= n["lane"] <= l1:
                    n["group"] = bid
        spec["groups"] = groups_out
        # every label stays in the placed spec: the builder measures the room exactly and decides (ERROR label on a
        # primary edge, `note: label dropped` on a dashed one)
        spec.pop("layout", None)
        return spec


def needs_layout(spec: dict) -> bool:
    return spec.get("layout") == "auto" or any("col" not in n or "lane" not in n for n in spec.get("nodes", []))


def plan(spec: dict, seed: int = 7, steps: int = 9000) -> tuple[dict, list[str]]:
    """Return (placed spec, notes: the hard violations that remain — an edge with no one-bend route, a primary
    edge whose text has no room, …)."""
    best_spec, best_notes, best_cost = None, None, None
    for s in range(seed, seed + 2):                      # two restarts; keep the best
        p = Placement(spec, seed=s)
        p.descent()
        p.solve(steps)
        p.descent()
        p.compact_columns()
        c, notes = p.cost()
        if best_cost is None or c < best_cost:
            best_spec, best_cost, best_notes = p.apply(), c, list(notes)
    return best_spec, best_notes


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        print(__doc__)
        return 2
    spec = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    placed, notes = plan(spec)
    Path(args[1]).write_text(json.dumps(placed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {args[1]}")
    for n in placed["nodes"]:
        print(f"  {n['id']:<24} col {n['col']:>2}  lane {n['lane']:>2}  {n.get('group') or 'outside'}")
    for n in notes:
        print(f"  unresolved: {n}")
    return 1 if notes else 0


if __name__ == "__main__":
    sys.exit(main())
