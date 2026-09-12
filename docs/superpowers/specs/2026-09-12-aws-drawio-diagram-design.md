# aws-drawio-diagram 플러그인 설계

날짜: 2026-09-12
상태: 승인됨

## 목적

AWS 아키텍처를 **편집 가능한 `.drawio` XML**로 생성하는 스킬을 `hi-aws-skills` 마켓플레이스에 두 번째 플러그인으로 추가한다.
[vidanov/aws-architecture-diagram-skill](https://github.com/vidanov/aws-architecture-diagram-skill)
(MIT, 커밋 `29c1bab`)을 기반으로 하되, 아이콘 카탈로그는 손수 작성한 부분 목록을 복사하지 않고
draw.io 원본 `Sidebar-AWS4.js`에서 스크립트로 재생성한다. draw.io 내장 스텐실에 없는 아이콘은
공식 아이콘 팩과의 차집합만 SVG로 동봉해 `shape=image` 폴백으로 쓴다.

## 배경과 근거

두 플러그인은 아이콘을 다른 방식으로 다룬다.

| | aws-diagram-design (기존) | aws-drawio-diagram (신규) |
|---|---|---|
| 산출물 | HTML/SVG/PNG 에디토리얼 다이어그램 | 편집 가능한 `.drawio` XML (+ PNG/SVG/PDF export) |
| 아이콘 소스 | 공식 SVG 824개 동봉 | draw.io 내장 `mxgraph.aws4.*` 스텐실 **이름** |
| draw.io 관계 | `.drawio` → 재작도 (역방향) | `.drawio` 생성 (정방향) |

draw.io `dev` 브랜치(커밋 `f3abfe0`) 기준 스텐실 수와 vidanov 카탈로그의 갭:

| 항목 | 개수 |
|---|---|
| draw.io service-level (`resIcon=`) | 329 |
| draw.io resource-level (`shape=`) | 578 |
| draw.io group (`grIcon=`) | 15 |
| vidanov 카탈로그 등재 | 382 |
| draw.io에 있으나 vidanov 누락 service-level | 156 |
| vidanov에 있으나 draw.io에 없는 이름 | 최소 5 (`cloud_hsm`, `vpc_peering`, `log_group`, …) |

draw.io 자체에 없는 아이콘도 있다. 공식 팩과 저장소 소유자가 트레이싱한 Amazon Bedrock AgentCore
리소스 아이콘 11개가 대표적이다. draw.io에는 `bedrock_agentcore` 서비스 아이콘 하나만 있다.

## 결정 사항

1. **별도 플러그인**으로 만든다. 합치지 않는다.
   - 트리거 충돌 방지: "draw.io로", "편집 가능하게" 가 명확한 분기점이 된다.
   - aws-diagram-design은 masangbeom 1.2.0 포크라 다른 계보를 섞으면 업스트림 동기화가 어려워진다.
2. 이름은 `aws-drawio-diagram`.
3. 3D/아이소메트릭(aws3d, Allied Telesis)은 **제외**. 필요하면 후속 작업.
4. draw.io에 없는 아이콘은 **차집합만** `assets/extra-icons/`에 SVG로 복사한다. 824개 전체를 중복하지 않고, 형제 플러그인 경로도 참조하지 않는다.

## 디렉터리 구조

```
plugins/aws-drawio-diagram/
├── .claude-plugin/plugin.json
├── plugin.json                       # agent-plugins.org 스키마 (기존 플러그인 관례)
├── LICENSE                           # MIT © Alexey Vidanov, © hi-space
├── THIRD_PARTY_LICENSES.md
├── README.md                         # 한국어
├── README.en.md
├── skills/aws-drawio-diagram/
│   ├── SKILL.md
│   ├── references/
│   │   ├── aws-icons-<category>.md   # 생성물 (build_icon_catalog.py)
│   │   ├── aws-icons-groups.md       # 생성물: grIcon 15개 + 로직 그룹 스타일
│   │   ├── aws-icons-extra.md        # 생성물 (build_extra_icons.py)
│   │   ├── aws-icons-aliases.md      # 수기 유지: 서비스 리네임 → 스텐실 이름
│   │   └── layout-and-style.md       # 레이아웃/엣지/캔버스/멀티페이지 규칙
│   ├── templates/*.drawio            # vidanov 5종 그대로
│   ├── assets/extra-icons/*.svg      # 차집합 SVG
│   └── scripts/
│       ├── validate_drawio.py        # vidanov 것 + isometric 오탐 제거
│       ├── build_icon_catalog.py
│       ├── build_extra_icons.py
│       └── extra-icons.txt           # 차집합 허용 목록 (수기 확정)
├── scripts/
│   └── fixtures/
│       ├── Sidebar-AWS4.js           # 파싱 소스 스냅샷
│       └── SOURCE.md                 # 스냅샷 출처 URL + 커밋 해시 + 라이선스
└── tests/
    ├── test_build_icon_catalog.py
    ├── test_validate_drawio.py
    └── fixtures/                     # 최소 .drawio 샘플
```

## 컴포넌트

### build_icon_catalog.py

- **입력:** `scripts/fixtures/Sidebar-AWS4.js` (기본), `--source <path|url>` 로 교체 가능.
- **처리:**
  1. `setCurrentSearchEntryLibrary('aws4', 'aws4<Section>')` 호출을 경계로 파일을 섹션 단위로 자른다.
     섹션 이름이 카테고리가 된다. 총 30개 섹션 = 서비스 카테고리 26개(Analytics, Application Integration, …, Storage) + Arrows, General Resources, Illustrations, Groups.
  2. 각 섹션에서 `createVertexTemplateEntry(<style>, w, h, '', '<label>', …)` 호출을 파싱한다.
     스타일 문자열은 `n + '<name>;'`, `n3 + 'resourceIcon;resIcon=' + gn + '.<name>;'`, `grIcon=' + gn + '.<name>'` 등
     문자열 연결 형태이므로 정규식이 아니라 `+`로 이어진 리터럴을 모두 결합한 뒤 `mxgraph.aws4.<name>`을 추출한다.
     단순 정규식은 `quicksight`, `product` 같은 변형을 놓친 것이 확인되었다.
  3. 분류: `resIcon=`에 오면 **service**, `grIcon=`이면 **group**, 그 외 `shape=mxgraph.aws4.<name>`이면 **resource**.
  4. 표시명은 라벨 인자에서 가져오고, 같은 이름이 여러 섹션에 나오면 첫 섹션에 둔다.
- **출력:** 카테고리별 `references/aws-icons-<slug>.md`. 각 파일 상단에 `fillColor`(카테고리 색), 패턴별 필수 `strokeColor`,
  그리고 "생성물이니 수정하지 말 것" 헤더. 표 형식은 vidanov와 동일하게 `| name | Display Name |` 두 열을 유지해 모델이 익숙한 형태로 읽게 한다.
  Arrows/Illustrations 는 `aws-icons-general.md` 한 파일로 합친다.
- **실패 조건:** 섹션이 0개이거나 service 이름이 300개 미만이면 파싱 실패로 보고 종료 코드 1. 소스 형식이 바뀌었다는 신호다.

### build_extra_icons.py

- **입력:** 공식 팩 아이콘 디렉터리 경로 (`--icons <dir>`, 기본값은 형제 플러그인 `../aws-diagram-design/skills/aws-diagram-design/assets/aws-icons`),
  카탈로그 생성 결과, `scripts/extra-icons.txt`.
- **처리:**
  1. `--report` 모드: 공식 팩 파일명을 정규화(`Arch_Amazon-Bedrock-AgentCore_48` → `bedrock_agentcore`, `Res_AWS-Lambda_Lambda-Function_48` → `lambda_function`)해
     카탈로그 이름과 비교하고, 매칭 안 되는 후보 목록을 stdout에 낸다. 자동 매칭은 오탐이 있으므로 **참고용**이다.
  2. 기본 모드: `extra-icons.txt`(한 줄에 `<아이콘 디렉터리 기준 상대 경로>|<표시명>`, `#` 주석 허용)에 적힌 파일만 `assets/extra-icons/`로 복사하고, 각 파일을 base64로 인코딩해
     `references/aws-icons-extra.md`에 `shape=image;aspect=fixed;image=data:image/svg+xml;base64,…` 스니펫과 표시명, 권장 크기(78×78)를 쓴다.
- **초기 허용 목록:** AgentCore 리소스 11개 (AgentCore, AI Agent, Runtime, Gateway, Memory, Identity, Observability, Policy Engine, Evaluations, Browser Tool, Code Interpreter).
  `--report` 결과에서 명백한 것만 구현 중 추가한다.

### validate_drawio.py

vidanov `tests/validate_drawio.py`를 가져오되 다음을 바꾼다.

- Issue #2 (`exitX`/`entryX` 누락 경고)는 `edgeStyle=orthogonalEdgeStyle`인 엣지에만 적용한다. CHANGELOG에 기록된 isometric 오탐 제거.
- 새 검사 추가: 모든 `resIcon=`/`shape=mxgraph.aws4.` 이름이 생성된 카탈로그(references/*.md)에 존재하는지 확인. 없으면 오류.
- 새 검사 추가: service-level(`resIcon=`)에 `strokeColor=#ffffff`, resource-level에 `strokeColor=none`이 아니면 오류.

### SKILL.md

vidanov 플러그인판 SKILL.md를 기반으로 다음을 바꾼다.

- **frontmatter description**에 한국어 트리거 추가: `draw.io로 그려줘`, `드로우아이오`, `편집 가능한 구성도`, `drawio 파일로`.
  그리고 구분 문장: "HTML/SVG/PNG 에디토리얼 결과물이 필요하면 aws-diagram-design 스킬을 쓴다."
- 레이아웃/엣지/캔버스/멀티페이지/오디언스 모드 규칙은 `references/layout-and-style.md`로 옮기고 SKILL.md는 절차와 핵심 규칙(두 아이콘 패턴, 검증, 출력)만 남긴다.
- **아이콘 조회 순서:** ① 카테고리 참조 파일 → ② `aws-icons-aliases.md` → ③ `aws-icons-extra.md`(shape=image) → ④ 그래도 없으면 상위 서비스 아이콘으로 대체하고 사용자에게 알린다. 절대 이름을 추측하지 않는다.
- 생성 후 `scripts/validate_drawio.py`를 반드시 실행하고, 오류가 있으면 고친 뒤 재검증.
- export 안내는 Linux `drawio` CLI를 기본으로, macOS 경로를 보조로 적는다.
- 3D 관련 내용은 넣지 않는다.

### 패키징

- `.claude-plugin/plugin.json`: name `aws-drawio-diagram`, version `1.0.0`, MIT, keywords에 `drawio`, `aws-icons`, `editable`.
- `plugin.json`(루트): 기존 aws-diagram-design 관례와 동일한 스키마.
- `THIRD_PARTY_LICENSES.md`: vidanov(MIT), draw.io `Sidebar-AWS4.js` 파싱 소스(Apache-2.0, 스냅샷만 fixtures에 보관하고 배포물에는 파생 md만 포함), AWS Architecture Icons 약관, 트레이싱 AgentCore 아이콘 고지(aws-diagram-design과 동일 문구).
- `.claude-plugin/marketplace.json`에 두 번째 항목 추가. 루트 `README.md` 표에 행 추가와 "생성은 aws-drawio-diagram, `.drawio` 재작도는 aws-diagram-design" 안내.

## 테스트

1. `test_build_icon_catalog.py`
   - fixtures의 `Sidebar-AWS4.js`로 생성 시 service ≥ 300, resource ≥ 500, group = 15.
   - vidanov 템플릿 5종 + 예제 3종에 등장하는 모든 `mxgraph.aws4.*` 이름이 카탈로그에 존재.
   - `lambda`는 service, `lambda_function`은 resource, `group_vpc2`는 group으로 분류.
   - 소스가 비어 있거나 섹션이 없으면 종료 코드 1.
2. `test_validate_drawio.py`
   - 템플릿 5종 통과.
   - service-level에 `strokeColor=none`을 쓴 샘플은 실패.
   - 카탈로그에 없는 이름을 쓴 샘플은 실패.
   - `isometricEdgeStyle` 엣지의 `exitX` 누락은 경고하지 않음.
3. 수동: `/usr/bin/drawio -x -f png` 로 템플릿 1종 렌더해 빈 아이콘 여부 육안 확인. 헤드리스 환경에서 실패하면 xvfb 필요 여부를 기록.

## 범위 밖

- 3D/아이소메트릭 지원.
- ChatGPT/Kiro용 프롬프트 파일 (`chatgpt/`, `kiro/`). 이 저장소는 Claude Code 플러그인이 1차 대상이고 스킬 디렉터리 심링크로 Kiro도 커버된다.
- aws-diagram-design 쪽 변경. import-drawio는 그대로 둔다.
- 슬래시 커맨드. 스킬 트리거로 충분하며 필요 시 후속 추가.
