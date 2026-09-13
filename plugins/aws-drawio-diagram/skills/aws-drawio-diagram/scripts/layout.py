#!/usr/bin/env python3
"""Automatic grid placement for build_diagram.py specs.

Give it a spec whose nodes have `group` (or `outside`) and edges but no `col`/`lane`, and it assigns every node
a cell and every group a rectangle such that the builder's rules hold: every edge straight (same column or same
lane, empty corridor) or a single bend into the adjacent column (empty trunk in the source's column), a node
side holding one straight edge or a bus of same-direction bends, groups as non-overlapping rectangles, users and
external systems outside the cloud. Columns come from longest-path layering along the edges; lanes from a
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

HARD = 1000.0

# Longest edge label (characters) per straight-edge situation, derived from the builder's geometry (6.2 px per
# character + 16 px padding, 240 px column pitch, 78 px icon, 40 px gap between groups):
#   lane      162 px clear between two icons on one lane                                → 16 characters
#   border    a horizontal edge between adjacent groups (or users → first service) crosses a 40 px gap; the label
#             sits in one of the two 61 px pockets either side of it, and the builder slides it in 4 px steps,
#             so the box must leave a few px of slack                                   → 6 characters
#   vertical  the label hangs left of the line and must stay inside the 100 px to the group's left border → 12
# Bent edges carry no label at all (draw.io centres it on the corner). Keep in step with layout-and-style.md §5.
LABEL_MAX_LANE, LABEL_MAX_BORDER, LABEL_MAX_VERTICAL = 16, 6, 12


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
        # spine: greedy longest chain from the start on lane 0
        n, c = start, 0 if self.nodes[start].get("outside") else 1
        while True:
            put(n, c, 0)
            nxt = [v for v in out[n] if v not in col and not self.nodes[v].get("outside")]
            if not nxt:
                break
            m = max(nxt, key=depth)
            self.spine.add((n, m))
            n, c = m, c + 1
        # fan-outs: for each placed node (BFS order), stack its unplaced neighbours in the adjacent columns,
        # same-group neighbours together, alternating above/below, keeping the node's own column clear
        queue = [start] + [x for x in col if x != start]
        seen = set(queue)
        while queue:
            u = queue.pop(0)
            cu, lu = col[u], lane[u]
            pend = [v for v in out[u] if v not in col] + [v for v in inc[u] if v not in col]
            pend.sort(key=lambda v: (self.nodes[v].get("group") or "", v))
            side, k_up, k_dn = 1, 1, 1
            for v in pend:
                if v in col:
                    continue
                if self.nodes[v].get("outside"):
                    cv = 0 if v in inc[u] else self.max_col + 1
                    lv = lu
                    while not free(cv, lv):
                        lv += 1
                    put(v, cv, lv)
                    continue
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
                if not placed:                                       # park it right of everything
                    cv, lv = self.max_col + 1, 0
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
                cv, lv = self.max_col + 1, 0
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
        box_of: dict[str, int] = {}
        for i, (gid, c0, c1, l0, l1) in enumerate(boxes):
            for nid, d in self.nodes.items():
                if d.get("group") == gid and c0 <= col[nid] <= c1 and l0 <= lane[nid] <= l1:
                    box_of[nid] = i
        sides: dict[tuple[str, str], list[tuple[str, str]]] = defaultdict(list)   # (node, side) -> [(kind, role)]
        segs: list[tuple[str, float, float, float, str, str, str]] = []           # (orient, coord, lo, hi, leg, s, t)
        for e in self.edges:
            s, t = e["from"], e["to"]
            sc, sl, tc, tl = col[s], lane[s], col[t], lane[t]
            soft += abs(sc - tc) + abs(sl - tl)
            solid = not e.get("dashed")
            if (s, t) in self.spine and sl != tl:
                soft += 80.0                                        # the request path stays on one lane
            label = e.get("label")
            if label and (sc == tc or sl == tl):                    # straight edge: will the label fit this geometry?
                if sc == tc:
                    limit = LABEL_MAX_VERTICAL
                elif box_of.get(s) != box_of.get(t) and abs(sc - tc) == 1:
                    limit = LABEL_MAX_BORDER
                else:
                    limit = LABEL_MAX_LANE
                if len(label) > limit:
                    if solid and len(label) <= LABEL_MAX_LANE:
                        # it fits on a lane or a vertical edge somewhere — making that room is the planner's job,
                        # otherwise an unrelated change elsewhere would decide whether this label survives
                        hard += 1
                        notes.append(f"edge {s}→{t}: label '{label}' does not fit here (max {limit}) — needs a cell "
                                     "where the edge stays inside one group box or runs vertically")
                    else:
                        soft += 20.0 if solid else 4.0              # can fit nowhere: the builder's ERROR label says shorten
            if sc == tc:                                            # vertical straight
                soft += 1.0 if solid else 0.0
                segs.append(("v", sc, min(sl, tl), max(sl, tl), "only", s, t))
                step = 1 if tl > sl else -1
                for l in range(sl + step, tl, step):
                    if (sc, l) in cells:
                        hard += 1
                        notes.append(f"edge {s}→{t}: '{cells[(sc, l)]}' sits on the vertical corridor")
                sides[(s, "B" if step > 0 else "T")].append(("straight", "out"))
                sides[(t, "T" if step > 0 else "B")].append(("straight", "in"))
            elif sl == tl:                                          # horizontal straight
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
                soft += (3.0 if solid else 0.0) + (8.0 if e.get("label") else 0.0)   # a bend drops its label
                step = 1 if tl > sl else -1
                cstep = 1 if tc > sc else -1
                v_cells = [(sc, l) for l in range(sl + step, tl + step, step)] + [(c, tl) for c in range(sc + cstep, tc, cstep)]
                h_cells = [(c, sl) for c in range(sc + cstep, tc + cstep, cstep)] + [(tc, l) for l in range(sl + step, tl, step)]
                v_block = [cells[c] for c in v_cells if c in cells]
                h_block = [cells[c] for c in h_cells if c in cells]
                if not v_block:
                    sides[(s, "B" if step > 0 else "T")].append(("bend", "out"))
                    sides[(t, "L" if cstep > 0 else "R")].append(("bend", "in"))
                    segs.append(("v", sc, min(sl, tl), max(sl, tl), "first", s, t))
                    segs.append(("h", tl, min(sc, tc), max(sc, tc), "last", s, t))
                elif not h_block:
                    sides[(s, "R" if cstep > 0 else "L")].append(("bend", "out"))
                    sides[(t, "T" if step > 0 else "B")].append(("bend", "in"))
                    segs.append(("h", sl, min(sc, tc), max(sc, tc), "first", s, t))
                    segs.append(("v", tc, min(sl, tl), max(sl, tl), "last", s, t))
                    soft += 1.0
                else:
                    hard += 1
                    notes.append(f"edge {s}→{t}: both L routes are blocked ('{v_block[0]}' / '{h_block[0]}')")
                soft += 2.0 * (abs(tc - sc) - 1)                     # long legs are allowed, short ones look better
        for i, a in enumerate(segs):                               # W8: collinear overlapping legs of different edges
            for b in segs[i + 1:]:
                if a[0] != b[0] or a[1] != b[1] or (a[5], a[6]) == (b[5], b[6]):
                    continue
                if min(a[3], b[3]) - max(a[2], b[2]) <= 0:
                    continue
                bus = (a[4] == b[4] == "first" and a[5] == b[5]) or (a[4] == b[4] == "last" and a[6] == b[6])
                if not bus:
                    hard += 1
                    notes.append(f"edges {a[5]}→{a[6]} and {b[5]}→{b[6]} run on top of each other")
        for (nid, side), uses in sides.items():
            kinds = {k for k, _ in uses}
            roles = {r for _, r in uses}
            if len(uses) > 1 and ("straight" in kinds or len(roles) > 1):
                hard += 1
                notes.append(f"node '{nid}': {len(uses)} edges on its {side} side that cannot share it")
        # groups are drawn as one or more rectangles that hold only their own members (see boxes());
        # fewer rectangles per group is better
        for gid in self.groups:
            n_boxes = sum(1 for b in boxes if b[0] == gid)
            soft += 12.0 * max(0, n_boxes - 1)
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

    def boxes(self, col, lane) -> list[tuple[str, int, int, int, int]]:
        """(group, c0, c1, l0, l1) rectangles: per group, per column, maximal runs of lanes whose cells are
        members or empty; runs in neighbouring columns with identical lane ranges merge into one rectangle."""
        owner = {(col[n], lane[n]): d.get("group") for n, d in self.nodes.items() if d.get("group")}
        occupied = {(col[n], lane[n]) for n in self.nodes}
        out = []
        for gid in self.groups:
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

    # ---- output --------------------------------------------------------------------------------------
    def apply(self) -> dict:
        spec = json.loads(json.dumps(self.spec))
        for n in spec["nodes"]:
            n["col"], n["lane"] = self.col[n["id"]], self.lane[n["id"]]
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
        # labels are judged against the *drawn* boxes: one logical group may have become two boxes with a border
        box_of = {n["id"]: n.get("group") for n in spec["nodes"]}
        self.dropped_labels, self.too_long_primary = [], []
        for e in spec.get("edges", []):
            label = e.get("label")
            if label:
                problem = self.label_problem(e["from"], e["to"], label, box_of)
                if problem:
                    e.pop("label")
                    text = f"{e['from']} → {e['to']} ('{label}'): {problem}"
                    self.dropped_labels.append(text)
                    # a primary (solid) relationship keeps its label or says "—" explicitly; the builder refuses the rest
                    if "too long" in problem and not e.get("dashed"):
                        self.too_long_primary.append(text)
        spec.pop("layout", None)
        return spec

    def label_problem(self, s: str, t: str, label: str, box_of: dict[str, str | None]) -> str | None:
        """Why `label` cannot stay on the placed edge s → t, or None when it fits (LABEL_MAX_* above)."""
        if self.col[s] != self.col[t] and self.lane[s] != self.lane[t]:
            return "bent edge — name the target instead; the guide carries the meaning"
        if self.col[s] == self.col[t]:
            limit, where = LABEL_MAX_VERTICAL, "a vertical edge"
        elif box_of[s] != box_of[t] and abs(self.col[s] - self.col[t]) == 1:
            limit, where = LABEL_MAX_BORDER, "an edge between adjacent groups"
        else:
            limit, where = LABEL_MAX_LANE, "an edge on one lane"
        if len(label) > limit:
            return (f"{len(label)} characters is too long for {where} (max {limit}) — shorten the Label in the brief, "
                    "or write — when the pair explains itself")
        return None


def needs_layout(spec: dict) -> bool:
    return spec.get("layout") == "auto" or any("col" not in n or "lane" not in n for n in spec.get("nodes", []))


def plan(spec: dict, seed: int = 7, steps: int = 9000) -> tuple[dict, list[str]]:
    """Return (placed spec, notes: remaining hard violations plus 'label dropped …' lines)."""
    best_spec, best_notes, best_cost = None, None, None
    for s in range(seed, seed + 2):                      # two restarts; keep the best
        p = Placement(spec, seed=s)
        p.descent()
        p.solve(steps)
        p.descent()
        c, notes = p.cost()
        if best_cost is None or c < best_cost:
            best_spec, best_cost = p.apply(), c
            best_notes = list(notes) + [("label too long: " if d in p.too_long_primary else "label dropped: ") + d
                                        for d in p.dropped_labels]
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
    hard = [n for n in notes if not n.startswith("label dropped")]          # "label too long" is hard too
    for n in notes:
        tag = "note" if n.startswith("label dropped") else "ERROR label" if n.startswith("label too long") else "unresolved"
        print(f"  {tag}: {n}")
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
