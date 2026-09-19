---
name: aws-tech-blog-writer
description: "Use when the user wants a post for the AWS Tech Blog (aws.amazon.com/ko/blogs/tech) about a project, PoC, or customer engagement built on AWS: a customer case study, an implementation walkthrough, or an architecture deep dive, even if they only say '블로그 글 써줘' with project documents attached; also when an existing AWS blog draft needs a style pass or a technical fact-check. The deliverable is a Word (.docx) file, built with the docx skill, with colour-coded placeholders wherever only the author knows the fact. Korean triggers: AWS 기술 블로그 글 작성, AWS 블로그 기고, 테크 블로그 초안, 프로젝트 소개 블로그, 고객 사례 블로그, PoC 블로그, 블로그 포스팅 써줘."
license: MIT
metadata:
  version: "2.0.0"
  source: "https://github.com/hi-space/hi-agent-skills"
---

# AWS Tech Blog Writer

Turn a finished project into a post that could go up on the AWS Tech Blog as-is: correct AWS facts, real
diagrams, house style, and honest placeholders where the author has to fill in what only they know. The
deliverable is `<work>/06-final.docx`; the Markdown it was built from stays next to it for WordPress.

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
- [ ] Stage 5  Fact-check | Lint (parallel)    -> 05-claims.md | lint report
- [ ] Stage 5b Style pass                      -> 06-final.md, placeholders.md
- [ ] Stage 6  Word document, built and verified -> 06-final.docx
```

Entering mid-way is normal: a user who already has a draft starts at Stage 1 with the draft registered
as source `S01`, and skips to Stage 5 once `01-facts.md` exists.

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

Fill `templates/prompt-drafter.md` and send it to a general-purpose subagent. The subagent reads exactly
seven files: `references/voice.md`, the relevant sections of `aws-blog-conventions.md`,
`references/placeholders.md`, `02-plan.md`, `01-facts.md`, `03-research.md`, and `diagrams/manifest.md`.
It does not see the sources, the digests, the brief, or this conversation, and it writes
`<work>/04-draft.md` in one pass.

The rules the prompt enforces, so you can check the result: every project statement ends with its fact
IDs in an HTML comment; every AWS statement rests on a research entry or is written so the fact-checker
can test it; numbers only from facts or research; placeholders in the exact `placeholders.md` form;
noun-phrase headings; subjects that can act; no passive with a known actor; no figurative nouns; AWS
names as AWS writes them; figures introduced, embedded, and captioned.

When the draft comes back, read it once as the target reader. If the argument order is wrong, tell the
same subagent what to move (SendMessage keeps its context); do not start editing sentences yet.

## Stage 5: Fact-check and lint, in parallel

**Fact-check**: fill `templates/prompt-fact-checker.md` and send it to a general-purpose subagent with
`04-draft.md`, `templates/claims.md`, and `references/verification.md`. It writes `<work>/05-claims.md`
and returns counts plus a corrections list (proposed sentence for each `corrected` claim, proposed
`[기술 검증 필요] (Cnn)` text for each `unverified` one). It never edits the draft.

**Lint**, while the fact-check runs: `python3 <skill-dir>/scripts/lint_blog.py <work>/04-draft.md`. It
reports, with line numbers, forbidden punctuation, wrong or unintroduced service names, images without
captions or files, code blocks without a language, malformed placeholders (errors), and the voice
findings (warnings): banned vocabulary, figurative nouns, abstract nouns as actors, passives with an
available actor, plain-form headings, connective overuse, long sentences.

**Style pass** (Stage 5b, one writer): with the corrections list and the lint report in hand, edit the
draft once following `references/voice.md` §5. Apply corrections first, then the voice rules paragraph
by paragraph, then rerun the lint until it exits 0 with the warnings you keep justified. Save as
`<work>/06-final.md`, write the placeholder list with `--placeholders-out <work>/placeholders.md`, and
run `lint_blog.py <work>/06-final.md --final`; it must exit 0 before Stage 6 because a leftover fact-ID
comment or a mis-coloured span goes straight into the author's Word copy. Then
`python3 <skill-dir>/scripts/check_claims.py <work>` confirms every unverified claim has its placeholder.

## Stage 6: Word document, built and verified

The author reads and comments in Word. Invoke the `docx` skill and follow its "Creating a new Word
document" workflow (docx-js); this skill's builder is the document script for that workflow:

```bash
node <skill-dir>/scripts/build_docx.js <work>
```

It reads `06-final.md`, writes `06-final.docx`, and appends `placeholders.md` as a final "남은
placeholder" section (`--no-appendix` turns that off). Placeholder spans become runs shaded in their
category colour, figures are embedded at text width with their caption, tables and code keep their
structure. Do not convert with `pandoc -o file.docx` instead: pandoc's DOCX writer drops the inline
colours and the author cannot see what is missing.

The script ends with a verification block comparing Markdown and DOCX: image count and, per placeholder
category, tags in the draft, in the document, and shaded runs. It exits 0 only when they agree. On
`FAIL` or `MISSING`, fix the draft or the image path and rebuild. Then read the opening from the outside,
`pandoc <work>/06-final.docx -t plain | head -80`, as the author would. If the post needs a construct
the builder prints as plain text, extend `scripts/build_docx.js` under the `docx` skill's `docx-js.md`
rules and keep the change in the skill.

## What to hand back

In the user's language: the path of `06-final.docx` (the deliverable) and of `06-final.md`, the
builder's verification summary, the figures with their `.brief.md`, the claims counts (verified /
corrected / unverified), the placeholder list by category, and any stage skipped or not reviewed. While
placeholders remain the post is ready for the author's pass, not ready to publish.

## Subagents

Digests, research, the draft, and the fact-check are subagent work: file in, file out, given only the
files named above and never the sources they do not need. Never fork yourself; a fork inherits this
whole context, which is the problem the split exists to avoid. Never let a subagent spawn subagents.
Diagram skills run their own Reviewer.

## Reference files

| File | Read it when |
|---|---|
| [voice.md](references/voice.md) | Drafter reads it whole; style pass follows its §5. Sentence rules, structure, before/after |
| [aws-blog-conventions.md](references/aws-blog-conventions.md) | Planning and drafting: post types and skeletons, title, opening, naming, figures, code, links, bios |
| [verification.md](references/verification.md) | Stage 3 research and Stage 5 fact-check: tool order, evidence rule, claim types, statuses |
| [diagrams.md](references/diagrams.md) | Stage 3: which diagram skill, how to brief it from the facts, how to verify the picture |
| [placeholders.md](references/placeholders.md) | Any time a fact is missing: four categories, exact HTML, how to word the request |
| [templates/](templates/) | brief, source-digest, facts, plan, research, claims, diagram-manifest, blog-post, prompt-drafter, prompt-fact-checker |

## Scripts

| Script | Purpose |
|---|---|
| `scripts/init_workspace.py <slug> [--dir <path>]` | Create `<work>` and copy templates |
| `scripts/ingest_sources.py <work>` | Convert PDF / DOCX / PPTX / drawio in `sources/` to text |
| `scripts/lint_blog.py <draft.md> [--final] [--placeholders-out <file>] [--strict]` | Punctuation, naming, image, code, placeholder, and voice checks |
| `scripts/check_claims.py <work>` | Validate `05-claims.md` and match unverified claims to draft placeholders |
| `scripts/build_docx.js <work> [--out <file>] [--no-appendix]` | Build and verify `06-final.docx` from `06-final.md` with docx-js |
