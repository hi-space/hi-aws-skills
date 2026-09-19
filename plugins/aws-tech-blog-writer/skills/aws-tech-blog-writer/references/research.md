# Phase 2: Gap analysis and deep research

## Two bins

After Phase 1, `01-facts.md` has an `## Open questions` list. Sort each item before doing anything.

**Project-specific**: only the people who did the project can answer. Signals: it concerns this
customer's data, choices, numbers, schedule, people, or results. Examples: "how many tables does the HIS
DB have", "why did the team pick Fargate over Lambda for the gateway", "did the pilot start". Action:
write a placeholder in the plan and later the draft (`references/placeholders.md`). Do not research
these; a search result about another company's Fargate decision is not this customer's reason.

**General technical**: true for anyone using the service. Signals: it is about how an AWS service, SDK,
protocol, or open-source tool behaves. Examples: "what authentication does AgentCore Gateway use toward a
Lambda target", "does Bedrock support Codex/GPT models in ap-northeast-2", "what does the OIDC discovery
document need to contain". Action: research, record, cite.

An item can be both ("the team says Gateway calls Lambda with SigV4" is a project statement about an AWS
behaviour). Research the AWS part; keep the project part as a fact with its source ID.

## Tool order

1. **`aws-docs` MCP** (`search_documentation` then `read_documentation` / `read_sections`). Official
   documentation is what Phase 6 will cite, so research from it directly. Prefer the Developer Guide or
   User Guide for behaviour, the API Reference for parameter names, "What's New" posts for launch dates
   and regions, and the service quotas page for limits.
2. **`aws-mcp` proxy tools** (`aws___search_documentation`, `aws___read_documentation`,
   `aws___get_regional_availability`) when the `aws-docs` server is unavailable, or for regional
   availability questions specifically.
3. **`deep-research` skill** when a question needs synthesis (compare AgentCore Gateway with an
   open-source MCP gateway; summarise how three teams handle multi-tenant cost attribution) or when the
   material is outside AWS documentation (a protocol spec, an academic result). Give it a tight question
   and ask for an evidence table; it writes to `<work>/research/`.
4. **`WebFetch`** for GitHub READMEs, release notes, vendor documentation (Anthropic model names, MCP
   specification), and AWS blog posts. Fetch the page; do not rely on a search snippet.
5. **`context7`** for SDK and framework API details (Strands Agents, LangGraph, boto3) when the AWS
   documentation does not cover them.

Search results are leads, not evidence. A finding is recorded only after the page was opened and the
relevant passage read.

## Recording: `<work>/02-research.md`

One entry per question:

```
### R03  AgentCore Gateway → Lambda target 인증 방식
Bin: general technical      Raised by: F17 (S02 transcript, 32:10)
Finding: Gateway invokes Lambda targets with its own execution role; the role needs lambda:InvokeFunction
         on the target ARN. Inbound auth to the Gateway is separate (JWT or IAM).
Source:  https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-target-lambda.html (opened 2026-09-19)
Quote:   "..." (one or two lines, verbatim)
Use in post: §4.2 구현 상세, sentence about how existing systems were exposed without modification.
Status: answered | partial | unanswered → placeholder
```

Keep the `Raised by` link: when the author later corrects fact F17, you need to know which research
entries depended on it.

## Depth

Research the questions the post will actually make claims about, at the depth the post needs. A
sentence that says "Gateway는 MCP 툴 호출을 Lambda로 전달합니다" needs one documentation page. A
paragraph explaining the auth chain end to end needs the auth page, the target page, and probably the
IAM policy example. A comparison table needs a source per cell.

Stop when every general-technical open question has a status. Do not research topics the post does not
raise; interesting is not the same as needed, and every extra page is a page Phase 6 has to re-verify.

## Source quality

Rank for AWS behaviour: official documentation > AWS "What's New" and AWS blog posts > AWS re:Post
answers by AWS staff > GitHub issues in AWS-owned repos > third-party blogs. Never cite a third-party
blog for an AWS capability if documentation exists; if only a third-party source exists, the claim is
`unverified` in Phase 6 and becomes a `[기술 검증 필요]` placeholder that names that source.

Dates matter. AWS services change monthly. Note the date you opened each page; if a page says "preview"
or a feature was announced after the project's timeline, say so in the post or leave it out.
