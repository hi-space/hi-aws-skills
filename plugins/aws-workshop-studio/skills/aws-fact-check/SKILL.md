---
name: aws-fact-check
description: Verify AWS service facts fresh — GA vs preview, regional availability, exact feature names — and label every claim by confidence (verified / documented / assumed / needs-check). Use for any "is X GA?", "is X available in region Y?", "what is this feature actually called?" question, and for fact-checking AWS claims in a doc before it goes to a customer. Triggers: "fact-check", "is it GA", "available in Seoul/region", "리전 되나", "GA야?", "사실 확인".
---

# AWS Fact Check

Answer AWS capability questions with **fresh verification, never memory**. This is the standalone form of the workshop pipeline's research stage — usable on its own for any customer-facing claim.

> Shared reference: the full discipline lives at the plugin root — `references/research-discipline.md`. Read it first; this file is the entry point, not a replacement.

## Procedure

1. **Pin the canonical name.** One name can mean two features (e.g. "Knowledge Base": Amazon Bedrock Knowledge Bases vs AgentCore Managed KB — different regions). Record the chosen interpretation and the rejected one.
2. **Verify, in order of trust:** live/authoritative (AWS Regional Services List, console in the target region, `aws` CLI, AWS docs MCP) → official docs / What's New → web search only to *find* the primary AWS source, never to stop at a paraphrase.
3. **Label every claim** with exactly one of: **verified** (checked live this session) / **documented** (official docs, not run) / **assumed** (inference) / **needs-check** (could not verify — say so, never disguise).
4. **Stamp freshness:** `confirmed_date` + `valid_until` (default +14 days). Regional tables for new services change frequently — past `valid_until`, re-verify before reuse.
5. **If the answer is "not available there":** don't stop at no — offer the resolution (alternate region, alternate service, scope reduction), with its costs stated.

## Output shape

A table row per fact:

| Claim | Canonical name | Status | In \<region\>? | Confidence | confirmed_date | valid_until | Implication |
|---|---|---|---|---|---|---|---|

## Rules

- Never promote assumed/needs-check to verified.
- Distinguish "GA somewhere" from "available in the asked region" — the question is always the region.
- Prefer pointing at an existing managed service over hand-rolling; state region/preview/constraints alongside.
