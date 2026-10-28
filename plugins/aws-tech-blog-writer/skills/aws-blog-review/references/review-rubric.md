# Review rubric: the six criteria, their checks, and the severity scale

Every finding in `review-report.md` belongs to one criterion and carries one severity. The three
checks (lint, fact-check, story review) each feed specific criteria; the table says which.

## Criteria

| ID | Criterion | Fed by | What passes |
|---|---|---|---|
| A | 최신성 (matches current AWS) | `05-claims.md` rows whose Note records a change since the draft was written | Names, GA/preview status, regions, limits, and API surfaces as the documentation states them today |
| B | 기술 정확성 (technically correct) | `05-claims.md` `corrected` and `unverified` rows, including every code block | Every testable AWS, SDK, or protocol statement has a URL that says the same thing |
| C | 그림 캡션 (every figure captioned) | lint E3, story review S3 | A `그림 N.` caption on the line under every image and every `[이미지 필요]` placeholder, sequential numbers, caption describes the picture |
| D | 서비스명과 링크 (official name and link at first mention) | lint E2, W2, E8 | Full official name at the first body mention, hyperlinked to a `docs.aws.amazon.com` or `aws.amazon.com` page; sub-service names as AWS writes them |
| E | 스토리와 논리 (argument holds) | story review S1 to S8 | A reader can state what the post argues, every section answers a question they had, figures arrive when needed, the conclusion answers the opening |
| F | 문체 (house voice) | lint warnings W4 to W9 | Reported at 권고 unless the sentence also fails another criterion; the review is not a rewrite |

## Severity

| Severity | Meaning | Examples |
|---|---|---|
| 차단 | Editors would send the post back; must be fixed before submission | wrong or outdated AWS statement, code that would not run, missing caption, first mention without name or link, reader cannot say what the post is about, a section that contradicts another |
| 수정 | Weakens the post; fix in the revision | decision without a reason, figure introduced after it appears, term used before definition, heading that is a sentence, duplicated paragraph |
| 권고 | Improves the post; apply if it does not require a fact the author has not given | tighter opening, a table instead of a list, a newer AWS service worth a sentence, voice warnings |

An `unverified` claim is 차단 until it carries its `[기술 검증 필요]` placeholder, then 수정.

## Where each check's output goes

**Lint codes.** Every code that appears in `lint.txt` becomes one report row (two rows when one code
carries two different messages, suffixed `a`, `b`), with its positions listed in 위치:

| Code | Criterion | Default severity | Code | Criterion | Default severity |
|---|---|---|---|---|---|
| E1 punctuation, arrow, emoji | F | 수정 | W1 `~`, `!`, long bold | F | 권고 |
| E2 wrong prefix, transliteration | D | 차단 | W2 short name before full name | D | 차단 |
| E3 image without caption, alt, or file | C | 차단 | W3 figure numbering | C | 수정 |
| E4 code fence without language | B | 수정 | W4 vocabulary, metaphor, connectives | F | 권고 |
| E5 malformed placeholder | F | 수정 | W5 translated constructions, endings | F | 권고 |
| E6 more than one H1 | E | 수정 | W6 heading form or level | E | 수정 |
| E7 leftover fact-ID comment | F | 수정 | W7 English-only paragraph | F | 권고 |
| E8 first mention without AWS link | D | 차단 | W8 long sentence | F | 권고 |
| | | | W9 abstract actor, agentless passive | F | 권고 |

**Claims.** A `corrected` row whose Note records a change over time (renamed, preview to GA, superseded,
shut down, quota changed) is criterion A; every other `corrected` or `unverified` row is criterion B.
`verified` and `out-of-scope` rows do not enter the report.

**Story.** Every `Snn` row enters the report under E with its severity; rows whose 심각도 is 통과 do not.

**One defect, one row.** When two checks name the same place for the same reason (lint W6 and story S7
on the same heading, lint E3 and story S3 on the same figure), keep one row with the higher severity
and both IDs in the ID column.

**Story rows the report drops.** A `story.md` row whose 인용 is a placeholder span (`[이미지 필요]` with
its caption on the next line, `[작성자 확인]`, `[인용 승인 필요]`) is not a finding: the author fills it
after the review and `placeholders.md` already lists it. Keep such a row only when its 문제 names the
sentence that cannot stand until the fact arrives. A story row that gives a skeleton absence or a heading
form a severity other than 수정 is normalised to 수정. The report's 집계 counts the rows that remain.

**Verdict.** 구조 수정 필요 when `story.md` proposes a new order or S1 failed; otherwise 수정 후 게재
가능 when any 차단 row remains; otherwise 게재 가능.

## Criterion E: the eight story checks

The story reviewer (`agents/blog-reviewer.md`) runs these and writes `story.md`. Each check either
produces findings or one row that says 통과.

| Check | Question the reviewer answers | Finding when |
|---|---|---|
| S1 요지 | Can the reader state in one sentence, after the opening, what the post will show and for whom? | The opening (conventions §3) lacks the problem, the reason it matters now, or the scope; or the one-sentence reading contradicts the title |
| S2 독자 질문 | Does every H2 answer one question the target reader has at that point, in the order they would ask? | A section with no question (cut or merge), a question answered two sections late (reorder), two sections answering the same question (merge) |
| S3 그림 | Is every figure introduced before it appears, does the caption name what the picture shows, and does the picture match the text? | Uncaptioned or unintroduced figure, caption and picture disagree, nodes in the picture absent from the text or components in the text absent from the picture, numbering gap, a slide pasted as an image |
| S4 연결 | Does each section's last paragraph give a reason to read the next, and is every term defined before use? | A jump the reader cannot follow, an undefined term or acronym, a decision without its reason |
| S5 결론 | Does the closing section answer the question the opening posed, with the results tied to the problem? | Conclusion restates the table of contents, introduces a new claim, or leaves the opening question unanswered; next steps as wishes instead of facts or placeholders |
| S6 중복과 공백 | Is anything said twice, and is any step or reason missing that the reader needs to rebuild or to believe? | Repeated paragraph, missing step in a walkthrough, a result without the method that produced it |
| S7 유형 | Does the post follow one skeleton (conventions §1) with noun-phrase headings? | Mixed types; headings that are sentences (`~필요했다`, `~다른 경로다`, `~옮기다`) or questions, listed in one finding with replacements; a required section missing (결과 or 저자 소개 in a case study, 리소스 정리 in a walkthrough) |
| S8 비중 | Is the length of each section proportional to its weight in the argument, within the 4,000-character guidance? | A section three times longer than its neighbours without carrying more of the argument, an introduction longer than the solution |

## Finding format

One row per finding, in every intermediate file and in the report:

```
| ID | 기준 | 심각도 | 위치 | 인용 | 문제 | 수정 제안 | 출처 |
```

- `ID`: the lint code (`E8`, `W4a`) for lint rows, `Cnn` from the fact-check, `Snn` from the story
  review. Never a bare `Lnn`; that form is a line number and belongs in 위치.
- `위치`: `L123`, or `L120-L131` for a span; `§3.2` when the finding is about a whole section.
- `인용`: the sentence, heading, or caption verbatim, trimmed to one line.
- `문제`: what the reader experiences or what the documentation says instead. Facts, not adjectives.
- `수정 제안`: the sentence to write, the move to make, or the placeholder text. Something the
  revision can apply without a second decision.
- `출처`: the URL that supports a fact finding; the rubric check for a story finding; the lint code.

## Story review file (`story.md`)

```
# Story review: <제목>

한 문장 요지: <the reviewer's reading>

## 독자 질문 지도
| L | 소제목 (그대로) | 형태 | 독자의 질문 | 답함 | 비고 |
(one row per H2 and H3, heading text verbatim; 형태 is 명사구 or 문장, and 문장 for every heading that
ends in a verb ending such as ~다, ~했다, ~이다, ~남는다, ~옮기다 or in a question mark; every 문장 row is
listed in the single S7 heading finding)

## 스켈레톤 대조
| 필수 섹션 (conventions §1, 유형 <A|B|C>) | 있음 / 없음 | L |
(one row per section the skeleton requires, including 저자 소개 and 참고 자료; every 없음 row is an S7
finding at 수정)

## 그림
| 그림 | 상태 | 소개 문장 L | 캡션 | 그림과 캡션 일치 | 본문과 그림의 차이 |
(상태 is 파일 for an embedded PNG, 이미지 필요 for a `[이미지 필요]` span, 파일 없음 for a path that does
not resolve; an 이미지 필요 row whose caption is on the next line and whose span says what to capture is
일치 and produces no finding)

## Findings
| ID | 기준 | 심각도 | 위치 | 인용 | 문제 | 수정 제안 | 출처 |
(one row per finding; a check with nothing to report is one row with 심각도 = 통과 and the check name in 기준)

## 집계
차단 N / 수정 N / 권고 N  (equal to the rows above)

## 제안 순서 (변경이 있을 때만)
1. ...
```
