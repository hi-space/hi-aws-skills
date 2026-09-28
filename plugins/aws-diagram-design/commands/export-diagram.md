---
description: Render an aws-diagram-design SVG to PNG (or lift a 1.x/motion HTML diagram to SVG + PNG)
argument-hint: <svg-or-html-file> [--scale=N] [--png-dir=<dir>]
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
---

Produce the PNG for the diagram at `$1`, following [`skills/aws-diagram-design/references/export.md`](../skills/aws-diagram-design/references/export.md). Treat that reference as the source of truth — don't reimplement the logic here.

Full argument string: `$ARGUMENTS`

## Behaviour by input

- **`.svg`** (the normal deliverable) → run `python3 <skill-dir>/scripts/finalize.py <file> [--scale N] [--png-dir DIR]`. This re-checks the file, embeds the Amazon Ember faces it uses, and writes `<stem>.png` next to it.
- **`.html` produced by aws-diagram-design 1.x** (static page with one diagram) → run `python3 <skill-dir>/scripts/html_to_svg.py <file>` to get `<stem>.svg`, then `finalize.py` on that. Report both new paths; leave the HTML in place unless the user asks to delete it.
- **`.html` motion diagram** (has `data-motion-root`) → follow `export.md § 3` (static frame via `?motion=static`). No SVG is produced for motion files.

## Flags

- `--scale=N` — PNG device scale factor, 1–4, fractional allowed (`1.25` turns a 960-wide viewBox into 1200 px). Default `2`.
- `--png-dir=<dir>` — write the PNG somewhere other than next to the source.

## Required behaviour

1. **No path provided** → ask which file to export. Don't guess.
2. **Source is `assets/index.html`** (gallery) → refuse and ask for a specific diagram file.
3. **`finalize.py` exits 1** → show its FAIL lines verbatim and stop; the file was not modified.
4. **`--scale` outside 1–4** → `finalize.py` exits 2 with its own message; relay it and stop.
5. **Playwright missing** → `finalize.py` prints the install instruction; relay it verbatim, do **not** auto-install.

After producing the outputs, report the file paths and pixel sizes back to the user.
