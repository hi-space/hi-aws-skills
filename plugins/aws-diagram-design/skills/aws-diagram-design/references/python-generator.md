# Programmatic generation — `scripts/pygen/`

Python generator that bakes the skill's mandatory rules into code. A spec supplies layout coordinates and
text; the library paints everything else the way SKILL.md §5–§7 prescribe. Load this file when the user
wants **many diagrams in one house style**, a **ko/en pair from one layout**, **repeatable rebuilds** when
content changes, or **PNG deliverables for docs** (Workshop Studio, Hugo, MkDocs, wikis) instead of a
one-off HTML page.

Hand-written SVG (SKILL.md §10) still wins for a single hero diagram or the types the library does not model
(radar, Venn, Gantt, charts). The generator covers block-style types: architecture, data flow, process, flowchart
(decision diamonds), sequence (lifelines), layers, nested zones.

## Workflow

```
python3 <skill>/scripts/pygen/awsdiag.py                                   # 1. catalogue: node/zone kinds, icon names
cp <skill>/scripts/pygen/spec_example.py docs/diagrams/spec_<group>.py     # 2. start from the working example
python3 <skill>/scripts/pygen/build.py docs/diagrams --out docs/diagrams/out --strict          # 3. HTML; fails on overflow
python3 <skill>/scripts/self_check.py docs/diagrams/out/<slug>-ko.html                        # 4. verify one language
python3 <skill>/scripts/verify-geometry.py docs/diagrams/out/<slug>-ko.html
python3 <skill>/scripts/pygen/export.py docs/diagrams/out --png-dir static/images/diagrams   # 5. PNG @2x
```

`<skill>` is this skill's directory (plugin cache path, `~/.claude/skills/aws-diagram-design`, or a clone).
`build.py` puts `scripts/pygen` on `sys.path`, so specs import with `from awsdiag import Canvas, T`.
Embed the PNG in the doc and delete the Mermaid source it replaces. Open the PNG and read every label before
declaring done; a diagram that needs zooming has too much text.

Spec contract:

```python
from awsdiag import Canvas, T
def build(lang):                       # called once per language in --langs (default ko,en)
    t = lambda ko, en: T(lang, ko, en)
    c = Canvas(960, 464, "slug", t("제목", "Title"), t("한 문장 설명", "One sentence"), lang)
    ...
    return [("slug", c)]               # several diagrams per spec are fine
```

## Layout recipe

Every diagram is built the same way. Follow the steps in order; the numbers are on the 4px grid.

1. **Canvas.** Width 960 for body-width docs, 1280 for wide pages or slides. Height = content + 40 top margin +
   56 legend strip; keep the lowest node or zone edge at or above `h - 60`.
2. **Columns and rows.** Nodes sit on a grid: column x starts at 40, node widths from the table below, gaps of 64–96
   between columns (room for a labelled arrow), 40–72 between rows. Put the primary flow left→right (or top→bottom)
   and side services (registry, storage, monitoring) on a second row or column, never floating in a corner.
3. **Node sizes.** Pick from the table; `awsdiag.min_node_w(name, sub, icon=True, h=64)` returns the minimum width
   for a given text. Design for the longer language, then use the same box for both.

   | Content | w × h | Icon |
   |---|---|---|
   | name + sublabel, AWS service | 240 × 64 (up to 280 for long names) | 32px |
   | name + sublabel, short | 184 × 56 | 24px |
   | name only | 160 × 48 | 24px |
   | compact step in a row of 5+ | 144 × 48, no sublabel | 24px |
   | actor / user | 184 × 64, `kind="input"`, icon `User` or `Users` | 32px |

4. **Zones.** `kind` chooses the official group badge: `cloud` (AWS Cloud, the outermost box only), `account`,
   `region` (dashed), `vpc`, `public` / `private` subnet, `ec2` (instance contents), `greengrass`, `server`,
   `corporate` (on-prem), `autoscaling`. A *service* or a *cluster* is not a group: draw EKS, CloudFront, or a
   team as `kind="generic"` with `icon="EKS"` in the eyebrow, or as a node. Zone padding: 40px top (badge row),
   24px sides and bottom.
5. **Arrows attach to edges.** Compute endpoints from the nodes, never by eye: right edge `(x + w, y + h/2)`, left
   edge `(x, y + h/2)`, bottom `(x + w/2, y + h)`, top `(x + w/2, y)`. Two arrows on one edge sit ≥12px apart
   (`y + h/3`, `y + 2h/3`). Paths: `hline`/`vline` when endpoints share an axis, `L_hv`/`L_vh` for one bend,
   `elbow_hvh`/`elbow_vhv` for two bends with `mid=` pinning the middle leg so parallel connectors stay ≥12px apart.
   An arrow never stops in open canvas and never crosses a node that is not its endpoint.
6. **Labels.** Horizontal segment at `Y`: `c.label(mid_x, Y - 12, "READ")`. Vertical segment at `X`:
   `c.label(X + 16, mid_y, "PULL", anchor="start")`. Labels are ≤14 characters, uppercase for verbs, mono, and sit on
   a straight run that clears both boxes by ≥8px; a mask that overlaps a node is clipped by the node fill.
7. **Focal.** `kind="focal"` on 1–2 nodes. Everything else `step` (default), `store`, `input`, `external`, `optional`,
   `security`.
8. **Legend.** One entry per node kind and arrow style actually used, nothing else. Keys: a node kind, `arrow`,
   `arrow:accent`, `arrow:link`, `arrow-dashed`, `arrow:link-dashed`, or an icon name.

## API (Canvas)

| Call | Draws | Notes |
|---|---|---|
| `zone(x,y,w,h,label,kind="generic",icon=None)` | Group container | `kind` from step 4; unknown kind raises |
| `node(x,y,w,h,name,sub=None,icon=None,kind="step",tag=None)` | Block node | `name` may be a 2-item list for two lines; `tag` is a 10px eyebrow (module number), no width check |
| `stack(x,y,w,h,name,...,depth=2)` | Node with ghost outlines | Replicas, workers |
| `decision(cx,cy,w,h,text)` | Flowchart diamond | |
| `lifeline(x,y1,y2)` | Sequence lifeline | Pair with `hline` messages + `label` |
| `path(d,style="default",dashed=False,head=True)` | Connector | `style`: `default` `accent` `link` `soft`; dashed = optional / async / return |
| `hline(x1,y,x2)` `vline(x,y1,y2)` `L_hv` `L_vh` `elbow_hvh(x1,y1,x2,y2,mid=)` `elbow_vhv(...)` | Path strings | All orthogonal, r=8 arcs |
| `label(x,y,text,*,anchor="middle")` | Arrow label on an opaque mask | `y` is the baseline; `size=`/`color=` keyword-only; `\n` for two lines |
| `note(x,y,text,anchor="middle")` | Mono annotation above nodes | |
| `legend([(key,text), ...])` | Bottom strip | See step 8 |
| `html()` / `svg()` | Output | `html(kr_webfont=False)` for offline builds (drops the Noto Sans KR link; arrows/Hangul use installed fallbacks) |

Icon names: `icon=` accepts an alias from `awsdiag.AWS` (`S3`, `EKS`, `SageMaker`, `User`, …), any file stem from
`assets/aws-icons/INDEX.md` (`Amazon-Route-53`, `Res_Amazon-EC2_Instance_48`), or a generic monochrome name from
`references/primitive-icons.md` (`robot`, `python`, `docker`, `kubernetes`, `file`). `python3 awsdiag.py` prints all
three lists. An unknown name raises `KeyError` with the same hint. Paint order is fixed (zones → arrows → labels →
nodes → overlay → legend), so spec statement order does not matter.

## Rules the library enforces, and what the spec still decides

Baked in (plus the layout checks listed under WARN policy): white paper, squid-ink `#232F3E`, smile-orange accent tint/stroke for `focal`, Amazon Ember with Noto Sans
KR / NanumBarunGothic fallback for Hangul, presentation type ramp (name 16 · sublabel 12 · arrow label 12 · zone 14 ·
tag 10), icon-left pattern (32px icon in a ≥64px node, 24px in ≥48px, 16px below), opaque node mask, four arrow
markers, accessible `<title>`/`<desc>` with slug-prefixed ids, transparent-background PNG at 2x.

The spec owns the text budget: one name line (or two via a list) plus one short sublabel. Parameters, lists, and
caveats go in the document prose or a table, not in the box. Keep AWS service names in English in both languages.

**WARN policy.** `build.py` prints one `WARN` line per violation and, with `--strict`, exits 1. Zero WARNs before
export. Two families:

- `WARN name|sub [slug-lang] '<text>' needs w>=N`: a label wider than its box. Widen to the printed width, shorten
  the text, or drop the sublabel. The estimate has no font metrics, so a mono sublabel flagged by ≤10px may render
  fine; confirm on the PNG rather than assuming.
- `WARN layout [slug-lang] ...` from `Canvas.check()`: two nodes overlap; a node straddles a zone border; a node sits
  on a zone's badge row (`y < zone.y + 36`); a node or zone runs into the legend strip (`> h - 60`); an arrow endpoint
  touches nothing (no node edge, zone edge, lifeline, or other connector). Each message names the element and the
  coordinate to change.

## Common mistakes

| Symptom | Fix |
|---|---|
| Label text clipped to a fragment on a node border | Mask overlapped the node; move the label to the straight run outside the box or lengthen the arrow |
| Arrow ends in empty space or starts inside a box | Endpoints were guessed; compute them from node geometry (step 5) |
| AWS Cloud badge on a service box | `cloud` is the outer boundary only; a service or cluster is a `generic` zone with `icon=` or a node |
| Korean renders as boxes / fallback serif | Offline build without Noto Sans KR and no Nanum font installed; install NanumBarunGothic or build with network |
| `KeyError: unknown AWS icon` | Run `python3 awsdiag.py` for the alias list, or use a stem from `assets/aws-icons/INDEX.md` |
| `TypeError` on `label(...)` | `anchor`, `size`, `color` are keyword-only: `label(x, y, "TEXT", anchor="start")` |
| Two arrows merge into one stroke | Different `mid=` for each `elbow_*`, or fan the attach points along the edge |
| PNG looks like Helvetica | Amazon Ember woff2 not reachable; the `file://` path in the HTML must reach `<skill>/assets/fonts/woff2` |
| Legend overlaps the diagram | Increase canvas `h`; the strip is anchored at `h - 40`, content must end by `h - 60` |
| `WARN layout ... straddles zone` | Nodes are fully inside or fully outside a zone; an actor outside AWS goes left of the `cloud` zone, not on its border |
