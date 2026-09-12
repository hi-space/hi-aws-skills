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

## Decisions
- OpenSearch uses the legacy stencil name `elasticsearch_service`; CloudWatch uses `cloudwatch_2`.
- AgentCore Memory has no draw.io stencil: bundled SVG via `"image"`.
- Bedrock Guardrails / Knowledge Bases have no stencil and no bundled SVG, so they are not drawn.
