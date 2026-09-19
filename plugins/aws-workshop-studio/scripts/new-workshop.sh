#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# new-workshop.sh — Copy the verified VitePress scaffold to a target path and substitute tokens.
#
#   new-workshop.sh <target-path> [--name NAME] [--title TITLE] [--desc DESC] [--color HEX] [--force]
#
#   Example:
#     new-workshop.sh ~/ws/hanbitpay --name hanbitpay-quick-workshop \
#       --title "HanbitPay Quick Workshop" --desc "Fintech ops-automation demo" --color "#8b2fe8"
#
#   Behavior: copy assets/scaffold/ to <target-path> (excluding node_modules/dist/cache) ->
#             replace __TOKEN__ with the given values (sed) -> print remaining tokens and next steps.
#   Idempotent: aborts if the target is non-empty (use --force to overwrite).
# ─────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCAFFOLD="$SCRIPT_DIR/../assets/scaffold"

DEST=""; NAME=""; TITLE=""; DESC=""; COLOR="#232F3E"; FORCE=0

usage() {
  grep -E '^#( |$)' "$0" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

# First non-flag argument is the target path
while [ $# -gt 0 ]; do
  case "$1" in
    --name)  NAME="$2"; shift 2 ;;
    --title) TITLE="$2"; shift 2 ;;
    --desc)  DESC="$2"; shift 2 ;;
    --color) COLOR="$2"; shift 2 ;;
    --force) FORCE=1; shift ;;
    -h|--help) usage 0 ;;
    -*) echo "Unknown option: $1" >&2; usage 1 ;;
    *) if [ -z "$DEST" ]; then DEST="$1"; shift; else echo "Too many arguments: $1" >&2; usage 1; fi ;;
  esac
done

[ -n "$DEST" ] || { echo "Error: a target path is required." >&2; usage 1; }
[ -d "$SCAFFOLD" ] || { echo "Error: scaffold not found: $SCAFFOLD" >&2; exit 1; }

# Idempotency guard
if [ -e "$DEST" ] && [ -n "$(ls -A "$DEST" 2>/dev/null || true)" ]; then
  if [ "$FORCE" != "1" ]; then
    echo "Warning: '$DEST' is not empty. Use --force to overwrite." >&2
    exit 1
  fi
  echo "── --force: overwriting existing target: $DEST"
fi

mkdir -p "$DEST"

# Copy (excluding node_modules / dist / cache)
if command -v rsync >/dev/null 2>&1; then
  rsync -a \
    --exclude 'node_modules' \
    --exclude 'docs/.vitepress/dist' \
    --exclude 'docs/.vitepress/cache' \
    "$SCAFFOLD"/ "$DEST"/
else
  # No rsync: copy then delete the excluded paths
  cp -R "$SCAFFOLD"/. "$DEST"/
  rm -rf "$DEST/node_modules" "$DEST/docs/.vitepress/dist" "$DEST/docs/.vitepress/cache"
fi

echo "── Scaffold copied → $DEST"

# Bundle the enforcement scripts into the workshop so the .claude hooks work standalone:
#   Stop hook → scripts/workshop-check.sh, stage gates → scripts/gate.sh, capture list → image-manifest.mjs
mkdir -p "$DEST/scripts"
for s in workshop-check.sh gate.sh image-manifest.mjs; do
  [ -f "$SCRIPT_DIR/$s" ] && cp "$SCRIPT_DIR/$s" "$DEST/scripts/$s"
done
chmod +x "$DEST/scripts/"*.sh 2>/dev/null || true
echo "── Enforcement scripts bundled → $DEST/scripts/ (used by .claude/settings.json hooks)"

# Token substitution (sed) — only for values that were provided. Works on both macOS/BSD and GNU.
sed_i() {
  local pat="$1"; shift
  # Substitute only in the target files
  local files=(
    "$DEST/package.json"
    "$DEST/package-lock.json"
    "$DEST/docs/.vitepress/config.mts"
    "$DEST/docs/index.md"
  )
  for f in "${files[@]}"; do
    [ -f "$f" ] || continue
    if sed --version >/dev/null 2>&1; then
      sed -i "$pat" "$f"           # GNU
    else
      sed -i '' "$pat" "$f"        # BSD/macOS
    fi
  done
}

# Use | as the sed delimiter (values may contain /). Escape | & \ inside the value.
esc() { printf '%s' "$1" | sed 's/[|&\\]/\\&/g'; }

[ -n "$NAME" ]  && { sed_i "s|__WORKSHOP_NAME__|$(esc "$NAME")|g";      echo "  ✓ __WORKSHOP_NAME__ → $NAME"; }
[ -n "$TITLE" ] && { sed_i "s|__SITE_TITLE__|$(esc "$TITLE")|g";        echo "  ✓ __SITE_TITLE__ → $TITLE"; }
[ -n "$DESC" ]  && { sed_i "s|__SITE_DESCRIPTION__|$(esc "$DESC")|g";   echo "  ✓ __SITE_DESCRIPTION__ → $DESC"; }
[ -n "$COLOR" ] && { sed_i "s|__THEME_COLOR__|$(esc "$COLOR")|g";       echo "  ✓ __THEME_COLOR__ → $COLOR"; }

# List remaining tokens
echo "── Remaining tokens (fill these in yourself):"
REMAIN=$(grep -rloE '__[A-Z_]+__' "$DEST/package.json" "$DEST/docs" 2>/dev/null | sort -u || true)
if [ -z "$REMAIN" ]; then
  echo "  (none — all tokens substituted)"
else
  grep -rhoE '__[A-Z_]+__' "$DEST/package.json" "$DEST/docs" 2>/dev/null | sort -u | sed 's/^/  · /'
fi

cat <<EOF

── Next steps
  cd "$DEST"
  npm install
  npm run docs:dev      # local preview
  npm run docs:build    # production build

  · Features/flows: fill in docs/.vitepress/data/{features,flows}.ts per the blueprint
  · If any tokens remain, edit the files above directly
  · Token reference: assets/scaffold/TOKENS.md
EOF
