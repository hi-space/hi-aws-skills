# Pipeline contract — every gate and procedure, spelled out from the harness's point of view

This document is the contract that the harness running the skill (Claude Code + subagents/workflows) **must** honor. It promotes failures observed across two real live runs into gates.

## 0. Shared invariants (cut across every stage)

| ID | Invariant | Why (observed failure) |
|---|---|---|
| INV-1 **output = file** | Each stage **writes its result as a file** to `artifacts/NN-name.ext`. The next stage reads that file. It does not depend on the returning text/summary of the previous agent. **No execution instruction can defer this — not "return as text", not "debug/test", not "partial run"** — if a partial run is needed, write it to a file as `stageNN-partial.md`. | A research agent wrote to a file but returned only a summary → the full text never reached the blueprint. In the cold run, a single "return as text" instruction defeated the file-writing of stages 2 & 3 (GAP-01) |
| INV-1a **verify prerequisite output exists** | Before starting each stage, **hard-blocking check** that the immediately preceding stage's output file actually exists at the designated path. Absent = automatic failure, do not start. | GAP-01 — the next stage proceeds even when the file is missing |
| INV-2 **stall tolerance, splitting, model by difficulty** | Choose the model **by difficulty** — use the strongest model (opus) + high effort for the hardest reasoning stage, and cheap models to get throughput on parallel/mechanical stages (it is not "heavy, so use a weak model"). Prepare for stalls (a no-progress timeout): ① retry (backoff) ② on repeated stalls, **split** the work into smaller units (e.g., generate the blueprint scenario by scenario) ③ **compress the seed prompt down to only the facts needed** (do not load everything) ④ resume with `resumeFromRunId` if needed. Splitting/parallelism reduces the blast radius of a stall more than one single mega-generation. | The blueprint stall was not opus's fault but a compound of a large prompt + one single mega-generation + the watchdog. opus + high + a large prompt worked fine on this session's research and design outputs (= banning the tier is a misattribution) |
| INV-3 **isolate structured-output failures** | A schema-enforcing agent is a parallel cell unit. Even if one cell fails by exceeding its retry limit, keep the rest alive. Re-run just that cell with `resumeFromRunId`, or fall back to text. | One persona exceeded the StructuredOutput retry limit |
| INV-4 **SSOT immutable** | `brief.yaml` is read-only. To change a value, record an explicit amend in `artifacts/00-amendments.md` and regenerate only the affected stages. | Requirement to manage fixed values |
| INV-5 **completeness count** | Verify requested count == produced count at every stage. A mismatch is a gate failure. (6 personas requested vs 5 produced, features in flows vs the features pages, datasets matching in three places) | Synthesis discovered after the fact that "6 were requested but only 5 arrived" |
| INV-6 **preserve confidence labels** | The verified/documented/assumed/needs-check labels propagate into the generation stage and are never erased. Never promote an assumption to verified. **Attach the label as a column/field in that stage's structured output (scene tables, etc.), not in prose or a friction log.** If a table has no label, it is a gate failure. | Research discipline. In the cold run, the "assumed" label from stage 2 carried into the stage 3 scene table and hardened as if confirmed (GAP-02) |
| INV-7 **booth & multi-entry check** | When `format==booth`, GATE-3b difficulty is computed not on a fixed order but also against **arbitrary entry points** (so a mid-session joiner does not get hit by a bomb of new concepts). Add a **reset time < inter-scene wait** constraint to GATE-4a. GATE-4c forbids not only fake screenshots but also **hiding real latency with a pre-cache to stage it as if real-time** (label it explicitly). | GAP-07 · 08 · 09 — booth loop replay, mid-session join, and cold-start concealment leak through static checks |
| INV-8 **visual-first — visuals are mandatory, not decorative** | Text is the last resort, not the default. Every scene and every non-trivial concept **must** carry at least one visual, chosen by this rule: (a) a setup/config screen or an example result screen → a `<Screenshot>` capture slot; (b) a flow, a sequence/order of steps, or a whole-picture/architecture view → a diagram — **drawio (AWS4 official icons)** for service architecture & trust boundaries, **mermaid** for flows/sequences/decisions, **excalidraw** for a rough concept/analogy/before-after; (c) the workshop's own scene→feature chain → the `<FlowMap>` component. A wall of text explaining a flow or a screen, with no visual, is a defect. Enforced at GATE-3e (planned) and GATE-4d (present) and by `workshop-check.sh`. | Minimal-text is the whole point of the quick-* format; without a hard rule, generation drifts back to prose and the workshop stops being skimmable |
| INV-9 **why before how — insight-first** | Every architecture and service the participant touches is accompanied by *why it was chosen*, *what it contributes*, and *what changes once adopted*. Stage 3 writes it once (`artifacts/03a-architecture-rationale.md`, per `references/architecture-rationale.md`); stage 4 renders it on the overview page (architecture diagram + four marked sections), in every scene's "Why these services here" table and every feature's "Why this service" section. Value claims carry confidence labels; no invented figures. | Workshops that walked participants through every click left architects and decision-makers unable to say why the architecture was chosen or what they would gain — the hands-on succeeded, the adoption conversation did not. |

## 1. Per-stage contract

Each stage: **reads → steps → writes → GATE (pass condition) → failure handling**. In `staged` mode the SA signs off at a ★GATE; `oneshot` is automatic but **checks the same pass conditions** and halts on violation.

**Deterministic enforcement (hooks/scripts — not prose):** before starting each stage 2–8, run `bash scripts/gate.sh <stage>` (hard form of INV-1a + the blueprint `[BLOCKER]` check; exit 2 = do not start). The generated workshop's `.claude/settings.json` wires a Stop hook (`workshop-check.sh --fix`: datasets, presenter notes, emoji, assets, visual-first) and a PreToolUse hook (`protect-brief.mjs`: INV-4, blocks editing `brief.yaml` after intake). Everything hooks cannot decide (label honesty, dataset realism, review quality) remains this document's contract.

### 1 Intake
- reads: SA input · writes: `brief.yaml` (+ `artifacts/01-brief-snapshot.yaml`)
- steps: collect required fields (§brief-schema) → for missing fields, ask (do not guess defaults). **Explicitly ask for the brand image files**: the customer logo and a favicon (a file path or drag-and-drop; store under `assets/customer/` and copy into `docs/public/images/`). If the SA has none, record `null` — the site uses the wordmark/theme-color placeholder and the capture manifest lists the logo as pending. Never fabricate or restyle a logo (branding.md). **Also ask for design preferences** (`design:` block — primary/accent color, mood keywords, dark/light): every field accepts `auto`, in which case derive per branding.md §Design derivation and record `source: derived` before the brief freezes.
- GATE: all required brief-schema fields filled + `mode`, `audience`, `region`, `scenarios` present + **logo/favicon asked and answered** (a path or an explicit null — "never asked" fails the gate) + **design block present with a `source` label** (given or derived — an unlabeled palette fails).
- failure: missing field → cannot proceed, re-ask.

### 2 Research ★
- reads: `brief.yaml` · writes: `artifacts/02-feature-facts.md` (+ `02a-company-context.md`, `02b-audience-context.md`)
- steps: run research as **parallel cells** (INV-3 applies — one failed cell never sinks the rest):
  - **company cell** → `02a-company-context.md`: the customer's industry, scale, public tech stack, and domain vocabulary — so scenarios/datasets read as "our story", not generic.
  - **audience cell** → `02b-audience-context.md`: what the target roles (from `audience.roles`) actually do day-to-day, their tooling, and what they already know — calibrates scene difficulty and jargon (feeds GATE-3b).
  - **one technology cell per service/feature group** in `brief.aws.services` → verify **region availability and GA/preview** via web/docs → confidence label → "design implications".
  - a **merge step** combines the technology cells into `02-feature-facts.md` (counting cells in == rows out, INV-5) and cross-references 02a/02b.
- **GATE-2a region consistency**: does each service actually work in brief.region. If a feature that does not work is needed by a scenario → cannot pass without presenting a resolution (alternate region / alternate service / scope reduction). **`confirmed_date` and `valid_until` (default: run date −14 days) are required for the verdict** — on entry to GATE-5 · 8, if `valid_until` has passed, it cannot pass without re-verification (region tables for new services change frequently, GAP-05).
- **GATE-2b naming ambiguity**: when one name can refer to two features (e.g., KB), nail down a definitive interpretation + its basis.
- GATE-2c: a confidence label on every feature. `needs-check` items are entered into the pre-blueprint to-do list.
- failure: if web access is unavailable, label everything `needs-check` and state that fact explicitly (do not disguise it as assumed).

### 3 Blueprint ★
- reads: `brief.yaml`, `02-feature-facts.md`, `02a`, `02b` · writes: `artifacts/03-blueprint.md`, `artifacts/03a-architecture-rationale.md`
- steps: scenario→scene decomposition (difficulty) · feature→scene mapping (flows) · features catalog · dataset requirements · diagram list · rough image slots · **open questions** · **architecture rationale** (`references/architecture-rationale.md`: problem, chosen architecture, decisions with alternatives, per-service role and value, adoption benefits, one insight per scene).
- **GATE-3a close open questions**: the blueprint's open questions (e.g., vector store undecided, anomaly-detection logic undecided) must **all be decided before entering generation (4)**. If a scene script already presumes an undecided item as settled, it fails. → record the decision as a brief amend or in the blueprint.
- **GATE-3b difficulty continuity**: difficulty jump between adjacent scenes ≤ 1 step. ≤ 2 new concepts per scene (split if exceeded).
- **GATE-3c format fitness**: when `format==hands-on`, every scene has ≥ 1 action the participant **does directly** (no watch-only). When `format==booth`, watching + one hands-on action is allowed. When `presenter-led`, a presenter demo is allowed.
- GATE-3d: every scene's features exist in the features catalog + match flows (INV-5).
- **GATE-3e visual plan (INV-8)**: the blueprint assigns, as a **structured column per scene**, at least one planned visual and its kind — `screenshot` (setup/example screens), `drawio` (architecture), `mermaid` (flow/sequence), `excalidraw` (concept), or `flowmap`. A scene row with an empty visual column is a `[BLOCKER]`. The diagram list and image-slot outline must cover every entry in this column (INV-5). The diagram list always starts with the **workshop overview architecture** and **one architecture diagram per scenario**, drawn with `aws-diagram-design` (see `diagram-recipes.md` §2).
- **GATE-3f architecture rationale (INV-9)**: `03a-architecture-rationale.md` exists with all six sections; one row per service in `02-feature-facts.md` (INV-5); at least one alternative per decision; every value claim labeled; region/GA caveats from stage 2 carried over; one insight sentence per scene in the blueprint. Missing or generic rows ("improves security") are `[BLOCKER]`s. `gate.sh 4` refuses to start generation without `03a`.
- failure: mark gate-violating items in the blueprint as `[BLOCKER]`; in staged mode, the SA rejects.

### 4 Generation
- reads: `brief.yaml`, `02`, `03`, `03a` · writes: `docs/**`, `demo_datasets/**`, `artifacts/04-image-manifest.json`
- steps: fill pages with the templates (overview/feature/scene) · generate datasets (+ locales) · architecture diagrams with `aws-diagram-design` + mermaid flows (`diagram-recipes.md`) · Screenshot slots → manifest.
- **GATE-4a dataset realism**: the data satisfies the constraints the scene logic requires (e.g., moving-average demo → guarantee time-series continuity, an inserted outlier exceeds the threshold). State it in the spec.
- **GATE-4b three-way match**: dataset ↔ the mapping table in `reference/datasets.md` ↔ the feature page's "Related datasets" (INV-5).
- **GATE-4c evidence slots**: a control claim such as "the policy blocked it" requires before/after capture slots in the manifest. Do not generate product screenshots (only mark them as capture targets).
- **GATE-4d visuals present (INV-8)**: every scene page actually contains ≥ 1 visual (a `<Screenshot>` slot, a mermaid block, a diagram image, or `<FlowMap>`), matching the kind planned in GATE-3e. Applying the decision rule: setup/example screens → `<Screenshot>`; flow/order/whole picture → drawio/mermaid/excalidraw per `diagram-recipes.md`. A text-only scene page fails the gate. `workshop-check.sh` reports pages with zero visuals.
- **GATE-4e insight rendered (INV-9)**: `docs/start/overview.md` and every locale copy contain the overview architecture diagram and the four `<!-- arch:* -->` sections from `templates/overview.md`, filled from `03a` (services table rows == services in `02-feature-facts.md`, INV-5); every scenario index carries its architecture diagram and a why-paragraph; every scene page has the "Why these services here" table; every feature page has "Why this service". `workshop-check.sh` reports overview pages missing the diagram or a marker; the rest is checked by the persona `insight-gap` axis.
- failure: leave a missing slot/data as unresolved in the manifest and re-check in QA.

### 5 Assembly
- reads: `docs/**`, scaffold · writes: the built site, `artifacts/05-build-report.txt`
- steps: copy & substitute the skeleton with `new-workshop.sh` → wire config/nav/i18n → build.
- GATE-5: build passes + 0 dead links + 0 missing locales.
- failure: resolve every error in the build log, then rebuild.

### 6 Persona evaluation
- reads: `brief.yaml` (audience), the built site / `03` · writes: `artifacts/06-persona-review.md`
- steps: active cells of the audience matrix = finalize the persona list → parallel review (schema) → completion verdict & findings → synthesize & sort by severity → apply blocker & major → rebuild. The Architect and Decision-maker/PM cells must evaluate the `insight-gap` axis (INV-9) against the overview's architecture sections.
- **GATE-6a panel completeness**: number of active cells == number of produced reviews (INV-5). Re-run to fill any missing cell.
- **GATE-6b "all good" is void**: each persona has ≥ 2 findings + a concrete fix. An empty review is void.
- **GATE-6c clear blockers**: 0 blockers remaining after applying. Max 2 rounds; if any remain, state them as "known limitations" in the handoff.
- **GATE-6d walkthrough loop (follow, don't just read)**: personas *critique*; this gate *executes*. Loop until a clean round (max 3 rounds):
  1. a **fresh-eyes participant agent** (no prior context of this build) follows the workshop page by page in participant order and **actually executes every executable instruction** — dataset downloads exist, referenced pages/links resolve, copy-paste prompts are self-contained, setup commands are correct, the site builds, and the deploy instructions actually deploy (real when credentials and a safe target exist, otherwise dry-run and **labeled** as such). Writes `artifacts/06b-walkthrough-round-N.md` (page | severity | step followed | what happened | fix) + a completion verdict ("where would I give up?").
  2. an **author agent** applies the fixes (blockers & majors), rebuilds, and records what changed.
  3. next round re-walks **only from a fresh agent** — never the author checking its own fixes.
  - Pass: a round with 0 blockers and 0 majors. Leftovers after round 3 → "known limitations" in the handoff.
  - **Deterministic enforcement:** the walker is the plugin agent `aws-workshop-studio:participant-walker` (read-only tools; a NEW instance per round). Each round artifact **must end with the machine-checked marker** `WALKTHROUGH_RESULT: CLEAN` or `WALKTHROUGH_RESULT: blockers=<n> majors=<n> minors=<n>`. `scripts/gate.sh 7` hard-blocks QA until the latest round is CLEAN, and `workshop-check.sh` (Stop hook) warns whenever scenario content exists without a clean round.
- failure: a failed cell is re-run alone per INV-3.

### 7 QA gate
- reads: everything · writes: `artifacts/07-qa-report.md`
- steps: `workshop-check.sh` (assets, datasets, presenter notes, flows) + build.
- GATE-7: all 4 axes pass + no presenter-only wording in `docs/` + unresolved image slots listed.
- failure: fix the obvious ones; report the ones needing judgment to the SA.

### 8 Handoff
- reads: everything · writes: `artifacts/08-handoff.md`
- steps: image capture manifest · presenter notes pointer · Amplify deployment guide · remaining needs-check / known limitations.
- GATE-8: capture manifest complete + pre-deploy re-verification items (region tables, etc.) stated.

## 2. MANIFEST

`artifacts/MANIFEST.md` indexes the status of the 8 stages (✅/⬜/★pending) and whether each gate passed. In staged mode it stops at a ★pending.
