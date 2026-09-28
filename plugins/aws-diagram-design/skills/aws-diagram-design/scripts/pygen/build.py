#!/usr/bin/env python3
"""Render spec files to standalone SVG (and PNG with --png).

    python3 build.py <spec_dir> [--out DIR] [--langs ko,en] [--only slug,slug] [--strict] [--png] [--scale 2] [--png-dir DIR]

Every `spec_*.py` in <spec_dir> must define `build(lang) -> list[(slug, Canvas)]`.
Output: <out>/<slug>-<lang>.svg (default <spec_dir>/out). Each label wider than its box prints
`WARN name|sub [slug-lang] '<text>' needs w>=N ...` to stderr; resolve every WARN before shipping.
--strict makes WARNs fail the build. --png runs finalize.py on each SVG (check, embed fonts, PNG @scale);
a check failure fails the build.
"""
import argparse, importlib.util, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec_dir", type=pathlib.Path)
    ap.add_argument("--out", type=pathlib.Path)
    ap.add_argument("--langs", default="ko,en", help="comma-separated; a spec may ignore lang")
    ap.add_argument("--only", default="", help="comma-separated slugs to build")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any label overflows its box")
    ap.add_argument("--png", action="store_true", help="finalize each SVG: check, embed fonts, render PNG")
    ap.add_argument("--scale", type=float, default=2.0)
    ap.add_argument("--png-dir", type=pathlib.Path, help="default: next to each SVG")
    a = ap.parse_args()

    spec_dir = a.spec_dir.resolve(); out = (a.out or spec_dir / "out").resolve(); out.mkdir(parents=True, exist_ok=True)
    sys.path[:0] = [str(HERE), str(HERE.parent), str(spec_dir)]   # awsdiag, finalize, and the specs
    import awsdiag, finalize
    only = {s for s in a.only.split(",") if s}; langs = [l for l in a.langs.split(",") if l]
    specs = sorted(spec_dir.glob("spec_*.py"))
    if not specs:
        print(f"no spec_*.py in {spec_dir}", file=sys.stderr); return 2
    written: list[pathlib.Path] = []
    for f in specs:
        spec = importlib.util.spec_from_file_location(f.stem, f); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        for lang in langs:
            for slug, canvas in mod.build(lang):
                if only and slug not in only: continue
                for issue in canvas.check(): awsdiag._warn(issue)
                path = out / f"{slug}-{lang}.svg"; path.write_text(canvas.svg(), encoding="utf-8"); written.append(path)
                print("svg", slug, lang)
    print(f"{len(written)} files → {out}")
    if awsdiag.WARNINGS:
        print(f"{len(awsdiag.WARNINGS)} WARN (text overflow or layout). Fix every one before shipping; see references/python-generator.md § WARN policy.", file=sys.stderr)
        if a.strict: return 1
    if a.png:
        for path in written:
            argv = [str(path), "--scale", str(a.scale)] + (["--png-dir", str(a.png_dir)] if a.png_dir else [])
            if finalize.main(argv) != 0: return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
