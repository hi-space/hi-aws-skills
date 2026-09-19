# Substitution tokens

This scaffold embeds substitution tokens in the `__UPPER_SNAKE__` format.
`scripts/new-workshop.sh` replaces them (via sed) with the values you pass. If a value
is not provided, the token stays in place so you (or Claude) can fill it in later by
editing the file directly.

| Token | Meaning | Example | Default |
|-------|---------|---------|---------|
| `__WORKSHOP_NAME__` | `name` in package.json (npm package name, kebab-case) | `hanbitpay-quick-workshop` | (none, `--name`) |
| `__SITE_TITLE__` | Site title (navbar, home hero, `<title>`) | `HanbitPay Quick Workshop` | (none, `--title`) |
| `__SITE_DESCRIPTION__` | Site description (meta description, home tagline, package.json) | `Fintech ops-automation demo scenario` | (none, `--desc`) |
| `__THEME_COLOR__` | Browser theme-color meta (mobile address-bar color) | `#8b2fe8` | `#232F3E` (AWS squid ink) |

## Where the tokens appear

- `package.json` — `__WORKSHOP_NAME__`, `__SITE_DESCRIPTION__`
- `package-lock.json` — `__WORKSHOP_NAME__`
- `docs/.vitepress/config.mts` — `__SITE_TITLE__`, `__SITE_DESCRIPTION__`, `__THEME_COLOR__`
- `docs/index.md` — `__SITE_TITLE__`, `__SITE_DESCRIPTION__`

## Not tokens (fill in directly)

The feature list, flows, and scenario content are not token-substituted. Following the
blueprint, edit `docs/.vitepress/data/features.ts`, `flows.ts`, and the `docs/**` pages
directly to fill them in.
