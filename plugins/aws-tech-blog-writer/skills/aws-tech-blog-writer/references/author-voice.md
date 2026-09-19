# Author voice: how these posts are actually written

Two published posts by the author set the target tone. Read this file before drafting and again during
the style pass; when `writing-rules-ko.md` and this file disagree, this file wins, because it describes
what the author has already published and editors have already accepted.

Reference posts:
- "AWS 환경에서 Physical AI 모델 구축하기 – (1) 데이터" (https://aws.amazon.com/ko/blogs/tech/physical-ai-model-data/)
- "Part 1: 삼성계정 서비스의 AI SecOps, Multi-Agent로 진화하는 보안 위협 탐지" (https://aws.amazon.com/ko/blogs/tech/part1-samsung-account-ai-secops/)

## 1. Structure

**Numbered H2, decimal H3.** `1. 들어가며`, `2. Physical AI 모델의 구성 요소와 데이터 유형`, ..., `5. 정리`;
under them `1.1`, `1.2`, `3.4.1`. The numbering is part of the voice: it tells the reader the post is an
argument with steps, not a collection of tips. Use it for deep dives and case studies alike.

**Headings are theses, often in plain form.** `1.1 성능을 제한하는 것은 모델이 아니다`,
`3.1 관측값만으로는 학습이 되지 않는다`, `3.3 수집 비용은 다양성에 비례한다`,
`4.3 온프레미스 데이터를 Bulk로 업로드`. A heading states the claim the section defends; the body
proves it. Plain form (`~다`) is normal in headings; the body stays in `합니다`체. Headings with a colon
carry a sub-claim: `3.4.1 텔레오퍼레이션: 기본 데이터 수집 방법`, `3.5 정교한 워크플로우 제어를 위한
Strands Agents 도입`.

**Typical spine for a case study or build story:**

```
1. 개요                         규모와 맥락을 숫자로 (21억 사용자, 초당 270만 건, 하루 1~2TB)
2. 배경 및 목표 설정             2.1 문제 정의 / 2.2 현재 운영 방식 / 2.3 목표 설정 (bullet 3개, 각각 "~할 수 있어야 한다")
3. <구축 과정>                   3.1 ~ 3.6, 시도한 순서대로. 첫 버전, 한계, 다음 결정. 비교는 표로.
4. 실제 <동작/탐지> 사례          사례마다 "공격 패턴 / 분석 / 결론" 같은 고정 항목
5. 핵심 교훈 (Key Takeaways)     4개 내외, 각 항목이 하나의 일반화된 문장
6. 향후 계획
7. 결론 및 시사점                3~4문장
```

**Typical spine for a concept-plus-architecture post:**

```
1. 들어가며                      1.1 통념을 뒤집는 주장 / 1.2 업계는 어떻게 푸는가 / 1.3 기존 방식과 다른 점
2. 구성 요소와 유형
3. 구조와 비용                   3.x 패턴 다섯 가지, 각 패턴을 H3로
4. 파이프라인 구축               4.1 ~ 4.6 데이터 흐름 순서대로, 단계마다 AWS 서비스 매핑
5. 정리                          3문장: 결국 무엇이 상한을 정하는가, 이 글이 다룬 범위, 출발점
```

**Series posts** announce the series in the opening and list the parts as bullets, with the current
part in bold: `1부 – 데이터 / 2부 – 학습 / ...`. The title carries the part marker as `– (1) 데이터` or
`Part 1:`. This en dash in the title and the parts list is the one place an en dash is accepted.

## 2. Opening

First sentence defines the subject in one breath, then the second sentence gives the scale of the
difficulty with a concrete list:

> Physical AI는 텍스트를 생성하던 AI가 물리 세계에서 직접 인식하고, 추론하고, 행동하는 단계로 넘어가는
> 흐름을 뜻합니다. 휴머노이드 로봇부터 자율주행까지 응용은 빠르게 늘고 있지만, 실제로 만들어 내려면 대규모
> 멀티모달 데이터, 막대한 학습 연산, 고정밀 시뮬레이션, 그리고 이 모든 것을 실제 동작으로 잇는
> 오케스트레이션까지 새로운 파이프라인이 필요합니다.

For a customer post the opening is the customer's scale, in numbers, before any AWS service is named:

> 삼성 계정(Samsung Account)은 전 세계 21억 사용자에게 삼성 디바이스와 서비스를 연결하는 통합 인증
> 플랫폼입니다. 초당 270만 건의 트래픽을 365일 24시간 무중단으로 처리하며, 하루 1~2TB에 달하는 AWS WAF
> 로그와 그 10배에 달하는 Amazon CloudWatch 로그가 생성됩니다.

Then one sentence on what the post covers: `이 시리즈는 ... 단계별로 살펴봅니다.` No "이 글은 세 부분으로
구성됩니다" style table of contents beyond the series list.

## 3. Sentence level

**Dense, specific, parenthetical.** The author packs the measurable detail into the sentence rather
than a separate one, using parentheses for units, English terms, and expansions:

> 한 에피소드에는 카메라(30~60fps), 조인트 엔코더(100~1000Hz), 힘/토크 센서, 언어 지시문까지 서로 다른
> 데이터가 서로 다른 주기로 들어옵니다. 이 비동기 스트림을 timestamp 기준으로 정렬해야 비로소 하나의 학습
> 샘플이 됩니다.

> 데이터의 문맥성(contextual grounding)과 그것을 학습시키는 레시피

> Egocentric Human Video (1인칭 사람 시점 영상)

> 무차별 대입(Brute Force) 공격이 2만 건 이상 확인됨

The pattern is `한국어 용어(English term)` on first use, then whichever is shorter afterwards. English
technical nouns stay English inside Korean sentences (`timestamp 기준으로`, `action 라벨`, `embodiment 정합`).

**Two-sentence paragraphs that land on a consequence.** A paragraph states a fact, then states what
follows from it. The closing sentence is a consequence or a constraint, not a comment on importance:

> 실로봇에서 얻는 텔레오퍼레이션 데이터는 사람이 직접 조종해 수집하므로, 수집 시간이 수집량에 비례해
> 선형으로 늘어납니다.

> 데이터를 쌓는 것 자체는 어렵지 않지만, 3만 개 에피소드 중에서 '접촉에 실패한 에피소드만', '특정 조명
> 조건의 실패 사례만' 골라내지 못하면 큐레이션도 재학습도 시작할 수 없습니다.

> 이 차이 때문에 LLM 파이프라인을 그대로 가져다 쓸 수 없습니다.

This is the distinction the style pass must apply: `~할 수 없습니다`, `~해야 합니다`, `~에 비례합니다` as
a closing sentence is the author's voice; `~의 중요성을 보여줍니다`, `~에 핵심적인 역할을 합니다` is not.

**Contrast structure `A는 ~지만, B는 ~`.** Used to separate the familiar case from the new one:

> 텍스트 토큰은 순서만 맞으면 되지만, 로봇 데이터는 카메라 영상/힘/토크/관절 상태/언어 지시 등 여러
> 스트림을 하나의 시간축에 정렬해야 합니다.

> 텔레오퍼레이션 데이터는 정확한 action 라벨과 타겟 embodiment 정합 덕분에 가장 신뢰도 높은 소스로
> 여겨지지만, 수집 비용이 비싸고 다양성이 제한적입니다.

**Decisions are narrated as a sequence with the reason attached.** `첫 번째 버전은 심플했습니다. ...
구조였습니다.` then the limitation, then `이에 따라 AWS에서 제공하는 오픈 소스 SDK인 Strands Agents 도입을
결정했습니다.` and `이러한 단일 에이전트의 구조적 한계를 극복하기 위해, 역할이 명확히 분리된 Multi-Agent
아키텍처로의 전환을 결정했습니다.` Verb of choice: `결정했습니다`, `도입했습니다`, `전환했습니다`.

**Connectives in use:** `다만`, `즉`, `예를 들어`, `이때`, `결국`, `특히`, `한편`, `그 결과`, `이에 따라`,
`이러한 ~를 극복하기 위해`. `이를 통해` appears but at most once per section.

**Endings:** `합니다`, `입니다`, `있습니다`, `됩니다`, `했습니다`, `되었습니다`, `할 수 있습니다`. Bullet
items inside a goals list may end in plain form (`분석할 수 있어야 한다`), which reads as a requirement
statement; body paragraphs do not.

**Subject.** Solo posts have no first person; the post itself or the technology is the subject
(`이 글에서 다룬 내용은`, `Physical AI에서 성능의 상한을 정하는 것은`). Co-authored customer posts use `우리는`
and `저희는` for the joint team, and this is accepted; keep it to where a decision or an action is being
attributed, not as a habit at every sentence start.

## 4. Lists and tables

**Bullets with a bold lead phrase and a colon**, three to five items, one sentence each. Used for
requirements, options, features, and takeaways:

> **멀티모달/시간 정렬 데이터**: 텍스트 토큰은 순서만 맞으면 되지만, 로봇 데이터는 ... 정렬해야 합니다.
> **행동이 라벨링된 데이터**: LLM은 다음 텍스트 토큰만 예측하면 되지만, ... 라벨로 붙어야 합니다.
> **인터넷에서 스크랩 할 수 없는 데이터**: 웹 텍스트와 달리 로봇 궤적은 인터넷에 존재하지 않습니다.

Goals list: `• 대규모 로그 분석: 하루 수백만 건의 WAF 로그를 분석할 수 있어야 한다.` Three goals, each
testable. The bullet glyph is Markdown `-`, never a typed `•` or `·` in prose (the published HTML renders
the list marker; the draft must not contain the glyph).

**Tables for side-by-side option comparison**, one row per criterion, options as columns:

| 비교 항목 | Amazon Bedrock Agent | Strands Agents (Python SDK) |
|---|---|---|
| 개발 방식 | Low-Code / No-Code (콘솔 중심) | Code-First (Python 코드 중심) |
| Workflow 제어 | 프롬프트 기반의 Orchestration에 의존 | 개발자가 실행 흐름을 직접 설계 |

Tables also map pipeline stages to AWS services (stage / what happens / service / why). A comparison
that would take three paragraphs goes into a table; a table with one row goes back into a sentence.

**Case sections use fixed labels** so several cases read the same way: `공격 패턴`, `분석`, `결론` each as a
bold lead. The `결론` line is a judgement in noun form: `... 무차별 스캐닝을 시도하는 상황으로 판단`.

## 5. Figures

Captions: `그림 1. Physical AI 모델의 네 가지 구성 축`, `그림 2. Physical AI 모델을 위한 학습 데이터
피라미드 – 품질과 규모의 트레이드오프`. Number, period, noun phrase; a sub-clause after a colon is
preferred over the en dash in new drafts (`그림 2. 학습 데이터 피라미드: 품질과 규모의 트레이드오프`).
Figures are conceptual as often as architectural: a four-axis model, a data pyramid, a pipeline.

## 6. Closing

Short and declarative. Three sentences: the thesis restated as a result, the scope of what was covered,
the starting point for the reader.

> 결국 Physical AI에서 성능의 상한을 정하는 것은 모델이 아니라 데이터입니다. 이 글에서 다룬 내용은 대부분
> 파이프라인을 구성하기 이전에 고려해야 하는 사항으로, 데이터를 어떻게 설계하고 어떤 AWS 서비스와 연결할지에
> 대해 초기 설계가 필요합니다. 데이터 파이프라인을 구축하는 것이 모든 학습의 출발점입니다.

Before the closing, a `핵심 교훈 (Key Takeaways)` section with four generalisable one-liners is the
author's way of giving the reader something portable:

> 복잡한 비즈니스 로직을 하나의 에이전트가 모두 처리하려 할 때 성능 저하와 판단 오류가 발생합니다.
> 많은 정보를 한 번에 주입하면 에이전트는 혼란을 겪습니다(Context Pollution).
> 처음부터 완벽한 시스템을 설계하려 하기보다, 작게 시작하며 단계별로 문제를 발견하는 점진적 접근법이
> 리스크를 줄입니다.

A closing wish to the reader is acceptable once, at the very end of a customer post: `이번 포스팅이 ...
고민하는 많은 엔지니어분들에게 의미 있는 영감이 되기를 바랍니다.` Do not add one to a concept post.

## 7. Author bios

AWS: `<이름> <직함>는 <배경 경험>을 바탕으로 고객이 비즈니스 목표를 달성하도록 아키텍처 설계와 기술을
지원하고 있습니다.`

> 이유정 AI/ML Specialist SA는 자율주행차량/로보틱스의 AI 연구개발 경험을 바탕으로 고객이 비즈니스 목표를
> 달성하도록 아키텍처 설계와 기술을 지원하고 있습니다.

Customer (Samsung uses the in-house title `프로`): `<이름> 프로는 <팀>의 <직함>로서 <전문 분야>의 경험을
바탕으로 <무엇>을 담당하고 있습니다.`

> 박시온 프로는 삼성계정 서비스 개발팀의 Sr. Engineer로서 클라우드 인프라, DevOps, AI Security의 경험을
> 바탕으로 복잡한 비즈니스 문제 해결과 지능형 보안 시스템 구축을 담당하고 있습니다.

Use the customer's own title conventions (`프로`, `매니저`, `책임`), which the author must confirm:
`[작성자 확인]`.

## 8. What to imitate and what to avoid

Imitate: thesis headings, numbers in the first paragraph, `용어(term)` pairs, consequence-closing
paragraphs, `A는 ~지만 B는` contrasts, decisions with `결정했습니다` and the reason, comparison tables,
a `핵심 교훈` section, a three-sentence `정리`.

Avoid even though it appears in the reference posts (the published versions passed, the lint will still
flag them, and the author asked for less of them): `여정` in headings (`AI SecOps 구축 여정`), `차세대`,
`통찰력 있는`, `이를 통해 ... 할 수 있게 되었습니다` as a paragraph closer, `•` typed as a glyph. When the
draft needs the same effect, use the mechanism (`3.1에서 3.6까지의 구축 과정`, `다음 세대의` → the concrete
capability, `~를 알 수 있습니다`).
