#!/usr/bin/env python3
"""Build the illustrated concept figures of a blog work directory and make a preview sheet.

    python3 build_figures.py <work> [--only slug,slug] [--langs ko] [--install <N>:<slug> ...]

Reads  <work>/diagrams/_specs/spec_*.py   (each defines build(lang) -> [(slug, Canvas)])
Writes <work>/diagrams/out/<slug>-<lang>.svg, <work>/diagrams/out/png/<slug>-<lang>.png,
       <work>/diagrams/out/preview.png    (all PNGs stacked; open it and look before shipping)
--install 2:il-vs-rl copies the ko PNG to <work>/images/fig2-il-vs-rl.png and the SVG to <work>/diagrams/.

The renderer is the aws-diagram-design skill's scripts/pygen/build.py. It is looked up in
$AWS_DIAGRAM_SKILL_DIR, the sibling plugin of this one, ~/.claude/skills, and the plugin cache.
_pict.py is copied into _specs/ when it is missing; an existing copy is left alone so local pictograms survive.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
PICT = SKILL_DIR / "assets" / "illustration" / "_pict.py"


def find_pygen() -> Path | None:
    rel = Path("scripts/pygen/build.py")
    cands = []
    if os.environ.get("AWS_DIAGRAM_SKILL_DIR"):
        cands.append(Path(os.environ["AWS_DIAGRAM_SKILL_DIR"]))
    cands.append(SKILL_DIR.parents[2] / "aws-diagram-design" / "skills" / "aws-diagram-design")
    cands.append(Path.home() / ".claude" / "skills" / "aws-diagram-design")
    cache = Path.home() / ".claude" / "plugins"
    if cache.exists():
        cands += sorted(cache.glob("**/aws-diagram-design/skills/aws-diagram-design"), reverse=True)[:5]
    for c in cands:
        if (c / rel).exists():
            return c / rel
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("work", type=Path)
    ap.add_argument("--only", default="")
    ap.add_argument("--langs", default="ko")
    ap.add_argument("--install", nargs="*", default=[], metavar="N:slug")
    a = ap.parse_args()

    specs = a.work / "diagrams" / "_specs"
    if not list(specs.glob("spec_*.py")):
        print(f"no spec_*.py in {specs}; start from {SKILL_DIR / 'assets' / 'illustration' / 'spec_example.py'}", file=sys.stderr)
        return 2
    if not (specs / "_pict.py").exists():
        shutil.copyfile(PICT, specs / "_pict.py")
        print(f"copied _pict.py into {specs}")
    build = find_pygen()
    if build is None:
        print("aws-diagram-design not found. Install the plugin or set AWS_DIAGRAM_SKILL_DIR to its skill directory.", file=sys.stderr)
        return 2

    out = a.work / "diagrams" / "out"
    png = out / "png"
    cmd = [sys.executable, str(build), str(specs), "--out", str(out), "--langs", a.langs, "--png", "--png-dir", str(png)]
    if a.only:
        cmd += ["--only", a.only]
    r = subprocess.run(cmd, capture_output=True, text=True)
    noise = ("OK ", "fonts embedded", "png:", "svg ")
    for line in (r.stdout + r.stderr).splitlines():
        if not line.startswith(noise):
            print(line)
    if r.returncode != 0:
        return r.returncode

    lang = a.langs.split(",")[0]
    pngs = sorted(png.glob(f"*-{lang}.png"))
    try:
        from PIL import Image
        ims = [Image.open(p).convert("RGB") for p in pngs]
        w = max(i.width for i in ims)
        sheet = Image.new("RGB", (w, sum(i.height for i in ims) + 24 * len(ims)), "#8A8A8A")
        y = 0
        for i in ims:
            sheet.paste(i, (0, y)); y += i.height + 24
        if sheet.height > 6000:      # keep the sheet readable when opened as one image
            sheet = sheet.resize((int(w * 6000 / sheet.height), 6000))
        sheet.save(out / "preview.png")
        print(f"preview: {out / 'preview.png'}  ({len(pngs)} figures). Open it and check overlaps before shipping.")
    except ImportError:
        print("Pillow not installed; open each PNG in", png)

    for item in a.install:
        n, slug = item.split(":", 1)
        src_png, src_svg = png / f"{slug}-{lang}.png", out / f"{slug}-{lang}.svg"
        if not src_png.exists():
            print(f"--install {item}: {src_png} not found", file=sys.stderr); return 1
        (a.work / "images").mkdir(exist_ok=True)
        name = slug[4:] if slug.startswith("fig-") else slug
        shutil.copyfile(src_png, a.work / "images" / f"fig{n}-{name}.png")
        shutil.copyfile(src_svg, a.work / "diagrams" / f"fig{n}-{name}-{lang}.svg")
        print(f"installed images/fig{n}-{name}.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
