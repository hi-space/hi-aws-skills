---
description: Participant-walkthrough loop — a fresh-eyes agent follows the workshop for real (executes steps, checks links/datasets/prompts/build/deploy), an author agent fixes what it hits, repeat until a clean round
argument-hint: [workshop-root] [--rounds N]
---

Run the GATE-6d walkthrough loop against the workshop (defaults: current directory, max 3 rounds).

Per round N:

1. **Walk** — spawn the plugin agent **`aws-workshop-studio:participant-walker`** (a FRESH instance, no context of this build). It follows its own protocol: reads pages in participant order, **executes every executable instruction** (files/datasets exist, links resolve, prompts self-contained, setup commands correct, `npm ci && npm run docs:build`, deploy instructions — real only when safe, else labeled dry-run), never edits files, and writes `artifacts/06b-walkthrough-round-N.md` ending with the machine-checked marker `WALKTHROUGH_RESULT: CLEAN` or `WALKTHROUGH_RESULT: blockers=<n> majors=<n> minors=<n>`.
2. **Fix** — spawn an author subagent that applies the blocker and major fixes, rebuilds, and appends a "changed in round N" list to the same artifact. Judgment calls it can't decide go to the user, not silently skipped.
3. **Re-walk** with a NEW fresh `participant-walker` instance (never the author verifying itself). Stop early when the round marker is `WALKTHROUGH_RESULT: CLEAN`.

After the loop, report: rounds used, findings fixed vs remaining (remaining = known limitations for the handoff), and the final completion verdict. Do not soften findings. Note: `scripts/gate.sh 7` blocks the QA stage until the latest round is CLEAN — this command is how you clear that gate.
