#!/usr/bin/env bash
# aws-diagram-design installer
#
#   ./install.sh claude-code                  # print Claude Code plugin install steps
#   ./install.sh kiro [--workspace] [--link]  # copy (or symlink) the skill for Kiro
#   ./install.sh fonts                         # install bundled Amazon Ember TTFs to the OS font dir
#
# Add --force to overwrite an existing install of the same name.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SRC="$REPO_DIR/skills/aws-diagram-design"
SKILL_NAME="aws-diagram-design"

TARGET="${1:-}"
shift || true

FORCE=0; LINK=0; WORKSPACE=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --force) FORCE=1 ;;
    --link) LINK=1 ;;
    --workspace) WORKSPACE=1 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

die() { echo "error: $*" >&2; exit 1; }

place() { # place <dst-dir>
  local dst="$1"
  if [[ -e "$dst" || -L "$dst" ]]; then
    [[ $FORCE -eq 1 ]] || die "$dst already exists — re-run with --force to replace it"
    rm -rf "$dst"
  fi
  mkdir -p "$(dirname "$dst")"
  if [[ $LINK -eq 1 ]]; then
    ln -s "$SKILL_SRC" "$dst"
    echo "symlinked: $dst -> $SKILL_SRC"
  else
    cp -R "$SKILL_SRC" "$dst"
    echo "copied: $dst"
  fi
}

case "$TARGET" in
  claude-code)
    cat <<EOF
Claude Code installs this repo as a plugin (skill + slash commands). In a Claude Code session run:

  /plugin marketplace add hi-space/hi-aws-skills      # or the local clone: $(dirname "$(dirname "$REPO_DIR")")
  /plugin install aws-diagram-design@hi-aws-skills

Then restart or /reload-plugins when prompted.

If the original 'diagram-design' marketplace plugin is still enabled, disable it
(/plugin -> diagram-design -> disable) so the two similar skills don't compete.

Skill-only alternative (no slash commands):
  ln -s "$SKILL_SRC" ~/.claude/skills/$SKILL_NAME
EOF
    ;;

  kiro)
    if [[ $WORKSPACE -eq 1 ]]; then
      DST="$PWD/.kiro/skills/$SKILL_NAME"
    else
      DST="$HOME/.kiro/skills/$SKILL_NAME"
    fi
    place "$DST"
    cat <<EOF

Kiro's default agent (IDE and CLI) discovers the skill automatically.
A CUSTOM agent (kiro-cli chat --agent <name>) must declare it in its config:
  "resources": ["skill://~/.kiro/skills/**/SKILL.md", "skill://.kiro/skills/**/SKILL.md"]

To install as a Kiro Power instead (one-click install, keyword activation):
  Powers panel -> Add Custom Power -> Import power from a folder -> $REPO_DIR
EOF
    ;;

  fonts)
    FONT_SRC="$SKILL_SRC/assets/fonts/ttf"
    [[ -d "$FONT_SRC" ]] || die "font directory not found: $FONT_SRC"
    case "$(uname -s)" in
      Darwin) FONT_DST="$HOME/Library/Fonts" ;;
      *)      FONT_DST="$HOME/.local/share/fonts/amazon-ember" ;;
    esac
    mkdir -p "$FONT_DST"
    cp "$FONT_SRC"/*.ttf "$FONT_DST/"
    echo "installed Amazon Ember TTFs to: $FONT_DST"
    if command -v fc-cache >/dev/null 2>&1; then
      fc-cache -f "$FONT_DST" >/dev/null && echo "font cache refreshed (fc-cache)"
    fi
    echo "Diagrams declaring 'Amazon Ember' will now render with the real face in local browsers."
    ;;

  *)
    echo "usage: ./install.sh <claude-code|kiro|fonts> [--force] [--link] [--workspace]" >&2
    exit 2
    ;;
esac
