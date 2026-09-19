# aws-workshop-studio

*[English guide](./README.en.md)*

[netsgo0319/workshop-scaffold](https://github.com/netsgo0319/workshop-scaffold) 0.2.6 을 hi-aws-skills 로 가져와 커스터마이징한 포크입니다. 스킬·커맨드·에이전트 이름은 원본과 같고 플러그인 이름만 `aws-workshop-studio` 입니다. 전체 변경 내역은 [UPSTREAM.md](UPSTREAM.md), 출처 고지는 [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md) 에 있습니다.

원본과 다른 점

| 영역 | aws-workshop-studio |
|---|---|
| 왜 이 아키텍처인가 (INV-9) | 절차만 안내하던 원본에 **인사이트 계층**을 추가. 청사진 단계가 `artifacts/03a-architecture-rationale.md`(문제, 채택 아키텍처, 대안과 트레이드오프, 서비스별 역할·가치, 도입 전후, 씬별 인사이트 한 문장)를 쓰고, 이것이 없으면 생성 단계 진입이 차단됨(GATE-3f) |
| 개요 페이지 | `start/overview.md` 가 전체 아키텍처 다이어그램 + "왜 이 아키텍처인가" + "서비스별 역할과 가치" + "도입 전과 후" 섹션을 담음. `workshop-check.sh` 가 다이어그램과 섹션 마커 누락을 잡음(GATE-4e) |
| 씬·기능 페이지 | 씬마다 "왜 이 서비스인가" 표(없다면 무엇을 겪는지, 얻는 것), 기능마다 "Why this service" 섹션이 필수 |
| 페르소나 리뷰 | `insight-gap` 축 추가. 아키텍트·의사결정자 페르소나가 "그래서 왜 도입해야 하나"에 사이트만 보고 답할 수 있어야 함 |
| 아키텍처 다이어그램 | 손으로 drawio XML 을 쓰던 방식 대신 hi-aws-skills 의 **`aws-diagram-design`**(페이지용 PNG/SVG) 또는 **`aws-drawio-diagram`**(편집 가능한 원본)에 위임. 워크샵 전체 아키텍처 1장 + 시나리오별 1장이 필수 |
| 가치 서술의 정직성 | 모든 가치 주장에 신뢰도 라벨, 수치는 verified/documented 일 때만, 비교 대상은 경쟁사가 아니라 고객의 현재 방식 |

**워크샵 주제 · 시나리오 · 대상 고객**만 던지면, 사내에서 검증된 quick-\* VitePress 형식으로 핸즈온 워크샵 한 벌을 만들어 주는 Claude Code 스킬입니다. 기능 카탈로그·시나리오 실습·샘플 데이터셋·AWS 아키텍처 다이어그램·이미지 슬롯·고객 co-branding까지 생성하고, **레벨×직군 페르소나 패널**이 실제로 읽고 개선점을 냅니다.

매번 처음부터 짜는 대신 검증된 골격을 채우는 방식입니다. **이 스킬만 설치하면, 아무것도 없는 사람도 워크샵을 처음부터 끝까지 만들어 배포할 수 있게** 자체 완결형으로 구성돼 있습니다.

> 스킬 내부 문서(SKILL.md·references·templates)는 전 세계 SA와 공유하기 위해 영어로 작성돼 있습니다. 이 문서는 한국어 이용 가이드입니다.

---

## 데모 영상

[![데모 — 파이프라인이 다이어그램과 페이지를 그려내는 장면](https://img.youtube.com/vi/3aEmSaqTq44/maxresdefault.jpg)](https://youtu.be/3aEmSaqTq44)

*클릭해서 시청 — 스킬이 워크샵을 실제로 생성하는 장면: mermaid 플로우, AWS 아키텍처 다이어그램, 시나리오 페이지.*

이 스킬로 만든 **샘플 워크샵(라이브)**: **https://sample-workshop.yejinkm.people.aws.dev/**

---

## 무엇이 나오나

한 번 돌리면 대상 폴더에 이런 것들이 생깁니다.

- **VitePress 사이트** — 홈·아젠다·기능 카탈로그·시나리오별 실습 페이지. `npm run docs:dev`로 바로 보고, 빌드해서 배포합니다.
- **샘플 데이터셋** — 시나리오 로직에 맞는 현실적인 데이터(+필요 시 다국어 로케일 사본).
- **아키텍처/플로우 다이어그램** — 공식 AWS 아이콘으로 그린 그림.
- **이미지 슬롯** — 스크린샷·로고가 아직 안 들어간 자리를 빈 공간으로 표시하고, 무엇을 캡처해야 하는지 매니페스트로 정리.
- **`brief.yaml`** — 이 워크샵의 고정값(고객사·규모·일시·직군·시나리오·기술레벨…)을 담은 단일 출처(SSOT).
- **`artifacts/`** — 단계별 중간 산출물(연구 결과·청사진·페르소나 리뷰). 왜 이렇게 만들어졌는지 되짚을 수 있습니다.

---

## 준비물

- **Claude Code** — 이 스킬이 도는 환경
- **Node.js 18+** — 생성된 VitePress 사이트를 보고 빌드할 때
- **AWS 자격증명** — 배포(예: AWS Amplify)까지 할 경우에만

---

## 설치

hi-aws-skills 마켓플레이스에서 설치합니다:

```
/plugin marketplace add hi-space/hi-aws-skills
/plugin install aws-workshop-studio@hi-aws-skills
/reload-plugins
```

원본 `workshop-scaffold@workshop-scaffold-marketplace` 가 함께 켜져 있으면 같은 트리거에 스킬이 경쟁하므로 하나만 남기세요.

스킬 3개 — `workshop-scaffold`(전체 파이프라인), `aws-fact-check`(GA/리전/라벨 검증 단독), `persona-review`(레벨×직군 패널 평가 단독) — 와 커맨드 3개(`/aws-workshop-studio:new-workshop`, `/aws-workshop-studio:workshop-check`, `/aws-workshop-studio:workshop-walkthrough`), 에이전트 `aws-workshop-studio:participant-walker` 가 설치됩니다.

**또는 로컬 클론에서** (오프라인/개발용):

```bash
git clone https://github.com/hi-space/hi-aws-skills.git
claude plugin marketplace add ./hi-aws-skills
claude plugin install aws-workshop-studio
```

설치 후 실행 중인 세션에서는 `/reload-plugins`로 바로 로드됩니다(재시작도 가능). 이 플러그인의 스킬은 플러그인 루트의 `references/`·`scripts/`·`assets/` 를 참조하므로 다른 hi-aws-skills 스킬처럼 `skills/<name>` 디렉터리만 심링크하는 단독 설치는 동작하지 않습니다. 플러그인으로 설치하세요.

---

## 무엇이 들어있나

**스킬** — 대화에서 호출하는 것:

| 스킬 | 하는 일 |
|---|---|
| `workshop-scaffold` | **주로 쓰는 것** — 아래 8단계 파이프라인 전체 |
| `aws-fact-check` | 단독 사용: GA/리전/정확한 기능명 검증, 모든 주장에 신뢰도 라벨 |
| `persona-review` | 단독 사용: 아무 문서·덱·사이트나 레벨×직군 페르소나 패널로 평가 |

**커맨드** — 결정론적 진입점:

| 커맨드 | 하는 일 |
|---|---|
| `/aws-workshop-studio:workshop-walkthrough` | 참가자↔작성자 수정 루프 — QA 게이트를 여는 유일한 방법 |
| `/aws-workshop-studio:workshop-check` | 기계 QA(5축) + 참가자 플로우 리뷰 |
| `/aws-workshop-studio:new-workshop` | 골격 복사 + 브랜딩 토큰 치환 (파이프라인이 조립 단계에서 스스로 호출) |

**에이전트:**

- `participant-walker` — 신선한 눈의 참가자: 배포된 사이트를 실제 브라우저(Chrome CDP)로 클릭하며 걷고, 실행 가능한 단계를 전부 실행하고, 모든 판정에 **executed / inspected / untestable-here** 라벨을 답니다. 라운드마다 새 인스턴스 — 작성자가 자기 수정을 검증하는 일이 없게.

**생성된 워크샵마다 함께 심어지는 강제 장치** — 산문이 아니라 훅·게이트:

- **Stop 훅** → 매 턴 끝에 `workshop-check.sh --fix` 자동 실행 (데이터셋·발표자노트·이모지·에셋·비주얼)
- **PreToolUse 훅** → `protect-brief.mjs`가 인테이크 이후 `brief.yaml` 편집을 차단 — 변경은 `artifacts/00-amendments.md`로만
- **`scripts/gate.sh <단계>`** → 선행 산출물 없는 단계 착수를 하드 차단, 워크스루가 `WALKTHROUGH_RESULT: CLEAN`으로 끝나기 전엔 QA 진입 차단

**에셋·레퍼런스** — 파이프라인이 딛고 만드는 것:

- `assets/scaffold/` — 동작하는 VitePress 골격 (테마·컴포넌트·훅 내장)
- `assets/workshop-pipeline.workflow.mjs` — 같은 파이프라인의 멀티에이전트 Workflow 버전
- `references/` — 계약 문서들: format-spec · component-api · research-discipline · diagram-recipes · persona-rubric · branding · pipeline-contract · templates/
- `assets/brief.example.yaml` (입력 예시) · `examples/hanbitpay/` (실제 실행 중간 산출물)

---

## 빠른 시작 (아무것도 없는 상태에서)

```bash
# 1. 설치(1회) 후, Claude Code 안에서 /reload-plugins 실행(또는 재시작)
claude plugin marketplace add hi-space/hi-aws-skills
claude plugin install aws-workshop-studio

# 2. 새 빈 폴더에서 Claude Code 실행
mkdir my-workshop && cd my-workshop && claude
```

```
/aws-workshop-studio:workshop-scaffold   # 또는 그냥: "이 주제로 워크샵 만들어줘: …"
```

이게 전부입니다 — 골격 생성은 스킬이 알아서 합니다(조립 단계에서 `scripts/new-workshop.sh` 를 스스로 호출). 인테이크 질문에 답하면 이후 단계가 콘텐츠를 채우고 검증합니다.

---

## 사용법

새 워크샵을 만들 **빈 폴더**를 하나 만들고 그 안에서 Claude Code를 실행한 뒤:

```
/aws-workshop-studio:workshop-scaffold
```

자연어도 됩니다: `"식품 제조 고객 대상으로 Claude Code on Bedrock 워크샵 만들어줘."`

그러면 `brief.yaml`에 고정될 값들을 물어봅니다.

| 물어보는 것 | 예 |
|---|---|
| 주제 · 대상 AWS 서비스 | "Claude Code on Bedrock", "AgentCore" |
| 청중 (레벨 × 직군) | L200 개발자, L300 아키텍트 … |
| 시나리오 수 · 제목 | 3개: 개인 생산성 / 데이터 분석 / 외부 연동 |
| 소요시간 · 형식 | 4.5시간 · 실습(hands-on) / 부스(booth) / 발표주도 |
| 언어 | ko / en / ja |
| 고객사 | 이름 · 로고 · 업종 · 기술레벨 |
| 실행 모드 | `staged`(기본) 또는 `oneshot` |

입력 예시는 [`assets/brief.example.yaml`](assets/brief.example.yaml), 실제로 돌린 결과 예시는 [`examples/hanbitpay/`](examples/hanbitpay/)를 참고하세요.

---

## 무엇을 어떤 순서로 해주나 (파이프라인)

매 실행은 이 8단계를 밟습니다. `staged` 모드에서는 **★에서 멈춰 확인**을 받습니다.

| # | 단계 | 스킬이 해주는 것 | 산출물 |
|---|---|---|---|
| 1 | **인테이크** | 필요한 걸 전부 먼저 물어봅니다: 주제·청중(레벨×직군)·시나리오·시간·형식·언어 + **고객 로고·favicon 파일** + **디자인 취향**(컬러/무드, `auto`면 브랜드+서비스+페르소나로 도출) | `brief.yaml` (고정 SSOT) |
| 2 | **연구 ★** | **병렬 리서치** — 기업, 참가 직군의 실제 업무, 그리고 AWS 기술별 셀(GA/리전/preview를 그때그때 검증, 신뢰도 라벨) | `02-feature-facts.md`, `02a/02b` |
| 3 | **청사진 ★** | 시나리오 아크·씬 분해 + **시나리오 레벨링**(인접 씬 난이도 점프 ≤1, 씬당 신규 개념 ≤2), 기능↔씬 매핑, 씬별 비주얼 계획, 데이터셋·다이어그램 요구 | `03-blueprint.md` |
| 4 | **생성** | **기능 카탈로그**(1기능=1페이지), **복붙 가능한 프롬프트·코드 샘플이 든 씬별 실습 페이지**, 씬 로직을 만족하는 **현실적 데이터셋**, **다이어그램**(mermaid 플로우·drawio AWS 아이콘 아키텍처), 스크린샷 슬롯 | `docs/**`, `demo_datasets/**` |
| 5 | **조립** | VitePress config·내비·다국어 배선 + 깨끗한 빌드(죽은 링크 0) | 빌드된 사이트 |
| 6 | **검수** | 2중 검수: **레벨×직군 페르소나 패널**이 읽고 비평 → **새 참가자 에이전트가 실제로 따라하며**(단계 실행·링크/데이터셋/빌드/배포 확인) 막히면 작성자 에이전트가 수정, 클린 라운드까지 반복 | `06-persona-review.md`, `06b-walkthrough-*` |
| 7 | **QA** | 기계 점검(데이터셋·발표자노트·이모지·에셋·비주얼) + 빌드 — 워크스루가 클린이 아니면 QA 진입 자체가 차단됨 | `07-qa-report.md` |
| 8 | **핸드오프** | 캡처할 스크린샷 목록, 발표자 노트, 배포 절차, 사람 리허설 체크리스트·알려진 한계 | `08-handoff.md` |

**두 가지 모드**
- `staged`(기본): 연구·청사진 ★에서 사람 확인을 받고 진행. 처음 쓰거나 중요한 워크샵에 권장.
- `oneshot`: 멈춤 없이 끝까지. 단, 동일한 통과 조건을 검사하고 위반 시 중단.

**워크플로우로도 실행(선택):** [`assets/workshop-pipeline.workflow.mjs`](assets/workshop-pipeline.workflow.mjs)가 파이프라인을 멀티에이전트 Workflow(연구·생성·페르소나를 병렬 셀로)로 인코딩합니다. 워크플로우 오케스트레이션 사용에 동의해야 돌아가며, 동일한 게이트를 지킵니다.

---

## 이 스킬이 지키는 규칙 (알고 쓰세요)

결과물의 신뢰를 지키기 위해 스킬이 **일부러 하지 않는 것**들이 있습니다.

- **제품 스크린샷을 AI로 만들어 내지 않습니다.** 스크린샷 자리는 “실제로 이걸 캡처하세요” 슬롯으로만 남습니다.
- **아키텍처·플로우 다이어그램은 공식 AWS 아이콘**으로만 그립니다.
- **고객 로고·이름은 실제로 진행하는 고객 워크샵의 co-branding에만** 씁니다. 날조된 추천사·가짜 인용·미승인 로고 사용은 하지 않습니다.
- **AWS 기능 사실은 기억이 아니라 그때그때 검증**합니다. 리전 가용성·GA/preview는 실행 시점에 다시 확인하며, 검증/문서/추정을 **라벨로 구분**해 남깁니다.
- **발표자 전용 내용**(시연 팁 등)은 배포되는 `docs/` 밖 `PRESENTER_NOTES.md`에만 둡니다.

생성된 사이트의 기본 테마는 [`references/format-spec.md`](references/format-spec.md)의 규격을 따릅니다(예: 내비게이션 바는 불투명 배경 + 상단 고정).

---

## 문제가 생기면

- **스킬이 안 잡혀요** → `claude plugin list`에 `aws-workshop-studio`가 enabled로 보이는지 확인하고 `/reload-plugins`(또는 재시작)하세요.
- **빌드가 안 돼요** → 생성된 폴더에서 `npm ci` 후 `npm run docs:build`. Node 18+ 인지 확인.
- **AWS 기능 정보가 오래돼 보여요** → 리전/GA 정보는 실행 시점 기준입니다. 배포 전 `artifacts/`의 라벨과 `confirmed_date`를 다시 보세요.
