---
description: Scaffold a new quick-* VitePress workshop into a target folder (copies the skeleton, substitutes tokens, bundles enforcement scripts & hooks)
argument-hint: <target-path> [--name NAME] [--title TITLE] [--desc DESC] [--color HEX] [--force]
---

Run the scaffold generator with the user's arguments:

```
bash "${CLAUDE_PLUGIN_ROOT}/scripts/new-workshop.sh" $ARGUMENTS
```

Then report: the target path, which tokens were substituted, which tokens remain, and the next steps the script printed (`npm install`, `npm run docs:dev`). If the target was non-empty and the script aborted, relay the `--force` option instead of retrying on your own.

After scaffolding, suggest the natural next step: run the `workshop-scaffold` skill in that folder to fill it (intake → research → …).
