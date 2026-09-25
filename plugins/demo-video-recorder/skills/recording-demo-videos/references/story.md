# Story: message → chapters → beats → cards

The video argues one thing. Everything on screen — chapter order, which take is kept, every caption, both cards — is a step in that argument. The frame is the evidence for a step; the caption is the step. Write this file's four layers **before** recording or cutting; `edit_demo.py` and `make_cards.py` only render what is decided here.

## 1. Message (one sentence)

What the viewer should be able to say after watching: "System One models belong in four places in a robot stack, and each place has a different hand-off rule." If the video accompanies a post, the message is the post's thesis, in the post's words. One message per video; a second message is a second video.

Write it at the top of `story.md` (or `PLAN.md`) in the work folder, with the source of every number the video will show (log file, results table, dashboard).

## 2. Chapters (3–6)

A chapter is one **answer** the message needs, not one recording. Its title is the answer, its subtitle is the setting that produces the evidence:

| Chapter title (the answer) | Subtitle (the setting) | Evidence take |
|---|---|---|
| 스텝마다 판단하는 게이트 · Laya | Live · 작업 중 물체가 떨어지는 시나리오 | live.mov 57–70 s |
| Laya가 넘기는 판단 · 물체 이동 | Live · 작업 중 물체가 다른 위치로 옮겨집니다 | live.mov 23.6–44.5 s |
| 코드로 처리할 판단 · 사람 접근 | Live · 작업 중 사람 손이 로봇에 다가옵니다 | live.mov 104.8–115.8 s |

Rules that came out of re-cutting the same material three times:

- **Order by the argument, not by the recording.** Start with the chapter whose evidence is the most visible surprise (the drop and the recovery), then the hand-off, then the code rule, then comparisons and results. The "normal run" chapter is a contrast, not an opener; if the message does not need the contrast, cut it.
- **One take per answer.** Two takes that show the same answer are a duplicate; keep the one with the clearer event and drop the other even if it was expensive to record.
- **A chapter may span several clips** (pieces at different `speed`); only the first piece carries the title/subtitle, the pieces join with `fade 0` (see [reel-manifest.md](reel-manifest.md)).
- **Length budget before beats.** Short reel 2–3 min, full reel 4–6 min; give each chapter a target (20–45 s) and let the budget decide how much of a take to keep and where `speed` is needed.
- **The last chapter is the result or the comparison**, and the video ends on the summary card, never on a wait.

## 3. Beats (per chapter, 4–15)

Each beat is one step of the chapter's argument, in the order the viewer needs it: **what happened → who decided → what followed**, with the number that makes it checkable. The frame at that second must show the event; the sentence says what it means for the message. Compare:

| Reads the screen | Advances the argument |
|---|---|
| 로봇이 물체를 다시 잡습니다 | 파지 직후 물체 낙하 → Laya가 retry_grasp 99.0% 선택 |
| System 2 패널이 열립니다 | Laya가 막힌 순간 → 복구 판단을 AgentCore의 Bedrock으로 |
| 오른쪽 컬럼이 느립니다 | 오른쪽: 스텝마다 Bedrock 판단 약 5초 대기 |

The last beat of a chapter is the **insight**: the chapter's answer to the message in one sentence ("Laya 판단만으로 복구·완료 · Bedrock 호출 0회", "사람 0.08 m · 기준 0.25 m 미만 → 모델과 무관하게 코드가 정지"). One or two per chapter, styled `insight`. If a chapter has no sentence like that, the chapter does not belong in this video.

Every number on a beat is from **this take's** log or UI. If the take did something else than the post says (a plan that failed instead of being reused), the beat says what the take shows and the general claim stays in the post.

Sentence-level rules (length, wording, evidence): [caption-style.md](caption-style.md).

## 4. Cards (`python3 scripts/make_cards.py cards.json --out clips`)

Two cards frame the reel; chapter cards are optional and used when a chapter changes the setting (a different page, a different dataset).

- **Intro card** (8 s): kicker = the series or experiment name; title = the message as a question or claim, two lines max; 3–4 rows = the context a first-time viewer needs (what the layers are, what is not measured elsewhere, what the model does) with the last row in `accent` carrying the number that justifies the video.
- **Summary card** (10–12 s): kicker "정리"; a title per half of the message ("어디에 쓰는가: 네 위치" / "어떻게 쓰는가: 세 원칙"); one row per chapter answer **with its number**, coloured by the layer that acted (`accent` = the model, `alt` = the agent, `warn` = code/human). The rows are the insight beats of the chapters, rewritten as noun phrases.
- **Chapter card** (3–4 s, optional): kicker = chapter number, title = the chapter's answer, one row = the setting.

Every sentence on a card is copied from the post or from an insight beat. Cards state the argument; they do not introduce evidence the reel does not show.

Spec shape (one file per reel, `cards.json` beside `reel.json`):

```json
{"card-intro": {"seconds": 8, "lines": [
  ["kicker", "Physical AI · Laya fine-tune 실험", "accent"],
  ["title", "System One 모델을 로봇 제어의"],
  ["title", "어디에, 어떻게 쓸 것인가"],
  ["gap"],
  ["row", "System 2 (추론) / System 1 (동작) 분리 — GR00T N1 · Helix · Hi Robot", "dim"],
  ["row", "Laya: 오픈 가중치 → 로봇 state로 fine-tune, 다음 스킬 정확도 15% → 96%", "accent"]
 ]},
 "card-summary": {"seconds": 11, "lines": [
  ["kicker", "정리", "accent"],
  ["title", "어디에 쓰는가: 네 위치"],
  ["row", "스텝마다 판단하는 게이트 — Laya 0.54 s vs Amazon Bedrock 5.23 s (S1 p50)", "accent"],
  ["row", "코드로 처리할 판단 — 안전 정지 · 반복 횟수 · 전제조건", "warn"],
  ["row", "LLM Agent에 넘길 판단 — 복구 전략 (미끄러운 물체 0/8 vs 8/8)", "alt"]
 ]}}
```

## Working order

1. Message and number sources → 2. chapter table with takes and time windows → 3. cards.json (the argument, end to end) → 4. beats per chapter → 5. record or normalize → 6. clip, cards, reel → 7. check each insight beat against its frame. Writing the summary card third, before the beats, is deliberate: if a chapter has no row on the summary card, it has no reason to be in the reel.
