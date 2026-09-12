# Agentic RAG Chat — Serverless on AWS

Sample generated with the aws-drawio-diagram skill (hi-aws-skills), 2026-09-12.

## Flow
1. Users reach CloudFront over HTTPS; static assets come from S3, `/api` goes to API Gateway.
2. API Gateway authorizes the caller against a Cognito user pool.
3. The chat Lambda stores session state in DynamoDB, retrieves context from the OpenSearch vector index, and prompts Bedrock (Claude).
4. Bedrock AgentCore Memory keeps long-term memory across sessions (image fallback icon — draw.io has no stencil).
5. EventBridge schedules the ingest Lambda, which reads documents from S3, embeds them, and writes to OpenSearch. Logs and metrics go to CloudWatch.

## Services
CloudFront, S3, API Gateway, Cognito, Lambda, Bedrock, Bedrock AgentCore Memory, DynamoDB, OpenSearch Service, EventBridge, CloudWatch.

## Decisions
- OpenSearch uses the legacy stencil name `elasticsearch_service` (renamed service).
- CloudWatch uses `cloudwatch_2` (current icon).
