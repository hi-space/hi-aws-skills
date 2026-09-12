# Phase 1 when the input is a codebase

"Analyse my repo and draw the architecture" is the hardest request this skill gets, and the one where a thin
result is a failure: the user already knows their system, so a six-box overview tells them nothing. The brief
must come out **as detailed as the code**, and every component must be traceable to a file. This page is the
Architect's procedure for that case; the brief template in architecture-brief.md still applies.

## 0. What a good result looks like

- Every AWS resource the code deploys or calls is a node, with its own icon. Nothing is summarised into a box
  named after a team, a project or a repository directory.
- Every node has an **Evidence** cell (`path:line` or `path § symbol`) — the reader can open it and see the
  resource.
- A repo with several deployable units yields **several diagrams**, one per unit, each complete — never one
  diagram that hides the units behind abstract nodes.
- Relationships come from the code too (IAM policies, environment variables carrying ARNs/URLs, SDK calls,
  event source mappings, target groups, ingress rules), not from what "usually" connects.

## 1. Inventory the deployable units (5 minutes, read-only)

Find every deployment definition in the whole tree — IaC often sits four or five directories deep
(`deployment/terraform/environments/prod/main.tf`), so never stop at depth three:

```bash
find . \( -name node_modules -o -name .venv -o -name .git -o -name dist \) -prune -o \
  \( -name '*.tf' -o -name cdk.json -o -name template.yaml -o -name serverless.yml -o -name Pulumi.yaml \
     -o -name Chart.yaml -o -name kustomization.yaml -o -name Dockerfile -o -name 'docker-compose*.yml' \) -print
```

Group the hits by the directory they deploy, then list every unit that has its own deployment definition:

| Marker | Unit type |
|---|---|
| `*.tf`, `cdk.json` + `lib/`, `template.yaml` / `samconfig.toml`, `serverless.yml`, `Pulumi.yaml` | IaC stack |
| `Chart.yaml`, `k8s/`, `manifests/`, `kustomization.yaml` | Kubernetes workload |
| `Dockerfile` + `deploy.sh` / `.github/workflows/*deploy*` | container service |
| `docker-compose*.yml` **and nothing else in the whole tree** | local-only — see §5 (a compose file next to a `deployment/` folder is a dev harness, not the unit) |

Write the result into the brief as **`## Scope`** before anything else, and once the tables are done add one line
under the title: `Components: 30 · Relationships: 33` — the builder checks the tables against it, so a later
phase cannot quietly cut rows — and `Repo: /absolute/path/to/repo`: `scaffold_spec.py` then verifies that every
path in the Evidence column exists there. Evidence is a file you opened, cited as `path:line` relative to Repo;
a plausible-looking path you did not open is fabrication and fails the build.

```markdown
## Scope
| Unit | Path | Deploys with | Region/account (if in code) | Diagram |
|---|---|---|---|---|
| agent-platform | agent-platform/infra | Terraform (ECS Fargate) | ap-northeast-1 | agent-platform |
| llm-gateway | llm-gateway/deployment/charts | Helm on EKS | ap-northeast-2 | llm-gateway |
| t2s-agent | t2s-agent/terraform | Terraform (AgentCore) | ap-northeast-2 | t2s-agent |
Cross-unit calls: agent-platform → llm-gateway (MCP tool, `server/tools/llm_gateway.py:41`) → drawn on both.
```

**Rules for the Diagram column**

- One deployable unit → one diagram, one output set (`<unit>.brief.md`, `.json`, `.drawio`, `.drawio.png`),
  Phases 2–4 run per diagram.
- A unit with more than ~25 components → split it **by request path** (e.g. `llm-gateway-request`,
  `llm-gateway-admin`), never by merging services. A split **covers the unit**: the split briefs' Components
  tables together contain every component of the unit (shared ones, like the API and its stores, appear in
  both), and Scope lists each split diagram with its component count. Seven components on a "chat" page and
  three on an "admin" page out of forty-one is not a split, it is a deletion — the Reviewer sends it back.
  With the automatic layout a unit of 30–40 components fits one page; split only when the layout reports
  `unresolved:` edges you cannot fix by moving a node.
- Two or more units that call each other → add a **system map** *only if the user asks for it or the calls are
  the point of the request*. Its nodes are still real services: each unit's entry service and the services on
  the cross-unit edges (ALB → EKS ingress, AgentCore Gateway → Lambda), grouped by unit. A node labelled
  "LLM Gateway" with a load-balancer icon is not allowed anywhere (see §4).
- When the user asked for "the architecture" of a multi-unit repo and gave no preference, produce the per-unit
  diagrams; list them in the reply; offer the system map. Do not spend the run on the map instead.

## 2. Components from code — IaC first, then SDK, then config

Read in this order and stop when a component has evidence; do not infer from README diagrams alone (they
are often aspirational — cite them only as `README` evidence when nothing else exists, and mark `assumed`).

1. **IaC resources.** Map resource types to stencils:

   | Terraform / CloudFormation / CDK | Stencil |
   |---|---|
   | `aws_lambda_function`, `AWS::Lambda::Function`, `lambda.Function` | `lambda` |
   | `aws_ecs_service` / `aws_ecs_task_definition`, `ecs.FargateService` | `ecs_service` (one per service) |
   | `aws_eks_cluster` + Helm charts | `eks` + one `eks_cloud`/`ecs_service`-style node per Deployment |
   | `aws_lb` (application) | `elastic_load_balancing` |
   | `aws_apigatewayv2_api`, `aws_api_gateway_rest_api` | `api_gateway` |
   | `aws_cloudfront_distribution` | `cloudfront` |
   | `aws_cognito_user_pool` | `cognito` |
   | `aws_dynamodb_table` | `dynamodb` |
   | `aws_s3_bucket` | `s3` |
   | `aws_rds_cluster` (aurora) / `aws_db_instance` | `aurora` / `rds` |
   | `aws_elasticache_*` | `elasticache` |
   | `aws_sqs_queue`, `aws_sns_topic`, `aws_cloudwatch_event_rule` / EventBridge | `sqs`, `sns`, `eventbridge` |
   | `aws_kinesis_stream`, `aws_kinesis_firehose_delivery_stream` | `kinesis_data_streams`, `kinesis_data_firehose` |
   | `aws_secretsmanager_secret`, `aws_ssm_parameter` | `secrets_manager`, `parameter_store` |
   | `aws_cloudwatch_metric_alarm`, log groups | `cloudwatch_2` (one node; alarms → `sns` edge) |
   | `aws_wafv2_web_acl` | `waf` |
   | `aws_vpclattice_*` | `vpc_lattice` |
   | `aws_ecr_repository` | `ecr` (draw only if the request is about delivery) |
   | `aws_bedrockagentcore_*`, `agentcore` CLI/SDK (`bedrock-agentcore` client, `CreateAgentRuntime`, `CreateGateway`) | AgentCore SVGs in aws-icons-extra.md (`Res_Amazon-Bedrock-AgentCore_Runtime_48.svg`, `…_Gateway_48.svg`, `…_Memory_48.svg`) — **never** `lambda` |
   | `aws_bedrock_guardrail`, `bedrock-runtime` client, model ids | `bedrock` (no Guardrails stencil: label the node "Bedrock Guardrails"), `bedrock` |
   | `aws_opensearchserverless_collection` | `elasticsearch_service` (alias) |

   Every other type: look it up (SKILL.md § Icon lookup). Unknown → parent service icon **of that resource's
   own service**, never a look-alike from another service.
2. **SDK clients in code.** `grep -rn "boto3.client(\|boto3.resource(\|@aws-sdk/client-\|aws-sdk\|software.amazon.awssdk"`.
   Each distinct service client is a component (deployed elsewhere → tag `referenced`). **External systems the
   code calls** — SaaS APIs (Tavily, OpenAI), on-premises endpoints (SAP, a token service), partner databases —
   are components too: Group `outside`, Provenance `referenced`, icon from aws-icons-general.md (`internet`,
   `traditional_server`, `generic_database`). A relationship whose target is not a component cannot be
   drawn, and dropping the relationship instead is the mistake this rule prevents.
3. **Configuration.** Environment variables and config files carrying ARNs, queue URLs, table names,
   endpoints, account ids, regions: they give you *relationships* and cross-account/cross-region facts.
4. **Runtime manifests.** Helm values / K8s Deployments (one node per Deployment when they have different
   neighbours), ECS task definitions (one node per service), Lambda handlers (one node per function, or one
   per role when several functions share every neighbour — label "Lambda (4 tools)").

Components table gets two extra columns when the input is code:

```markdown
| id | Service (stencil) | Role in this system | Group | Evidence | Provenance |
|---|---|---|---|---|---|
| server | ECS Fargate service (`ecs_service`) | FastAPI backend | Backend | infra/modules/ecs/main.tf:88 (`aws_ecs_service.server`) | deployed |
| runtime | Bedrock AgentCore Runtime (image `Res_Amazon-Bedrock-AgentCore_Runtime_48.svg`) | agent execution | Agents | agent-runtime/scripts/deploy.sh:31 (`agentcore launch`) | deployed |
| mantle | Bedrock (`bedrock`) — account 905… | cross-account model access | Models | llm-gateway/values.yaml:112 (`BEDROCK_ACCOUNT_905`) | referenced |
| waf | WAF (`waf`) | edge protection | Entry | — | assumed (README says "behind WAF", no resource found) |
```

**Provenance** is one of `deployed` (a resource in this repo's IaC/manifests), `referenced` (called or
configured here, created elsewhere), `assumed` (no evidence; state why it is in the picture). `assumed`
components are allowed only when leaving them out would make the picture wrong, and each one is a Decisions
line. A component you cannot place in any of the three does not exist for this diagram.

## 3. Relationships from code

For every component, answer "who calls it, what does it call" from:

- IAM policies attached to the caller (`aws_iam_role_policy`, task role, IRSA): `dynamodb:PutItem` on table X
  = edge caller → X.
- Environment/config on the caller naming the callee (URL, ARN, table, bucket, queue).
- Event wiring: `aws_lambda_event_source_mapping`, SNS subscriptions, EventBridge targets, S3 notifications,
  ALB target groups / listener rules, K8s Ingress → Service → Deployment.
- SDK calls in the handler when the above are silent.

Each row keeps its **Evidence** too (`server/services/threads.py:57 (table.put_item)`). Kind: `sync` for
request/response, `async` for queues/topics/streams/event source mappings, `aux (dashed)` for logs, metrics,
secrets reads, health checks. The diagram budget (architecture-brief.md) then decides which aux edges are drawn
— never which primary ones.

## 4. Detail rules — what may and may not be merged

- **Never an abstract node.** A node is one AWS service/resource, or a user/external system. Names like
  "Agent Platform", "Backend services", "Text2SQL + SAP Agents", a repository directory, or a team are not
  nodes — they are *groups* (the role-group rectangles) or separate diagrams. An icon that is not the icon of
  the service it stands for (a load balancer standing for a platform, Cognito standing for "agents") is a
  defect the Reviewer sends back.
- **Same service, same role, same neighbours → one node, count in the label** ("DynamoDB (3 tables)",
  "Lambda (4 MCP tools)", "S3 (artifacts · skills · knowledge)"). List the members in Flow or Decisions.
- **Same service, different neighbours → separate nodes.** A `threads` table written by the API and an
  `events` table written by a stream consumer are two DynamoDB nodes.
- **Cross-account / cross-region** resources stay as nodes with the account/region in the label
  ("Bedrock (acct 905, Mantle)"); the group title carries the region when a diagram spans two.
- **Do not draw** IAM roles, KMS keys, ECR repositories, CodeBuild, log groups as nodes unless the request is
  about security/delivery/observability — mention them under *Out of scope* in the brief.
- **Budget pressure is solved by layout, not by deletion.** `scaffold_spec.py` + the builder's auto layout place
  30–40 nodes with all their edges (hubs fan out along their column — layout-and-style.md § 5, "bus"). If the
  layout reports `unresolved:` edges after a hand adjustment, split by request path (§1). Dropping a *primary*
  relationship or a `deployed` component to make the picture fit is never an option the Drawer has, and neither
  is rewriting the brief to match a smaller spec — the brief's `Components: N · Relationships: M` line (write it
  under the title) is checked against its tables.

## 5. Special cases

- **Local-only code (compose, no IaC):** say so in the brief's first line, draw the *intended* AWS mapping only
  if the user asked for it, and tag every component `assumed`.
- **Monorepo with shared modules:** a shared Terraform module used by three units is drawn inside each unit's
  diagram (its resources are per unit).
- **Generated / vendored code, `node_modules`, `.venv`, build outputs:** never evidence.
- **Handover archives, zips, `docs/*.pptx`:** ignore for evidence; may inform naming.

## 6. Hand-off to Phase 2

The Assessor reads the Components table with Evidence and Provenance. It will spot-check service identity
against the evidence (architecture-review.md § 2 step 0) before reviewing — a Runtime tagged `lambda` with
evidence pointing at `agentcore launch` goes back to the Architect, not into a finding.
