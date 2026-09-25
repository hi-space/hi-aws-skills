# Caption style

Two halves: what a caption says (the script) and how it is drawn (`edit_demo.py`). The look is fixed in the script constants so every clip of a post matches; change it there, not per clip. What the captions argue, and in which order, is decided in [story.md](story.md) first; this file is about the sentence.

## Writing a beat

A beat is one step of the chapter's argument, not a description of the frame. The frame is where the viewer checks the sentence; the sentence says what the event means for the video's message.

- **Shape: event → decision → consequence, with the number.** "파지 직후 물체 낙하 → Laya가 retry_grasp 99.0% 선택", "사람 0.08 m · 기준 0.25 m 미만 → 모델과 무관하게 코드가 정지". Use `→` for the causal step and `·` to join two facts; both read at a glance.
- **Name the actor that decided** (Laya, Bedrock, the agent, the code rule, the human), because the message is about who decides when. "로봇이 다시 잡습니다" says nothing; "Laya가 retry_grasp 99.0% 선택" does.
- One sentence, ≤ 45 characters (Korean or English). Longer wraps to two lines and covers the evidence; split into two beats instead.
- Plain statements. No metaphors, no figurative headings, no rhetorical questions, no adjectives that the number already says.
- **Evidence in the frame, meaning in the sentence.** The anchor `at` is the second the event is visible (a tap, a status text, a panel, a number). If nothing in the frame changes at that second, there is no beat there; if the sentence cannot be checked against the frame or the log, drop the sentence.
- Numbers come from **this take's** logs or UI, not from the post or an earlier run. A batch statistic or a caveat with no event of its own goes on a late summary shot (results table, wide shot) or on the summary card, never mid-action.
- 4–15 beats per clip; a short piece at 4× speed may carry a single beat (`"(4배속) Agent가 턴마다 Gateway 도구로 상태 조회·스킬 실행"`). Fewer than 4 in a 1× clip of 30 s means silence; more than 15 means captions over the action.
- The chapter's last beat is the **insight** (`"style": "insight"`): the chapter's answer to the message, in one sentence a viewer would repeat ("Laya 판단만으로 복구·완료 · Bedrock 호출 0회"). 1–2 per chapter; it is the sentence that later becomes a row on the summary card.
- `"pos": "top"` when the lower third would sit on the evidence (a bottom table, a status bar).
- **Title = the chapter's answer**, subtitle = the setting: `"title": "코드로 처리할 판단 · 사람 접근"`, `"subtitle": "Live · 작업 중 사람 손이 로봇에 다가옵니다"`. Not the scene name, not the page name. When a chapter is cut into several pieces, only the first piece has a title.
- Speed pieces announce themselves: prefix `(4배속)` so the viewer does not read the speed as the system's.

## How it is drawn (constants in `edit_demo.py`)

| Element | Font | Size | Position | Box | Timing |
|---|---|---|---|---|---|
| Title | bold (`DEMO_FONT_BOLD`, default NanumSquareB) | 58 | x 96, y h-260 | `0x0b0f14@0.72`, border 18 | 0.2–4.2 s |
| Subtitle | regular | 30 | x 96, y h-170 | same | 0.5–4.2 s |
| Beat (lower third) | regular | 32 | x 96, y h-150 (or y 120 with `pos: top`) | same dark box | from its anchor, until the next beat, max 7 s, min 1.5 s |
| Insight beat | bold | 34 | same as beat | `0x1f6feb@0.82` (blue) | same |
| Tag (`--tag`, off by default) | mono | 22 | top-right, `w-tw-40`, `h-58` | none, `0xcfd8dc` text | whole clip |

- Every caption fades in and out over 0.35 s inside its window; beats never start under the title card (earliest 4.4 s when a title exists).
- One caption on screen at a time. Beat windows are computed from the gap to the next beat minus 0.3 s, so two beats closer than 1.3 s make the first one too short and it is skipped with a `skip beat (no room)` message; space them out or drop one.
- Output: 1920×1080, 30 fps, H.264 high 4.1, CRF 19, `-preset slow`, silent stereo AAC 96 k so every player and LinkedIn accept the file; `+faststart`.
- Fonts resolve in this order: `DEMO_FONT_BOLD` / `DEMO_FONT_REGULAR` / `DEMO_FONT_MONO` env, then `/usr/share/fonts/truetype/nanum/NanumSquare{B,R}.ttf` and `NanumGothicCoding.ttf`, then `fc-match sans:bold` / `sans` / `monospace`. Korean text needs a CJK font; check `fc-match -f '%{file}' sans` before the first clip on a new machine.
- Changing the look for one post: edit the constants at the top of `edit_demo.py` (font sizes are literal in `_encode_clip`), re-run every clip so the set matches. No per-beat size or colour fields on purpose.
