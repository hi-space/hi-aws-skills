# Companion guide — `<name>.guide.md`

The brief is the Drawer's contract: ids, stencil names, table cells. The guide is what a reader opens next to the
picture: it walks the architecture **one numbered step per relationship**, in sentences, and each step **quotes
the text drawn on that arrow** (the brief's *What flows* phrase) — the reader sees `order message` on the picture
and finds the step that says (라벨 `order message`). Write it after the Reviewer's `ready`, from the brief and the
final `.drawio.png`. It is the third deliverable next to `.drawio` and `.drawio.png`, and
`scripts/check_guide.py <name>.guide.md <name>.brief.md` must pass before hand-off.

**Language.** The brief's `Language:` line (Phase 1) is the language the *user* wrote in — write the whole guide in
it. `ko` → Korean prose, Korean section headings, AWS service names and protocol names in English (`API Gateway`,
`SQS`, `HTTPS`, `SigV4`). The English of the code or of the brief is not a reason to write English; the checker
measures the Hangul share and refuses an English guide for `Language: ko`.

**Numbering and quoting.** One step per row of the brief's Relationships, in `#` order, list number = `#`. Every
step ends with the phrase as it is drawn — `(라벨 \`put order\`)` — copied from the brief's *What flows* cell
(the checker looks for it, case- and space-insensitive). A dashed edge whose text the builder dropped
(`note: label dropped`) still quotes the phrase and says the arrow has no text. An aux row that is not drawn
still gets its step, marked "(그림에 없음 / not drawn)". Do not merge steps; a fan-out is two steps that read alike.

Length: an overview screen plus the step list. Every step is one to three sentences. No bullet dumps of table
cells — the brief already has those.

## Template (Language: ko)

```markdown
# <제목>

<두세 문장: 이 시스템이 무엇을 누구에게 해 주는지, 요청 경로의 모양 — 진입점과 데이터가 최종적으로 놓이는 곳.>

![<제목>](<name>.drawio.png)

## 다이어그램 읽는 법
- **그룹** — 역할 그룹마다 한 줄: 무엇이 들어 있고 왜 묶었는지 ("API & Ingestion: 비즈니스 로직 전에 요청이 거치는 것들").
- **선** — 실선 = 동기 호출, 점선 = 비동기·보조, 빨간 점선 = 오류 경로. 선 위의 글자가 그 홉에서 **무엇이
  흐르는지**이고, 아래 단계마다 같은 글자를 `라벨`로 인용했으니 그림에서 그 화살표를 찾으면 된다.
- 사용자와 외부 시스템은 AWS Cloud 상자 밖에 있다.

## 단계별 흐름
<관계표 한 행에 한 단계, `#` 순서, 목록 번호 = `#`. 각 단계: **From → To**를 굵게, 이어서 무엇이 흐르고 왜인지,
동기/비동기, 실패하면 어떻게 되는지(중요할 때), 끝에 화살표의 글자를 (라벨 `…`)로. 서비스 이름은 브리프의 표기
그대로(영문).>

1. **Mobile client → API Gateway** — 앱이 REST 엔드포인트를 HTTPS로 호출한다. API Gateway가 TLS를 종료하고
   요청 형식을 검증하고 스로틀링한다. (라벨 `order requests`)
2. **API Gateway → SQS** — 주문을 메시지로 큐에 넣고 클라이언트에는 즉시 202를 돌려준다. 이 큐가 비동기 경계라서
   뒤쪽 처리가 느려져도 주문 접수는 멈추지 않는다. (라벨 `order message`)
3. **API Gateway → Cognito** — 모든 호출에서 bearer 토큰을 검증한다. 점선: 요청 데이터 경로의 한 홉이 아니라
   요청 옆에서 도는 검사다. (라벨 `token validation`)
4. …
7. **Step Functions → Payment** — 결제 Lambda를 task로 호출한다. 꺾인 선의 위쪽 다리에 글자가 있다; 8번 Inventory
   호출과 같은 종류의 task 호출이다. (라벨 `task invoke`)
…
12. **DynamoDB → S3** — 주문 테이블을 주기적으로 S3에 내보낸다(point-in-time export). 점선·보조. (라벨 `PITR export`)

## 서비스
| 서비스 | 이 시스템에서의 역할 | 비고 |
|---|---|---|
| API Gateway | REST 진입점, TLS 종료, 스로틀링 | regional endpoint |
| … | … | … |
| (not drawn) IAM role | Lambda 실행 역할 | 그림에 없음 |

## 설계 결정
- <브리프 Decisions & assumptions의 모든 줄을, 결과까지 포함한 문장으로.>
- <수용한 Architecture review finding 전부, 출처 URL과 함께.>
- <아이콘 대체: "AgentCore Gateway는 AgentCore SVG로 그렸다 — draw.io에 스텐실이 없다.">
- <그리지 않은 보조 관계: "모든 서비스가 CloudWatch에 로그를 쓴다; API Gateway 엣지 하나만 그렸다.">

## 이 다이어그램에 없는 것
<의도적으로 뺀 것 — VPC·서브넷, IAM 역할, CI/CD — 과 다른 곳에 그렸다면 어디인지.>
```

For `Language: en` use the same structure with the headings `## How to read the diagram`, `## Step-by-step`,
`## Services`, `## Design decisions`, `## Not in this diagram`. The checker accepts either set of headings.

## Rules

- **One step per relationship, numbered like the brief's `#`** — primary and aux, drawn or not. The checker refuses
  a guide with a missing step number, a step that does not name both endpoints (component id or the brief's
  service name), or a step that does not quote its row's *What flows* phrase. Re-numbering the brief after
  Phase 3 makes the guide disagree with the brief: do not.
- **Every Components row appears in Services**, the "not drawn" ones too, marked so.
- Prose, not table cells: "Lambda가 큐를 배치로 폴링해서 주문을 DynamoDB에 쓴 뒤 saga를 시작한다" — not
  "batch poll / put order".
- Explain the *why* where the brief only says *what*: why a queue here, why the export is dashed, why Cognito is
  beside the path rather than on it.
- Quote the arrow's text in every step ("(라벨 `order message`)"); when the builder dropped a dashed edge's text,
  quote the phrase anyway and add "(그림의 선에는 글자 없음)" so the reader knows what to look for.
- No claims the brief and the Architecture review do not support. The guide explains the diagram; it does not
  invent capacity figures, SLAs or best-practice verdicts. Where the review accepted a finding, say so with the
  source.
- Same file-name stem as the diagram, `.guide.md`; the image link points to the `.drawio.png` beside it. One
  guide per output set — a repo with three deployable units gets three guides.
