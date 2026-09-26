# demo-video-recorder

웹 UI 데모 영상을 대본, 녹화, 자막, 하이라이트 릴 순서로 만드는 스킬입니다. 링크드인 게시용 시연 영상을 만들면서 정리한 절차와 스크립트를 한 플러그인으로 묶었습니다. AWS 전용은 아니며 GUI 없는 리눅스 서버에서 Playwright와 ffmpeg만으로 돕니다.

## 무엇을 만드나

| 단계 | 도구 | 산출물 |
|---|---|---|
| 대본 | `references/script.md` 순서로 직접 작성 | 인트로 카드(전달하는 메시지와 무엇을 보여주는 데모인지), 챕터와 간지 카드, 챕터별 자막(그 기능이 사용자에게 무엇을 해 주는지, 합니다체 45자 이내), 정리 카드(take home messages) |
| 녹화 | `node scripts/record_demo.mjs --url … --storyboard storyboard.mjs` | `raw/<stem>.webm` + `raw/<stem>.camlog.json`. 기본 1920x1080, 한 화면에 다 들어오는 UI는 `--layout 1280x720`으로 1.5배 확대 녹화 |
| 클립 | `python3 scripts/edit_demo.py clip raw/<stem>.webm --script scripts/<stem>.json` | `clips/<stem>.mp4` 1080p30, 타이틀 카드와 자막, 기본 1.25배속, 대기 구간은 `speed: 4` |
| 카드 | `python3 scripts/make_cards.py cards.json --out clips` | 인트로, 간지, 정리 카드 mp4와 PNG 미리보기 |
| 릴 | `python3 scripts/edit_demo.py reel reel.json --out reel.mp4` | 인트로 카드, 챕터, 정리 카드 순서의 한 영상 |

카메라는 브라우저 안에서 `body`에 CSS `transform`을 걸어 움직입니다. 녹화된 영상을 나중에 잘라 확대하면 흐려지지만, 페이지 안에서 확대하면 글자가 그 크기로 다시 그려져 2배까지 선명합니다. `--layout 1280x720`도 같은 이유로 `html { zoom }`을 씁니다.

직접 찍은 화면 녹화(.mov)도 같은 `clip`/`reel` 명령으로 자막을 넣습니다. 이때 자막의 `at`은 원본의 초 단위 시각입니다.

## 요구 사항

```bash
sudo apt install ffmpeg fonts-nanum        # 한국어 자막 글꼴
pip install pillow                         # 카드 렌더링
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

- [SKILL.md](skills/recording-demo-videos/SKILL.md): 9단계 파이프라인, 빠른 참조, 흔한 실수
- [references/script.md](skills/recording-demo-videos/references/script.md): 인트로 카드, 챕터와 간지, 자막 문장 규칙, 정리 카드, `cards.json` 형식
- [references/reel-manifest.md](skills/recording-demo-videos/references/reel-manifest.md): 릴 매니페스트 형식, 구간별 `fade_in`/`fade_out`
- `scripts/storyboard.example.mjs`: 스토리보드 예시(고정 대기와 이벤트 감지 루프)

## 테스트

```bash
cd plugins/demo-video-recorder && python3 -m pytest tests -q
PLAYWRIGHT_ROOT=<node_modules/playwright가 있는 디렉터리> python3 -m pytest tests -q   # --layout 녹화 스모크 테스트 포함
```

ffmpeg가 있어야 합니다. 앵커 계산, 기본 배속, 구간별 페이드, 해상도 검사, 임시 파일 정리, 문서 규칙을 확인합니다.
