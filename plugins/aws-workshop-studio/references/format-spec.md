# quick-* workshop format spec

The skeleton extracted from `ai-passport` and `media-briefing`. Generated output must follow this structure to pass the QA gates.

## Directory

```
docs/
  start/       overview.md, setup.md            # overview = purpose + architecture diagram + why/value/before-after (template: overview.md); setup = environment prep
  features/    {id}.md …                         # one feature = one file (template: feature.md)
  scenario-{x}/ index.md, scene1..N.md           # hands-on labs (template: scene.md). x is a, b, … for N of them
  reference/   datasets.md, demo-guide.md, tips.md
  public/images/   screenshot / icon / logo slots
  .vitepress/  config.mts + data/{features,flows}.ts + theme/components
demo_datasets/  scenario_{x}/…  (+ _en/_ja locale copies)
PRESENTER_NOTES.md   # outside docs = not deployed
scripts/workshop-check.sh
amplify.yml
```

## Data files (SSOT)

- `.vitepress/data/features.ts` — feature metadata (id, name, icon, scenario, scenes). The single source of truth for feature pages, `<FeatureMeta>`, and `<FeatureLinks>`.
- `.vitepress/data/flows.ts` — the feature connections per scenario (FlowMap). Scene↔feature mapping.
- When you add a feature or scene, update these two files and the nav (config.mts) together — skip it and QA catches you.

## Theme components & containers (details in component-api.md)

`<FeatureMeta>` `<Screenshot src alt caption>` `<FeatureLinks ids>` `<FlowMap>` · `::: prompt` `::: warning` `::: talk` `::: tip`.
`<Screenshot>` = an image slot. The `src` may point to a path that does not exist yet → the capture manifest collects it.

## Theme CSS baseline (required rules in `theme/custom.css`)

The default VitePress navbar is semi-transparent, so content behind it shows through on scroll, and when a sidebar is present only the logo area inherits the sidebar color (`--vp-c-bg-alt`), splitting the header into two colors left and right and making it look flat. **Include the following by default in the `custom.css` of every generated workshop** — it fills the header with an opaque background plus a bottom border and pins it to the top (shared across light/dark; because it uses the `--vp-c-bg` token, dark mode adapts automatically). Brand color tokens layer on top of this.

```css
/* Header (navbar): opaque background + pinned to top — prevents transparency and the left/right color split */
.VPNav { position: fixed; top: 0; left: 0; right: 0; z-index: var(--vp-z-index-nav); background-color: var(--vp-c-bg); }
.VPNavBar { background-color: var(--vp-c-bg) !important; border-bottom: 1px solid var(--vp-c-divider); }
.VPNavBar.has-sidebar .content { background-color: transparent; }  /* prevent the right side from going transparent */
.VPNavBar .title { background-color: transparent; }                /* remove the gray from the logo area → unify its color with the right side */
```

The default VitePress layout already reserves top padding on the body equal to the navbar height, so `position: fixed` does not cover content. If a given theme overlaps, correct it with `.VPContent { padding-top: var(--vp-nav-height); }`.

## i18n

Three locales: `ko` (default), `en`, `ja`. Mirrored under `docs/en/` and `docs/ja/`, with dataset copies under `demo_datasets_en/` and `_ja/`. Add or remove locales via `languages` in brief.yaml.

## Invariants (enforced by QA)

- **Attribution on every page**: the theme's `layout-bottom` slot renders "Built with [workshop-scaffold](https://github.com/netsgo0319/workshop-scaffold)" on all pages (theme/index.ts + `.built-with` CSS). Ships in the scaffold — do not remove or hide it during generation or review fixes.

- **Visual-first (INV-8)**: every scene page contains ≥ 1 visual — a `<Screenshot>` slot for setup/example screens, a drawio/mermaid/excalidraw diagram for flows and whole-picture views, or `<FlowMap>` for the scene→feature chain. Text-only scene pages fail GATE-4d and are flagged by `workshop-check.sh`.
- **Why before how (INV-9)**: `start/overview.md` (every locale) carries the overview architecture diagram under `<!-- arch:diagram -->` and the `<!-- arch:why -->`, `<!-- arch:services -->`, `<!-- arch:adoption -->` sections filled from `artifacts/03a-architecture-rationale.md`; scene pages carry "Why these services here", feature pages "Why this service". `workshop-check.sh` flags overview pages missing the diagram or a marker (GATE-4e).
- Presenter-only wording lives only in `PRESENTER_NOTES.md`, never inside `docs/`.
- Datasets match in three places: the download ZIP / the mapping table in `reference/datasets.md` / the "Related datasets" section of the feature page.
- Spell out abbreviations on first appearance. No unsupported figures or definitive claims about competitors.
- The feature connections and scene composition for scenarios A/B are consistent across pages.

## Build & deploy

VitePress. `npm run dev` (local) · `npm run build`. The dataset ZIPs are regenerated automatically in the Amplify build. Push to main → Amplify auto-deploys.
