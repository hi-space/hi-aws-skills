# Reel manifest (`edit_demo.py reel`)

```json
{"fade": 0.4, "segments": [
 {"file": "clips/replay-normal.mp4",   "start": 0,  "end": 16},
 {"file": "clips/replay-escalation.mp4", "start": 0, "end": 46},
 {"file": "clips/live-move_object.mp4", "start": 0,  "end": 42},
 {"file": "clips/live-move_object.mp4", "start": 76, "end": 90},
 {"file": "clips/lab-slippery.mp4",     "start": 343, "end": 372},
 {"file": "clips/replay-results.mp4",   "start": 0,  "end": 30}
]}
```

- `file`: a finished clip (already has title card and captions). Paths relative to the cwd where `edit_demo.py` runs.
- `start`/`end`: seconds inside that clip; `end` null or omitted = to the end. The same clip may appear several times (intro window, then the payoff later).
- `fade`: video and audio fade in/out per segment, seconds. 0.4 reads as a clean cut with no flash.
- Each segment is re-encoded with the same x264 settings, then concatenated with stream copy, so the output is exactly the sum of windows.

Choosing windows: open `raw/<stem>.camlog.json` and take `t` of the shots you want; clip time = camlog `t` minus the clip's trimmed lead-in (`edit_demo.py clip` prints `seconds` and starts 0.4 s before the first shot unless `--start` was given). Keep the title card (first 4 s of a clip) only for the first appearance of that clip.

Two reels usually cover a post: a **short** (3–6 min, one window per scene, ends on the results scene) and a **full** (every clip whole, with the slowest scene's dead time cut out).

Per-segment `fade_in` / `fade_out` (seconds, `0` = hard cut) override `fade` for that segment. Use them when one scene was cut into several clips at different `speed` values; only the outer edges of the scene fade:

```json
{"fade": 0.4, "segments": [
 {"file": "clips/04a-lab-start.mp4",  "fade_out": 0},
 {"file": "clips/04b-lab-agent.mp4",  "fade_in": 0, "fade_out": 0},
 {"file": "clips/04c-lab-result.mp4", "fade_in": 0}
]}
```

`04b` was clipped with `"speed": 4`, so its 17.5 s of agent turns play in 4.4 s; the viewer sees one continuous scene. Every segment must have the same resolution; the tool aborts before encoding if two files differ.
