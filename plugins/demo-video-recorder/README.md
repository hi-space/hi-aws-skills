# demo-video-recorder

웹 UI 데모 영상을 스토리 대본 → 녹화 → 자막 → 하이라이트 릴 순서로 만드는 스킬입니다. 링크드인 게시용 시연 영상을 만들면서 정리한 절차와 스크립트를 한 플러그인으로 묶었습니다. AWS 전용은 아니며 GUI 없는 리눅스 서버에서 Playwright와 ffmpeg만으로 돕니다.

## 무엇을 만드나

| 단계 | 도구 | 산출물 |
|---|---|---|
| 스토리 | `references/story.md` 순서로 직접 작성 | 메시지 한 문장 → 챕터(제목 = 그 챕터가 주는 답, 부제 = 상황) → `cards.json` → 챕터별 4–15개 비트(`scripts/<stem>.json`). 비트는 화면 묘사가 아니라 논지의 한 단계(사건, 판단 주체, 결과와 숫자)이거나, 기능 투어라면 그 기능이 하는 일. 자막은 합니다체이고 em dash, 가운뎃점, 화살표, 배속 표기, 촬영 사정 설명을 쓰지 않음 |
| 녹화 | `node scripts/record_demo.mjs --url … --storyboard storyboard.mjs` | `raw/<stem>.webm` + `raw/<stem>.camlog.json` (모든 카메라 이동과 이벤트의 시각) |
| 클립 | `python3 scripts/edit_demo.py clip raw/<stem>.webm --script scripts/<stem>.json` | `clips/<stem>.mp4` 1080p30, 타이틀 카드 + 자막, 대기 구간은 `speed` |
| 표지 | `python3 scripts/make_cards.py cards.json --out clips` | `clips/card-intro.mp4`(메시지·맥락), `clips/card-summary.mp4`(챕터별 답과 숫자), 선택적 챕터 카드. PNG 미리보기 포함 |
| 릴 | `python3 scripts/edit_demo.py reel reel.json --out reel.mp4` | 인트로 카드 → 논지 순서의 챕터 → 정리 카드 |

카메라는 브라우저 안에서 `body`에 CSS `transform`을 걸어 움직입니다. 녹화된 영상을 나중에 잘라 확대하면 흐려지지만, 페이지 안에서 확대하면 글자가 그 크기로 다시 그려져 2배까지 선명합니다.

직접 찍은 화면 녹화(.mov)도 같은 `clip`/`reel` 명령으로 자막을 넣습니다. 이때 비트의 `at`은 원본의 초 단위 시각입니다.

## 요구 사항

```bash
sudo apt install ffmpeg fonts-nanum        # 한국어 자막 글꼴
pip install pillow                         # 표지 카드 렌더링
mkdir pw && cd pw && npm i playwright && npx playwright install chromium   # 앱 저장소에 playwright가 없을 때
```

`--playwright-root <dir>`는 `node_modules/playwright`가 있는 아무 디렉터리면 됩니다.

## 설치

```
/plugin marketplace add hi-space/hi-aws-skills
/plugin install demo-video-recorder@hi-aws-skills
```

스킬만 쓸 때:

```bash
ln -s "$PWD/hi-aws-skills/plugins/demo-video-recorder/skills/recording-demo-videos" ~/.claude/skills/recording-demo-videos
```

## 문서

- [SKILL.md](skills/recording-demo-videos/SKILL.md) — 9단계 파이프라인, 빠른 참조, 흔한 실수
- [references/story.md](skills/recording-demo-videos/references/story.md) — 메시지 → 챕터 → 비트 → 카드. 챕터 순서·중복 제거·길이 예산 규칙, `cards.json` 형식
- [references/caption-style.md](skills/recording-demo-videos/references/caption-style.md) — 자막 한 문장의 규칙(논지 영상과 기능 투어의 차이, 합니다체, 금지 기호와 배속 표기, 45자, 비유와 번역체 없음)과 글꼴·위치·색·타이밍 상수
- [references/reel-manifest.md](skills/recording-demo-videos/references/reel-manifest.md) — 릴 매니페스트 형식, 구간별 `fade_in`/`fade_out`
- `scripts/storyboard.example.mjs` — 스토리보드 예시(고정 대기 + 이벤트 감지 루프)

## 테스트

```bash
cd plugins/demo-video-recorder && python3 -m pytest tests -q
```

ffmpeg가 있어야 합니다. 앵커 계산, `speed`, 구간별 페이드, 해상도 검사, 임시 파일 정리, SKILL.md 형식을 확인합니다.
