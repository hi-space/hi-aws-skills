# aws-workshop-studio

*[한국어 가이드](./README.md)*

A hi-aws-skills fork of [netsgo0319/workshop-scaffold](https://github.com/netsgo0319/workshop-scaffold) 0.2.6. Skill, command and agent names are unchanged; only the plugin is named `aws-workshop-studio`. Full change list in [UPSTREAM.md](UPSTREAM.md), attribution in [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

What differs from upstream

| Area | aws-workshop-studio |
|---|---|
| Why this architecture (INV-9) | Adds an **insight layer** to a pipeline that only taught procedure. The blueprint stage writes `artifacts/03a-architecture-rationale.md` (problem, chosen architecture, decisions with alternatives and trade-offs, per-service role and value, before/after, one insight sentence per scene); generation is blocked without it (GATE-3f) |
| Overview page | `start/overview.md` carries the overview architecture diagram plus "Why this architecture", "What each service does here, and why it is worth it" and "Before and after". `workshop-check.sh` flags a missing diagram or section marker (GATE-4e) |
| Scene and feature pages | Every scene has a "Why these services here" table (without it / what you gain); every feature page has a "Why this service" section |
| Persona review | New `insight-gap` axis: the Architect and Decision-maker personas must be able to answer "so why should we adopt this?" from the site alone |
| Architecture diagrams | Instead of hand-written drawio XML, delegate to hi-aws-skills' **`aws-diagram-design`** (PNG/SVG for pages) or **`aws-drawio-diagram`** (editable source). One overview architecture diagram plus one per scenario are mandatory |
| Honesty of value claims | Every value claim carries a confidence label, figures only when verified/documented, and the comparison baseline is the customer's current way of working, not competitors |

A Claude Code skill that turns a **topic + scenarios + target customer** into a complete hands-on AWS workshop, in the proven quick-\* VitePress format. It generates the feature catalog, scenario labs, sample datasets, AWS architecture diagrams, image slots, and customer co-branding — then a **level×role persona panel** reads it and produces concrete improvements.

Instead of building a workshop from scratch every time, you fill a validated skeleton. It's self-contained: **with only this skill installed, someone starting from nothing can build and deploy a workshop end to end.**

---

## Demo

[![Demo — the pipeline drawing diagrams and pages](https://img.youtube.com/vi/3aEmSaqTq44/maxresdefault.jpg)](https://youtu.be/3aEmSaqTq44)

*Click to watch — the skill generating a workshop live: mermaid flows, AWS architecture diagrams, scenario pages.*

**Live sample workshop** built with this skill: **https://sample-workshop.yejinkm.people.aws.dev/**

---

## What you get

One run produces, in a target folder:

- **A VitePress site** — home, agenda, feature catalog, and per-scenario lab pages. Preview with `npm run docs:dev`; build and deploy the static output.
- **Sample datasets** — realistic data that satisfies the scenario logic (+ locale copies if requested).
- **Architecture / flow diagrams** — drawn with official AWS icons.
- **Image slots** — every screenshot/logo that isn't in yet is left as a labeled placeholder, and the capture manifest lists exactly what to shoot.
- **`brief.yaml`** — the single source of truth for this workshop's fixed values (customer, size, date, roles, scenarios, tech level…).
- **`artifacts/`** — the intermediate output of each stage (research facts, blueprint, persona reviews), so decisions are traceable.

---

## Requirements

- **Claude Code** — the environment this skill runs in.
- **Node.js 18+** — to preview and build the generated VitePress site.
- **AWS credentials** — only if you deploy (e.g. to AWS Amplify).

---

## Install

Install from the hi-aws-skills marketplace:

```
/plugin marketplace add hi-space/hi-aws-skills
/plugin install aws-workshop-studio@hi-aws-skills
/reload-plugins
```

If the upstream `workshop-scaffold@workshop-scaffold-marketplace` is also enabled, both compete for the same triggers; keep one.

You get three skills — `workshop-scaffold` (the full pipeline), `aws-fact-check` (standalone GA/region/label verification), `persona-review` (standalone level×role panel review) — three commands (`/aws-workshop-studio:new-workshop`, `/aws-workshop-studio:workshop-check`, `/aws-workshop-studio:workshop-walkthrough`) and the agent `aws-workshop-studio:participant-walker`.

**Or from a local clone** (air-gapped / for development):

```bash
git clone https://github.com/hi-space/hi-aws-skills.git
claude plugin marketplace add ./hi-aws-skills
claude plugin install aws-workshop-studio
```

After installing, run `/reload-plugins` in a running session (or restart Claude Code). The skills read `references/`, `scripts/` and `assets/` from the plugin root, so symlinking a single `skills/<name>` directory (as the other hi-aws-skills plugins allow) does not work here; install it as a plugin.

---

## What's inside

**Skills** — what you invoke in chat:

| Skill | What it does |
|---|---|
| `workshop-scaffold` | **The one you run** — the full 8-stage pipeline below |
| `aws-fact-check` | Standalone: verify GA / region / exact feature names, every claim confidence-labeled |
| `persona-review` | Standalone: level×role persona panel on any doc, deck, or site |

**Commands** — deterministic entry points:

| Command | What it does |
|---|---|
| `/aws-workshop-studio:workshop-walkthrough` | Participant↔author fix loop — the only way to clear the QA gate |
| `/aws-workshop-studio:workshop-check` | Mechanical QA (5 axes) + participant-flow review |
| `/aws-workshop-studio:new-workshop` | Copy the skeleton + substitute branding tokens (the pipeline runs the underlying `scripts/new-workshop.sh` itself during Assemble) |

**Agent:**

- `participant-walker` — a fresh-eyes participant: browser-walks the deployed site (Chrome CDP), executes every executable step, and labels each check **executed / inspected / untestable-here**. A new instance every round — never the author checking its own fixes.

**Enforcement shipped into every generated workshop** — hooks and gates, not prose:

- **Stop hook** → `workshop-check.sh --fix` runs after every turn (datasets, presenter notes, emoji, assets, visual-first)
- **PreToolUse hook** → `protect-brief.mjs` blocks editing `brief.yaml` after intake — changes go through `artifacts/00-amendments.md`
- **`scripts/gate.sh <stage>`** → hard-blocks any stage whose prerequisite artifact is missing, and blocks QA until a walkthrough round ends `WALKTHROUGH_RESULT: CLEAN`

**Assets & references** — what the pipeline builds from:

- `assets/scaffold/` — the working VitePress skeleton (theme, components, hooks preinstalled)
- `assets/workshop-pipeline.workflow.mjs` — the same pipeline as a multi-agent Workflow
- `references/` — the contracts: format-spec · component-api · research-discipline · diagram-recipes · persona-rubric · branding · pipeline-contract · templates/
- `assets/brief.example.yaml` (input example) · `examples/hanbitpay/` (a real run's intermediate artifacts)

---

## Quick start (from nothing)

```bash
# 1. Install once, then run /reload-plugins in Claude Code (or restart it)
claude plugin marketplace add hi-space/hi-aws-skills
claude plugin install aws-workshop-studio

# 2. In a new empty folder, start Claude Code and run the skill
mkdir my-workshop && cd my-workshop && claude
```

```
/aws-workshop-studio:workshop-scaffold   # or just: "build a workshop about … for …"
```

That's all — the skill scaffolds the folder itself (it runs `scripts/new-workshop.sh` internally during Assemble), asks the intake questions, then generates and verifies the content stage by stage.

---

## Usage

Create an **empty folder** for the new workshop, start Claude Code in it, then:

```
/aws-workshop-studio:workshop-scaffold
```

Natural language works too: `"build a workshop about Claude Code on Bedrock for a food-manufacturing customer."`

The skill asks for the values that get frozen into `brief.yaml`:

| Prompted for | Example |
|---|---|
| Topic · target AWS services | "Claude Code on Bedrock", "AgentCore" |
| Audience (level × role) | L200 developer, L300 architect … |
| Scenario count · titles | 3: personal productivity / data analysis / external integration |
| Duration · format | 4.5h · hands-on / booth / presenter-led |
| Languages | ko / en / ja |
| Customer | name · logo · industry · tech level |
| Run mode | `staged` (default) or `oneshot` |

See [`assets/brief.example.yaml`](assets/brief.example.yaml) for the input shape and [`examples/hanbitpay/`](examples/hanbitpay/) for a real run's intermediate artifacts.

---

## What it does, in order (the pipeline)

Every run walks these 8 stages. In `staged` mode it **pauses at ★ for your sign-off**.

| # | Stage | What the skill does for you | Output |
|---|---|---|---|
| 1 | **Intake** | Asks for everything up front: topic, audience (level×role), scenarios, duration, format, languages — plus the **customer logo & favicon files** and **design preferences** (colors/mood; `auto` = derived from brand + service + persona) | `brief.yaml` (frozen SSOT) |
| 2 | **Research ★** | **Parallel research cells** — the company, the audience's actual roles, and each AWS technology (GA/region/preview verified fresh, confidence-labeled) | `02-feature-facts.md`, `02a/02b` context |
| 3 | **Blueprint ★** | Scenario arc & scene decomposition with **difficulty leveling** (adjacent scenes jump ≤1 level, ≤2 new concepts per scene), feature↔scene mapping, a planned visual per scene, dataset & diagram requirements | `03-blueprint.md` |
| 4 | **Generate** | **Feature catalog** (one page per feature), **scenario lab pages with copy-paste-ready prompts & code samples**, **realistic datasets** that satisfy the scene logic, **diagrams** (mermaid flows, drawio AWS-icon architecture), screenshot slots | `docs/**`, `demo_datasets/**` |
| 5 | **Assemble** | Wires VitePress config/nav/i18n, builds clean (0 dead links) | built site |
| 6 | **Review** | Two-layer review: a **level×role persona panel** critiques it, then a **fresh-eyes participant agent actually follows it** (runs steps, checks links/datasets/build/deploy) and an author agent fixes what it hits — looping until a clean round | `06-persona-review.md`, `06b-walkthrough-*` |
| 7 | **QA** | Mechanical checks (datasets, presenter notes, emoji, assets, visual-first) + build — QA is hard-blocked until the walkthrough is clean | `07-qa-report.md` |
| 8 | **Handoff** | Screenshot capture list, presenter notes pointer, deploy steps, human rehearsal checklist & known limitations | `08-handoff.md` |

**Two run modes**
- `staged` (default): stop at the Research and Blueprint ★ gates for human review. Recommended for first-time or high-stakes workshops.
- `oneshot`: run straight through, still checking the same pass conditions and stopping on violation.

**As a workflow (optional):** [`assets/workshop-pipeline.workflow.mjs`](assets/workshop-pipeline.workflow.mjs) encodes the pipeline as a multi-agent Workflow (parallel research/generation/persona cells) for maximum parallelism. It requires opting into workflow orchestration and honors the same gates.

---

## Rules the skill keeps (so you can trust the output)

To protect the credibility of what it produces, the skill deliberately **won't** do some things:

- **It never AI-generates a product screenshot.** Screenshot spots stay as "capture this here" slots — you fill them with the real screen on the day.
- **Architecture / flow diagrams use official AWS icons only.**
- **Customer logos/names are only for a genuine customer workshop's co-branding.** No fabricated testimonials, fake quotes, or unapproved logos.
- **AWS facts are verified fresh, not from memory.** Region availability and GA/preview are re-checked at run time, and what was verified vs. read in docs vs. assumed is kept as an explicit **label**.
- **Presenter-only content** (demo tips) stays in `PRESENTER_NOTES.md`, outside the deployed `docs/`.

The generated site's base theme follows [`references/format-spec.md`](references/format-spec.md) (e.g. the nav bar is opaque and pinned to the top).

---

## Troubleshooting

- **The skill isn't picked up** → `claude plugin list` should show `aws-workshop-studio` enabled; run `/reload-plugins` (or restart Claude Code).
- **The build fails** → in the generated folder, `npm ci` then `npm run docs:build`. Check you're on Node 18+.
- **AWS info looks stale** → region/GA facts are point-in-time. Before deploying, re-check the labels and `confirmed_date` in `artifacts/`.
