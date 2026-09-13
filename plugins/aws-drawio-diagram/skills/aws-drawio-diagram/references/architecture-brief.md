# Phase 1 — Architecture brief

Write `<name>.brief.md` **before** any layout work. The brief is the contract between the person who understands
the system (the Architect) and the person who draws it (the Drawer): if a relationship is not in the brief, it
is not in the diagram. It also becomes the companion guide that ships next to the `.drawio`.

Keep it to one screen per diagram. Bullet points, tables, no prose paragraphs.

**Input is a codebase?** Read [`from-source-code.md`](from-source-code.md) first: it adds a `## Scope` section
(one diagram per deployable unit), `Evidence` and `Provenance` columns to Components, and the rules on what may be
merged. The brief must be as detailed as the code — a six-node overview of a forty-resource repo is a failed
Phase 1, not a stylistic choice.

## Template

```markdown
# <Title>

<One sentence: what the system does and for whom.>  Audience: technical | executive.
Language: ko   <!-- the language the USER wrote the request in — the guide is written in it; service names stay English -->

## Components
| id | Service (stencil) | Role in this system | Group |
|---|---|---|---|
| users | Users (`users`, resource) | People on the web app | outside |
| cf | CloudFront (`cloudfront`) | CDN + TLS termination | Frontend |
| lambda | Lambda (`lambda`) | Chat agent handler | Agent runtime |
| memory | Bedrock AgentCore Memory (image `Res_Amazon-Bedrock-AgentCore_Memory_48.svg`) | Long-term memory | Agent runtime |

## Relationships
| # | From → To | What flows | Kind | Label on diagram |
|---|---|---|---|---|
| 1 | users → cf | HTTPS requests | sync | HTTPS |
| 2 | cf → s3web | static assets | sync | static assets |
| 3 | apigw → cognito | token validation | async/aux (dashed) | verify JWT |
| 4 | lambda → oss | vector query | sync | retrieve |
| 5 | lambda → ddb | session read/write | sync | — |

## Flow (numbered, matches the relationships)
1. Users reach CloudFront over HTTPS; …
2. …

## Groups (2–7, role-based)
Frontend · API & Auth · Agent runtime · Foundation model · Observability · Knowledge · Document ingestion

## Checks
- [ ] Every service in the request has a row in Components; every stencil name was looked up (SKILL.md § Icon lookup).
- [ ] Every relationship has a direction and a kind; no relationship implies a service that is missing.
- [ ] AWS sanity (see below) — each item answered or marked N/A.
- [ ] Open questions / assumptions listed.

## Architecture review
(filled in Phase 2 by the Assessor — see architecture-review.md; leave this heading in place)

## Decisions & assumptions
- OpenSearch drawn with legacy stencil `elasticsearch_service` (renamed service).
- No Guardrails icon in draw.io: guardrails are described, not drawn.
- R1 (WAF in front of API Gateway) accepted for v1 — source: Serverless Applications Lens, <url>.
```

## The `#` column is the badge on the edge

Every relationship's `#` is drawn on its edge as a small number badge and is the step number in `<name>.guide.md`
— the reader's link between picture and text. Number rows 1…n in flow order and **never renumber after Phase 3
starts** (a renumbered brief makes the picture disagree with the guide). Aux rows keep their numbers even when not
drawn; their step in the guide says so.

## Labels — the picture carries what fits, the guide carries the rest

The *Label on diagram* column is filled for **every primary relationship**: the *What flows* phrase, ≤ 16
characters, no commas (`static assets`, `verify JWT`, `StartExecution`, `publish status`). Write `—` only when the
pair already says it (Lambda → DynamoDB with nothing to add). Aux rows take a label too when one word names
them (`metrics`, `export`).

The Drawer's tools decide per placed edge whether the label has room — 16 characters on one lane, 6 across a
group border (`HTTPS`), 12 on a vertical edge, none on a bent edge (layout-and-style.md § 5) — and print a
`note:` for every label they drop on a bent or dashed edge. A too-long label on a **primary** relationship stops
the build (`ERROR label`) until it is shortened to the limit named or replaced by `—` — so write them short from
the start (`SQL`, `verify JWT`, `invoke`), not as protocol strings (`PostgreSQL 5432 (via bedrock Lambda)`). What
the picture cannot show, `<name>.guide.md` explains step by step (architecture-guide.md); nothing in this table is
lost, it only moves.

## Diagram budget — decide it here, not in the drawing

The grid gives every node a left and a right slot (one straight edge each) and a top and a bottom slot that can
carry a **bus**: any number of bent edges that all leave (or all arrive) there, run along the node's own column
and turn into the neighbouring columns (layout-and-style.md § 5). So a hub with eight neighbours is drawable —
as long as its own column stays empty above/below it and the neighbours stack in the adjacent columns. The
brief has to respect the following, or the Drawer will run out of cells:

- **Hubs keep their column.** A component with more than four relationships is a hub: plan its neighbours in
  the two adjacent columns, on the lanes above and below, and leave the hub's own column free there. Two hubs
  never share a column.
- **One representative edge per cross-cutting sink.** CloudWatch, X-Ray, KMS, IAM, Secrets Manager receive
  from everything; draw **one** edge into them from the most telling source (the stream, the API, the main
  service) and say "all services log to CloudWatch" in Flow. Never one edge per service.
- **Fan-out to the same side ≤ 2 per lane** (one target left, one right of the hub's column, per lane step);
  more consumers on one hop → a topic/queue in between if the code has one — if it does not, add lanes, not
  fiction.
- **Aux edges are optional in the picture.** Mark them `aux` in the relationship table; the Reviewer may trim
  them (see review-checklist.md § A) — they still belong in Flow. **Primary edges are never optional**, and
  neither is a component: a Drawer that cannot place one comes back to the Architect for a layout decision
  (more lanes, split by request path — from-source-code.md § 1), not a smaller architecture.
- **No abstract nodes.** A node is one AWS service/resource or one user/external system, drawn with its own
  icon. "Backend", "Agents", "Platform X" are groups or separate diagrams. Identical resources with identical
  neighbours may share one node with a count in the label ("DynamoDB (3 tables)").

## AWS sanity checklist

Answer each for the architecture in front of you. A "no" is a finding to raise with the user, not something to
paper over in the drawing.

- **Entry point**: Is there exactly one clear entry (CloudFront / API Gateway / ALB / AppSync)? Users and external
  systems sit *outside* the AWS Cloud.
- **Auth**: Who authenticates callers (Cognito, IAM, custom authorizer)? If nothing does, say so.
- **Async boundaries**: Queue/topic/bus between producer and consumer where the request says "event-driven",
  "async", "decoupled" (SQS, SNS, EventBridge, Kinesis). Sync chains longer than 3 hops deserve a question.
- **Orchestration**: Multi-step workflows are one Step Functions icon at overview level; the steps go in the
  brief's Flow and, if needed, on a detail page — not as a dozen Lambdas.
- **State**: Where does each stateful thing live (DynamoDB, RDS, S3, ElastiCache, OpenSearch)? Every store has at
  least one writer and one reader.
- **Networking**: VPC-bound services (RDS, ElastiCache, EC2, ECS on EC2, OpenSearch provisioned) only when the
  request is about networking; otherwise stay at service level and skip VPC/subnet boxes.
- **Observability**: CloudWatch (and optionally X-Ray, alarms → SNS) unless the user said to leave it out.

This checklist is *completeness* (is anything obviously missing from the picture?). Whether the architecture
follows AWS best practice is Phase 2's job, answered from AWS sources — do not write best-practice claims here.
- **Direction**: Arrows point the way data or the request travels; a response path is not a second arrow.
- **Naming**: Current service names (OpenSearch Service not Elasticsearch, EventBridge not CloudWatch Events,
  Amazon Q / Quick Suite not QuickSight) — the alias table maps them to stencil names.
- **Renames & gaps**: Anything with no stencil and no bundled SVG is a decision to record (substitute parent
  icon, or leave it out and say so).

## The brief is checked mechanically

`build_diagram.py` reads `<name>.brief.md` when it sits next to `<name>.json` and refuses a spec that is smaller
than the brief (and a brief whose `Components: N · Relationships: M` line no longer matches its tables): every id in Components must be a node (write **"not drawn"** in a row's Service cell for the rare
thing a picture cannot show — a Cognito domain, an IAM role), every `From → To` in Relationships must be an edge
with that direction unless its Kind contains `aux`, and the spec may hold nothing the brief does not list. So
write ids the Drawer can use verbatim, and put the aux marker where you mean "optional in the picture".

The first scaffold run also freezes the brief: `<name>.contract.json` records every component id and every
`From → To` pair with its status (drawn / aux / not drawn). Afterwards the scaffold and the builder refuse a brief
whose ids or pairs differ (`ERROR contract`) and print a `note:` for every row newly marked aux or not drawn. The
Drawer's licence is Label text and "not drawn" markers — never the target of a relationship. When *you* change
the architecture after Phase 3 started, delete the contract file and write the reason under Decisions.

## What the Drawer needs from the brief

Component ids (they become node ids), stencil names or image files, the group of every inside component, and the
relationship table with the kind and the label text. Nothing else. If the Drawer has to invent any of these,
the brief is incomplete — send it back.
