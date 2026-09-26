# Script: intro card, chapters, beats, summary card

Write the script before recording. It has four parts, and `make_cards.py` / `edit_demo.py` only render what is decided here.

## 1. Intro card (6–8 s): the message, and what the demo shows

The viewer needs two things before the first screen: **what this video says** and **what they are about to see** to back it up.

- kicker: product or series name
- title: the message, one or two lines, 합니다체 or a short claim
- 2–3 rows: what the demo shows (the features or scenarios, in the order they appear)

```json
"card-intro": {"seconds": 7, "lines": [
  ["kicker", "Agent Platform"],
  ["title", "코드 배포 없이 에이전트를 만들고 운영합니다"],
  ["gap"],
  ["row", "채팅에서 데이터로 발표 자료를 만드는 과정"],
  ["row", "모델, 툴, 지식 베이스를 골라 에이전트를 만드는 과정"],
  ["row", "비용과 사용량을 한 화면에서 보는 관리 화면", "accent"]
]}
```

## 2. Chapters and chapter cards (간지)

A chapter is one feature or one scenario. Its title says what the feature lets the user do, its subtitle says where in the UI it happens:

| Title (what the user can do) | Subtitle (where) |
|---|---|
| 데이터만 주면 발표 자료를 받습니다 | 채팅, pptx 스킬 |
| 코드 없이 에이전트를 만듭니다 | Agent Builder |

A **chapter card** (3 s) marks the change between chapters: kicker = chapter number, title = the chapter title, one row = the subtitle. Put one before each chapter that changes the screen or the scenario; a short chapter that continues on the same screen does not need one. Order chapters so the one whose result fills the screen comes first and the management or settings view comes last.

## 3. Beats (the captions)

A beat says **what the feature on screen does for the user**. The frame shows it; the sentence is not a description of the frame.

| ✗ Describes the frame | ✓ Says what the feature does |
|---|---|
| ✗ 설정 페이지가 열립니다 | ✓ 관리자는 사이드바 메뉴 노출 여부를 정합니다 |
| ✗ 표가 보입니다 | ✓ 에이전트별로 턴, 사용자, 토큰 비용을 나눠 봅니다 |

Rules for every beat, title, subtitle and card row:

- **합니다체**, one sentence, **≤ 45 characters**. Longer wraps to two lines and covers the UI; split it into two beats.
- **No em dash, middle dot or arrow** (U+2014, U+00B7, U+2192). Join with a comma or 와/과/하고.
- **Nothing that sounds generated**: no metaphors, rhetorical questions, aphorisms ("A는 B가 아니라 C다"), translationese ("~에 의해", "~하는 것이 가능합니다").
- **No speed labels and no notes about the recording** ("4배속", "이 녹화에서는 누르지 않았습니다"). Report skipped actions in the chat, not on screen.
- Anchor `at` at the second the event is visible (a click, a status text, a panel, a result). If the take did something other than planned, caption what the take shows.
- Numbers only when the number is the feature ("모델별 100만 토큰당 가격을 설정합니다"); what this take cost or how long it ran is noise.
- The last beat of a chapter can be `"style": "insight"` (blue box): the chapter's take home message in one sentence. It becomes a row on the summary card.
- `"pos": "top"` when the lower third would sit on the evidence (a bottom table, a status bar).

4–15 beats per clip at 1× is a normal density; a short sped-up piece may carry a single beat. Format and anchor forms: `python3 scripts/edit_demo.py --help`.

## 4. Summary card (8–10 s): take home messages

What the viewer should remember. One row per take home message, 3–5 rows, each a 합니다체 sentence. The chapters' insight beats are the usual source; a message that no chapter showed does not belong here.

```json
"card-summary": {"seconds": 9, "lines": [
  ["kicker", "정리"],
  ["title", "한 플랫폼에서 만들고, 쓰고, 관리합니다"],
  ["gap"],
  ["row", "데이터만 주면 발표 자료와 대시보드를 채팅에서 받습니다"],
  ["row", "코드 배포 없이 에이전트를 만들고 수정합니다"],
  ["row", "비용과 사용량, 가드레일을 한 화면에서 봅니다", "accent"]
]}
```

Card line kinds: `kicker`, `title`, `row`, `gap`; colours `fg` (default), `dim`, `accent`, `alt`, `warn` or `#rrggbb`. All cards of a reel go in one `cards.json` (`{"card-intro": …, "card-ch2": …, "card-summary": …}`).

## Working order

1. Intro card and summary card first: the message and the take home messages exist end to end before any footage.
2. Chapter list with title, subtitle and the take that will show it.
3. Storyboard and recording.
4. Beats per chapter, written from the camlog and the stills, then the check that each insight beat is a row on the summary card.
