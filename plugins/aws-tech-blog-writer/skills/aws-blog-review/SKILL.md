---
name: aws-blog-review
description: "Use when the user has a finished or nearly finished Korean AWS Tech Blog draft, as Markdown or a Word file, and asks to review, check, or proofread it before submission or after an editor sent it back: whether its AWS statements still match current documentation, whether anything is technically wrong, whether every figure is captioned, whether each AWS service is introduced by its official name with a documentation link, and whether the argument holds from opening to conclusion. Korean triggers: 블로그 리뷰, 블로그 검토, 이 글 검토해줘, 게재 전 점검, 기고 전 확인, 초안 리뷰, 원고 검수. Not for writing a post from project sources (that is aws-tech-blog-writer)."
license: MIT
metadata:
  version: "3.0.1"
  source: "https://github.com/hi-space/hi-aws-skills"
---

# AWS Blog Review

A draft comes in; a review report and a revised draft go out. The review is done by readers who did
not write the text and who each look for one kind of defect: a script for the mechanical rules, a
fact-checker with the AWS documentation open, and a first-time reader for the argument. The main agent
consolidates their findings into one report, then applies every finding in a single revision pass and
delivers the result as Markdown and Word.

`<skill-dir>` is the directory containing this SKILL.md; `<writer-dir>` is its sibling
`skills/aws-tech-blog-writer`, whose lint, conventions, voice rules, placeholder rules, and Word
builder this skill reuses. Every artifact lives in `<work>`: `./blog-review/<slug>/` for a draft that
arrives as a file, or the writer skill's own work directory when that skill hands over `04-draft.md`
(its Stage 5), in which case this skill is also where the post gets its Word file.

```
Review Progress (copy into your reply and keep it updated):
- [ ] R1  Intake                        -> draft.md, images/
- [ ] R2  Lint | Fact-check | Story (parallel) -> lint.txt | 05-claims.md | story.md
- [ ] R3  Report                        -> review-report.md                 [approval gate]
- [ ] R4  Revision, one writer          -> revised.md, placeholders.md
- [ ] R5  Verified and built            -> <제목>.docx
```

## R1: Intake

```bash
python3 <skill-dir>/scripts/prepare_review.py <draft.md | draft.docx> [--slug <name>] [--dir <parent>]
python3 <skill-dir>/scripts/prepare_review.py <work>/04-draft.md --in-place      # from aws-tech-blog-writer
```

It writes `<work>/draft.md`, copies every local image into `<work>/images/` and rewrites the paths, and
drops the claims and report templates. With `--in-place` the draft's own directory is `<work>`: `draft.md`
is a copy of the source next to it, `images/` is used where it is, and `01-facts.md`, if present, is
passed to the fact-checker as `<facts>` so project facts are not counted as claims. A `.docx` is converted with pandoc after the script repairs what
the Word file encodes with formatting only: headings (docx-js omits the Normal style pandoc needs),
code blocks (shaded paragraphs), and placeholder spans (shaded runs) come back as Markdown, the
builder's appendix is dropped. Text in angle brackets (`<이름>`) does not survive the Word build, so a
Word draft never carries it; if the Markdown the Word file was built from exists, review that instead.
Read its summary line; if images are missing, ask the user for them only if reachable, otherwise let
the lint record them. Do not read the draft yet: your context is for consolidating three reports in R3,
and a reader who has already formed an opinion of the draft argues with findings instead of applying
them. You read it once, in R3, with the findings in hand.

## R2: Three checks, in parallel

Start all three at once. None depends on another.

**Lint** (mechanical rules, criteria C, D, F):

```bash
python3 <writer-dir>/scripts/lint_blog.py <work>/draft.md > <work>/lint.txt; true
```

A non-zero exit is expected on a draft under review. Every code in the output has a criterion and a
default severity in `references/review-rubric.md` ("Where each check's output goes"): E2, W2, and E8
feed criterion D (names and links), E3 and W3 feed C (captions), W6 feeds E, the rest feed B or F.

**Fact-check** (criteria A, B): fill `templates/prompt-fact-checker.md` and send it to the plugin's
`blog-fact-checker` agent (Agent tool, `subagent_type: aws-tech-blog-writer:blog-fact-checker`). The
prompt names the fact table (`<facts: <work>/01-facts.md>` when the draft came from the writer skill,
`none` otherwise, in which case every AWS sentence is a claim) and asks for currency: rows where the current page differs from the draft (renamed, preview to GA,
superseded operation) come back `corrected` with the date. It writes `<work>/05-claims.md` and replies
with counts, a corrections list, link placements, and a 권고 list.

**Story** (criterion E): fill `templates/prompt-reviewer.md` and send it to the plugin's
`blog-reviewer` agent (`subagent_type: aws-tech-blog-writer:blog-reviewer`). It has Read and Write
only, reads the rubric, four sections of the conventions, the draft, and the PNGs, and writes
`<work>/story.md` (one-sentence reading, question map, figure table, findings, proposed order).

If a plugin agent is not registered, send the same prompt to a general-purpose subagent with the agent
body from `agents/` prepended. Never fork yourself and never let a subagent spawn subagents.

## R3: Report

Now read `<work>/draft.md` once, then the three outputs. Fill `<work>/review-report.md` from
`templates/review-report.md` following `references/review-rubric.md`:

1. The verdict line, by the rubric's precedence: 구조 수정 필요 (story review proposes a new order or
   S1 failed), else 수정 후 게재 가능 (any 차단 row), else 게재 가능. Quote the reviewer's one-sentence
   reading next to it; the reviewer has already raised S1 if it contradicts the title.
2. The counts table by criterion and severity, counting the rows of the findings table.
3. The findings table, 차단 first, then by criterion, following the rubric's "Where each check's output
   goes": one row per lint code that appears (ID is the code, positions listed in 위치), one row per
   `corrected` or `unverified` claim (`Cnn`; a currency change is A, the rest B), one row per story
   finding (`Snn`) that is not 통과. Two checks on the same defect share one row with the higher
   severity. Each row's 수정 제안 is something the revision can apply without another decision: the
   sentence, the move, or the placeholder text.
4. 구조 제안: the reviewer's proposed order or "현재 순서 유지".
5. 개정에서 적용하지 않는 것: 권고 items that need a fact only the author has, with the reason.

If the user is reachable, show the verdict, the counts, and the 차단 rows, and wait; they may strike
findings. Unattended, proceed and say in the hand-back that the report was not reviewed.

## R4: Revision, one writer

You are the only hand that edits. Copy `draft.md` to `<work>/revised.md` and work through the report
in this order, which is `voice.md` §5 with structure added:

1. Fact corrections (`corrected` rows): replace the sentence with the proposed one and add the URL as
   a link if the row says where.
2. `unverified` rows: wrap the sentence in the `[기술 검증 필요] (Cnn) ...` placeholder from the row,
   exact HTML form from `<writer-dir>/references/placeholders.md`. Never delete the claim, never soften
   it to `~로 알려져 있습니다`.
3. Structure (story findings S1, S2, S4 to S8): move, merge, or cut sections as the 수정 제안 says.
   A finding that asks for a sentence you cannot write from the draft becomes a `[작성자 확인]`
   placeholder that says what the sentence must state. Inside a placeholder's text, name another
   placeholder kind in words (`인용 승인 placeholder`), never as a bracketed tag: the lint and the
   Word builder count bracketed tags, and a tag quoted inside another span fails the build.
4. Figures (E3, S3): add or fix `그림 N.` captions, renumber, add the introducing sentence before the
   image. A missing file becomes an `[이미지 필요]` placeholder with the caption already written.
5. Names and links (E2, W2, E8): full official name at first body mention, linked to the URL from the
   fact-checker's link list or the service's documentation landing page; `AgentCore Gateway`, never
   `Bedrock Gateway`.
6. Voice (W4 to W9, criterion F): fix the warnings the report kept; leave the author's sentence when
   the warning is a false positive and say so in the hand-back.

Every edit traces to a finding ID; do not rewrite sentences the report did not name. Then:

```bash
python3 <writer-dir>/scripts/lint_blog.py <work>/revised.md --final --placeholders-out <work>/placeholders.md
python3 <writer-dir>/scripts/check_claims.py <work> --draft <work>/revised.md
```

Both must exit 0. Rerun the lint until it does, with the warnings you keep justified.

## R5: Word document

Invoke the `docx` skill and follow its "Creating a new Word document" workflow; the builder is
`<writer-dir>/scripts/build_docx.js`:

```bash
node <writer-dir>/scripts/build_docx.js <work>          # reads revised.md, writes <work>/<제목>.docx
```

The file is named after the post: the first H1 of `revised.md`, with characters a file name cannot
carry removed (on a single file, `--name-from-title` does the same; `--out` overrides). The builder
embeds figures with captions, shades placeholders in their category colours, appends `placeholders.md`,
and ends with a verification block that must say ok. Then read the opening as the author would:
`pandoc "<work>/<제목>.docx" -t plain | head -60`.

## What to hand back

In the user's language: the verdict; the paths of `review-report.md`, `revised.md`, and `<제목>.docx`;
a before-and-after line (lint errors and warnings, claims verified / corrected / unverified, story
findings by severity); the section moves you made; the placeholders that remain by category; and any
stage skipped or not reviewed. While placeholders remain, the post is ready for the author's pass, not
for submission.

## Agents

| Agent | Tools | Reads | Writes |
|---|---|---|---|
| [blog-fact-checker](../../agents/blog-fact-checker.md) | Read, Write, WebFetch, aws-docs and aws-mcp documentation tools | verification, claims template, draft | `05-claims.md` |
| [blog-reviewer](../../agents/blog-reviewer.md) | Read, Write | rubric, conventions §1 §3 §6 §10, draft, PNGs | `story.md` |

## Reference files

| File | Read it when |
|---|---|
| [review-rubric.md](references/review-rubric.md) | R3 and R4: criteria A to F, severity, the eight story checks, finding and story.md formats |
| [templates/](templates/) | review-report, prompt-reviewer, prompt-fact-checker |
| `<writer-dir>/references/voice.md` §5 | R4: the order of the revision pass |
| `<writer-dir>/references/placeholders.md` | R4: exact HTML for the four placeholder kinds |
| `<writer-dir>/references/aws-blog-conventions.md` | R3 and R4: skeletons (§1), naming (§5), figures (§6), links (§9) |

## Scripts

| Script | Purpose |
|---|---|
| `scripts/prepare_review.py <draft> [--slug] [--dir] \| --in-place` | Create `<work>` (or use the draft's directory), convert `.docx`, copy images, drop templates |
| `<writer-dir>/scripts/lint_blog.py <draft.md> [--final] [--placeholders-out <file>]` | Mechanical checks, including E8 first-mention links |
| `<writer-dir>/scripts/check_claims.py <work> --draft <file>` | Every unverified claim has its placeholder |
| `<writer-dir>/scripts/build_docx.js <work>` | Build and verify `<제목>.docx` from `revised.md` |
