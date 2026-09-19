# Architecture rationale — stage 3 (`03a`) and the overview page (INV-9)

A workshop that only says *what to click* teaches a procedure. A workshop that also says *why this architecture, what each service contributes, and what changes once it is adopted* leaves the participant with an insight they can defend back at work. INV-9 makes the second kind mandatory. This file is the contract for it.

## Where the rationale lives

| Stage | Artifact / page | What goes there |
|---|---|---|
| 3 Blueprint | `artifacts/03a-architecture-rationale.md` | The reasoning, in full, with confidence labels. Source of truth for every "why" sentence in the site. |
| 4 Generate | `docs/start/overview.md` | The participant-facing version: overview architecture diagram, why this architecture, per-service role and value, before/after. Template: `templates/overview.md`. |
| 4 Generate | `docs/scenario-{x}/index.md` | Scenario architecture diagram + one paragraph on why this scenario needs this slice of the architecture. |
| 4 Generate | `docs/scenario-{x}/scene{n}.md` | "Why these services here" table (template `scene.md`). |
| 4 Generate | `docs/features/{id}.md` | "Why this service" section (template `feature.md`). |

The overview page is the only place the whole story is told at once. Scene and feature pages repeat only the slice they need and link back to `/start/overview#architecture`.

## `03a-architecture-rationale.md` — required sections

1. **Problem statement** — the customer's situation in one paragraph (from `02a-company-context.md`), the outcome the workshop demonstrates, and what the participant should be able to argue afterwards.
2. **Chosen architecture** — the list of AWS services actually exercised (every row in `02-feature-facts.md` appears here; cells in == rows out, INV-5) and the overview diagram plan: which diagram, drawn with what (see `diagram-recipes.md` §2), where it lands.
3. **Decisions and alternatives** — one row per architectural decision:

   | Decision | Chosen | Alternatives considered | Why chosen here | Trade-off accepted | Label |
   |---|---|---|---|---|---|

   At least one alternative per decision. "No alternative" is allowed only with a reason (for example, the customer already standardised on it).
4. **Per-service role and value** — one row per service:

   | Service | Role in this workshop | Problem it removes | Why this service (not the alternative) | What changes for the team once adopted | Label |
   |---|---|---|---|---|---|

   The last column is the insight the participant should take home. It must be concrete ("the ops team stops rotating batch credentials by hand; Identity issues scoped short-lived credentials per tool call"), not generic ("improves security").
5. **Adoption benefits** — what is different before and after, organised by the audience roles in `brief.audience.roles` (a developer, an architect, and a decision-maker each care about different deltas). Three to six rows.
6. **Insight per scene** — for every scene in `03-blueprint.md`, the one sentence the participant should be able to say after the scene ("I now know why the agent could not touch the account without approval"). This feeds the `::: talk` and "Why these services here" blocks in stage 4.

## Honesty rules (they inherit from research-discipline.md)

- Every value claim carries a confidence label. A benefit stated in AWS documentation is `documented` (cite the page). A benefit you reasoned out for this customer is `assumed` until the customer confirms it. Never promote.
- **No invented numbers.** Percentages, latency figures, cost deltas appear only when `verified` or `documented` with a source. Otherwise describe the direction of change in words.
- Competitor comparisons follow format-spec: no unsupported figures or definitive claims about competitors. Compare against *the customer's current way of doing it* instead; that is the alternative that matters.
- Region and GA caveats from `02-feature-facts.md` must survive into the rationale. A "why this service" that ignores a Seoul-availability blocker fails GATE-3f.

## Writing rules for the participant-facing version

- Lead with the problem, then the service, then the change. Problem → why this service → what changes. Never start with the service name.
- One insight per service, one sentence each. Tables, not paragraphs (visual-first, INV-8). Longer reasoning stays in `03a`.
- Use the participant's vocabulary (from `02b-audience-context.md`). An L100 decision-maker reads "the agent cannot spend money without a person approving"; an L300 architect reads "Policy gates irreversible tool calls behind a human approval step".
- The before/after table is the place a decision-maker forms an opinion. Write the "before" from the customer's actual current state (02a), not from a generic strawman.
- Presenter-only framing (objection handling, competitive talk track) goes to `PRESENTER_NOTES.md`, never to `docs/`.

## Gates that read this file

- **GATE-3f** (stage 3): `03a` exists, has all six sections, one row per service (INV-5), one alternative per decision, every claim labeled, and the overview diagram is planned in GATE-3e's list. `gate.sh 4` blocks generation without `03a`.
- **GATE-4e** (stage 4): `docs/start/overview.md` (and every locale copy) contains the architecture diagram plus the four marked sections from `templates/overview.md`; every scene page has its "Why these services here" table; every feature page has "Why this service". `workshop-check.sh` reports overview pages missing the diagram or a marker.
- **Persona axis `insight-gap`** (stage 6): the Architect and Decision-maker/PM personas must be able to answer "why this architecture and what do we gain" from the site alone.
