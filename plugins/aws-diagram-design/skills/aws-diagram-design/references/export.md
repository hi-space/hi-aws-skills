# Export — PNG from SVG, and the two HTML cases

The deliverable is the `.svg`; its PNG comes from `finalize.py`. This file covers the three ways a PNG (or SVG) request arrives.

## 1. `.svg` → `.png` (the normal case)

```
python3 <skill-dir>/scripts/finalize.py diagram.svg [--scale 2] [--png-dir DIR]
```

`finalize.py` re-runs the contract check (fails loudly, file untouched), embeds the Amazon Ember faces the file uses as base64 woff2, then screenshots the `<svg>` in headless Chromium at `viewBox × scale` with a transparent page background (the paper `<rect>` inside the SVG supplies the visible background). Hangul text pulls Noto Sans KR at render time only.

Playwright missing → the SVG is finished, the PNG is skipped, and this instruction is printed; relay it verbatim and never auto-install:

> Playwright isn't installed. To enable PNG export, run:
> ```
> pip install playwright
> playwright install chromium
> ```

## 2. 1.x HTML diagram → SVG + PNG

Files produced by aws-diagram-design 1.x are an HTML page wrapping one `<svg>`.

```
python3 <skill-dir>/scripts/html_to_svg.py old-diagram.html        # → old-diagram.svg (page CSS carried, foreignObject → text)
python3 <skill-dir>/scripts/finalize.py old-diagram.svg           # check, embed, PNG
```

`html_to_svg.py` extracts the *outer* `<svg>` depth-aware (nested icon `<svg>`s stay inside), keeps only the page CSS rules that style SVG content, and adds the `local()` `@font-face` block. If the check then fails, the usual cause is an unescaped `&` in a label — a standalone SVG is strict XML.

## 3. Motion HTML → static-frame PNG

Motion diagrams (`animation.md`) stay HTML because their controller is JavaScript. Render the **HTML**, not an extracted SVG, so fonts and the static frame behave:

```python
from playwright.sync_api import sync_playwright
import sys, pathlib

src, out = sys.argv[1], sys.argv[2]
scale = float(sys.argv[3]) if len(sys.argv) > 3 else 2

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(device_scale_factor=scale)
    page.goto(f"file://{pathlib.Path(src).resolve()}?motion=static")
    page.wait_for_load_state("networkidle")
    page.evaluate("document.fonts.ready")
    assert page.locator("[data-motion-root]").first.get_attribute("data-frame") == "static"
    page.locator("svg").first.screenshot(path=out, omit_background=True)
    browser.close()
```

Never capture after an arbitrary delay; the `data-frame="static"` assertion is the gate.

## Sizing

Pixel size = `viewBox × scale`. The size decision was made when the diagram was drawn ([`output-spec.md` §2](output-spec.md)); export only picks the multiplier.

| Destination | Scale | From a 1280×720 `viewBox` |
|---|---|---|
| Docs, README, wiki | 2 | 2560×1440 |
| Slide deck (projected) | 2 | 2560×1440 |
| Print / PDF handout | 3 | 3840×2160 |
| Inline thumbnail, email | 1 | 1280×720 |

Exact pixel targets: `scale = target_width / viewBox_width` (fractional is fine — a 960-wide viewBox at 1200 px is `1.25`). Never below 1 (soft type) or above 4 (upscaling a layout designed smaller) — redraw at another preset instead. If the aspect ratio doesn't match, say so and offer to redraw; padding or cropping a finished diagram breaks the 40 px safe margin.

## What export never does

- Modifies a `.svg` beyond the font-embedding block, or any `.html`.
- Adds `<script>` to an SVG; embeds an HTML wrapper via `foreignObject`.
- Runs unprompted — PNG for hand-drawn diagrams is produced by the `finalize.py` step of the drawing procedure (SKILL.md §10), and re-export only when asked.
