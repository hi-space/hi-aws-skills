---
description: Run the workshop QA gate — mechanical checks (datasets, presenter notes, emoji, assets, visual-first) + build, then a judgment review of the participant flow
argument-hint: [workshop-root]
---

1. Run the mechanical checks against the workshop (defaults to the current directory):

```
bash "${CLAUDE_PLUGIN_ROOT}/scripts/workshop-check.sh" $ARGUMENTS --full
```

2. Report each axis result verbatim (do not soften warnings). Fix only the mechanically obvious issues (e.g., regenerate a stale ZIP with `--fix`); anything needing judgment goes to the user as a finding, not a silent fix.

3. Then do the part the script cannot: a **participant-perspective flow review** — walk the scenario pages in order as a first-time participant and check: does each scene state what I do, what I should see, and what to do when it fails? Do difficulty jumps stay ≤ 1 step between adjacent scenes? Does every scene page carry at least one visual (screenshot slot / diagram / FlowMap)? List concrete findings with page paths.
