---
name: recording-demo-videos
description: Use when the user wants a demo, LinkedIn or product video of a web UI (dashboard, live simulation, replay page) with zoom-ins on panels, a title card, burned-in captions, or a highlight reel cut from longer takes; also when captioning a screen recording (.mov) they made themselves. Headless Linux with Playwright and ffmpeg. Korean triggers: 데모 영상, 시연 영상, 링크드인 영상, 영상 녹화, 화면 녹화 편집, 자막 넣어줘, 하이라이트 릴, 릴 만들어줘.
---

# Recording Demo Videos

## Overview

Decide the message first, then record the real UI in wall-clock time with Playwright `recordVideo` while an in-page CSS camera pans and zooms; then burn the story's captions, render the intro and summary cards, and cut a reel with ffmpeg from a JSON manifest. The video argues one thing; chapters are its answers, captions are the steps of the argument, the frame is the evidence for each step. Captions never describe what is on screen. Nothing in the app is patched; only the camera is scripted.

Two inputs are supported: a take recorded by `record_demo.mjs` (webm + camlog, beats anchored to events) or a screen recording the user made (.mov/.mp4, beats anchored to raw seconds). Editing and reel steps are the same.

## Pipeline

1. **Find selectors**: open the app with Playwright once and dump candidates, e.g. `page.evaluate(() => [...document.querySelectorAll('section,aside,[class*=panel],[class*=strip]')].map(e => e.className + ' ' + JSON.stringify(e.getBoundingClientRect().toJSON())))`, at the recording viewport (1920×1080, rects change with size), or take a screenshot and read it. Click targets without a class: `page.getByRole('button', { name: /Run/ })`. Never record against guessed selectors; a `rec.focus` that matches nothing leaves the camera where it was, prints a `selector matched nothing` warning and writes `missing: true` into the camlog. Grep the camlog for `missing` before editing.
2. **Write the story** ([references/story.md](references/story.md)): one message sentence with its number sources; 3–6 chapters, each titled with the **answer** it gives (not the scene name) and subtitled with the setting; `cards.json` for the intro and summary cards, so the argument exists end to end before any beat; then per chapter 4–15 beats (`scripts/<stem>.json`, format in `python3 scripts/edit_demo.py --help`). A beat is one step of the argument — event → who decided → consequence, with the number — ≤ 45 characters, anchored to the second the event is visible. The last beat of a chapter is `"style": "insight"`: the chapter's answer in one sentence, which later becomes a row on the summary card. Sentence rules: [references/caption-style.md](references/caption-style.md).
3. **Storyboard** (`storyboard.mjs`, copy `scripts/storyboard.example.mjs`): one async function that navigates, calls `rec.install()`, then alternates shots (`rec.reset` / `rec.region` / `rec.focus(key, selector, {pad,kmax}, label)`) with waits. Plan the reel length here: every `rec.sleep` is footage, so size the holds to the target duration and leave ~10 % headroom for the 1.4 s camera moves. Fixed holds (`rec.sleep`) when you know what happens; the event-probe loop only when the UI changes at unpredictable times. Use `tap(locator)` for every click; `rec.note('<kind>')` at every beat's event so the script can anchor to it. Shot labels are an edit sheet, not captions. The example's `?paused=1` URL is app-specific.
4. **Record**: `node scripts/record_demo.mjs --url <site> --storyboard ./storyboard.mjs --name <stem> --out raw --playwright-root <dir>` → `raw/<stem>.webm` + `raw/<stem>.camlog.json`. `--playwright-root` is any directory whose `node_modules` contains `playwright` (the app repo usually); if none, `mkdir pw && cd pw && npm i playwright && npx playwright install chromium`.
5. **Cut points**: read the camlog; each entry has `t` (seconds from launch) and a kind (`shot` with `key`/`label`, `caption` when the UI's own caption changed, your `note` kinds). Fill each beat's `at` with `shot:<key>[#n]`, `caption:<substring>`, `<note kind>` or raw seconds, plus `offset`. Scene boundaries = anchor `t` minus ~0.5 s so the camera move is inside the scene. Prefer event anchors: after a re-record every raw-second anchor must be re-tuned by hand, event anchors survive unchanged.
6. **Clip**: `python3 scripts/edit_demo.py clip raw/<stem>.webm --script scripts/<stem>.json` → `clips/<stem>.mp4`, 1080p30 H.264. No persistent overlays (no URL or watermark) unless the user asks; `--tag` exists for that case only. Title card 0–4 s, then the beats as lower-thirds (default duration = gap to the next beat, max 7 s). A missing anchor aborts with its name; fix the script, not the camlog. Without `--script` the tool falls back to shot labels as captions, which only say where the camera looks. Waiting stretches (agent turns, cloud calls, physics settling) get `"speed": 4` in that clip's script instead of full playback; split the scene into one script per tempo, each with its own `start`/`end` window on the same raw file (`04a.json` 0–72 s at 1×, `04b.json` 72–89.5 s at `"speed": 4`, `04c.json` 89.5– at 1×), run `clip` once per script, and re-join the pieces in the reel with `fade_out: 0` on the earlier piece and `fade_in: 0` on the later one so there is no dip to black inside one scene (worked example in [references/reel-manifest.md](references/reel-manifest.md)).
7. **Cards**: `python3 scripts/make_cards.py cards.json --out clips` → `clips/card-intro.mp4`, `clips/card-summary.mp4` (+ `.png` previews; read them). Intro 8 s states the message and the context; summary 10–12 s lists one row per chapter answer with its number, coloured by the layer that acted. Every card sentence is copied from the post or an insight beat. Optional chapter cards (3–4 s) when the setting changes.
8. **Reel**: write `reel.json` (see [references/reel-manifest.md](references/reel-manifest.md)): intro card, chapters in argument order, summary card last; `python3 scripts/edit_demo.py reel reel.json --out reel.mp4`. Length = sum of windows; fades are inside each window, no overlap. All segments must share one resolution; the tool aborts before encoding if they differ.
9. **Check**: read one still per clip at its insight beat and confirm the frame is evidence for that sentence, and that the sentence is a row on the summary card; `ffprobe` duration; one `ffmpeg -ss <t> -frames:v 1` still per clip at a zoomed moment; read the still to confirm a full 1920×1080 frame with no blank margins. If the UI did something other than what the script says (a timeout, a different recovery path), rewrite the beat to what happened; do not keep a sentence the frame contradicts.

Run independent scenes in parallel; run scenes that are CPU-heavy in the browser (WASM models, WebGL physics) one at a time or their timing slows. Both commands delete their temp files when they finish; raw takes and clips are the only outputs left on disk.

### User-made screen recordings (.mov)

`edit_demo.py clip` accepts any video without a camlog. Normalize first with ffmpeg, keeping the timing unchanged so every beat `at` is raw seconds of the original file:

```bash
ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 demo.mov   # e.g. 3024,2110
ffmpeg -i demo.mov -vf "crop=3024:1896:0:214,scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2" -c:v libx264 -crf 18 -c:a aac demo-1080.mp4
```

`crop=w:h:x:y` removes the menu bar or black strip (read one still to measure it); `scale … decrease` + `pad` letterboxes instead of stretching. Then `python3 scripts/edit_demo.py clip demo-1080.mp4 --script scripts/demo.json`, one `clip` command per script. Beat candidates are the moments the UI state changes: a button press, a status text or counter that changes, a panel or result table that appears, the end of a motion. Take a still every 5 s first (`ffmpeg -ss <t> -frames:v 1`), note where those changes happen, then refine to 0.5 s around each one and write the beat from what the still shows. A scene that ends abruptly can be given a 3 s last-frame hold with `-vf tpad=stop_mode=clone:stop_duration=3` before clipping.

## Quick reference

| Need | Do |
|---|---|
| Zoom on an element | `rec.focus('key', '.selector', { pad: 12, kmax: 1.75 }, 'edit-sheet label')` |
| Zoom on a page rectangle | `rec.region('key', x, y, w, h, { pad: 0, kmax: 1.1 })` |
| Back to wide | `rec.reset('wide')` |
| Click a control | `await tap(page.locator(...))`; text inputs: fill them before `rec.install()` or set `.value` and dispatch `input` via `locator.evaluate` |
| Cut when the UI changes | poll a cheap `page.evaluate` probe every 300 ms, shoot on state edges, hold 4–6 s |
| Anchor a beat | `rec.note('run_clicked')` in the storyboard → `"at": "run_clicked"` in the script |
| Speed up a dull stretch | own script with `"speed": 4`, join in the reel with `fade_in: 0` / `fade_out: 0` |
| Message, chapters, cards | [references/story.md](references/story.md) |
| Caption sentence and look | [references/caption-style.md](references/caption-style.md) |
| Intro / summary card | `cards.json` → `python3 scripts/make_cards.py cards.json --out clips` |
| Fonts | `DEMO_FONT_BOLD/REGULAR/MONO` env, else installed Nanum, else `fc-match` |

## Common mistakes

- **Captions that read the screen** ("로봇이 물체를 다시 잡습니다", "System 2 패널이 열립니다", or camera labels like "Robot + decision stack"): the viewer can already see that; they learn nothing about the message. Every beat is a step of the argument: event → who decided → consequence, with the number.
- **Chapters named after scenes** ("Live 낙하", "Lab seed 7") instead of the answer they give ("스텝마다 판단하는 게이트 · Laya"): the reel becomes a tour of pages instead of an argument. Title = answer, subtitle = setting.
- **Cards written last**: if the summary card is written after the beats, chapters without an answer slip in. Write `cards.json` before the beats; a chapter with no row on the summary card is cut.
- **Captions that generalize past the take**: "the plan is reused on recovery" when this recording shows the plan failing and the local policy taking over. Caption the take that was recorded; move the general claim to the post text.
- **Per-frame screenshots** for deterministic animation: a live UI (physics, model calls, polling) keeps running in wall time while each screenshot takes 100–300 ms, so 30 s of UI becomes minutes and the timeline is false. Record wall-clock video; the camera moves via CSS transitions.
- **`page.click()` / `fill()`**: they scroll the target into view and break the camera math. `tap()` dispatches the event without scrolling.
- **Measuring rects while zoomed**: `getBoundingClientRect` returns transformed coordinates; the camera inverts the current body transform and folds in scroll. Do not hand-roll camera math in storyboards.
- **`deviceScaleFactor` > 1 with a smaller viewport**: `recordVideo` captures CSS pixels, so the page lands top-left in the 1080p frame with blank margins. Viewport stays 1920×1080; zoom only via `kmax`.
- **Cropping or `zoompan` in ffmpeg afterwards**: upscales rasterized pixels, blurry at 2×.
- **`networkidle` on apps that poll or hold a socket**: wait for a selector plus a fixed settle.
- **Headless WebGL is slow**: app timeouts may fire that would not on a desktop. Report the run as it happened; do not edit the outcome.
- **Full playback of waits**: a 60 s scene where 40 s is a spinner loses the viewer; the user preferred 4× over the wait every time. Compress with `speed`, keep the decisions at 1×.
- **Disk**: raw webm ≈ 10 MB/min, clips ≈ 15 MB/min; check `df` before a batch and delete superseded takes.
