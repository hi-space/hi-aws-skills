# IoT 텔레메트리 수집·분석 플랫폼

Factory sensors stream telemetry into AWS; the latest state is kept hot in DynamoDB, everything lands in an
S3 data lake for SQL analytics and dashboards, and threshold breaches page the ops team. Audience: technical.

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
| # | From → To | What flows | Kind | Label |
|---|---|---|---|---|
| 1 | sensors → iotcore | telemetry over MQTT | sync | MQTT |
| 2 | iotcore → kinesis | rule action: put record | sync | — |
| 3 | kinesis → normalize | event source mapping | sync | — |
| 4 | normalize → ddb | upsert latest state | sync | — |
| 5 | normalize → s3lake | write curated records | sync | — |
| 6 | normalize → sns | publish threshold breach | sync | — (target named "threshold alerts") |
| 7 | s3lake → crawler | crawl new partitions | sync | — |
| 8 | crawler → catalog | update tables | sync | — |
| 9 | catalog → athena | query metadata | sync | — |
| 10 | athena → quicksight | SPICE / direct query | sync | — |
| 11 | kinesis → cw | stream metrics | aux (dashed) | — |
| 12 | sns → ops | email / SMS | async (dashed) | notify |

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

## Decisions
- `quicksight` (retired palette) instead of `quick_suite` so the PNG renders on draw.io ≤ 26.x; switch to
  `quick_suite` on a current build (see `aws-icons-aliases.md`).
- CloudWatch is fed from Kinesis rather than from the Lambda: the Lambda's four sides are taken; Lambda logging is implied.
