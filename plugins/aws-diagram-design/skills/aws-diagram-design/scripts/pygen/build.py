#!/usr/bin/env python3
"""Render spec files to HTML.

    python3 build.py <spec_dir> [--out DIR] [--langs ko,en] [--only slug,slug]

Every `spec_*.py` in <spec_dir> must define `build(lang) -> list[(slug, Canvas)]`.
Output: <out>/<slug>-<lang>.html (default <spec_dir>/out). Each label wider than its box prints
`WARN name|sub [slug-lang] '<text>' needs w>=N ...` to stderr with the minimum width that fits; resolve every WARN
(widen, shorten, or drop the sublabel) before exporting. --strict makes WARNs fail the build.
"""
import argparse, importlib, importlib.util, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec_dir", type=pathlib.Path)
    ap.add_argument("--out", type=pathlib.Path)
    ap.add_argument("--langs", default="ko,en", help="comma-separated; a spec may ignore lang")
    ap.add_argument("--only", default="", help="comma-separated slugs to build")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any label overflows its box")
    a = ap.parse_args()

    spec_dir = a.spec_dir.resolve(); out = (a.out or spec_dir / "out").resolve(); out.mkdir(parents=True, exist_ok=True)
    sys.path[:0] = [str(HERE), str(spec_dir)]          # `from awsdiag import Canvas, T` works from any spec dir
    import awsdiag
    only = {s for s in a.only.split(",") if s}; langs = [l for l in a.langs.split(",") if l]
    specs = sorted(spec_dir.glob("spec_*.py"))
    if not specs:
        print(f"no spec_*.py in {spec_dir}", file=sys.stderr); return 2
    n = 0
    for f in specs:
        spec = importlib.util.spec_from_file_location(f.stem, f); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        for lang in langs:
            for slug, canvas in mod.build(lang):
                if only and slug not in only: continue
                for issue in canvas.check(): awsdiag._warn(issue)
                (out / f"{slug}-{lang}.html").write_text(canvas.html(), encoding="utf-8"); n += 1
                print("html", slug, lang)
    print(f"{n} files → {out}")
    if awsdiag.WARNINGS:
        print(f"{len(awsdiag.WARNINGS)} WARN (text overflow or layout). Fix every one before exporting; see references/python-generator.md § WARN policy.", file=sys.stderr)
        return 1 if a.strict else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
