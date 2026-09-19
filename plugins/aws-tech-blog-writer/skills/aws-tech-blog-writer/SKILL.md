---
name: aws-tech-blog-writer
description: "Use when the user wants a post for the AWS Tech Blog (aws.amazon.com/ko/blogs/tech) about a project, PoC, or customer engagement built on AWS: a customer case study, an implementation walkthrough, or an architecture deep dive, even if they only say '블로그 글 써줘' with project documents attached; also when an existing AWS blog draft needs a style pass or a technical fact-check. The deliverable is a Word (.docx) file, built with the docx skill, with colour-coded placeholders wherever only the author knows the fact. Korean triggers: AWS 기술 블로그 글 작성, AWS 블로그 기고, 테크 블로그 초안, 프로젝트 소개 블로그, 고객 사례 블로그, PoC 블로그, 블로그 포스팅 써줘."
license: MIT
metadata:
  version: "1.1.0"
  source: "https://github.com/hi-space/hi-agent-skills"
---

# AWS Tech Blog Writer

Turn a finished project into a post that could go up on the AWS Tech Blog as-is: correct AWS facts, real
diagrams, house style, and honest placeholders where the author has to fill in what only they know. The
deliverable is a Word file (`<work>/06-final.docx`) the author reviews and comments on; the Markdown it was
built from stays next to it for the WordPress paste.

`<skill-dir>` is the directory containing this SKILL.md. Every intermediate artifact lives in a work
directory `<work>` (default `./blog-work/<slug>/`), so a later session, a subagent, or the author can pick
the job up from any phase by reading files rather than conversation history.

## Why the pipeline is fixed

Blog posts about real projects fail in three predictable ways: the writer invents details the sources
never said, the architecture picture drifts from what was actually built, and the prose reads like a
translated press release. Each phase below exists to close one of those holes, and each phase writes a
file the next phase reads. Skipping a phase to "save time" reintroduces the failure it prevents.

```
Blog Progress (copy into your reply and keep it updated):
- [ ] Phase 0  Workspace and intake            -> <work>/00-intake.md
- [ ] Phase 1  Source digest and fact base     -> <work>/sources/*.digest.md, <work>/01-facts.md
- [ ] Phase 2  Gap analysis and deep research  -> <work>/02-research.md
- [ ] Phase 3  Post plan (outline + claims)    -> <work>/03-plan.md            [approval gate]
- [ ] Phase 4  Diagrams, built and verified    -> <work>/diagrams/, manifest.md
- [ ] Phase 5  Draft                           -> <work>/04-draft.md
- [ ] Phase 6  Fact-check against AWS docs     -> <work>/05-claims.md
- [ ] Phase 7  Style pass and lint             -> <work>/06-final.md (+ placeholders.md)
- [ ] Phase 8  Word document, built and verified -> <work>/06-final.docx
```

## Phase 0: Workspace and intake

Run `python3 <skill-dir>/scripts/init_workspace.py <slug>` to create `<work>` with the templates copied in.

Fill `<work>/00-intake.md` (template: `templates/intake.md`) from what the user gave you. The post cannot
be written without four things, so get them first and record how you got each one (stated, inferred,
assumed):

1. **What was built and for whom.** One paragraph in the author's words. Customer name and whether it may
   be published.
2. **Why the reader should care.** The problem before, the decision that made the project interesting,
   the outcome. This becomes the thesis of the post; a post without one is a feature list.
3. **Post type.** Customer case study, implementation walkthrough, or architecture deep dive. The type
   decides the section skeleton (see `references/aws-blog-conventions.md`).
4. **Reference material.** Every file, link, repo, transcript, deck, and diagram the author can share.
   Register each one in the intake's source table with an ID (`S01`, `S02`, ...). These IDs follow every
   fact through to the final draft.

Ask the author only what changes the writing, in one grouped message, and only if they are reachable.
Unattended, write your assumptions under `## Assumptions` and continue. Never ask about things a source
already answers; read first, then ask.

Convert non-text sources so they can be read in full: `python3 <skill-dir>/scripts/ingest_sources.py <work>`
turns PDF, DOCX, PPTX, and `.drawio` briefs into `<work>/sources/text/`. Video without a transcript is
registered but marked `not readable`; ask for a transcript or a written summary instead of guessing at it.

## Phase 1: Source digest and fact base

Read every source completely before writing a word of the post. The author sent them because they matter,
and the details that make a post credible (the exact error that motivated a redesign, the number of tables
behind a Text-to-SQL agent, who deployed what on which day) are always in the sources, never in your head.

For each source write `<work>/sources/<ID>.digest.md` using `templates/source-digest.md`: what the source
is, the facts it establishes (one per line, quoted or closely paraphrased, with a location), numbers and
dates, direct quotes worth keeping, and anything the source contradicts elsewhere. Long sources (a
100-page transcript, a repo) may be digested by parallel general-purpose subagents, one source each, that
receive only the file path and the template and write only the digest file. Do not let a subagent draft
the post, and do not fork yourself for this.

Then consolidate into `<work>/01-facts.md` (template: `templates/facts.md`): a numbered fact table with
source IDs and a confidence column (`stated` / `inferred` / `conflict`), the project timeline, the
component inventory (every AWS service and external system, with its role), the people and organizations
who may be named, and an `## Open questions` list. The fact table is the only thing the draft is allowed
to state as true about the project.

## Phase 2: Gap analysis and deep research

Sort every open question into one of two bins:

- **Project-specific** (what the customer's latency was, why they chose Aurora over DynamoDB, whether the
  pilot has started): nobody but the author knows. These become placeholders in the draft. Do not
  research them and do not infer them.
- **General technical** (how AgentCore Gateway authenticates a Lambda target, what an OIDC discovery URL
  must return, current quotas for a service): research them. Use the `aws-docs` MCP tools
  (`search_documentation`, `read_documentation`) first because the fact-check in Phase 6 will use the same
  sources; use the `deep-research` skill when the question needs synthesis across several sources or
  comparison with non-AWS material; use `WebFetch` for GitHub READMEs and release notes.

Record findings in `<work>/02-research.md` with the URL you actually opened next to each finding. A
finding without an opened URL is not a finding. Details in `references/research.md`.

## Phase 3: Post plan

Write `<work>/03-plan.md` (template: `templates/plan.md`). Read `references/aws-blog-conventions.md` first;
it has the section skeleton for each post type and the house rules the plan has to obey.

The plan lists, per section: purpose (one sentence the reader should be able to say after reading it),
the fact IDs it draws on, the diagrams it needs, code or config it shows, the claims that will need
verification, and a word budget. It also fixes the title, the one-paragraph opener, the author list, and
the disclaimer wording.

Two checks before moving on. First, walk the plan as the target reader (a solutions architect or a
technical lead at a similar company): does each section answer a question they would actually have?
Second, every planned section must map to facts or to a placeholder; a section with neither is speculation
and gets cut. If the author is reachable, present the plan and wait; the outline is the cheapest place to
change direction. Unattended, proceed and say in the final report that the plan was not reviewed.

## Phase 4: Diagrams, built and verified

The post needs at least one architecture diagram of what was built and usually one concept diagram (a flow,
a before/after, a sequence). Read `references/diagrams.md` for the choice between the two diagram skills
and the verification protocol. In short:

- **AWS architecture** (services, boundaries, request paths): invoke the `aws-drawio-diagram` skill. Its
  brief is written from `01-facts.md`'s component inventory, never from memory. Its builder must finish
  with `brief check ... ✓` and `0 errors, 0 warnings`, and its Reviewer phase must return `ready`. Ship
  the `.drawio.png` (XML embedded) and keep the `.brief.md` next to it.
- **Concept, flow, sequence, comparison**: invoke the `aws-diagram-design` skill, then export PNG through
  its export procedure. Run its `self_check.py` on the HTML before exporting.

After the diagram skill declares its output ready, verify it yourself against the fact base: open the
PNG, list every node and edge, and check each against the component inventory. A service in the picture
that is not in `01-facts.md`, or a component in the facts that the picture silently omits, is a defect,
whatever the diagram skill's own validator said. Record the check in `<work>/diagrams/manifest.md`
(figure number, file, caption, what it shows, verification result, fact IDs covered).

Diagrams only the author can supply (console screenshots, demo UI) become `[이미지 필요]` placeholders
that describe the exact screen and what should be visible in it.

## Phase 5: Draft

Write `<work>/04-draft.md` from the plan, in Korean unless the intake says otherwise, following
`references/author-voice.md` (the author's published posts: numbered thesis headings, dense parenthetical
sentences, consequence-closing paragraphs, comparison tables, a three-sentence 정리),
`references/aws-blog-conventions.md` (structure, naming, captions, code, bios) and
`references/writing-rules-ko.md` (the list of patterns that mark text as machine-written). Read all
three before the first sentence; when they disagree, author-voice.md wins.

Rules that decide whether the draft is publishable:

- **Every project statement traces to a fact ID.** Keep the IDs in HTML comments (`<!-- F12 -->`) at the
  end of the sentence or paragraph while drafting; the style pass strips them. If you cannot point to a
  fact, write a placeholder instead of the sentence.
- **Placeholders, not inference.** Use the exact convention in `references/placeholders.md`: a coloured
  span, a category tag, and a description of what should go there and why the post needs it. A placeholder
  that just says "TODO" wastes the author's time; one that says what a good answer looks like gets filled.
- **Numbers only from sources or opened documentation.** No round-number estimates, no "약 30%".
- **AWS service names as AWS writes them** (`Amazon Bedrock`, `AWS Lambda`, `Amazon Bedrock AgentCore
  Gateway`), full name at first mention, and never a wrong prefix. The lint script checks a table of
  common mistakes; the conventions file explains the pattern.
- **Diagrams embedded with a numbered caption** (`그림 1. ...`) and referenced from the text before they
  appear.

Draft the whole post in one pass, then read it once as the reader. Reordering sections at this point is
cheap; do it now rather than in the style pass.

## Phase 6: Fact-check against AWS documentation

Extract every checkable technical claim from the draft into `<work>/05-claims.md` (template:
`templates/claims.md`): service capabilities, limits, API and parameter names, authentication flows,
regional availability, pricing model statements, and anything a reader could try and find false. Project
facts are not claims (they are covered by fact IDs) but a project fact that implies an AWS capability is.

Verify each claim with the `aws-docs` MCP tools and record the URL opened, a short quote or paraphrase of
what the page says, and a status: `verified`, `corrected` (fix the draft, note the change), or
`unverified` (turn the sentence into a `[기술 검증 필요]` placeholder that says what to check). Run this
phase in a fresh context when you can (a general-purpose subagent given the draft, the claims template,
and this section) because the writer tends to confirm their own sentences. Protocol and examples are in
`references/fact-check.md`. `python3 <skill-dir>/scripts/check_claims.py <work>` confirms every row has a
status and a URL and that every `unverified` claim has a matching placeholder in the draft.

## Phase 7: Style pass and lint

Read the draft aloud in your head, one paragraph at a time, against `references/author-voice.md` and
`references/writing-rules-ko.md`.
Then run `python3 <skill-dir>/scripts/lint_blog.py <work>/04-draft.md`. It reports, with line numbers:
forbidden punctuation (em dash, en dash, middle dots, bullet glyphs, arrows, emoji), the translation-ese
and marketing patterns from the rules file, wrong or unintroduced AWS service names, images without
captions or with missing files, code blocks without a language, sentences that run too long, leftover
fact-ID comments, and a summary of every placeholder by category. Fix everything it reports as an error,
judge each warning, and rerun until it exits 0.

Save the result as `<work>/06-final.md` and write `<work>/placeholders.md` (the lint script's
`--placeholders-out` flag does this) so the author has one list of what they still need to supply. Run the
lint with `--final` on this file; it must exit 0 before Phase 8, because the Word build reads the Markdown
as-is and a leftover fact-ID comment or a mis-coloured span goes straight into the author's copy.

## Phase 8: Word document, built and verified

The author reads and comments in Word, not in Markdown, so the post is not delivered until
`<work>/06-final.docx` exists and has been checked. Invoke the `docx` skill for this phase and follow its
"Creating a new Word document" workflow (docx-js); this skill's builder is the document script for that
workflow, so you do not write one from scratch:

```bash
node <skill-dir>/scripts/build_docx.js <work>
```

It reads `06-final.md`, writes `06-final.docx`, and appends `placeholders.md` as a final "남은 placeholder"
section so the author has the post and the to-do list in one file (`--no-appendix` turns that off). Every
placeholder span becomes a run shaded in its category colour, bare `[태그]`s in headings and captions are
coloured too, figures are embedded at text width with their `그림 N.` caption, tables and code blocks keep
their structure, and the H1 becomes the document title. Do not convert with `pandoc -o file.docx` instead:
pandoc's DOCX writer drops the inline colours and the author cannot see what is missing.

The script ends with a verification block comparing the Markdown and the DOCX: image count, and for each
placeholder category the number of tags in the draft, in the document, and the shaded runs. It exits 0 only
when they agree. If it reports `FAIL` or `MISSING`, fix the draft or the image path and rebuild; do not
hand over a file whose verification failed. Then open the result once more from the outside,
`pandoc <work>/06-final.docx -t plain | head -80`, and read the opening as the author would: title, first
paragraph, disclaimer, first heading.

If the post needs something the builder does not render (a construct pandoc parses that the script prints
as plain text), extend `scripts/build_docx.js` following the `docx` skill's `docx-js.md` rules (every
paragraph a `Paragraph`, every line of text a `TextRun`, `ShadingType.CLEAR`, `ImageRun` with `type`),
rerun, and keep the change in the skill so the next post gets it too.

## What to hand back

Report in the user's language: the path of `06-final.docx` (the deliverable) and of `06-final.md` (for
the WordPress paste), the builder's verification summary, the diagrams (with their `.brief.md`), the
claims report with counts (verified / corrected / unverified), the placeholder list grouped by category,
and any phase that was skipped or not reviewed. Do not describe the post as ready to publish while
placeholders remain; describe it as ready for the author's pass.

## Subagents

Use them for isolated, file-in file-out work: one digest per large source, the diagram skill's own
Reviewer, the fact-check pass. Give each one only the files it needs and the template it must fill. Never
fork yourself to "look into" something; a fork inherits this whole task and will start writing the post.
Never let a subagent spawn further subagents.

## Reference files

| File | Read it when |
|---|---|
| [author-voice.md](references/author-voice.md) | Drafting and style pass: the author's published tone, with verbatim examples to imitate |
| [aws-blog-conventions.md](references/aws-blog-conventions.md) | Planning and drafting: post types, section skeletons, naming, captions, bios, disclaimer |
| [writing-rules-ko.md](references/writing-rules-ko.md) | Drafting and style pass: voice, forbidden patterns, before/after examples |
| [placeholders.md](references/placeholders.md) | Any time a fact is missing: the four categories, the HTML, how to word the request, how they render in Word |
| [diagrams.md](references/diagrams.md) | Phase 4: which skill, how to brief it, how to verify the output against the fact base |
| [research.md](references/research.md) | Phase 2: gap bins, tool order, evidence recording |
| [fact-check.md](references/fact-check.md) | Phase 6: what counts as a claim, statuses, common AWS facts people get wrong |
| [templates/](templates/) | Skeletons for intake, digest, facts, plan, claims, diagram manifest, and the post itself |

## Scripts

| Script | Purpose |
|---|---|
| `scripts/init_workspace.py <slug> [--dir <path>]` | Create `<work>` and copy templates |
| `scripts/ingest_sources.py <work>` | Convert PDF / DOCX / PPTX / drawio briefs in `sources/` to text |
| `scripts/lint_blog.py <draft.md> [--placeholders-out <file>] [--strict]` | Style, naming, image, code, placeholder checks |
| `scripts/check_claims.py <work>` | Validate `05-claims.md` and cross-check unverified claims against draft placeholders |
| `scripts/build_docx.js <work> [--out <file>] [--no-appendix]` | Build `06-final.docx` from `06-final.md` with docx-js (pandoc parses, docx renders); verifies placeholder colours and images against the Markdown |
