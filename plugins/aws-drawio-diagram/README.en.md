# AWS draw.io Diagram Skill (aws-drawio-diagram)

> Fork of [vidanov/aws-architecture-diagram-skill](https://github.com/vidanov/aws-architecture-diagram-skill) (MIT) maintained in [hi-aws-skills](https://github.com/hi-space/hi-aws-skills). The icon catalog is **regenerated from draw.io's own sources by script**, with a validator and SVG fallbacks for icons draw.io lacks added on top.

[한국어](README.md) | **English**

**Describe it in words, get an editable `.drawio` file.**

> "Draw a serverless API architecture with Lambda, DynamoDB, and API Gateway as a draw.io diagram"

The result is XML you can open and edit directly in draw.io (diagrams.net). Icons come from the official AWS Architecture Icons stencils built into draw.io, and every stencil name is checked against a catalog generated from draw.io's own source.

## Why icons break and how this skill prevents it

draw.io's AWS icons come in two patterns with opposite `strokeColor` rules.

| Pattern | Style | strokeColor |
|---|---|---|
| Service | `shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.<name>` | must be `#ffffff` |
| Resource | `shape=mxgraph.aws4.<name>` | must be `none` |

On top of that, stencil names don't track service renames (OpenSearch is still `elasticsearch_service`). This skill prevents the problem with (1) a catalog of 1,000+ names generated from draw.io's `Sidebar-AWS4.js` and `aws4.xml`, (2) a rename-alias table, and (3) a validator that runs automatically after generation.

## Sample

Produced with this skill. The skill works in three phases: ① an architecture brief (components, relationship table, flow, groups, AWS sanity checks), ② a grid spec (JSON) written from the brief alone and built into `.drawio` by `scripts/build_diagram.py`, which also validates it, ③ a review of the rendered PNG against the brief for overlaps, readability and grouping. Rules: 240 × 170 grid, role-group cards, Amazon Ember, every edge straight or with one bend (`references/layout-and-style.md`). The `.drawio.png` embeds the XML, so it opens for editing in draw.io.

![Agentic RAG Chat](docs/samples/agentic-rag-chat.drawio.png)

[brief](docs/samples/agentic-rag-chat.brief.md) · [spec](docs/samples/agentic-rag-chat.json) · [agentic-rag-chat.drawio](docs/samples/agentic-rag-chat.drawio)

![Order pipeline](docs/samples/order-pipeline.drawio.png)

[brief](docs/samples/order-pipeline.brief.md) · [spec](docs/samples/order-pipeline.json) · [order-pipeline.drawio](docs/samples/order-pipeline.drawio) — shows the Step Functions fan-out (one bend) and a Korean title

## Install (Claude Code)

```
/plugin marketplace add hi-space/hi-aws-skills
/plugin install aws-drawio-diagram@hi-aws-skills
/reload-plugins
```

To use just the skill, symlink `skills/aws-drawio-diagram` into `~/.claude/skills/` or `~/.kiro/skills/`.

## Export to PNG/SVG/PDF

Requires the draw.io desktop CLI. On headless Linux, prefix with `xvfb-run -a`.

```bash
drawio -x -f png -e -b 10 -o name.drawio.png name.drawio
```

**Known limitations**

- Root or CI: check `drawio --version` first. Current builds need `--no-sandbox` right after `drawio`; builds 26.x and earlier reject it with `error: too many arguments` — drop the flag and run as non-root instead.
- A stencil newer than your installed draw.io build (e.g. `bedrock_agentcore`) renders as a blank colored square. Update draw.io desktop, or open the file at https://app.diagrams.net, which is always current; `shape=image` fallbacks are unaffected.

## Layout

```
skills/aws-drawio-diagram/
├── SKILL.md                    procedure, the two-pattern rule, icon lookup order, validation
├── references/
│   ├── layout-and-style.md     layout/edge/group/multi-page rules
│   ├── aws-icons-<category>.md generated: per-category stencil tables
│   ├── aws-icons-groups.md     generated: group badges and boundary styles
│   ├── aws-icons-aliases.md    hand-written: rename → stencil name
│   ├── aws-icons-legacy.md     generated: names not in the palette but still renderable
│   ├── aws-icons-retired.md    generated: retired palette
│   └── aws-icons-extra.md      generated: shape=image snippets for icons draw.io lacks
├── templates/                  5 reference templates
├── assets/extra-icons/         set-difference SVGs (AgentCore resources, etc.)
└── scripts/
    ├── validate_drawio.py      validates generated output (the skill runs this every time)
    ├── build_icon_catalog.py   regenerates the catalog (needs Node, maintainer-only)
    ├── build_extra_icons.py    reports/builds the set-difference icons (maintainer-only)
    └── stencil-index.json      the name index the validator reads
```

## Refreshing the catalog (maintainers)

```bash
scripts/fetch_sources.sh                       # refresh the draw.io dev-branch snapshot
python3 skills/aws-drawio-diagram/scripts/build_icon_catalog.py
python3 skills/aws-drawio-diagram/scripts/build_extra_icons.py --report   # review candidates, then edit extra-icons.txt
python3 skills/aws-drawio-diagram/scripts/build_extra_icons.py
python3 -m pytest tests -q
```

## Related skill

Finished images for docs/slides (HTML/SVG/PNG), or redrawing an existing `.drawio` file in the house style, is handled by the sibling plugin [aws-diagram-design](../aws-diagram-design/).

## License

MIT. Third-party notices in [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).
