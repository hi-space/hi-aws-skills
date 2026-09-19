# Research discipline — stage 2

Stage 2 ("Research ★") turns the brief's intended AWS features into **verified facts** before any page is written. The output is `artifacts/02-feature-facts.md`. This is a ★ gate: in `staged` mode the SA signs off; in `oneshot` mode the same pass conditions are checked and the run stops on violation.

## Run it as parallel cells

Research fans out in parallel (one agent per cell; INV-3 failure isolation):

| Cell | One per | Writes | Why |
|---|---|---|---|
| Company | engagement | `artifacts/02a-company-context.md` | Industry, scale, public tech stack, domain vocabulary — scenarios and datasets must read as the customer's own story. |
| Audience | engagement | `artifacts/02b-audience-context.md` | What each target role does day-to-day, their tools, their prior knowledge — calibrates difficulty and jargon (GATE-3b input). |
| Technology | service/feature group in `brief.aws.services` | rows merged into `02-feature-facts.md` | The GA/region/label verification below. |

A merge step assembles the technology rows into `02-feature-facts.md` (cells in == rows out, INV-5). The company/audience cells follow the same labeling rules: public facts you found are `documented`, your inferences are `assumed` — never present an assumed customer fact as real.

The reason this stage exists: AWS capabilities — GA vs preview, regional availability, exact feature names — change often and cannot be answered from memory. A workshop that hands participants a feature that isn't in their region, or calls a preview "GA", fails in the room. See GATE-2a / GATE-2b / GATE-2c in `pipeline-contract.md`.

## What to produce per feature

For every AWS feature a scenario relies on, record:

1. **Canonical name** — the exact current product/feature name (resolve ambiguity — see below).
2. **Status** — GA / preview / not-yet-available, at the time of checking.
3. **Region availability** — specifically whether it is available in `brief.region`. Not "generally available somewhere" — available *there*.
4. **Confidence label** — one of the four below.
5. **`confirmed_date`** — the date you verified it.
6. **`valid_until`** — default `confirmed_date + 14 days`. After this, the fact must be re-checked before GATE-5 (assembly) and GATE-8 (handoff) — new services move regions frequently (GAP-05).
7. **Design implication** — one line on what this means for the scenario (e.g. "must run in us-east-1", "use classic Bedrock KB instead", "demo only, not hands-on because quota approval takes days").

## The four confidence labels (use these exact words)

| Label | Meaning | Allowed source |
|---|---|---|
| **verified** | I actually confirmed it — ran it, or saw it in the live console / an authoritative regional table, this session. | Live check, AWS Regional Services List, console. |
| **documented** | The official AWS documentation states it, but I did not run it. | AWS docs, release notes. |
| **assumed** | My inference, not confirmed. Must be resolved before generation, or the scenario must not depend on it. | — |
| **needs-check** | Could not verify (no web access, ambiguous docs). Explicitly flagged, never disguised as fact. | — |

**Never promote `assumed`/`needs-check` to `verified`.** These labels propagate forward and must appear as a column in the stage-3 scene tables (INV-6) — not buried in prose. A scene table without labels fails the gate.

## How to verify (in order of trust)

1. **Live / authoritative**: the AWS Regional Services List, the service console in the target region, `aws` CLI availability calls, or an AWS documentation MCP if available. → `verified`.
2. **Official docs / release notes / What's New**: authoritative for existence and stated regions, but you didn't run it. → `documented`.
3. **Web search**: use to find the doc/announcement, then cite the primary AWS source — don't stop at a blog's paraphrase. Label by what the primary source supports.
4. **No access**: label everything `needs-check`, say so plainly in the artifact, and list each `needs-check` item in the pre-generation to-do (GATE-2c). Do not invent a plausible answer.

> **Running on Amazon Bedrock (3P)?** The WebSearch tool does not exist there (documented: Claude Code Bedrock docs). Verify via **WebFetch on known AWS URLs** (Regional Services List, docs pages, What's New), an **AWS docs MCP**, or the **`aws` CLI** instead. Everything else in this skill — MCP tools (incl. Chrome CDP), subagents, hooks, gates, `claude -p` — is client-side and works on Bedrock. Model aliases (`haiku` etc.) resolve to Bedrock model IDs that must be enabled in the account; pin `ANTHROPIC_DEFAULT_*_MODEL` for team rollouts.

Prefer a managed service the customer may not know exists over hand-rolling: if an AWS service overlaps what the scenario builds, note it — with region / preview / constraints — even when the scenario ends up not using it.

## Naming ambiguity (GATE-2b)

One name can mean two things (classic example: "Knowledge Base" — Amazon Bedrock Knowledge Bases vs an AgentCore Managed KB; these have different regional availability). When a name is ambiguous:
- Pin the exact interpretation and cite the source that disambiguates.
- Record both the chosen meaning and the rejected one, so a later reader doesn't silently re-resolve it the other way.

## Region mismatch handling (GATE-2a)

If a feature a scenario needs is **not** available in `brief.region`, the gate does not pass on "note it and move on." Provide a resolution:
- an alternate region for that portion, or
- an alternate service that is available there, or
- a scope reduction (e.g. demo-only instead of hands-on),

and record the decision (as a `brief` amendment in `artifacts/00-amendments.md` or in the feature-facts design implication). Only then does stage 2 pass.

## Output shape (`artifacts/02-feature-facts.md`)

A table plus per-feature design implications, e.g.:

```md
| Feature | Canonical name | Status | In <region>? | Confidence | confirmed_date | valid_until | Design implication |
|---|---|---|---|---|---|---|---|
| Vector search | Amazon Bedrock Knowledge Bases | GA | yes | verified | 2026-08-28 | 2026-09-11 | OK for hands-on in-region |
| Managed KB | AgentCore Managed KB | preview | NO | verified | 2026-08-28 | 2026-09-11 | Not in-region → use classic Bedrock KB (row above) |
```

The stage-3 blueprint and stage-4 scenes read this file (INV-1). They must not restate a fact more confidently than its label here.
