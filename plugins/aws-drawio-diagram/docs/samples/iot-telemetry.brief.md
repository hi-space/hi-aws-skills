# IoT 텔레메트리 수집·분석 플랫폼

Factory sensors stream telemetry into AWS; the latest state is kept hot in DynamoDB, everything lands in an
S3 data lake for SQL analytics and dashboards, and threshold breaches page the ops team. Audience: technical.
Language: ko

## Components
| id | Service (stencil) | Role in this system | Group |
|---|---|---|---|
| sensors | Sensor (`sensor`, resource) | Factory-floor devices | outside |
| iotcore | AWS IoT Core (`iot_core`) | MQTT broker, device auth, rules | Ingestion |
| kinesis | Kinesis Data Streams (`kinesis_data_streams`) | Ordered telemetry stream | Ingestion |
| normalize | Lambda (`lambda`) | Normalize units, enrich, detect thresholds | Processing |
| s3lake | S3 (`s3`) | Data lake (raw + curated) | Storage |
| ddb | DynamoDB (`dynamodb`) | Latest state per device | Storage |
| crawler | Glue crawler (`glue_crawlers`, resource) | Schema discovery | Analytics |
| catalog | Glue Data Catalog (`glue_data_catalog`, resource) | Table metadata | Analytics |
| athena | Athena (`athena`) | SQL over the lake | Analytics |
| quicksight | QuickSight (`quicksight`, retired name) | Dashboards | Analytics |
| cw | CloudWatch (`cloudwatch_2`) | Stream metrics, Lambda logs, alarms | Observability |
| sns | SNS (`sns`) | Threshold alert topic | Notification |
| ops | User (`user`, resource) | Ops team on call | outside |

## Relationships
| # | From → To | What flows | Kind |
| --- | --- | --- | --- |
| 1 | sensors → iotcore | telemetry over MQTT | sync |
| 2 | iotcore → kinesis | rule action: put record | sync |
| 3 | kinesis → normalize | record batch | sync |
| 4 | normalize → ddb | upsert latest state | sync |
| 5 | normalize → s3lake | write to lake | sync |
| 6 | normalize → sns | publish threshold breach | sync |
| 7 | s3lake → crawler | new files | sync |
| 8 | crawler → catalog | update tables | sync |
| 9 | catalog → athena | query metadata | sync |
| 10 | athena → quicksight | SPICE / direct query | sync |
| 11 | kinesis → cw | stream metrics | aux (dashed) |
| 12 | sns → ops | email / SMS | async (dashed) |

## Flow
1. Sensors publish telemetry to IoT Core over MQTT; an IoT rule forwards records to Kinesis Data Streams.
2. The normalize Lambda consumes the stream, writes the latest state to DynamoDB and curated records to the S3 data lake.
3. When a reading crosses a threshold the Lambda publishes to SNS, which notifies the ops team.
4. A Glue crawler catalogs new lake partitions; Athena queries them and QuickSight renders dashboards.
5. Kinesis and Lambda metrics land in CloudWatch.

## Groups
Ingestion · Processing · Storage · Analytics · Observability · Notification

## Checks
- [x] Entry: IoT Core (device certificates authenticate sensors).
- [x] Async boundary: Kinesis between ingestion and processing; SNS between detection and people.
- [x] State: DynamoDB (writer normalize, reader apps — out of scope), S3 (writer normalize, readers Glue/Athena).
- [x] Observability: CloudWatch from Kinesis (Lambda logs implied; not drawn to keep one edge per node side).

## Layout notes (Drawer)
- Main lane 1: sensors → IoT Core → Kinesis → Normalize → DynamoDB. Normalize fans out with two bends: up-right to
  S3 (lane 0) and down-right to SNS (lane 2) — one edge per side, so its four sides are left/right/top/bottom.
- Analytics chain on lane 0 from S3; QuickSight below Athena. Ops team outside the cloud on the right, on SNS's lane.
- Two labels only: `MQTT` (outside the cloud) and `notify` (free space under Analytics). No label on the bent
  edge to SNS — the target's name carries the meaning.

## Architecture review
Lens: IoT Lens (read: landing page `iot-lens.html`; closest scenario: *Device telemetry* — the brief matches its
IoT Core → stream → processing → storage shape). Skills: aws-serverless
(event-sources.md), setting-up-cloudwatch-alarm-notifications, securing-s3-buckets,
managing-amazon-kinesis-data-streams (no finding). Tool: AWS Knowledge MCP (`aws-mcp`). Date: 2026-09-12.

| # | Pillar | Finding | Source | Severity | Diagram |
|---|---|---|---|---|---|
| R1 | Reliability | `kinesis → normalize` is drawn as a plain event source mapping with no failure-destination or bounded-retry path. Kinesis/DynamoDB-Streams ESMs need `OnFailure` destination, `MaximumRetryAttempts`, and `MaximumRecordAgeInSeconds` — without them a poison record can block the shard for the whole retention window | aws-serverless skill, `references/event-sources.md` § "Error handling and concurrency" ("DynamoDB/Kinesis: BisectBatchOnFunctionError; ReportBatchItemFailures; MaximumRetryAttempts + MaximumRecordAgeInSeconds (prevent shard blocking); OnFailure destination") | should | + an `OnFailure` destination (e.g. SQS DLQ) hanging off the `kinesis → normalize` edge |
| R2 | Operational excellence | CloudWatch only receives Kinesis stream metrics (relationship 11); no CloudWatch alarm→notification action is drawn. The threshold-breach path to SNS (relationship 6) is the Lambda's own application logic, not an infrastructure alarm (e.g. on IteratorAge or Lambda Errors) | setting-up-cloudwatch-alarm-notifications skill (SKILL.md): "Always use this skill when configuring alarm notifications — it creates encrypted SNS topics... and links alarms to notification actions" | should | + `cw → sns` edge (alarm action), reusing the existing SNS node |

Out of scope, consider: S3 data-lake baseline controls (default encryption, HTTPS-only bucket policy, Block
Public Access) aren't things this diagram shows either way — noted per the securing-s3-buckets skill's
"Secure New Bucket" workflow (encryption + `DenyInsecureTransport` policy as required steps), not drawn as a
finding since the brief doesn't omit anything a node/edge could represent here.

Decisions: no *must* findings, so nothing was applied. R1 and R2 **accepted for v1** and recorded under Decisions with their sources; both are one-node additions (OnFailure queue, alarm edge) for the production version.

Sources consulted (incl. no-finding): https://docs.aws.amazon.com/wellarchitected/latest/iot-lens/iot-lens.html,
https://aws.amazon.com/blogs/publicsector/4-common-iot-protocols-and-their-security-considerations/ (IoT Core
X.509/mTLS — already satisfied by the brief's device-certificate entry check, no finding), skill aws-serverless
(SKILL.md, references/event-sources.md), skill setting-up-cloudwatch-alarm-notifications (SKILL.md), skill
securing-s3-buckets (SKILL.md), skill managing-amazon-kinesis-data-streams (SKILL.md — covers KDS→S3 Tables
channels, not applicable to this brief's plain Kinesis stream, no finding), search results for
`querying-data-lake` / `ingesting-into-data-lake` / `exploring-data-catalog` skills (Glue/Athena/S3 lake — no
skill matched the crawler→catalog→Athena→QuickSight relationships closely enough to cite a finding).

## Decisions
- `quicksight` (retired palette) instead of `quick_suite` so the PNG renders on draw.io ≤ 26.x; switch to
  `quick_suite` on a current build (see `aws-icons-aliases.md`).
- CloudWatch is fed from Kinesis rather than from the Lambda: the Lambda's four sides are taken; Lambda logging is implied.
- Review R1 accepted for v1: Kinesis → Normalize event source mapping has no OnFailure destination / bounded retry (source: aws-serverless skill, references/event-sources.md § Error handling and concurrency).
- Review R2 accepted for v1: no CloudWatch alarm → SNS action drawn; the SNS edge shown is application threshold logic (source: setting-up-cloudwatch-alarm-notifications skill).
