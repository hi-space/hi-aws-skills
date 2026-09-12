# Layout and style rules

Read this once per diagram; SKILL.md only keeps the procedure and the two icon patterns. The rules are
numeric on purpose: a diagram that follows them renders like an AWS reference architecture — compact, grouped by
role, every edge one straight segment or one bend, nothing overlapping. **`scripts/build_diagram.py` applies
§1, §2, §5 and §6 for you** from a grid spec (see its header); read those sections to plan the grid and to
understand what the builder did, and follow them literally only when writing XML by hand. The validator checks
what it can (`W4`–`W7`); the rest is the self-check at the end of this file. Two finished examples:
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
  main lane, 260 px left of the first column.
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
| Node label | 12 | regular | `#232F3E` |
| Edge label, legend | 11 | regular | `#232F3E` / `#5A6C86` |

Node labels: 1–3 words, sentence case, qualifier in parentheses (`S3 (static site)`, `Bedrock (Claude)`).
No `fontStyle=1` on node labels.

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
| ↑ up | `exitX=0.5;exitY=0;exitDx=0;exitDy=0;entryX=0.5;entryY=1;entryDx=0;entryDy=0;` |
| ↓ down | `exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;` |

- **Same column or same lane.** Connected icons share x (vertical edge) or y (horizontal edge) exactly. If a pair
  cannot, move a node into a free cell — or use the fan-out pattern below. Never an S-shaped edge.
- **Fan-out (the one allowed bend).** Source S on lane B fans out to targets in the **next column**: the target
  on S's own lane gets a straight horizontal edge; a target on the lane above gets `exitX=0.5;exitY=0;` (leave
  S's top) + `entryX=0;entryY=0.5;` (enter the target's left) — one bend at (S.x, target.y); a target on the lane
  below leaves S's bottom the same way. Each fan-out edge uses a different side of S, so no two edges share a
  segment. The cell directly above/below S must be empty (the vertical leg runs through it). Same ports mirrored
  for fan-in from the left. Validator: `W4` accepts an L whose ports match its geometry and rejects anything else.
- **Empty corridor.** No other icon on any leg of the edge; no two edges in the same corridor.
- Every edge has `source`, `target`, `<mxGeometry relative="1" as="geometry" />`. No `value` when unlabeled.
- Edges may cross group borders (that is what groups are for); they must not run along one.
- Left-to-right for the request path: users left, models/data right. Auxiliary (logs, alarms) below.

**Edge labels.** Most edges need none (Lambda → DynamoDB is self-explanatory). When one helps:

- Horizontal edge: `verticalAlign=bottom;` (label above the line). Vertical edge: `align=right;spacingRight=4;`
  (label left of the line).
- Only where the segment has ≥ 60 px of free space: the run from users into the cloud, a vertical edge crossing
  the gap between two group rows (`retrieve`, `embed`), or an edge inside one group. **Never on an edge between
  two adjacent groups** — the 40 px gap cannot hold a label, and the white label background bites a hole in the
  group border (`W7`).
- **Slide the label along the edge** when the midpoint is on a border: `<mxGeometry x="-0.6" relative="1"
  as="geometry"/>` (−1 = at the source, 0 = midpoint, 1 = at the target). The users → first-service edge always
  needs this, because its midpoint sits on the AWS Cloud border; the builder computes the offset, by hand aim
  for the middle of the free space outside the cloud (label ≤ 7 characters there).
- When two labeled edges meet at one node, at most one keeps its label.

## 6. Node label placement — keep text out of edge paths

Default is below the icon. Ports are at icon centers, so an edge entering from below runs through a bottom
label; move the label to the free side. In every case **delete the base style's later `align=center;`** — a later
key wins in draw.io and the text lands on the icon.

| Edges on the node | Label position | style fragment |
|---|---|---|
| none / left / right / top only | below (default) | `verticalLabelPosition=bottom;verticalAlign=top;align=center;` |
| bottom (and any of left/right) | above | `verticalLabelPosition=top;verticalAlign=bottom;align=center;` |
| top **and** bottom (a pass-through node) | first choice: **avoid it** — move one neighbour to the side so the edge is horizontal and the bottom stays free (DynamoDB → S3 archive to its left instead of below). If both vertical edges must stay: right (or left) | `labelPosition=right;verticalLabelPosition=middle;align=left;verticalAlign=middle;spacingLeft=8;` (mirror: `labelPosition=left;…;align=right;spacingRight=8;`) — needs an **empty cell** beside the node inside the same group |
| top, bottom and a side (hub), or no free cell beside | bottom-left corner | `labelPosition=left;verticalLabelPosition=bottom;align=right;verticalAlign=top;spacingRight=6;` — ≤ 55 px wide: break into two lines with `<br>` (`API<br>Gateway`, `Chat<br>agent`) |

Labels must stay inside their group rectangle; if a side label does not fit, free the node's bottom side, shorten
the text, or widen the group by one column — do not overflow the border. The builder picks the side from the
incident edges in this order (bottom → top → right/left if the cell is free → bottom-left two-line);
`"label_pos"` in the spec overrides it.

## 7. Multi-page

```xml
<mxfile host="app.diagrams.net">
  <diagram id="overview" name="Overview">…</diagram>
  <diagram id="network" name="Networking Detail">…</diagram>
</mxfile>
```

Above ~14 icons, split: page 1 = service-level overview, later pages = resource-level detail (subnets,
instances, tables). Each page follows the same grid.

## 8. Audience mode

Ask "Technical audience or executive/non-technical?" when unclear.

- **Technical**: service names, protocols (HTTPS, gRPC), CIDRs, instance types.
- **Non-technical**: action labels ("Store data", "Notify"), hide implementation detail, number the flow with
  circled digits as edge labels: `value="①"` with `fontSize=14;fontStyle=1;labelBackgroundColor=#ffffff;`.
  Second flow uses ❶ ❷ ❸.

## 9. Companion guide

Next to `name.drawio`, write `name.md`: title, numbered flow matching the edge labels, service list with purpose,
key design decisions (including any icon substitutions).

## 10. Writing the file

- No XML comments (`<!-- -->`) — draw.io's importer rejects them in some paths.
- Escape `&amp; &lt; &gt; &quot;` in values. Unique `id` per cell. Root cells `id="0"` and `id="1" parent="0"`.
- Large diagrams: write in chunks (header + left, middle, right, bottom + close) to stay within tool limits.
- Save as `<descriptive-name>.drawio`. Export via the draw.io CLI (see SKILL.md) as `name.drawio.png` so the
  PNG embeds the XML and stays editable.

## 11. Self-check (Drawer, before handing to the Reviewer)

For every node: which group? which column, which lane? label side free of edges? label inside the group? For
every edge: same column or lane, or a proper fan-out? corridor empty? label only in a free gap? For the canvas:
white background, title, legend if two edge types, no half-empty page, no empty band. Then run the validator
and **look at the PNG** — the Reviewer's checklist (`review-checklist.md`) is what you will be measured against.
