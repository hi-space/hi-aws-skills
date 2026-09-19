# Template · one feature page (features/{id}.md)

One page of the feature catalog for a quick-* workshop. Fill in the `{{...}}`. Real example: `ai-passport docs/features/a-01-schedule.md`.

```md
# {{feature name}}

<FeatureMeta scenario="{{A}}" scenes="{{PRE, Scene 1, Scene 6}}" icon="{{icon key}}" />

> **Scenario {{A}} · {{Scene 1}}** — {{one-line context}}

## Feature description

{{What the feature is and how it works, 2–4 sentences. If there are pitfalls or constraints, here. Link related features with [link](./{{other-id}}).}}

<Screenshot src="/images/{{scenario_a}}/{{01_xxx}}.png" alt="{{what screen this shows}}" caption="{{one-line caption}}" />

## What you see on screen

| Item | Detail |
|------|------|
| Setup | {{...}} |
| Behavior | {{...}} |
| Value | {{what the user gets}} |

## Why this service

| | |
|------|------|
| Problem it removes | {{the pain in the customer's current way of working, from 02a}} |
| Why this service, not {{the alternative}} | {{one sentence; keep the confidence label if the reason rests on a documented/assumed claim}} |
| What changes once adopted | {{the concrete delta for the team — not "improves X"}} |

## Prompt to try

::: prompt {{prompt title}}
​```text
{{The prompt the participant actually types. Get the dataset path exact.}}
​```
:::

::: warning {{pitfall / required prep}}
{{Something that breaks the demo if omitted, or a common mistake}}
:::

## Talking points for this feature

::: talk
- "{{one sentence the presenter says}}"
- "{{a sentence that makes the value stick}}"
:::

## Related datasets

- `{{scenario_a/xxx.csv}}` — {{role}}
```

## Fill-in rules

- A `<Screenshot>` slot is an **actual capture target**. The src may point to a path that does not exist yet (a gap) → `image-manifest.mjs` collects it.
- The `icon` key must match an icon defined in `.vitepress/data/features.ts` (`component-api.md`).
- When `tech_level` is low, expand the feature description and reduce pitfalls. When high, the reverse.
- Minimize text — the principle is to explain with tables, prompts, and screenshots.
- **Why before how (INV-9).** "Why this service" is mandatory and comes from `03a-architecture-rationale.md` §4. Name the alternative (or the customer's current method) explicitly. No invented numbers.
