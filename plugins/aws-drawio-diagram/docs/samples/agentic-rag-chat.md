# Agentic RAG Chat — Serverless on AWS

Sample generated with the aws-drawio-diagram skill (hi-aws-skills), 2026-09-12, v2 (grid + role groups + Amazon Ember).

## Flow
1. Users reach CloudFront over HTTPS; static assets come from S3, API calls go to API Gateway.
2. API Gateway authorizes the caller against a Cognito user pool (dashed) and ships execution logs to CloudWatch, which alarms to SNS.
3. The chat agent (Lambda) reads and writes long-term memory in Bedrock AgentCore Memory, retrieves context from the OpenSearch Serverless vector index, and prompts Bedrock (Claude).
4. Document ingestion: an object created in the documents bucket raises an EventBridge event; the ingest Lambda embeds the document and writes vectors to OpenSearch.

## Services
CloudFront, S3, API Gateway, Cognito, Lambda, Bedrock, Bedrock AgentCore Memory, OpenSearch Serverless, EventBridge, CloudWatch, SNS.

## Layout
- Grid: columns 380 / 620 / 860 / 1100, lanes 260 / 430 (row 1) and 650 / 870 (row 2); users at x=120 outside the cloud.
- Role groups: Frontend, API & Auth, Agent runtime, Foundation model (row 1); Observability, Knowledge, Document ingestion (row 2).
- Hub nodes (API Gateway, chat agent) carry two-line bottom-left labels; nodes with an edge from below carry their label on top; OpenSearch (edges top and bottom) has its label on the right inside a two-column group.
- Only four edge labels: `HTTPS`, `retrieve`, `embed`, `alarm` — each sits in free space, none between adjacent groups.

## Decisions
- OpenSearch uses the legacy stencil name `elasticsearch_service` (renamed service); CloudWatch uses `cloudwatch_2`.
- AgentCore Memory has no draw.io stencil: `shape=image` with the bundled SVG from `references/aws-icons-extra.md`.
- Bedrock Guardrails / Knowledge Bases have no stencil and no bundled SVG, so they are not drawn; the Knowledge group stands for the retrieval layer.
