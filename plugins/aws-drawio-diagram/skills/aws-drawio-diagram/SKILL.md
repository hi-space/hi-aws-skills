---
name: aws-drawio-diagram
description: "Generate editable AWS architecture diagrams as draw.io (.drawio) XML using draw.io's built-in official AWS icon stencils, with an optional PNG/SVG/PDF export that keeps the XML embedded. Use when the user asks for a draw.io / diagrams.net file, an editable diagram, or says 'drawio'. Korean triggers: draw.io로 그려줘, 드로우아이오, 편집 가능한 구성도, drawio 파일로 만들어줘. Not for HTML/SVG/PNG editorial diagrams — use the aws-diagram-design skill for those; use this one when the output must be opened and edited in draw.io."
license: MIT
metadata:
  version: "1.0.0"
  base: "vidanov/aws-architecture-diagram-skill 29c1bab (MIT) + regenerated stencil catalog, validator, image fallbacks"
  source: "https://github.com/hi-space/hi-aws-skills"
---

# AWS draw.io Diagram

Produce a `.drawio` file whose every icon renders, because every stencil name comes from a catalog generated from
draw.io's own sources — never from memory.

## Procedure

1. **Clarify** only what changes the drawing: audience (technical vs executive), rough service list, whether the
   user wants a PNG too. One question at most.
2. **Read** [`references/layout-and-style.md`](references/layout-and-style.md) once. It holds the canvas, edge,
   group, multi-page, and audience rules.
3. **Look up every icon** (see *Icon lookup*). Write the names down before writing XML.
4. **Group, then lay out** (layout-and-style.md §1–§2, §6): decide 2–7 role groups (Frontend, API & Auth, Agent
   runtime, Data, Ingestion, Observability, …), snap them to the 240 × 170 grid, place every icon in a group cell,
   every connected pair on the same column or lane so each edge is one straight segment, and pick each node's
   label side so no edge runs through text. Size the canvas to the content — never a fixed 2400 × 1400 page.
5. **Write the XML** with the Write tool to `<descriptive-name>.drawio`. Large diagrams: write in chunks.
6. **Validate**: run `python3 <skill-dir>/scripts/validate_drawio.py <file>.drawio`. Fix every `ERROR`, then rerun.
   Treat `warn` lines as suggestions, except `W4`/`W5` (crooked or obstructed edges) and `W6` (icon outside every
   group): fix the layout.
7. **Export** if asked (see *Export*), then **look at the PNG** before handing it over: overlapping text, a label on a
   group border, or an edge through an icon means a coordinate is wrong — fix it and re-export.
8. **Companion guide**: write `<name>.md` next to the file (title, numbered flow, services, decisions).

`<skill-dir>` is the directory containing this SKILL.md. Locate it with the plugin root you were installed from;
do not assume it is under the current working directory.

## Two icon patterns — the rule that decides whether icons render

| Pattern | Style | strokeColor | Use for |
|---|---|---|---|
| **Service-level** | `shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.<name>;` | **`#ffffff`** (required) | A named service as a node: colored square + white glyph |
| **Product frame** (variant of service-level) | `shape=mxgraph.aws4.productIcon;prIcon=mxgraph.aws4.<name>;` | **`#ffffff`** (required) | Same as service-level with a product-style frame; rare, appears in one template |
| **Resource-level** | `shape=mxgraph.aws4.<name>;` | **`none`** (required) | Sub-resources and generic marks: colored silhouette |
| Group | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.<group_name>;` | category color | Boundary box with a corner badge |

Swap the strokeColor rules and the glyph disappears or the shape breaks. Every service-level icon also needs the
category `fillColor` (it is in the reference file header). Standard vertex (a child of a role group, coordinates relative to it, `fontFamily` on every cell):

```xml
<mxCell id="lambda1" value="Order Handler" style="sketch=0;points=[[0,0,0],[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0,0],[0,1,0],[0.25,1,0],[0.5,1,0],[0.75,1,0],[1,1,0],[0,0.25,0],[0,0.5,0],[0,0.75,0],[1,0.25,0],[1,0.5,0],[1,0.75,0]];outlineConnect=0;fontColor=#232F3E;fillColor=#ED7100;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;fontFamily=Amazon Ember;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.lambda;" vertex="1" parent="g_agent">
  <mxGeometry x="61" y="60" width="78" height="78" as="geometry" />
</mxCell>
```

## Icon lookup (in this order — never guess a name)

1. **Category file** in `references/` — generated from draw.io, one per palette:
   [`aws-icons-compute.md`](references/aws-icons-compute.md), [`aws-icons-containers.md`](references/aws-icons-containers.md),
   [`aws-icons-database.md`](references/aws-icons-database.md), [`aws-icons-storage.md`](references/aws-icons-storage.md),
   [`aws-icons-network-content-delivery.md`](references/aws-icons-network-content-delivery.md),
   [`aws-icons-application-integration.md`](references/aws-icons-application-integration.md),
   [`aws-icons-security-identity-compliance.md`](references/aws-icons-security-identity-compliance.md),
   [`aws-icons-analytics.md`](references/aws-icons-analytics.md), [`aws-icons-artificial-intelligence.md`](references/aws-icons-artificial-intelligence.md),
   [`aws-icons-management-governance.md`](references/aws-icons-management-governance.md), [`aws-icons-developer-tools.md`](references/aws-icons-developer-tools.md),
   [`aws-icons-internet-of-things.md`](references/aws-icons-internet-of-things.md), [`aws-icons-migration-modernization.md`](references/aws-icons-migration-modernization.md),
   [`aws-icons-front-end-web-mobile.md`](references/aws-icons-front-end-web-mobile.md), [`aws-icons-media-services.md`](references/aws-icons-media-services.md),
   [`aws-icons-general.md`](references/aws-icons-general.md) (users, client, internet, documents), [`aws-icons-groups.md`](references/aws-icons-groups.md).
   Other categories follow the same `aws-icons-<category>.md` naming; `ls <skill-dir>/references/` lists them.
2. **Renamed service?** [`aws-icons-aliases.md`](references/aws-icons-aliases.md) — OpenSearch is `elasticsearch_service`,
   CloudWatch is `cloudwatch_2`, QuickSight is `quick_suite`, and so on.
3. **Still nothing?** [`aws-icons-legacy.md`](references/aws-icons-legacy.md) (renders, not in the palette) and
   [`aws-icons-retired.md`](references/aws-icons-retired.md).
4. **draw.io has no stencil at all** (Bedrock AgentCore Runtime, Gateway, Memory, …):
   [`aws-icons-extra.md`](references/aws-icons-extra.md) gives a ready `shape=image;…` style with the official SVG embedded.
5. **Not there either**: use the parent service icon, label the node with the resource name, and tell the user which
   icon was substituted. Do not invent a stencil name.

Quick grep when a name is on the tip of your tongue: `grep -ri "opensearch" <skill-dir>/references/aws-icons-*.md`.

## Templates

[`templates/`](templates/README.md) holds five upstream diagrams (`serverless-rest-api`, `event-driven-processing`,
`static-website`, `three-tier-web-app`, `vpc-networking`) as a **topology** reference: which services connect to
which. They predate the grid/grouping rules (280 px spacing, no role groups, grey page), so do not copy their
coordinates — rebuild the same topology on the §1 grid. The finished reference for look-and-feel is
[`docs/samples/agentic-rag-chat.drawio`](../../docs/samples/agentic-rag-chat.drawio) in the plugin root.

## Export

Install Amazon Ember before exporting when you can (see layout-and-style.md §3); otherwise the PNG falls back to
Helvetica/Arial and looks slightly wider than the `.drawio` will in a browser with the font. The exported file uses a double extension so the PNG keeps the XML and reopens in draw.io. `-f svg` / `-f pdf` work the same way. If no CLI is available, say so and point to https://app.diagrams.net (File → Import). Never claim a PNG was produced without the file existing.

```bash
# Linux (drawio CLI on PATH). Headless servers need xvfb: prefix with `xvfb-run -a`.
drawio -x -f png -e -b 10 -o name.drawio.png name.drawio
# macOS
/Applications/draw.io.app/Contents/MacOS/draw.io -x -f png -e -b 10 -o name.drawio.png name.drawio
```

Root/CI on a current build: add `--no-sandbox` right after `drawio` (older builds, 26.x and earlier, reject it with `error: too many arguments` — drop it and run as non-root instead). A stencil newer than your installed build (e.g. `bedrock_agentcore`) renders as a blank square — update draw.io desktop, or open the file at https://app.diagrams.net, which is always current.

## Validation checklist (the script enforces most of these)

- Every `resIcon` / `prIcon` / `grIcon` / `shape=mxgraph.aws4.*` name exists in the references (`E1`).
- Service-level `strokeColor=#ffffff`; resource-level `strokeColor=none` (`E2`).
- Every edge has `source`, `target`, and `<mxGeometry relative="1" as="geometry" />` (`E3`).
- Groups carry `container=1` (`E4`); children reference the group as `parent`.
- Unique ids, no XML comments, uncompressed XML (`E5`, `E6`).
- A white (`#FFFFFF`) background rectangle is the first vertex; title, then legend if two edge types.
- Every edge is one straight segment between icons on the same column or lane, with a clear corridor (`W4`, `W5`).
- Every service icon sits inside a role group when an AWS Cloud group exists (`W6`).
- Not checked by the script, checked by your eyes on the PNG: labels off edges and off group borders, `fontFamily`
  on every cell, canvas sized to content.

## Related skill

For an editorial HTML/SVG/PNG rendering (docs, slides, blog), or to **redraw** an existing `.drawio` in a house style,
use `aws-diagram-design`. This skill is for producing the editable `.drawio` itself.
