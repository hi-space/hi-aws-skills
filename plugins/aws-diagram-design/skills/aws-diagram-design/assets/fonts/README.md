# Amazon Ember — bundled fonts

Amazon Ember (and Amazon Ember Mono) as distributed by Amazon at
<https://developer.amazon.com/en-US/alexa/branding/echo-guidelines/identity-guidelines/typography>
(`Amazon_Typefaces_Complete_Font_Set_Mar2020.zip`). Usage terms:
[`Amazon-Ember-Licensing-Guidelines.pdf`](Amazon-Ember-Licensing-Guidelines.pdf) in this directory.

## Inventory

| File (woff2/) | Family | Weight / style |
|---|---|---|
| `AmazonEmber_W_Lt.woff2` | Amazon Ember | 300 |
| `AmazonEmber_W_Rg.woff2` | Amazon Ember | 400 |
| `AmazonEmber_W_RgIt.woff2` | Amazon Ember | 400 italic |
| `AmazonEmber_W_SBd.woff2` | Amazon Ember | 600 |
| `AmazonEmber_W_Bd.woff2` | Amazon Ember | 700 |
| `AmazonEmber_W_He.woff2` | Amazon Ember | 800 |
| `AmazonEmberMono_W_Rg.woff2` | Amazon Ember Mono | 400 |
| `AmazonEmberMono_W_Bd.woff2` | Amazon Ember Mono | 700 |

`ttf/` carries the desktop faces (Ember Lt/Rg/RgIt/Medium/Bd/He + Ember Mono Rg/Bd) for OS installation via
`./install.sh fonts` (repo root).

## Canonical @font-face faces (what finalize.py embeds)

Every `assets/template*.svg` already carries this block, `local()`-only — no `url()` source,
because a standalone deliverable SVG must never reference an external or relative file
(`self_check.py` rejects any `url()` that isn't a `data:` URI). `scripts/finalize.py` reads
the used faces from this inventory and rewrites each rule's `src` to an embedded `data:font/woff2`
URI before the SVG ships (see `references/style-guide.md § Font stack`):

```css
@font-face { font-family: 'Amazon Ember'; font-weight: 300; font-style: normal;
  src: local('Amazon Ember Light'), local('Amazon Ember'); }
@font-face { font-family: 'Amazon Ember'; font-weight: 400; font-style: normal;
  src: local('Amazon Ember'); }
@font-face { font-family: 'Amazon Ember'; font-weight: 400; font-style: italic;
  src: local('Amazon Ember Italic'), local('Amazon Ember'); }
@font-face { font-family: 'Amazon Ember'; font-weight: 600; font-style: normal;
  src: local('Amazon Ember Medium'), local('Amazon Ember'); }
@font-face { font-family: 'Amazon Ember'; font-weight: 700; font-style: normal;
  src: local('Amazon Ember Bold'), local('Amazon Ember'); }
@font-face { font-family: 'Amazon Ember'; font-weight: 800; font-style: normal;
  src: local('Amazon Ember Heavy'), local('Amazon Ember'); }
@font-face { font-family: 'Amazon Ember Mono'; font-weight: 400; font-style: normal;
  src: local('Amazon Ember Mono'); }
@font-face { font-family: 'Amazon Ember Mono'; font-weight: 700; font-style: normal;
  src: local('Amazon Ember Mono Bold'), local('Amazon Ember Mono'); }
```

`local()` first — a machine with the fonts installed never fetches the files. Always keep the
fallback stacks on `font-family` declarations (`'Helvetica Neue', Helvetica, Arial, sans-serif`
for Ember; `ui-monospace, monospace` for Ember Mono); environments that block file fonts
(e.g., GitHub's SVG sandbox) fall back to system faces. Ember Mono ships 400/700 — mono specs
at 500/600 snap to the nearest weight. No external font CDN is needed anywhere. Never hand-add
a `url('...')` source to an SVG yourself — `finalize.py` is the only thing that embeds fonts.
