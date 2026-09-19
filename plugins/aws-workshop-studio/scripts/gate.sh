#!/usr/bin/env bash
# gate.sh — deterministic stage-entry gate (INV-1a + mechanical gate checks).
#   Usage: bash scripts/gate.sh <stage 2..8> [workshop-root]
#   Exit 0 = the stage may start. Exit 2 = BLOCKED (reason on stderr).
#
# This is the hard, non-probabilistic form of the pipeline contract's
# prerequisite checks: a stage must not start unless the previous stage's
# artifact file actually exists (and blueprint has no open [BLOCKER]s).
set -uo pipefail
STAGE="${1:-}"; ROOT="${2:-$PWD}"
cd "$ROOT" 2>/dev/null || { echo "BLOCKED: workshop root not found: $ROOT" >&2; exit 2; }
[ -n "$STAGE" ] || { echo "Usage: gate.sh <stage 2..8> [root]" >&2; exit 2; }

need() { # need <file> <producing-stage>
  [ -f "$1" ] && return 0
  echo "BLOCKED (INV-1a): required artifact '$1' from stage $2 does not exist — do not start stage $STAGE. Produce/repair the artifact first." >&2
  exit 2
}

case "$STAGE" in
  2) need brief.yaml "1 (intake)" ;;
  3) need brief.yaml "1"; need artifacts/02-feature-facts.md "2 (research)" ;;
  4)
    need artifacts/02-feature-facts.md "2"
    need artifacts/03-blueprint.md "3 (blueprint)"
    need artifacts/03a-architecture-rationale.md "3 (architecture rationale, GATE-3f/INV-9)"
    if grep -q '\[BLOCKER\]' artifacts/03a-architecture-rationale.md 2>/dev/null; then
      echo "BLOCKED (GATE-3f): artifacts/03a-architecture-rationale.md still contains [BLOCKER] items — close them before generation." >&2
      exit 2
    fi
    if grep -q '\[BLOCKER\]' artifacts/03-blueprint.md 2>/dev/null; then
      echo "BLOCKED (GATE-3a/3e): artifacts/03-blueprint.md still contains [BLOCKER] items — close them before generation." >&2
      exit 2
    fi
    ;;
  5) need artifacts/03-blueprint.md "3"; [ -d docs ] || { echo "BLOCKED: docs/ missing — run generation (4) first." >&2; exit 2; } ;;
  6) need artifacts/03-blueprint.md "3"
     [ -d docs/.vitepress/dist ] || echo "note: no build output found — persona review should read a built site (run stage 5)." >&2 ;;
  7)
    need artifacts/06-persona-review.md "6 (persona review)"
    # GATE-6d: QA may not start until a walkthrough round ended clean (machine-checked marker).
    last_walk=$(ls artifacts/06b-walkthrough-round-*.md 2>/dev/null | sort | tail -1)
    if [ -z "$last_walk" ]; then
      echo "BLOCKED (GATE-6d): no walkthrough round found (artifacts/06b-walkthrough-round-N.md) — run the participant walkthrough loop (/workshop-walkthrough) before QA." >&2
      exit 2
    fi
    if ! grep -q '^WALKTHROUGH_RESULT: CLEAN$' "$last_walk"; then
      echo "BLOCKED (GATE-6d): latest walkthrough round ($last_walk) is not CLEAN — fix blocker/major findings and re-walk with a fresh agent." >&2
      exit 2
    fi
    ;;
  8) need artifacts/07-qa-report.md "7 (QA)" ;;
  *) echo "Usage: gate.sh <stage 2..8> [root]" >&2; exit 2 ;;
esac

echo "gate ok: stage $STAGE may start"
exit 0
