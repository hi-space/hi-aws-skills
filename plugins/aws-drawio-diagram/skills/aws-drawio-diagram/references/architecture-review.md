# Phase 2 — Architecture review (evidence only)

Before anything is drawn, the brief is checked against what AWS has **published**: the Well-Architected
Framework and its lenses, service documentation, and AWS's own agent skills. The Assessor does not judge; it
looks things up. **Every finding cites a source retrieved during this review. No source → no finding.** If no
AWS MCP server is reachable, the review is *skipped and said so* — never replaced by the model's own opinion.

The Assessor reads the brief and writes one section back into it: `## Architecture review`. Nothing else
changes until the user has decided what to do with the findings.

## 1. Sources you may use (public, official)

| Source | How to reach it | Use for |
|---|---|---|
| **AWS Knowledge MCP Server** — `https://knowledge-mcp.global.api.aws` (no auth) | tools `search_documentation` (topics `general`, `agent_skills`), `read_documentation`, `recommend`, `retrieve_skill`. Installed here as `awsknowledge` (deploy-on-aws plugin) and `aws-mcp`; add with `claude mcp add --transport http aws-knowledge https://knowledge-mcp.global.api.aws` | docs, Well-Architected lenses, AWS skills registry |
| **AWS Documentation MCP Server** (awslabs) | `uvx awslabs.aws-documentation-mcp-server@latest` → `search_documentation`, `read_documentation`, `read_sections`, `recommend` | same docs, section-level reads |
| **AWS agent skills** (registry behind `retrieve_skill`) | `search_documentation(topics=["agent_skills"], search_phrase="<service> best practices")` → copy `skill_name` verbatim → `retrieve_skill(skill_name)` and `retrieve_skill(skill_name, file="references/…")` | production-readiness rules per service: e.g. `aws-serverless`, `amazon-dynamodb`, `amazon-opensearch-service`, `aws-iam`, `aws-security`, `aws-resilience-lifecycle` (search — the list changes) |
| **awslabs/agent-plugins** marketplace (Claude Code plugins) | `claude plugin marketplace add awslabs/agent-plugins`; plugins `aws-serverless`, `databases-on-aws`, `deploy-on-aws`, `sagemaker-ai`, … | when installed, their skills are local files you can read |
| **Well-Architected Framework & lenses** | `https://docs.aws.amazon.com/wellarchitected/latest/framework/` and `…/wellarchitected/latest/<lens>/` via `read_documentation` | pillar questions and reference scenarios |

Not admissible: your own memory, third-party blogs, "everybody knows". AWS blogs (`aws.amazon.com/blogs`) are
official but secondary — cite one only when no documentation page says the same thing.

Tool names differ per installation (`mcp__aws-mcp__aws___search_documentation`,
`mcp__plugin_deploy-on-aws_awsknowledge__aws___search_documentation`, `mcp__aws-docs__search_documentation`).
Look for `search_documentation` / `retrieve_skill` in your tool list; any one of them is enough.

## 2. Procedure

1. **Tool check.** No `search_documentation`-style tool → write into the brief:
   `## Architecture review — skipped: no AWS MCP server available (add: claude mcp add --transport http
   aws-knowledge https://knowledge-mcp.global.api.aws)` and tell the user. Stop here; go to Phase 3.
2. **Pick the lens.** From the brief's one-line summary and Components choose one lens (two at most):

   | Workload | Lens (`docs.aws.amazon.com/wellarchitected/latest/…`) |
   |---|---|
   | Lambda / API Gateway / Step Functions / EventBridge / SQS | `serverless-applications-lens/` |
   | Bedrock, RAG, agents, LLM apps | `generative-ai-lens/` |
   | IoT Core, Greengrass, device fleets | `iot-lens/` |
   | Kinesis, Glue, Athena, Redshift, lake | `analytics-lens/` |
   | ECS / EKS / containers | `container-build-lens/` |
   | Multi-tenant SaaS | `saas-lens/` |
   | Anything else | `framework/` (the six pillars) |

   The landing page is prose without links in the markdown reader — go straight to
   `…/<lens>/scenarios.html` (every lens has one; it lists the scenario names), then `read_documentation` the
   scenario page whose services overlap the brief most (Serverless: `restful-microservices.html`,
   `streaming-processing.html`, `event-driven-architectures.html`; IoT: `device-telemetry.html`; GenAI:
   `smbdb-knowledge-worker-co-pilot.html`, …). No scenario matches exactly — pick the closest, and write the
   delta in the section's header line ("closest: RESTful microservices; brief adds SQS buffering + saga").
   Scenario pages are long: read the TOC first and jump to *Reference architecture* with `start_index`.
3. **Per service.** For every row in Components: `search_documentation(topics=["agent_skills"], …)`; when a
   skill exists, `retrieve_skill` it and read the parts that match the brief's *relationships* for that
   service (Lambda ← SQS: DLQ, batch size, partial batch response; API Gateway: authorizer, throttling, WAF;
   DynamoDB: access patterns, on-demand vs provisioned; OpenSearch Serverless: private access, encryption).
   One `agent_skills` search per service is enough to decide "no skill". Then one
   `search_documentation(topics=["general"], "<service> best practices <the relationship>")`. The result's
   `context` is verbatim page text and **counts as opened** — cite its `url`. If the only hits are AWS blogs,
   cite the blog chunk once, mark it "(blog)", and move on; do not keep searching for a canonical page.

   **What is evidence.** A doc page or skill file you read (or a search chunk of it). A registry
   `skill_description` blurb alone is **not** — open the skill (`retrieve_skill`) or find a doc page. When
   `retrieve_skill` fails because the skill is too large, the error names a file where the output was saved;
   read that file (Read / `sed -n`) and cite the skill normally.
4. **Per pillar, only what a diagram can show.** Ask each question once, answer from the sources:

   | Pillar | Diagram-level question | Typical evidence |
   |---|---|---|
   | Security | Who authenticates callers? Is the edge protected (WAF / CloudFront)? Are data stores reachable only privately? Secrets/keys managed? | lens SEC questions, service skill "security" section |
   | Reliability | Queue/topic between producer and consumer? DLQ / retry on every async hop? Multi-AZ where the service needs it? Idempotent consumers? | lens REL questions, `aws-serverless` / `aws-resilience-lifecycle` |
   | Performance | Cache in front of hot reads (CloudFront, ElastiCache, DAX)? Right integration (event source mapping vs polling)? | lens PERF questions, service docs |
   | Cost | Serverless/on-demand tiers where traffic is spiky; provisioned where steady; lifecycle rules on buckets | lens COST questions |
   | Operational excellence | Metrics/logs/traces (CloudWatch, X-Ray), alarms → notification, deployment path | lens OPS questions |
   | Sustainability | Only when the user asks | framework SUS pillar |

5. **Write findings.** A finding names *what the brief lacks or has wrong*, the *source*, a severity, and whether
   it changes the picture:

   | Severity | Meaning |
   |---|---|
   | **must** | the source calls it a requirement / "should always"; the diagram would mislead without it (e.g. public API with no authorizer) |
   | **should** | recommended best practice the brief omits (DLQ, WAF, alarms) |
   | **could** | optimisation the source lists as optional; note only, rarely drawn |

6. **Stop** when the lens scenario and each service's skill/doc have been read once, or at 8 findings. This is a
   review, not a research project — typical budget is 10–15 tool calls.
7. **Hand-off.** Present the findings; for each the user picks **fix** (the Architect edits Components /
   Relationships — respecting the diagram budget) or **accept** (goes under Decisions as *known deviation*, with
   the source). The Drawer draws the decided architecture. **Unattended** (no user in the loop): apply *must*
   findings that add ≤ 1 component each; *should* and *could* are **presented only** — listed as
   "accepted for now" with their sources, never applied silently — and say so in the hand-off.

## 3. Section template (goes into the brief)

```markdown
## Architecture review
Lens: Serverless Applications Lens (read: landing page, "RESTful microservices" scenario). Skills: aws-serverless,
amazon-dynamodb. Tool: AWS Knowledge MCP. Date: 2026-09-12.

| # | Pillar | Finding | Source | Severity | Diagram |
|---|---|---|---|---|---|
| R1 | Security | API Gateway has no WAF; the lens scenario puts AWS WAF in front of public REST APIs | https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/… | should | + WAF badge on API Gateway group |
| R2 | Reliability | SQS → Lambda without a dead-letter queue | aws-serverless skill § "Event source mappings" | must | + DLQ node under SQS |
| R3 | Operational excellence | No alarm → notification path from CloudWatch | https://docs.aws.amazon.com/wellarchitected/latest/framework/ops… | should | + CloudWatch → SNS edge |

Decisions: R2 fixed (DLQ added). R1, R3 accepted for v1 — noted under Decisions with sources.
(While the user has not decided yet, write `Decisions (proposed): …` with fix/accept suggestions instead.)

Sources consulted (incl. no-finding): <url>, <url>, skill aws-serverless (SKILL.md, references/event-source-mappings.md)
```

## 4. What is not a review finding

- A preference without a source ("I'd use EventBridge here").
- Anything the diagram cannot show: IAM policy wording, code-level retries, instance sizing. At most one line
  under *Out of scope, consider*.
- Anything already satisfied in the brief — do not pad the table. Zero findings with a full *Sources consulted*
  list is a valid, good result.
- A source you did not open in this review. Quoting a URL from memory is fabrication; open it with
  `read_documentation` (or have its verbatim chunk from `search_documentation`) first.
- A finding whose only evidence is a skill's registry description. Descriptions say what a skill *covers*,
  not what AWS *recommends*.
