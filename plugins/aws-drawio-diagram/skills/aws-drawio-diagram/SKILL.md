---
name: aws-drawio-diagram
description: "Generate editable AWS architecture diagrams as draw.io (.drawio) XML using draw.io's built-in official AWS icon stencils, with an optional PNG/SVG/PDF export that keeps the XML embedded. Use when the user asks for a draw.io / diagrams.net file, an editable diagram, or says 'drawio' — including 'analyse this repo / codebase and draw its AWS architecture' (source code is read as evidence, one detailed diagram per deployable unit). Korean triggers: draw.io로 그려줘, 드로우아이오, 편집 가능한 구성도, drawio 파일로 만들어줘, 코드 분석해서 아키텍처 그려줘. Not for HTML/SVG/PNG editorial diagrams — use the aws-diagram-design skill for those; use this one when the output must be opened and edited in draw.io."
license: MIT
metadata:
  version: "1.3.0"
  base: "vidanov/aws-architecture-diagram-skill 29c1bab (MIT) + regenerated stencil catalog, grid builder, validator, image fallbacks"
  source: "https://github.com/hi-space/hi-aws-skills"
---

# AWS draw.io Diagram

Produce a `.drawio` file that looks like an AWS reference architecture — compact grid, role groups, one font,
every edge a single straight segment or one bend, nothing overlapping — and whose every icon renders, because
every stencil name comes from a catalog generated from draw.io's own sources.

`<skill-dir>` is the directory containing this SKILL.md. Locate it from the plugin root you were installed from;
do not assume it is under the current working directory.

## Four phases, four hats

Do not start drawing. Understand → check against AWS guidance → lay out → review, with a file between each
step so the next hat sees only what it needs. When the Agent tool is available, run each phase as its **own subagent** with a fresh context and
hand it only the files named below; otherwise do the phases yourself in order and still write the files.

| Phase | Hat | Reads | Writes | Reference |
|---|---|---|---|---|
| 1 | **Architect** | the request (or the codebase), this file's *Icon lookup* | `<name>.brief.md` (one per deployable unit) | [`references/architecture-brief.md`](references/architecture-brief.md); codebase input: [`references/from-source-code.md`](references/from-source-code.md) |
| 2 | **Assessor** | the brief + AWS docs/skills via MCP | `## Architecture review` section in the brief | [`references/architecture-review.md`](references/architecture-review.md) |
| 3 | **Drawer** | the brief | `<name>.json` → `<name>.drawio` (+ `.drawio.png`) | [`references/layout-and-style.md`](references/layout-and-style.md) |
| 4 | **Reviewer** | the brief, builder/validator output, the PNG | findings as spec changes → back to 3 | [`references/review-checklist.md`](references/review-checklist.md) |

Output set for `<name>`: `brief.md` (also the companion guide), `json` (layout spec), `drawio`, `drawio.png`.
A repo with several deployable units produces several output sets — never one diagram of abstract boxes.

**Drawer and Reviewer are different contexts.** A Drawer that reviews its own picture passes it; every trial that
skipped the split shipped dropped edges, invented nodes and unread validator warnings. Spawn the Reviewer as a
subagent, or at minimum write `<name>.review.md` with the § A counts before touching the spec again.

### Phase 1 — Architect

0. **Input is source code?** Follow [`references/from-source-code.md`](references/from-source-code.md): inventory
   the deployable units into `## Scope` (one diagram each), take components from IaC → SDK clients → config with
   an `Evidence` and `Provenance` column per row, relationships from IAM/env/event wiring. The brief must be as
   detailed as the code; a repo with 40 resources does not become a 6-box picture.
1. Clarify only what changes the drawing: audience (technical vs executive), services in scope, PNG wanted?
   One question at most; otherwise assume and record the assumption.
2. Fill the brief template: components (id, stencil name, role, group), relationship table (from → to, what,
   sync/async, label or —), numbered flow, 2–7 role groups, the AWS sanity checklist, decisions.
3. **Look up every stencil name** (see *Icon lookup*) and write it into the Components table. Never guess.
4. **Respect the diagram budget** (architecture-brief.md § Diagram budget): hubs keep their own column free
   above/below so their neighbours can stack beside them (bus edges), one representative edge into
   CloudWatch-like sinks, no abstract nodes. Budget problems are solved with lanes, buses and more diagrams —
   never by merging services or dropping primary relationships.
5. Findings from the sanity checklist (no auth, sync chain of six, store with no writer) go to the user as
   questions or stated assumptions — not silently into the drawing.

### Phase 2 — Assessor

0. Spot-check service identity against the brief's Evidence column first (a Runtime labelled Lambda makes
   every later finding wrong) — mismatches go back to the Architect (architecture-review.md § 2 step 0).
1. Check the tool list for an AWS MCP server (`search_documentation` / `retrieve_skill`). None → write
   "Architecture review — skipped" into the brief with the install command and move on. **Never** substitute
   your own opinion for the missing source.
2. Pick the Well-Architected lens for the workload, read its closest reference scenario, then look up each
   service's AWS skill or documentation for the relationships the brief draws
   (architecture-review.md § 2).
3. Write the `## Architecture review` table into the brief: pillar, finding, **source you opened**, severity
   (must / should / could), diagram impact. No source, no finding. Zero findings with a sources list is fine.
   The header line states the tool and the **number of calls made**; three calls for fifteen services is not a
   review.
4. Put the findings to the user: fix (Architect edits the brief) or accept (Decisions, with the source).
   Unattended: apply *must* findings that add ≤ 1 component, accept the rest for now and say so.

### Phase 3 — Drawer

1. Read [`references/layout-and-style.md`](references/layout-and-style.md) §1–§2 and §5–§6 once — to understand
   what the builder does, not to do it yourself.
2. **Do not place nodes by hand.** Run `python3 <skill-dir>/scripts/scaffold_spec.py <name>.brief.md <name>.json`:
   it turns the brief's Components and Relationships tables into a coordinate-free spec (nodes with icon/image and
   group, edges with dashed/label). Fix any `warn:` it prints (unknown stencil → look it up; a relationship naming
   an undrawn component → mark that row "not drawn" or add the component) by editing the **brief**, then rerun.
3. Build: `python3 <skill-dir>/scripts/build_diagram.py <name>.json <name>.drawio`. Nodes without coordinates are
   placed automatically (`scripts/layout.py`: request path left → right on one lane, hubs with their neighbours
   stacked beside them, groups as rectangles, users outside) and the placed spec is saved as
   `<name>.layout.json`. The builder then computes ports, labels, group boxes, cloud box and canvas, checks the
   spec against the brief, and runs the validator. Hand-tuning: edit `<name>.layout.json` (move a node to another
   cell, force `"route": "h"` on an edge) and rebuild **from that file**; never from a hand-written subset.
4. Read the builder's output to the end. `unresolved:` lines mean two nodes cannot be joined with one bend in
   this placement — move one of them in `<name>.layout.json`; if a node has neighbours spread over four or more
   columns, that is the signal to split the diagram by request path (from-source-code.md § 1). `note: label
   dropped` is fine (bent edges carry no label).
   **Exit status 0 is the only pass**: any `ERROR` or `W4`–`W9` prints `Layout defects … NOT CLEAN` and exits 1
   — fix it by changing the spec (move a node, drop a label, widen a group, stack a hub's neighbours beside it);
   read the builder's `hint:` lines too. Never export, and never call the diagram done, on a non-zero exit.
   Keep `<name>.brief.md` next to `<name>.json`: the builder then **checks the spec against the brief** (every
   Components row is a node unless marked "not drawn"; every Relationships row is an edge unless its Kind says
   `aux`; nothing in the spec that the brief lacks) and prints `brief check: N components → N nodes … ✓`. A
   mismatch is an error — the fix is a layout change or a second diagram (from-source-code.md § 1), never a
   node the brief does not have and never a dropped edge. There is no flag that makes a deliverable skip this
   check; a build log without `brief check … ✓` is an unfinished build.
5. `W9 icon has no edge` means the brief lists a component with no relationship: either the Architect forgot the
   relationship (add the row) or the component does not belong in the picture (mark its row "not drawn" — VPC,
   NAT, ECR, IAM roles usually). The Drawer never solves it by deleting the node from the spec.
6. Export (see *Export*) — always a plain preview PNG for the Reviewer, plus the `-e` embedded one for the user.
7. Hand-written XML is the fallback only when the spec cannot express something (multi-page, VPC/subnet
   nesting): follow layout-and-style.md §1–§6 literally and validate with `scripts/validate_drawio.py`.

### Phase 4 — Reviewer

1. Look at the PNG **before** the spec. Walk the checklist: faithful to the brief (count components and
   relationships against nodes and edges and write the numbers down), no abstract nodes, validator exit 0,
   nothing overlapping, read order, grouping, balance, typography. Verdict `ready` / `not ready`, nothing else.
2. Report findings as spec changes; the Drawer applies them and re-exports. Two rounds is normal; a third means
   the group plan or the brief is wrong — return to Phase 1 (and re-run Phase 2 if components changed). Exception the Reviewer may settle alone: when the
   brief over-specified instrumentation (five edges into CloudWatch, a sink drawn from every service), trim the
   brief's relationship table to the representative edge, record why under Decisions, and continue.
3. Done when: `brief check … ✓`, `0 errors, 0 warnings`, and a fresh look at the PNG finds nothing to fix.
   Then tell the user the paths and any substitutions or assumptions from the brief. **Briefs alone are not a
   deliverable**: the request was a diagram, so the run ends only when every output set named in `## Scope` has
   its `.drawio` and PNGs — a "final report" with specs "ready for export" is an unfinished run.

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
5. **Not there either**: use the parent service icon **of the same service** (AgentCore Gateway → an AgentCore
   SVG or `bedrock_agentcore`, never `api_gateway`; a Guardrail → `bedrock`), label the node with the resource
   name, and record the substitution in the brief's Decisions. Do not invent a stencil name. This rule is for
   *resources without a stencil*; it never licenses an abstract node — "Agent Platform" drawn as a load balancer
   or "Agents" drawn as Cognito is a defect, not a substitution.

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
- `W4` edge that needs two bends · `W5` edge through an icon · `W6`
  icon inside the cloud but in no group · `W7` edge label on a group border · `W8` two edges drawn on top of
  each other (bent edges sharing a trunk from one side of one node are a *bus*, allowed) · `W9` icon with no
  edge. All six are defects: the validator and the builder exit 1 on them. `W1`–`W3` are style hints. The
  builder refuses specs that would produce `W4`/`W8` and prints `hint:` lines for sparse groups and
  single-icon lanes — act on them.
- Not checked by the script, checked by the Reviewer's eyes: label length, read order, balance,
  faithfulness to the brief. Architecture quality is not checked here at all — that is Phase 2, against AWS sources.

## Related skill

For an editorial HTML/SVG/PNG rendering (docs, slides, blog), or to **redraw** an existing `.drawio` in a house
style, use `aws-diagram-design`. This skill is for producing the editable `.drawio` itself.
