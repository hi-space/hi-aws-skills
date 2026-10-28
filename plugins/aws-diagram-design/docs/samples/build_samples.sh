#!/usr/bin/env bash
# Rebuild the README showcase SVG+PNG pairs from docs/samples/specs with the bundled generator.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd); skill="$here/../../skills/aws-diagram-design"
tmp=$(mktemp -d)
python3 "$skill/scripts/pygen/build.py" "$here/specs" --out "$tmp" --langs en --strict --png
for f in "$tmp"/*-en.svg; do slug=$(basename "$f" -en.svg); cp "$f" "$here/$slug.svg"; cp "$tmp/$slug-en.png" "$here/$slug.png"; done
rm -rf "$tmp"; echo "samples rebuilt in $here"
