# AWS Tech Blog Writer (aws-tech-blog-writer)

AWS에서 구축한 프로젝트, PoC, 고객 사례를 **AWS 기술 블로그(aws.amazon.com/ko/blogs/tech)에 그대로 올릴 수 있는 원고**로 바꾸는 Claude Code 플러그인입니다. 결과물은 작성자가 검토하고 코멘트를 달 수 있는 **Word(.docx) 파일**이고, WordPress에 붙일 Markdown이 그 옆에 남습니다.

> "경신홀딩스랑 한 3A PoC를 AWS 기술 블로그 고객 사례 글로 써줘. 최종보고 PDF랑 전사록, drawio 파일이 ./docs/ks 에 있어."

## 이 스킬이 막는 세 가지 실패

| 실패 | 막는 방법 |
|---|---|
| 자료에 없는 내용을 지어낸다 | 모든 자료를 `S01`, `S02` ID로 등록해 끝까지 읽고 사실 목록(`01-facts.md`)을 만든다. 초안의 모든 프로젝트 문장은 사실 ID를 달고 있어야 하고, 사실이 없으면 문장 대신 placeholder를 쓴다 |
| 아키텍처 그림이 실제 구축과 어긋난다 | `aws-drawio-diagram`(편집 가능한 아키텍처), `aws-diagram-design`(개념도 PNG)에 사실 목록의 구성 요소 표로 브리프를 쓰고, 나온 그림의 모든 노드와 엣지를 사실 목록과 다시 대조한다 |
| 번역투 보도자료처럼 읽힌다 | 작성자의 기존 게재글에서 뽑은 voice 규칙(`author-voice.md`), AWS 블로그 관례, 기계 문장 패턴 목록으로 쓰고 `lint_blog.py`로 검사한다 |

기술 주장은 `aws-docs` MCP로 공식 문서를 열어 URL과 함께 검증(`05-claims.md`)하고, 확인되지 않은 것은 삭제하거나 추측하지 않고 `[기술 검증 필요]` placeholder로 남깁니다.

## Placeholder

작성자만 아는 사실은 네 가지 색으로 표시됩니다. Word 파일에서 그대로 보이고, 문서 마지막에 목록으로 한 번 더 정리됩니다.

| 태그 | 색 | 무엇 |
|---|---|---|
| `[작성자 확인]` | 노랑 | 수치, 날짜, 이름, 결정, 결과, 저자 소개 |
| `[기술 검증 필요]` | 빨강 | 공식 문서에서 확인하지 못한 기술 문장 (claim ID 포함) |
| `[이미지 필요]` | 파랑 | 콘솔 화면, 데모 캡처 |
| `[인용 승인 필요]` | 초록 | 고객사명, 로고, 인용문 |

## 파이프라인

`blog-work/<slug>/` 에 단계마다 파일을 남기므로 다음 세션이나 서브에이전트가 파일만 읽고 이어서 작업할 수 있습니다.

| Phase | 산출물 |
|---|---|
| 0 워크스페이스와 인테이크 | `00-intake.md` |
| 1 자료 digest와 사실 목록 | `sources/*.digest.md`, `01-facts.md` |
| 2 갭 분석과 딥 리서치 | `02-research.md` |
| 3 글 계획 (승인 게이트) | `03-plan.md` |
| 4 다이어그램 생성과 검증 | `diagrams/`, `manifest.md` |
| 5 초안 | `04-draft.md` |
| 6 AWS 문서 기반 사실 검증 | `05-claims.md` |
| 7 스타일 패스와 린트 | `06-final.md`, `placeholders.md` |
| 8 Word 문서 빌드와 검증 | `06-final.docx` |

## Word 파일 (Phase 8)

`docx` 스킬의 docx-js 워크플로로 만듭니다. pandoc의 DOCX writer는 인라인 색을 버려 placeholder가 보이지 않으므로 쓰지 않습니다.

```bash
node skills/aws-tech-blog-writer/scripts/build_docx.js blog-work/<slug>
```

pandoc이 Markdown을 파싱하고 docx-js가 렌더링합니다. placeholder span은 같은 두 색으로 shading된 run이 되고, 그림은 본문 폭에 맞춰 `그림 N.` 캡션과 함께 들어가며, 표와 코드 블록은 구조를 유지하고, `placeholders.md`가 마지막 섹션으로 붙습니다. 스크립트 끝의 검증 블록이 Markdown과 DOCX의 이미지 수와 태그별 placeholder 수를 비교해 일치할 때만 exit 0 입니다.

## 설치

```
/plugin marketplace add hi-space/hi-aws-skills
/plugin install aws-tech-blog-writer@hi-aws-skills
```

필요한 도구: `pandoc`, `node` 와 전역 `docx` 패키지(`npm install -g docx`), Python 3. 다이어그램 단계는 같은 마켓플레이스의 `aws-drawio-diagram`, `aws-diagram-design` 플러그인을, 사실 검증은 `aws-docs` MCP 서버를 씁니다.

## 스크립트

| 스크립트 | 용도 |
|---|---|
| `scripts/init_workspace.py <slug>` | 작업 디렉터리와 템플릿 생성 |
| `scripts/ingest_sources.py <work>` | PDF / DOCX / PPTX / drawio 자료를 텍스트로 변환 |
| `scripts/lint_blog.py <draft.md> [--final] [--placeholders-out <file>]` | 문체, 서비스명, 이미지·캡션, 코드, placeholder 검사 |
| `scripts/check_claims.py <work>` | `05-claims.md` 검증과 초안 placeholder 대조 |
| `scripts/build_docx.js <work> [--out <file>] [--no-appendix]` | `06-final.docx` 빌드와 검증 |

## 테스트

```bash
pytest plugins/aws-tech-blog-writer/tests
```
