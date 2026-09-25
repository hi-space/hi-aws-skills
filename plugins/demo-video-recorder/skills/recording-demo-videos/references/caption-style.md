# Caption style

Two halves: what a caption says (the script) and how it is drawn (`edit_demo.py`). The look is fixed in the script constants so every clip of a post matches; change it there, not per clip. What the captions argue, and in which order, is decided in [story.md](story.md) first; this file is about the sentence.

## Two kinds of video

Decide which one you are cutting before the first beat; the beat shape differs.

- **Argument video** (a post's thesis, an experiment, a before/after): a beat is one step of the argument. Say what happened, who decided, and what followed, with the number from this take that makes it checkable.
- **Feature tour** (the user asks for "전체 기능 데모", every tab, a product walkthrough): a beat says **what the feature does for the user**. Measured values from the take ("12턴인데 $17.63", "84초, 툴 6번") are not the point and read as noise; drop them. A number stays only when it is the feature itself ("모델별 100만 토큰당 가격을 설정합니다"). Admin and settings screens (rates, menu visibility, connectors) are features too and get their own beat, not a pan past them.

## Voice (user feedback 2026-09-25, overrides any example below)

Every beat, title, subtitle and card row follows these rules. A reel that broke them was rejected whole and re-captioned.

- **합니다체, plain description.** "모델 요율 탭에서 모델별 100만 토큰당 가격을 설정합니다". Not 한다체 headlines, not noun-phrase fragments.
- **No em dash, no middle dot, no arrow** (U+2014, U+00B7, U+2192) in any caption, title or card. Join facts with a comma or 와/과/하고: "입력, 출력, 캐시 가격을 직접 넣거나 Price List에서 가져옵니다".
- **Nothing that sounds generated.** No metaphors, no figurative headings, no rhetorical questions, no aphorisms of the form "A는 B가 아니라 C다", no translationese ("~에 의해", "~하는 것이 가능합니다", "~를 가지고 있습니다"). Adjectives the frame already shows are cut.
- **No speed labels.** A sped-up piece carries an ordinary beat; never prefix ✗ "(4배속)". The viewer does not need the edit explained.
- **No notes about the recording.** Never caption what was not done on camera (✗ "이 녹화에선 누르지 않았습니다"). Caption what the control does ("Create agent를 누르면 AgentCore에 harness가 배포됩니다") and tell the user in the chat report what was skipped and why.

## Writing a beat

A beat is not a description of the frame. The frame is where the viewer checks the sentence; the sentence says what the event means (argument video) or what the feature is for (feature tour).

| ✗ Reads the screen | ✓ Says what it is for |
|---|---|
| ✗ 설정 페이지가 열립니다 | ✓ 관리자는 Settings에서 사이드바 메뉴 노출 여부를 정합니다 |
| ✗ 표가 보입니다 | ✓ 에이전트별로 턴, 사용자, 토큰, 모델 비용을 나눠 봅니다 |
| ✗ 로봇이 물체를 다시 잡습니다 | ✓ 물체가 떨어지자 Laya가 retry_grasp를 99.0%로 선택합니다 |

- **Name the actor** when the video is about who decides (Laya, Bedrock, the agent, the code rule, the human, the admin).
- One sentence, ≤ 45 characters (Korean or English). Longer wraps to two lines and covers the evidence; split into two beats instead.
- **Evidence in the frame.** The anchor `at` is the second the event is visible (a tap, a status text, a panel, a number). If nothing in the frame changes at that second, there is no beat there. If the take did something else than planned (a row that did not expand, a tool the agent did not call), rewrite the beat to what the frame shows.
- Numbers, when used, come from **this take's** logs or UI, not from the post or an earlier run.
- 4–15 beats per clip; a short sped-up piece may carry a single beat. Fewer than 4 in a 1× clip of 30 s means silence; more than 15 means captions over the action.
- The chapter's last beat is the **insight** (`"style": "insight"`): the chapter's point in one 합니다체 sentence ("코드 배포 없이 에이전트를 만들고 수정합니다"). 1–2 per chapter; it later becomes a row on the summary card.
- `"pos": "top"` when the lower third would sit on the evidence (a bottom table, a status bar).
- **Title = the chapter's point**, subtitle = the setting, both under the voice rules: `"title": "04 코드 없이 에이전트를 만듭니다"`, `"subtitle": "Agent Harness, 모델, MCP, 스킬, Knowledge Base, 내장 툴"`. Not the scene name, not the page name. When a chapter is cut into several pieces, only the first piece has a title.

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
