# aws-drawio-diagram Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a second plugin, `aws-drawio-diagram`, that generates editable AWS `.drawio` diagrams with a stencil catalog regenerated from draw.io's own sources plus SVG fallbacks for icons draw.io lacks.

**Architecture:** A Node harness executes draw.io's `Sidebar-AWS4.js` against a stub `Sidebar` to capture every palette entry (name, label, category, style). A Python generator merges that with the renderable stencil list from `stencils/aws4.xml` and writes per-category markdown references plus a machine-readable `stencil-index.json`. A validator checks generated `.drawio` files against the index and the two-pattern `strokeColor` rule. Official-pack icons with no draw.io stencil (Bedrock AgentCore resources) are copied as SVG and exposed as `shape=image` data-URI snippets.

**Tech Stack:** Python 3.10+ stdlib (`xml.etree`, `json`, `base64`, `subprocess`), Node 18+ (build-time only, for the harness), pytest, bash/curl for source refresh. No runtime dependencies for the skill itself.

**Spec:** `docs/superpowers/specs/2026-09-12-aws-drawio-diagram-design.md`

## Global Constraints

- Plugin name and skill name: `aws-drawio-diagram`. Version `1.0.0`. License MIT.
- Upstream pinned: vidanov/aws-architecture-diagram-skill commit `29c1babbbe7ec69bed7f28f34380f906af5ae7af` (MIT © 2026 Alexey Vidanov). draw.io `dev` branch commit `f3abfe0f082c18f7b4fee8a34c2d07b1987687fd` (Apache-2.0).
- Do not copy all 824 official SVGs. Only the allow-listed delta goes to `assets/extra-icons/`. Never reference the sibling plugin's path at runtime.
- No 3D/isometric content (`aws3d`, Allied Telesis) anywhere.
- Generated files (`references/aws-icons-*.md` except `aws-icons-aliases.md`, `scripts/stencil-index.json`, `references/aws-icons-extra.md`) carry a "generated, do not edit" header.
- Service-level style: `shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.<name>` with `strokeColor=#ffffff`. Resource-level: `shape=mxgraph.aws4.<name>` with `strokeColor=none`. `productIcon;prIcon=` is treated as service-level.
- Image fallback style uses `image=data:image/svg+xml,<base64>` with **no** `;base64` (draw.io strips it; `;` is the style separator).
- Korean-first docs: `README.md` Korean, `README.en.md` English, matching `plugins/aws-diagram-design/`.
- Commit after every task. Commit messages end with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
- Run tests from the plugin dir: `cd plugins/aws-drawio-diagram && python3 -m pytest tests -q`.

---

## File Structure

| Path (under `plugins/aws-drawio-diagram/`) | Responsibility |
|---|---|
| `.claude-plugin/plugin.json`, `plugin.json` | Plugin manifests (Claude Code + agent-plugins.org schema) |
| `LICENSE`, `THIRD_PARTY_LICENSES.md`, `README.md`, `README.en.md`, `.gitignore` | Legal + docs |
| `scripts/fetch_sources.sh` | Refresh draw.io snapshots into `scripts/fixtures/` and write `SOURCE.md` |
| `scripts/fixtures/Sidebar-AWS4.js` | Snapshot: draw.io AWS palette definitions |
| `scripts/fixtures/aws4-stencil-names.txt` | Snapshot: one renderable stencil name per line, derived from `stencils/aws4.xml` |
| `scripts/fixtures/SOURCE.md` | Where the snapshots came from (URL, commit, license) |
| `skills/aws-drawio-diagram/SKILL.md` | Skill entry: procedure, two-pattern rule, lookup order, validation, export |
| `skills/aws-drawio-diagram/references/layout-and-style.md` | Layout, canvas, edges, groups, multi-page, audience mode |
| `skills/aws-drawio-diagram/references/aws-icons-aliases.md` | Hand-maintained service-rename → stencil-name table |
| `skills/aws-drawio-diagram/references/aws-icons-<slug>.md` | Generated per-category catalogs |
| `skills/aws-drawio-diagram/references/aws-icons-extra.md` | Generated image-fallback snippets |
| `skills/aws-drawio-diagram/templates/*.drawio`, `templates/README.md` | vidanov's 5 templates |
| `skills/aws-drawio-diagram/assets/extra-icons/*.svg` | Delta icons |
| `skills/aws-drawio-diagram/scripts/extract_stencils.js` | Node harness: Sidebar-AWS4.js → JSON |
| `skills/aws-drawio-diagram/scripts/build_icon_catalog.py` | JSON + stencil names → markdown + `stencil-index.json` |
| `skills/aws-drawio-diagram/scripts/stencil-index.json` | Generated name → kind/label/section index used by the validator |
| `skills/aws-drawio-diagram/scripts/build_extra_icons.py`, `scripts/extra-icons.txt` | Delta icon report/build + allow list |
| `skills/aws-drawio-diagram/scripts/validate_drawio.py` | Validator |
| `tests/test_extract_stencils.py`, `tests/test_build_icon_catalog.py`, `tests/test_build_extra_icons.py`, `tests/test_validate_drawio.py`, `tests/test_aliases.py` | pytest suites |

---

### Task 1: Scaffold the plugin, pin upstream sources, copy templates

**Files:**
- Create: `plugins/aws-drawio-diagram/.claude-plugin/plugin.json`
- Create: `plugins/aws-drawio-diagram/plugin.json`
- Create: `plugins/aws-drawio-diagram/LICENSE`
- Create: `plugins/aws-drawio-diagram/.gitignore`
- Create: `plugins/aws-drawio-diagram/scripts/fetch_sources.sh`
- Create: `plugins/aws-drawio-diagram/scripts/fixtures/{Sidebar-AWS4.js,aws4-stencil-names.txt,SOURCE.md}` (via the script)
- Create: `plugins/aws-drawio-diagram/skills/aws-drawio-diagram/templates/*.drawio`, `templates/README.md` (copied from upstream)
- Create: `plugins/aws-drawio-diagram/tests/test_scaffold.py`

**Interfaces:**
- Produces: fixture paths used by Tasks 2–3: `scripts/fixtures/Sidebar-AWS4.js`, `scripts/fixtures/aws4-stencil-names.txt`. Template dir used by Task 3 and 6 tests.

- [ ] **Step 1: Write the failing scaffold test**

`plugins/aws-drawio-diagram/tests/test_scaffold.py`:

```python
import json
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
SKILL = PLUGIN / "skills" / "aws-drawio-diagram"


def test_manifests_are_valid_json_and_agree_on_name():
    a = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
    b = json.loads((PLUGIN / "plugin.json").read_text())
    assert a["name"] == b["name"] == "aws-drawio-diagram"
    assert a["version"] == b["version"] == "1.0.0"


def test_fixture_snapshots_exist_and_are_plausible():
    js = PLUGIN / "scripts" / "fixtures" / "Sidebar-AWS4.js"
    names = PLUGIN / "scripts" / "fixtures" / "aws4-stencil-names.txt"
    assert "addAWS4Palette" in js.read_text()
    lines = [l for l in names.read_text().splitlines() if l.strip()]
    assert len(lines) > 1000
    assert "lambda_function" in lines and "group_vpc" in lines
    assert (PLUGIN / "scripts" / "fixtures" / "SOURCE.md").exists()


def test_templates_copied():
    templates = sorted(p.name for p in (SKILL / "templates").glob("*.drawio"))
    assert templates == [
        "event-driven-processing.drawio",
        "serverless-rest-api.drawio",
        "static-website.drawio",
        "three-tier-web-app.drawio",
        "vpc-networking.drawio",
    ]
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd plugins/aws-drawio-diagram 2>/dev/null || mkdir -p plugins/aws-drawio-diagram/tests; cd /home/ubuntu/workspace/hi-aws-skills/plugins/aws-drawio-diagram && python3 -m pytest tests/test_scaffold.py -q`
Expected: 3 failures (FileNotFoundError).

- [ ] **Step 3: Create manifests, license, gitignore**

`plugins/aws-drawio-diagram/.claude-plugin/plugin.json`:

```json
{
  "name": "aws-drawio-diagram",
  "description": "Generate editable AWS architecture diagrams as draw.io (.drawio) XML using draw.io's built-in official AWS icon stencils. Catalog of 1,000+ verified stencil names regenerated from draw.io sources, service/resource two-pattern rule, layout conventions, 5 reference templates, and a validator. SVG image fallback for icons draw.io lacks (Bedrock AgentCore resources). Korean triggers: draw.io로 그려줘, 드로우아이오, 편집 가능한 구성도.",
  "version": "1.0.0",
  "author": { "name": "hi-space" },
  "license": "MIT",
  "keywords": ["aws", "drawio", "draw.io", "architecture", "diagram", "aws-icons", "editable", "stencil"],
  "repository": "https://github.com/hi-space/hi-aws-skills"
}
```

`plugins/aws-drawio-diagram/plugin.json`:

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "aws-drawio-diagram",
  "version": "1.0.0",
  "description": "Editable AWS architecture diagrams as draw.io XML — verified stencil catalog regenerated from draw.io sources, two-pattern icon rule, layout conventions, templates, validator, and SVG fallback for icons draw.io lacks.",
  "author": { "name": "hi-space" },
  "keywords": ["aws diagram", "drawio", "draw.io", "architecture diagram", "aws icons", "editable diagram"],
  "license": "MIT",
  "repository": "https://github.com/hi-space/hi-aws-skills"
}
```

`plugins/aws-drawio-diagram/LICENSE`:

```
MIT License

Copyright (c) 2026 Alexey Vidanov (aws-architecture-diagram-skill)
Copyright (c) 2026 hi-space (aws-drawio-diagram — catalog generator, validator, extra icons, docs)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

`plugins/aws-drawio-diagram/.gitignore`:

```
.DS_Store
__pycache__/
*.pyc
.pytest_cache/
```

- [ ] **Step 4: Write the source-refresh script**

`plugins/aws-drawio-diagram/scripts/fetch_sources.sh`:

```bash
#!/usr/bin/env bash
# Refresh the draw.io source snapshots that build_icon_catalog.py reads.
#
#   scripts/fetch_sources.sh            # from jgraph/drawio branch "dev"
#   scripts/fetch_sources.sh <ref>      # any branch, tag, or commit
#
# Writes: fixtures/Sidebar-AWS4.js, fixtures/aws4-stencil-names.txt, fixtures/SOURCE.md
set -euo pipefail

REF="${1:-dev}"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/fixtures"
BASE="https://raw.githubusercontent.com/jgraph/drawio/${REF}/src/main/webapp"
mkdir -p "$DIR"

curl -fsSL "${BASE}/js/diagramly/sidebar/Sidebar-AWS4.js" -o "${DIR}/Sidebar-AWS4.js"

# stencils/aws4.xml is ~6.6 MB; keep only the normalized shape names.
# draw.io lowercases stencil names and replaces spaces with "_" when registering them.
curl -fsSL "${BASE}/stencils/aws4.xml" \
  | grep -oE '<shape [^>]*name="[^"]+"' \
  | sed -E 's/.*name="([^"]+)".*/\1/' \
  | tr 'A-Z' 'a-z' | tr ' ' '_' \
  | sort -u > "${DIR}/aws4-stencil-names.txt"

SHA="$(curl -fsSL "https://api.github.com/repos/jgraph/drawio/commits/${REF}" \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["sha"])')"

cat > "${DIR}/SOURCE.md" <<EOF
# Snapshot sources

Fetched by \`scripts/fetch_sources.sh ${REF}\` on $(date -u +%Y-%m-%d).

| File | Upstream | Commit | License |
|---|---|---|---|
| \`Sidebar-AWS4.js\` | https://github.com/jgraph/drawio/blob/${SHA}/src/main/webapp/js/diagramly/sidebar/Sidebar-AWS4.js | \`${SHA}\` | Apache-2.0 |
| \`aws4-stencil-names.txt\` | derived from https://github.com/jgraph/drawio/blob/${SHA}/src/main/webapp/stencils/aws4.xml (shape names only, normalized) | \`${SHA}\` | Apache-2.0 |

These snapshots are build inputs only. The distributed skill ships the derived
\`references/aws-icons-*.md\` and \`scripts/stencil-index.json\`, not these files' content.
EOF

echo "Sidebar-AWS4.js: $(wc -c < "${DIR}/Sidebar-AWS4.js") bytes"
echo "stencil names:   $(wc -l < "${DIR}/aws4-stencil-names.txt")"
echo "commit:          ${SHA}"
```

Run: `chmod +x plugins/aws-drawio-diagram/scripts/fetch_sources.sh && plugins/aws-drawio-diagram/scripts/fetch_sources.sh f3abfe0f082c18f7b4fee8a34c2d07b1987687fd`
Expected: `stencil names: 1050` (±0), commit echoed.

- [ ] **Step 5: Copy the upstream templates at the pinned commit**

```bash
cd /tmp && rm -rf vidanov-skill && git clone -q https://github.com/vidanov/aws-architecture-diagram-skill vidanov-skill && cd vidanov-skill && git checkout -q 29c1babbbe7ec69bed7f28f34380f906af5ae7af
mkdir -p /home/ubuntu/workspace/hi-aws-skills/plugins/aws-drawio-diagram/skills/aws-drawio-diagram/templates
cp templates/*.drawio templates/README.md /home/ubuntu/workspace/hi-aws-skills/plugins/aws-drawio-diagram/skills/aws-drawio-diagram/templates/
```

Do **not** copy `templates/.$serverless-rest-api.drawio.dtmp` (draw.io temp file).

- [ ] **Step 6: Run the scaffold test**

Run: `cd /home/ubuntu/workspace/hi-aws-skills/plugins/aws-drawio-diagram && python3 -m pytest tests/test_scaffold.py -q`
Expected: 3 passed.

- [ ] **Step 7: Commit**

```bash
cd /home/ubuntu/workspace/hi-aws-skills
git add plugins/aws-drawio-diagram
git commit -m "Scaffold aws-drawio-diagram plugin with pinned draw.io snapshots and upstream templates

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: Node harness that executes Sidebar-AWS4.js and emits palette JSON

**Files:**
- Create: `plugins/aws-drawio-diagram/skills/aws-drawio-diagram/scripts/extract_stencils.js`
- Test: `plugins/aws-drawio-diagram/tests/test_extract_stencils.py`

**Interfaces:**
- Consumes: `scripts/fixtures/Sidebar-AWS4.js` (Task 1).
- Produces: stdout JSON `{"sections": [{"id": "aws4Compute", "title": "AWS / Compute", "entries": [{"style": str, "width": number, "height": number, "value": str, "label": str}]}]}`. Exit 1 with a message on stderr if zero palettes were captured. Task 3 calls it via `subprocess`.

- [ ] **Step 1: Write the failing test**

`plugins/aws-drawio-diagram/tests/test_extract_stencils.py`:

```python
import json
import subprocess
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[1]
HARNESS = PLUGIN / "skills" / "aws-drawio-diagram" / "scripts" / "extract_stencils.js"
SIDEBAR = PLUGIN / "scripts" / "fixtures" / "Sidebar-AWS4.js"


def run(source: Path):
    return subprocess.run(["node", str(HARNESS), str(source)], capture_output=True, text=True)


@pytest.fixture(scope="module")
def data():
    proc = run(SIDEBAR)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_captures_all_palettes_including_retired(data):
    ids = [s["id"] for s in data["sections"]]
    assert len(ids) == 31
    assert ids[0] == "aws4Arrows" and ids[-1] == "aws4r"
    assert "aws4Compute" in ids and "aws4Groups" in ids


def test_entries_have_resolved_styles(data):
    compute = next(s for s in data["sections"] if s["id"] == "aws4Compute")
    first = compute["entries"][0]
    assert first["label"] == "Compute"
    assert "shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.compute;" in first["style"]
    assert "fillColor=#ED7100" in first["style"]
    assert first["width"] == 78


def test_arrows_are_dropped_and_retired_functions_resolve(data):
    arrows = next(s for s in data["sections"] if s["id"] == "aws4Arrows")
    assert arrows["entries"] == []
    retired = next(s for s in data["sections"] if s["id"] == "aws4r")
    styles = " ".join(e["style"] for e in retired["entries"])
    assert "resIcon=mxgraph.aws4.quicksight;" in styles
    assert "fillColor=#8C4FFF" in styles


def test_fails_loudly_on_unrelated_source(tmp_path):
    bogus = tmp_path / "x.js"
    bogus.write_text("Sidebar.prototype.addAWS4Palette = function() {};")
    proc = run(bogus)
    assert proc.returncode == 1
    assert "no palettes" in proc.stderr
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd plugins/aws-drawio-diagram && python3 -m pytest tests/test_extract_stencils.py -q`
Expected: failures (`Cannot find module` / assertion on returncode).

- [ ] **Step 3: Write the harness**

`plugins/aws-drawio-diagram/skills/aws-drawio-diagram/scripts/extract_stencils.js`:

```js
#!/usr/bin/env node
'use strict';
// Execute draw.io's Sidebar-AWS4.js against a stub Sidebar and print every AWS
// palette entry as JSON. This is a build-time tool for build_icon_catalog.py;
// the skill itself does not need Node at runtime.
//
//   node extract_stencils.js <path/to/Sidebar-AWS4.js> > palette.json
//
// Output: {"sections":[{"id","title","entries":[{"style","width","height","value","label"}]}]}
const fs = require('fs');

const source = process.argv[2];
if (!source) {
  console.error('usage: extract_stencils.js <Sidebar-AWS4.js>');
  process.exit(2);
}
const code = fs.readFileSync(source, 'utf8');

const sections = [];

class StubSidebar {
  // Every palette entry flows through here. Returning the record lets
  // addPaletteFunctions receive the same objects in its entries array.
  createVertexTemplateEntry(style, width, height, value, label) {
    return { style, width, height, value: value || '', label: label || '' };
  }
  // Arrow palette entries are edge styles, not stencils.
  createEdgeTemplateEntry() { return null; }
  addPaletteFunctions(id, title, _expand, entries) {
    sections.push({ id, title, entries: (entries || []).filter(Boolean) });
  }
  setCurrentSearchEntryLibrary() {}
  getTagsForStencil() { return []; }
}

global.Sidebar = StubSidebar;                 // the file assigns Sidebar.prototype.addAWS4*Palette
global.mxConstants = { STYLE_SHAPE: 'shape' }; // the only mx* global the file touches

new Function(code)();                          // runs the IIFE that installs the palette methods

const sb = new StubSidebar();
if (typeof sb.addAWS4Palette === 'function') sb.addAWS4Palette();
if (typeof sb.addAWS4RetiredPalette === 'function') sb.addAWS4RetiredPalette();

if (sections.length === 0) {
  console.error('no palettes captured: Sidebar-AWS4.js format changed?');
  process.exit(1);
}
process.stdout.write(JSON.stringify({ sections }));
```

- [ ] **Step 4: Run the tests**

Run: `cd plugins/aws-drawio-diagram && python3 -m pytest tests/test_extract_stencils.py -q`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/aws-drawio-diagram/skills/aws-drawio-diagram/scripts/extract_stencils.js plugins/aws-drawio-diagram/tests/test_extract_stencils.py
git commit -m "Add Node harness that extracts draw.io AWS palette entries as JSON

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: Catalog generator — markdown references and stencil-index.json

**Files:**
- Create: `plugins/aws-drawio-diagram/skills/aws-drawio-diagram/scripts/build_icon_catalog.py`
- Create (generated): `plugins/aws-drawio-diagram/skills/aws-drawio-diagram/references/aws-icons-*.md`, `plugins/aws-drawio-diagram/skills/aws-drawio-diagram/scripts/stencil-index.json`
- Test: `plugins/aws-drawio-diagram/tests/test_build_icon_catalog.py`

**Interfaces:**
- Consumes: `extract_stencils.js` output (Task 2); `scripts/fixtures/aws4-stencil-names.txt` (Task 1).
- Produces (Python API, imported by tests and by Task 5/6):
  - `extract(sidebar_js: Path) -> dict`
  - `load_stencil_names(path: Path) -> set[str]`
  - `slug_for(section_id: str) -> str`
  - `classify(style: str) -> tuple[str, str | None]` — kind ∈ `service|group|resource|style`
  - `build_index(data: dict, stencil_names: set[str]) -> tuple[dict, list[dict]]` — returns `(stencils, boundaries)`; `stencils[name] = {"kind", "label", "section", "sectionTitle", "fillColor", "strokeColor", "renderable"}`; `kind` ∈ `service|resource|group|legacy`
  - `render_markdown(stencils: dict, boundaries: list[dict], out_dir: Path) -> list[Path]`
  - `write_index(stencils: dict, path: Path, sources: dict) -> None` — JSON `{"generated_from": {...}, "js_shapes": [...], "stencils": {...}}`
  - Constant `JS_SHAPES = ("group", "group2", "groupCenter", "productIcon", "resourceIcon")`
- Produces (file): `scripts/stencil-index.json` read by `validate_drawio.py` (Task 6) and `build_extra_icons.py` (Task 5).

- [ ] **Step 1: Write the failing tests**

`plugins/aws-drawio-diagram/tests/test_build_icon_catalog.py`:

```python
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[1]
SKILL = PLUGIN / "skills" / "aws-drawio-diagram"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

import build_icon_catalog as bic  # noqa: E402

SIDEBAR = PLUGIN / "scripts" / "fixtures" / "Sidebar-AWS4.js"
NAMES = PLUGIN / "scripts" / "fixtures" / "aws4-stencil-names.txt"


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("refs")
    data = bic.extract(SIDEBAR)
    stencils, boundaries = bic.build_index(data, bic.load_stencil_names(NAMES))
    files = bic.render_markdown(stencils, boundaries, out)
    bic.write_index(stencils, out / "stencil-index.json", {"sidebar": "test", "stencils": "test"})
    return stencils, boundaries, files, out


def test_counts_meet_floors(built):
    stencils, _, _, _ = built
    kinds = {}
    for s in stencils.values():
        kinds[s["kind"]] = kinds.get(s["kind"], 0) + 1
    assert kinds["service"] >= 300
    assert kinds["resource"] >= 500
    assert kinds["group"] == 16
    assert kinds["legacy"] >= 50


def test_classification_examples(built):
    stencils, _, _, _ = built
    assert stencils["lambda"]["kind"] == "service"
    assert stencils["lambda"]["fillColor"] == "#ED7100"
    assert stencils["lambda_function"]["kind"] == "resource"
    assert stencils["group_vpc2"]["kind"] == "group"
    assert stencils["group_vpc"]["kind"] == "legacy"          # renders, not in palette
    assert stencils["quicksight"]["section"] == "retired"
    assert stencils["elasticsearch_service"]["kind"] == "service"


def test_classify_and_slug():
    assert bic.classify("a;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ec2;") == ("service", "ec2")
    assert bic.classify("shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_region;") == ("group", "group_region")
    assert bic.classify("shape=mxgraph.aws4.instance2;") == ("resource", "instance2")
    assert bic.classify("fillColor=none;strokeColor=#147EBA;") == ("style", None)
    assert bic.slug_for("aws4Network Content Delivery") == "network-content-delivery"
    assert bic.slug_for("aws4r") == "retired"
    assert bic.slug_for("aws4Illustrations") == "general"


def test_every_template_stencil_is_in_index(built):
    stencils, _, _, _ = built
    used = set()
    for tpl in (SKILL / "templates").glob("*.drawio"):
        used |= set(re.findall(r"mxgraph\.aws4\.([A-Za-z0-9_]+)", tpl.read_text()))
    used -= set(bic.JS_SHAPES)
    missing = sorted(n for n in used if n not in stencils)
    assert missing == []


def test_markdown_files_and_headers(built):
    _, _, files, out = built
    names = sorted(p.name for p in files)
    assert "aws-icons-compute.md" in names
    assert "aws-icons-groups.md" in names
    assert "aws-icons-general.md" in names
    assert "aws-icons-retired.md" in names
    assert "aws-icons-legacy.md" in names
    compute = (out / "aws-icons-compute.md").read_text()
    assert compute.startswith("# AWS Icons: Compute")
    assert "Do not edit by hand" in compute
    assert "fillColor: `#ED7100`" in compute
    assert "| `lambda` | Lambda |" in compute
    assert "| `lambda_function` | Lambda Function |" in compute
    groups = (out / "aws-icons-groups.md").read_text()
    assert "| `group_vpc2` | `#8C4FFF` | VPC |" in groups
    assert "Availability Zone" in groups           # boundary style without grIcon


def test_index_json_shape(built):
    _, _, _, out = built
    idx = json.loads((out / "stencil-index.json").read_text())
    assert set(idx) == {"generated_from", "js_shapes", "stencils"}
    assert idx["js_shapes"] == list(bic.JS_SHAPES)
    assert idx["stencils"]["s3"]["kind"] == "service"


def test_cli_fails_on_empty_source(tmp_path):
    bogus = tmp_path / "Sidebar-AWS4.js"
    bogus.write_text("Sidebar.prototype.addAWS4Palette = function() {};")
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "build_icon_catalog.py"), "--sidebar", str(bogus),
         "--stencils", str(NAMES), "--out-dir", str(tmp_path / "refs"), "--index", str(tmp_path / "i.json")],
        capture_output=True, text=True,
    )
    assert proc.returncode == 1
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd plugins/aws-drawio-diagram && python3 -m pytest tests/test_build_icon_catalog.py -q`
Expected: `ModuleNotFoundError: build_icon_catalog`.

- [ ] **Step 3: Write the generator**

`plugins/aws-drawio-diagram/skills/aws-drawio-diagram/scripts/build_icon_catalog.py`:

```python
#!/usr/bin/env python3
"""Generate the AWS stencil catalog for the aws-drawio-diagram skill.

Inputs (snapshots under <plugin>/scripts/fixtures/, refresh with scripts/fetch_sources.sh):
  Sidebar-AWS4.js         draw.io palette definitions: names, labels, categories, style pattern
  aws4-stencil-names.txt  every renderable stencil name from stencils/aws4.xml (ground truth)

Outputs:
  references/aws-icons-<section>.md   one markdown table set per palette section
  references/aws-icons-groups.md      grIcon badges + boundary styles without grIcon
  references/aws-icons-general.md     General Resources + Illustrations
  references/aws-icons-retired.md     retired palette (still renders)
  references/aws-icons-legacy.md      renderable stencils absent from the palette
  scripts/stencil-index.json          name -> kind/label/section, read by validate_drawio.py

Usage:
  build_icon_catalog.py [--sidebar PATH] [--stencils PATH] [--out-dir DIR] [--index PATH]
Requires Node.js (runs extract_stencils.js). Build-time only.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter, OrderedDict
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_DIR = HERE.parent
PLUGIN_DIR = SKILL_DIR.parents[1]
FIXTURES = PLUGIN_DIR / "scripts" / "fixtures"
REFERENCES = SKILL_DIR / "references"

JS_SHAPES = ("group", "group2", "groupCenter", "productIcon", "resourceIcon")
MIN_SERVICE = 300
MIN_RESOURCE = 500

SECTION_SLUGS = {
    "aws4r": "retired",
    "aws4General Resources": "general",
    "aws4Illustrations": "general",
    "aws4Groups": "groups",
}
SECTION_TITLES = {
    "general": "General Resources & Illustrations",
    "groups": "Groups",
    "retired": "Retired (still renders)",
    "legacy": "Legacy stencils (render, not in the palette)",
}
GENERATED_NOTE = (
    "> Generated by `scripts/build_icon_catalog.py` from draw.io `Sidebar-AWS4.js` and "
    "`stencils/aws4.xml` (see `scripts/fixtures/SOURCE.md`). Do not edit by hand — rerun the script."
)

RE_RES = re.compile(r"resIcon=mxgraph\.aws4\.([A-Za-z0-9_]+)")
RE_GR = re.compile(r"grIcon=mxgraph\.aws4\.([A-Za-z0-9_]+)")
RE_SHAPE = re.compile(r"shape=mxgraph\.aws4\.([A-Za-z0-9_]+)")
RE_FILL = re.compile(r"(?:^|;)fillColor=([^;]+)")
RE_STROKE = re.compile(r"(?:^|;)strokeColor=([^;]+)")


def extract(sidebar_js: Path) -> dict:
    """Run the Node harness and return its JSON."""
    proc = subprocess.run(
        ["node", str(HERE / "extract_stencils.js"), str(sidebar_js)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        sys.exit(f"extract_stencils.js failed: {proc.stderr.strip()}")
    return json.loads(proc.stdout)


def load_stencil_names(path: Path) -> set[str]:
    return {ln.strip() for ln in path.read_text().splitlines() if ln.strip() and not ln.startswith("#")}


def slug_for(section_id: str) -> str:
    if section_id in SECTION_SLUGS:
        return SECTION_SLUGS[section_id]
    return section_id.removeprefix("aws4").strip().lower().replace(" ", "-")


def classify(style: str) -> tuple[str, str | None]:
    if m := RE_RES.search(style):
        return "service", m.group(1)
    if m := RE_GR.search(style):
        return "group", m.group(1)
    if (m := RE_SHAPE.search(style)) and m.group(1) not in JS_SHAPES:
        return "resource", m.group(1)
    return "style", None


def _first(regex: re.Pattern, style: str) -> str | None:
    m = regex.search(style)
    return m.group(1) if m else None


def build_index(data: dict, stencil_names: set[str]) -> tuple[dict, list[dict]]:
    stencils: "OrderedDict[str, dict]" = OrderedDict()
    boundaries: list[dict] = []
    for sec in data["sections"]:
        slug = slug_for(sec["id"])
        for e in sec["entries"]:
            kind, name = classify(e["style"])
            label = (e.get("label") or e.get("value") or name or "").strip()
            if kind == "style":
                if slug == "groups":
                    boundaries.append({"label": label, "style": e["style"]})
                continue
            if name in stencils:          # first palette wins
                continue
            stencils[name] = {
                "kind": kind,
                "label": label,
                "section": slug,
                "sectionTitle": SECTION_TITLES.get(slug, sec["title"].removeprefix("AWS / ")),
                "fillColor": _first(RE_FILL, e["style"]),
                "strokeColor": _first(RE_STROKE, e["style"]),
                "style": e["style"] if kind == "group" else None,
                "renderable": name in stencil_names,
            }
    for name in sorted(stencil_names - set(stencils)):
        stencils[name] = {
            "kind": "legacy",
            "label": name.replace("_", " "),
            "section": "legacy",
            "sectionTitle": SECTION_TITLES["legacy"],
            "fillColor": None,
            "strokeColor": None,
            "style": None,
            "renderable": True,
        }
    return stencils, boundaries


def _table(rows: list[tuple[str, ...]], header: tuple[str, ...]) -> str:
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)


def _kind_table(items: list[tuple[str, dict]], kind: str, show_fill: bool) -> str:
    if kind == "service":
        heading = ("## Service-level — `shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.<name>` "
                   "· **strokeColor=#ffffff** · 78×78")
        col = "resIcon"
    else:
        heading = ("## Resource-level — `shape=mxgraph.aws4.<name>` "
                   "· **strokeColor=none** · 48×48 or 78×78")
        col = "shape"
    header = (col, "Display Name") + (("fillColor",) if show_fill else ())
    rows = [
        (f"`{n}`", s["label"] or n) + ((f"`{s['fillColor']}`",) if show_fill else ())
        for n, s in items
    ]
    return heading + "\n" + _table(rows, header)


def _render_section(slug: str, title: str, items: list[tuple[str, dict]]) -> str:
    fills = Counter(s["fillColor"] for _, s in items if s["fillColor"])
    show_fill = len(fills) > 1
    parts = [f"# AWS Icons: {title}", "", GENERATED_NOTE, ""]
    if len(fills) == 1:
        parts += [f"fillColor: `{next(iter(fills))}`", ""]
    elif fills:
        parts += ["fillColor varies per row (see column).", ""]
    if slug == "retired":
        parts += ["These stencils still render but AWS retired the service or replaced the icon. "
                  "Prefer the current icon in the category file; use these only for legacy diagrams.", ""]
    for kind in ("service", "resource"):
        sub = [(n, s) for n, s in items if s["kind"] == kind]
        if sub:
            parts += [_kind_table(sub, kind, show_fill), ""]
    return "\n".join(parts).rstrip() + "\n"


def _render_groups(items: list[tuple[str, dict]], boundaries: list[dict]) -> str:
    parts = ["# AWS Icons: Groups", "", GENERATED_NOTE, "",
             "All groups: `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.<grIcon>;fillColor=none;container=1;"
             "verticalAlign=top;align=left;spacingLeft=30;`  ", "The badge is the grIcon; the border takes strokeColor.", "",
             "## Group badges (grIcon)"]
    rows = []
    for n, s in items:
        rows.append((f"`{n}`", f"`{s['strokeColor'] or 'none'}`", s["label"] or n))
    parts += [_table(rows, ("grIcon", "strokeColor", "Display Name")), "",
              "## Boundary styles without a badge", "",
              "Use the full style string as-is (add `container=1;` when children live inside).", ""]
    for b in boundaries:
        parts += [f"**{b['label']}**", "", "```", b["style"], "```", ""]
    return "\n".join(parts).rstrip() + "\n"


def _render_legacy(items: list[tuple[str, dict]]) -> str:
    parts = ["# AWS Icons: Legacy stencils", "", GENERATED_NOTE, "",
             "These names exist in draw.io's `aws4.xml` stencil set, so they render, but the current palette "
             "does not list them (renamed or superseded). Use them as resource-level shapes "
             "(`shape=mxgraph.aws4.<name>;strokeColor=none`) or as grIcon badges when the name starts with `group_`. "
             "Prefer the palette name from the category files when one exists.", ""]
    rows = [(f"`{n}`", s["label"]) for n, s in items]
    parts += [_table(rows, ("name", "Guessed Display Name")), ""]
    return "\n".join(parts).rstrip() + "\n"


def render_markdown(stencils: dict, boundaries: list[dict], out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    by_section: "OrderedDict[str, list[tuple[str, dict]]]" = OrderedDict()
    for n, s in stencils.items():
        by_section.setdefault(s["section"], []).append((n, s))
    written: list[Path] = []
    for slug, items in by_section.items():
        title = items[0][1]["sectionTitle"]
        if slug == "groups":
            text = _render_groups(items, boundaries)
        elif slug == "legacy":
            text = _render_legacy(items)
        else:
            text = _render_section(slug, title, items)
        path = out_dir / f"aws-icons-{slug}.md"
        path.write_text(text)
        written.append(path)
    return written


def write_index(stencils: dict, path: Path, sources: dict) -> None:
    slim = {
        n: {k: s[k] for k in ("kind", "label", "section", "fillColor", "strokeColor", "renderable")}
        for n, s in stencils.items()
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(
        {"generated_from": sources, "js_shapes": list(JS_SHAPES), "stencils": slim},
        indent=1, ensure_ascii=False,
    ) + "\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sidebar", type=Path, default=FIXTURES / "Sidebar-AWS4.js")
    ap.add_argument("--stencils", type=Path, default=FIXTURES / "aws4-stencil-names.txt")
    ap.add_argument("--out-dir", type=Path, default=REFERENCES)
    ap.add_argument("--index", type=Path, default=HERE / "stencil-index.json")
    args = ap.parse_args(argv)

    data = extract(args.sidebar)
    stencils, boundaries = build_index(data, load_stencil_names(args.stencils))
    counts = Counter(s["kind"] for s in stencils.values())
    if counts["service"] < MIN_SERVICE or counts["resource"] < MIN_RESOURCE:
        print(f"refusing to write: service={counts['service']} resource={counts['resource']} "
              f"(floors {MIN_SERVICE}/{MIN_RESOURCE}); source format changed?", file=sys.stderr)
        return 1
    unrenderable = sorted(n for n, s in stencils.items() if not s["renderable"])
    files = render_markdown(stencils, boundaries, args.out_dir)
    write_index(stencils, args.index, {"sidebar": args.sidebar.name, "stencils": args.stencils.name})
    print(f"wrote {len(files)} reference files to {args.out_dir}")
    print("counts:", dict(counts))
    if unrenderable:
        print("WARNING palette names without a stencil (check draw.io):", ", ".join(unrenderable))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests**

Run: `cd plugins/aws-drawio-diagram && python3 -m pytest tests/test_build_icon_catalog.py -q`
Expected: 7 passed. If `test_every_template_stencil_is_in_index` fails, print `missing` and fix the *template* (a stencil name that is in neither the palette nor `aws4.xml` cannot render); do not weaken the test.

- [ ] **Step 5: Generate the real references and index**

Run: `python3 plugins/aws-drawio-diagram/skills/aws-drawio-diagram/scripts/build_icon_catalog.py`
Expected output: `wrote 31 reference files` (or the actual count; 27 categories + general + groups + retired + legacy), `counts: {'service': 4xx, 'resource': 6xx, 'group': 16, 'legacy': 6x}`, and no WARNING line (only `group` is a JS shape and is excluded before the check).

Run: `ls plugins/aws-drawio-diagram/skills/aws-drawio-diagram/references | wc -l && grep -c '^| `' plugins/aws-drawio-diagram/skills/aws-drawio-diagram/references/aws-icons-compute.md`
Expected: 31 files; compute has ~130 rows.

- [ ] **Step 6: Commit**

```bash
git add plugins/aws-drawio-diagram/skills/aws-drawio-diagram/scripts/build_icon_catalog.py plugins/aws-drawio-diagram/skills/aws-drawio-diagram/scripts/stencil-index.json plugins/aws-drawio-diagram/skills/aws-drawio-diagram/references plugins/aws-drawio-diagram/tests/test_build_icon_catalog.py
git commit -m "Generate AWS stencil catalog and index from draw.io sources

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: Hand-maintained references — aliases and layout/style rules

**Files:**
- Create: `plugins/aws-drawio-diagram/skills/aws-drawio-diagram/references/aws-icons-aliases.md`
- Create: `plugins/aws-drawio-diagram/skills/aws-drawio-diagram/references/layout-and-style.md`
- Test: `plugins/aws-drawio-diagram/tests/test_aliases.py`

**Interfaces:**
- Consumes: `scripts/stencil-index.json` (Task 3).
- Produces: alias table format `| Service name | stencil | pattern |` where `stencil` is a backticked name and `pattern` ∈ `service|resource|group|image`. `image` rows point at `aws-icons-extra.md` (Task 5) and are skipped by the test.

- [ ] **Step 1: Write the failing test**

`plugins/aws-drawio-diagram/tests/test_aliases.py`:

```python
import json
import re
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
SKILL = PLUGIN / "skills" / "aws-drawio-diagram"
ALIASES = SKILL / "references" / "aws-icons-aliases.md"
INDEX = SKILL / "scripts" / "stencil-index.json"

ROW = re.compile(r"^\|\s*[^|]+\|\s*`([A-Za-z0-9_]+)`\s*\|\s*(service|resource|group|image)\s*\|", re.M)


def test_every_alias_target_exists_in_index():
    idx = json.loads(INDEX.read_text())["stencils"]
    rows = ROW.findall(ALIASES.read_text())
    assert len(rows) >= 20
    bad = [(n, p) for n, p in rows if p != "image" and n not in idx]
    assert bad == []


def test_alias_patterns_agree_with_index_kind():
    idx = json.loads(INDEX.read_text())["stencils"]
    rows = ROW.findall(ALIASES.read_text())
    mismatched = []
    for name, pattern in rows:
        if pattern == "image":
            continue
        kind = idx[name]["kind"]
        ok = (pattern == "service" and kind in ("service", "legacy")) \
            or (pattern == "resource" and kind in ("resource", "legacy")) \
            or (pattern == "group" and kind in ("group", "legacy"))
        if not ok:
            mismatched.append((name, pattern, kind))
    assert mismatched == []
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd plugins/aws-drawio-diagram && python3 -m pytest tests/test_aliases.py -q`
Expected: FileNotFoundError on `aws-icons-aliases.md`.

- [ ] **Step 3: Write the aliases reference**

`plugins/aws-drawio-diagram/skills/aws-drawio-diagram/references/aws-icons-aliases.md`:

```markdown
# AWS Icons: Aliases (renamed services → draw.io stencil names)

Hand-maintained. draw.io keeps the stencil name a service had when the icon was first added, so the current
AWS marketing name often does not match. Look here when the category file has no obvious row.
`pattern` tells you which style to use: `service` = resourceIcon frame + `strokeColor=#ffffff`,
`resource` = standalone shape + `strokeColor=none`, `group` = grIcon badge, `image` = SVG fallback in
[`aws-icons-extra.md`](aws-icons-extra.md).

| Service name (current) | stencil | pattern | Note |
|---|---|---|---|
| Amazon OpenSearch Service | `elasticsearch_service` | service | renamed from Elasticsearch Service in 2021 |
| Amazon OpenSearch Serverless / cluster nodes | `opensearch_service_data_node` | resource | resource icons kept the OpenSearch name |
| Amazon Quick Suite (was QuickSight) | `quick_suite` | service | `quicksight` is in the retired palette |
| Amazon SageMaker AI | `sagemaker_2` | service | `sagemaker` is the older icon |
| Amazon Managed Service for Apache Flink (was Kinesis Data Analytics) | `managed_service_for_apache_flink` | service | `kinesis_data_analytics` is retired |
| Amazon Data Firehose | `kinesis_data_firehose` | service | |
| Amazon Kinesis Data Streams | `kinesis_data_streams` | service | |
| Amazon MSK | `managed_streaming_for_kafka` | service | |
| Amazon CloudWatch | `cloudwatch_2` | service | `cloudwatch` (no suffix) is legacy |
| Amazon CloudWatch Logs | `cloudwatch_logs` | resource | |
| Amazon EventBridge (was CloudWatch Events) | `eventbridge` | service | |
| AWS Certificate Manager | `certificate_manager_3` | service | `certificate_manager` / `_2` are older icons |
| AWS IAM | `identity_and_access_management` | service | |
| AWS IAM Identity Center (was SSO) | `single_sign_on` | service | |
| Amazon SES | `simple_email_service` | service | |
| Amazon SNS | `sns` | service | |
| Amazon SQS | `sqs` | service | |
| Amazon ECS | `ecs` | service | |
| Amazon EKS | `eks` | service | |
| Amazon ECR | `ecr` | service | |
| Elastic Load Balancing (service) | `elastic_load_balancing` | service | |
| Application Load Balancer | `application_load_balancer` | resource | |
| Network Load Balancer | `network_load_balancer` | resource | |
| Amazon VPC (service icon) | `vpc` | service | |
| VPC boundary (group badge) | `group_vpc2` | group | `group_vpc` is legacy but still renders |
| Private subnet boundary | `group_security_group` | group | draw.io reuses this badge; set `strokeColor=#00A4A6` |
| Public subnet boundary | `group_security_group` | group | set `strokeColor=#7AA116` |
| AWS Systems Manager | `systems_manager` | service | |
| Amazon Rekognition | `rekognition_2` | service | |
| Amazon DocumentDB | `documentdb_with_mongodb_compatibility` | service | |
| Amazon ElastiCache (Valkey) | `elasticache_for_valkey` | resource | service icon is `elasticache` |
| Amazon Q | `q` | service | |
| Amazon Nova | `nova2` | service | |
| Amazon Bedrock | `bedrock` | service | |
| Amazon Bedrock AgentCore (service) | `bedrock_agentcore` | service | |
| Bedrock AgentCore Runtime / Gateway / Memory / Identity / … | `agentcore_runtime` | image | no draw.io stencil; see aws-icons-extra.md |
| AWS Step Functions | `step_functions` | service | |
| AWS Transit Gateway | `transit_gateway` | service | route table: `transit_gateway_attachment` (resource) |
| VPC peering connection | `peering` | resource | `vpc_peering` does **not** exist |
| AWS CloudHSM | `cloudhsm` | service | `cloud_hsm` does **not** exist |
| Amazon S3 Glacier | `glacier` | service | Deep Archive: `glacier_deep_archive` (resource) |
| AWS Elastic Beanstalk | `elastic_beanstalk` | service | |
| AWS Global Accelerator | `global_accelerator` | service | |
```

Every non-`image` name above must exist in `stencil-index.json`. If the test reports one missing, fix the row (search the index for the right name), do not delete the row silently.

- [ ] **Step 4: Write the layout and style reference**

`plugins/aws-drawio-diagram/skills/aws-drawio-diagram/references/layout-and-style.md`:

````markdown
# Layout and style rules

Adapted from vidanov/aws-architecture-diagram-skill (MIT). Read this once per diagram; SKILL.md only keeps the
procedure and the two icon patterns.

## Layout

- **Left-to-right flow** for the request/data path. Users and front ends on the **left**, data stores and
  external systems on the **right**.
- Horizontal lanes for parallel paths (top lane, bottom lane).
- **≥220 px horizontal** spacing between icons (room for edge labels). **≥250 px vertical** between lanes.
- Secondary services (monitoring, DLQ, error paths) go **below** the main flow with a **≥280 px** gap.
- Icon size **78×78** for main services, **65×65** for secondary. `sketch=0` on every icon. Labels 12 px.
- Above ~12 icons, split into pages (see Multi-page).

## Canvas and title

```xml
<mxGraphModel dx="2800" dy="1600" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="2400" pageHeight="1400" math="0" shadow="0">
```

First element after the root cells: a full-canvas background (prevents black PNG backgrounds), then a title block.

```xml
<mxCell id="bg" value="" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#F5F5F5;strokeColor=none;" vertex="1" parent="1">
  <mxGeometry x="0" y="0" width="2400" height="1400" as="geometry" />
</mxCell>
<mxCell id="title" value="&lt;b&gt;Diagram Title&lt;/b&gt;&lt;br&gt;Author | Date | Version" style="text;html=1;align=left;verticalAlign=top;whiteSpace=wrap;rounded=0;fontSize=14;spacing=8;" vertex="1" parent="1">
  <mxGeometry x="40" y="30" width="420" height="60" as="geometry" />
</mxCell>
```

## Edges

Base style for every edge:

```
edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=2;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;
```

- Every edge has `source` and `target` and a child `<mxGeometry relative="1" as="geometry" />`.
- Labels: 1–2 words. Add `labelBackgroundColor=#F5F5F5;fontSize=11;`. Horizontal edges: `verticalAlign=bottom;`
  (label above). Vertical edges: `align=right;`. Unlabeled edge: omit the `value` attribute.
- Routing to a service above/below the flow: exit bottom `exitX=0.5;exitY=1;`, enter top `entryX=0.5;entryY=0;`,
  exit top `exitX=0.5;exitY=0;`, enter bottom `entryX=0.5;entryY=1;`.
- Types: solid black = primary flow; `dashed=1;` = optional/async; `dashed=1;strokeColor=#DD344C;` = error path.
- Do not label an edge when the relationship is obvious (Lambda → DynamoDB needs no "Write").

## Groups

Always `fillColor=none;container=1;dropTarget=1;`. Names and colors come from
[`aws-icons-groups.md`](aws-icons-groups.md) (generated). The common ones:

| Boundary | style fragment |
|---|---|
| AWS Cloud | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_aws_cloud_alt;strokeColor=#232F3E;fontColor=#232F3E;` |
| Region | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_region;strokeColor=#00A4A6;fontColor=#147EBA;dashed=1;` |
| VPC | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc2;strokeColor=#8C4FFF;fontColor=#8C4FFF;` |
| Availability Zone | `fillColor=none;strokeColor=#147EBA;dashed=1;verticalAlign=top;fontStyle=0;fontColor=#147EBA;` (no badge) |
| Private subnet | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;strokeColor=#00A4A6;fontColor=#147EBA;` |
| Public subnet | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;strokeColor=#7AA116;fontColor=#248814;` |
| Security group | `fillColor=none;strokeColor=#DD3522;verticalAlign=top;fontStyle=0;fontColor=#DD3522;` (no badge) |
| AWS Account | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_account;strokeColor=#CD2264;fontColor=#CD2264;` |
| On-premise / corporate DC | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_corporate_data_center;strokeColor=#7D8998;fontColor=#5A6C86;` |
| Logical group | `whiteSpace=wrap;html=1;fillColor=none;dashed=1;dashPattern=8 8;strokeColor=#5A6C86;fontColor=#5A6C86;` |

Common group prefix: `points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=1;verticalAlign=top;align=left;spacingLeft=30;`
Children of a group set `parent="<group id>"` and use coordinates relative to the group.

## Multi-page

```xml
<mxfile host="app.diagrams.net">
  <diagram id="overview" name="Overview">…</diagram>
  <diagram id="network" name="Networking Detail">…</diagram>
</mxfile>
```

Page 1 = service-level overview. Later pages = resource-level detail (subnets, instances, tables).

## Legend

For diagrams with more than one edge type, place a small legend under the title: solid = primary flow,
dashed = optional/async, red dashed = error path.

## Audience mode

Ask "Technical audience or executive/non-technical?" when unclear.

- **Technical**: service names, protocols (HTTPS, gRPC), CIDRs, instance types.
- **Non-technical**: action labels ("Store data", "Notify"), hide implementation detail, number the flow with
  circled digits as edge labels: `value="①"` with `fontSize=14;fontStyle=1;labelBackgroundColor=#ffffff;`.
  Second flow uses ❶ ❷ ❸.

## Companion guide

Next to `name.drawio`, write `name.md`: title, numbered flow matching the edge labels, service list with purpose,
key design decisions.

## Writing the file

- No XML comments (`<!-- -->`) — draw.io's importer rejects them in some paths.
- Escape `&amp; &lt; &gt; &quot;` in values. Unique `id` per cell. Root cells `id="0"` and `id="1" parent="0"`.
- Large diagrams: write in chunks (header + left, middle, right, bottom + close) to stay within tool limits.
- Save as `<descriptive-name>.drawio`. Export via the draw.io CLI (see SKILL.md) as `name.drawio.png` so the
  PNG embeds the XML and stays editable.
````

- [ ] **Step 5: Run the alias tests**

Run: `cd plugins/aws-drawio-diagram && python3 -m pytest tests/test_aliases.py -q`
Expected: 2 passed. If a name is missing, look it up: `python3 -c "import json;i=json.load(open('skills/aws-drawio-diagram/scripts/stencil-index.json'))['stencils'];print([k for k in i if 'opensearch' in k])"` and correct the row.

- [ ] **Step 6: Commit**

```bash
git add plugins/aws-drawio-diagram/skills/aws-drawio-diagram/references/aws-icons-aliases.md plugins/aws-drawio-diagram/skills/aws-drawio-diagram/references/layout-and-style.md plugins/aws-drawio-diagram/tests/test_aliases.py
git commit -m "Add alias table and layout/style reference for aws-drawio-diagram

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 5: Extra icons — delta report, allow list, SVG copy, image-style snippets

**Files:**
- Create: `plugins/aws-drawio-diagram/skills/aws-drawio-diagram/scripts/build_extra_icons.py`
- Create: `plugins/aws-drawio-diagram/skills/aws-drawio-diagram/scripts/extra-icons.txt`
- Create (generated): `plugins/aws-drawio-diagram/skills/aws-drawio-diagram/assets/extra-icons/*.svg`, `references/aws-icons-extra.md`
- Test: `plugins/aws-drawio-diagram/tests/test_build_extra_icons.py`

**Interfaces:**
- Consumes: `scripts/stencil-index.json` (Task 3); official icon dir (default `plugins/aws-diagram-design/skills/aws-diagram-design/assets/aws-icons`, build-time only).
- Produces (Python API):
  - `normalize(filename: str) -> str` — `Arch_Amazon-Bedrock-AgentCore_48.svg` → `bedrock_agentcore`; `Res_AWS-Lambda_Lambda-Function_48.svg` → `lambda_function`
  - `report(icons_dir: Path, index_names: set[str]) -> list[tuple[str, str]]` — `(relative_path, normalized)` for unmatched icons
  - `read_allow_list(path: Path) -> list[tuple[str, str]]` — `(relative_path, display_name)`
  - `image_style(svg_bytes: bytes) -> str` — full style string with `image=data:image/svg+xml,<base64>`
  - `build(icons_dir: Path, allow: list[tuple[str, str]], assets_dir: Path, out_md: Path) -> list[Path]`
- Allow-list format: one `relative/path.svg|Display Name` per line, `#` comments allowed.

- [ ] **Step 1: Write the failing tests**

`plugins/aws-drawio-diagram/tests/test_build_extra_icons.py`:

```python
import base64
import json
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
SKILL = PLUGIN / "skills" / "aws-drawio-diagram"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

import build_extra_icons as bei  # noqa: E402

SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect width="48" height="48" fill="#7B27FF"/></svg>'


def test_normalize():
    assert bei.normalize("Arch_Amazon-Bedrock-AgentCore_48.svg") == "bedrock_agentcore"
    assert bei.normalize("Res_AWS-Lambda_Lambda-Function_48.svg") == "lambda_function"
    assert bei.normalize("Res_Users_48_Light.svg") == "users"
    assert bei.normalize("Arch_Amazon-Simple-Storage-Service_48.svg") == "simple_storage_service"


def test_report_lists_only_unmatched(tmp_path):
    (tmp_path / "service").mkdir()
    (tmp_path / "service" / "Arch_AWS-Lambda_48.svg").write_bytes(SVG)
    (tmp_path / "service" / "Arch_Amazon-Made-Up_48.svg").write_bytes(SVG)
    out = bei.report(tmp_path, {"lambda"})
    assert out == [("service/Arch_Amazon-Made-Up_48.svg", "made_up")]


def test_image_style_has_no_semicolon_inside_data_uri():
    style = bei.image_style(SVG)
    assert style.startswith("shape=image;")
    assert "image=data:image/svg+xml," in style
    assert ";base64" not in style
    b64 = style.split("image=data:image/svg+xml,")[1].rstrip(";")
    assert base64.b64decode(b64) == SVG


def test_build_copies_and_renders(tmp_path):
    icons = tmp_path / "icons" / "resource" / "AI"
    icons.mkdir(parents=True)
    (icons / "Res_Amazon-Bedrock-AgentCore_Memory_48.svg").write_bytes(SVG)
    allow = [("resource/AI/Res_Amazon-Bedrock-AgentCore_Memory_48.svg", "AgentCore Memory")]
    assets = tmp_path / "assets"
    md = tmp_path / "aws-icons-extra.md"
    written = bei.build(tmp_path / "icons", allow, assets, md)
    assert (assets / "Res_Amazon-Bedrock-AgentCore_Memory_48.svg").read_bytes() == SVG
    text = md.read_text()
    assert "Do not edit by hand" in text
    assert "### AgentCore Memory" in text
    assert "shape=image;" in text and ";base64" not in text
    assert md in written


def test_read_allow_list(tmp_path):
    f = tmp_path / "extra-icons.txt"
    f.write_text("# comment\nresource/a/X_48.svg|X Thing\n\nresource/b/Y_48.svg | Y\n")
    assert bei.read_allow_list(f) == [("resource/a/X_48.svg", "X Thing"), ("resource/b/Y_48.svg", "Y")]


def test_shipped_extra_md_matches_allow_list():
    allow = bei.read_allow_list(SCRIPTS / "extra-icons.txt")
    assert len(allow) >= 11
    text = (SKILL / "references" / "aws-icons-extra.md").read_text()
    for rel, name in allow:
        assert f"### {name}" in text
        assert (SKILL / "assets" / "extra-icons" / Path(rel).name).exists()
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd plugins/aws-drawio-diagram && python3 -m pytest tests/test_build_extra_icons.py -q`
Expected: `ModuleNotFoundError: build_extra_icons`.

- [ ] **Step 3: Write the script**

`plugins/aws-drawio-diagram/skills/aws-drawio-diagram/scripts/build_extra_icons.py`:

```python
#!/usr/bin/env python3
"""Ship official AWS icons that draw.io has no stencil for, as draw.io image styles.

  build_extra_icons.py --report [--icons DIR]   list official-pack icons with no matching stencil name
  build_extra_icons.py [--icons DIR]            copy allow-listed SVGs to assets/extra-icons/ and
                                                write references/aws-icons-extra.md

The report is a heuristic (file-name normalization vs stencil names) — review it, then add the icons you
want to scripts/extra-icons.txt as "relative/path.svg|Display Name". Only the allow list is shipped.

Default --icons is the sibling aws-diagram-design plugin's official icon pack (build-time only; nothing in
the shipped skill points there).
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_DIR = HERE.parent
PLUGIN_DIR = SKILL_DIR.parents[1]
DEFAULT_ICONS = PLUGIN_DIR.parent / "aws-diagram-design" / "skills" / "aws-diagram-design" / "assets" / "aws-icons"
INDEX = HERE / "stencil-index.json"
ALLOW_LIST = HERE / "extra-icons.txt"
ASSETS = SKILL_DIR / "assets" / "extra-icons"
OUT_MD = SKILL_DIR / "references" / "aws-icons-extra.md"

GENERATED_NOTE = ("> Generated by `scripts/build_extra_icons.py` from `scripts/extra-icons.txt`. "
                  "Do not edit by hand — edit the allow list and rerun.")

_PREFIX = re.compile(r"^(Arch_|Res_|Arch-Category_)")
_SUFFIX = re.compile(r"(_48|_32|_64|_16)?(_Light|_Dark)?\.svg$")
_VENDOR = re.compile(r"^(amazon|aws)[-_]")


def normalize(filename: str) -> str:
    """Official-pack file name -> draw.io-ish stencil name.

    Res_ files are "<Service>_<Resource>"; the resource part alone is what draw.io usually names.
    """
    stem = _SUFFIX.sub("", _PREFIX.sub("", filename))
    if filename.startswith("Res_") and "_" in stem:
        stem = stem.split("_", 1)[1]
    name = re.sub(r"[^a-z0-9]+", "_", stem.lower()).strip("_")
    return _VENDOR.sub("", name)


def _index_names() -> set[str]:
    data = json.loads(INDEX.read_text())
    return set(data["stencils"]) | set(data["js_shapes"])


def report(icons_dir: Path, index_names: set[str]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for svg in sorted(icons_dir.rglob("*.svg")):
        norm = normalize(svg.name)
        candidates = {norm, f"amazon_{norm}", f"aws_{norm}", norm.replace("_", "")}
        if candidates & index_names:
            continue
        out.append((svg.relative_to(icons_dir).as_posix(), norm))
    return out


def read_allow_list(path: Path) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        rel, _, name = line.partition("|")
        rows.append((rel.strip(), name.strip() or Path(rel.strip()).stem))
    return rows


def image_style(svg_bytes: bytes) -> str:
    # draw.io stores data URIs in cell styles WITHOUT ";base64" because ";" separates style keys.
    b64 = base64.b64encode(svg_bytes).decode("ascii")
    return ("shape=image;aspect=fixed;imageAspect=0;verticalLabelPosition=bottom;verticalAlign=top;"
            "align=center;html=1;fontSize=12;fontColor=#232F3E;sketch=0;"
            f"image=data:image/svg+xml,{b64};")


def build(icons_dir: Path, allow: list[tuple[str, str]], assets_dir: Path, out_md: Path) -> list[Path]:
    assets_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    parts = ["# AWS Icons: Extra (image fallback for icons draw.io lacks)", "", GENERATED_NOTE, "",
             "These official-pack icons have no `mxgraph.aws4` stencil. Use the full style below on a 78×78 "
             "vertex. They are plain images: no `resIcon`, no `strokeColor` rule applies. The SVG files live "
             "in `assets/extra-icons/` for reference; the style already embeds them.", ""]
    for rel, name in allow:
        src = icons_dir / rel
        if not src.exists():
            sys.exit(f"allow-listed icon not found: {src}")
        dst = assets_dir / src.name
        shutil.copyfile(src, dst)
        written.append(dst)
        parts += [f"### {name}", "", f"File: `assets/extra-icons/{src.name}`", "", "```",
                  image_style(src.read_bytes()), "```", ""]
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(parts).rstrip() + "\n")
    written.append(out_md)
    return written


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--icons", type=Path, default=DEFAULT_ICONS)
    ap.add_argument("--list", type=Path, default=ALLOW_LIST)
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args(argv)
    if not args.icons.is_dir():
        print(f"icon directory not found: {args.icons}", file=sys.stderr)
        return 1
    if args.report:
        for rel, norm in report(args.icons, _index_names()):
            print(f"{norm:50s} {rel}")
        return 0
    files = build(args.icons, read_allow_list(args.list), ASSETS, OUT_MD)
    print(f"wrote {len(files) - 1} icons and {OUT_MD.relative_to(SKILL_DIR)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Write the allow list**

`plugins/aws-drawio-diagram/skills/aws-drawio-diagram/scripts/extra-icons.txt`:

```
# Official-pack icons with no draw.io stencil. Format: relative/path.svg|Display Name
# Paths are relative to the --icons directory (default: sibling aws-diagram-design plugin's assets/aws-icons).
# Amazon Bedrock AgentCore resource icons — traced from PNG artwork, NOT from the official package
# (see THIRD_PARTY_LICENSES.md). draw.io ships only the service icon `bedrock_agentcore`.
resource/Artificial-Intelligence/Res_Amazon-Bedrock-AgentCore_AgentCore_48.svg|AgentCore (resource)
resource/Artificial-Intelligence/Res_Amazon-Bedrock-AgentCore_AI-Agent_48.svg|AgentCore AI Agent
resource/Artificial-Intelligence/Res_Amazon-Bedrock-AgentCore_Runtime_48.svg|AgentCore Runtime
resource/Artificial-Intelligence/Res_Amazon-Bedrock-AgentCore_Gateway_48.svg|AgentCore Gateway
resource/Artificial-Intelligence/Res_Amazon-Bedrock-AgentCore_Memory_48.svg|AgentCore Memory
resource/Artificial-Intelligence/Res_Amazon-Bedrock-AgentCore_Identity_48.svg|AgentCore Identity
resource/Artificial-Intelligence/Res_Amazon-Bedrock-AgentCore_Observability_48.svg|AgentCore Observability
resource/Artificial-Intelligence/Res_Amazon-Bedrock-AgentCore_Policy-Engine_48.svg|AgentCore Policy Engine
resource/Artificial-Intelligence/Res_Amazon-Bedrock-AgentCore_Evaluations_48.svg|AgentCore Evaluations
resource/Artificial-Intelligence/Res_Amazon-Bedrock-AgentCore_Browser-Tool_48.svg|AgentCore Browser Tool
resource/Artificial-Intelligence/Res_Amazon-Bedrock-AgentCore_Code-Interpreter_48.svg|AgentCore Code Interpreter
```

- [ ] **Step 5: Run the report, extend the allow list only with clear wins**

Run: `python3 plugins/aws-drawio-diagram/skills/aws-drawio-diagram/scripts/build_extra_icons.py --report | head -80`

Skim the output. Add a row to `extra-icons.txt` only when (a) the icon is a real AWS service or resource an architect would place on a diagram, and (b) a search of `stencil-index.json` for two or three keywords from the name finds nothing. Expect most report rows to be false positives caused by naming differences (e.g. `simple_storage_service` vs `s3`); leave those out. Record the rows you rejected and why in the commit message body.

- [ ] **Step 6: Build the shipped assets and markdown**

Run: `python3 plugins/aws-drawio-diagram/skills/aws-drawio-diagram/scripts/build_extra_icons.py`
Expected: `wrote 11 icons and references/aws-icons-extra.md` (or more if you added rows).

- [ ] **Step 7: Run the tests**

Run: `cd plugins/aws-drawio-diagram && python3 -m pytest tests/test_build_extra_icons.py -q`
Expected: 6 passed.

- [ ] **Step 8: Commit**

```bash
git add plugins/aws-drawio-diagram/skills/aws-drawio-diagram/scripts/build_extra_icons.py plugins/aws-drawio-diagram/skills/aws-drawio-diagram/scripts/extra-icons.txt plugins/aws-drawio-diagram/skills/aws-drawio-diagram/assets plugins/aws-drawio-diagram/skills/aws-drawio-diagram/references/aws-icons-extra.md plugins/aws-drawio-diagram/tests/test_build_extra_icons.py
git commit -m "Ship AgentCore resource icons as draw.io image-style fallbacks

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 6: Validator

**Files:**
- Create: `plugins/aws-drawio-diagram/skills/aws-drawio-diagram/scripts/validate_drawio.py`
- Test: `plugins/aws-drawio-diagram/tests/test_validate_drawio.py`

**Interfaces:**
- Consumes: `scripts/stencil-index.json` (Task 3), templates (Task 1).
- Produces (Python API): `validate_text(xml_text: str, index: dict) -> tuple[list[str], list[str]]` (errors, warnings); `validate_file(path: Path, index: dict) -> tuple[list[str], list[str]]`; `load_index(path: Path = INDEX) -> dict` returning `{"names": set[str], "js_shapes": set[str]}`; CLI `validate_drawio.py FILE...` exits 1 on any error.
- Error/warning codes are prefixes: `E1` unknown stencil, `E2` wrong strokeColor for pattern, `E3` bad edge endpoints, `E4` group missing container=1, `E5` duplicate id, `E6` XML comment or compressed diagram, `W1` orthogonal edge without exit/entry, `W2` icon without fillColor, `W3` group without dropTarget.

- [ ] **Step 1: Write the failing tests**

`plugins/aws-drawio-diagram/tests/test_validate_drawio.py`:

```python
import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[1]
SKILL = PLUGIN / "skills" / "aws-drawio-diagram"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

import validate_drawio as vd  # noqa: E402

INDEX = vd.load_index()


def wrap(cells: str) -> str:
    return f"""<mxfile><diagram id="d" name="P"><mxGraphModel><root>
<mxCell id="0"/><mxCell id="1" parent="0"/>
{cells}
</root></mxGraphModel></diagram></mxfile>"""


SERVICE_OK = '<mxCell id="a" value="Lambda" style="sketch=0;fillColor=#ED7100;strokeColor=#ffffff;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.lambda;" vertex="1" parent="1"><mxGeometry x="0" y="0" width="78" height="78" as="geometry"/></mxCell>'
RESOURCE_OK = '<mxCell id="b" value="Fn" style="sketch=0;fillColor=#ED7100;strokeColor=none;shape=mxgraph.aws4.lambda_function;" vertex="1" parent="1"><mxGeometry x="300" y="0" width="78" height="78" as="geometry"/></mxCell>'
EDGE_OK = '<mxCell id="e" style="edgeStyle=orthogonalEdgeStyle;strokeWidth=2;exitX=1;exitY=0.5;entryX=0;entryY=0.5;" edge="1" source="a" target="b" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>'


def codes(msgs):
    return sorted({m.split()[0] for m in msgs})


def test_clean_minimal_diagram_passes():
    errors, warnings = vd.validate_text(wrap(SERVICE_OK + RESOURCE_OK + EDGE_OK), INDEX)
    assert errors == [] and warnings == []


def test_unknown_stencil_is_error():
    bad = SERVICE_OK.replace("aws4.lambda;", "aws4.lambda_supreme;")
    errors, _ = vd.validate_text(wrap(bad), INDEX)
    assert codes(errors) == ["E1"] and "lambda_supreme" in errors[0]


def test_vidanov_broken_names_are_caught():
    bad = RESOURCE_OK.replace("lambda_function", "vpc_peering")
    errors, _ = vd.validate_text(wrap(bad), INDEX)
    assert codes(errors) == ["E1"]


def test_service_with_stroke_none_is_error():
    bad = SERVICE_OK.replace("strokeColor=#ffffff", "strokeColor=none")
    errors, _ = vd.validate_text(wrap(bad), INDEX)
    assert codes(errors) == ["E2"]


def test_resource_with_white_stroke_is_error():
    bad = RESOURCE_OK.replace("strokeColor=none", "strokeColor=#ffffff")
    errors, _ = vd.validate_text(wrap(bad), INDEX)
    assert codes(errors) == ["E2"]


def test_product_icon_counts_as_service_level():
    ok = SERVICE_OK.replace("resourceIcon;resIcon=", "productIcon;prIcon=")
    errors, _ = vd.validate_text(wrap(ok), INDEX)
    assert errors == []


def test_legacy_group_vpc_badge_is_accepted_and_group_needs_container():
    grp = ('<mxCell id="g" value="VPC" style="shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc;'
           'strokeColor=#8C4FFF;fillColor=none;" vertex="1" parent="1"><mxGeometry x="0" y="0" width="400" height="300" as="geometry"/></mxCell>')
    errors, warnings = vd.validate_text(wrap(grp), INDEX)
    assert codes(errors) == ["E4"]
    fixed = grp.replace("fillColor=none;", "fillColor=none;container=1;")
    errors, warnings = vd.validate_text(wrap(fixed), INDEX)
    assert errors == [] and codes(warnings) == ["W3"]


def test_edge_endpoint_and_orthogonal_warning():
    dangling = EDGE_OK.replace('target="b"', 'target="zzz"')
    errors, _ = vd.validate_text(wrap(SERVICE_OK + RESOURCE_OK + dangling), INDEX)
    assert codes(errors) == ["E3"]
    no_ports = EDGE_OK.replace("exitX=1;exitY=0.5;entryX=0;entryY=0.5;", "")
    errors, warnings = vd.validate_text(wrap(SERVICE_OK + RESOURCE_OK + no_ports), INDEX)
    assert errors == [] and codes(warnings) == ["W1"]
    iso = no_ports.replace("orthogonalEdgeStyle", "isometricEdgeStyle")
    errors, warnings = vd.validate_text(wrap(SERVICE_OK + RESOURCE_OK + iso), INDEX)
    assert errors == [] and warnings == []


def test_duplicate_id_comment_and_compressed():
    errors, _ = vd.validate_text(wrap(SERVICE_OK + SERVICE_OK), INDEX)
    assert "E5" in codes(errors)
    errors, _ = vd.validate_text(wrap("<!-- note -->" + SERVICE_OK), INDEX)
    assert codes(errors) == ["E6"]
    compressed = '<mxfile><diagram id="d" name="P">eJxTKM5ILEhVAAA=</diagram></mxfile>'
    errors, _ = vd.validate_text(compressed, INDEX)
    assert codes(errors) == ["E6"]
    xxe = '<!DOCTYPE x [<!ENTITY e SYSTEM "file:///etc/passwd">]>' + wrap(SERVICE_OK)
    errors, _ = vd.validate_text(xxe, INDEX)
    assert codes(errors) == ["E6"]


def test_missing_fill_is_warning():
    nofill = SERVICE_OK.replace("fillColor=#ED7100;", "")
    errors, warnings = vd.validate_text(wrap(nofill), INDEX)
    assert errors == [] and codes(warnings) == ["W2"]


@pytest.mark.parametrize("tpl", sorted((SKILL / "templates").glob("*.drawio")), ids=lambda p: p.name)
def test_shipped_templates_have_no_errors(tpl):
    errors, _ = vd.validate_file(tpl, INDEX)
    assert errors == []


def test_cli_exit_codes(tmp_path):
    good = tmp_path / "good.drawio"
    good.write_text(wrap(SERVICE_OK + RESOURCE_OK + EDGE_OK))
    bad = tmp_path / "bad.drawio"
    bad.write_text(wrap(SERVICE_OK.replace("strokeColor=#ffffff", "strokeColor=none")))
    ok = subprocess.run([sys.executable, str(SCRIPTS / "validate_drawio.py"), str(good)], capture_output=True, text=True)
    assert ok.returncode == 0 and "0 errors" in ok.stdout
    ko = subprocess.run([sys.executable, str(SCRIPTS / "validate_drawio.py"), str(bad)], capture_output=True, text=True)
    assert ko.returncode == 1 and "E2" in ko.stdout
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd plugins/aws-drawio-diagram && python3 -m pytest tests/test_validate_drawio.py -q`
Expected: `ModuleNotFoundError: validate_drawio`.

- [ ] **Step 3: Write the validator**

`plugins/aws-drawio-diagram/skills/aws-drawio-diagram/scripts/validate_drawio.py`:

```python
#!/usr/bin/env python3
"""Validate .drawio files produced by the aws-drawio-diagram skill.

Errors (exit 1):
  E1  mxgraph.aws4 name (shape / resIcon / prIcon / grIcon) not in stencil-index.json
  E2  service-level icon (resourceIcon/productIcon) without strokeColor=#ffffff,
      or resource-level stencil without strokeColor=none
  E3  edge without source/target, or pointing at a missing cell
  E4  group container (shape=mxgraph.aws4.group*) without container=1
  E5  duplicate cell id
  E6  XML comment, DOCTYPE/ENTITY declaration, or compressed <diagram> payload
Warnings:
  W1  orthogonalEdgeStyle edge without exitX/entryX (routing may wander)
  W2  aws4 icon without fillColor (renders white in PNG export)
  W3  group container without dropTarget=1

Usage: validate_drawio.py FILE [FILE ...]
Adapted from vidanov/aws-architecture-diagram-skill tests/validate_drawio.py (MIT).
"""
from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
INDEX = HERE / "stencil-index.json"

SERVICE_FRAMES = {"resourceIcon", "productIcon"}
GROUP_SHAPES = {"group", "group2", "groupCenter"}
RE_AWS4 = re.compile(r"mxgraph\.aws4\.([A-Za-z0-9_]+)")


def load_index(path: Path = INDEX) -> dict:
    data = json.loads(path.read_text())
    return {"names": set(data["stencils"]), "js_shapes": set(data["js_shapes"])}


def parse_style(style: str | None) -> dict[str, str]:
    out: dict[str, str] = {}
    for part in (style or "").split(";"):
        if not part:
            continue
        k, _, v = part.partition("=")
        out[k] = v
    return out


def _aws4_name(value: str) -> str | None:
    m = RE_AWS4.search(value or "")
    return m.group(1) if m else None


def validate_text(xml_text: str, index: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    known = index["names"] | index["js_shapes"]

    if "<!--" in xml_text:
        errors.append("E6 XML comment found — remove all <!-- --> blocks")
    if re.search(r"<!(DOCTYPE|ENTITY)", xml_text, re.I):
        # draw.io never writes these; refusing them keeps stdlib ElementTree safe from XXE/billion-laughs.
        errors.append("E6 DOCTYPE/ENTITY declaration found — not a draw.io file")
        return errors, warnings
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        return [f"E6 XML parse error: {exc}"], warnings

    for diagram in root.iter("diagram"):
        if diagram.find("mxGraphModel") is None and (diagram.text or "").strip():
            errors.append(f"E6 diagram '{diagram.get('name', diagram.get('id'))}' is compressed — "
                          "write plain <mxGraphModel> XML")
    if errors:
        return errors, warnings

    cells: dict[str, ET.Element] = {}
    for cell in root.iter("mxCell"):
        cid = cell.get("id")
        if cid is None:
            continue
        if cid in cells:
            errors.append(f"E5 duplicate cell id '{cid}'")
        cells[cid] = cell

    for cid, cell in cells.items():
        style = parse_style(cell.get("style"))
        shape = _aws4_name(style.get("shape", ""))
        if shape is None:
            continue
        res = _aws4_name(style.get("resIcon", "")) or _aws4_name(style.get("prIcon", ""))
        gr = _aws4_name(style.get("grIcon", ""))
        stroke = style.get("strokeColor", "")
        for name in (shape, res, gr):
            if name and name not in known:
                errors.append(f"E1 cell '{cid}': unknown stencil 'mxgraph.aws4.{name}' — look it up in references/")
        if shape in SERVICE_FRAMES:
            if stroke.lower() != "#ffffff":
                errors.append(f"E2 cell '{cid}': service-level icon needs strokeColor=#ffffff (has '{stroke or 'unset'}')")
            if not style.get("fillColor"):
                warnings.append(f"W2 cell '{cid}': icon has no fillColor — renders white in PNG export")
        elif shape in GROUP_SHAPES:
            if style.get("container") != "1":
                errors.append(f"E4 cell '{cid}': group needs container=1")
            if style.get("dropTarget") != "1":
                warnings.append(f"W3 cell '{cid}': group should set dropTarget=1")
        else:
            if stroke != "none":
                errors.append(f"E2 cell '{cid}': resource-level stencil needs strokeColor=none (has '{stroke or 'unset'}')")
            if not style.get("fillColor"):
                warnings.append(f"W2 cell '{cid}': icon has no fillColor — renders white in PNG export")

    for cid, cell in cells.items():
        if cell.get("edge") != "1":
            continue
        for end in ("source", "target"):
            ref = cell.get(end)
            if not ref:
                errors.append(f"E3 edge '{cid}': missing {end}")
            elif ref not in cells:
                errors.append(f"E3 edge '{cid}': {end}='{ref}' does not exist")
        style = parse_style(cell.get("style"))
        if style.get("edgeStyle") == "orthogonalEdgeStyle" and "exitX" not in style and "entryX" not in style:
            warnings.append(f"W1 edge '{cid}': no exitX/entryX — set explicit ports so routing stays clean")

    return errors, warnings


def validate_file(path: Path, index: dict) -> tuple[list[str], list[str]]:
    return validate_text(path.read_text(encoding="utf-8"), index)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print(__doc__)
        return 2
    index = load_index()
    total_e = total_w = 0
    for f in map(Path, args):
        errors, warnings = validate_file(f, index)
        total_e += len(errors)
        total_w += len(warnings)
        print(f"== {f}")
        for e in errors:
            print(f"  ERROR {e}")
        for w in warnings:
            print(f"  warn  {w}")
        if not errors and not warnings:
            print("  ok")
    print(f"Summary: {total_e} errors, {total_w} warnings in {len(args)} file(s)")
    return 1 if total_e else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests**

Run: `cd plugins/aws-drawio-diagram && python3 -m pytest tests/test_validate_drawio.py -q`
Expected: all pass. If a shipped template fails `E2`/`E4`, fix the template's style (these are upstream bugs we are correcting); if it fails `E1`, the name is unknown to draw.io — replace it with the closest name from `references/` and note the change in the commit body.

- [ ] **Step 5: Commit**

```bash
git add plugins/aws-drawio-diagram/skills/aws-drawio-diagram/scripts/validate_drawio.py plugins/aws-drawio-diagram/tests/test_validate_drawio.py plugins/aws-drawio-diagram/skills/aws-drawio-diagram/templates
git commit -m "Add draw.io validator with stencil-index and two-pattern strokeColor checks

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 7: SKILL.md

**Files:**
- Create: `plugins/aws-drawio-diagram/skills/aws-drawio-diagram/SKILL.md`
- Test: `plugins/aws-drawio-diagram/tests/test_skill_md.py`

**Interfaces:**
- Consumes: every reference file name from Tasks 3–5, `scripts/validate_drawio.py` (Task 6).

- [ ] **Step 1: Write the failing test**

`plugins/aws-drawio-diagram/tests/test_skill_md.py`:

```python
import re
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
SKILL = PLUGIN / "skills" / "aws-drawio-diagram"
SKILL_MD = SKILL / "SKILL.md"


def test_frontmatter():
    text = SKILL_MD.read_text()
    fm = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert fm, "missing frontmatter"
    assert "name: aws-drawio-diagram" in fm.group(1)
    assert "draw.io로" in fm.group(1) and "드로우아이오" in fm.group(1)
    assert "aws-diagram-design" in fm.group(1)


def test_every_linked_reference_exists():
    text = SKILL_MD.read_text()
    links = set(re.findall(r"\]\((references/[^)#]+|scripts/[^)#]+|templates/[^)#]+)\)", text))
    assert links, "SKILL.md should link its references"
    missing = sorted(l for l in links if not (SKILL / l).exists())
    assert missing == []


def test_mentions_validator_and_lookup_order():
    text = SKILL_MD.read_text()
    assert "scripts/validate_drawio.py" in text
    assert "aws-icons-aliases.md" in text and "aws-icons-extra.md" in text
    assert "aws3d" not in text.lower()
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd plugins/aws-drawio-diagram && python3 -m pytest tests/test_skill_md.py -q`
Expected: FileNotFoundError.

- [ ] **Step 3: Write SKILL.md**

`plugins/aws-drawio-diagram/skills/aws-drawio-diagram/SKILL.md`:

````markdown
---
name: aws-drawio-diagram
description: "Generate editable AWS architecture diagrams as draw.io (.drawio) XML using draw.io's built-in official AWS icon stencils, with an optional PNG/SVG/PDF export that keeps the XML embedded. Use when the user asks for a draw.io / diagrams.net file, an editable diagram, or says 'drawio'. Korean triggers: draw.io로 그려줘, 드로우아이오, 편집 가능한 구성도, drawio 파일로 만들어줘. Not for HTML/SVG/PNG editorial diagrams — use the aws-diagram-design skill for those; use this one when the output must be opened and edited in draw.io."
license: MIT
metadata:
  version: "1.0.0"
  base: "vidanov/aws-architecture-diagram-skill 29c1bab (MIT) + regenerated stencil catalog, validator, image fallbacks"
  source: "https://github.com/hi-space/hi-aws-skills"
---

# AWS draw.io Diagram

Produce a `.drawio` file whose every icon renders, because every stencil name comes from a catalog generated from
draw.io's own sources — never from memory.

## Procedure

1. **Clarify** only what changes the drawing: audience (technical vs executive), rough service list, whether the
   user wants a PNG too. One question at most.
2. **Read** [`references/layout-and-style.md`](references/layout-and-style.md) once. It holds the canvas, edge,
   group, multi-page, and audience rules.
3. **Look up every icon** (see *Icon lookup*). Write the names down before writing XML.
4. **Write the XML** with the Write tool to `<descriptive-name>.drawio`. Large diagrams: write in chunks.
5. **Validate**: run `python3 <skill-dir>/scripts/validate_drawio.py <file>.drawio`. Fix every `ERROR`, then rerun.
   Treat `warn` lines as suggestions.
6. **Export** if asked (see *Export*), then open or print the path.
7. **Companion guide**: write `<name>.md` next to the file (title, numbered flow, services, decisions).

`<skill-dir>` is the directory containing this SKILL.md. Locate it with the plugin root you were installed from;
do not assume it is under the current working directory.

## Two icon patterns — the rule that decides whether icons render

| Pattern | Style | strokeColor | Use for |
|---|---|---|---|
| **Service-level** | `shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.<name>;` | **`#ffffff`** (required) | A named service as a node: colored square + white glyph |
| **Resource-level** | `shape=mxgraph.aws4.<name>;` | **`none`** (required) | Sub-resources and generic marks: colored silhouette |
| Group | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.<group_name>;` | category color | Boundary box with a corner badge |

Swap the strokeColor rules and the glyph disappears or the shape breaks. Every service-level icon also needs the
category `fillColor` (it is in the reference file header). Standard vertex:

```xml
<mxCell id="lambda1" value="Order Handler" style="sketch=0;points=[[0,0,0],[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0,0],[0,1,0],[0.25,1,0],[0.5,1,0],[0.75,1,0],[1,1,0],[0,0.25,0],[0,0.5,0],[0,0.75,0],[1,0.25,0],[1,0.5,0],[1,0.75,0]];outlineConnect=0;fontColor=#232F3E;fillColor=#ED7100;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.lambda;" vertex="1" parent="1">
  <mxGeometry x="600" y="300" width="78" height="78" as="geometry" />
</mxCell>
```

## Icon lookup (in this order — never guess a name)

1. **Category file** in `references/` — generated from draw.io, one per palette:
   [`aws-icons-compute.md`](references/aws-icons-compute.md), [`aws-icons-containers.md`](references/aws-icons-containers.md),
   [`aws-icons-database.md`](references/aws-icons-database.md), [`aws-icons-storage.md`](references/aws-icons-storage.md),
   [`aws-icons-network-content-delivery.md`](references/aws-icons-network-content-delivery.md),
   [`aws-icons-application-integration.md`](references/aws-icons-application-integration.md),
   [`aws-icons-security-identity-compliance.md`](references/aws-icons-security-identity-compliance.md),
   [`aws-icons-analytics.md`](references/aws-icons-analytics.md), [`aws-icons-artificial-intelligence.md`](references/aws-icons-artificial-intelligence.md),
   [`aws-icons-management-governance.md`](references/aws-icons-management-governance.md), [`aws-icons-developer-tools.md`](references/aws-icons-developer-tools.md),
   [`aws-icons-internet-of-things.md`](references/aws-icons-internet-of-things.md), [`aws-icons-migration-modernization.md`](references/aws-icons-migration-modernization.md),
   [`aws-icons-front-end-web-mobile.md`](references/aws-icons-front-end-web-mobile.md), [`aws-icons-media-services.md`](references/aws-icons-media-services.md),
   [`aws-icons-general.md`](references/aws-icons-general.md) (users, client, internet, documents), [`aws-icons-groups.md`](references/aws-icons-groups.md).
   Other categories follow the same `aws-icons-<category>.md` naming; `ls <skill-dir>/references/` lists them.
2. **Renamed service?** [`aws-icons-aliases.md`](references/aws-icons-aliases.md) — OpenSearch is `elasticsearch_service`,
   CloudWatch is `cloudwatch_2`, QuickSight is `quick_suite`, and so on.
3. **Still nothing?** [`aws-icons-legacy.md`](references/aws-icons-legacy.md) (renders, not in the palette) and
   [`aws-icons-retired.md`](references/aws-icons-retired.md).
4. **draw.io has no stencil at all** (Bedrock AgentCore Runtime, Gateway, Memory, …):
   [`aws-icons-extra.md`](references/aws-icons-extra.md) gives a ready `shape=image;…` style with the official SVG embedded.
5. **Not there either**: use the parent service icon, label the node with the resource name, and tell the user which
   icon was substituted. Do not invent a stencil name.

Quick grep when a name is on the tip of your tongue: `grep -ri "opensearch" <skill-dir>/references/aws-icons-*.md`.

## Templates

Start from [`templates/`](templates/README.md) when the request matches: `serverless-rest-api`, `event-driven-processing`,
`static-website`, `three-tier-web-app`, `vpc-networking`. Copy, rename ids and labels, keep the styles.

## Export

The exported file uses a double extension so the PNG keeps the XML and reopens in draw.io.

```bash
# Linux (drawio CLI on PATH). Headless servers need xvfb: prefix with `xvfb-run -a`.
drawio --no-sandbox -x -f png -e -b 10 -o name.drawio.png name.drawio
# macOS
/Applications/draw.io.app/Contents/MacOS/draw.io -x -f png -e -b 10 -o name.drawio.png name.drawio
```

`-f svg` / `-f pdf` work the same way. If no CLI is available, say so and point to https://app.diagrams.net
(File → Import). Never claim a PNG was produced without the file existing.

## Validation checklist (the script enforces most of these)

- Every `resIcon` / `prIcon` / `grIcon` / `shape=mxgraph.aws4.*` name exists in the references (`E1`).
- Service-level `strokeColor=#ffffff`; resource-level `strokeColor=none` (`E2`).
- Every edge has `source`, `target`, and `<mxGeometry relative="1" as="geometry" />` (`E3`).
- Groups carry `container=1` (`E4`); children reference the group as `parent`.
- Unique ids, no XML comments, uncompressed XML (`E5`, `E6`).
- A `#F5F5F5` background rectangle is the first vertex; a title block follows.

## Related skill

For an editorial HTML/SVG/PNG rendering (docs, slides, blog), or to **redraw** an existing `.drawio` in a house style,
use `aws-diagram-design`. This skill is for producing the editable `.drawio` itself.
````

- [ ] **Step 4: Run the test**

Run: `cd plugins/aws-drawio-diagram && python3 -m pytest tests/test_skill_md.py -q`
Expected: 3 passed. If `test_every_linked_reference_exists` lists a file, check `ls skills/aws-drawio-diagram/references/` — the slug must match what `build_icon_catalog.py` produced (for example `aws-icons-network-content-delivery.md`, `aws-icons-security-identity-compliance.md`). Fix the link, not the generator.

- [ ] **Step 5: Commit**

```bash
git add plugins/aws-drawio-diagram/skills/aws-drawio-diagram/SKILL.md plugins/aws-drawio-diagram/tests/test_skill_md.py
git commit -m "Write aws-drawio-diagram SKILL.md with lookup order and validation loop

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 8: Docs, licenses, marketplace registration

**Files:**
- Create: `plugins/aws-drawio-diagram/README.md`, `plugins/aws-drawio-diagram/README.en.md`, `plugins/aws-drawio-diagram/THIRD_PARTY_LICENSES.md`
- Modify: `.claude-plugin/marketplace.json` (add second plugin entry)
- Modify: `README.md` (root; add table row + role note)
- Test: `plugins/aws-drawio-diagram/tests/test_scaffold.py` (extend)

- [ ] **Step 1: Extend the scaffold test**

Append to `plugins/aws-drawio-diagram/tests/test_scaffold.py`:

```python
def test_marketplace_registers_plugin():
    root = PLUGIN.parents[1]
    mp = json.loads((root / ".claude-plugin" / "marketplace.json").read_text())
    names = {p["name"]: p for p in mp["plugins"]}
    assert "aws-drawio-diagram" in names
    assert names["aws-drawio-diagram"]["source"] == "./plugins/aws-drawio-diagram"
    assert "aws-drawio-diagram" in (root / "README.md").read_text()


def test_docs_and_licenses_present():
    for f in ("README.md", "README.en.md", "THIRD_PARTY_LICENSES.md", "LICENSE"):
        assert (PLUGIN / f).exists(), f
    tpl = (PLUGIN / "THIRD_PARTY_LICENSES.md").read_text()
    assert "Vidanov" in tpl and "Apache" in tpl and "AgentCore" in tpl
```

Run: `cd plugins/aws-drawio-diagram && python3 -m pytest tests/test_scaffold.py -q` → expected 2 new failures.

- [ ] **Step 2: Register in the marketplace**

Edit `.claude-plugin/marketplace.json` so `plugins` reads:

```json
  "plugins": [
    {
      "name": "aws-diagram-design",
      "source": "./plugins/aws-diagram-design",
      "description": "AWS-branded editorial diagrams (27 types) as HTML/SVG/PNG with official AWS Architecture Icons and Amazon Ember; draw.io and Mermaid import; Python generator for ko/en PNG sets."
    },
    {
      "name": "aws-drawio-diagram",
      "source": "./plugins/aws-drawio-diagram",
      "description": "Editable AWS architecture diagrams as draw.io (.drawio) XML. Stencil catalog of 1,000+ names regenerated from draw.io sources, two-pattern icon rule, layout conventions, 5 templates, validator, and SVG image fallback for icons draw.io lacks (Bedrock AgentCore resources)."
    }
  ]
```

and update `metadata.description` to: `"hi-space's AWS skills for Claude Code and other Agent Skills runtimes: aws-diagram-design (AWS-branded editorial HTML/SVG/PNG diagrams with a Python generator) and aws-drawio-diagram (editable draw.io diagrams with a verified stencil catalog)."`

- [ ] **Step 3: Update the root README**

In `README.md` (root), replace the skills table with:

```markdown
| 스킬 | 하는 일 | 문서 |
|---|---|---|
| [aws-diagram-design](plugins/aws-diagram-design/) | 공식 AWS Architecture Icons + Amazon Ember 스킨의 에디토리얼 다이어그램 27종을 HTML/SVG/PNG로 생성. draw.io·Mermaid 재작도. `scripts/pygen` Python 생성기로 한 레이아웃에서 ko/en PNG 세트를 일괄 생성 | [README](plugins/aws-diagram-design/README.md) · [SKILL.md](plugins/aws-diagram-design/skills/aws-diagram-design/SKILL.md) |
| [aws-drawio-diagram](plugins/aws-drawio-diagram/) | **편집 가능한 `.drawio` 파일**을 생성. draw.io 소스에서 재생성한 스텐실 카탈로그(1,000개+), 서비스/리소스 두 패턴 규칙, 레이아웃 관례, 템플릿 5종, 검증 스크립트, draw.io에 없는 아이콘(Bedrock AgentCore 리소스)의 SVG 폴백 | [README](plugins/aws-drawio-diagram/README.md) · [SKILL.md](plugins/aws-drawio-diagram/skills/aws-drawio-diagram/SKILL.md) |

**어느 쪽을 쓸까?** 문서·슬라이드·블로그에 넣을 완성된 그림이면 `aws-diagram-design`, draw.io에서 계속 편집할 `.drawio` 파일이 필요하면 `aws-drawio-diagram`. 기존 `.drawio`를 하우스 스타일로 **재작도**하는 것은 `aws-diagram-design`의 `/aws-diagram-design:import-drawio` 가 담당합니다.
```

Add under the install block a second install line:

```
/plugin install aws-drawio-diagram@hi-aws-skills
```

Add to the standalone-install section:

```bash
ln -s "$PWD/hi-aws-skills/plugins/aws-drawio-diagram/skills/aws-drawio-diagram" ~/.claude/skills/aws-drawio-diagram
```

Add to 출처와 라이선스:

```markdown
`aws-drawio-diagram` 은 [vidanov/aws-architecture-diagram-skill](https://github.com/vidanov/aws-architecture-diagram-skill) (MIT, 커밋 `29c1bab`)을 기반으로, 아이콘 카탈로그를 draw.io 원본(`Sidebar-AWS4.js`, `stencils/aws4.xml`, Apache-2.0)에서 스크립트로 재생성하고 검증 스크립트와 SVG 폴백을 더한 것입니다.
```

- [ ] **Step 4: Write the plugin READMEs**

`plugins/aws-drawio-diagram/README.md`:

````markdown
# AWS draw.io Diagram Skill (aws-drawio-diagram)

> [vidanov/aws-architecture-diagram-skill](https://github.com/vidanov/aws-architecture-diagram-skill) (MIT) 을 기반으로 [hi-aws-skills](https://github.com/hi-space/hi-aws-skills) 에서 관리하는 포크. 아이콘 카탈로그를 draw.io 원본에서 **스크립트로 재생성**하고, 검증 스크립트와 draw.io에 없는 아이콘의 SVG 폴백을 더했습니다.

**한국어** | [English](README.en.md)

**말로 설명하면 편집 가능한 `.drawio` 파일이 나옵니다.**

> "Lambda, DynamoDB, API Gateway로 서버리스 API 구성도를 draw.io로 그려줘"

결과는 draw.io(diagrams.net)에서 바로 열어 고칠 수 있는 XML입니다. 아이콘은 draw.io에 내장된 공식 AWS Architecture Icons 스텐실을 쓰고, 모든 스텐실 이름은 draw.io 소스에서 생성한 카탈로그로 검증됩니다.

## 왜 아이콘이 깨지는가, 이 스킬은 어떻게 막는가

draw.io AWS 아이콘에는 `strokeColor` 규칙이 반대인 두 패턴이 있습니다.

| 패턴 | 스타일 | strokeColor |
|---|---|---|
| 서비스 | `shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.<name>` | `#ffffff` 필수 |
| 리소스 | `shape=mxgraph.aws4.<name>` | `none` 필수 |

여기에 더해 스텐실 이름은 서비스 리네임을 따라가지 않습니다(OpenSearch 는 여전히 `elasticsearch_service`). 이 스킬은 (1) draw.io 의 `Sidebar-AWS4.js` 와 `aws4.xml` 에서 생성한 1,000개 이상의 이름 카탈로그, (2) 리네임 별칭표, (3) 생성 후 자동 실행하는 검증 스크립트로 이 문제를 막습니다.

## 설치 (Claude Code)

```
/plugin marketplace add hi-space/hi-aws-skills
/plugin install aws-drawio-diagram@hi-aws-skills
/reload-plugins
```

스킬만 쓰려면 `skills/aws-drawio-diagram` 을 `~/.claude/skills/` 또는 `~/.kiro/skills/` 에 심링크하세요.

## PNG/SVG/PDF 내보내기

draw.io 데스크톱 CLI가 필요합니다. 헤드리스 리눅스는 `xvfb-run -a` 를 앞에 붙입니다.

```bash
drawio --no-sandbox -x -f png -e -b 10 -o name.drawio.png name.drawio
```

## 구성

```
skills/aws-drawio-diagram/
├── SKILL.md                    절차, 두 패턴 규칙, 아이콘 조회 순서, 검증
├── references/
│   ├── layout-and-style.md     레이아웃·엣지·그룹·멀티페이지 규칙
│   ├── aws-icons-<category>.md 생성물: 카테고리별 스텐실 표
│   ├── aws-icons-groups.md     생성물: 그룹 배지와 경계 스타일
│   ├── aws-icons-aliases.md    수기: 리네임 → 스텐실 이름
│   ├── aws-icons-legacy.md     생성물: 팔레트에 없지만 렌더되는 이름
│   ├── aws-icons-retired.md    생성물: 은퇴 팔레트
│   └── aws-icons-extra.md      생성물: draw.io에 없는 아이콘의 shape=image 스니펫
├── templates/                  참조 템플릿 5종
├── assets/extra-icons/         차집합 SVG (AgentCore 리소스 등)
└── scripts/
    ├── validate_drawio.py      생성 결과 검증 (스킬이 매번 실행)
    ├── build_icon_catalog.py   카탈로그 재생성 (Node 필요, 유지보수용)
    ├── build_extra_icons.py    차집합 아이콘 리포트/빌드 (유지보수용)
    └── stencil-index.json      검증기가 읽는 이름 색인
```

## 카탈로그 갱신 (유지보수)

```bash
scripts/fetch_sources.sh                       # draw.io dev 브랜치 스냅샷 갱신
python3 skills/aws-drawio-diagram/scripts/build_icon_catalog.py
python3 skills/aws-drawio-diagram/scripts/build_extra_icons.py --report   # 후보 확인 후 extra-icons.txt 편집
python3 skills/aws-drawio-diagram/scripts/build_extra_icons.py
python3 -m pytest tests -q
```

## 관련 스킬

문서·슬라이드용 완성 이미지(HTML/SVG/PNG)나 기존 `.drawio` 의 하우스 스타일 재작도는 형제 플러그인 [aws-diagram-design](../aws-diagram-design/) 이 담당합니다.

## 라이선스

MIT. 서드파티 고지는 [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).
````

`plugins/aws-drawio-diagram/README.en.md`: same structure in English. Headings: *Why icons break and how this skill prevents it*, *Install (Claude Code)*, *Export*, *Layout*, *Refreshing the catalog (maintainers)*, *Related skill*, *License*. Translate each paragraph above one-to-one; keep the code blocks identical.

- [ ] **Step 5: Write THIRD_PARTY_LICENSES.md**

`plugins/aws-drawio-diagram/THIRD_PARTY_LICENSES.md`:

```markdown
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
```

- [ ] **Step 6: Run the whole suite**

Run: `cd plugins/aws-drawio-diagram && python3 -m pytest tests -q`
Expected: all passed.

- [ ] **Step 7: Commit**

```bash
cd /home/ubuntu/workspace/hi-aws-skills
git add .claude-plugin/marketplace.json README.md plugins/aws-drawio-diagram
git commit -m "Document aws-drawio-diagram, add third-party notices, register in marketplace

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 9: End-to-end verification and render check

**Files:**
- No new files unless a fix is needed. Possibly modify templates or references.

- [ ] **Step 1: Regenerate from scratch and confirm the tree is stable**

```bash
cd /home/ubuntu/workspace/hi-aws-skills
python3 plugins/aws-drawio-diagram/skills/aws-drawio-diagram/scripts/build_icon_catalog.py
python3 plugins/aws-drawio-diagram/skills/aws-drawio-diagram/scripts/build_extra_icons.py
git status --short plugins/aws-drawio-diagram
```

Expected: `git status` prints nothing — generation is deterministic. If a file changed, find the non-determinism (dict order, timestamps) and fix it in the generator, then re-commit.

- [ ] **Step 2: Validate the shipped templates through the CLI**

Run: `python3 plugins/aws-drawio-diagram/skills/aws-drawio-diagram/scripts/validate_drawio.py plugins/aws-drawio-diagram/skills/aws-drawio-diagram/templates/*.drawio`
Expected: `Summary: 0 errors, N warnings in 5 file(s)`.

- [ ] **Step 3: Write a fresh diagram the way the skill would, including an image fallback**

Create `/tmp/agentcore-demo.drawio` by hand following SKILL.md: background, title, `bedrock_agentcore` service icon, one `shape=image` cell copied from `references/aws-icons-extra.md` (AgentCore Memory), one edge between them. Run the validator on it. Expected: 0 errors.

- [ ] **Step 4: Attempt a headless PNG render**

```bash
cd /tmp && timeout 120 xvfb-run -a drawio --no-sandbox --disable-gpu -x -f png -e -b 10 -o /tmp/agentcore-demo.drawio.png /tmp/agentcore-demo.drawio 2>&1 | grep -viE 'error:|warning:|xio' | tail -3
ls -la /tmp/agentcore-demo.drawio.png
```

If the PNG appears: open it with the Read tool and confirm the two icons render (no empty squares). If the render fails with an X/ANGLE display error (this happened on the dev box during planning), record the exact error and the command in `plugins/aws-drawio-diagram/README.md` under 내보내기 as a known limitation, and verify rendering instead by opening the file at https://app.diagrams.net when a browser is available. Do not mark the render step as done if neither happened.

- [ ] **Step 5: Full test run and final commit**

```bash
cd /home/ubuntu/workspace/hi-aws-skills/plugins/aws-drawio-diagram && python3 -m pytest tests -q
cd /home/ubuntu/workspace/hi-aws-skills && git status --short
```

Expected: all tests pass; only intentional changes (if any from Step 4) remain. Commit them:

```bash
git add -A plugins/aws-drawio-diagram
git commit -m "Verify aws-drawio-diagram end to end; note headless export caveat

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

## Self-review notes

- **Spec coverage:** directory structure (T1, T3, T5), catalog generator with failure floors (T3), extra icons with allow list and `--report` (T5), validator changes incl. isometric false-positive removal and new E1/E2 checks (T6), SKILL.md with Korean triggers, lookup order, no 3D (T7), packaging/licensing/marketplace/root README (T1, T8), tests 1–3 (T3, T6, T9). Spec's "validator checks references/*.md" is implemented via the generated `stencil-index.json` written alongside the markdown; same data, machine-readable.
- **Deviation from spec, deliberate:** the generator executes `Sidebar-AWS4.js` in Node instead of parsing JS text in Python. Planning verified that this captures all 31 palettes (service 406, resource 610, group 16) including the retired palette's function-built styles, which a regex cannot resolve. Node is a build-time dependency only.
- **Type consistency:** `classify` returns `(kind, name)`; `build_index` returns `(stencils, boundaries)`; `load_index` returns `{"names", "js_shapes"}`; `read_allow_list` returns `list[tuple[str, str]]` — used identically across T3/T4/T5/T6 tests.
