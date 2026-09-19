# Voice: how the post has to read

The reader is an engineer or an architect deciding whether to try what the post describes. They stop
reading at the first sentence that sounds generated: an abstract noun doing something, a metaphor, a
passive verb hiding who acted, a comment on how important something is. This file is the whole style
contract for the drafter and the style pass. `scripts/lint_blog.py` checks the mechanical parts (word
lists, punctuation, endings, density); the judgement parts are here.

Two published posts by the author set the structural target and are quoted below:
"AWS 환경에서 Physical AI 모델 구축하기 – (1) 데이터" (aws.amazon.com/ko/blogs/tech/physical-ai-model-data/)
and "Part 1: 삼성계정 서비스의 AI SecOps" (aws.amazon.com/ko/blogs/tech/part1-samsung-account-ai-secops/).
Their sentence habits are kept; their plain-form thesis headings are not (see §2.4).

## 1. Sentence rules

### 1.1 The subject is someone or something that can act

People, teams, organizations, AWS services, components, code. Abstract nouns (문제, 질문, 조건, 선택,
결정, 구조, 차이, 필요, 일, 한계, 이유) do not act, arrive, remain, pile up, decide, or support.

| Generated | Written |
|---|---|
| 범용 챗봇에 SQL 기능을 추가하면 세 가지 문제가 남습니다. | 범용 챗봇에 SQL 기능을 추가하면 세 가지를 해결할 수 없습니다. |
| 특화 에이전트가 둘 이상 되면 곧바로 다음 질문이 따라옵니다. | 특화 에이전트가 둘 이상이면 다음으로 누가 에이전트를 승인하는지 정해야 합니다. |
| 아래 표의 오른쪽 열이 이 글의 나머지를 결정합니다. | 이 글의 나머지는 아래 표의 오른쪽 열을 항목별로 설명합니다. |
| 기존 시스템을 바꾸지 않는다는 조건이 이 선택을 뒷받침했습니다. | 기존 시스템을 바꿀 수 없었기 때문에 이 방식을 선택했습니다. |
| 에이전트 코드 바깥의 일이 먼저 쌓입니다. | 에이전트 코드보다 인프라 작업이 먼저 필요합니다. |

Test: can the subject of the sentence be photographed or logged in? If not, rewrite with the team,
the service, or the reader as the subject, or turn the sentence into `~이 있습니다` / `~해야 합니다`.

### 1.2 Active voice whenever an agent exists

`~됩니다`, `~되었습니다`, `~이루어집니다`, `~요구됩니다`, `~제공됩니다`, `~구성됩니다`, `~정리됩니다`,
`~확인됩니다`, `~처리됩니다`, `~적용됩니다`, `~사용됩니다`, `~판단됩니다` all hide who did it. Name the
actor. Passive is acceptable only when the actor is unknown or truly irrelevant (`로그는 30일 뒤
삭제됩니다` as a retention statement) and never in two consecutive sentences. `~에 의해` is never used.

| Generated | Written |
|---|---|
| 최종 구성은 두 개의 요청 경로로 정리됩니다. | 최종 구성에는 요청 경로가 두 개 있습니다. |
| 인증은 Cognito를 통해 처리됩니다. | Amazon Cognito가 인증을 처리합니다. |
| 이 과정에서 스키마 문서화가 요구됩니다. | 이 단계에서는 팀이 스키마를 문서화해야 합니다. |
| 파일럿은 9월에 진행될 예정입니다. | 정보전략팀은 9월에 파일럿을 시작할 계획입니다. |

### 1.3 No figurative language

A word for a physical thing used for a non-physical thing is a metaphor and goes. Frequent offenders in
drafts: 축 (for a request path or a workstream), 몫, 재료, 뼈대, 그림 (`큰 그림`, `목표 그림`), 지도,
층 (for a responsibility), 여정, 열쇠, 다리, 발판, 무대, 심장, 두뇌, 엔진, 톱니바퀴, 퍼즐, 지렛대,
밑거름, 문을 열다, 길을 열다. Replace each with the literal noun: 축 → 경로 / 구성 / 부분, 몫 → 플랫폼
소유자가 해야 하는 일, 재료 → 자격증명 / 토큰, 목표 그림 → 목표 구성.

Services doing their job (`Gateway가 인증을 처리합니다`, `Runtime이 세션을 격리합니다`) is literal and fine.
Idioms that read as a person talking (`짚어 둘 필요가 있습니다`, `살펴보겠습니다`, `주목할 점은`) go.

### 1.4 No evaluation

The sentence says what happened, what is true, or what follows. It does not say that it matters:
no 중요한, 핵심적인, 의미 있는, 인상적인, 주목할, 흥미로운, and no closing sentence of the form
`이는 ~의 중요성을 보여줍니다`. A closing sentence that states a consequence or a constraint stays:
`이 차이 때문에 LLM 파이프라인을 그대로 가져다 쓸 수 없습니다.`

### 1.5 Dense, specific, parenthetical

Pack the measurable detail into the sentence, with parentheses for units, English terms, expansions:

> 한 에피소드에는 카메라(30~60fps), 조인트 엔코더(100~1000Hz), 힘/토크 센서, 언어 지시문까지 서로 다른
> 데이터가 서로 다른 주기로 들어옵니다.

`한국어 용어(English term)` on first use, then whichever is shorter. English technical nouns stay
English inside Korean sentences (`timestamp 기준으로`, `Lambda 함수`, `IAM 역할`); Korean transliteration
(`람다`) is wrong. Numbers as digits with Korean counters (`4주`, `27개`, `35%`); dates `2026년 9월 8일`.

### 1.6 Decisions are narrated as decisions

`A 대신 B를 선택했습니다. B를 선택한 이유는 ~입니다.` with `결정했습니다`, `도입했습니다`, `전환했습니다`.
Not as inevitabilities (`B가 필수적입니다`) and not as the technology choosing itself.

### 1.7 Rhythm and register

- `합니다`체 in the body. Bullet items inside a requirements list may end in `~해야 한다`.
- One idea per sentence; under about 110 characters. Two long sentences then a short one is how
  people write; ten of the same length is how models write.
- Connectives `그래서`, `하지만`, `이때`, `결국`, `다만`, `즉` at most once per section each. Prefer a
  cause clause (`~때문에`, `~하려면 ~해야 합니다`) over a connective that starts a new sentence.
- Solo posts have no first person. Co-authored customer posts use `저희는` only where a decision or an
  action is attributed. The reader is addressed indirectly (`~할 수 있습니다`), never `여러분`, never
  `하세요` outside a step list.
- Contrast form `A는 ~지만, B는 ~` separates the familiar case from the new one and is encouraged.

## 2. Structure

### 2.1 Opening

First sentence defines the subject; second sentence gives the scale of the difficulty as a concrete
list or as the customer's numbers. No AWS service is named before the problem is stated.

> 삼성 계정(Samsung Account)은 전 세계 21억 사용자에게 삼성 디바이스와 서비스를 연결하는 통합 인증
> 플랫폼입니다. 초당 270만 건의 트래픽을 365일 24시간 무중단으로 처리하며, 하루 1~2TB에 달하는 AWS WAF
> 로그와 그 10배에 달하는 Amazon CloudWatch 로그가 생성됩니다.

Then one sentence on what the post covers and for whom. No table of contents in prose.

### 2.2 Numbered sections

`1.`, `2.` for H2 and `1.1`, `3.4.1` for H3 in case studies and deep dives. The section skeletons per
post type are in `aws-blog-conventions.md` §1.

### 2.3 Paragraphs

Two to five sentences, one point, and the last sentence is a fact or a constraint (§1.4). A paragraph
that states what the section will do (`이 절에서는 ~를 살펴봅니다`) is deleted; the section starts with
its first fact.

### 2.4 Headings are noun phrases

`2. 전체 아키텍처`, `3.2 SAP 에이전트: OpenAPI 타깃과 interceptor`, `1.3 AgentCore를 선택한 이유`.
Not a plain-form sentence (`~는 다른 문제다`, `~가 아니다`), not a question, not a promise (`~완벽 정리`).
A colon may add a sub-claim in noun form. The published posts used plain-form thesis headings; the
author has asked for noun phrases in new drafts, and the lint warns on a heading that ends in `다`.

### 2.5 Lists and tables

Bullets with a bold lead phrase and a colon, three to five items, one sentence each, for requirements,
options, and takeaways. The list marker is Markdown `-`; a typed `•` or `·` is an error. A comparison of
two or more options with three or more criteria is a table (criteria as rows, options as columns); a
table with one row goes back into a sentence. Case sections repeat fixed bold labels (`공격 패턴`,
`분석`, `결론`) so several cases read the same way.

### 2.6 Figures

Introduced in the text before they appear (`아래 그림 1은 전체 구성입니다.`), caption `그림 N. 명사구`
under the image, alt text describes what is drawn. A figure the text never mentions is cut.

### 2.7 Closing

Optional `핵심 교훈 (Key Takeaways)`: four one-sentence lessons that generalise beyond this project.
Then `정리` or `결론`: three or four sentences, the result, the scope covered, what is next as a fact or a
placeholder. No wish to the reader in a concept post; one is acceptable at the very end of a customer
post. A conclusion that could replace the opening without loss is rewritten.

### 2.8 Author bios

AWS: `<이름> <직함>는 <배경 경험>을 바탕으로 고객이 비즈니스 목표를 달성하도록 아키텍처 설계와 기술을
지원하고 있습니다.` Customer: `<이름> <사내 호칭>는 <팀>의 <직함>로서 <전문 분야>의 경험을 바탕으로
<담당 업무>를 담당하고 있습니다.` Use the customer's own title (`프로`, `매니저`, `책임`) and leave the
bio as a `[작성자 확인]` placeholder with the pattern filled in.

## 3. Words the lint rejects

The full lists live in `scripts/lint_blog.py` (`BANNED_VOCAB`, `METAPHORS`, `CONSTRUCTIONS`). The ones
that most often survive a first draft: `여정`, `핵심`, `인사이트`, `다양한` (name the items), `원활한`,
`효율적으로` (without a measurement), `이를 통해`, `~에 있어`, `~를 가능하게`, `~라고 볼 수 있습니다`,
`단순히 ~가 아니라`, `뿐만 아니라`, `첫째/둘째/셋째`, `이는`/`이것은` as a sentence subject,
`~에 대해 알아보겠습니다`, `결론적으로`, `요약하면`. Punctuation that is always an error: em and en
dashes (except the series marker in the H1), middle dots, arrows, emoji, `...`, `!` in body text.

## 4. Before and after

Before:
> 본 프로젝트는 단순히 챗봇을 구축하는 것이 아니라, 경신의 데이터 여정에 있어 새로운 패러다임을 제시하는
> 혁신적인 시도였습니다. 이를 통해 구성원들은 다양한 업무를 원활하게 처리할 수 있게 되었습니다.

After:
> 이 프로젝트의 목표는 챗봇이 아니라, 사내 시스템의 데이터를 에이전트가 쓸 수 있는 형태로 바꾸는 표준
> 경로를 만드는 것이었습니다. 4주 뒤 HIS와 SAP 두 시스템이 MCP 서버로 노출되었고, 정보전략팀 담당자가
> 8월 28일에 두 번째 에이전트를 직접 배포했습니다. <!-- F04 F09 F21 -->

Before:
> 에이전트 하나는 애플리케이션 서버 위에서도 돌아갑니다. 하지만 조직이 에이전트를 운영하려면 에이전트
> 코드 바깥의 일이 먼저 쌓입니다. 관리형이 대신하는 것과 소유자의 몫으로 남는 것은 다릅니다.

After:
> 에이전트 하나는 애플리케이션 서버 위에서도 동작합니다. 조직 단위로 운영하려면 에이전트 코드보다 세션
> 격리, 인증, 도구 연결, 로그 수집 같은 인프라 작업이 먼저 필요합니다. AgentCore가 이 가운데 무엇을
> 대신하고 플랫폼 소유자가 무엇을 직접 해야 하는지는 아래 표에 정리했습니다. <!-- F22 R04 -->

Before:
> 결론적으로, 이번 PoC는 성공적으로 완료되었으며 경신의 AX 여정에 중요한 이정표가 되었습니다.

After:
> PoC 1단계는 8월 말에 끝났습니다. 다음 단계의 범위와 파트너 착수 시점은
> <span style="background-color:#FFF2CC;color:#7F6000;padding:1px 4px;">[작성자 확인] 9월 8일 최종보고에서
> 요청한 결정 (A) 프로덕션 전환 범위, (B) 파일럿 시점과 인원 규모의 결과를 적어 주세요. 결정이 나지 않았다면
> "검토 중"으로 표기합니다.</span>

## 5. Style pass procedure

1. Apply the fact-checker's corrections list first; a corrected fact often breaks the next sentence.
2. Read each paragraph once for meaning. If the reader learns nothing new, cut it.
3. For every sentence, name the subject. Abstract noun acting (§1.1) or passive with a known actor
   (§1.2): rewrite.
4. Search for figurative nouns (§1.3) and evaluation words (§1.4); replace with the literal thing or
   delete.
5. Check every heading is a noun phrase (§2.4) and every paragraph's last sentence is a fact or a
   constraint (§1.4).
6. Read three consecutive sentences at a time; if they share a structure, vary one.
7. Run `lint_blog.py`; fix every error, judge every warning, rerun until it exits 0. Strip fact-ID
   comments only after the fact-check has used them.
