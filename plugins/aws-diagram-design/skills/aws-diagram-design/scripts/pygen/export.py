#!/usr/bin/env python3
"""Rasterize built HTML diagrams to PNG (diagram <svg> only, transparent background).

    python3 export.py <html_dir_or_files...> [--png-dir DIR] [--scale 2]

Requires Playwright + Chromium:  pip install playwright && playwright install chromium
PNG size = viewBox × scale (960×560 @2 → 1920×1120). Waits for webfonts (Amazon Ember, Noto Sans KR) before capture.
"""
import argparse, pathlib, sys


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", type=pathlib.Path, help="HTML files or directories containing *.html")
    ap.add_argument("--png-dir", type=pathlib.Path, help="default: next to each source")
    ap.add_argument("--scale", type=float, default=2, help="device scale factor (1-4)")
    a = ap.parse_args()
    if not 1 <= a.scale <= 4:
        print("scale must be within 1..4 (see references/export.md § Sizing)", file=sys.stderr); return 2
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright isn't installed. Run:\n  pip install playwright\n  playwright install chromium", file=sys.stderr); return 3

    files: list[pathlib.Path] = []
    for p in a.inputs:
        files += sorted(p.glob("*.html")) if p.is_dir() else [p]
    if a.png_dir: a.png_dir.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        b = pw.chromium.launch(); page = b.new_page(device_scale_factor=a.scale)
        for src in files:
            out = (a.png_dir or src.parent) / (src.stem + ".png")
            page.goto(f"file://{src.resolve()}")
            page.wait_for_load_state("networkidle")
            page.evaluate("document.fonts.ready")
            page.wait_for_timeout(300)
            page.locator("svg").first.screenshot(path=str(out), omit_background=True)
            print("wrote", out)
        b.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
