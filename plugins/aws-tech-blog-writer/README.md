# AWS Tech Blog Writer (aws-tech-blog-writer)

AWS에서 구축한 프로젝트, PoC, 고객 사례를 **AWS 기술 블로그(aws.amazon.com/ko/blogs/tech)에 그대로 올릴 수 있는 원고**로 바꾸는 Claude Code 플러그인입니다. 스킬 두 개가 한 파이프라인을 이룹니다. `aws-tech-blog-writer`가 자료에서 초안을 만들고, `aws-blog-review`가 그 초안을 검토하고 고쳐 작성자가 코멘트를 달 수 있는 **Word(.docx) 파일**(글 제목이 파일 이름)을 냅니다. WordPress에 붙일 Markdown이 그 옆에 남습니다. 검토 스킬은 다 쓴 원고만 따로 받아도 같은 결과를 냅니다.

> "경신홀딩스랑 한 3A PoC를 AWS 기술 블로그 고객 사례 글로 써줘. 최종보고 PDF랑 전사록, drawio 파일이 ./docs/ks 에 있어."

## 이 스킬이 막는 네 가지 실패

| 실패 | 막는 방법 |
|---|---|
| 자료에 없는 내용을 지어낸다 | 모든 자료를 `S01`, `S02` ID로 등록하고 자료별 서브에이전트가 digest를 쓴 뒤 사실 목록(`01-facts.md`)으로 합친다. 초안의 모든 프로젝트 문장은 사실 ID를 달고, 사실이 없으면 문장 대신 placeholder를 쓴다 |
| 아키텍처 그림이 실제 구축과 어긋난다 | `aws-drawio-diagram`(편집 가능한 아키텍처), `aws-diagram-design`(개념도 PNG)에 사실 목록의 구성 요소 표로 브리프를 쓰고, 나온 그림의 모든 노드와 엣지를 사실 목록과 다시 대조한다 |
| 자료를 다 읽은 컨텍스트가 글까지 쓰다 문장이 무너진다 | 초안은 계획, 사실 표, 리서치, 다이어그램 manifest, `voice.md`만 받은 **새 서브에이전트**가 쓴다. 원본 자료와 digest, 대화 이력은 보지 않는다 |
| 기계가 쓴 문장처럼 읽힌다 | `voice.md`의 규칙(주어는 사람·팀·서비스, 행위자가 있으면 능동, 비유 명사 금지, 명사구 소제목, 평가어 금지)으로 쓰고 `lint_blog.py`가 의인화·피동·비유·서술형 소제목을 경고한다 |

기술 주장은 리뷰 스킬 안에서 새 컨텍스트의 팩트체커가 `aws-docs` MCP로 공식 문서를 열어 URL과 함께 검증(`05-claims.md`)하고 수정 목록만 돌려줍니다. 초안을 고치는 손은 리뷰 스킬의 개정 패스(R4) 하나입니다. 확인되지 않은 것은 삭제하거나 추측하지 않고 `[기술 검증 필요]` placeholder로 남깁니다. 검토를 거치지 않은 `04-draft.md`로는 Word 파일을 만들지 않습니다.

## Placeholder

작성자만 아는 사실은 네 가지 색으로 표시됩니다. Word 파일에서 그대로 보이고, 문서 마지막에 목록으로 한 번 더 정리됩니다.

| 태그 | 색 | 무엇 |
|---|---|---|
| `[작성자 확인]` | 노랑 | 수치, 날짜, 이름, 결정, 결과, 저자 소개 |
| `[기술 검증 필요]` | 빨강 | 공식 문서에서 확인하지 못한 기술 문장 (claim ID 포함) |
| `[이미지 필요]` | 파랑 | 콘솔 화면, 데모 캡처 |
| `[인용 승인 필요]` | 초록 | 고객사명, 로고, 인용문 |

## 파이프라인

`blog-work/<slug>/` 에 단계마다 파일을 남기므로 다음 세션이나 서브에이전트가 파일만 읽고 이어서 작업할 수 있습니다. 3단계는 병렬이고, 5단계는 같은 폴더에서 `aws-blog-review` 를 이어 돌리는 것입니다.

| Stage | 누가 | 산출물 |
|---|---|---|
| 1 브리프와 사실 목록 | digest는 자료별 서브에이전트, 통합은 메인 | `00-brief.md`, `sources/*.digest.md`, `01-facts.md` |
| 2 글 계획 (승인 게이트) | 메인 | `02-plan.md` |
| 3 리서치 ‖ 다이어그램 | 리서치 서브에이전트 ‖ 다이어그램 스킬 + 메인 검증 | `03-research.md` ‖ `diagrams/manifest.md`, `images/` |
| 4 초안 | `blog-drafter` 에이전트 (Read, Write만, packet 8개 파일) | `04-draft.md` |
| 5 `aws-blog-review` 에 인계 | `prepare_review.py 04-draft.md --in-place` 뒤 리뷰 스킬 R1~R5 | `review-report.md`, `revised.md`, `<제목>.docx` |

## 두 번째 스킬: aws-blog-review

원고를 검토하고 개정본과 Word 파일까지 내는 스킬입니다. writer 스킬이 5단계에서 `--in-place` 로 넘긴 `04-draft.md` 를 같은 `blog-work/<slug>/` 에서 이어 받거나, 사용자가 보낸 Markdown 또는 Word(.docx) 초안을 `blog-review/<slug>/` 에 받아 작업합니다.

> "이 블로그 초안 게재 전에 검토해줘. 최신 AWS 정보랑 맞는지, 기술적으로 틀린 거 없는지, 그림 캡션이랑 서비스명 링크도 봐줘."

| 단계 | 누가 | 산출물 |
|---|---|---|
| R1 Intake | `prepare_review.py` (docx는 pandoc 변환, 이미지 복사; `--in-place` 면 writer 작업 폴더 그대로) | `draft.md`, `images/` |
| R2 린트 ‖ 팩트체크 ‖ 스토리 리뷰 (병렬) | `lint_blog.py` ‖ `blog-fact-checker` (최신성 확인 포함) ‖ `blog-reviewer` (Read, Write만; 그림도 열어 봄) | `lint.txt` ‖ `05-claims.md` ‖ `story.md` |
| R3 보고서 (승인 게이트) | 메인 | `review-report.md` |
| R4 개정 | 메인 (유일한 편집자, 모든 수정은 finding ID로 추적) | `revised.md`, `placeholders.md` |
| R5 검증과 빌드 | 메인 | `<제목>.docx` (첫 H1이 파일 이름) |

여섯 기준으로 봅니다. A 최신성(이름 변경, preview→GA, 리전), B 기술 정확성(코드 블록 포함), C 그림 캡션, D 첫 등장 서비스의 공식 이름과 공식 문서 하이퍼링크(린트 E8), E 스토리와 논리(요지, 섹션별 독자 질문, 그림 배치, 연결, 결론, 중복과 공백, 유형, 비중), F 문체. 지적은 차단 / 수정 / 권고 세 등급이고, 개정본은 보고서의 지적만 반영하며 모르는 사실은 placeholder로 남깁니다.

## 에이전트

초안, 팩트체크, 스토리 리뷰는 플러그인의 커스텀 에이전트(`agents/`)가 맡습니다. 도구 목록을 하네스가 강제하므로 드래프터는 웹을 검색하거나 원본 자료를 열 수 없고, 팩트체커는 문서 도구와 파일 쓰기만 갖습니다. 프롬프트 템플릿(`templates/prompt-*.md`)은 파일 경로와 이 글의 변수만 담습니다.

| 에이전트 | 도구 | 역할 |
|---|---|---|
| `blog-drafter` | Read, Write | packet 8개 파일만 읽고 `04-draft.md`를 한 번에 씀 |
| `blog-fact-checker` | Read, Write, WebFetch, `aws-docs`/`aws-mcp` 문서 도구 | 기술 주장마다 공식 문서를 열어 `05-claims.md`와 수정 목록을 돌려줌. 초안은 안 건드림 |
| `blog-reviewer` | Read, Write | 초안과 그림만 읽는 첫 독자. 요지 한 문장, 섹션별 독자 질문 지도, 그림 표, 구조 지적을 `story.md`로 돌려줌. 초안은 안 건드림 |

자료 digest와 리서치는 general-purpose 서브에이전트가 맡습니다.

## 문체

`references/voice.md` 한 파일이 초안 작성자와 리뷰 스킬의 개정 패스가 공유하는 계약입니다. 핵심 규칙 다섯 가지:

- 주어는 사람, 팀, 서비스, 컴포넌트. 추상명사(문제, 질문, 조건, 선택)는 남거나 따라오거나 쌓이거나 결정하지 않는다.
- 행위자가 있으면 능동. `~로 정리됩니다`, `~가 요구됩니다`는 누가 했는지 쓴다. `~에 의해`는 쓰지 않는다.
- 비유 명사 금지. 축, 몫, 재료, 그림, 여정, 열쇠는 문자 그대로의 명사로 바꾼다.
- 소제목은 명사구. 서술형 문장(`~는 다른 문제다`)과 질문은 쓰지 않는다.
- 평가어 금지. 중요한, 핵심, 의미 있는 대신 무슨 일이 있었는지만 쓴다.

## Word 파일 (aws-blog-review R5)

`docx` 스킬의 docx-js 워크플로로 만듭니다. pandoc의 DOCX writer는 인라인 색을 버려 placeholder가 보이지 않으므로 쓰지 않습니다.

```bash
node skills/aws-tech-blog-writer/scripts/build_docx.js blog-work/<slug>     # revised.md → <제목>.docx
```

파일 이름은 `revised.md` 의 첫 H1(글 제목)에서 파일명에 쓸 수 없는 문자를 뺀 것입니다. pandoc이 Markdown을 파싱하고 docx-js가 렌더링합니다. placeholder span은 같은 두 색으로 shading된 run이 되고, 그림은 본문 폭에 맞춰 `그림 N.` 캡션과 함께 들어가며, 표와 코드 블록은 구조를 유지하고, `placeholders.md`가 마지막 섹션으로 붙습니다. 스크립트 끝의 검증 블록이 Markdown과 DOCX의 이미지 수와 태그별 placeholder 수를 비교해 일치할 때만 exit 0 입니다.

## 설치

```
/plugin marketplace add hi-space/hi-aws-skills
/plugin install aws-tech-blog-writer@hi-aws-skills
```

스킬 두 개(`aws-tech-blog-writer`, `aws-blog-review`)와 에이전트 세 개가 함께 설치됩니다. `aws-blog-review` 는 형제 스킬의 스크립트를 상대 경로로 쓰므로 플러그인으로 설치하거나 `skills/` 디렉터리를 통째로 심링크하세요.

필요한 도구: `pandoc`, `node` 와 전역 `docx` 패키지(`npm install -g docx`), Python 3. 다이어그램 단계는 같은 마켓플레이스의 `aws-drawio-diagram`, `aws-diagram-design` 플러그인을, 사실 검증은 `aws-docs` MCP 서버를 씁니다.

## 스크립트

| 스크립트 | 용도 |
|---|---|
| `scripts/init_workspace.py <slug>` | 작업 디렉터리와 템플릿 생성 |
| `scripts/ingest_sources.py <work>` | PDF / DOCX / PPTX / drawio 자료를 텍스트로 변환 |
| `scripts/lint_blog.py <draft.md> [--final] [--placeholders-out <file>]` | 문장부호, 서비스명, 이미지와 캡션, 코드, placeholder, 문체(의인화, 피동, 비유, 서술형 소제목) 검사 |
| `scripts/check_claims.py <work> --draft <file>` | `05-claims.md` 검증과 개정본 placeholder 대조 |
| `scripts/build_docx.js <work> [--out <file>] [--name-from-title] [--no-appendix]` | `revised.md` 로 `<제목>.docx` 빌드와 검증 |

## 테스트

```bash
pytest plugins/aws-tech-blog-writer/tests
```
