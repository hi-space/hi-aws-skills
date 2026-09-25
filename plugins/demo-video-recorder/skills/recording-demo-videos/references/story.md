# Story: message → chapters → beats → cards

The video argues one thing. Everything on screen (chapter order, which take is kept, every caption, both cards) is a step in that argument. The frame is the evidence for a step; the caption is the step. Write this file's four layers **before** recording or cutting; `edit_demo.py` and `make_cards.py` only render what is decided here.

## 1. Message (one sentence)

What the viewer should be able to say after watching: "System One models belong in four places in a robot stack, and each place has a different hand-off rule." If the video accompanies a post, the message is the post's thesis, in the post's words. One message per video; a second message is a second video.

Write it at the top of `story.md` (or `PLAN.md`) in the work folder, with the source of every number the video will show (log file, results table, dashboard).

## 2. Chapters (3–6)

A chapter is one **answer** the message needs, not one recording. Its title is the answer, its subtitle is the setting that produces the evidence:

| Chapter title (the answer) | Subtitle (the setting) | Evidence take |
|---|---|---|
| 스텝마다 Laya가 판단합니다 | Live, 작업 중 물체가 떨어지는 시나리오 | live.mov 57–70 s |
| 물체가 옮겨지면 Laya가 판단을 넘깁니다 | Live, 작업 중 물체가 다른 위치로 옮겨집니다 | live.mov 23.6–44.5 s |
| 사람이 다가오면 코드가 멈춥니다 | Live, 작업 중 사람 손이 로봇에 다가옵니다 | live.mov 104.8–115.8 s |

A feature tour uses the same table; the title is what the feature group lets the user do:

| Chapter title | Subtitle | Evidence take |
|---|---|---|
| 01 데이터로 발표 자료와 대시보드를 만듭니다 | content_creator harness, pptx 스킬과 html 스킬 | ch1.webm |
| 04 코드 없이 에이전트를 만듭니다 | Agent Harness, 모델, MCP, 스킬, Knowledge Base, 내장 툴 | ch6.webm |
| 06 비용, 사용량, 가드레일을 한 화면에서 봅니다 | Insights, Settings, Knowledge | ch7.webm |

Rules that came out of re-cutting the same material three times:

- **Order by the argument, not by the recording.** Start with the chapter whose evidence is the most visible surprise (the drop and the recovery), then the hand-off, then the code rule, then comparisons and results. The "normal run" chapter is a contrast, not an opener; if the message does not need the contrast, cut it.
- **One take per answer.** Two takes that show the same answer are a duplicate; keep the one with the clearer event and drop the other even if it was expensive to record.
- **A chapter may span several clips** (pieces at different `speed`); only the first piece carries the title/subtitle, the pieces join with `fade 0` (see [reel-manifest.md](reel-manifest.md)).
- **Length budget before beats.** Short reel 2–3 min, full reel 4–6 min; give each chapter a target (20–45 s) and let the budget decide how much of a take to keep and where `speed` is needed.
- **Feature tour order:** open with the chapter whose output fills the screen (a generated deck, a dashboard, an interactive app), then discovery and building (catalog, agent builder), then safety and per-conversation settings, and end on the admin view (usage, cost, settings). Every tab the user named gets a shot and a beat, including settings tabs; a tab shown without a caption reads as skipped.
- **The last chapter is the result or the comparison**, and the video ends on the summary card, never on a wait.

## 3. Beats (per chapter, 4–15)

In an argument video each beat is one step of the chapter's argument, in the order the viewer needs it: what happened, who decided, what followed, with the number that makes it checkable. In a feature tour each beat says what the feature on screen does for the user. Either way the frame at that second must show the event, and the sentence is not a description of it:

| ✗ Reads the screen | ✓ Advances the story |
|---|---|
| ✗ 로봇이 물체를 다시 잡습니다 | ✓ 물체가 떨어지자 Laya가 retry_grasp를 99.0%로 선택합니다 |
| ✗ System 2 패널이 열립니다 | ✓ Laya가 막히면 복구 판단을 AgentCore의 Bedrock에 넘깁니다 |
| ✗ 모델 요율 표가 보입니다 | ✓ 모델 요율 탭에서 모델별 100만 토큰당 가격을 설정합니다 |

The last beat of a chapter is the **insight**: the chapter's point in one 합니다체 sentence ("Laya 판단만으로 복구하고 Bedrock은 한 번도 부르지 않습니다", "코드 배포 없이 에이전트를 만들고 수정합니다"). One or two per chapter, styled `insight`. If a chapter has no sentence like that, the chapter does not belong in this video.

Every number on a beat is from **this take's** log or UI. If the take did something else than the post says (a plan that failed instead of being reused), the beat says what the take shows and the general claim stays in the post. A feature tour does not list measured values at all unless the number is the feature.

Sentence-level rules (length, wording, evidence): [caption-style.md](caption-style.md).

## 4. Cards (`python3 scripts/make_cards.py cards.json --out clips`)

Two cards frame the reel; chapter cards are optional and used when a chapter changes the setting (a different page, a different dataset).

- **Intro card** (8 s): kicker = the series or experiment name; title = the message as a question or claim, two lines max; 3–4 rows = the context a first-time viewer needs (what the layers are, what is not measured elsewhere, what the model does) with the last row in `accent` carrying the number that justifies the video.
- **Summary card** (10–12 s): kicker "정리"; a title per half of the message ("어디에 쓰는가: 네 위치" / "어떻게 쓰는가: 세 원칙"); one row per chapter answer (with its number in an argument video, the feature in a tour), coloured by the layer that acted (`accent` = the model, `alt` = the agent, `warn` = code/human). The rows are the insight beats of the chapters, kept as 합니다체 sentences.
- **Chapter card** (3–4 s, optional): kicker = chapter number, title = the chapter's answer, one row = the setting.

Every sentence on a card is copied from the post or from an insight beat. Cards state the argument; they do not introduce evidence the reel does not show.

Spec shape (one file per reel, `cards.json` beside `reel.json`):

```json
{"card-intro": {"seconds": 8, "lines": [
  ["kicker", "AgentCore Agent Platform"],
  ["title", "에이전트를 찾고, 만들고, 쓰고, 관리합니다"],
  ["gap"],
  ["row", "Registry에서 에이전트, 스킬, MCP 서버를 찾아 바로 실행해 봅니다", "fg"],
  ["row", "채팅 안에서 발표 자료, 대시보드, 앱을 결과로 받습니다", "accent"],
  ["row", "비용과 사용량, 가드레일을 한 화면에서 확인합니다", "alt"]
 ]},
 "card-summary": {"seconds": 12, "lines": [
  ["kicker", "정리"],
  ["title", "한 플랫폼에서 할 수 있는 일"],
  ["gap"],
  ["row", "01  데이터만 주면 발표 자료와 대시보드를 채팅 안에서 받습니다", "accent"],
  ["row", "04  코드 배포 없이 에이전트를 만들고 수정합니다", "fg"],
  ["row", "05  공격은 가드레일이 막고, 모델과 프롬프트는 대화마다 바꿉니다", "warn"]
 ]}}
```

Card rows follow the voice rules in [caption-style.md](caption-style.md): 합니다체, no em dash, middle dot or arrow.

## Working order

1. Message, video kind (argument or feature tour) and number sources. 2. Chapter table with takes and time windows. 3. cards.json, the story end to end. 4. Beats per chapter. 5. Record or normalize. 6. Clip, cards, reel. 7. Check each insight beat against its frame and grep every script and cards.json for the banned symbols. Writing the summary card third, before the beats, is deliberate: if a chapter has no row on the summary card, it has no reason to be in the reel.
