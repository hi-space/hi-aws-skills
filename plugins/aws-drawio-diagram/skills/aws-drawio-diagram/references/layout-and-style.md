# Layout and style rules

Read this once per diagram; SKILL.md only keeps the procedure and the two icon patterns. The rules are
numeric on purpose: a diagram that follows them renders like an AWS reference architecture — compact, grouped by
role, every edge one straight segment or one bend, nothing overlapping. **`scripts/build_diagram.py` applies
§1, §2, §5 and §6 for you** from a grid spec (see its header); read those sections to plan the grid and to
understand what the builder did, and follow them literally only when writing XML by hand. The validator checks
what it can (`W4`–`W8`); the rest is the self-check at the end of this file. Two finished examples:
`docs/samples/agentic-rag-chat.*` and `docs/samples/order-pipeline.*` in the plugin root.

Origin: vidanov/aws-architecture-diagram-skill (MIT) for the icon patterns and edge conventions; the grid,
grouping and typography rules below replace its sparse 280 px layout.

## 1. Grid — all coordinates come from here

| Constant | Value | Notes |
|---|---|---|
| Icon | **78 × 78** | draw.io AWS4 palette default. Never scale icons; scale the canvas instead. |
| Column pitch | **240 px** | Distance between icon centers on the same lane (162 px clear between icons). |
| Lane pitch | **170 px** inside a group | 92 px clear between an icon's label and the icon below it. |
| Group-row gap | **+50 px** | Lanes in *different* group rows are 220 px apart (170 + 50) so group borders and labels fit. |
| Group width | **200 px per column**, 40 px gap | Group x = first column center − 100; width = 200 × columns + 40 × (columns − 1). |
| Group height | **60 px above** first icon, **46 px below** last icon | 60 = group title row + room for a top-placed node label. |
| Cloud padding | 40 px around the outermost groups | AWS Cloud x = first group x − 40; title row inside it. |
| Canvas | content + 40–80 px margin, white | Typical 4-column diagram: ~1320 × 1040. **Never** a fixed 2400 × 1400 page. |

Column *i* center `x = 140 + 240·i` (column 0 is the outside column for users/clients: `140, 380, 620, 860, …`).
Lane *j* center `y = 260 + 170·j`, plus 50 px for every group-row boundary above lane *j*. A group-row boundary
is a lane where one group ends and another begins (the builder derives it; by hand, add the 50 px yourself).
Icon top-left = center − 39.

Children of a group use coordinates **relative to the group**: `child.x = center.x − 39 − group.x`.

## 2. Groups — every icon belongs to one

An AWS diagram without role groups reads as a scatter of logos. Group first, then place.

- Decide the **role groups** before placing anything: Frontend, API & Auth, Agent runtime, Data, Ingestion,
  Observability, … 2–7 groups. Each holds 1–4 icons on adjacent grid cells; a single-icon group is fine
  ("Foundation model").
- Groups are **rectangles snapped to grid cells** (§1 formulas). Arrange them in **group rows**: row 1 across
  the top (lanes A–B), row 2 below (lanes C–D). Groups in the same row share their top edge unless one is
  intentionally shorter (then it hugs its content, top-aligned to its own first lane).
- **AWS Cloud** (badge group) contains the role groups; **Users / on-premise / SaaS** sit outside it, on the
  main lane, in column 0 shifted 60 px further out (`OUTSIDE_GAP`) so the first edge into the cloud has room for
  its text.
- Nesting deeper than *AWS Cloud → role group → icons* only when the request is about networking (then Region →
  VPC → AZ → subnet from the table below, same 200/40 arithmetic).
- Validator `W6`: a service icon whose parent is the canvas while an AWS Cloud group exists → put it in a group.
- **Orchestrators at overview level.** Step Functions, EventBridge rules, Batch: one icon stands for the
  workflow; its steps are listed in the brief's Flow. Draw the steps as icons only when they are ≤ 3 and fit the
  fan-out pattern (§5) in the next column, or on a detail page (§7). Never a dozen Lambdas for one state machine.
- **Empty cells cost.** A fan-out or a side label leaves one empty cell inside a group — acceptable. A group with
  more empty cells than icons, or an empty band across the top of the cloud, means the lane plan is wrong: move
  upper-lane items there (auth, static assets, memory) or fan out downward instead.

**Role group style** (no badge — this is the modern light card look):

```
rounded=0;whiteSpace=wrap;html=1;fillColor=#F7F8FA;strokeColor=#C9D1D9;strokeWidth=1;fontColor=#232F3E;fontFamily=Amazon Ember;fontSize=13;fontStyle=1;verticalAlign=top;align=left;spacingLeft=12;spacingTop=4;container=1;dropTarget=1;
```

**Badge groups** (AWS Cloud, Region, VPC, …). Always `fillColor=none;container=1;dropTarget=1;`. Names and
colors come from [`aws-icons-groups.md`](aws-icons-groups.md) (generated). The common ones:

| Boundary | style fragment |
|---|---|
| AWS Cloud | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_aws_cloud_alt;strokeColor=#232F3E;fontColor=#232F3E;fillColor=none;container=1;dropTarget=1;` |
| Region | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_region;strokeColor=#00A4A6;fontColor=#147EBA;dashed=1;fillColor=none;container=1;dropTarget=1;` |
| VPC | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc2;strokeColor=#8C4FFF;fontColor=#8C4FFF;fillColor=none;container=1;dropTarget=1;` |
| Availability Zone | `fillColor=none;strokeColor=#147EBA;dashed=1;verticalAlign=top;fontStyle=0;fontColor=#147EBA;container=1;dropTarget=1;` (no badge) |
| Private subnet | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;strokeColor=#00A4A6;fontColor=#147EBA;fillColor=none;container=1;dropTarget=1;` |
| Public subnet | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;strokeColor=#7AA116;fontColor=#248814;fillColor=none;container=1;dropTarget=1;` |
| Security group | `fillColor=none;strokeColor=#DD3522;verticalAlign=top;fontStyle=0;fontColor=#DD3522;container=1;dropTarget=1;` (no badge) |
| AWS Account | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_account;strokeColor=#CD2264;fontColor=#CD2264;fillColor=none;container=1;dropTarget=1;` |
| On-premise / corporate DC | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_corporate_data_center;strokeColor=#7D8998;fontColor=#5A6C86;fillColor=none;container=1;dropTarget=1;` |

Badge group prefix: `points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontFamily=Amazon Ember;fontSize=14;fontStyle=1;verticalAlign=top;align=left;spacingLeft=30;`

## 3. Typography

One family, four sizes. Put `fontFamily=Amazon Ember;` in **every** cell style (icons, groups, edges, text).
draw.io cannot embed fonts: the PNG uses whatever the exporting machine has installed, and the `.drawio`
uses the viewer's. Amazon Ember ships with the sibling plugin
(`plugins/aws-diagram-design/skills/aws-diagram-design/assets/fonts/ttf/`; copy to `~/.fonts` and run
`fc-cache -f`). Without it draw.io falls back to Helvetica/Arial; **Noto Sans** is the preferred fallback
where Ember is not allowed — then write `fontFamily=Noto Sans;` instead.

| Element | Size | Weight | Color |
|---|---|---|---|
| Diagram title | 20 | bold | `#232F3E` |
| Subtitle (author · date · version) | 12 | regular | `#5A6C86` |
| AWS Cloud / badge group label | 14 | bold | group color |
| Role group label | 13 | bold | `#232F3E` |
| Node label | 13 | bold | `#232F3E` |
| Edge label, legend | 11 | regular | `#232F3E` / `#5A6C86` |

Node labels: 1–3 words, sentence case, qualifier in parentheses (`S3 (static site)`, `Bedrock (Claude)`).
Node labels are bold (`fontSize=13;fontStyle=1`) so the service name reads as fast as the icon; group
titles share the size and weight, which keeps one visual level for "names" and one for the grey subtitle/legend.

## 4. Canvas, title, legend

```xml
<mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1320" pageHeight="1040" math="0" shadow="0">
```

First cells after the root: a **white** full-canvas background (prevents black PNGs), then the title, then a
legend when the diagram has more than one edge type.

```xml
<mxCell id="bg" value="" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=none;" vertex="1" parent="1">
  <mxGeometry x="0" y="0" width="1320" height="1040" as="geometry" />
</mxCell>
<mxCell id="title" value="&lt;font style=&quot;font-size:20px&quot;&gt;&lt;b&gt;Diagram Title&lt;/b&gt;&lt;/font&gt;&lt;br&gt;&lt;font color=&quot;#5A6C86&quot;&gt;Author · Date · Version&lt;/font&gt;" style="text;html=1;align=left;verticalAlign=top;whiteSpace=wrap;rounded=0;fontFamily=Amazon Ember;fontSize=12;fontColor=#232F3E;spacing=0;" vertex="1" parent="1">
  <mxGeometry x="40" y="32" width="700" height="60" as="geometry" />
</mxCell>
<mxCell id="lg1" value="" style="shape=line;strokeWidth=2;strokeColor=#232F3E;html=1;" vertex="1" parent="1"><mxGeometry x="1020" y="44" width="40" height="10" as="geometry" /></mxCell>
<mxCell id="lg1t" value="request / data flow" style="text;html=1;align=left;verticalAlign=middle;fontFamily=Amazon Ember;fontSize=11;fontColor=#5A6C86;" vertex="1" parent="1"><mxGeometry x="1068" y="38" width="160" height="22" as="geometry" /></mxCell>
<mxCell id="lg2" value="" style="shape=line;strokeWidth=2;strokeColor=#232F3E;dashed=1;html=1;" vertex="1" parent="1"><mxGeometry x="1020" y="68" width="40" height="10" as="geometry" /></mxCell>
<mxCell id="lg2t" value="async / auxiliary" style="text;html=1;align=left;verticalAlign=middle;fontFamily=Amazon Ember;fontSize=11;fontColor=#5A6C86;" vertex="1" parent="1"><mxGeometry x="1068" y="62" width="160" height="22" as="geometry" /></mxCell>
```

Legend lines are `shape=line` **vertices**, not edges (edges without source/target fail `E3`).

## 5. Edges — one straight segment each

Base style for every edge:

```
edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=2;strokeColor=#232F3E;fontFamily=Amazon Ember;fontSize=11;fontColor=#232F3E;labelBackgroundColor=#FFFFFF;endArrow=block;endFill=1;
```

then the ports for the direction, then `dashed=1;` for async/auxiliary, `dashed=1;strokeColor=#DD344C;` for
error paths.

| Direction | ports |
|---|---|
| → right | `exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;` |
| ← left | `exitX=0;exitY=0.5;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;` |
| ↑ up | `exitX=0.5;exitY=0;exitDx=0;exitDy=0;entryX=0.5;entryY=B;entryDx=0;entryDy=0;entryPerimeter=0;` |
| ↓ down | `exitX=0.5;exitY=B;exitDx=0;exitDy=0;exitPerimeter=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;` |

`B` is the **under-the-label** port: `(78 + 4 + 18 × lines) / 78` → `1.282` for a one-line label, `1.513` for two
lines. A vertical edge therefore starts or ends below the node's label instead of running through it; the
arrowhead of an edge arriving from below sits just under the text. `exitPerimeter=0` / `entryPerimeter=0` are
required, otherwise draw.io snaps the point back onto the icon.

- **Same column or same lane.** Connected icons share x (vertical edge) or y (horizontal edge) exactly. If a pair
  cannot, move a node into a free cell — or use the fan-out pattern below. Never an S-shaped edge.
- **The one allowed bend — an L in either orientation.** Two nodes that share neither column nor lane are
  joined by one L. *Vertical-first* (the fan-out pattern): leave S's top (`exitX=0.5;exitY=0;`) or bottom (`B`
  port), run along S's column to the target's lane, enter the target's left/right (`entryX=0|1;entryY=0.5;`);
  corner at (S.cx, T.cy). *Horizontal-first*: leave S's left/right, run along S's lane to the target's column,
  enter the target's top (`entryX=0.5;entryY=0;`) or bottom (`B` port); corner at (T.cx, S.cy). **Pin the
  corner** with a waypoint (`<Array as="points"><mxPoint x="…" y="…"/></Array>` inside the geometry): a port
  outside the shape lets draw.io's router pick the first leg's direction, and it will run sideways along the
  label. Both legs may be long, but **every cell they cross must be empty** (builder error naming the blockers,
  validator `W5`); the builder picks vertical-first when both are free (`"route": "h"` in the spec forces the
  other). Never an S: a path that needs two bends is `W4`.
- **A side holds one straight edge, or up to three bends side by side.** A straight edge owns its side. Bent
  edges that touch one side — leaving, arriving or both — are **separate lines**, never one shared trunk: each
  leaves from its own port, 20 px apart (`exitX` / `entryY` = 0.5 ± 0.256 k), so the reader follows one line from
  its source to its arrowhead. A shared trunk with several branches was tried (1.3–1.5, the "bus") and read
  badly: two branches turning left and right at the same lane looked like one line passing through, and a
  branch crossing another hub's trunk looked like it belonged to that hub. The spacing is a judged middle:
  14 px still read as one bundle, 26 px looked scattered. The builder orders the lines so siblings never cross:
  along the side, the edges turning to one direction take that half, the nearest turn outermost (its leg turns
  away before the longer trunks reach it). That is how a hub draws eight neighbours: **all four sides** — a
  straight edge or up to three bends per side, neighbours stacked in the columns beside it above and below,
  the hub's own column kept clear. `scripts/layout.py` does this placement for you (SKILL.md Phase 3): it pays
  a small cost for every extra line on a side and, when a side is full, routes a bend horizontally first
  (`"route": "h"` in the placed spec) so it leaves the hub's left or right instead. A straight edge next to
  bends on one side would run between the trunks through its own target's cell (builder error); a fourth bend
  on a side is a builder error too; two edges on one line is validator `W8`. Every edge carries
  `jumpStyle=arc;jumpSize=6;`: where a line does cross another, draw.io draws a small hop, so a crossing never
  reads as a junction.
- **Empty corridor.** No other icon on any leg of the edge; no two edges in the same corridor.
- Every edge has `source`, `target`, `<mxGeometry relative="1" as="geometry" />` and, as `value`, the brief's
  *What flows* phrase (see *Edge text* below). No `value` only for a `—` row.
- Edges may cross group borders (that is what groups are for); they must not run along one.
- Left-to-right for the request path: users left, models/data right. Auxiliary (logs, alarms) below.

**Edge text.** Every edge shows the brief's *What flows* phrase — what travels on that hop — so a reader follows
the picture without the guide, and the guide's steps quote the same words. The builder draws the phrase as an
html label (11 pt, 6.2 px per character + 16 px padding, 14 px per line), wrapped into at most **3 lines of
≤ 24 characters** and re-wrapped so the lines come out even (`Fetch dynamic` / `credentials (optional)`), and
places it on the **longest leg** of the edge that has a clear spot — a bent edge carries its text on one of its
legs, positioned along the polyline with the relative `mxGeometry x` (−1 source … 1 target, by length). On a
horizontal leg the text sits above the line (`align=center;verticalAlign=bottom;`) or, if that is taken, below it
(`verticalAlign=top;`); on a vertical leg left of it (`align=right;spacingRight=4;verticalAlign=middle;`) or
right of it (`align=left;spacingLeft=4;`). The builder slides it from the middle of the leg outwards in 1/20
steps until the box covers **no group or cloud border, no title row (top 28 px of a titled container), no icon or
node label, no other edge's text and no other edge's line**, and tries narrower wraps (24 → 18 → 14 → 10 → 8 → 6
characters per line) when the wide one has no room. The validator's `W7` checks exactly that on the file. Room
by situation (`chars_that_fit` in `build_diagram.py`):

| Leg | Characters per line | Room |
|---|---|---|
| Horizontal, inside one group box (or on an empty column) | **22–24** | 162 px clear between two icons on a lane; 201 px on the horizontal leg of a bend |
| Horizontal, the first hop into the cloud (users → first service) | **16** | users sit `OUTSIDE_GAP` = 60 px further from the cloud than the grid column, so the pocket outside the cloud border is 121 px |
| Horizontal, between two neighbouring group boxes | **6 characters** (per line, up to 3 lines) | two 61 px pockets either side of the 40 px gap — `HTTPS`, `invoke`, `put` / `order`, `start` / `saga`. The one tight spot: condense the phrase to short words here |
| Vertical (straight, or the trunk of a bend) | **12 characters** | hangs beside the line inside the 100 px to the box border; must stay below the target box's title row — a vertical hop between two group rows is a roomy place for text. Between two neighbouring trunks (20 px) there is no room, so the middle line of a fan-out carries its text on its horizontal leg |

- **Nothing is dropped silently.** A phrase with no clear spot on a **primary (solid) edge** stops the build
  (`ERROR label`, naming the characters per line the edge offers): condense it in the brief (`StartExecution` →
  `start saga`, `write curated records` → `write to lake`, `prompt / completion` → `LLM prompt`) or move a node in
  the `.layout.json` so the edge runs inside one box or vertically — never delete the text from the spec. On a
  dashed edge the same case is a `note: label dropped` and allowed; the guide still explains the hop.
- **Pinning by hand**: `"label_offset": -0.6` on an edge fixes the relative position (−1 source … 1 target, along
  the polyline); the builder then only picks the side. Use it after reading a `W7`, not instead of it.
- Hand-written XML: `value` with `<br>` between lines and `html=1`, one of the four alignment styles above, and
  the relative `x`. The validator measures the box from the longest line and the line count.

## 6. Node labels — always below the icon

Every node label sits under its icon, centred, 13 bold, with a background the colour of its container:

```
verticalLabelPosition=bottom;verticalAlign=top;align=center;labelBackgroundColor=#F7F8FA;   (inside a role group)
verticalLabelPosition=bottom;verticalAlign=top;align=center;labelBackgroundColor=#FFFFFF;   (outside the cloud)
```

No side labels, no top labels, no `label_pos` switches: the reader always finds the name in the same place.
Edges keep out of the text by construction — anything that leaves or enters the node's bottom uses the `B` port
(§5), which is under the label, so the line is continuous from the text down. The background colour is a
safety net, not a routing tool: if a line still disappears behind a label, the layout is wrong (fix the spec).

- **Length.** ≤ 22 characters on one line (~7 px per bold character; the column pitch is 240 px). Longer labels
  break into two lines at the space nearest the middle (`OpenSearch Serverless<br>(vector index)`); the builder
  does this. Never three lines — shorten instead.
- **Room below.** One line needs 22 px under the icon, two lines 40 px; the group keeps 46 px below the last
  icon and lanes are 170 px apart, so labels never touch the next lane or the group border.
- **Delete the base style's later `align=center;`** when writing XML by hand — a later key wins in draw.io and
  the text lands on the icon.

## 7. Several diagrams, not a smaller one

Above ~25 icons, or when the source has several deployable units (from-source-code.md § 1), produce **several
complete diagrams** — one output set each (`<unit>.json` → `.drawio` → `.png`), each following the same grid.
Never shrink the architecture into abstract boxes to fit one page. To ship them as one multi-page `.drawio`,
concatenate the `<diagram>` elements under a single `<mxfile>` (ids must stay unique across pages):

```xml
<mxfile host="app.diagrams.net">
  <diagram id="agent-platform" name="Agent Platform">…</diagram>
  <diagram id="llm-gateway" name="LLM Gateway">…</diagram>
</mxfile>
```

Resource-level detail (subnets, instances, individual tables) also goes on its own page, not into the
service-level one.

## 8. Audience mode

Ask "Technical audience or executive/non-technical?" when unclear.

- **Technical**: service names, protocols (HTTPS, gRPC), CIDRs, instance types.
- **Non-technical**: action labels ("Store data", "Notify"), hide implementation detail, number the flow with
  circled digits as edge labels: `value="①"` with `fontSize=14;fontStyle=1;labelBackgroundColor=#ffffff;`.
  Second flow uses ❶ ❷ ❸.

## 9. Companion guide

Next to `name.drawio`, write `name.guide.md` — the step-by-step companion the reader opens beside the picture.
Template and rules: [`architecture-guide.md`](architecture-guide.md). The brief stays the Drawer's contract;
the guide is where every relationship — labeled on the picture or not — is explained in sentences.

## 10. Writing the file

- No XML comments (`<!-- -->`) — draw.io's importer rejects them in some paths.
- Escape `&amp; &lt; &gt; &quot;` in values. Unique `id` per cell. Root cells `id="0"` and `id="1" parent="0"`.
- Large diagrams: write in chunks (header + left, middle, right, bottom + close) to stay within tool limits.
- Save as `<descriptive-name>.drawio`. Export via the draw.io CLI (see SKILL.md) as `name.drawio.png` so the
  PNG embeds the XML and stays editable.

## 11. Self-check (Drawer, before handing to the Reviewer)

For every node: which group? which column, which lane? label ≤ 22 characters or split in two? For
every edge: same column or lane, or a proper fan-out? corridor empty? label only in a free gap? For the canvas:
white background, title, legend if two edge types, no half-empty page, no empty band. Then run the validator
and **look at the PNG** — the Reviewer's checklist (`review-checklist.md`) is what you will be measured against.
