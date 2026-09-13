# 이벤트 기반 주문 처리 파이프라인

Mobile orders are accepted by an API, queued, persisted, and settled by a payment/inventory workflow that
notifies the customer. Audience: technical.
Language: ko

## Components
| id | Service (stencil) | Role in this system | Group |
|---|---|---|---|
| mobile | Mobile client (`mobile_client`, resource) | Customer's app | outside |
| apigw | API Gateway (`api_gateway`) | REST entry point, request validation | API & Ingestion |
| cognito | Cognito (`cognito`) | JWT authorizer for the API | API & Ingestion |
| sqs | SQS (`sqs`) | Order queue, buffers bursts | API & Ingestion |
| dlq | SQS (`sqs`) | Dead-letter queue for the order queue (`maxReceiveCount`) — added by review R1 | API & Ingestion |
| handler | Lambda (`lambda`) | Order handler: validates, persists, starts the workflow | Order processing |
| ddb | DynamoDB (`dynamodb`) | Orders table | Order processing |
| sfn | Step Functions (`step_functions`) | Payment & inventory saga | Payment & inventory workflow |
| payment | Lambda (`lambda`) | Payment step | Payment & inventory workflow |
| inventory | Lambda (`lambda`) | Inventory reservation step | Payment & inventory workflow |
| sns | SNS (`sns`) | Order status topic | Notification |
| customer | User (`user`, resource) | Notification recipient | outside |
| cw | CloudWatch (`cloudwatch_2`) | Metrics, logs, alarms | Observability |
| s3 | S3 (`s3`) | Order archive (DynamoDB export) | Archive |

## Relationships
| # | From → To | What flows | Kind |
| --- | --- | --- | --- |
| 1 | mobile → apigw | order requests | sync |
| 2 | apigw → sqs | order message | sync |
| 3 | apigw → cognito | token validation | aux (dashed) |
| 4 | sqs → handler | batch poll | sync |
| 5 | handler → ddb | put order | sync |
| 6 | handler → sfn | start saga | sync |
| 7 | sfn → payment | task invoke | sync |
| 8 | sfn → inventory | task invoke | sync |
| 9 | sfn → sns | post status | sync |
| 10 | sns → customer | email / push | async (dashed) |
| 11 | apigw → cw | metrics, logs | aux (dashed) |
| 12 | ddb → s3 | PITR export | aux (dashed) |
| 13 | sqs → dlq | messages that exceed `maxReceiveCount` | aux (dashed) |

## Flow
1. The mobile app calls API Gateway over HTTPS; Cognito validates the token.
2. API Gateway drops the order on the SQS queue and returns 202.
3. The order handler Lambda polls the queue, writes the order to DynamoDB and starts the Step Functions saga. Messages that fail repeatedly move to the dead-letter queue.
4. Step Functions runs the payment and inventory steps (each a Lambda) and publishes the result to SNS.
5. SNS notifies the customer; API metrics flow to CloudWatch; DynamoDB exports to S3 for archive.

## Groups
API & Ingestion · Order processing · Payment & inventory workflow · Notification · Observability · Archive

## Checks
- [x] Entry: API Gateway. Auth: Cognito authorizer.
- [x] Async boundary between API and processing (SQS); saga steps orchestrated by Step Functions, drawn as a fan-out of two steps.
- [x] State: DynamoDB (orders) has a writer (handler) and readers (workflow, export).
- [x] Observability: CloudWatch from API Gateway; Lambda logs implied.
- [x] Customer is outside the cloud, to the right of the notification path.

## Layout notes (Drawer)
- Main lane 1: mobile → apigw → sqs → handler → sfn → inventory. Fan-out: sfn → payment (lane 0, one bend). DLQ above SQS (lane 0), filling the group's empty cell.
- Row 2 (lane 2): CloudWatch under API Gateway, S3 left of DynamoDB, SNS under Step Functions, customer outside.
- Labels: every straight edge carries its brief label — `HTTPS` (shifted into the pocket before the cloud), `order message` (lane, inside the API group), `verify JWT` / `redrive` / `metrics` / `put order` / `on complete` (vertical), `poll` / `start` / `export` (≤ 6 characters across a group border), `invoke task` (lane, inside the workflow group), `notify`. The fan-out `sfn → payment` bends and carries none — the guide explains it.

## Architecture review
Lens: Serverless Applications Lens (read: landing page "welcome.html", "RESTful microservices" scenario —
closest match: API Gateway → Lambda → DynamoDB, extended here with SQS buffering and a Step Functions saga).
Skills: aws-serverless (SKILL.md, references/event-sources.md, references/orchestration.md),
amazon-dynamodb (SKILL.md). Tool: AWS Knowledge MCP (`aws-mcp`).
Date: 2026-09-12.

| # | Pillar | Finding | Source | Severity | Diagram |
|---|---|---|---|---|---|
| R1 | Reliability | SQS → handler (#4) has no dead-letter queue. The event-source-mapping reference lists a DLQ / redrive policy (`maxReceiveCount`) as a strategy to apply "always" for SQS sources, not as optional hardening | aws-serverless skill, `references/event-sources.md` § "Error handling and concurrency" ("SQS \| Redrive policy / DLQ (`maxReceiveCount`) always") | must | + DLQ node above `sqs` (free cell in the API & Ingestion group) |
| R2 | Security | `apigw` has no WAF association. The API Gateway security whitepaper lists AWS WAF (managed OWASP rules, IP/geo blocking) as the edge protection for regional API endpoints, alongside the authorizer the brief already has (Cognito) | https://docs.aws.amazon.com/whitepapers/latest/security-overview-amazon-api-gateway/security-design-principles.html § "AWS WAF integration" ("AWS WAF is a managed web applications firewall … used in conjunction with API Gateway regional endpoints … effective security for your API Gateway instances") | should | + WAF badge on `apigw` group |
| R3 | Reliability | `sfn` (payment & inventory saga) has no workflow-type decision recorded. The orchestration reference classifies "long-running, `.sync`/callback, non-idempotent (payments)" work as a Standard-workflow case (exactly-once semantics, 90-day execution history), distinct from Express | aws-serverless skill, `references/orchestration.md` § "Standard vs Express" (use-case table) | should | label `sfn` node "Standard workflow" |

Decisions: R1 **fixed** — `dlq` (SQS dead-letter queue) added above the order queue with a dashed `sqs → dlq` edge; relationship 13. R2 and R3 **accepted for v1** — recorded under Decisions with their sources; WAF becomes a node when the API is public-facing in production, the workflow type is an ASL setting the picture cannot show.

Out of scope, consider (not drawn): the `ddb` → `s3` periodic export (#12) uses `ExportTableToPointInTime`, which
requires point-in-time recovery enabled on the `ddb` table — a table-level setting, not something the diagram can
show. Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/S3DataExport_Requesting.html
("To use the export to S3 feature, you must enable PITR on your table").

Sources consulted (incl. no-finding): https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/welcome.html,
https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/restful-microservices.html,
https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/S3DataExport_Requesting.html,
skill aws-serverless (SKILL.md, references/event-sources.md, references/orchestration.md),
https://docs.aws.amazon.com/whitepapers/latest/security-overview-amazon-api-gateway/security-design-principles.html,
skill amazon-dynamodb (SKILL.md — capacity-mode and PITR sections; Cognito authorizer on `apigw`→`cognito` (#3)
and the DynamoDB writer/reader shape were checked against this lens and skill and found already satisfied, no finding).

## Decisions
- CloudWatch uses `cloudwatch_2` (current icon).
- Payment and inventory are drawn as separate Lambda steps to show the saga; a larger workflow would go on a detail page instead.
- Review R2 accepted for v1: no WAF in front of API Gateway (source: API Gateway security whitepaper, "AWS WAF integration"). Add when the API is exposed publicly in production.
- Review R3 accepted for v1: Step Functions workflow type (Standard, for the non-idempotent payment step) is a state-machine setting, not drawn (source: aws-serverless skill, references/orchestration.md § Standard vs Express).
