---
name: persona-review
description: Review any document, site, or deck through a level×role persona panel (e.g. L200 developer, L300 architect, L100 manager) — each persona actually reads it and returns concrete findings with severity and fixes. Use to catch "only makes sense to the author" problems in workshops, proposals, docs, and slides. Triggers: "persona review", "read this as an L200 developer", "페르소나 평가", "이 문서 L300 관점으로 읽어줘".
---

# Persona Review

Read a deliverable through the eyes of its actual audience — a **level×role matrix** of personas — and return findings the author can act on. This is the standalone form of the workshop pipeline's stage 6, usable on any artifact.

> Shared reference: the persona matrix, rubric, and severity definitions live at the plugin root — `references/persona-rubric.md`. Read it first.

## Procedure

1. **Fix the audience.** Ask (or read from context) which levels (L100–L400) × roles (developer, architect, data/ML, manager, …) actually matter. Review only those cells — not the whole matrix.
2. **One parallel review per active cell** (subagents; isolate failures per cell — one failed cell never voids the rest). Each persona reads the *actual artifact*, start to finish, as that person: their vocabulary, their prior knowledge, their patience.
3. **Findings, not vibes.** Each persona returns **≥ 2 findings**, each with: severity (**blocker / major / minor**), where (page/section), what breaks for *this* persona, and a concrete fix. An "it's all good" review is void — re-run it.
4. **Count completeness:** active cells == returned reviews. Re-run missing cells individually.
5. **Synthesize:** merge, dedupe, sort by severity. Blockers and majors get applied (or explicitly declined with a reason); minors are listed.

## Output shape

- A findings table: `persona | severity | where | issue | fix`
- A one-paragraph completion verdict per persona: could this person actually finish/use the artifact?

## Rules

- Personas critique the artifact, never invent facts about the domain — uncertainty is flagged, not filled in.
- Severity means: **blocker** = this persona cannot proceed/is misled; **major** = will cause real friction or wrong takeaway; **minor** = polish.
- Keep the panel honest: if every persona says the same thing, say so once — don't inflate the count.
