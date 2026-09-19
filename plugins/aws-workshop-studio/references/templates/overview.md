# Template · workshop overview (start/overview.md)

The one page that tells the whole story: purpose, **the architecture and why it was chosen, what each service contributes, what changes when adopted** (INV-9), then the scenario flow. The four `<!-- arch:* -->` markers are read by `workshop-check.sh` — keep them, in this order, in every locale copy. Source for every sentence: `artifacts/03a-architecture-rationale.md`.

```md
# {{Workshop title}}

::: tip Purpose of this workshop
{{Who, what, why — one or two sentences from brief.yaml.}}
:::

## One-sentence message

> {{The single insight the participant should carry home.}}

<!-- arch:diagram -->
## Overall architecture {#architecture}

![{{Workshop}} overall architecture]({{/images/diagrams/overview-architecture.png}})

{{Two sentences: what the participant is looking at, read left to right. Name every service that appears in the diagram exactly once.}}

<!-- arch:why -->
## Why this architecture

{{Problem → choice → reason. Three to five sentences, or a three-row table Problem | Choice | Reason. State the alternative that was rejected and the trade-off accepted. Confidence labels stay visible where a claim is documented or assumed.}}

<!-- arch:services -->
## What each service does here, and why it is worth it

| Service | Role in this workshop | Why this service | What changes once adopted |
|---|---|---|---|
| {{Service}} | {{one clause}} | {{the reason it beats the alternative or the current way}} | {{the concrete delta for the team}} |

<!-- arch:adoption -->
## Before and after

| | Today ({{customer}}) | With this architecture |
|---|---|---|
| {{a concern a developer has}} | {{current state, from 02a}} | {{new state}} |
| {{a concern an architect has}} | {{...}} | {{...}} |
| {{a concern a decision-maker has}} | {{...}} | {{...}} |

## Scenario flow

{{One sentence: how the scenarios build on each other.}}

<FlowMap scenario="A" />

## How to use this guide

Each **feature page** gives you: what the feature is · what you see on screen · the exact prompt to type · **why this service** · key points · related datasets.

::: info Next
Set up your environment in [Setup](./setup), then start [Scenario A](/scenario-a/).
:::
```

## Fill-in rules

- The diagram is produced with the `aws-diagram-design` skill (official AWS icons) into `docs/public/images/diagrams/`; see `diagram-recipes.md` §2. If the export is not ready yet, use `<Screenshot src="/images/diagrams/overview-architecture.png" …/>` so the manifest tracks it — the marker check accepts either form.
- Every service in the services table appears in the diagram, and every service in `02-feature-facts.md` appears in the table (INV-5).
- No invented figures. Direction of change in words unless the number is `verified`/`documented` with a source.
- Before/after rows are keyed to the audience roles in `brief.yaml`; the "Today" column comes from `02a-company-context.md`, not from a generic strawman.
- Keep it to one screen of reading per section. Detail stays in `03a`.
