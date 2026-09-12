#!/usr/bin/env python3
"""Trace flat-colour PNG icons into 48x48 SVGs that follow the AWS resource-icon file layout.

    python3 scripts/trace_png_icons.py <png_dir> <out_dir> --service Amazon-Bedrock-AgentCore [--color '#7B27FF'] [--map name=Resource ...]

For every PNG: split opaque pixels into colour classes (near-black, and each remaining dominant colour),
trace each class with potrace (pip install potracer), and write
    <out_dir>/Res_<service>_<Resource>_48.svg
with a 0 0 48 48 viewBox, one <path> per colour, fill-rule evenodd, and a <title> like the official set.
Use --map to rename files (`Policy_Engine=Policy-Engine`); unmapped names get `_`→`-` and Title-Case words.
Prints the list of written files so INDEX.md / aws-icons.html can be updated.
"""
import argparse, collections, pathlib, sys
from PIL import Image

try:
    import potrace
except ImportError:
    sys.exit("potrace missing: pip install potracer")

UP = 2  # trace at 2x for smoother curves


def classes(im: Image.Image):
    """Return {hex: bool-mask} for near-black and the dominant chromatic colours (>=2% of opaque pixels)."""
    w, h = im.size; px = im.load()
    opaque = [(x, y) for y in range(h) for x in range(w) if px[x, y][3] > 128]
    counts = collections.Counter()
    for x, y in opaque:
        r, g, b, _ = px[x, y]
        counts["#000000" if max(r, g, b) < 110 else f"#{r//16*16:02X}{g//16*16:02X}{b//16*16:02X}"] += 1
    keep = {c for c, n in counts.items() if n >= 0.02 * len(opaque)}
    # merge chromatic buckets into their median colour
    buckets = collections.defaultdict(list)
    for x, y in opaque:
        r, g, b, _ = px[x, y]
        key = "#000000" if max(r, g, b) < 110 else f"#{r//16*16:02X}{g//16*16:02X}{b//16*16:02X}"
        if key in keep: buckets[key].append((x, y, r, g, b))
    out = {}
    for key, pts in buckets.items():
        if key == "#000000": col = "#000000"
        else:
            rs = sorted(p[2] for p in pts); gs = sorted(p[3] for p in pts); bs = sorted(p[4] for p in pts); m = len(pts) // 2
            col = f"#{rs[m]:02X}{gs[m]:02X}{bs[m]:02X}"
        mask = [[False] * w for _ in range(h)]
        for x, y, *_ in pts: mask[y][x] = True
        out.setdefault(col, mask)
        if col != "#000000" and len(out) > 1:
            # merge near-identical chromatic buckets (anti-alias variants) into the first chromatic colour
            first = next(c for c in out if c != "#000000")
            if first != col:
                for y in range(h):
                    row = out[first][y]; src = mask[y]
                    for x in range(w):
                        if src[x]: row[x] = True
                del out[col]
    return out


def trace(mask, scale: float) -> str:
    import numpy as np
    bm = potrace.Bitmap(~np.array(mask, dtype=bool))  # potracer inverts internally: True must mean background
    path = bm.trace(turdsize=4, turnpolicy=potrace.POTRACE_TURNPOLICY_MINORITY, alphamax=1.0, opticurve=True, opttolerance=0.2)
    d = []
    f = lambda pt: f"{pt.x*scale:.3f},{pt.y*scale:.3f}"
    for curve in path:
        d.append("M" + f(curve.start_point))
        for seg in curve:
            if seg.is_corner:
                d.append("L" + f(seg.c) + "L" + f(seg.end_point))
            else:
                d.append("C" + f(seg.c1) + " " + f(seg.c2) + " " + f(seg.end_point))
        d.append("Z")
    return "".join(d)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("png_dir", type=pathlib.Path); ap.add_argument("out_dir", type=pathlib.Path)
    ap.add_argument("--service", required=True, help="e.g. Amazon-Bedrock-AgentCore")
    ap.add_argument("--category", default="Artificial-Intelligence", help="for the <title> only")
    ap.add_argument("--map", nargs="*", default=[], help="Stem=Resource-Name overrides")
    ap.add_argument("--color", help="force every chromatic class to this hex (unify slightly different purples)")
    a = ap.parse_args()
    ren = dict(m.split("=", 1) for m in a.map)
    a.out_dir.mkdir(parents=True, exist_ok=True)
    for png in sorted(a.png_dir.glob("*.png")):
        res = ren.get(png.stem) or "-".join(w[:1].upper() + w[1:] for w in png.stem.replace("_", "-").split("-"))
        im = Image.open(png).convert("RGBA")
        im = im.resize((im.width * UP, im.height * UP), Image.LANCZOS)
        scale = 48 / im.width
        cls = classes(im)
        if a.color:
            cls = {("#000000" if c == "#000000" else a.color.upper()): m for c, m in cls.items()}
        paths = [f'        <path d="{trace(mask, scale)}" fill="{col}"/>' for col, mask in cls.items()]
        name = f"Res_{a.service}_{res}_48"
        svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
               f'<svg width="48px" height="48px" viewBox="0 0 48 48" version="1.1" xmlns="http://www.w3.org/2000/svg">\n'
               f'    <title>Icon-Resource/{a.category}/{name}</title>\n'
               f'    <g id="Icon-Resource/{a.category}/{name}" stroke="none" stroke-width="1" fill-rule="evenodd">\n'
               + "\n".join(paths) + "\n    </g>\n</svg>\n")
        (a.out_dir / f"{name}.svg").write_text(svg)
        print(f"{name}.svg  colours={list(cls)} bytes={len(svg)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
