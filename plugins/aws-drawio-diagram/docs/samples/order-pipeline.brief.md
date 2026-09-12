# 이벤트 기반 주문 처리 파이프라인

Mobile orders are accepted by an API, queued, persisted, and settled by a payment/inventory workflow that
notifies the customer. Audience: technical.

## Components
| id | Service (stencil) | Role in this system | Group |
|---|---|---|---|
| mobile | Mobile client (`mobile_client`, resource) | Customer's app | outside |
| apigw | API Gateway (`api_gateway`) | REST entry point, request validation | API & Ingestion |
| cognito | Cognito (`cognito`) | JWT authorizer for the API | API & Ingestion |
| sqs | SQS (`sqs`) | Order queue, buffers bursts | API & Ingestion |
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
| # | From → To | What flows | Kind | Label |
|---|---|---|---|---|
| 1 | mobile → apigw | order requests | sync | HTTPS |
| 2 | apigw → sqs | order message | sync | — |
| 3 | apigw → cognito | token validation | aux (dashed) | — |
| 4 | sqs → handler | batch poll | sync | — |
| 5 | handler → ddb | put order | sync | — |
| 6 | handler → sfn | StartExecution | sync | — |
| 7 | sfn → payment | task invoke | sync | — |
| 8 | sfn → inventory | task invoke | sync | — |
| 9 | sfn → sns | publish status | sync | on completion |
| 10 | sns → customer | email / push | async (dashed) | notify |
| 11 | apigw → cw | metrics, logs | aux (dashed) | metrics |
| 12 | ddb → s3 | periodic export | aux (dashed) | — |

## Flow
1. The mobile app calls API Gateway over HTTPS; Cognito validates the token.
2. API Gateway drops the order on the SQS queue and returns 202.
3. The order handler Lambda polls the queue, writes the order to DynamoDB and starts the Step Functions saga.
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
- Main lane 1: mobile → apigw → sqs → handler → sfn → inventory. Fan-out: sfn → payment (lane 0, one bend).
- Row 2 (lane 2): CloudWatch under API Gateway, S3 left of DynamoDB, SNS under Step Functions, customer outside.
- Labels: `HTTPS` (shifted into the space before the cloud), `metrics`, `on completion` (both in row gaps), `notify` (inside the cloud, clear of the border). Nothing between adjacent groups.

## Decisions
- CloudWatch uses `cloudwatch_2` (current icon).
- Payment and inventory are drawn as separate Lambda steps to show the saga; a larger workflow would go on a detail page instead.
