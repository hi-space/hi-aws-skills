# Template · hands-on scene (scenario-{x}/scene{n}.md)

One scene of a story-style hands-on lab. The participant follows along and flows naturally into the next scene. Real example: `ai-passport docs/scenario-a/scene1.md`.

```md
# Scene {{n}} · {{scene title}}

<FeatureMeta scenario="{{A}}" scenes="{{Scene 1 · slide 3}}" icon="{{icon key}}" />

> {{1–2 sentences of narrative that open the scene. The situation the user is in.}}

{{1–2 sentences on what happens. Link related features with [link](/features/{{id}}).}}

<Screenshot src="/images/{{scenario_a}}/{{scene1}}.png" alt="{{screen}}" caption="{{caption}}" />

## What happens

| Feature | Behavior |
|------|------|
| **{{feature}}** | {{what it does in this scene}} |

## How it flows

{{The order the participant actually clicks/types. State the transition into the next scene.}}
→ Continues to [Scene {{n+1}}](./scene{{n+1}}).

## Why these services here

| Service | What it does in this scene | Without it | What you gain |
|------|------|------|------|
| **{{service}}** | {{one clause}} | {{the manual step, risk, or gap the participant would face}} | {{the concrete change, in the participant's words}} |

> {{One sentence the participant should be able to say after this scene — from `03a-architecture-rationale.md` §6.}} See the whole picture in [the architecture overview](/start/overview#architecture).

## Features in this scene

<FeatureLinks ids="{{a-01-xxx,a-02-yyy}}" />

## Key points

::: talk
- "{{presenter line — the message of this scene}}"
:::

## Related datasets

- `{{scenario_a/xxx.csv}}` — {{role}}
```

## Fill-in rules

- A scene maps to **a single use_case** (brief.yaml). Have the whole arc cover the use_cases.
- Every feature in the `What happens` table must have a page under features/ and match `<FeatureLinks ids>`.
- **No difficulty jump between adjacent scenes** (a deduction axis in the persona evaluation).
- Always state the transition into the next scene — so the story does not break.
- **Why before how (INV-9).** The "Why these services here" table is mandatory: one row per service the scene exercises, the "Without it" column names the real manual step or risk, the "What you gain" column is concrete. Copy the sentences from `03a-architecture-rationale.md`; never invent figures.
