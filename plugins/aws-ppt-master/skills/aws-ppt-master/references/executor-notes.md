> See [`executor-base.md`](./executor-base.md) for the always-loaded Executor core.

# Executor Speaker-notes Branch

Conditional late-stage authority for generating or validating the complete speaker-notes document.

**Trigger**: Default loads this after the final quality check when the effective Speaker Notes outcome in `design_spec.md §I` is enabled (a missing legacy outcome defaults to enabled); Quick loads it after its final check when the agent selected notes. With notes disabled, do not load this branch or create `notes/total.md`.

## 1. Complete Speaker-notes Document

Write the whole deck to `notes/total.md` in one batch: `# <number>_<page_title>` per page, `---` between pages. Write prose only — no list/bullet markup, stage markers, key-point labels, duration lines, or other metadata. Keep one language unless the confirmed contract is bilingual — then every page keeps the same segment order (first language, blank line, second language).

**Pre-SVG script branch**: when `notes/total.md` already exists from a final/literal script, validate it instead of regenerating. Retain every word and segment of a final/literal script; agent-authored Quick notes may be repaired only for final-SVG inconsistency. A `# Slide <number>` heading remains valid until Generate Step 7.1 resolves the roster.

**Length follows content**: size natural sentences to semantic burden — two to five is typical, not a cap; anchor pages may use less and dense pages more. Duration is pacing guidance only: never pad, repeat, compress, or omit meaning to hit it.

## 2. Final-SVG Grounding and Coverage

**Hard rule — the final SVG is the visible page authority**: read every finalized `svg_output/<slide>.svg` in slide order with the active plan/context and approved sources; never write from the outline or core message alone.

Before drafting, internally inventory the visible title/subtitle and every information-bearing direct-root `<g id>` (structured placeholder content counts). Coverage means its unique claim, evidence, example, relationship, qualifier, or implication — not merely its label — enters the notes. For a pre-SVG script, apply the inventory in reverse: every independent visible claim is supported by its script segment; repair the visual page or return to planning for final/literal input, repair the notes for agent-authored Quick notes, and give every spoken idea needing orientation a visible state or explicit speech-only role.

- Text blocks, comparisons, and processes keep every independent fact or relationship; combine related short groups causally or comparatively.
- Charts, tables, and KPIs state the takeaway, decisive values or trend, comparison basis, implication, and material uncertainty — not every axis, row, or cell.
- Quotes keep the decisive clause, material attribution, and relevance. Explain semantic images or text-free diagrams only from the SVG plus plan/source; never infer facts from appearance.
- Speak a source or footer only when attribution, uncertainty, or qualification changes the argument. Omit backgrounds, decoration, chrome, page numbers, and fixed Master/Layout atoms.

Form one coherent argument in intended reading/reveal order — proposition → evidence or mechanism → implication or bridge; DOM order need not be speaking order. A sentence may cover related groups and a complex group may need several sentences, but no independent group disappears to meet a count. Never vocalize IDs, positions, colors, icons, "this card shows" descriptions, or coverage markers.

## 3. Reading Mode

| `consumption_mode` | Notes emphasis |
|---|---|
| `text` | Interpret and connect a self-contained page; synthesize every independent information group rather than omitting it |
| `balanced` | Connect visible claim and evidence, explain the trade-off, bridge forward |
| `presentation` | Carry reasoning, context, and supporting detail intentionally omitted from the sparse page |

Put transitions naturally in the opening sentence when useful; never label them. When `notes/total.md` is complete, return to Generate Step 7.1 (Default) or `quick-generate.md` §4 (Quick); each route owns splitting and its success criterion.
