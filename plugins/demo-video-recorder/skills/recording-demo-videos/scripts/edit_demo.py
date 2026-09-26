#!/usr/bin/env python3
"""Turn raw Playwright recordings (webm + camlog.json) into LinkedIn-ready MP4 clips.

  python3 edit_demo.py clip raw/intro.webm --script scripts/intro.json
  python3 edit_demo.py clip raw/intro.webm --title "…" --subtitle "…"      # no story: shot labels as captions
  python3 edit_demo.py reel reel.json --out reel.mp4

`clip` trims the page-load lead-in, burns a title card and lower-third captions, plays the take at 1.25x
(DEFAULT_SPEED; set "speed" in the script to change it, e.g. 4 for a waiting stretch, 1 for real time) and
encodes H.264 1080p30 + silent AAC. With `--script` the captions are the beats of a script JSON, each anchored
to a camlog event (see script_time). Without a script the captions fall back to the camera shot labels,
which describe where the camera looks, not what the viewer should understand.
`reel` concatenates trimmed windows from several finished clips into one highlight video.
Nothing about the recorded UI is altered; only overlays are added. Temp files are removed when each command ends.

Look (fixed here so every clip of a set matches; change the constants, re-run every clip):
  title      bold 58 px at x 96, y h-260, 0.2-4.2 s     subtitle  regular 30 px at y h-170, 0.5-4.2 s
  beat       regular 32 px at x 96, y h-150 (y 120 with "pos": "top"), dark box 0x0b0f14@0.72, border 18
  insight    bold 34 px, same place, blue box 0x1f6feb@0.82        tag  mono 22 px top-right (off unless --tag)
  every caption fades 0.35 s in and out; one caption at a time; a beat never starts under the title card
  fonts: DEMO_FONT_BOLD / DEMO_FONT_REGULAR / DEMO_FONT_MONO env, else Nanum, else fc-match (Korean needs a CJK font)

The raw input can also be a screen recording (.mov/.mp4) with no camlog: then every beat "at" is raw seconds
of that file. Crop black bars first with ffmpeg (-vf crop=...) so the frame is the UI only.

Script JSON:
  {"title": "03 판단을 넘깁니다", "subtitle": "…", "start": null, "end": null,   # optional "tag": persistent corner label, off by default
   "speed": 1.25,                             # default 1.25; 4 for waits (agent turns, cloud calls); "at" stays raw seconds
   "beats": [
     {"at": "shot:stage", "text": "Laya가 다음 스킬을 판단합니다", "dur": 5},
     {"at": "caption:System 2에 복구", "offset": 0.5, "text": "확률 0.95인데도 규칙이 이관합니다"},
     {"at": "note:play", "text": "…"},          # any rec.note(kind)
     {"at": "shot:stage#2", "text": "…"},       # 2nd occurrence
     {"at": 41.0, "text": "…", "style": "insight"},  # raw seconds; insight = accent box
     {"at": "shot:table", "text": "…", "pos": "top"}  # caption at the top when the lower third hides the evidence
   ]}
  Beat duration defaults to the gap to the next beat (max 7 s, min 1.5 s). `#n` counts occurrences of that
  same key / substring / kind only. Raw seconds are seconds from launch and are not validated against the
  camlog. A context fact with no event of its own (a batch statistic, a caveat) belongs on a late summary
  shot, e.g. the stats or wide shot, not mid-action.
"""
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path


def _font(env: str, preferred: str, pattern: str) -> str:
    """Font file for drawtext: $env override, else the preferred file if installed, else fc-match."""
    import os
    if os.environ.get(env):
        return os.environ[env]
    if Path(preferred).exists():
        return preferred
    out = subprocess.run(["fc-match", "-f", "%{file}", pattern], capture_output=True, text=True)
    return out.stdout.strip() or preferred

FONT_BOLD = _font("DEMO_FONT_BOLD", "/usr/share/fonts/truetype/nanum/NanumSquareB.ttf", "sans:bold")
FONT_REG = _font("DEMO_FONT_REGULAR", "/usr/share/fonts/truetype/nanum/NanumSquareR.ttf", "sans")
FONT_MONO = _font("DEMO_FONT_MONO", "/usr/share/fonts/truetype/nanum/NanumGothicCoding.ttf", "monospace")
W, H, FPS = 1920, 1080, 30
DEFAULT_SPEED = 1.25  # a demo at real time drags; 1.25x reads as a confident pace without looking sped up


def run(cmd: list[str]) -> None:
    print("+", " ".join(shlex.quote(c) for c in cmd), file=sys.stderr)
    subprocess.run(cmd, check=True)


def probe_duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         check=True, capture_output=True, text=True).stdout.strip()
    return float(out)


def drawtext(textfile: Path, *, font: str, size: int, x: str, y: str, start: float, end: float,
             color: str = "white", box: bool = True, alpha_fade: bool = True,
             boxcolor: str = "0x0b0f14@0.72") -> str:
    enable = f"between(t\\,{start:.2f}\\,{end:.2f})"
    # expansion=none: the text is literal (a '%' would otherwise start a drawtext expansion sequence)
    parts = [f"drawtext=fontfile={font}", f"textfile={textfile}", "expansion=none", f"fontsize={size}", f"fontcolor={color}",
             f"x={x}", f"y={y}", f"enable='{enable}'"]
    if box:
        parts += ["box=1", f"boxcolor={boxcolor}", "boxborderw=18"]
    if alpha_fade:
        # fade in/out over 0.35 s inside the enable window
        fade = (f"if(lt(t-{start:.2f}\\,0.35)\\,(t-{start:.2f})/0.35\\,"
                f"if(lt({end:.2f}-t\\,0.35)\\,({end:.2f}-t)/0.35\\,1))")
        parts.append(f"alpha='{fade}'")
    return ":".join(parts)


def script_time(at, log: list[dict]) -> float:
    """Resolve a beat anchor to raw seconds. Forms: number | 'shot:<key>[#n]' | 'caption:<substring>[#n]' |
    'note:<kind>[#n]' | '<kind>[#n]' (any camlog kind, e.g. 'scene_end', 'play')."""
    if isinstance(at, (int, float)):
        return float(at)
    spec, _, nth = str(at).partition("#")
    n = int(nth) if nth else 1
    kind, _, arg = spec.partition(":")
    if kind == "note":
        kind, arg = arg, ""
    if kind == "shot":
        hits = [e for e in log if e["kind"] == "shot" and e.get("key") == arg]
    elif kind == "caption":
        hits = [e for e in log if e["kind"] == "caption" and arg in e.get("text", "")]
    else:
        hits = [e for e in log if e["kind"] == kind]
    if len(hits) < n:
        raise SystemExit(f"script anchor not found in camlog: {at!r}")
    return float(hits[n - 1]["t"])


def build_clip(raw: Path, out: Path, title: str | None, subtitle: str | None, start: float | None,
               end: float | None, captions: bool, tag: str | None, script: Path | None = None) -> None:
    camlog = raw.with_suffix("").with_suffix(".camlog.json") if raw.suffix == ".webm" else None
    log = []
    if camlog and camlog.exists():
        log = json.loads(camlog.read_text())["log"]
    story = json.loads(script.read_text()) if script else None
    if story:
        title = title or story.get("title")
        subtitle = subtitle or story.get("subtitle")
        tag = tag or story.get("tag")
        start = start if start is not None else story.get("start")
        end = end if end is not None else story.get("end")
    shots = [e for e in log if e["kind"] == "shot"]
    if start is None:
        start = max(0.0, (shots[0]["t"] - 0.4) if shots else 0.0)
    duration = probe_duration(raw)
    if end is None:
        end = duration
    speed = float(story.get("speed", DEFAULT_SPEED)) if story else DEFAULT_SPEED  # beat "at" stays raw seconds
    with tempfile.TemporaryDirectory(prefix="edit-") as tmp_name:  # drawtext files; removed when the encode is done
        tmp = Path(tmp_name)
        _encode_clip(raw, out, title, subtitle, tag, start, end, captions, story, log, shots, speed, tmp)


def _encode_clip(raw: Path, out: Path, title, subtitle, tag, start: float, end: float, captions: bool,
                 story, log: list[dict], shots: list[dict], speed: float, tmp: Path) -> None:
    filters = ([f"setpts=PTS/{speed}"] if speed != 1 else []) + [f"fps={FPS}", f"scale={W}:{H}:flags=lanczos", "format=yuv420p"]
    rel = lambda t: (t - start) / speed  # noqa: E731
    placed = 0
    if title:
        (tmp / "title.txt").write_text(title)
        filters.append(drawtext(tmp / "title.txt", font=FONT_BOLD, size=58, x="96", y="h-260", start=0.2, end=4.2))
        if subtitle:
            (tmp / "subtitle.txt").write_text(subtitle)
            filters.append(drawtext(tmp / "subtitle.txt", font=FONT_REG, size=30, x="96", y="h-170", start=0.5, end=4.2))
    if tag:
        (tmp / "tag.txt").write_text(tag)
        filters.append(drawtext(tmp / "tag.txt", font=FONT_MONO, size=22, x="w-tw-40", y="h-58", start=0, end=10_000,
                                color="0xcfd8dc", alpha_fade=False))
    if story and story.get("beats"):
        beats = []
        for b in story["beats"]:
            t_raw = script_time(b["at"], log) + float(b.get("offset", 0))
            beats.append((rel(t_raw), b))
        beats.sort(key=lambda x: x[0])
        for i, (t0, b) in enumerate(beats):
            t0 = max(t0, 4.4 if title else 0.2 if speed == 1 else 0.0)  # never under the title card
            nxt = beats[i + 1][0] if i + 1 < len(beats) else rel(end)
            dur = float(b.get("dur", min(7.0, nxt - t0 - 0.3)))
            t1 = min(t0 + max(dur, 1.5), rel(end) - 0.1)
            if t1 - t0 < 1.0:
                print(f"skip beat (no room): {b['text']!r}", file=sys.stderr)
                continue
            f = tmp / f"beat{i}.txt"
            f.write_text(b["text"])
            y = "120" if b.get("pos") == "top" else "h-150"  # pos=top when the lower third would cover the evidence
            if b.get("style") == "insight":
                filters.append(drawtext(f, font=FONT_BOLD, size=34, x="96", y=y, start=t0, end=t1,
                                        color="0xffffff", boxcolor="0x1f6feb@0.82"))
            else:
                filters.append(drawtext(f, font=FONT_REG, size=32, x="96", y=y, start=t0, end=t1))
            placed += 1
    elif captions:
        labelled = [s for s in shots if s.get("label") and rel(s["t"]) > 4.6]
        for i, shot in enumerate(labelled):
            t0 = rel(shot["t"]) + 0.9  # let the camera settle first
            nxt = labelled[i + 1]["t"] if i + 1 < len(labelled) else end
            t1 = min(t0 + 4.5, rel(nxt) + 0.4, rel(end) - 0.1)
            if t1 - t0 < 1.2:
                continue
            f = tmp / f"cap{i}.txt"
            f.write_text(shot["label"])
            filters.append(drawtext(f, font=FONT_REG, size=32, x="96", y="h-150", start=t0, end=t1))
            placed += 1
    vf = ",".join(filters)
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-v", "error", "-stats", "-ss", f"{start:.3f}", "-to", f"{end:.3f}", "-i", str(raw),
           "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
           "-vf", vf, "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-profile:v", "high", "-level", "4.1",
           "-c:a", "aac", "-b:a", "96k", "-shortest", "-movflags", "+faststart", str(out)]
    run(cmd)
    print(json.dumps({"out": str(out), "seconds": round(rel(end), 2), "captions": placed}))


def probe_size(path: Path) -> str:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                          "-of", "csv=s=x:p=0", str(path)], check=True, capture_output=True, text=True).stdout.strip()
    return out.rstrip("x")


def build_reel(spec: Path, out: Path) -> None:
    """spec: {"segments": [{"file": "...mp4", "start": 0, "end": 25, "fade_in": 0}, ...], "fade": 0.4}"""
    cfg = json.loads(spec.read_text())
    fade = float(cfg.get("fade", 0.4))
    # concat with stream copy needs identical streams; a mixed-size reel fails late with a cryptic error, so check first
    sizes = {seg["file"]: probe_size(Path(seg["file"])) for seg in cfg["segments"]}
    if len(set(sizes.values())) > 1:
        raise SystemExit("reel segments differ in resolution: " + ", ".join(f"{f} {s}" for f, s in sizes.items()))
    with tempfile.TemporaryDirectory(prefix="reel-") as tmp_name:  # re-encoded parts; removed after the concat
        tmp = Path(tmp_name)
        parts = []
        for i, seg in enumerate(cfg["segments"]):
            src = Path(seg["file"])
            s, e = float(seg.get("start", 0)), float(seg.get("end") or probe_duration(src))
            d = e - s
            part = tmp / f"part{i:02d}.mp4"
            # per-segment "fade_in"/"fade_out" (0 = hard cut) join pieces of one scene without a dip to black
            fi, fo = float(seg.get("fade_in", fade)), float(seg.get("fade_out", fade))
            vf = ",".join([f"fade=t=in:st=0:d={fi}"] * (fi > 0) + [f"fade=t=out:st={max(0, d - fo):.2f}:d={fo}"] * (fo > 0)) or "null"
            af = ",".join([f"afade=t=in:st=0:d={fi}"] * (fi > 0) + [f"afade=t=out:st={max(0, d - fo):.2f}:d={fo}"] * (fo > 0)) or "anull"
            run(["ffmpeg", "-y", "-v", "error", "-ss", f"{s:.3f}", "-to", f"{e:.3f}", "-i", str(src), "-vf", vf, "-af", af,
                 "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-c:a", "aac", "-b:a", "96k", str(part)])
            parts.append(part)
        lst = tmp / "list.txt"
        lst.write_text("".join(f"file '{p}'\n" for p in parts))
        out.parent.mkdir(parents=True, exist_ok=True)
        run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", "-movflags", "+faststart", str(out)])
    print(json.dumps({"out": str(out), "seconds": round(probe_duration(out), 1), "parts": len(parts)}))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("clip")
    c.add_argument("raw", type=Path)
    c.add_argument("--out", type=Path)
    c.add_argument("--title")
    c.add_argument("--subtitle")
    c.add_argument("--tag", help="small persistent top-right label, e.g. the site URL")
    c.add_argument("--start", type=float)
    c.add_argument("--end", type=float)
    c.add_argument("--no-captions", action="store_true")
    c.add_argument("--script", type=Path, help="story script JSON: title/subtitle/tag + beats anchored to camlog events")
    r = sub.add_parser("reel")
    r.add_argument("spec", type=Path)
    r.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    if a.cmd == "clip":
        out = a.out or Path("clips") / (a.raw.stem + ".mp4")
        build_clip(a.raw, out, a.title, a.subtitle, a.start, a.end, not a.no_captions, a.tag, a.script)
    else:
        build_reel(a.spec, a.out)


if __name__ == "__main__":
    main()
