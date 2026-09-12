# Phase 1 — Architecture brief

Write `<name>.brief.md` **before** any layout work. The brief is the contract between the person who understands
the system (the Architect) and the person who draws it (the Drawer): if a relationship is not in the brief, it
is not in the diagram. It also becomes the companion guide that ships next to the `.drawio`.

Keep it to one screen. Bullet points, tables, no prose paragraphs.

## Template

```markdown
# <Title>

<One sentence: what the system does and for whom.>  Audience: technical | executive.

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
| 2 | cf → s3web | static assets | sync | — |
| 3 | apigw → cognito | token validation | async/aux (dashed) | — |
| 4 | lambda → oss | vector query | sync | retrieve |

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

## Decisions & assumptions
- OpenSearch drawn with legacy stencil `elasticsearch_service` (renamed service).
- No Guardrails icon in draw.io: guardrails are described, not drawn.
```

## Diagram budget — decide it here, not in the drawing

The grid gives every node **four sides and one edge per side**, and a bend only reaches the diagonally adjacent
cell. The brief has to respect that, or the Drawer will drop relationships to make the picture work.

- **≤ 4 relationships per component.** A component with more is a hub: put a queue/topic/bus next to it
  (SQS, SNS, EventBridge) and hang the consumers off that, or split it into two components.
- **One representative edge per cross-cutting sink.** CloudWatch, X-Ray, KMS, IAM, Secrets Manager receive
  from everything; draw **one** edge into them from the most telling source (the stream, the API, the main
  Lambda) and say "all services log to CloudWatch" in Flow. Never one edge per service.
- **Fan-out/fan-in ≤ 3 targets**, all in the column next to the source (one on its lane, one above, one
  below). More targets → a topic/bus in between.
- **Aux edges are optional in the picture.** Mark them `aux` in the relationship table; the Reviewer may trim
  them (see review-checklist.md § A) — they still belong in Flow.

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
- **Direction**: Arrows point the way data or the request travels; a response path is not a second arrow.
- **Naming**: Current service names (OpenSearch Service not Elasticsearch, EventBridge not CloudWatch Events,
  Amazon Q / Quick Suite not QuickSight) — the alias table maps them to stencil names.
- **Renames & gaps**: Anything with no stencil and no bundled SVG is a decision to record (substitute parent
  icon, or leave it out and say so).

## What the Drawer needs from the brief

Component ids (they become node ids), stencil names or image files, the group of every inside component, and the
relationship table with the kind and the label text. Nothing else. If the Drawer has to invent any of these,
the brief is incomplete — send it back.
