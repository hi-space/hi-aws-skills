# AWS Icons: Aliases (renamed services → draw.io stencil names)

Hand-maintained. draw.io keeps the stencil name a service had when the icon was first added, so the current
AWS marketing name often does not match. Look here when the category file has no obvious row.
`pattern` tells you which style to use: `service` = resourceIcon frame + `strokeColor=#ffffff`,
`resource` = standalone shape + `strokeColor=none`, `group` = grIcon badge, `image` = SVG fallback in
[`aws-icons-extra.md`](aws-icons-extra.md).

| Service name (current) | stencil | pattern | Note |
|---|---|---|---|
| Amazon OpenSearch Service | `elasticsearch_service` | service | renamed from Elasticsearch Service in 2021 |
| Amazon OpenSearch Serverless / cluster nodes | `opensearch_service_data_node` | resource | resource icons kept the OpenSearch name |
| Amazon Quick Suite (was QuickSight) | `quick_suite` | service | added 2025; renders blank on draw.io ≤ 26.x — use retired `quicksight` there |
| Amazon SageMaker AI | `sagemaker_2` | service | `sagemaker` is the older icon |
| Amazon Managed Service for Apache Flink (was Kinesis Data Analytics) | `managed_service_for_apache_flink` | service | `kinesis_data_analytics` is retired |
| Amazon Data Firehose | `kinesis_data_firehose` | service | |
| Amazon Kinesis Data Streams | `kinesis_data_streams` | service | |
| Amazon MSK | `managed_streaming_for_kafka` | service | |
| Amazon CloudWatch | `cloudwatch_2` | service | `cloudwatch` (no suffix) is legacy |
| Amazon CloudWatch Logs | `cloudwatch_logs` | resource | |
| Amazon EventBridge (was CloudWatch Events) | `eventbridge` | service | |
| AWS Certificate Manager | `certificate_manager_3` | service | `certificate_manager` / `_2` are older icons |
| AWS IAM | `identity_and_access_management` | service | |
| AWS IAM Identity Center (was SSO) | `single_sign_on` | service | |
| Amazon SES | `simple_email_service` | service | |
| Amazon SNS | `sns` | service | |
| Amazon SQS | `sqs` | service | |
| Amazon ECS | `ecs` | service | |
| Amazon EKS | `eks` | service | |
| Amazon ECR | `ecr` | service | |
| Elastic Load Balancing (service) | `elastic_load_balancing` | service | |
| Application Load Balancer | `application_load_balancer` | resource | |
| Network Load Balancer | `network_load_balancer` | resource | |
| Amazon VPC (service icon) | `vpc` | service | |
| VPC boundary (group badge) | `group_vpc2` | group | `group_vpc` is legacy but still renders |
| Private subnet boundary | `group_security_group` | group | draw.io reuses this badge; set `strokeColor=#00A4A6` |
| Public subnet boundary | `group_security_group` | group | set `strokeColor=#7AA116` |
| AWS Systems Manager | `systems_manager` | service | |
| Amazon Rekognition | `rekognition_2` | service | |
| Amazon DocumentDB | `documentdb_with_mongodb_compatibility` | service | |
| Amazon ElastiCache (Valkey) | `elasticache_for_valkey` | resource | service icon is `elasticache` |
| Amazon Q | `q` | service | |
| Amazon Nova | `nova2` | service | |
| Amazon Bedrock | `bedrock` | service | |
| Amazon Bedrock AgentCore (service) | `bedrock_agentcore` | service | |
| Bedrock AgentCore Runtime / Gateway / Memory / Identity / … | `shape=image` | image | no draw.io stencil; see aws-icons-extra.md |
| AWS Step Functions | `step_functions` | service | |
| AWS Transit Gateway | `transit_gateway` | service | route table: `transit_gateway_attachment` (resource) |
| VPC peering connection | `peering` | resource | `vpc_peering` does **not** exist |
| AWS CloudHSM | `cloudhsm` | service | `cloud_hsm` does **not** exist |
| Amazon S3 Glacier | `glacier` | service | Deep Archive: `glacier_deep_archive` (resource) |
| AWS Elastic Beanstalk | `elastic_beanstalk` | service | |
| AWS Global Accelerator | `global_accelerator` | service | |
