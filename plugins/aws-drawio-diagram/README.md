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

이 스킬로 만든 다이어그램입니다. `.drawio.png`는 XML이 내장되어 draw.io에서 바로 열어 편집할 수 있습니다.

![Agentic RAG Chat](docs/samples/agentic-rag-chat.drawio.png)

[agentic-rag-chat.drawio](docs/samples/agentic-rag-chat.drawio) · [설명](docs/samples/agentic-rag-chat.md)

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
