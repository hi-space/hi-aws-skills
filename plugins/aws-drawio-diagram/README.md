# AWS draw.io Diagram Skill (aws-drawio-diagram)

> [vidanov/aws-architecture-diagram-skill](https://github.com/vidanov/aws-architecture-diagram-skill) (MIT) 을 기반으로 [hi-aws-skills](https://github.com/hi-space/hi-aws-skills) 에서 관리하는 포크. 아이콘 카탈로그를 draw.io 원본에서 **스크립트로 재생성**하고, 검증 스크립트와 draw.io에 없는 아이콘의 SVG 폴백을 더했습니다.

**한국어** | [English](README.en.md)

**말로 설명하면 편집 가능한 `.drawio` 파일이 나옵니다.**

> "Lambda, DynamoDB, API Gateway로 서버리스 API 구성도를 draw.io로 그려줘"

결과는 draw.io(diagrams.net)에서 바로 열어 고칠 수 있는 XML입니다. 아이콘은 draw.io에 내장된 공식 AWS Architecture Icons 스텐실을 쓰고, 모든 스텐실 이름은 draw.io 소스에서 생성한 카탈로그로 검증됩니다.

## 왜 아이콘이 깨지는가, 이 스킬은 어떻게 막는가

draw.io AWS 아이콘에는 `strokeColor` 규칙이 반대인 두 패턴이 있습니다.

| 패턴 | 스타일 | strokeColor |
|---|---|---|
| 서비스 | `shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.<name>` | `#ffffff` 필수 |
| 리소스 | `shape=mxgraph.aws4.<name>` | `none` 필수 |

여기에 더해 스텐실 이름은 서비스 리네임을 따라가지 않습니다(OpenSearch 는 여전히 `elasticsearch_service`). 이 스킬은 (1) draw.io 의 `Sidebar-AWS4.js` 와 `aws4.xml` 에서 생성한 1,000개 이상의 이름 카탈로그, (2) 리네임 별칭표, (3) 생성 후 자동 실행하는 검증 스크립트로 이 문제를 막습니다.

## 샘플

이 스킬로 만든 다이어그램입니다. 스킬은 네 단계로 일합니다. ① 아키텍처 브리프(구성요소·관계표·흐름·그룹·완결성 체크)를 먼저 쓰고, ② 브리프를 AWS가 공개한 가이드와 대조하는 아키텍처 리뷰를 합니다. Well-Architected 렌즈, 서비스 문서, AWS 공식 agent skills를 AWS Knowledge MCP 서버로 읽고, 모든 finding에 읽은 출처를 붙입니다. MCP 서버가 없으면 임의로 판단하지 않고 건너뛴다고 기록합니다. ③ 브리프만 보고 그리드 스펙(JSON)을 작성해 `scripts/build_diagram.py`로 `.drawio`를 생성·검증하고, ④ 렌더한 PNG를 브리프와 대조해 겹침·가독성·구성을 리뷰합니다. 240×170 그리드, 역할별 그룹 카드, Amazon Ember 글꼴, 직선 또는 한 번 꺾인 엣지가 규칙입니다(`references/layout-and-style.md`). `.drawio.png`는 XML이 내장되어 draw.io에서 바로 열어 편집할 수 있습니다(리뷰용 `.preview.png`는 같은 그림이며 완료 시 삭제됩니다). 모든 엣지에는 브리프 관계표의 **What flows** 문구가 그대로 글자로 올라갑니다 — 최대 3줄로 줄바꿈해서 직선이든 꺾인 선이든 자리가 있는 다리 위에 놓고, 경계·아이콘·다른 글자·다른 선과 겹치지 않는 곳만 고릅니다(그룹 상자 사이를 건너는 홉만 6자 이하 단어로 줄여야 합니다). 주요 엣지의 문구가 자리를 못 찾으면 빌드가 멈춥니다(`ERROR label`). `<name>.guide.md`는 관계 하나에 한 단계씩, 요청한 언어(한국어 요청이면 한국어 본문 + 영문 서비스명)로 풀어 쓰고 각 단계에 화살표의 글자를 (라벨 `…`)로 인용하며, `scripts/check_guide.py`가 언어·단계 누락·인용 누락을 기계적으로 검사합니다(`references/architecture-guide.md`). 소스코드 저장소를 입력으로 주면 IaC·SDK 호출·설정에서 구성요소를 근거(파일:행)와 함께 뽑아내고, 배포 단위마다 한 장씩 상세 다이어그램을 만듭니다(`references/from-source-code.md`). 추상 노드("플랫폼", "에이전트들")는 금지입니다. 노드 배치는 손으로 하지 않습니다. `scaffold_spec.py`가 brief를 스펙으로 옮기고 `build_diagram.py`가 자동 배치(`layout.py`)와 brief 대조 검사를 수행합니다.

![Agentic RAG Chat](docs/samples/agentic-rag-chat.drawio.png)

[brief](docs/samples/agentic-rag-chat.brief.md) · [spec](docs/samples/agentic-rag-chat.json) · [agentic-rag-chat.drawio](docs/samples/agentic-rag-chat.drawio)

![Order pipeline](docs/samples/order-pipeline.drawio.png)

[brief](docs/samples/order-pipeline.brief.md) · [guide](docs/samples/order-pipeline.guide.md) · [spec](docs/samples/order-pipeline.json) · [order-pipeline.drawio](docs/samples/order-pipeline.drawio) — Step Functions 팬아웃(한 번 꺾임), 한국어 제목, 13개 관계의 What flows 문구가 모두 선 위에 있고, 단계별 가이드가 이를 인용하는 예시

![IoT telemetry](docs/samples/iot-telemetry.drawio.png)

[brief](docs/samples/iot-telemetry.brief.md) · [spec](docs/samples/iot-telemetry.json) · [iot-telemetry.drawio](docs/samples/iot-telemetry.drawio) — 한 노드에서 위·아래로 두 번 갈라지는 허브(Lambda)와 클라우드 밖 수신자 예시

## 설치 (Claude Code)

```
/plugin marketplace add hi-space/hi-aws-skills
/plugin install aws-drawio-diagram@hi-aws-skills
/reload-plugins
```

스킬만 쓰려면 `skills/aws-drawio-diagram` 을 `~/.claude/skills/` 또는 `~/.kiro/skills/` 에 심링크하세요.

## PNG/SVG/PDF 내보내기

draw.io 데스크톱 CLI가 필요합니다. 헤드리스 리눅스는 `xvfb-run -a` 를 앞에 붙입니다.

```bash
drawio -x -f png -e -b 10 -o name.drawio.png name.drawio
```

**알려진 제약사항**

- 루트 권한 또는 CI 환경이라면 먼저 `drawio --version` 을 확인하세요. 최신 데스크톱 빌드는 `drawio` 바로 뒤에 `--no-sandbox` 가 필요하지만, 26.x 이하 빌드는 이 플래그를 모르는 인자로 취급해 `error: too many arguments` 로 종료합니다 — 이 경우 플래그를 빼고 비루트 사용자로 실행하세요.
- 설치된 draw.io보다 나중에 추가된 스텐실(예: `bedrock_agentcore`)은 단색 정사각형으로 렌더링됩니다. draw.io 데스크톱을 업데이트하거나 항상 최신 상태인 https://app.diagrams.net 에서 열어보세요. `shape=image` 폴백 아이콘은 영향받지 않습니다.

## 구성

```
skills/aws-drawio-diagram/
├── SKILL.md                    절차, 두 패턴 규칙, 아이콘 조회 순서, 검증
├── references/
│   ├── layout-and-style.md     레이아웃·엣지·그룹·멀티페이지 규칙
│   ├── aws-icons-<category>.md 생성물: 카테고리별 스텐실 표
│   ├── aws-icons-groups.md     생성물: 그룹 배지와 경계 스타일
│   ├── aws-icons-aliases.md    수기: 리네임 → 스텐실 이름
│   ├── aws-icons-legacy.md     생성물: 팔레트에 없지만 렌더되는 이름
│   ├── aws-icons-retired.md    생성물: 은퇴 팔레트
│   └── aws-icons-extra.md      생성물: draw.io에 없는 아이콘의 shape=image 스니펫
├── templates/                  참조 템플릿 5종
├── assets/extra-icons/         차집합 SVG (AgentCore 리소스 등)
└── scripts/
    ├── validate_drawio.py      생성 결과 검증 (스킬이 매번 실행)
    ├── build_icon_catalog.py   카탈로그 재생성 (Node 필요, 유지보수용)
    ├── build_extra_icons.py    차집합 아이콘 리포트/빌드 (유지보수용)
    └── stencil-index.json      검증기가 읽는 이름 색인
```

## 카탈로그 갱신 (유지보수)

```bash
scripts/fetch_sources.sh                       # draw.io dev 브랜치 스냅샷 갱신
python3 skills/aws-drawio-diagram/scripts/build_icon_catalog.py
python3 skills/aws-drawio-diagram/scripts/build_extra_icons.py --report   # 후보 확인 후 extra-icons.txt 편집
python3 skills/aws-drawio-diagram/scripts/build_extra_icons.py
python3 -m pytest tests -q
```

## 관련 스킬

문서·슬라이드용 완성 이미지(HTML/SVG/PNG)나 기존 `.drawio` 의 하우스 스타일 재작도는 형제 플러그인 [aws-diagram-design](../aws-diagram-design/) 이 담당합니다.

## 라이선스

MIT. 서드파티 고지는 [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).
