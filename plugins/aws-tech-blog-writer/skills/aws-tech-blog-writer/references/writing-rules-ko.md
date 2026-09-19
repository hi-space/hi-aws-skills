# Writing rules for Korean technical prose

The reader is an engineer or an architect who reads AWS blog posts to decide whether to try something.
They stop reading when a paragraph tells them nothing new, when a sentence sounds translated, or when the
text praises itself. These rules exist to keep them reading. `scripts/lint_blog.py` checks the mechanical
ones; the rest need your judgement during the style pass.

## 1. What good looks like

- One idea per sentence. A sentence carries a subject, a verb, and at most one qualifying clause.
- A paragraph makes one point and ends when the point is made. Three to five sentences is typical; a
  one-sentence paragraph is fine when it carries a decision or a result.
- Concrete over abstract: the service, the number, the error message, the file name. "응답 지연이 늘었다"
  is weaker than "p95 응답 시간이 1.2초에서 3.8초로 늘었다" and both are weaker than either with a source.
- The sentence says what happened and why. It does not comment on its own importance.
- Sentence length varies. Two long sentences in a row followed by a short one is how people write; ten
  sentences of the same length is how models write.
- The author's decisions appear as decisions: `A 대신 B를 선택했습니다. 이유는 ...입니다.` Not as
  inevitabilities (`B가 필수적입니다`).

## 2. Punctuation (hard errors in lint)

| Never | Why | Write instead |
|---|---|---|
| em dash `—`, en dash `–`, `--` as a dash | The single strongest machine-text marker in Korean | A period, a comma, a colon, or parentheses |
| middle dots `·` `•` `‧` `∙` `・` in prose | Reads as a slide, not a sentence | `,` and `및`/`와`; in a title `,` or `와` |
| arrows `→` `⇒` `->` in prose | Slide notation | `에서 ... 로`, `다음`, `이어서`; arrows are allowed inside code blocks and tables |
| check marks and emoji `✅ ✓ 🚀 ✨` | Decorative | Nothing |
| `~` except as a numeric range (`7월~8월`) | `~하기` in body text is an unfinished thought | Finish the sentence |
| ellipsis `…` or `...` in prose | Trails off | Finish the sentence; `# ...` inside code is fine |
| `!` in body text | Marketing | `.` |
| straight double quotes for emphasis (`"핵심"`) | Emphasis by quotation is a tic | Plain text, or backticks for identifiers |
| bold on whole sentences | Shouting | Bold at most a term or a short phrase, rarely |

Bullet lists are not forbidden, but a bulleted section is a slide. Convert a list to prose when the items
are sentences; keep it when the items are parallel nouns (a component inventory, links).

## 3. Translation-ese and machine tells (lint warns; you decide)

### Vocabulary to remove

`여정`, `혁신적인`, `획기적인`, `강력한`, `놀라운`, `탁월한`, `최첨단`, `차세대`, `게임 체인저`,
`패러다임`, `원활한/원활하게`, `매끄러운/매끄럽게`, `손쉽게`, `한층`, `한 걸음 더`, `시너지`, `인사이트`(when
`분석 결과`, `발견` works), `레버리지`, `임팩트`, `비즈니스 가치`, `디지털 전환의 핵심`, `든든한`,
`안정적이고 확장 가능한`(as a pair), `확장성과 유연성`(as a pair), `최적의`, `완벽한`, `성공적으로`,
`효과적으로`, `효율적으로`(when no measurement follows), `다양한`(when the items can be named), `핵심적인
역할`, `중요한 역할을 합니다`, `필수적입니다`, `궁극적으로`, `결론적으로`, `요약하면`, `정리하면`,
`주목할 점은`, `흥미로운 점은`, `놀랍게도`, `중요한 점은`, `핵심은 ~입니다`, `잊지 마세요`,
`살펴보도록 하겠습니다`(prefer `살펴봅니다`/`설명합니다`).

### Constructions to rewrite

| Pattern | Problem | Rewrite |
|---|---|---|
| `~에 있어`, `~함에 있어서` | Translated "in terms of" | `~에서`, `~할 때` |
| `~를 통해` more than once per paragraph | Translated "through" | `~로`, `~를 사용해`, or restructure |
| `이를 통해 ~할 수 있습니다` closing every paragraph | Formula | Say what actually happened |
| `~하는 것을 가능하게 합니다`, `~를 가능하게` | Translated "enables" | `~할 수 있습니다`, `~가 됩니다` |
| `~라고 할 수 있습니다`, `~라고 볼 수 있습니다` | Hedged assertion | Assert or cut |
| `~할 수 있게 됩니다` | Double auxiliary | `~할 수 있습니다` |
| `~되어집니다`, `~에 의해 ~되었습니다` | Passive stacking | Active with the team as subject |
| `단순히 ~가 아니라 ~입니다`, `~뿐만 아니라 ~도` | Negative parallelism | State the second half |
| `첫째, 둘째, 셋째` / `먼저, 다음으로, 마지막으로` in every section | Formula | Prose, or a table if three parallel items |
| Three adjectives or three nouns in a row, everywhere | Rule of three | Two, or the one that matters |
| `그것은`, `이것은`, `이는` starting a sentence | Pronoun subject | Repeat the noun |
| `~에 대해 알아보겠습니다` opening | Common but empty | State the question the section answers |
| Metaphors: `나침반`, `등불`, `항해`, `여정`, `심장`, `두뇌`, `무대`, `다리 역할`, `톱니바퀴`, `퍼즐`, `열쇠`, `문을 열`, `발판`, `날개를 달`, `엔진`(figurative), `레시피`, `지도`(figurative), `풍경` | Metaphor in technical prose | The literal thing |
| Rhetorical question followed by its answer, more than once per post | Device overuse | Statement |
| Paragraph ending on a "significance" sentence (`이는 ~의 중요성을 보여줍니다`) | Fake depth | Cut it. A closing sentence that states a consequence or constraint (`이 차이 때문에 ~를 그대로 쓸 수 없습니다`) is the author's voice and stays |
| `~하며`, `~하면서` chaining three clauses | Run-on | Split |
| `우리는`/`저희는` at the start of most sentences | Habit | Keep it where a decision or action is attributed (co-authored customer posts); otherwise the team name or the post |
| English loanwords with Korean equivalents in common use (`레벨`, `이슈`, `니즈`, `케이스`) | Jargon | `수준`, `문제`, `요구`, `사례`; but keep established terms (`파이프라인`, `프록시`) |

### Structural tells

- Every section ending with a summary sentence.
- Headings that are full sentences or that promise (`~하는 방법 완벽 정리`).
- A "장점/단점" or "도전 과제와 향후 전망" section written as parallel bullets with nothing measured.
- Introductions that describe the post ("이 글은 세 부분으로 구성됩니다") instead of starting it.
- Conclusions that repeat the introduction.

## 4. Before and after

Before:
> 본 프로젝트는 단순히 챗봇을 구축하는 것이 아니라, 경신의 데이터 여정에 있어 새로운 패러다임을 제시하는
> 혁신적인 시도였습니다. 이를 통해 구성원들은 다양한 업무를 원활하게 처리할 수 있게 되었습니다.

After:
> 이 프로젝트의 목표는 챗봇이 아니라, 사내 시스템의 데이터를 에이전트가 쓸 수 있는 형태로 바꾸는 표준
> 경로를 만드는 것이었습니다. 4주 뒤 HIS와 SAP 두 시스템이 MCP 서버로 노출되었고, 정보전략팀 담당자가
> 8월 28일에 두 번째 에이전트를 직접 배포했습니다. <!-- F04 F09 F21 -->

Before:
> AgentCore Gateway는 강력한 기능을 제공합니다. 첫째, 인증을 처리합니다. 둘째, 라우팅을 담당합니다. 셋째,
> 관측성을 제공합니다. 이러한 기능들은 프로덕션 환경에서 핵심적인 역할을 합니다.

After:
> AgentCore Gateway는 기존 시스템 앞에 두는 MCP 엔드포인트입니다. 인바운드 요청은 JWT 또는 IAM으로 인증하고,
> 도구 호출은 등록된 Lambda 타겟으로 전달합니다. 이 구성에서 HIS와 SAP 쪽 코드는 바꾸지 않았습니다.
> <!-- R03 F17 -->

Before:
> 결론적으로, 이번 PoC는 성공적으로 완료되었으며 경신의 AX 여정에 중요한 이정표가 되었습니다.

After:
> PoC 1단계는 8월 말에 끝났습니다. 다음 단계의 범위와 파트너 착수 시점은
> <span style="background-color:#FFF2CC;color:#7F6000;padding:1px 4px;">[작성자 확인] 9월 8일 최종보고에서
> 요청한 결정 (A) 프로덕션 전환 범위, (B) 파일럿 시점과 인원 규모의 결과를 적어 주세요. 결정이 나지 않았다면
> "검토 중"으로 표기합니다.</span>

## 5. Style pass procedure

1. Read each paragraph once for meaning. Ask: what does the reader know now that they did not before? If
   nothing, cut it.
2. Read it again for rhythm. Mark any three consecutive sentences with the same structure and vary one.
3. Search the draft for every item in §2 and §3; the lint script does the mechanical part.
4. Check every paragraph's last sentence. If it comments on significance, delete it; if it states a
   consequence, keep it (see author-voice.md §3).
5. Check the first sentence of every section. If it announces the section, replace it with the section's
   first fact.
6. Read the opening and the conclusion together. If the conclusion could be pasted over the opening
   without loss, rewrite the conclusion to say what happened and what is next.
7. Strip fact-ID comments (`<!-- F12 -->`) only after the fact-check pass has used them.
