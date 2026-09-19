#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# workshop-check.sh — Workshop change checks (generalized)
#   workshop-check.sh [path] [--fix] [--full]
#     path   : workshop root to check (default: current directory)
#     --fix  : if datasets are newer than their ZIP, regenerate the download ZIP (only if the script exists)
#     --full : also verify the VitePress build (+ always print the report)
#
#   Checks only the mechanically verifiable axes. The scaffold may have few files,
#   so a missing file never causes a hard exit (downgraded to a warning):
#     1) datasets <-> download ZIP freshness   2) presenter notes excluded from deploy
#     3) zero participant-facing emoji          4) referenced assets (icons/logo) exist
#     5) visual-first (INV-8/GATE-4d): every scene page has >=1 visual
#        (<Screenshot>/<Video>/<FlowMap>/mermaid/image) — text-only pages are flagged
#     6) insight-first (INV-9/GATE-4e): every start/overview.md carries the overview
#        architecture diagram (/images/diagrams/) and the four <!-- arch:* --> sections
#   "Participant-perspective demo flow" needs judgment -> review it in the /workshop-check skill.
# ─────────────────────────────────────────────────────────────
set -uo pipefail

FIX=0; FULL=0; ROOT=""
for a in "$@"; do
  case "$a" in
    --fix)  FIX=1 ;;
    --full) FULL=1 ;;
    -*) : ;;
    *) [ -z "$ROOT" ] && ROOT="$a" ;;
  esac
done
ROOT="${ROOT:-$PWD}"
cd "$ROOT" 2>/dev/null || { echo "Path not found: $ROOT" >&2; exit 0; }

ISSUES=0; FIXED=0
BUF=""
add(){ BUF+="$1"$'\n'; }
warn(){ add "  ⚠️  $*"; ISSUES=$((ISSUES+1)); }
ok(){ add "  ✓ $*"; }

add "── Workshop check ($ROOT) ──────────────────────"

# 1) Dataset dir <-> download ZIP freshness
#    Auto-detect demo_datasets* directories (including locale copies). Skip if none.
latest_zip() { ls -t docs/public/downloads/"$1"*.zip 2>/dev/null | head -1; }
ds_dirs=$(find . -maxdepth 1 -type d -name 'demo_datasets*' 2>/dev/null | sed 's|^\./||')
if [ -z "$ds_dirs" ]; then
  ok "No dataset directory — freshness check skipped"
else
  stale=0
  while IFS= read -r src; do
    [ -z "$src" ] && continue
    prefix="${src}_"
    z=$(latest_zip "$prefix")
    if [ -z "$z" ]; then stale=1;
    elif [ -n "$(find "$src" -type f ! -name '.DS_Store' -newer "$z" 2>/dev/null | head -1)" ]; then stale=1; fi
  done <<< "$ds_dirs"
  if [ "$stale" = "1" ]; then
    if [ "$FIX" = "1" ] && [ -f scripts/build-dataset-zips.sh ]; then
      if bash scripts/build-dataset-zips.sh >/dev/null 2>&1; then add "  ↻ Download ZIP regenerated"; FIXED=$((FIXED+1)); else warn "ZIP regeneration failed"; fi
    else
      warn "Datasets are newer than the download ZIP — regeneration needed (--fix, or handled automatically at deploy)"
    fi
  else
    ok "Download ZIP up to date"
  fi
fi

# 2) Presenter notes excluded from deploy (anything under docs/ gets deployed -> not allowed)
if find docs -type f -iname '*presenter*' 2>/dev/null | grep -q .; then
  warn "Presenter notes found under docs/ (would be deployed!) — move outside docs/ (repo root)"
else
  ok "Presenter notes kept out of deploy"
fi
[ -f PRESENTER_NOTES.md ] || warn "PRESENTER_NOTES.md missing (recommended)"

# 3) Zero participant-facing emoji
EMO=0
while IFS= read -r f; do
  n=$(perl -CSD -ne 'while(/[\x{1F300}-\x{1FAFF}\x{2600}-\x{27BF}\x{2B00}-\x{2BFF}\x{FE0F}]/g){$c++} END{print $c+0}' "$f" 2>/dev/null)
  EMO=$((EMO + ${n:-0}))
done < <(find docs -name '*.md' 2>/dev/null)
[ "$EMO" = "0" ] && ok "Zero participant-facing emoji" || warn "${EMO} emoji remaining (participant-facing should be 0)"

# 4) Referenced assets exist
#    features.ts icon: keys -> docs/public/images/icons/<key>.svg existence check (kept)
amiss=0
if [ -f docs/.vitepress/data/features.ts ]; then
  while IFS= read -r key; do
    [ -z "$key" ] && continue
    [ -f "docs/public/images/icons/$key.svg" ] || { warn "Missing icon: icons/$key.svg"; amiss=$((amiss+1)); }
  done < <(grep -oE "icon: '[a-z0-9-]+'" docs/.vitepress/data/features.ts 2>/dev/null | sed "s/icon: '//; s/'//" | sort -u)
  [ "$amiss" = "0" ] && ok "All feature icon assets present"
else
  ok "No features.ts — icon check skipped"
fi
# Logo assets: ai-passport-specific assumptions (logo/aws-light/aws-dark) downgraded to warnings only
for L in logo.png; do
  [ -f "docs/public/images/home/$L" ] || warn "Logo asset missing (recommended): home/$L"
done

# 5) Visual-first (INV-8 / GATE-4d): every scene page carries >=1 visual
noviz=0
while IFS= read -r f; do
  [ -z "$f" ] && continue
  if ! grep -qE '<Screenshot|<Video|<FlowMap|```mermaid|!\[|<img ' "$f" 2>/dev/null; then
    warn "Text-only scene page (needs a Screenshot slot or diagram): $f"
    noviz=$((noviz+1))
  fi
done < <(find docs -path '*scenario-*' -name 'scene*.md' 2>/dev/null)
[ "$noviz" = "0" ] && ok "Visual-first: every scene page has a visual"

# 6) Insight-first (INV-9 / GATE-4e): overview pages carry the architecture diagram + why/services/adoption sections
ov_bad=0; ov_n=0
while IFS= read -r f; do
  [ -z "$f" ] && continue
  ov_n=$((ov_n+1))
  if ! grep -qE 'images/diagrams/' "$f" 2>/dev/null; then
    warn "Overview without an architecture diagram (expected an image or <Screenshot> under /images/diagrams/): $f"; ov_bad=$((ov_bad+1))
  fi
  for m in arch:diagram arch:why arch:services arch:adoption; do
    grep -q "<!-- $m -->" "$f" 2>/dev/null || { warn "Overview missing section marker <!-- $m --> (why/value/before-after, INV-9): $f"; ov_bad=$((ov_bad+1)); }
  done
done < <(find docs -path '*start*' -name 'overview.md' 2>/dev/null)
if [ "$ov_n" = "0" ]; then warn "No start/overview.md found (INV-9 needs one)"; elif [ "$ov_bad" = "0" ]; then ok "Insight-first: overview pages carry the architecture diagram and why/value sections"; fi

# 7) Walkthrough status (GATE-6d) — informational: warn when content exists but no clean walkthrough round yet
if [ -d artifacts ] && find docs -path '*scenario-*' -name '*.md' 2>/dev/null | grep -q .; then
  last_walk=$(ls artifacts/06b-walkthrough-round-*.md 2>/dev/null | sort | tail -1)
  if [ -z "$last_walk" ]; then
    warn "No participant walkthrough round yet (GATE-6d) — run /workshop-walkthrough before QA"
  elif grep -q '^WALKTHROUGH_RESULT: CLEAN$' "$last_walk"; then
    ok "Walkthrough clean ($last_walk)"
  else
    warn "Latest walkthrough round is not CLEAN ($last_walk) — fix and re-walk with a fresh agent"
  fi
fi

# 8) --full: build
if [ "$FULL" = "1" ]; then
  if [ -f package.json ]; then
    if npm run docs:build >/tmp/ws_build.log 2>&1; then ok "VitePress build succeeded"; else warn "Build failed (see /tmp/ws_build.log)"; fi
  else
    warn "No package.json — build skipped"
  fi
fi

add "─────────────────────────────────────────────"
if [ "$ISSUES" = "0" ]; then
  add "✅ Mechanical checks passed (${FIXED} auto-fixes)"
else
  add "⚠️  ${ISSUES} item(s) need review"
fi
add "※ Participant-perspective demo flow review needs judgment → use the /workshop-check skill"

# Output: only when --full, or there are issues/fixes (stays quiet in a Stop hook)
if [ "$FULL" = "1" ] || [ "$ISSUES" -gt 0 ] || [ "$FIXED" -gt 0 ]; then
  printf '%s' "$BUF"
fi
exit 0
