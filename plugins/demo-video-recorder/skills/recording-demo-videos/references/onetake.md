# One-take mode: a working demo as one uninterrupted session

Use it when the video must prove the product works end to end: a customer proposal, a "working demo" of a deployed agent or app, a walkthrough where a cut would look like something was hidden. The viewer sees one continuous session from the storefront to logout; nothing is cut out, waits only play faster. Chapter mode (the rest of SKILL.md) is for feature tours and LinkedIn reels, where cuts and fades are fine.

| | Chapter mode | One-take mode |
|---|---|---|
| Footage | several takes or windows, joined with fades | one take, contiguous speed-ramped segments, hard joins that are invisible |
| Waits | own clip at `speed: 4`, cut down | kept in full at ×4 with an on-screen badge |
| Captions | one 합니다체 sentence | chip, purpose, how it works (below) |
| Cards | intro, chapter cards, summary | only before and after the take; no chapter cards inside |
| Camera | pan + zoom on panels | `--camera zoom`: whole page at 100 %, ≤1.12 while typing and reading |

## 1. Storyline: one customer, every feature

1. **Inventory what is actually built** before writing a word: product specs, the UI components (entry points, buttons, panels), the agent's tool list, and the *deployed* configuration (model, which tools are enabled, which data source, memory settings, guardrails). Captions may only claim what this inventory says. In the ARIA run the deployed search was an in-agent catalog, not the OpenSearch path the README shows; the caption said so.
2. **One persona with one goal** that needs most features in a natural order. A shopper: arrive → ask in plain words → sign in → first answer → change one condition → expand (related item, "similar") → open the source/detail page → identity-bound tool (saved items) → out-of-scope question → another entry point → new conversation → stop a reply → reopen history → UI conveniences → delete → sign out.
3. **Check every planned prompt against the data** before recording. A "find similar" on a product that has no siblings returns an honest "nothing similar" and the take is wasted. Count matches in the catalog (e.g. 3 navy coats, only 1 under the budget) and move the action to a dense category.
4. **Cards outside the take**: intro (message, audience, what is real: "실제 배포 환경, 실제 모델 응답"), storyline (the numbered steps the take will follow), architecture (one card, official service icons, what each box does in this request), then after the take a "what you saw" grid and, for a proposal, "what changes for your system" (now / then rows), plus a one-line note of what is not implemented.

## 2. Captions: chip, purpose, how it works

```json
{"from": "budget_typing", "to": "budget_result", "chip": "04 조건 변경",
 "title": "예산만 바꿔 말해도 앞의 조건을 이어서 다시 찾습니다",
 "how": "AgentCore Memory에 저장된 같은 대화의 기록을 읽어 앞의 조건을 기억합니다"}
```

- **chip**: step number and feature name, the same numbers as the storyline card.
- **title** (≤45 chars, 합니다체): what the feature does for the user, or what happens on screen *for a reason*. Not a description of the frame.
- **how** (≤70 chars, optional): the mechanism, naming the real component (service, tool, check). This line is what makes a proposal video different from a promo: the audience learns how it is built.
- Same writing rules as [script.md](script.md): no middle dot, arrow or em dash (join with a comma or 와/과), no aphorisms, no translationese, no speed wording (the badge carries it). `onetake.py check` enforces length, characters and overlap.
- Sample or stubbed features say so in `how` ("데모 Lambda는 고객 ID별 샘플 목록을 돌려줍니다"). A caption that oversells a stub is the one the customer remembers.
- Two captions per turn usually: request and wait (`<k>_typing → <k>_result`), then the answer (`<k>_result → next step`), optionally a third on the cards.

## 3. Recording

- `node scripts/record_demo.mjs --url … --storyboard storyboard.mjs --name take --out raw --camera zoom --max-seconds 1500`. Start from [`scripts/storyboard.onetake.example.mjs`](../scripts/storyboard.onetake.example.mjs).
- Note names follow the turn convention (`<k>_typing`, `<k>_typed`, `<k>_working`, `<k>_result`, `<k>_answer`, `<k>_card_<i>`); `onetake.py` derives the ramps from them.
- **Guards that abort the take** (cheaper than filming a failure): non-200, an error frame, a guardrail stop reason, an expected tool not called, no cards rendered within 8 s (they render after the stream ends, so wait, don't count once).
- **Guardrail stops**: reproduce the exact answer text with the provider's apply/test API to see which policy fired before touching anything. In the ARIA run Bedrock's PII detector read the price "854,050원" as a card CVV, on output and on input (history and screened tool results). Changing a deployed guardrail is the user's decision: report the policy, the matched text and the options, then wait.
- **Popups and new tabs** are recorded as their own page video; save it (`popup.video().saveAs`) and insert it with `inserts` so the viewer sees the tab that really opened.
- **Destructive steps** (delete a conversation, an item): identify the target by an ID captured in this take (e.g. the last 8 characters of the session ID shown in the list), refuse if it does not match exactly one row.
- Keep failed takes (`takes/fail-N/` with their camlog and turns) and note why each failed.

## 4. Edit and assemble

```bash
python3 scripts/onetake.py check onetake.json      # anchors, caption rules, overlaps; fix before encoding
python3 scripts/onetake.py edit onetake.json       # clips/take.mp4 + .srt + .timeline.json
node scripts/render_cards.mjs cards                # cards/*.html -> PNG (start from assets/card-template.html)
python3 scripts/onetake.py assemble final.json     # cards + take -> final mp4 + .ko.srt (silent AAC track)
```

- Speeds: model wait ×4 (badge), sign-in ×2.5, typing ×1.6, everything the viewer reads ×1. Add a ×4 ramp over a navigation that flashes a blank page (logout redirect).
- `K` (media/camlog duration, ~1.03) is applied automatically; captions anchored to events stay aligned after any re-record.
- Caption palette: take `style` from the product UI (paper, ink, accent) so overlays and cards look like one piece.

## 5. Check before handing over

- `python3 scripts/onetake.py sheet final.mp4 --every 10`: read the sheet; every caption matches what its frame shows.
- `python3 scripts/onetake.py scan final.mp4`: blank-ish runs outside card fades are navigation flashes; ramp them.
- Full decode: `ffmpeg -v error -i final.mp4 -f null -` prints nothing.
- `qa/turns.json`: every turn 200 and finished as expected (a deliberate Stop is the only aborted one); the identity-bound tool was really called.
- In the README next to the video: length, what was real, what is sample, any change made to the deployment to film it, failed takes and why.
