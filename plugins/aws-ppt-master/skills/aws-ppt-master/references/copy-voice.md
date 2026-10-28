# Copy Voice: writing slide text a person would actually say

> Load when authoring or rewriting on-slide text or speaker notes in Korean or English.
> Machine check: `scripts/pptx_qa_check.py --checks copy` (reads slide text and notes). Ported from myslide (jesamkim, MIT).

Design and words are separate crafts, and slide copy is the one users rewrite
first. A deck can be laid out beautifully and still read as machine drafted,
because the tells live in the sentences and in the short label slots, not in
the layout.

## Who writes what

| Layer | Owner | Why |
|---|---|---|
| Structure, narrative order, logic, what each slide argues | the building model (Fable 5, or a Codex worker via `orca-cli`) | This is composition and judgment, which is what that model is picked for. |
| The sentences that land on the slide | A dedicated prose-writing agent when the session has one registered, with this file in its brief; otherwise the building model, applying this file inline | The contract is what closes the gap, not the model: measured 2026-08-20, the same deck brief produced 8 banned dashes on Opus 4.6 and 20 on Opus 5 without it, and 0 on both with it. |

The sentence layer is a genuine handoff, not a spellcheck. The writer may
replace any line outright, because a line that reads as machine drafted usually
cannot be repaired word by word. What it must not change: the facts, the
numbers, the product names, the slide's claim and role, and the character budget
(the card is already sized).

Two consequences worth internalizing:

- Getting the layout right does not get the copy right. Run the pass.
- The pass is not a substitute for drafting well. Write to the rules below
  while drafting, so the pass has little to do. Both layers earn their keep:
  the recipe raises the floor, the pass raises the ceiling.

## The root cause (read this before the rule tables)

Nearly every pattern below grows from one condition: **a slide with nothing
specific to say.** When a slide has no concrete claim, no number, and no
decision behind it, the model still has to fill the slot, so it reaches for the
safest available filler, which is commentary *about* the content rather than the
content. "왜 중요한가" is not a style tic. It is a slot with no answer in it.

That is why a thin brief reliably produces this defect. "슬라이드 만들어줘" with
no audience, no decision being asked for, and no concrete claim converges on
"정보 → 의미 → 행동" scaffolding every time, in any model.

Measured, and the size of the effect is the reason this section leads with the
brief rather than with the rules: from a thin brief, a copy-only run produced
**12 banned dashes** and the built deck **6**. From a brief that stated an
audience and a topic, **zero**. The upstream fix outperforms every downstream
rule in this file, so spend the effort at the Outline stage.

So the first fix is upstream: before writing a single line, each slide needs
**one claim, and the fact, number, or decision that carries it.** If that pair
is empty, the honest move is to cut the slide or go get the number, not to
narrate significance. Fixing this at the outline stage removes the pressure that
creates the AI dialect in the first place; the rules below then have almost
nothing left to catch.

## What natural slide copy is (the positive recipe)

The rules below are all subtractive, so here is the shape to aim at, since
knowing what to write beats knowing what to avoid:

- **Plain over ornamented.** Say the thing. Drama comes from a real number or a
  sharp verb, not from punctuation or a rhetorical flourish.
- **One idea per line.** If a line needs a dash or a `not just X but Y` to hold
  two clauses together, split it or cut one.
- **Concrete over generic.** Names, numbers, and verbs (`추론 비용 42% 절감`,
  `배포가 하루 단위로`) beat abstract virtue words (`혁신적인`, `차별화된`,
  `faster, cheaper, better`, `seamless`, `robust`).
- **Someone does the thing.** The subject is a team, a person, or a service,
  and the verb is active: `Step Functions가 단계 순서를 관리합니다`, not
  `단계 순서가 관리됩니다`, and not `이 숫자들이 기준선이 됩니다`.
- **Literal words.** A host does not 쥐다 a schedule, a failure does not 번지다,
  a number is not an 출발점. Say what the thing is.
- **Varied rhythm.** Do not end every Korean bullet in `~합니다`, and do not
  reach for a three item list every time. Mix noun phrase endings (체언 종결)
  with the occasional full sentence.
- **Punctuation a person types.** Period, comma, colon, and the occasional
  parenthesis.

## Rule 1: a label slot holds the answer, never the question

This is the most visible offender and the one users report most (field report,
2026-08: sub-titles like "왜 중요한가" appearing unprompted on both Fable 5 and
Opus 5 output, in decks and in reports).

Label slots are titles, sub-titles, eyebrows, section labels, and card labels.
They are short, and a meta label is a cheap way to occupy a short slot without
committing to content. **If you were about to label a block "왜 중요한가",
write the answer in that slot instead.** If you do not know the answer
specifically enough to write it, the block should not exist.

| Meta label (do not use) | Write instead |
|---|---|
| `왜 중요한가`, `왜 중요할까요` | The answer, with its number: `월 인프라 비용 22% 감소` |
| `핵심 시사점`, `시사점` | The implication itself: `내년 예산은 이 기준으로 다시 잡아야 합니다` |
| `더 큰 그림`, `한 걸음 물러나 보면` | What that bigger picture actually is: `검색이 제품의 일부가 됐습니다` |
| `이것이 의미하는 것`, `무엇을 의미하나`, `무엇을 뜻하는가` | The meaning: `온프레미스 재계약을 미룰 수 있습니다` |
| `주목할 점`, `핵심 포인트` | The point itself |
| `Why this matters`, `Why it matters` | The takeaway plus the figure: `Idle GPU time fell from 18% to 7%` |
| `Key takeaway`, `The bigger picture`, `What this means` | The takeaway itself |

The function is legitimate; the label is not. A slide whose job is "so what for
you" is a good slide. It just needs a title that states the conclusion
("유휴 GPU를 줄여 월 2,200만원이 남습니다") rather than announcing that a
conclusion is coming.

**How the checker grades these.** All of the above are wrong in a label slot, but
the checker splits them by how certain the detection is.

It **fails the build** on these exact strings, wherever they appear:
`왜 중요한가`, `왜 중요할까`, `왜 중요한지`, `왜 중요합니까`, `핵심 시사점`,
`주요 시사점`, `이것이 의미하는`, `이것은 무엇을 의미`, `무엇을 의미하는가`,
`무엇을 의미하나`, `무엇을 의미할까`, `무엇을 뜻하는가`, `why this matters`,
`why it matters`, `why that matters`, `key takeaway`, `the key takeaway`,
`what this means`, `the bigger picture`.

It **warns** on these, which sometimes appear in legitimate prose: `시사점` on
its own, `더 큰 그림`, `한 걸음 물러나`, `주목할 점`, `핵심 포인트`,
`눈여겨볼 점`, `zoom out`, `stepping back`. A warning is not permission: it
means a human or the copy pass decides, rather than the regex.

**The checker is a verbatim string match, not a judgement.** It does not read
the surrounding slide, so it cannot apply the adjacency test below. That has a
consequence worth knowing: `핵심 시사점을 정리하면 비용 22% 절감입니다` fails the
build even though the answer is right there in the sentence, and
`Why this matters: idle GPU fell to 7%` fails even though it supplies the
figure. Treat the build-failing list as strings that simply do not belong in a
deck, in any position. The adjacency reasoning below is for YOU, deciding what
to write; the regex only enforces the floor.

**Where this rule stops.** A question-form label is fine when it is
*navigational* and the answer sits next to it. In a report deck, an eyebrow
reading `무엇을 했는가` above a title reading `네 가지 축으로 비용을 낮췄습니다`
is doing honest work: it marks the section, and the answer is right there. The
same goes for `지금의 문제`, `해결 방식`, `다음 단계`, and an agenda's own
section names.

What separates the two cases is whether the answer is present:

| | Label | Adjacent content | Verdict |
|---|---|---|---|
| Navigational | `무엇을 했는가` | `네 가지 축으로 비용을 낮췄습니다` | Fine. Section marker, answer supplied. |
| Meta filler | `왜 중요한가` | `비용을 절감할 수 있습니다` | Rewrite. The slot that should hold the answer holds the category, and the body only restates it abstractly. |

So the test is not "is it a question" but: **does anything on this slide answer
it with a specific?** If nothing does, the label is covering for missing
content, and the fix is the number, not a better label.

## Rule 2: no meta narration inside sentences

The same reflex in body text. It adds a sentence that comments on the previous
sentence instead of adding information.

| Do not write | Write |
|---|---|
| `이는 운영 효율이 개선된다는 것을 의미합니다` | `장애 대응이 4시간에서 20분으로 줄었습니다` |
| `단순히 비용 절감이 아니라 체질 개선입니다` | `고정비가 변동비로 바뀌었습니다` |
| `이것은 게임 체인저입니다` | What changed, in numbers |
| `여기서 중요한 것은 ~라는 점입니다` | Just state the thing |
| `Not just faster, but fundamentally different` | Name the difference |
| `This represents a fundamental shift in how teams work` | `배포 승인이 사람 손을 거치지 않습니다` |

### The `A가 아니라 B` reflex is the single most frequent offender

Measured on this skill's own output (8 generation runs, 2026-08-18), the
contrastive reflex fires at **0.77 times per slide on Opus 5** and 0.23 on
Fable 5. At roughly one per slide it is not a rhetorical choice, it is a tic.

Two things make it easy to miss:

1. **It usually appears without `단순히`.** Every measured instance used the
   bare form, so a rule written around "단순히 A가 아니라 B" catches almost
   none of them in practice. The shape to watch is just `A가 아니라 B`.
2. **It loves the title slot.** Measured examples, all from titles, subtitles,
   and captions: `디지털 전환은 기술이 아니라 일하는 방식을 바꾸는 일입니다`,
   `거버넌스는 나중이 아니라 처음부터`, `보안은 확산의 브레이크가 아니라
   액셀입니다`, `전략은 문서가 아니라 실행으로 완성됩니다`.

**The fix: delete A, keep B.** `기술이 아니라 일하는 방식을 바꾸는 일입니다`
becomes `일하는 방식을 바꾸는 일입니다`, and then, better still, becomes the
specific thing that changed. The contrast only carries information when the
audience actually holds belief A. That is rare, and it is never true four times
in one deck.

Why it feels good to write and reads badly: the foil manufactures the *shape* of
an insight without supplying one. `X가 아니라 Y` sounds like a correction of a
common misconception, so the sentence borrows authority it has not earned. It
also makes Y arrive late and sound defensive.

**Budget: at most one per deck, and only when A is a belief the room actually
holds.** The English twins (`not just X but Y`, `not only`, `, not Y`) count
against the same budget.

Not this pattern, and never flagged: `아니라면` (conditional), `아니라도`
(concessive), `아니라서` (reason), `아니라고` (quotative), and `뿐만 아니라`
(additive "not only X but also Y"). Those are ordinary Korean grammar that
happens to share a syllable with the tic.

## Rule 3: em dash and en dash are banned in slide copy

`—` and `–` do not appear in on-slide text. Not as an amplifier, not as a
`label — description` separator, not padded with spaces, not tight. This is a
hard rule, and `pptx_qa_check.py --checks copy` fails the deck on it rather than warning.

The reason it is absolute rather than a matter of taste: it is the single most
reliable machine visible fingerprint of AI drafted copy, so a reader who spots
two of them stops trusting the whole deck. There is always a better mark
available.

| Instead of | Write |
|---|---|
| `유휴 리소스 비용 — 피크 기준으로 산정` | `유휴 리소스 비용: 피크 기준으로 산정` (colon) |
| `governance from day one — not bolted on later` | `Governance is built in.` (one sentence) |
| `2026년 1월 – 6월` | `2026년 1~6월`, or `1월부터 6월까지` |
| `세 가지 원칙 — 자동화, 관측, 회수` | Put the three on their own lines, or use a colon |

Replacements, in order of preference: a period (two short sentences beat one
propped up sentence), a colon (label to value), a line break or a real list item
(when it was structure pretending to be punctuation), `~` for numeric ranges,
parentheses (for a genuine aside).

Not affected, and never flagged: hyphenated compounds and identifiers with no
surrounding spaces (`cloud-native`, `m5.xlarge`, `Well-Architected`,
`on-premises`, `24-7`). The ban is about dash as punctuation, not the hyphen
character.

Also a tic, though less severe: an ASCII hyphen with a space on both sides
(` - `) doing a colon's job. Same fix.

## Rule 3b: the middot and bullet dot as an inline separator are banned too

A middle dot (`·`) or a bullet (`•`) placed between phrases on one line
(`빠르고 · 저렴하고 · 안전한`, `자동화·관측·회수`, `A • B • C`) is the same tell as
the em dash: it manufactures the look of a tidy list without committing to real
structure, and it reads as machine drafted. This is a hard rule, and
`pptx_qa_check.py --checks copy` fails the deck on it rather than warning.

| Instead of | Write |
|---|---|
| `빠르고 · 저렴하고 · 안전한 아키텍처` | `배포는 하루 단위, 비용은 42% 절감.` (state the two that matter) |
| `자동화 · 관측 · 회수` | Put the three on their own lines, or `자동화, 관측, 회수` (comma) |
| `서울 · 도쿄 · 싱가포르 리전` | `서울, 도쿄, 싱가포르 리전` (comma) |

Replacements, in order of preference: a real list item on its own line (when the
items are genuinely parallel), a comma (a short in-line series), or a period
(two short sentences). The fix is the same one the dash rule reaches for.

Not affected, and never flagged: a **leading** list bullet at the start of a
line (`· 유휴 리소스 비용 절감`, `• 배포가 하루 단위로`). The ban is about the dot
as a *separator between words*, not the dot as a list marker. Native PowerPoint
bullets set through paragraph properties never contain the dot as text, so they
are outside this rule entirely.

## Rule 4: Korean 번역투 sweep

Default to 존댓말 throughout. Beyond tone, the recurring field correction on
Korean decks is not grammar but phrasing carried over literally from the English
tech idiom the deck was drafted in.

| Bad (번역투) | Good | Why it fails |
|---|---|---|
| `서버리스 여정을 시작하세요` | `작은 서비스 하나부터 옮겨 보세요` | "start your journey" 직역. 아무도 여정이라고 말하지 않습니다. |
| `운영 오버헤드 제거` | `운영 부담을 덜었습니다` | 음차. 개념을 쓰세요. |
| `조직 역량 내재화` | `팀이 직접 운영할 수 있습니다` | 관공서식 한자 조어. |
| `노브(knob) 총정리` | `튜닝 포인트 총정리`, `조정 항목` | 영어권 은어. 한국 청중에게 뜻이 없습니다. |
| `데이터 상주 요건` | `국내에 데이터를 둬야 하는 요건` | 컴플라이언스 용어의 사전식 직역. |
| `세 가지 축이 전부입니다` | `세 가지만 기억하시면 됩니다` | 문법은 맞지만 아무도 그렇게 말하지 않습니다. |
| `Pay-per-use 모델` | `쓴 만큼만 과금` | 한국어 슬라이드에 라틴 문자 상품 용어. |
| `TCO 최적화` | `총 소유 비용 절감`, 또는 그 금액 | 규정 용어의 계산기식 번역. |
| `~에 대한` 반복, `~를 통해` | 동사로 바꿉니다 | 한국어는 동사에 의미가 실립니다. 영어의 명사 습관을 옮기면 관공서 문체가 됩니다. |
| slide A `재순위화`, slide B `리랭킹` | 하나만 골라 덱 전체에 고정 | 용어가 바뀌면 청중은 개념이 바뀐 줄 읽습니다. 차용어와 번역어 쌍(리랭킹/재순위, 청킹/분할, 임베딩/벡터화)마다 찾기 한 번 돌리세요. |
| `~에 있어`, `~함에 있어` | `~에서`, `~할 때` | "in terms of" 직역. |
| `~를 가능하게 합니다` | `~할 수 있습니다`, 또는 능동 동사 | "enables" 직역. |
| `~라고 볼 수 있습니다`, `~라고 할 수 있습니다` | 그냥 단언합니다 | 영어 hedge의 번역. 슬라이드는 주장을 합니다. |
| `~에 관한 것입니다`, `~에 대한 이야기입니다` | 내용을 직접 씁니다 | "is about" 직역. 슬라이드가 무엇에 관한 것인지 말하는 대신 그것을 말합니다. |
| `이는`, `이것은` 으로 시작하는 문장 | 명사를 다시 씁니다 | "This ..." 직역. 대명사 주어는 앞 문장에 대한 논평으로 흐릅니다. |
| `첫째, 둘째, 셋째` | 각 항목을 한 줄씩 | 열거 공식. 목록 구조가 이미 번호를 보여 줍니다. |
| 모든 불릿이 `~합니다`로 끝남 | 체언 종결을 섞고 간간이 완전한 문장 | 같은 어미가 줄줄이 서면 기계가 쓴 것처럼 읽힙니다. |

When a term is genuinely ambiguous (차용어와 번역어가 둘 다 자연스러울 때),
prefer the form AWS Korean documentation and blog posts use, then keep it
consistent deck wide.

## Rule 4b: the subject can act, and the verb is active

Korean slide copy drifts to two shapes when the writer does not want to name
who did something: an abstract noun acting (`이 숫자들이 기준선이 됩니다`,
`기록이 먼저 답해 줍니다`, `핵심은 ~에 있습니다`) and a passive ending with
no actor (`~됩니다`, `~되었습니다`, `~이루어집니다`, `~확인된 것은`). Both read
as drafted by a machine because a presenter never talks that way on stage. The
presenter says who did it.

The subject of a sentence is something that can be photographed or logged in:
a team, a person, a role, an AWS service, a component. Abstract nouns (문제, 숫자,
결과, 조건, 선택, 구조, 차이, 핵심, 교훈, 변화) do not act, remain, arrive, decide,
answer, or support.

| Generated | Written |
|---|---|
| `이 숫자들이 이후 설계를 비교하는 기준선이 됩니다` | `이후 설계는 이 숫자를 기준으로 비교합니다` |
| `기록이 먼저 답해 줍니다` | `실행 기록에서 실패 지점을 먼저 확인합니다` |
| `이번 전환의 핵심은 상태를 호스트 밖으로 뺀 데 있습니다` | `실행 상태를 호스트 밖 DynamoDB로 옮겼습니다` |
| `이번 수치로 확인된 것은 재실행이 줄었다는 점입니다` | `3개월 동안 수동 재실행은 0회였습니다` |
| `인증은 Cognito를 통해 처리됩니다` | `Amazon Cognito가 인증을 처리합니다` |
| `스케줄이 실행 로직과 분리됩니다` | `EventBridge Scheduler가 스케줄을 맡고, Lambda가 실행합니다` |
| `실패를 설명할 수 있게 됐습니다` | `실패 지점을 실행 기록에서 찾습니다` |

Passive is acceptable when the actor is unknown or genuinely irrelevant
(`로그는 30일 뒤 삭제됩니다` as a retention fact), and never in two consecutive
lines. `~에 의해` does not appear at all. `~할 수 있게 됩니다` is a doubled
auxiliary; write `~할 수 있습니다` or the plain active verb.

The checker warns on the agentive passives (`요구/정리/구성/확인/처리/제공/적용/
사용/운영/관리/구축/배포/저장/수집/검증 + 됩니다/되었습니다/되며`), on `에 의해`,
and on `할 수 있게 됩니다`. It does not read the sentence, so a legitimate
retention statement will warn too; that is a judgement call for the pass, not a
build failure.

## Rule 4c: literal nouns and verbs, no figurative language

A word for a physical thing or motion used for a non-physical one is a
metaphor, and it goes. Metaphor is the second most reliable tell after the
dash: it sounds like insight while saying nothing a number could not say
better. Frequent offenders in this skill's own output: 여정, 축 (for a
workstream), 뼈대, 큰 그림, 열쇠, 다리, 발판, 무대, 심장, 두뇌, 엔진, 톱니바퀴,
퍼즐, 지렛대, 밑거름, 이정표, 청사진, 나침반, 항해, 출발점, 씨앗, 열매, 울타리,
무기, 문을 열다, 길을 열다, 날개를 달다, and the verbs 쥐다, 번지다, 묶이다,
떠받치다, 이끌다 applied to systems or numbers.

| Generated | Written |
|---|---|
| `그 호스트가 전체 일정을 쥐고 있었습니다` | `호스트 한 대가 멈추면 정산 전체가 멈췄습니다` |
| `단계로 나눌수록 실패가 번지는 범위가 좁아집니다` | `단계로 나누면 실패한 단계만 다시 실행합니다` |
| `cron 한 대에 묶인 정산` | `EC2 한 대의 cron으로 돌던 정산` |
| `이 숫자들이 전환의 출발점입니다` | `전환 전 기준값: 6시간, 월 2회 실패, 월 5회 온콜` |
| `서버리스 여정을 시작하세요` | `작은 서비스 하나부터 옮겨 보세요` |
| `세 가지 축으로 비용을 낮췄습니다` | `세 가지 방법으로 비용을 낮췄습니다` |

Services doing their job is literal and stays: `Gateway가 인증을 처리합니다`,
`Runtime이 세션을 격리합니다`. `축` is literal in `시간축`, `X축`, `좌표축`.
Fixed technical terms that happen to be metaphors in origin (`파이프라인`, `버킷`,
`스트림`, `큐`, `브리지` in a product name) are vocabulary, not figures of speech,
and are never flagged.

## Rule 4d: state, do not rate

The line says what happened, what is true, or what follows. It does not say
that it matters, and it does not decorate the fact with an adjective of
approval. Evaluation words are filler that a reader skips and a sceptic
counts: 핵심(은/적인), 중요한, 혁신적, 획기적, 강력한, 놀라운, 탁월한, 최첨단,
차세대, 게임 체인저, 패러다임, 원활한, 매끄러운, 손쉽게, 시너지, 레버리지,
임팩트, 비즈니스 가치, 최적의, 완벽한, 성공적으로, 필수적, 궁극적으로,
인사이트, 다양한 (name the items instead), 효율적으로 (without a number),
이를 통해.

| Generated | Written |
|---|---|
| `숫자보다 중요한 변화는 새벽에 호출을 받지 않는 운영입니다` | `배치 온콜 호출: 월 5회에서 0회` |
| `이번 전환의 핵심은 기록을 밖으로 뺀 것입니다` | `실행 상태는 DynamoDB에, 중간 데이터는 S3에 둡니다` |
| `다양한 배치 작업에 적용할 수 있습니다` | `정산, 재고 집계, 정산 검증 배치에 같은 구조를 씁니다` |
| `성공적으로 전환을 완료했습니다` | `3개월 운영, 수동 재실행 0회` |
| `이를 통해 운영 효율이 개선됩니다` | `운영자가 새벽에 호출받는 일이 없어졌습니다` |

A consequence or a constraint is not evaluation and stays: `이 차이 때문에 cron
서버를 유지할 이유가 없습니다`.

## Rule 5: English anti AI tone

| Bad (AI reflex) | Good | Pattern |
|---|---|---|
| `A working cluster is an afternoon, not a project` | `A working cluster takes an afternoon.` | "X, not Y" antithesis, in any punctuation. Drop the foil. |
| `Your monolith got you here. Containers take you further.` | Cut it. State the concrete gain. | got-you-here cliché |
| `faster releases, right-sized costs, and resilience built in` | Keep the one that matters and quantify it | reflexive tricolon. Vary the count: sometimes two, often one. |
| `Start your modernization journey today` | Name the first concrete step | "journey" |
| `Organizations that modernize report higher productivity` | Cite a real number and source, or cut | unsupported hedge |
| `unlock`, `empower`, `leverage`, `seamless`, `robust`, `in today's fast-paced world` | use, let, run, connect | buzzword filler |
| A closing slide that restates the opening in new words | End on the ask or the next step | ring-closing reflex |

## Rule 6: rhythm

Sameness of shape reads as machine generated even when every line is fine
alone. This is the tell that survives every other rule (measured 2026-10-28:
three runs that passed Rules 1 to 5 still ended four or more lines per slide in
`~니다`), so it is a shape requirement, not advice:

- **A slide with four or more lines has at least two lines that end in a noun
  or a number**, written as a label or a figure (`수동 재실행 0회`, `전환 전
  기준값: 6시간, 월 2회 실패`, `DynamoDB에 실행 상태 기록`), and the rest as
  full sentences. The title counts as a line.
- **Consecutive bullets do not share an ending.** `~했습니다` after `~했습니다`
  becomes a noun phrase or a `~합니다` / `~입니다` sentence.
- Vary sentence length, and do not reach for three parallel items every time.

The checker warns when 80% or more of four or more lines on one slide end in
`~니다`. Four lines ending in `0회`, `48분`, `옮겼습니다`, `DynamoDB 기록` do
not trip it.

## The test that decides

Read each line aloud in the presenter's voice.

- Korean: *"발표자가 무대에서 이 문장을 소리 내어 말한다면 자연스러운가?"*
- English: *"Would an engineer actually say this out loud, or is it slideware?"*

Meaning first, word second. If you would never hear it spoken at a real tech
talk, rewrite it. This one question resolves most cases above, which is why it
is worth more than the tables.

## The copy pass

Run it after the deck builds and **before** visual QA, so QA judges the final
wording. Skip it only for a one or two slide edit, where applying the rules
inline is cheaper than a handoff.

Dispatch to whichever prose-writing agent the session has registered, for
example:

```
Agent(subagent_type: "<prose-writing agent>", prompt: <the brief below>)
```

If no such agent exists, run the pass inline instead: reread the whole deck's
copy against this file in one go, rather than checking each string as you write
it. The one-pass reread is what catches a dialect; a per-string check does not.

**The brief has to carry this file**, quoted or as a path the agent can read.
That is the whole mechanism: an agent without the contract writes the same dialect
the building model would. Measured 2026-08-20 on one deck-copy brief, banned
dashes went 8 (Opus 4.6) and 20 (Opus 5) with no contract in context, and 0 on
both with it. An earlier version of this section pinned the agent to a specific
model and explained the pin as a writing-quality difference; the pin is gone
because that model is being retired and because the measurement shows the contract
does the work.

If the agent is not registered in this session, say so rather than silently
running the pass on the session model. Either enable the `myauto` plugin or hand
the same brief to kiro CLI.

The brief must be self contained, because the agent sees none of this
conversation:

```
You are rewriting the on-slide copy of a presentation. Below is every string,
slide by slide, with its slot marked (title / subtitle / eyebrow / card label /
body / caption).

Rewrite freely. You are not patching lines, you are taking over the sentence
layer: replace any string that reads as machine drafted, translated, or
padded. Leave a string alone only when you would not improve it.

Hold these fixed: facts, numbers, product names, each slide's claim and role,
and roughly the original character count per string (the card is already sized,
so a much longer line will overflow).

Fix, in priority order:
1. Meta labels in title/subtitle/eyebrow/card-label slots: "왜 중요한가",
   "핵심 시사점", "더 큰 그림", "이것이 의미하는 것", "Why this matters",
   "Key takeaway". Replace with the answer itself, carrying its number. If the
   surrounding content does not contain the answer, write
   [확인 필요: <what is missing>] rather than inventing one.
2. Meta narration in sentences: "이는 ~을 의미합니다", "단순히 A가 아니라 B",
   "not just X but Y". Delete A, state B.
3. Em dash and en dash: banned outright in slide copy. Use a period, colon,
   line break, or ~ for ranges. Keep hyphenated compounds (cloud-native).
   Also banned: a middot (·) or bullet (•) used as a separator between phrases
   ("자동화 · 관측 · 회수"). Use a real list item, a comma, or a period. A
   leading list bullet is fine.
4. Korean 번역투: 여정 / 오버헤드 / 내재화 / 노브 / 상주, Latin-script product
   and pricing terms on a Korean slide (Pay-per-use, TCO), noun piles and
   stacked ~에 대한 / ~를 통해 where a verb is natural, ~에 있어, ~를 가능하게
   합니다, ~라고 볼 수 있습니다, ~에 관한 것입니다, sentences opening with
   이는/이것은. Default 존댓말. One rendering per concept deck wide.
5. Subject and voice (Korean): the subject is a team, a person, or a service
   and the verb is active. Rewrite abstract nouns that act ("이 숫자들이
   기준선이 됩니다", "핵심은 ~에 있습니다") and actor-less passives ("~됩니다",
   "~확인된 것은", "~할 수 있게 됐습니다") so the actor is named. Never "~에 의해".
6. Figurative language (Korean): replace every metaphor with the literal noun
   or verb. 여정, 축, 뼈대, 큰 그림, 열쇠, 발판, 출발점, 이정표, 지렛대, and
   systems or numbers that 쥐다 / 번지다 / 묶이다 / 이끌다 / 답하다.
7. Evaluation words (Korean): 핵심, 중요한, 혁신적, 강력한, 원활한, 최적의,
   성공적으로, 필수적, 인사이트, 다양한, 이를 통해. State the fact; drop the
   rating.
8. English AI tone: "X, not Y" reflexes, reflexive tricolons,
   journey/unlock/empower/leverage/seamless/robust, unsupported hedges.
9. Monotone rhythm: on any slide with four or more lines, at least two lines
   end in a noun or a number (`수동 재실행 0회`, `실행 상태: DynamoDB`), and no
   two consecutive bullets share an ending.

Speaker notes are prose and follow rules 4 to 9 like any other string; include
them in the table with slot "notes".

Never invent a number, name, date, or outcome. Write
[확인 필요: ...] in its place and list those at the end.

Return a table only: | Slide | Slot | Original | Rewrite |. Omit strings you keep.

<the extracted strings>
```

Apply the returned rewrites to the slide strings, rebuild, then re-run
`python3 scripts/pptx_qa_check.py <deck>.pptx --checks copy` before the visual QA pass. Any
`[확인 필요: ...]` items go to the user as questions; never ship one on a slide
and never fill one in with a plausible guess.
