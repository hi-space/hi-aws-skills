# Component API — VitePress theme components

The scaffold registers these Vue components globally (see `assets/scaffold/docs/.vitepress/theme/index.ts`). Use them from any Markdown page. Text stays minimal; these components carry the visual load.

All components are locale-aware via `theme/i18n.ts` (labels adapt to `ko`/`en`/`ja`). Image/link paths are resolved with `withBase`, so write paths **from `docs/public`** (leading `/`), e.g. `/images/scenario_a/01_x.png`.

## `<Screenshot>` — the image slot

The single most important primitive: it is how an intentional, empty capture slot is expressed. If `src` does not exist yet, it renders a labeled placeholder instead of a broken image, and the build still passes.

```md
<Screenshot src="/images/scenario_a/01_briefing.png" alt="Morning briefing" caption="Scheduled run result shown in the Activity Feed" />
```

| Prop | Type | Required | Notes |
|---|---|---|---|
| `src` | string | yes | Path under `docs/public`. May point to a file that does not exist yet — renders a placeholder. |
| `alt` | string | no | Accessible label; defaults to the localized word "Screenshot". |
| `caption` | string | no | Figure caption below the image. |

**Never AI-generate a product screenshot to fill this.** Leave the slot; the capture manifest (`scripts/image-manifest.mjs`) collects every unfilled `src` so someone captures the real screen later. See GATE-4c in `pipeline-contract.md`.

## `<Video>` — video slot

Same placeholder behavior as `<Screenshot>` for `.mp4`/`.webm`.

| Prop | Type | Required | Notes |
|---|---|---|---|
| `src` | string | yes | Path under `docs/public`. |
| `poster` | string | no | Poster image. |
| `caption` | string | no | Caption. |
| `autoplay` | boolean | no | Autoplay implies muted (browser policy). |
| `loop` | boolean | no | Loop playback. |

## `<FeatureMeta>` — feature badges (feature page header)

Renders the icon + scenario badge + scene badge row at the top of a feature page.

```md
<FeatureMeta scenario="A" scenes="PRE, Scene 1, Scene 6" icon="notify" />
```

| Prop | Type | Notes |
|---|---|---|
| `scenario` | string | e.g. `A`. Drives badge color. |
| `scenes` | string | Free text, e.g. `Scene 1, Scene 6`. |
| `icon` | string | Icon key → `docs/public/images/icons/<icon>.svg` must exist. |

## `<FeatureGrid>` — feature catalog grid

Auto-renders cards for features from `data/features.ts`. No manual list needed.

```md
<FeatureGrid scenario="A" />   <!-- A only -->
<FeatureGrid />                <!-- all features -->
```

| Prop | Type | Notes |
|---|---|---|
| `scenario` | `'A' \| 'B' \| 'all'` | Omit or `all` for every feature. |

## `<FeatureLinks>` — cross-reference chips

Links to other feature pages by id. Used in scenes to point at the features they exercise.

```md
<FeatureLinks ids="a-01-schedule,a-02-activity-feed,a-03-os-notification" />
```

| Prop | Type | Notes |
|---|---|---|
| `ids` | string | Comma-separated feature ids from `data/features.ts`. Unknown ids are dropped silently — keep ids in sync. |

## `<FlowMap>` — clickable scene→feature flow

Renders the scenario's scene-by-scene feature flow as clickable chips. Reads `flowA`/`flowB` from `data/flows.ts` by scenario — you do **not** pass the flow data inline.

```md
<FlowMap scenario="A" />
```

| Prop | Type | Notes |
|---|---|---|
| `scenario` | `'A' \| 'B'` | Which flow to render. The data lives in `data/flows.ts`. |

## `<ScenarioCard>` — scenario entry card (home / index pages)

```md
<ScenarioCard
  title="A · A Day in the Life of a Category Manager"
  desc="Operational automation across one workday"
  tag="Scenario A"
  icon="proactive"
  link="/scenario-a/"
  cta="Start" />
```

| Prop | Type | Required | Notes |
|---|---|---|---|
| `title` | string | yes | |
| `link` | string | yes | Target route. |
| `desc` | string | no | One-line description. |
| `tag` | string | no | Small tag above the title. |
| `icon` | string | no | Icon key (defaults to `connect`). |
| `cta` | string | no | Call-to-action label (defaults to localized "Learn more"). |

## `<DownloadButton>` — dataset download

Points at a file, or (if `file` omitted) auto-resolves the locale's latest timestamped dataset ZIP injected at build time.

```md
<DownloadButton note="scenario_a · CSV/XLSX" />
<DownloadButton file="/downloads/extra.zip" label="Extra data" />
```

| Prop | Type | Notes |
|---|---|---|
| `file` | string | Explicit path; omit to use the auto dataset ZIP for the current locale. |
| `label` | string | Button label (defaults to localized "Download"). |
| `note` | string | Sub-label under the button. |

## `<Checklist>` — persistent setup checklist

Interactive checklist whose state persists in the reader's browser (`localStorage`). Ideal for `start/setup.md`.

```md
<Checklist :items="[
  'AWS account access confirmed',
  'Bedrock model access enabled in region',
  'Sample dataset downloaded',
]" id="setup" />
```

| Prop | Type | Notes |
|---|---|---|
| `items` | string[] | Checklist items. |
| `id` | string | Storage key so multiple checklists don't collide. |

## Markdown containers (callouts)

Defined in `config.mts` via `markdown-it-container`:

```md
::: prompt
Paste this into the app:
> Summarize yesterday's category performance and flag anomalies.
:::

::: talk
Key point the presenter should land here.
:::
```

- `::: prompt` — the exact prompt a participant types/pastes. Default title localizes to "Prompt".
- `::: talk` — key point / talking note that IS meant for participants (unlike presenter-only content, which goes in `PRESENTER_NOTES.md`).
- `::: tip` / `::: warning` / `::: details` — standard VitePress containers; use `warning` for the "gotcha" traps whose depth scales with `tech_level`.

## Keeping data in sync (enforced by QA)

`data/features.ts` and `data/flows.ts` are the single source of truth. When you add a feature or scene you must update **both** files and the nav in `config.mts`. `scripts/workshop-check.sh` and the persona/QA gates fail on drift (INV-5 in `pipeline-contract.md`): the ids referenced by `<FeatureLinks>`/`<FlowMap>` must exist in `features.ts`, and every `icon` key must have a matching `docs/public/images/icons/<key>.svg`.
