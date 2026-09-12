# Layout and style rules

Adapted from vidanov/aws-architecture-diagram-skill (MIT). Read this once per diagram; SKILL.md only keeps the
procedure and the two icon patterns.

## Layout

- **Left-to-right flow** for the request/data path. Users and front ends on the **left**, data stores and
  external systems on the **right**.
- Horizontal lanes for parallel paths (top lane, bottom lane).
- **≥220 px horizontal** spacing between icons (room for edge labels). **≥250 px vertical** between lanes.
- Secondary services (monitoring, DLQ, error paths) go **below** the main flow with a **≥280 px** gap.
- Icon size **78×78** for main services, **65×65** for secondary. `sketch=0` on every icon. Labels 12 px.
- Above ~12 icons, split into pages (see Multi-page).

## Canvas and title

```xml
<mxGraphModel dx="2800" dy="1600" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="2400" pageHeight="1400" math="0" shadow="0">
```

First element after the root cells: a full-canvas background (prevents black PNG backgrounds), then a title block.

```xml
<mxCell id="bg" value="" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#F5F5F5;strokeColor=none;" vertex="1" parent="1">
  <mxGeometry x="0" y="0" width="2400" height="1400" as="geometry" />
</mxCell>
<mxCell id="title" value="&lt;b&gt;Diagram Title&lt;/b&gt;&lt;br&gt;Author | Date | Version" style="text;html=1;align=left;verticalAlign=top;whiteSpace=wrap;rounded=0;fontSize=14;spacing=8;" vertex="1" parent="1">
  <mxGeometry x="40" y="30" width="420" height="60" as="geometry" />
</mxCell>
```

## Edges

Base style for every edge:

```
edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=2;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;
```

- Every edge has `source` and `target` and a child `<mxGeometry relative="1" as="geometry" />`.
- Labels: 1–2 words. Add `labelBackgroundColor=#F5F5F5;fontSize=11;`. Horizontal edges: `verticalAlign=bottom;`
  (label above). Vertical edges: `align=right;`. Unlabeled edge: omit the `value` attribute.
- Routing to a service above/below the flow: exit bottom `exitX=0.5;exitY=1;`, enter top `entryX=0.5;entryY=0;`,
  exit top `exitX=0.5;exitY=0;`, enter bottom `entryX=0.5;entryY=1;`.
- Types: solid black = primary flow; `dashed=1;` = optional/async; `dashed=1;strokeColor=#DD344C;` = error path.
- Do not label an edge when the relationship is obvious (Lambda → DynamoDB needs no "Write").

## Groups

Always `fillColor=none;container=1;dropTarget=1;`. Names and colors come from
[`aws-icons-groups.md`](aws-icons-groups.md) (generated). The common ones:

| Boundary | style fragment |
|---|---|
| AWS Cloud | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_aws_cloud_alt;strokeColor=#232F3E;fontColor=#232F3E;` |
| Region | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_region;strokeColor=#00A4A6;fontColor=#147EBA;dashed=1;` |
| VPC | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc2;strokeColor=#8C4FFF;fontColor=#8C4FFF;` |
| Availability Zone | `fillColor=none;strokeColor=#147EBA;dashed=1;verticalAlign=top;fontStyle=0;fontColor=#147EBA;` (no badge) |
| Private subnet | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;strokeColor=#00A4A6;fontColor=#147EBA;` |
| Public subnet | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;strokeColor=#7AA116;fontColor=#248814;` |
| Security group | `fillColor=none;strokeColor=#DD3522;verticalAlign=top;fontStyle=0;fontColor=#DD3522;` (no badge) |
| AWS Account | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_account;strokeColor=#CD2264;fontColor=#CD2264;` |
| On-premise / corporate DC | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_corporate_data_center;strokeColor=#7D8998;fontColor=#5A6C86;` |
| Logical group | `whiteSpace=wrap;html=1;fillColor=none;dashed=1;dashPattern=8 8;strokeColor=#5A6C86;fontColor=#5A6C86;` |

Common group prefix: `points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=1;verticalAlign=top;align=left;spacingLeft=30;`
Children of a group set `parent="<group id>"` and use coordinates relative to the group.

## Multi-page

```xml
<mxfile host="app.diagrams.net">
  <diagram id="overview" name="Overview">…</diagram>
  <diagram id="network" name="Networking Detail">…</diagram>
</mxfile>
```

Page 1 = service-level overview. Later pages = resource-level detail (subnets, instances, tables).

## Legend

For diagrams with more than one edge type, place a small legend under the title: solid = primary flow,
dashed = optional/async, red dashed = error path.

## Audience mode

Ask "Technical audience or executive/non-technical?" when unclear.

- **Technical**: service names, protocols (HTTPS, gRPC), CIDRs, instance types.
- **Non-technical**: action labels ("Store data", "Notify"), hide implementation detail, number the flow with
  circled digits as edge labels: `value="①"` with `fontSize=14;fontStyle=1;labelBackgroundColor=#ffffff;`.
  Second flow uses ❶ ❷ ❸.

## Companion guide

Next to `name.drawio`, write `name.md`: title, numbered flow matching the edge labels, service list with purpose,
key design decisions.

## Writing the file

- No XML comments (`<!-- -->`) — draw.io's importer rejects them in some paths.
- Escape `&amp; &lt; &gt; &quot;` in values. Unique `id` per cell. Root cells `id="0"` and `id="1" parent="0"`.
- Large diagrams: write in chunks (header + left, middle, right, bottom + close) to stay within tool limits.
- Save as `<descriptive-name>.drawio`. Export via the draw.io CLI (see SKILL.md) as `name.drawio.png` so the
  PNG embeds the XML and stays editable.
