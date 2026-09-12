# Claude Code 사용 가이드

## 설치

### 방법 1 — 플러그인 (권장)

스킬과 슬래시 커맨드 3종이 함께 설치된다. Claude Code 세션에서:

```
/plugin marketplace add hi-space/hi-aws-skills
/plugin install aws-diagram-design@hi-aws-skills
```

설치 후 안내에 따라 `/reload-plugins`를 실행하거나 세션을 재시작한다. 로컬 클론을 쓰려면 `/plugin marketplace add /path/to/hi-aws-skills` 로 저장소 루트를 등록한다.

### 방법 2 — 스킬 단독

슬래시 커맨드 없이 스킬만 쓰려면 심링크 하나로 충분하다:

```bash
ln -s /path/to/hi-aws-skills/plugins/aws-diagram-design/skills/aws-diagram-design ~/.claude/skills/aws-diagram-design
```

심링크라 저장소를 수정하면 즉시 반영된다. 개발 중에는 이 방식이 편하다.

## 기존 diagram-design 플러그인 정리

이 플러그인은 "marketplace판 diagram-design + AWS 스킨 오버레이" 구성을 대체한다. 둘을 같이 켜두면 트리거 조건이 겹치는 스킬 두 개가 경쟁하므로 다음을 정리한다.

1. 기존 플러그인 제거: `/plugin` → diagram-design → uninstall. disable만 하면 캐시 트리(`~/.claude/plugins/cache/diagram-design/`)가 남아 SessionStart 훅이 계속 그 트리를 대상으로 삼는다 — 지금은 스킨 마커(`.aws-skin-applied`)가 있어 조용할 뿐, 오버레이의 `SKIN_VERSION`을 올리면 비활성화된 플러그인을 다시 패치한다.
2. SessionStart 훅 정리: `~/.claude/settings.json`의 `apply_aws_skin.py` 훅은 실패하지 않지만(항상 exit 0) 플러그인 uninstall 뒤에는 세션마다 `[aws-diagram-skin] diagram-design plugin not found; nothing to do.` 한 줄을 출력한다. 훅 항목을 제거하면 이 출력도 사라진다. `~/.claude/aws-diagram-skin/` 디렉터리는 업스트림 신규 버전에 AWS 스킨을 재적용할 때 다시 쓸 수 있으므로 남겨두는 편이 낫다.

## 사용법

### 자동 트리거

"AWS 아키텍처 다이어그램 그려줘", "구성도 만들어줘", "이 흐름을 플로차트로" 같은 요청이면 스킬이 자동으로 걸린다. 영어·한글 트리거 모두 SKILL.md description에 들어 있다.

```
빗썸 시세 수집 파이프라인 아키텍처 다이어그램 그려줘.
API Gateway → Lambda → Kinesis → S3, 모니터링은 CloudWatch.
```

AWS 서비스를 지명하면 공식 아이콘이 자동으로 들어가고, VPC·서브넷·계정 경계는 공식 그룹 컨벤션(테두리 색 + 좌상단 배지)으로 그려진다.

### 슬래시 커맨드

| 커맨드 | 역할 |
|--------|------|
| `/aws-diagram-design:export-diagram <html> [--svg-only\|--png-only] [--scale=N] [--output=<path>]` | 생성된 HTML을 .svg/.png로 내보내기 |
| `/aws-diagram-design:import-drawio <file.drawio>` | draw.io 원본을 에디토리얼 스타일로 다시 그리기 |
| `/aws-diagram-design:import-mermaid <file.mmd>` | Mermaid 원본을 다시 그리기 |

임포트 커맨드 둘은 `--format=html|svg|png|html+png`, `--size=<프리셋>`, `--detail=faithful|balanced|simplified`, `--audience=engineer|mixed|executive`, `--variant=light|dark|full`, `--output=<경로>`, 페이지 선택(`--page`/`--diagram`)까지 받는다. 전체 시그니처의 기준은 각 `commands/*.md`의 argument-hint다.

### PNG/SVG 내보내기 사전 준비

내보내기는 headless Chromium을 쓴다. 한 번만 설치하면 된다:

```bash
pip install playwright && playwright install chromium
```

## 문서용 다이어그램 일괄 생성 (Python)

여러 장을 한 스타일로, 한국어·영어 판을 같은 레이아웃으로 뽑을 때는 `skills/aws-diagram-design/scripts/pygen/` 을 쓴다. "docs/diagrams 의 mermaid 를 이 스타일 PNG 로 바꿔줘", "모듈별 구성도를 ko/en 으로 만들어줘" 같은 요청에서 스킬이 §13 을 따라 이 경로를 택한다.

```bash
python3 <skill-dir>/scripts/pygen/build.py docs/diagrams --out docs/diagrams/out
python3 <skill-dir>/scripts/pygen/export.py docs/diagrams/out --png-dir static/images/diagrams
```

## 산출물 검증

저장소를 체크아웃한 상태라면 생성된 다이어그램을 스크립트로 검증할 수 있다:

```bash
python3 skills/aws-diagram-design/scripts/self_check.py <생성된.html>   # 접근성·단일 파일 계약
python3 scripts/verify-geometry.py <생성된.html>                        # 라벨 마스크-노드 겹침
python3 scripts/verify-motion.py <생성된.html>                          # 모션 사용 시
```

설치된 스킬로 쓸 때도 `self_check.py`는 스킬 디렉터리에 함께 배포되므로 그대로 실행된다.

## 폰트

Amazon Ember가 로컬에 설치돼 있어야 지정 서체로 렌더링된다. 브라우저·스크린샷 결과가 Helvetica로 보이면 폰트 미설치 상태다. 설치 여부 확인은 README의 폰트 절 참고.
