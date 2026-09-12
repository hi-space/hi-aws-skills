---
name: aws-drawio-diagram
description: "Generate editable AWS architecture diagrams as draw.io (.drawio) XML using draw.io's built-in official AWS icon stencils, with an optional PNG/SVG/PDF export that keeps the XML embedded. Use when the user asks for a draw.io / diagrams.net file, an editable diagram, or says 'drawio'. Korean triggers: draw.io로 그려줘, 드로우아이오, 편집 가능한 구성도, drawio 파일로 만들어줘. Not for HTML/SVG/PNG editorial diagrams — use the aws-diagram-design skill for those; use this one when the output must be opened and edited in draw.io."
license: MIT
metadata:
  version: "1.1.0"
  base: "vidanov/aws-architecture-diagram-skill 29c1bab (MIT) + regenerated stencil catalog, grid builder, validator, image fallbacks"
  source: "https://github.com/hi-space/hi-aws-skills"
---

# AWS draw.io Diagram

Produce a `.drawio` file that looks like an AWS reference architecture — compact grid, role groups, one font,
every edge a single straight segment or one bend, nothing overlapping — and whose every icon renders, because
every stencil name comes from a catalog generated from draw.io's own sources.

`<skill-dir>` is the directory containing this SKILL.md. Locate it from the plugin root you were installed from;
do not assume it is under the current working directory.

## Three phases, three hats

Do not start drawing. Understand → lay out → review, with a file between each step so the next hat sees only
what it needs. When the Agent tool is available, run each phase as its **own subagent** with a fresh context and
hand it only the files named below; otherwise do the phases yourself in order and still write the files.

| Phase | Hat | Reads | Writes | Reference |
|---|---|---|---|---|
| 1 | **Architect** | the request, this file's *Icon lookup* | `<name>.brief.md` | [`references/architecture-brief.md`](references/architecture-brief.md) |
| 2 | **Drawer** | the brief | `<name>.json` → `<name>.drawio` (+ `.drawio.png`) | [`references/layout-and-style.md`](references/layout-and-style.md) |
| 3 | **Reviewer** | the brief, builder/validator output, the PNG | findings as spec changes → back to 2 | [`references/review-checklist.md`](references/review-checklist.md) |

Output set for `<name>`: `brief.md` (also the companion guide), `json` (layout spec), `drawio`, `drawio.png`.

### Phase 1 — Architect

1. Clarify only what changes the drawing: audience (technical vs executive), services in scope, PNG wanted?
   One question at most; otherwise assume and record the assumption.
2. Fill the brief template: components (id, stencil name, role, group), relationship table (from → to, what,
   sync/async, label or —), numbered flow, 2–7 role groups, the AWS sanity checklist, decisions.
3. **Look up every stencil name** (see *Icon lookup*) and write it into the Components table. Never guess.
4. **Respect the diagram budget** (architecture-brief.md § Diagram budget): ≤ 4 relationships per component,
   one representative edge into CloudWatch-like sinks, fan-out ≤ 3. A brief that ignores this forces the Drawer
   to drop edges.
5. Findings from the sanity checklist (no auth, sync chain of six, store with no writer) go to the user as
   questions or stated assumptions — not silently into the drawing.

### Phase 2 — Drawer

1. Read [`references/layout-and-style.md`](references/layout-and-style.md) §1–§2 and §6 once.
2. Plan the grid from the brief: main request path on one lane left → right; upper lane for things the main lane
   calls "up" (auth, static assets, memory); lower row for observability/ingestion/archive. Users and external
   systems outside the cloud. Every inside node gets a group cell; a fan-out target sits in the next column on
   the lane above or below its source.
3. Write `<name>.json` — the spec format is in the header of
   [`scripts/build_diagram.py`](scripts/build_diagram.py): groups (cols, lanes), nodes (icon or image, col,
   lane, group | outside), edges (from, to, label?, dashed?). Node ids = brief ids.
4. Build: `python3 <skill-dir>/scripts/build_diagram.py <name>.json <name>.drawio`. The builder computes
   coordinates, ports, label sides, group rectangles, the cloud box and the canvas, then runs the validator.
   Fix every `ERROR` and every `W4`–`W8` by changing the spec (move a node, drop a label, widen a group);
   read the builder's `hint:` lines too.
5. Export (see *Export*) — always a plain preview PNG for the Reviewer, plus the `-e` embedded one for the user.
6. Hand-written XML is the fallback only when the spec cannot express something (multi-page, VPC/subnet
   nesting): follow layout-and-style.md §1–§6 literally and validate with `scripts/validate_drawio.py`.

### Phase 3 — Reviewer

1. Look at the PNG **before** the spec. Walk the checklist: faithful to the brief, validator clean, nothing
   overlapping, read order, grouping, balance, typography.
2. Report findings as spec changes; the Drawer applies them and re-exports. Two rounds is normal; a third means
   the group plan or the brief is wrong — return to Phase 1. Exception the Reviewer may settle alone: when the
   brief over-specified instrumentation (five edges into CloudWatch, a sink drawn from every service), trim the
   brief's relationship table to the representative edge, record why under Decisions, and continue.
3. Done when: brief rows = edges, `0 errors, 0 warnings`, and a fresh look at the PNG finds nothing to fix.
   Then tell the user the paths and any substitutions or assumptions from the brief.

## Two icon patterns — the rule that decides whether icons render

| Pattern | Style | strokeColor | Use for |
|---|---|---|---|
| **Service-level** | `shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.<name>;` | **`#ffffff`** (required) | A named service as a node: colored square + white glyph |
| **Product frame** (variant of service-level) | `shape=mxgraph.aws4.productIcon;prIcon=mxgraph.aws4.<name>;` | **`#ffffff`** (required) | Same as service-level with a product-style frame; rare |
| **Resource-level** | `shape=mxgraph.aws4.<name>;` | **`none`** (required) | Sub-resources and generic marks (users, mobile client): colored silhouette |
| Group | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.<group_name>;` | category color | Boundary box with a corner badge (AWS Cloud, VPC, …) |

The builder emits these from `scripts/stencil-index.json` (kind + category `fillColor`). When writing XML by
hand, swap the strokeColor rules and the glyph disappears. Standard vertex (child of a role group, coordinates
relative to it, `fontFamily` on every cell):

```xml
<mxCell id="lambda1" value="Order handler" style="sketch=0;points=[[0,0,0],[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0,0],[0,1,0],[0.25,1,0],[0.5,1,0],[0.75,1,0],[1,1,0],[0,0.25,0],[0,0.5,0],[0,0.75,0],[1,0.25,0],[1,0.5,0],[1,0.75,0]];outlineConnect=0;fontColor=#232F3E;fillColor=#ED7100;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;labelBackgroundColor=#F7F8FA;html=1;fontSize=13;fontStyle=1;fontFamily=Amazon Ember;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.lambda;" vertex="1" parent="g_order">
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
   [`aws-icons-general.md`](references/aws-icons-general.md) (users, mobile client, internet, documents), [`aws-icons-groups.md`](references/aws-icons-groups.md).
   Other categories follow the same `aws-icons-<category>.md` naming; `ls <skill-dir>/references/` lists them.
2. **Renamed service?** [`aws-icons-aliases.md`](references/aws-icons-aliases.md) — OpenSearch is `elasticsearch_service`,
   CloudWatch is `cloudwatch_2`, QuickSight is `quick_suite`, and so on.
3. **Still nothing?** [`aws-icons-legacy.md`](references/aws-icons-legacy.md) (renders, not in the palette) and
   [`aws-icons-retired.md`](references/aws-icons-retired.md).
4. **draw.io has no stencil at all** (Bedrock AgentCore Runtime, Gateway, Memory, …):
   [`aws-icons-extra.md`](references/aws-icons-extra.md) lists bundled SVGs; in the spec use
   `"image": "<file>.svg"` instead of `"icon"`.
5. **Not there either**: use the parent service icon, label the node with the resource name, and record the
   substitution in the brief's Decisions. Do not invent a stencil name.

Quick grep when a name is on the tip of your tongue: `grep -ri "opensearch" <skill-dir>/references/aws-icons-*.md`.

## Samples and templates

The look to match: [`docs/samples/`](../../docs/samples/) in the plugin root holds three complete output sets
(`agentic-rag-chat`, `order-pipeline`, `iot-telemetry`: `.brief.md`, `.json`, `.drawio`, `.drawio.png`). Read a spec before
writing your first one.

[`templates/`](templates/README.md) holds five upstream diagrams as a **topology** reference (which services
connect to which). They predate the grid rules; do not copy their coordinates.

## Export

Install Amazon Ember before exporting when you can (layout-and-style.md §3); otherwise the PNG falls back to
Helvetica/Arial. The `-e` export keeps the XML inside the PNG so it reopens in draw.io; the plain export is the
one to look at with the Read tool. `-f svg` / `-f pdf` work the same way. If no CLI is available, say so and point
to https://app.diagrams.net (File → Import). Never claim a PNG was produced without the file existing.

```bash
# Linux (drawio CLI on PATH). Headless servers: prefix with `xvfb-run -a`.
drawio -x -f png -e -b 10 -o name.drawio.png name.drawio     # deliverable, XML embedded
drawio -x -f png -b 10 -o name.preview.png name.drawio        # for review with the Read tool
# macOS
/Applications/draw.io.app/Contents/MacOS/draw.io -x -f png -e -b 10 -o name.drawio.png name.drawio
```

Root/CI on a current build: add `--no-sandbox` right after `drawio` (older builds, 26.x and earlier, reject it
with `error: too many arguments` — drop it and run as non-root instead). A stencil newer than your installed
build (e.g. `bedrock_agentcore`) renders as a blank square — update draw.io desktop, or open the file at
https://app.diagrams.net, which is always current.

## Validation codes (`scripts/validate_drawio.py`, run by the builder)

- `E1` unknown stencil name · `E2` wrong strokeColor for the pattern · `E3` edge without valid endpoints ·
  `E4` group without `container=1` · `E5` duplicate id · `E6` comment / DOCTYPE / compressed XML.
- `W4` edge that needs two bends or bends to a non-adjacent cell · `W5` edge through an icon · `W6` icon
  inside the cloud but in no group · `W7` edge label on a group border · `W8` two edges drawn on top of each
  other. Treat all five as defects; `W1`–`W3` are style hints. The builder refuses specs that would produce
  `W4`/`W8` and prints `hint:` lines for sparse groups and single-icon lanes — act on them.
- Not checked by the script, checked by the Reviewer's eyes: label length, read order, balance,
  faithfulness to the brief.

## Related skill

For an editorial HTML/SVG/PNG rendering (docs, slides, blog), or to **redraw** an existing `.drawio` in a house
style, use `aws-diagram-design`. This skill is for producing the editable `.drawio` itself.
