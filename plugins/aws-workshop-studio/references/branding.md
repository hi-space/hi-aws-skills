# Customer customization & branding conventions

The customer information from intake drives both the **scenario framing** and the **visuals** at once.

## brief.yaml customer block

```yaml
customer:
  name: "Hanbitpay"           # co-branding on the cover, hero, and scenario intro
  logo: "assets/customer/hanbitpay.svg"   # place the original once received (text only if absent)
  industry: "easy-payment PG" # scenario domain & the character of the dataset
  tech_level: L200            # scene difficulty, explanation density, prerequisite knowledge
  use_cases:                  # material for the narrative that reads as "our story"
    - "anomaly detection over 1.8M transactions/day"
    - "SSRF response in the settlement batch"
```

## What it drives

| Field | What it drives |
|---|---|
| `tech_level` | scene difficulty, explanation density, depth of the `::: warning` pitfalls, amount of prerequisite knowledge |
| `industry` | scenario domain, realism of the dataset columns & values, industry fit of the GuardDuty/log examples |
| `use_cases` | the backbone of the scenario arc. Make each scene map to at least one use_case |
| `name`/`logo` | co-branding slots on the home hero, the scenario index intro, and the presentation cover |

## Design derivation (colors & mood)

Intake **asks** for design preferences (`design:` block in brief.yaml) — but every field accepts `auto`. When auto, derive and **label the result `derived`** (vs `given`); never present a derived palette as the customer's official one.

| Field | If SA gave it | If `auto` — derive from |
|---|---|---|
| `primary_color` | use as-is | the customer logo's dominant color (sample the actual asset), else the customer's official brand color, else the topic service's brand tone |
| `accent_color` | use as-is | a complement/analog of primary with AA contrast on both light/dark backgrounds |
| `mood` | drives copy tone, illustration style, `::: warning` depth | industry + audience: finance/enterprise → restrained & precise; consumer/food/retail → warm & friendly; developer-heavy audience → terse, code-first |
| `appearance` | use as-is | quick-* convention is `dark` default; go `light` when the customer's brand assets clearly assume light |

Rules:
- Derived values are written back into `brief.yaml`'s design block **at intake** (before it freezes) with `source: derived` — later changes go through the amendment flow like any brief value.
- The palette lands in `theme/custom.css` (`--vp-c-brand-*` + the `__THEME_COLOR__` token) — one place, never scattered inline.
- Mood keywords steer conceptual illustrations (diagram-recipes.md) and hero copy; they never justify inventing customer-brand assets.

## Icon & logo sources

- **AWS service icons**: only the official AWS Architecture Icons. Architecture diagrams come from the `aws-diagram-design` skill (or `aws-drawio-diagram` for editable sources) — see `diagram-recipes.md` §2; fall back to the drawio AWS4 set only when neither skill is installed, and use an unverified `resIcon` only after a render test.
- **Customer logo**: from the original the customer provided or from official brand assets. Keep it in `assets/customer/` and copy it into `docs/public/images/`. No low resolution, distortion, or arbitrary recoloring.

## Honesty boundaries (non-negotiable)

- The customer logo and name are limited to legitimate co-branding for **an actual customer workshop you are running**.
- **No fabrication**: customer testimonials, fake quotes, nonexistent adoption results, or use of a logo the customer has not approved.
- Demo data must not look like real customer data — state "real source vs demo substitute" in `reference/datasets.md` (the quick-* convention).
- Do not publish or post output bearing the customer logo externally (internal workshop material). Deploy to an access-controlled location.
