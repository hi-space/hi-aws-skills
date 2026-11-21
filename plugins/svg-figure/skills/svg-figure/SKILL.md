---
name: svg-figure
description: Use when the user wants an explanatory figure drawn by hand as SVG and delivered as .svg and .png files (or pasted inline into an HTML page) - a structure or flow sketch, before/after or option comparison, a physical object with its parts or sensor coverage, a motion path, a step-by-step scene - in a flat editorial style where colour means state (decided, new, risk, proposal) and the same drawing reads in light and dark. Not for AWS architecture diagrams with official service icons (aws-diagram-design) or editable draw.io files (aws-drawio-diagram). Korean triggers - 그림 그려줘, SVG로 그려줘, 설명 그림, 개념도, 도해, 구조도, 전후 비교 그림, 센서 배치도, 동작 그림, 페이지에 넣을 그림, 회의록 그림 스타일.
---

# SVG Figure

## Overview

A figure shows at a glance what the surrounding text says. Position, size, line and colour each carry one meaning, and colour is written as a **token** (`fill="var(--ok)"`), never as a literal. That one rule gives the style: state colours that mean the same thing in every figure, and a drawing that works in light and dark without being redrawn.

Three files per figure, kept side by side:

| File | What it is |
|---|---|
| `<name>.src.svg` | The source you draw and later edit. Token colours, `<title>` and `<desc>` describe the content. |
| `<name>.svg` | Deliverable. Tokens resolved to hex, font stack added. Regenerated, never hand-edited. |
| `<name>.png` | Deliverable raster at 2x. |

To change a figure, edit `<name>.src.svg` and export again. The exported files have lost the state meaning of each colour.

## Workflow

1. **Brief.** Write down the one message the figure must carry, the facts it may use, and where it will sit (column, full width, phone, slide). Facts come from the user's material only.
2. **Compose.** Pick the composition that explains the message ([Composition](#composition)). If the subject is a physical thing or a movement, read [references/technical-illustration.md](references/technical-illustration.md) first.
3. **Draw** `<name>.src.svg` to the [figure contract](#figure-contract). Start from [assets/example.src.svg](assets/example.src.svg) for the skeleton.
4. **Check**: `python3 scripts/svg_figure.py check <name>.src.svg --prefix <name>-`. Fix every error. Each warning is an estimated overflow or overlap to confirm in the next step.
5. **Look**: `python3 scripts/svg_figure.py preview <name>.src.svg -o preview.html --png preview.png`, then open `preview.png`. Read every label in the light, dark and phone renders. Fix, re-check, re-render until nothing collides, clips or is too small to read.
6. **Export**: `python3 scripts/svg_figure.py export <name>.src.svg -o <name>.svg --png <name>.png`. Report the three paths.

## Figure contract

### Canvas and type

| Slot | viewBox | Smallest font-size |
|---|---|---|
| Column figure beside or between paragraphs (default) | `0 0 560 H` | 17 |
| Full-width figure, desktop or slide | `0 0 1120 H` | 15 |
| Phone version of a full-width figure | `0 0 400 H` | 14 |

`H` is whatever the content needs. A column figure is shown at roughly half to two thirds of its size on a phone, which is why its floor is 17; the phone render in the preview shows the real result. A figure read mostly on phones is drawn at 400 wide instead. When labels do not fit, cut labels or add height; the font floor does not move. A full-width figure that must also work on a phone gets a second SVG at 400 wide: the same content restacked top to bottom, names only, same numbers on the same elements.

Start with 6-10 elements for a column figure and adjust to the content.

### Skeleton

```xml
<svg viewBox="0 0 560 500" role="img" aria-labelledby="NAME-title NAME-desc">
<title id="NAME-title">One sentence: what the figure shows.</title>
<desc id="NAME-desc">The relations spelled out, so the figure is understood without seeing it.</desc>
<defs><marker id="NAME-arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto">
<path d="M0 0 L10 5 L0 10 Z" fill="var(--muted)"/></marker></defs>
…
</svg>
```

- The root has `viewBox`, `role="img"`, `aria-labelledby`; `<title>` then `<desc>` are its first two children. No `width`, `height`, `style` or `font-family`: the page or the export sets size and font.
- Every `id` starts with the figure's file name and a hyphen (`order-split-title` in `order-split.src.svg`; `NAME-` above), so several figures can share one page. `check --prefix` enforces it.
- Elements: `svg g path rect circle ellipse line polyline polygon text tspan title desc defs marker linearGradient stop clipPath`. `url()` only as `url(#id)`.
- Every `<text>` carries `font-size`. Hierarchy comes from `font-weight` (700 for names, regular for notes) and from `--ink` against `--muted`.

### Colour tokens

Values live in [assets/figure-tokens.css](assets/figure-tokens.css) as a light and a dark set. For a page with its own palette, copy that file, change the values, keep the names, and pass `--tokens <file>` to every command.

| Token | Use |
|---|---|
| `--ink` | Text, strong outlines, number badges |
| `--muted` | Secondary text, arrows, region titles |
| `--line` | Neutral borders, guides |
| `--panel` | Element background |
| `--band` | Region background (a layer, a group, a lane) |
| `--paper`, `--soft` | Page background, figure card background; also inner chips |
| `--key` | Highlight **fill** behind the one key result. Never text or stroke colour. |

State is drawn the same way in every figure:

| State | Fill | Stroke |
|---|---|---|
| Decided, confirmed | `--ok-bg` | `--ok`, solid |
| New, being added | `--new-bg` | `--new`, solid |
| Unknown, at risk | `--risk-bg` | `--risk`, `stroke-dasharray="6 4"` |
| Conditional proposal | `--panel` | `--muted`, `stroke-dasharray="6 4"` |
| Existing, unchanged | `--panel` | `--line`, solid |

Use a state colour when the element has that state. Kinds of things (camera against LiDAR, team A against team B) are told apart by shape, position and label.

The figure has no legend. A page shows the state legend once, outside the figures (markup in the tokens file); a standalone file gets its states named in the caption or in the labels themselves ("미측정", "신규").

### Labels and lines

- Labels are short noun phrases in the reader's language, using the official name of each product or term.
- Size each box to its label: a Hangul or CJK character is about 1.0 x font-size wide, a Latin character about 0.55. A long label goes on two `<tspan>` lines.
- Choose straight, curved or right-angled lines by what shows the relation most clearly. Lines never cross text: leave 6 or more units between a line and a label. Arrowheads are `<marker>` elements. A label on an arrow sits beside it, or in a pill (`rx` = half the height) on top of it.
- Stroke widths: 2 for the main outline and main flow, 1.5 for secondary, 1 for inner chips. Corner radius 10-12 for regions and cards, 8 for chips.
- Draw order: backgrounds and regions, then connectors between nodes, then nodes, then text. For an object with callouts the order differs; see the reference.
- Number badges (a filled `--ink` circle with a `--panel` digit) mark the points the text discusses, in reading order.

## Composition

Boxes in a row are the weakest option. First decide what the reader must see, then let the layout say it:

| The message is about | Composition |
|---|---|
| What sits on what, who owns what | Layers or nested regions; position is the meaning |
| What flows where, in what order | Flow along one axis; the arrow label says what moves |
| What changes | Before and after with shared parts in the same relative place and only the change coloured: side by side at 1120, stacked (before on top) at 560 and 400 |
| Options against criteria | Matrix: rows are options, columns are criteria, cells hold confirmed values |
| Where parts are, what a sensor covers, how a thing moves, what happens step by step | Technical illustration: `annotated`, `coverage`, `cutaway`, `exploded`, `motion`, `storyboard` ([reference](references/technical-illustration.md)) |
| None of the above fits | Free composition: pick the visual metaphor first, then combine techniques (parts + coverage + path, section + zoomed detail) |

A robot's sensor layout is drawn as the robot, and a movement as the object moving. A comparison of structures draws the structures. Size shows importance: the element the message is about is the largest or the most central.

Only the given facts go in. Where a position, angle, distance or count is unknown, draw it as a concept and say so in a label ("개념 배치", "감지 범위 개념도"), or leave it out. Example scenarios in this skill are not facts.

## Delivery

| Destination | Command or step |
|---|---|
| `.svg` + `.png` (default) | `python3 scripts/svg_figure.py export <name>.src.svg -o <name>.svg --png <name>.png` |
| Dark background | add `--theme dark --bg paper` |
| Card background behind the figure | add `--bg soft` |
| Slides, Word | the exported `.png`, or the exported `.svg` (colours are plain hex) |
| A file that follows the viewer's light/dark setting | add `--adaptive`; only where the surrounding background follows that setting too |
| Inline in an HTML page | paste the **source** SVG into `<figure class="fig">`, include the tokens CSS once, show the legend once; then `check page.html` validates every figure and catches duplicate ids |

## Common mistakes

| Symptom | Fix |
|---|---|
| Hex colours or a `<style>` block in the source | Tokens only. A per-figure palette is what breaks dark mode and state meaning. |
| 12-14px text in a 560 canvas | Floor is 17. Fewer labels or more height. |
| Legend drawn inside the figure | Remove it; the page or caption carries it. |
| Risk colour used to tell two kinds of parts apart | State colours mean state. Use shape and label. |
| `--key` yellow as text or line | Fill only. |
| Callout line disappears under the object's body | Draw callouts after the body (see reference). |
| State word repeated in every label ("(신규)", "(확정)") | The colour already says it. Name a state in words only where a standalone file needs it, once. |
| Edited the exported `.svg` | Edit `.src.svg`, export again. |
| Delivered without opening `preview.png` | The check estimates text width; only the render shows collisions. |
