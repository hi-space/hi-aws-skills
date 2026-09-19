# Verification: research (Stage 3) and fact-check (Stage 5)

Both stages open AWS documentation and record what it says next to a URL. Research runs before the
draft and answers the general technical questions the plan raises; the fact-check runs after the draft
and tests every technical sentence the drafter wrote. They share the tool order, the evidence rule, and
the source ranking below.

## Shared rules

**Tool order.**
1. `aws-docs` MCP: `search_documentation`, then `read_documentation` or `read_sections`. Developer or
   User Guide for behaviour, API Reference for names and parameters, "What's New" for launch dates and
   initial regions, the service quotas page for limits, the pricing page for the pricing model.
2. `aws-mcp` proxy (`aws___search_documentation`, `aws___read_documentation`,
   `aws___get_regional_availability`) when `aws-docs` is unavailable or for regional availability.
3. `WebFetch` for GitHub READMEs, release notes, vendor documentation (Anthropic model names, MCP
   specification), AWS blog posts.
4. `context7` for SDK and framework APIs (Strands Agents, LangGraph, boto3) the AWS docs do not cover.
5. `deep-research` skill only for a question that needs synthesis across several non-AWS sources.

**Evidence rule.** A search snippet is not evidence. Open the page, find the passage, quote or closely
paraphrase it, record the URL and the date opened. If the page is truncated, paginate with
`start_index` or use `read_sections`.

**Source ranking for AWS behaviour.** Official documentation > AWS "What's New" and AWS blog posts >
re:Post answers by AWS staff > issues in AWS-owned repos > third-party blogs. A capability confirmed
only by a third-party source is `unverified`.

**Dates and regions.** Note `preview` banners and region lists. If the project ran in `ap-northeast-2`,
check that region. A feature announced after the project's timeline is stated as such or left out.

## Stage 3: research, scoped by the plan

Input: `02-plan.md` (column "검증할 주장" and the open questions it kept) and `01-facts.md`'s
`## Open questions`. Sort each question:

- **Project-specific** (this customer's numbers, choices, schedule, people, results): nobody but the
  author knows. Do not research; the drafter writes a placeholder (`placeholders.md`).
- **General technical** (how an AWS service, SDK, or protocol behaves): research it.
- Both (`Gateway는 SigV4로 Lambda를 호출한다`, said by the team): research the AWS part, keep the project
  part as a fact with its source ID.

Research only what a planned section will state. A sentence that says `Gateway는 MCP 툴 호출을 Lambda로
전달합니다` needs one page; a paragraph on the auth chain needs the auth page, the target page, and the
IAM example; a comparison table needs a source per cell. Stop when every general technical question has
a status. Interesting is not needed, and every extra page is a page Stage 5 re-verifies.

Record in `03-research.md` (template `templates/research.md`), one entry per question:

```
### R03  AgentCore Gateway의 Lambda 타깃 인증 방식
Raised by: F17 (S02 32:10) / plan §4.2
Finding: Gateway invokes Lambda targets with its own execution role, which needs lambda:InvokeFunction
         on the target ARN. Inbound auth to the Gateway (JWT or IAM) is separate.
Source:  https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-target-lambda.html (opened 2026-09-19)
Quote:   "..."
Status:  answered | partial | unanswered (drafter writes [기술 검증 필요])
```

Keep `Raised by`: when the author later corrects F17, this is how you find the entries that depended on it.

## Stage 5: fact-check, in a fresh context

The drafter believes every sentence they wrote, so the fact-check runs as a general-purpose subagent
that receives only `04-draft.md`, `templates/claims.md`, and this file (prompt in
`templates/prompt-fact-checker.md`). It writes `05-claims.md` and returns a corrections list. It never
edits the draft; the style pass applies corrections so that one writer touches the text.

**What is a claim.** Anything about AWS, a vendor product, an SDK, or a protocol that a reader could
test and find false: capabilities, mechanisms (what authenticates what, what is synchronous), names and
identifiers (service names, API operations, parameters, model IDs, CLI flags, IAM actions), limits and
numbers attributed to AWS, availability (regions, preview vs GA, dates), every code block, comparisons,
security statements (`데이터는 계정을 벗어나지 않습니다`). Not a claim: what the project did, chose, or
measured (facts with source IDs), opinions marked as the team's, plans. A project fact that asserts an
AWS behaviour is both; verify the AWS part.

**Procedure.**
1. Read the draft top to bottom and fill `05-claims.md`: ID, the sentence verbatim, section, type, the
   fact or research IDs it rests on.
2. Verify each claim with the tool order above. Record URL, date, evidence.
3. Set the status:
   - `verified`: the page says it. Note where a link belongs in the draft (first mention or `참고 자료`).
   - `corrected`: the page says something different. Put the old and the proposed new sentence in
     `Note`. Do not edit the draft.
   - `unverified`: no official page confirms it after two well-phrased searches and one `recommend`
     call. Propose a `[기술 검증 필요]` placeholder that starts with the claim ID (`(C08)`), names what to
     check, and gives the sentence to restore once confirmed. Softening to `~로 알려져 있습니다` is not
     verification.
   - `out-of-scope`: a non-AWS product confirmed by its vendor's documentation (record that URL).
4. Return the corrections list: every `corrected` and `unverified` row with the proposed wording. The
   style pass applies it, then `python3 <skill-dir>/scripts/check_claims.py <work>` confirms every row
   has a status and a URL and every `unverified` claim has a matching placeholder in the draft.

**Code blocks.** Identify the API or CLI surface each block uses, open the reference page for each
operation, check operation names, required parameters, and return shapes. Code copied from the
project's repository is still checked; a snippet that depends on the project's helpers must say so.
Code that cannot be verified becomes a placeholder describing the intended call.

**Claims people get wrong in this domain.** Service prefixes and sub-service names (`Amazon Bedrock
AgentCore Gateway`, never `Bedrock Gateway`); inbound versus outbound authentication of a component;
regional availability on the project's dates; model IDs and vendor names (`Claude Opus 5`, cross-region
inference profile IDs; if the source only says "Opus", placeholder the ID); "not used for training"
statements (quote the exact wording); quotas quoted as fixed when they are adjustable; prices without a
date and a link; open-source versions and licenses; console layouts (describe the action, not the
button).
