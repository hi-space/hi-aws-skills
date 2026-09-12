# Agentic RAG Chat — Serverless on AWS

A chat assistant that answers from an organisation's documents, keeps long-term memory per user, and runs
serverless end to end. Audience: technical.

## Components
| id | Service (stencil) | Role in this system | Group |
|---|---|---|---|
| users | Users (`users`, resource) | People on the web chat | outside |
| s3web | S3 (`s3`) | Static site assets | Frontend |
| cf | CloudFront (`cloudfront`) | CDN, TLS, routes `/api` | Frontend |
| cognito | Cognito (`cognito`) | User pool, JWT authorizer | API & Auth |
| apigw | API Gateway (`api_gateway`) | Chat API | API & Auth |
| memory | Bedrock AgentCore Memory (image `Res_Amazon-Bedrock-AgentCore_Memory_48.svg`) | Long-term memory across sessions | Agent runtime |
| lambda | Lambda (`lambda`) | Chat agent: plans, retrieves, prompts | Agent runtime |
| bedrock | Bedrock (`bedrock`) | Claude foundation model | Foundation model |
| sns | SNS (`sns`) | Alarm notifications | Observability |
| cw | CloudWatch (`cloudwatch_2`) | Logs, metrics, alarms | Observability |
| oss | OpenSearch Serverless (`elasticsearch_service`) | Vector index | Knowledge |
| s3docs | S3 (`s3`) | Source documents | Document ingestion |
| eb | EventBridge (`eventbridge`) | Object-created events | Document ingestion |
| ingest | Lambda (`lambda`) | Chunk, embed, index | Document ingestion |

## Relationships
| # | From → To | What flows | Kind | Label |
|---|---|---|---|---|
| 1 | users → cf | HTTPS | sync | HTTPS |
| 2 | cf → s3web | static assets | sync | — |
| 3 | cf → apigw | `/api` requests | sync | — |
| 4 | apigw → cognito | token validation | aux (dashed) | — |
| 5 | apigw → lambda | invoke | sync | — |
| 6 | lambda → memory | read/write memory | sync | — |
| 7 | lambda → bedrock | prompt / completion | sync | — |
| 8 | lambda → oss | vector query | sync | retrieve |
| 9 | apigw → cw | execution logs | aux (dashed) | — |
| 10 | cw → sns | alarm | sync | alarm |
| 11 | s3docs → eb | object created | sync | — |
| 12 | eb → ingest | rule target | sync | — |
| 13 | ingest → oss | upsert vectors | sync | embed |

## Flow
1. Users reach CloudFront over HTTPS; static assets come from S3, API calls go to API Gateway.
2. API Gateway validates the Cognito token and invokes the chat agent Lambda.
3. The agent loads memory from AgentCore Memory, retrieves context from OpenSearch Serverless and prompts Bedrock (Claude).
4. Ingestion: an object created in the documents bucket raises an EventBridge event; the ingest Lambda embeds it and writes vectors to OpenSearch.
5. API Gateway logs to CloudWatch, which alarms to SNS.

## Groups
Frontend · API & Auth · Agent runtime · Foundation model · Observability · Knowledge · Document ingestion

## Checks
- [x] Entry: CloudFront. Auth: Cognito.
- [x] Ingestion is event-driven (EventBridge); the chat path is synchronous by design.
- [x] State: OpenSearch (writer: ingest, reader: agent), AgentCore Memory (agent), S3 buckets.
- [x] Observability: CloudWatch + SNS alarms.

## Layout notes (Drawer)
- Grid: main lane 1 (users → cf → apigw → lambda → bedrock); lane 0 for S3 site, Cognito, Memory; row 2 for Observability and Knowledge; row 3 for ingestion.
- Hub nodes (API Gateway, chat agent) get two-line bottom-left labels; OpenSearch (edges top and bottom) gets its label on the right inside the two-column Knowledge group.
- Four edge labels only: `HTTPS`, `retrieve`, `embed`, `alarm`.

## Architecture review
Lens: Generative AI Lens (read: landing page, "SMB/DB knowledge worker co-pilot" scenario — closest published
reference architecture to an agentic RAG chat with per-user memory; brief differs by using a direct
Lambda-orchestrated agent + OpenSearch Serverless vector store instead of the scenario's agent-framework +
Kendra GenAI Index / Bedrock Knowledge Bases pattern). Skills: aws-serverless (SKILL.md, references/api-gateway.md,
references/orchestration.md). Tool: AWS Knowledge MCP (`mcp__aws-mcp__aws___*`). Date: 2026-09-12.

| # | Pillar | Finding | Source | Severity | Diagram |
|---|---|---|---|---|---|
| R1 | Security | API Gateway (`apigw`) has no WAF; the reference architecture puts authentication *and rate limiting* at this layer, | https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/smbdb-knowledge-worker-co-pilot.html (Reference architecture: "Amazon API Gateway provides RESTful APIs with authentication and rate limiting") | should | + WAF in front of `apigw` (or a dashed WAF badge on the API & Auth group) |
| R2 | Reliability | EventBridge rule `eb → ingest` (rule target = ingest Lambda) has no dead-letter queue; the orchestration reference's EventBridge best-practice list states "DLQs on all targets" | aws-serverless skill, references/orchestration.md § "EventBridge rules, pipes, and patterns → Best practices" | should | + DLQ node off `ingest`'s EventBridge target, in Document ingestion group |
| R3 | Security | OpenSearch Serverless (`oss`) collection's network policy (public vs. VPC/private endpoint) is not stated in the brief; official docs describe both options and note a collection's network access is a first-class security setting alongside encryption and data-access policy | https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless-security.html ("a collection must have an assigned encryption key, network access settings, and a matching data access policy") | should | no new node (policy setting, not drawable); record chosen access mode under Decisions |
| R4 | Security | Chat path (`lambda → bedrock`) has no Bedrock Guardrails; the lens explicitly calls out mitigating "risks of harmful outputs and excessive agency" and Guardrails' own documentation lists prompt-injection/jailbreak and harmful-content filtering as its purpose for chatbot applications | https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/generative-ai-lens.html (pillar summary: "Security: ... mitigate risks of harmful outputs and excessive agency"); https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html | should | none drawable today — brief's own Decisions already note Guardrails have no stencil/SVG; accept as a known deviation |

Decisions: no *must* findings, so nothing was applied. R1–R4 **accepted for v1** and recorded under Decisions with their sources: WAF and the ingest DLQ are the first two additions for a production build; the OpenSearch Serverless network policy and Bedrock Guardrails are settings the picture cannot show.

Sources consulted (incl. no-finding):
- https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/generative-ai-lens.html
- https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/smbdb-knowledge-worker-co-pilot.html
- https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless-security.html
- https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html
- https://docs.aws.amazon.com/apigateway/latest/developerguide/security-monitoring.html
- https://docs.aws.amazon.com/apigateway/latest/developerguide/rest-api-monitor.html
- skill `aws-serverless` (SKILL.md, references/api-gateway.md, references/orchestration.md)

## Decisions
- OpenSearch uses the legacy stencil name `elasticsearch_service`; CloudWatch uses `cloudwatch_2`.
- AgentCore Memory has no draw.io stencil: bundled SVG via `"image"`.
- Bedrock Guardrails / Knowledge Bases have no stencil and no bundled SVG, so they are not drawn.
- Review R1 accepted for v1: no WAF in front of API Gateway (source: Generative AI Lens, SMB/DB knowledge worker co-pilot reference architecture).
- Review R2 accepted for v1: EventBridge → ingest Lambda has no DLQ (source: aws-serverless skill, references/orchestration.md — "DLQs on all targets").
- Review R3 accepted: OpenSearch Serverless collection assumed *private* (AWS service private access from Bedrock/Lambda) — a network policy, not a node (source: OpenSearch Serverless security overview).
- Review R4 accepted: Bedrock Guardrails on the chat path are described, not drawn — no stencil (source: Generative AI Lens security pillar; Bedrock Guardrails user guide).
