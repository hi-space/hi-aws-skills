# Phase 6: Fact-check against AWS documentation

The writer who drafted a sentence believes it. The fact-check exists because belief is not evidence and
because AWS changes: a limit that was true in the training data is a support ticket for a reader who
copies it. Run this phase against the draft as a reader would, sentence by sentence, and with a fresh
context when possible.

## What is a claim

Anything about AWS, a vendor product, an SDK, or a protocol that a reader could test and find false:

- Capabilities: "Bedrock에서 Codex 모델을 호출할 수 있습니다", "AgentCore Memory는 장기 기억을 제공합니다".
- Mechanisms: how authentication flows, what a service calls, what is synchronous.
- Names and identifiers: service names, API operations (`InvokeAgentRuntime`), parameters, model IDs,
  CLI flags, IAM actions.
- Limits and numbers: quotas, timeouts, sizes, prices, latencies attributed to AWS.
- Availability: regions, preview vs GA, launch dates.
- Code: every code block is a claim about an API surface.
- Comparisons: "오픈소스 게이트웨이와 달리 ~".
- Security statements: "데이터는 계정을 벗어나지 않습니다", "모델 학습에 사용되지 않습니다".

Not a claim: what the project did, chose, or measured (those are facts with source IDs), opinions
clearly marked as the team's, and the author's plans.

A project fact that asserts an AWS behaviour is both. "저희는 Gateway가 SigV4로 Lambda를 호출하도록
구성했습니다" is fact F17 (they configured it) and claim C08 (Gateway can do that). Verify C08.

## Procedure

1. Read the draft top to bottom and fill `<work>/05-claims.md` (template `templates/claims.md`): ID,
   the sentence (verbatim), section, claim type, and the fact or research IDs it rests on.
2. For each claim, search with the `aws-docs` MCP (`search_documentation` with a specific phrase, then
   `read_documentation` or `read_sections`). Open the page. Find the passage. Quote or closely paraphrase
   it in the `Evidence` column with the URL and the date opened.
3. Set status:
   - `verified`: the page says it. Add the URL to the draft as a link where a reader would want it
     (first mention of the capability, or in `더 알아보기`).
   - `corrected`: the page says something different. Fix the draft sentence, quote the old and new
     wording in the `Note` column, and re-read the paragraph; a corrected fact often breaks a neighbouring
     sentence.
   - `unverified`: no official page confirms it after two well-phrased searches and one `recommend`
     call. Replace the sentence's assertion with a `[기술 검증 필요]` placeholder that starts with the claim
     ID (`[기술 검증 필요] (C08) ...`), names what to check, and gives the sentence to restore once
     confirmed. `check_claims.py` matches unverified rows to placeholders by that ID. Do not soften the sentence into "~로 알려져 있습니다";
     hedging is not verification.
   - `out-of-scope`: the claim is about a non-AWS product and its vendor documentation confirms it (record
     the vendor URL). Anthropic model names, MCP specification, Terraform behaviour go here.
4. Run `python3 <skill-dir>/scripts/check_claims.py <work>`. It fails if a row lacks a status or URL, or
   if an `unverified` row has no matching placeholder in the draft.
5. Report counts by status in the final hand-back.

## Reading documentation well

- The Developer Guide describes behaviour; the API Reference is authoritative for names and parameters;
  the "What's New" post gives the launch date and initial regions; the service quotas page gives limits;
  the pricing page gives the pricing model (quote the model, not a number, unless the post's date is
  stated next to it).
- A search snippet is not evidence. Open the page. If the tool truncates, paginate with `start_index` or
  use `read_sections` for the section the search suggested.
- Version and date: note "preview" banners and "this feature is available in the following Regions"
  lists. If the project ran in `ap-northeast-2` and the page lists regions, check that one.
- When two pages disagree (common right after a launch), cite the more specific one and mention the
  discrepancy in `Note`.

## Claims people get wrong in this domain

Check these deliberately when they appear:

- Service prefixes and sub-service names (`Amazon Bedrock AgentCore Gateway`, not `Bedrock Gateway`).
- Which authentication a component accepts inbound versus uses outbound (Gateway inbound JWT/IAM versus
  Gateway's execution role invoking Lambda).
- Whether a capability is regional and whether it exists in the project's region on the project's dates.
- Model IDs and model names: vendor naming (`Claude Opus 5`), Bedrock model ID format, cross-region
  inference profile IDs. If the source only says "Opus", placeholder the ID.
- "Data is not used for training" statements: quote the exact documentation wording.
- Quotas quoted as fixed numbers: many are adjustable; say so.
- Pricing: never a number without the date and a link; prefer describing the dimension (per token, per
  request, per hour).
- Open-source component versions and licenses when the post recommends them.
- Screenshots described in the text that show a console layout: the console changes; describe the action,
  not the button position.

## Code blocks

For each code block: identify the API or CLI surface it uses, open the reference page for each
operation, and check operation names, required parameters, and return shapes. Code copied from the
project's repository is still checked; a snippet that works only with the project's helper functions must
say so. Code that cannot be verified becomes a placeholder describing the intended call, not an
approximate snippet.
