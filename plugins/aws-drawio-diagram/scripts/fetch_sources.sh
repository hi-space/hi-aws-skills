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
