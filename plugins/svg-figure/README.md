# svg-figure

설명용 그림을 SVG로 직접 그려 `.svg`와 `.png` 파일로 내는 스킬입니다. TransMeet 회의록 페이지의 그림 스타일을 따로 떼어 정리했습니다. AWS 전용은 아닙니다.

## 스타일

- **색은 토큰으로만 씁니다.** 원본에는 `fill="var(--ok)"`처럼 적고 16진 색을 쓰지 않습니다. 같은 그림이 라이트와 다크에서 그대로 읽힙니다.
- **색은 상태를 뜻합니다.** 확정(`--ok`), 신규(`--new`), 미확인·위험(`--risk` + 점선), 조건부 제안(`--muted` 점선), 기존(`--line`).
- **글자 크기 하한이 있습니다.** 본문 옆 그림(560 폭)은 17, 전체 폭 그림(1120)은 15, 휴대폰 판(400)은 14입니다. 라벨이 안 들어가면 라벨을 줄이거나 높이를 늘립니다.
- **박스 나열로 끝내지 않습니다.** 위치·크기·선·색이 각각 뜻을 갖게 하고, 실물이 주제면 실물을 그립니다(부품 위치, 감지 범위, 절개, 분해, 동작, 장면 순서).
- **그림 안에 범례를 넣지 않습니다.** 접근성용 `<title>`과 `<desc>`를 채웁니다.

## 산출물

| 파일 | 역할 |
|---|---|
| `<이름>.src.svg` | 원본. 수정은 여기에 합니다 |
| `<이름>.svg` | 납품용. 토큰을 실제 색으로 채운 파일 |
| `<이름>.png` | 납품용 2배 해상도 이미지 |

HTML 페이지에 넣을 때는 원본 SVG를 그대로 붙이고 `assets/figure-tokens.css`를 한 번 포함합니다.

## 도구

```bash
S=skills/svg-figure/scripts/svg_figure.py
python3 $S check   fig.src.svg --prefix fig-                    # 계약 위반(오류)과 겹침·넘침 추정(경고)
python3 $S preview fig.src.svg -o preview.html --png preview.png  # 라이트, 다크, 휴대폰 폭을 한 장에
python3 $S export  fig.src.svg -o fig.svg --png fig.png         # 납품용 파일
python3 $S export  fig.src.svg -o fig.dark.svg --theme dark --bg paper
```

`check`와 `export`는 표준 라이브러리만 씁니다. `--png`는 Playwright가 필요합니다(`pip install playwright && playwright install chromium`). 자체 팔레트를 쓰려면 `assets/figure-tokens.css`를 복사해 값만 바꾸고 `--tokens <파일>`로 넘깁니다.

## 설치

```
/plugin marketplace add hi-space/hi-aws-skills
/plugin install svg-figure@hi-aws-skills
```

스킬만 쓸 때:

```bash
ln -s "$PWD/hi-aws-skills/plugins/svg-figure/skills/svg-figure" ~/.claude/skills/svg-figure
```

## 문서

- [SKILL.md](skills/svg-figure/SKILL.md): 작업 순서, 그림 계약(캔버스, 토큰, 상태, 라벨과 선), 구성 선택, 납품 방식, 흔한 실수
- [references/technical-illustration.md](skills/svg-figure/references/technical-illustration.md): 물체와 동작 도해 6종
- [assets/example.src.svg](skills/svg-figure/assets/example.src.svg): 원본 예시
- [assets/figure-tokens.css](skills/svg-figure/assets/figure-tokens.css): 라이트·다크 토큰, 페이지용 figure와 범례 스타일

## 다른 스킬과의 구분

공식 AWS 아이콘이 들어간 아키텍처 다이어그램은 `aws-diagram-design`, draw.io에서 편집할 파일은 `aws-drawio-diagram`을 씁니다. `svg-figure`는 아이콘 없이 도형과 라벨로 개념·구조·실물을 설명하는 그림에 씁니다.

## 테스트

```bash
cd plugins/svg-figure && python3 -m pytest tests -q
```
