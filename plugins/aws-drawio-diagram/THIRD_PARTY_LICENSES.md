# Third-party licenses

aws-drawio-diagram is MIT-licensed (see [`LICENSE`](LICENSE)). It derives from and redistributes content
from the following sources.

## aws-architecture-diagram-skill (upstream base)

- **License:** MIT — © 2026 Alexey Vidanov
- **Upstream:** https://github.com/vidanov/aws-architecture-diagram-skill (commit `29c1babbbe7ec69bed7f28f34380f906af5ae7af`)
- **Used in:** `skills/aws-drawio-diagram/templates/` (5 templates + README), the layout/edge/group/audience rules
  in `references/layout-and-style.md` and `SKILL.md`, and the structure of `scripts/validate_drawio.py`.
  The hand-written icon tables were replaced by generated catalogs (below).

## draw.io (diagrams.net) sources

- **License:** Apache License 2.0 — © JGraph Ltd / draw.io AG
- **Upstream:** https://github.com/jgraph/drawio (commit recorded in `scripts/fixtures/SOURCE.md`)
- **Used in:** `scripts/fixtures/Sidebar-AWS4.js` (verbatim snapshot, build input only) and
  `scripts/fixtures/aws4-stencil-names.txt` (shape names extracted from `stencils/aws4.xml`).
  The shipped `references/aws-icons-*.md` and `scripts/stencil-index.json` are derived from them.
  Stencil names are identifiers; the icon artwork itself is rendered by the user's draw.io installation.

## AWS Architecture Icons

- **License / terms:** https://aws.amazon.com/architecture/icons/ — © Amazon Web Services, Inc. or its affiliates.
- **Used in:** the stencils draw.io renders are AWS's official icons; this plugin ships none of them directly
  except the files under `assets/extra-icons/` (see next section). Icons must not be altered or recolored.

## Amazon Bedrock AgentCore resource icons (traced, not from the official package)

- **Files:** `skills/aws-drawio-diagram/assets/extra-icons/Res_Amazon-Bedrock-AgentCore_*_48.svg` (11 icons) and their
  base64 copies inside `references/aws-icons-extra.md`.
- **Source:** PNG artwork supplied by the repository owner, vectorised with potrace in the sibling
  `aws-diagram-design` plugin. Colours as supplied: black `#000000` + purple `#7B27FF`.
- **Status:** not part of the AWS Architecture Icons package 07312026, which carries only the service icon
  (`bedrock_agentcore` in draw.io). Replace with the official resource icons when AWS publishes them.
