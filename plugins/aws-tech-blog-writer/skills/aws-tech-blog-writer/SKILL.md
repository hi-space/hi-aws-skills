---
name: aws-tech-blog-writer
description: "Use when the user wants a post for the AWS Tech Blog (aws.amazon.com/ko/blogs/tech) about a project, PoC, or customer engagement built on AWS: a customer case study, an implementation walkthrough, or an architecture deep dive, even if they only say '블로그 글 써줘' with project documents attached. The deliverable, produced through the sibling skill aws-blog-review at the end of the pipeline, is a Word (.docx) file with colour-coded placeholders wherever only the author knows the fact. Korean triggers: AWS 기술 블로그 글 작성, AWS 블로그 기고, 테크 블로그 초안, 프로젝트 소개 블로그, 고객 사례 블로그, PoC 블로그, 블로그 포스팅 써줘. A finished draft that only needs a review goes to the sibling skill aws-blog-review."
license: MIT
metadata:
  version: "3.0.1"
  source: "https://github.com/hi-space/hi-aws-skills"
---

# AWS Tech Blog Writer

Turn a finished project into a post that could go up on the AWS Tech Blog as-is: correct AWS facts, real
diagrams, house style, and honest placeholders where the author has to fill in what only they know. This
skill produces the draft (`<work>/04-draft.md`) and hands it to the sibling skill `aws-blog-review`, which
checks it, revises it, and builds the Word file the author receives. Nothing this skill writes goes to
the author unreviewed.

`<skill-dir>` is the directory containing this SKILL.md. Every artifact lives in `<work>` (default
`./blog-work/<slug>/`), so a later session or a subagent picks the job up from files, not from
conversation history.

## How the work is split

The agent that reads a hundred pages of sources should not be the agent that writes the prose. In the
first version of this skill one context did everything and the draft quality dropped with every file
it had read. Now the main agent orchestrates and verifies; reading and writing happen in fresh
subagents that receive only the files they need. Two groups of stages run in parallel.

```
Blog Progress (copy into your reply and keep it updated):
- [ ] Stage 1  Brief and fact base            -> 00-brief.md, sources/*.digest.md, 01-facts.md
- [ ] Stage 2  Plan                            -> 02-plan.md                        [approval gate]
- [ ] Stage 3  Research | Diagrams (parallel)  -> 03-research.md | diagrams/manifest.md, images/
- [ ] Stage 4  Draft, fresh context            -> 04-draft.md
- [ ] Stage 5  Hand-off to aws-blog-review     -> review-report.md, revised.md, <제목>.docx (that skill's R1 to R5)
```

Entering mid-way is normal: a user who already has a draft that needs rewriting starts at Stage 1 with
the draft registered as source `S01` and continues through Stage 4, because a rewrite needs the fact
base and the plan. A finished draft that needs a review and a corrected version, not a rewrite, skips
this skill entirely and goes to the sibling skill `aws-blog-review` (`../aws-blog-review/SKILL.md`),
which reuses this skill's lint, references, and builder.

## Stage 1: Brief and fact base

`python3 <skill-dir>/scripts/init_workspace.py <slug>` creates `<work>` with the templates.

Fill `<work>/00-brief.md` (template `templates/brief.md`) from what the user gave you: what was built
and for whom, why a reader should care (this becomes the thesis), the post type (A case study, B
walkthrough, C deep dive; skeletons in `references/aws-blog-conventions.md` §1), and the source
registry with an ID per file (`S01`, `S02`, ...). Mark each answer stated, inferred, or assumed. Ask the
user only what changes the writing, in one message, and only if they are reachable; unattended, write
assumptions and continue.

Convert non-text sources: `python3 <skill-dir>/scripts/ingest_sources.py <work>` turns PDF, DOCX, PPTX,
and `.drawio` files into `<work>/sources/text/`. Video without a transcript is registered `not readable`.

Digest every source with parallel general-purpose subagents, one per source, each given only the file
path and `templates/source-digest.md`, writing only `<work>/sources/<ID>.digest.md`. Do not read the
sources yourself beyond what the brief needs; the digests are the fact base's input and your context
stays free for orchestration.

Consolidate the digests into `<work>/01-facts.md` (template `templates/facts.md`): a numbered fact
table with source IDs and a confidence column (`stated` / `inferred` / `conflict`), the timeline, the
component inventory (every AWS service and external system, with its role), people and organizations
that may be named, and `## Open questions`. The fact table is the only thing the draft may state as
true about the project. Digests of two sources that contradict each other produce a `conflict` row,
which the draft turns into a placeholder.

## Stage 2: Plan

Write `<work>/02-plan.md` (template `templates/plan.md`) from `01-facts.md` and the skeleton for the
post type. Per section: the one sentence the reader should be able to say afterwards, the fact IDs it
draws on, the figures it needs, code it shows, the AWS claims it will make (these become research
questions), and a word budget. Fix the title (a noun phrase with the primary service's full name), the
opening paragraph, the author list, and the disclaimer.

Two checks: walk the plan as the target reader and cut any section that does not answer a question
they would have; every section must map to facts or to a named placeholder. If the user is reachable,
present the plan and wait. Unattended, proceed and say in the report that the plan was not reviewed.

## Stage 3: Research and diagrams, in parallel

Start both at once; neither depends on the other.

**Research** (`references/verification.md`, "Stage 3"): sort the plan's claims and the facts' open
questions into project-specific (placeholder, do not research) and general technical (research with
the `aws-docs` MCP first). Record each finding with the URL you actually opened in
`<work>/03-research.md` (template `templates/research.md`). Research only what a planned section will
state. This can run as a subagent given the plan, the open questions, and `verification.md`.

**Diagrams** (`references/diagrams.md`): at least one architecture figure of what was built, usually one
concept figure. Architecture goes through the `aws-drawio-diagram` skill briefed from the component
inventory and the request paths in `01-facts.md`; concept figures through `aws-diagram-design`. After
each skill reports ready, open the PNG, list every node and edge you see, and check them against the
inventory. A service in the picture that is not in the facts, or a component the picture omits, is a
defect regardless of the diagram skill's own validator. Record the check in `<work>/diagrams/manifest.md`
and copy shipping PNGs into `<work>/images/` as `figN-<name>.png`. Screenshots the author must take are
`[이미지 필요]` placeholders with the caption already written.

## Stage 4: Draft, in a fresh context

Fill `templates/prompt-drafter.md` and send it to the plugin's `blog-drafter` agent (Agent tool,
`subagent_type: aws-tech-blog-writer:blog-drafter`). The agent definition in `agents/blog-drafter.md`
holds its rules and limits it to Read and Write, so it cannot search the web or open the sources even if
it wanted to; the prompt carries only the paths and the variables of this post. The agent reads exactly
eight files: `references/voice.md`, the relevant sections of `aws-blog-conventions.md`,
`references/placeholders.md`, `02-plan.md`, `01-facts.md`, `03-research.md`, `diagrams/manifest.md`, and
the skeleton `templates/blog-post.md`. It does not see the sources, the digests, the brief, or this
conversation, and it writes `<work>/04-draft.md` in one pass (the file does not exist before then).

The rules the agent enforces, so you can check the result: every project statement ends with its fact
IDs in an HTML comment; every AWS statement rests on a research entry or is written so the fact-checker
can test it; numbers only from facts or research; placeholders in the exact `placeholders.md` form;
noun-phrase headings; subjects that can act; no passive with a known actor; no figurative nouns; AWS
names as AWS writes them; figures introduced, embedded, and captioned.

When the draft comes back, read it once as the target reader. If the argument order is wrong, tell the
same subagent what to move (SendMessage keeps its context); do not start editing sentences yet.

## Stage 5: Hand-off to aws-blog-review

The draft is finished but unchecked: no AWS statement has been tested against documentation, first
mentions are unlinked wherever `03-research.md` had no URL for the service, and only its writer has read
the prose. Everything from here (lint, fact-check, story review, report, revision, Word build) is the
sibling skill `aws-blog-review`, which runs the plugin's `blog-fact-checker` and `blog-reviewer` agents in
fresh contexts and applies their findings in one revision pass. Invoke it now, in this session, and
follow `../aws-blog-review/SKILL.md` from R1 with two differences that come from working inside a writer
work directory:

```bash
python3 <skill-dir>/../aws-blog-review/scripts/prepare_review.py <work>/04-draft.md --in-place
```

- R1 runs with `--in-place`: `<work>` stays the work directory, `draft.md` is a copy of `04-draft.md`
  (the writer's artifact is not edited), `images/` is used where it is.
- The fact-checker prompt gets `<facts: <work>/01-facts.md>`, so sentences the fact table states with a
  source ID are project facts, not claims, unless they also assert AWS behaviour.

The review skill writes `review-report.md`, `revised.md`, `placeholders.md`, and `<제목>.docx` (the post
title from the first H1) into `<work>`. Never build a Word file from `04-draft.md`: a document that
looks finished gets forwarded to the author, and this one has not been checked. If the user stops the
work before the review, hand back `04-draft.md` as Markdown and say that it is unreviewed.

## What to hand back

In the user's language: what the review skill's "What to hand back" lists (verdict, report, revised
Markdown, the `<제목>.docx` deliverable, before-and-after counts, remaining placeholders), plus the
figures with their `.brief.md`, the plan's open questions the author still owes, and any stage skipped
or not reviewed. While placeholders remain the post is ready for the author's pass, not ready to publish.

## Subagents

Digests, research, and the draft are subagent work: file in, file out, given only the files named
above and never the sources they do not need. The draft runs as this plugin's own agent
(`agents/blog-drafter.md`), whose tool list the harness enforces; digests and research run as
general-purpose subagents; the fact-checker and the story reviewer are the review skill's agents and run
in Stage 5 under its instructions. If the plugin agents are not
registered (the skill copied without its plugin), send the same prompt to a general-purpose subagent with
the agent body prepended. Never fork yourself; a fork inherits this whole context, which is the problem
the split exists to avoid. Never let a subagent spawn subagents. Diagram skills run their own Reviewer.

## Agents

| Agent | Stage | Tools | Reads | Writes |
|---|---|---|---|---|
| [blog-drafter](../../agents/blog-drafter.md) | 4 | Read, Write | voice, conventions, placeholders, plan, facts, research, manifest, skeleton | `04-draft.md` |
| [blog-fact-checker](../../agents/blog-fact-checker.md) | 5, via aws-blog-review R2 | Read, Write, WebFetch, aws-docs and aws-mcp documentation tools | verification, claims template, draft, facts | `05-claims.md` |
| [blog-reviewer](../../agents/blog-reviewer.md) | 5, via aws-blog-review R2 | Read, Write | review rubric, conventions §1 §3 §6 §10, draft, PNGs | `story.md` |

## Reference files

| File | Read it when |
|---|---|
| [voice.md](references/voice.md) | Drafter reads it whole; the review skill's revision pass follows its §5. Sentence rules, structure, before/after |
| [aws-blog-conventions.md](references/aws-blog-conventions.md) | Planning and drafting: post types and skeletons, title, opening, naming, figures, code, links, bios |
| [verification.md](references/verification.md) | Stage 3 research, and the fact-check the review skill runs in Stage 5: tool order, evidence rule, claim types, statuses |
| [diagrams.md](references/diagrams.md) | Stage 3: which diagram skill, how to brief it from the facts, how to verify the picture |
| [placeholders.md](references/placeholders.md) | Any time a fact is missing: four categories, exact HTML, how to word the request |
| [templates/](templates/) | brief, source-digest, facts, plan, research, claims (filled by the review skill's fact-checker), diagram-manifest, blog-post, prompt-drafter |

## Scripts

| Script | Purpose |
|---|---|
| `scripts/init_workspace.py <slug> [--dir <path>]` | Create `<work>` and copy templates |
| `scripts/ingest_sources.py <work>` | Convert PDF / DOCX / PPTX / drawio in `sources/` to text |
| `scripts/lint_blog.py <draft.md> [--final] [--placeholders-out <file>] [--strict]` | Punctuation, naming, first-mention links (E8), image, code, placeholder, and voice checks; run by aws-blog-review R2 and R4 |
| `scripts/check_claims.py` | Validate `05-claims.md` and match unverified claims to the revised draft's placeholders; run by aws-blog-review R4 |
| `scripts/build_docx.js` | Build and verify the Word file with docx-js, named after the post title; run by aws-blog-review R5, never on `04-draft.md` |
