#!/usr/bin/env python3
"""Render intro / chapter / summary cards for a reel as 1920x1080 MP4 (+ PNG preview) from a JSON spec.

  python3 make_cards.py cards.json --out clips

cards.json: {"card-intro": {"seconds": 8, "lines": [[kind, text, colour?], ...]}, "card-summary": {...}}
  kind    kicker (small bold label above the title) | title (one line each) | row (bullet line) | gap (spacer)
  colour  role name or "#rrggbb"; roles: fg (default) dim accent alt warn
Cards are silent, fade in/out 0.5 s, and drop into a reel manifest like any other clip. Intro card = the message and
what the demo shows, chapter card = one chapter title, summary card = take home messages (references/script.md).
Fonts: DEMO_FONT_BOLD / DEMO_FONT_REGULAR env, else Nanum, else fc-match (same rule as edit_demo.py).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1920, 1080, 30
LEFT = 150  # text column starts here; centred vertically
ROLES = {"fg": "#e8edf2", "dim": "#8b98a5", "accent": "#3ddc97", "alt": "#b39cff", "warn": "#f0a35e"}
BG = "#0b0f14"
# kind -> (font role, size, line step)
KINDS = {"kicker": ("bold", 30, 56), "title": ("bold", 64, 88), "row": ("regular", 36, 62), "gap": ("regular", 10, 34)}


def _font(env: str, preferred: str, pattern: str) -> str:
    if os.environ.get(env):
        return os.environ[env]
    if Path(preferred).exists():
        return preferred
    out = subprocess.run(["fc-match", "-f", "%{file}", pattern], capture_output=True, text=True)
    return out.stdout.strip() or preferred


FONTS = {"bold": _font("DEMO_FONT_BOLD", "/usr/share/fonts/truetype/nanum/NanumSquareB.ttf", "sans:bold"),
         "regular": _font("DEMO_FONT_REGULAR", "/usr/share/fonts/truetype/nanum/NanumSquareR.ttf", "sans")}


def colour(value: str | None) -> str:
    if value is None:
        return ROLES["fg"]
    if value.startswith("#"):
        return value
    if value not in ROLES:
        raise SystemExit(f"unknown colour role {value!r}; use one of {sorted(ROLES)} or #rrggbb")
    return ROLES[value]


def wrap(text: str, font: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines, cur = [], ""
    for word in text.split(" "):
        cand = f"{cur} {word}".strip()
        if cur and font.getlength(cand) > width:
            lines.append(cur)
            cur = word
        else:
            cur = cand
    return lines + [cur]


def render(lines: list[list], path: Path) -> None:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    laid = []
    for spec in lines:
        kind, text, col = (spec + [None, None])[:3] if len(spec) < 3 else spec
        text = text or ""
        if kind not in KINDS:
            raise SystemExit(f"unknown line kind {kind!r}; use one of {sorted(KINDS)}")
        role, size, step = KINDS[kind]
        font = ImageFont.truetype(FONTS[role], size)
        indent = 36 if kind == "row" else 0
        laid.append((kind, wrap(text, font, W - 2 * LEFT - indent) if text else [""], colour(col), font, step))
    total = sum(step * len(parts) for _, parts, _, _, step in laid)
    y = (H - total) // 2
    for kind, parts, col, font, step in laid:
        if kind == "row":
            d.rectangle([LEFT, y + 14, LEFT + 10, y + 24], fill=col)  # bullet square in the row's colour
        for part in parts:
            if part:
                d.text((LEFT + (36 if kind == "row" else 0), y), part, font=font, fill=col)
            y += step
    img.save(path)


def build(spec: Path, out: Path) -> None:
    cards = json.loads(spec.read_text())
    out.mkdir(parents=True, exist_ok=True)
    for name, card in cards.items():
        seconds = float(card["seconds"])
        with tempfile.TemporaryDirectory(prefix="card-") as tmp:
            png = Path(tmp) / f"{name}.png"
            render(card["lines"], png)
            fade = f"fade=t=in:st=0:d=0.5,fade=t=out:st={seconds - 0.5:.2f}:d=0.5"
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-loop", "1", "-framerate", str(FPS), "-i", str(png),
                            "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", f"{seconds}", "-vf", fade,
                            "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", "-b:a", "96k", "-shortest", "-movflags", "+faststart", str(out / f"{name}.mp4")],
                           check=True)
            Image.open(png).save(out / f"{name}.png")  # preview to read before cutting the reel
        print(json.dumps({"out": str(out / f"{name}.mp4"), "seconds": seconds}))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", type=Path)
    ap.add_argument("--out", type=Path, default=Path("clips"))
    a = ap.parse_args()
    try:
        build(a.spec, a.out)
    except SystemExit as e:
        print(e, file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
