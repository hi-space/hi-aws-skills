#!/usr/bin/env node
// PreToolUse hook — enforces INV-4: brief.yaml is a read-only SSOT after intake.
// Creating brief.yaml (intake, stage 1) is allowed; modifying an existing one is blocked.
// To change a frozen value: record an amendment in artifacts/00-amendments.md and
// regenerate the affected stages — do not edit brief.yaml in place.
// Exit codes: 0 = allow, 2 = block (stderr is shown to the model).
import { existsSync } from 'node:fs'
import { basename } from 'node:path'

let raw = ''
for await (const chunk of process.stdin) raw += chunk

let input
try {
  input = JSON.parse(raw)
} catch {
  process.exit(0) // not our concern — never break other tools on parse issues
}

const filePath = input?.tool_input?.file_path || ''
if (!filePath || basename(filePath) !== 'brief.yaml') process.exit(0)

// Allow initial creation during intake; block edits once it exists (INV-4).
if (!existsSync(filePath)) process.exit(0)

console.error(
  'BLOCKED (INV-4): brief.yaml is a read-only SSOT after intake. ' +
    'Record the change as an amendment in artifacts/00-amendments.md ' +
    'and regenerate only the affected stages instead of editing brief.yaml.'
)
process.exit(2)
