# Kiro 사용 가이드 (IDE · CLI)

Kiro는 IDE와 CLI 모두 Anthropic 형식 Agent Skills(SKILL.md)를 네이티브로 읽는다. 이 저장소의 `skills/aws-diagram-design/`을 그대로 스킬 디렉터리에 넣으면 동작하며, 루트의 `plugin.json`(Agent Plugins 1.0.0) 덕분에 Power로도 설치할 수 있다.

## 설치

### 방법 1 — 사용자 레벨 스킬 (권장)

모든 워크스페이스에서 동작한다:

```bash
./install.sh kiro            # ~/.kiro/skills/aws-diagram-design/ 에 복사
./install.sh kiro --link     # 복사 대신 심링크 (저장소 수정이 즉시 반영, 개발용)
```

### 방법 2 — 워크스페이스 스킬

특정 프로젝트에만 쓰고 팀과 커밋으로 공유하려면:

```bash
cd <프로젝트 루트>
/path/to/hi-aws-skills/plugins/aws-diagram-design/install.sh kiro --workspace   # .kiro/skills/ 에 복사
```

같은 이름이 양쪽에 있으면 워크스페이스 스킬이 우선한다.

### 방법 3 — IDE 임포트 UI

Kiro IDE의 Agent Steering & Skills 패널 → `+` → Import a skill → Local folder에서 `skills/aws-diagram-design` 폴더를 선택한다. GitHub URL로 임포트할 때는 저장소 루트가 아니라 **스킬 서브디렉터리**(`…/tree/main/skills/aws-diagram-design`)를 가리켜야 한다. 임포트는 복사 방식이라 이후 저장소 변경을 따라가지 않는다.

### 방법 4 — Power로 설치

원클릭 설치·키워드 활성화가 필요하면 Power로 넣는다. 루트 `plugin.json`이 매니페스트다.

Powers 패널 → Add Custom Power → Import power from a folder → `/path/to/hi-aws-skills/plugins/aws-diagram-design` 선택. 설치본은 `~/.kiro/powers/installed/aws-diagram-design/`에 복사되는 것으로 알려져 있고(공식 문서에 없는 경로 — GitHub 이슈에서만 확인, 빌드에 따라 다를 수 있다), 저장소를 수정한 뒤에는 해당 Power의 Check for updates → Install updates로 갱신한다.

일반 사용이라면 방법 1이면 충분하다. Kiro 문서 기준으로 Power가 나은 경우는 MCP 서버를 함께 배포할 때다.

## 사용법

- 기본 에이전트(IDE 채팅, `kiro-cli chat`)는 스킬을 자동 발견한다. "AWS 아키텍처 다이어그램 그려줘" 같은 요청이면 description 매칭으로 활성화된다.
- 명시 호출: `/aws-diagram-design` (CLI 2.1 이상에서 스킬이 슬래시 커맨드로 노출된다).
- Claude Code용 슬래시 커맨드(`commands/`)는 Kiro가 읽지 않는다. draw.io·Mermaid 임포트와 내보내기는 자연어로 요청하면 스킬 본문의 라우팅이 처리한다. 예: "이 diagram.drawio를 슬라이드용으로 다시 그려줘", "방금 만든 HTML을 PNG로 내보내줘".

### 커스텀 에이전트 주의

커스텀 에이전트(`kiro-cli chat --agent <이름>`)는 스킬을 자동 상속하지 않는 빌드가 있다. 에이전트 설정(`.kiro/agents/<이름>.json`)에 리소스를 선언한다:

```json
{
  "resources": [
    "skill://~/.kiro/skills/**/SKILL.md",
    "skill://.kiro/skills/**/SKILL.md"
  ]
}
```

## 내보내기·검증

Kiro 에이전트는 셸 실행이 가능하므로 Claude Code와 동일하게 동작한다:

```bash
pip install playwright && playwright install chromium   # PNG/SVG 내보내기 사전 준비 (1회)
python3 <스킬 경로>/scripts/self_check.py <생성된.html>  # 산출물 자체 점검
```

`drawio_extract.py`, `mermaid_extract.py`도 스킬 폴더에 함께 설치되므로 임포트 시 에이전트가 직접 실행한다.

## 제약 요약

| 항목 | 내용 |
|------|------|
| 슬래시 커맨드 | Claude Code `commands/`는 미지원 — 스킬 슬래시(`/aws-diagram-design`) 또는 자연어로 대체 |
| GitHub 임포트 | 스킬 서브디렉터리 URL만 허용, 복사 방식이라 업데이트 추적 없음 |
| 스티어링 | 이 스킬에는 불필요 — 스티어링은 상시 로드라 레퍼런스가 매 프롬프트에 끌려 들어간다 |
| 폰트 | Amazon Ember 로컬 설치 필요 (README 폰트 절 참고) |
