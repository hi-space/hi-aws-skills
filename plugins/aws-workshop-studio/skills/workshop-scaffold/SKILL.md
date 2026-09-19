---
name: workshop-scaffold
description: Generate a complete hands-on AWS workshop from a topic, scenarios, and target customer. Produces a proven quick-* VitePress site (feature catalog, scenario labs, sample datasets, AWS architecture diagrams, image slots, customer co-branding) and evaluates it with a level×role persona panel to lock in improvements. Triggers: "build a workshop", "workshop scaffold/builder", "make a hands-on workshop", "이 주제로 워크샵 만들어줘", "핸즈온 워크샵 스캐폴드".
---

# Workshop Scaffold

> **Paths in this file**: shared assets live at the **plugin root**, two levels up from this SKILL.md — `references/`, `scripts/`, `assets/`, `examples/` all resolve there. `scripts/gate.sh` / `workshop-check.sh` / `image-manifest.mjs` invocations inside pipeline stages refer to the **generated workshop's own bundled copies** (cwd = the workshop), which `new-workshop.sh` puts there.

Turn **topic + scenarios + target customer** into one complete quick-\* VitePress workshop. Fill the proven skeleton in `assets/scaffold/` — don't invent structure. Explain with visuals, not prose (INV-8). Say **why** before **how** — every architecture and service comes with the reason it was chosen, what it contributes, and what changes once adopted (INV-9). Verify AWS facts fresh, never from memory.

Self-contained: skeleton, scripts, hooks, and references are all bundled — a user starting from nothing can build and deploy end to end.

## Pipeline — 8 stages

`mode: staged` (default) stops at ★ for SA sign-off; `oneshot` runs through but checks the same conditions and halts on violation. **Before starting each stage 2–8, run `bash scripts/gate.sh <stage>`** — it hard-blocks if the previous stage's artifact is missing (INV-1a). Full per-stage contract: `references/pipeline-contract.md`.

1. **Intake** → `brief.yaml`. Collect: topic, AWS services, audience (level×role), scenarios, duration, format (hands-on/booth/presenter-led), languages, mode, customer (name, industry, tech level) — **ask for the customer logo and favicon image files** (path or drag-and-drop; explicit `null` if none — never skip the question, never fabricate a logo) — **and ask for design preferences** (primary/accent color, mood, dark/light; `auto` accepted → derive from the customer brand + topic service + audience persona per `references/branding.md` §Design derivation, labeled `source: derived`).
2. **Research ★** → `artifacts/02-feature-facts.md` + `02a-company-context.md` + `02b-audience-context.md`. **Fan out in parallel**: a company cell, an audience-roles cell, and one cell per technology (GA/region/preview verified per `references/research-discipline.md`, confidence-labeled). Merge tech cells; cells in == rows out.
3. **Blueprint ★** → `artifacts/03-blueprint.md` + `artifacts/03a-architecture-rationale.md`. Scenario arc, scene decomposition, feature→scene mapping, dataset needs, **a planned visual per scene** (GATE-3e; the diagram list always starts with the workshop overview architecture and one per scenario), open questions — all closed before stage 4. The rationale (`references/architecture-rationale.md`, GATE-3f): problem, chosen architecture, each decision with the alternative rejected, per-service role and value, before/after by audience role, one insight sentence per scene.
4. **Generate** → `docs/**`, `demo_datasets/**`, `artifacts/04-image-manifest.json`. Fill templates (`references/templates/` — overview, feature, scene), datasets, architecture diagrams with the **`aws-diagram-design`** skill and mermaid flows (`references/diagram-recipes.md`), branding (`references/branding.md`). Every scene page gets ≥1 visual (GATE-4d); the overview page renders the architecture diagram plus why-this-architecture, per-service value and before/after from `03a`; every scene and feature page carries its "why" block (GATE-4e).
5. **Assemble** → build. Copy skeleton via `scripts/new-workshop.sh` (bundles the enforcement scripts + `.claude/` hooks into the workshop), wire config/nav/i18n, build clean.
6. **Persona review + walkthrough loop** → `artifacts/06-persona-review.md`, `06b-walkthrough-round-N.md`. Level×role panel per `references/persona-rubric.md` (parallel cells, apply blockers/majors, rebuild). Then GATE-6d: a fresh-eyes participant agent **follows the workshop for real** — executes every executable step, checks links/datasets/prompts/build/deploy — an author agent fixes what it hits, and the loop repeats with a new fresh agent until a clean round (max 3).
7. **QA** → `artifacts/07-qa-report.md`. `bash scripts/workshop-check.sh --full`.
8. **Handoff** → `artifacts/08-handoff.md`. Capture manifest (`node scripts/image-manifest.mjs`), presenter notes pointer, deploy steps, known limitations.

## Enforcement: hooks over prose

The generated workshop ships with deterministic enforcement — don't rely on remembering the rules:

- `.claude/settings.json` (in the scaffold) wires a **Stop hook** → `workshop-check.sh --fix` (datasets, presenter notes, emoji, assets, visual-first) and a **PreToolUse hook** → `protect-brief.mjs` (blocks edits to `brief.yaml` after intake; INV-4 — amend via `artifacts/00-amendments.md`).
- `scripts/gate.sh <stage>` hard-blocks stage entry without the prerequisite artifact (INV-1a) and generation while the blueprint has `[BLOCKER]`s.
- What the hooks can't check (label honesty, dataset realism, persona quality) stays in `references/pipeline-contract.md` — read it before running.

## Non-negotiable rules

- **Visual-first (INV-8).** Setup/example screen → `<Screenshot>` slot; architecture → `aws-diagram-design` / `aws-drawio-diagram` (official AWS icons); flow/order → mermaid; concept → excalidraw; scene→feature chain → `<FlowMap>`. A text-only scene page is a defect.
- **Why before how (INV-9).** No service appears without its reason, its contribution, and the change it brings. Value claims carry confidence labels; no invented figures; compare against the customer's current way, not against competitors.
- **Never generate a product screenshot.** Slots are real capture targets. AI images only for labeled conceptual illustration.
- **Official AWS icons only** for architecture/flow diagrams.
- **Customer logos/names** only for a genuine engagement; no fabricated testimonials or restyled logos.
- **Confidence labels** (verified / documented / assumed / needs-check) propagate and are never promoted.
- **Presenter-only content** lives in `PRESENTER_NOTES.md`, outside `docs/`.

## Two ways to run

- **Interactive (default)** — drive the 8 stages yourself; best for `staged`.
- **Workflow** — `assets/workshop-pipeline.workflow.mjs` runs the pipeline as a multi-agent Workflow (parallel research/generation/persona cells). Requires the user's explicit opt-in to workflow orchestration; honors the same gates.

## References

`references/`: format-spec · component-api · templates/ (overview · feature · scene) · persona-rubric · research-discipline · diagram-recipes · architecture-rationale · branding · pipeline-contract. Example input `assets/brief.example.yaml` · example run `examples/hanbitpay/`.
