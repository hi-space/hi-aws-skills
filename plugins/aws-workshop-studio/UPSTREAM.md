# Upstream

- Source: https://github.com/netsgo0319/workshop-scaffold (author: yejinkm)
- Forked at: commit 50e370add8ce024380aa69b200d3e5b20640f85b (plugin version 0.2.6, 2026-09-19)
- Copied from the local marketplace clone `~/.claude/plugins/marketplaces/workshop-scaffold-marketplace`, which was at upstream `main` at the time.

## Added (0.3.0 — insight-first layer, INV-9)
- `references/architecture-rationale.md`: contract for `artifacts/03a-architecture-rationale.md` (six sections: problem, chosen architecture, decisions with alternatives, per-service role and value, adoption benefits by role, one insight per scene) and for the participant-facing rendering. Honesty rules: labeled value claims, no invented figures, baseline = customer's current way.
- `references/templates/overview.md`: overview page template with the `<!-- arch:diagram|why|services|adoption -->` markers.
- `pipeline-contract.md`: INV-9 invariant, GATE-3f (rationale present and complete), GATE-4e (rendered on overview/scenario/scene/feature pages), Architect + Decision-maker personas must run the `insight-gap` axis.
- `scripts/gate.sh` stage 4 requires `03a` and blocks on `[BLOCKER]`s in it. `scripts/workshop-check.sh` check 6 flags overview pages without a `/images/diagrams/` reference or any of the four markers.
- `references/persona-rubric.md`: `insight-gap` evaluation axis.
- Templates `scene.md` ("Why these services here" table) and `feature.md` ("Why this service" section) gain mandatory why-blocks; scaffold pages `start/overview.md`, `scenario-a/index.md`, `scenario-a/scene1..2.md` updated to match.
- `assets/workshop-pipeline.workflow.mjs`: blueprint prompt also writes `03a`; scene/feature prompts require the why-blocks; new overview-page agent.
- Tests `test_insight_first_layer_present`, `test_architecture_diagrams_delegate_to_aws_diagram_skills`.

## Changed
- `references/diagram-recipes.md` §2 and `references/branding.md`: architecture diagrams are produced with the `aws-diagram-design` skill (PNG/SVG) or `aws-drawio-diagram` (editable `.drawio`), hand-authored drawio AWS4 only as a fallback. The workshop overview architecture diagram (`docs/public/images/diagrams/overview-architecture.png`) and one per scenario are mandatory. SKILL.md stage 3/4 lines and the non-negotiable rules updated accordingly.
- Plugin version 0.2.6 → 0.3.0 (upstream base remains 0.2.6).
- `examples/hanbitpay/` predates the insight layer and has no `03a` artifact.
- Plugin renamed `workshop-scaffold` → `aws-workshop-studio` (`.claude-plugin/plugin.json`, root `plugin.json` added for parity with the other hi-aws-skills plugins). Skill (`workshop-scaffold`, `aws-fact-check`, `persona-review`), command (`new-workshop`, `workshop-check`, `workshop-walkthrough`) and agent (`participant-walker`) names are unchanged, so they now resolve under the `aws-workshop-studio:` namespace.
- Agent reference `workshop-scaffold:participant-walker` → `aws-workshop-studio:participant-walker` in `references/pipeline-contract.md`, `commands/workshop-walkthrough.md`, `assets/workshop-pipeline.workflow.mjs`.
- `README.md` (ko) / `README.en.md` (en): install instructions point at the hi-aws-skills marketplace; commands written with the plugin namespace. Upstream `README.ko.md` became `README.md`, upstream `README.md` became `README.en.md`.
- Author / repository fields point at hi-space / hi-aws-skills.

## Removed
- `.claude-plugin/marketplace.json` (the repo-level `hi-aws-skills` marketplace registers this plugin instead).

## Kept as-is
- The "Built with workshop-scaffold" attribution that every generated page renders (`assets/scaffold/docs/.vitepress/theme/index.ts`, `references/format-spec.md`) still links to the upstream repository.
- All skills, references, scripts, scaffold assets and the `examples/hanbitpay` run.
