export const meta = {
  name: 'workshop-pipeline',
  description: 'Build a quick-* AWS workshop end to end: research → blueprint → generate → assemble → persona review → QA → handoff',
  whenToUse: 'Run the workshop-scaffold pipeline as a multi-agent workflow (oneshot or max-parallelism). Honors the same gates/invariants as the interactive path.',
  phases: [
    { title: 'Research' },
    { title: 'Blueprint' },
    { title: 'Generate' },
    { title: 'Assemble' },
    { title: 'Persona' },
    { title: 'Walkthrough' },
    { title: 'QA' },
    { title: 'Handoff' },
  ],
}

// The workshop root (where brief.yaml lives). Pass via Workflow args; default to CWD.
const ROOT = (args && args.root) || '.'
const REFS = 'references' // relative to the installed skill; agents resolve real paths from the skill dir

// --- schemas (gate structured outputs) ---
const FEATURE_FACTS = {
  type: 'object',
  required: ['features', 'artifactPath'],
  properties: {
    artifactPath: { type: 'string' },
    features: {
      type: 'array',
      items: {
        type: 'object',
        required: ['name', 'status', 'inRegion', 'confidence'],
        properties: {
          name: { type: 'string' },
          status: { enum: ['GA', 'preview', 'not-available'] },
          inRegion: { type: 'boolean' },
          confidence: { enum: ['verified', 'documented', 'assumed', 'needs-check'] },
          designImplication: { type: 'string' },
        },
      },
    },
    regionBlockers: { type: 'array', items: { type: 'string' } },
  },
}
const BLUEPRINT = {
  type: 'object',
  required: ['scenes', 'artifactPath'],
  properties: {
    artifactPath: { type: 'string' },
    scenes: {
      type: 'array',
      items: {
        type: 'object',
        required: ['scenario', 'scene', 'features'],
        properties: {
          scenario: { type: 'string' },
          scene: { type: 'string' },
          difficulty: { type: 'integer' },
          features: { type: 'array', items: { type: 'string' } },
        },
      },
    },
    openQuestions: { type: 'array', items: { type: 'string' } },
  },
}
const WROTE = {
  type: 'object',
  required: ['path', 'ok'],
  properties: { path: { type: 'string' }, ok: { type: 'boolean' }, note: { type: 'string' } },
}
const REVIEW = {
  type: 'object',
  required: ['persona', 'findings'],
  properties: {
    persona: { type: 'string' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        required: ['severity', 'where', 'fix'],
        properties: {
          severity: { enum: ['blocker', 'major', 'minor'] },
          where: { type: 'string' },
          issue: { type: 'string' },
          fix: { type: 'string' },
        },
      },
    },
  },
}

// ── Stage 2: Research ★ (parallel cells: company × audience × one per technology) ──
phase('Research')
const plan = await agent(
  `Read ${ROOT}/brief.yaml. Return: the list of AWS services/feature groups to verify (aws.services, expanded by what the scenarios imply), the customer name/industry, and the audience roles.`,
  {
    phase: 'Research',
    schema: {
      type: 'object',
      required: ['services', 'customer', 'roles'],
      properties: {
        services: { type: 'array', items: { type: 'string' } },
        customer: { type: 'string' },
        roles: { type: 'array', items: { type: 'string' } },
      },
    },
  }
)
const services = (plan && plan.services) || []
// Company + audience + one cell per technology, all in parallel (INV-3: cells are isolated).
const cellResults = await parallel([
  () =>
    agent(
      `Research the customer "${plan && plan.customer}" (public sources only): industry, scale, public tech stack, domain vocabulary. Label facts documented/assumed per ${REFS}/research-discipline.md — never present an assumption as real. WRITE ${ROOT}/artifacts/02a-company-context.md. Return {path, ok}.`,
      { phase: 'Research', schema: WROTE, label: 'research:company' }
    ),
  () =>
    agent(
      `Research the audience roles ${JSON.stringify((plan && plan.roles) || [])}: day-to-day work, tooling, prior knowledge — to calibrate scene difficulty and jargon (GATE-3b input). WRITE ${ROOT}/artifacts/02b-audience-context.md. Return {path, ok}.`,
      { phase: 'Research', schema: WROTE, label: 'research:audience' }
    ),
  ...services.map((svc) => () =>
    agent(
      `Verify the AWS technology "${svc}" per ${REFS}/research-discipline.md: GA/preview status and availability in the region named in ${ROOT}/brief.yaml (verify freshly — web/docs, do not recall). One confidence label (verified|documented|assumed|needs-check) + confirmed_date + valid_until + a design implication. WRITE your rows to ${ROOT}/artifacts/02-tech-${svc.toLowerCase().replace(/[^a-z0-9]+/g, '-')}.md. Return {path, ok}.`,
      { phase: 'Research', schema: WROTE, label: `research:${svc}` }
    )
  ),
])
const cellsOk = cellResults.filter(Boolean).filter((c) => c.ok).length
log(`Research cells done: ${cellsOk}/${services.length + 2}`)
// Merge the technology rows into the single source of truth (cells in == rows out, INV-5).
const facts = await agent(
  `Merge the per-technology files ${ROOT}/artifacts/02-tech-*.md into ${ROOT}/artifacts/02-feature-facts.md (table + design implications), preserving every confidence label and cross-referencing 02a/02b. Verify row count == ${services.length} technology cells (INV-5). Resolve any region mismatch with an alternative (region/service/scope) or flag it. Return the structured summary.`,
  { phase: 'Research', schema: FEATURE_FACTS, effort: 'high' }
)
if (facts && facts.regionBlockers && facts.regionBlockers.length) {
  log(`Region blockers unresolved: ${facts.regionBlockers.join('; ')} — resolve before generation (GATE-2a).`)
}

// ── Stage 3: Blueprint ★ ────────────────────────────────────────
phase('Blueprint')
const blueprint = await agent(
  `Read ${ROOT}/brief.yaml and ${ROOT}/artifacts/02-feature-facts.md. Produce the workshop blueprint: scenario arc, scene decomposition with a difficulty (1..N; adjacent scenes jump ≤1; ≤2 new concepts per scene — GATE-3b), feature→scene mapping, dataset requirements, diagram list (starting with the workshop overview architecture and one architecture diagram per scenario, drawn with the aws-diagram-design skill — GATE-3e), image-slot outline, and open questions. Respect the format from ${REFS}/format-spec.md. WRITE to ${ROOT}/artifacts/03-blueprint.md (INV-1). THEN, following ${REFS}/architecture-rationale.md and reading ${ROOT}/artifacts/02a-company-context.md and 02b-audience-context.md, WRITE ${ROOT}/artifacts/03a-architecture-rationale.md with all six sections (problem, chosen architecture, decisions with alternatives, per-service role and value, adoption benefits by audience role, one insight sentence per scene); one row per service in feature-facts (INV-5), every value claim labeled, no invented figures (GATE-3f). Preserve every confidence label from feature-facts as a column in the scene tables (INV-6). Return the structured summary.`,
  { phase: 'Blueprint', schema: BLUEPRINT, effort: 'high' }
)
const scenes = (blueprint && blueprint.scenes) || []
if (blueprint && blueprint.openQuestions && blueprint.openQuestions.length) {
  log(`Open questions must be closed before generation (GATE-3a): ${blueprint.openQuestions.join('; ')}`)
}

// ── Stage 4: Generate (parallel over scenes) ────────────────────
phase('Generate')
// Each scene page is an independent cell (INV-3: a failed cell doesn't sink the rest).
const scenePages = await parallel(
  scenes.map((sc, i) => () =>
    agent(
      `Using ${REFS}/templates/scene.md and ${REFS}/component-api.md, write the page for ${sc.scenario} / ${sc.scene} into ${ROOT}/docs/${sc.scenario.toLowerCase().startsWith('scenario') ? sc.scenario.toLowerCase() : 'scenario-' + sc.scenario.toLowerCase()}/${sc.scene.toLowerCase().replace(/[^a-z0-9]+/g, '') || 'scene' + (i + 1)}.md. Features to exercise: ${(sc.features || []).join(', ')}. Include ::: prompt and ::: talk callouts and <Screenshot> slots for any product screen (never AI-generate screenshots). Include the mandatory "Why these services here" table filled from ${ROOT}/artifacts/03a-architecture-rationale.md (INV-9). Keep the confidence labels from the blueprint visible. Return {path, ok}.`,
      { phase: 'Generate', schema: WROTE, label: `scene:${sc.scenario}/${sc.scene}` }
    )
  )
)
const wrote = scenePages.filter(Boolean)
log(`Scene pages written: ${wrote.filter((w) => w.ok).length}/${scenes.length}`)
// INV-5: request count == output count
if (wrote.length !== scenes.length) log(`WARN count mismatch: requested ${scenes.length}, got ${wrote.length} (INV-5).`)

// Feature catalog + datasets + diagrams (one agent, reads the files above)
await agent(
  `Read ${ROOT}/artifacts/03-blueprint.md. Fill the feature catalog pages (${REFS}/templates/feature.md) into ${ROOT}/docs/features/, update ${ROOT}/docs/.vitepress/data/features.ts and flows.ts to match (INV-5), generate the required datasets under ${ROOT}/demo_datasets/ (satisfying scene logic — GATE-4a) with a mapping table in ${ROOT}/docs/reference/datasets.md, and produce diagrams per ${REFS}/diagram-recipes.md — architecture diagrams with the aws-diagram-design skill (official AWS icons), mermaid for flows. Every feature page must include the "Why this service" section from ${ROOT}/artifacts/03a-architecture-rationale.md (INV-9). Record every image slot in ${ROOT}/artifacts/04-image-manifest.json. Report what you wrote.`,
  { phase: 'Generate' }
)

// Overview page: the one place the whole story is told (INV-9 / GATE-4e).
await agent(
  `Using ${REFS}/templates/overview.md and ${ROOT}/artifacts/03a-architecture-rationale.md, write ${ROOT}/docs/start/overview.md (and each locale copy under ${ROOT}/docs/<locale>/start/overview.md if brief.yaml lists more languages): purpose, one-sentence message, the overview architecture diagram (generated with the aws-diagram-design skill into ${ROOT}/docs/public/images/diagrams/overview-architecture.png, or a <Screenshot> slot at that path if the export is pending), then the four <!-- arch:* --> sections — why this architecture, per-service role/why/what-changes table (rows == services in 02-feature-facts.md, INV-5), before/after by audience role — followed by the scenario flow. Also add each scenario's architecture diagram and why-paragraph to ${ROOT}/docs/scenario-*/index.md. No invented figures; keep confidence labels. Return {path, ok}.`,
  { phase: 'Generate', schema: WROTE, label: 'overview' }
)

// ── Stage 5: Assemble ───────────────────────────────────────────
phase('Assemble')
await agent(
  `In ${ROOT}: ensure config.mts nav/sidebar/i18n reflect the generated scenarios and features, then run \`npm install && npm run docs:build\`. Fix every build error and dead link until the build passes (GATE-5). Report the last line of the build log.`,
  { phase: 'Assemble', effort: 'high' }
)

// ── Stage 6: Persona review (parallel cells) ────────────────────
phase('Persona')
// Read the active audience cells from brief.yaml, review in parallel, isolate failures (INV-3).
const personaList = await agent(
  `Read ${ROOT}/brief.yaml audience (level×role) and ${REFS}/persona-rubric.md. Return the active persona cells to review as a JSON array of short persona descriptors.`,
  { phase: 'Persona', schema: { type: 'object', required: ['personas'], properties: { personas: { type: 'array', items: { type: 'string' } } } } }
)
const personas = (personaList && personaList.personas) || []
const reviews = (
  await parallel(
    personas.map((p) => () =>
      agent(
        `You are the persona: ${p}. Read the built workshop under ${ROOT}/docs and the blueprint. Following ${REFS}/persona-rubric.md, give at least 2 concrete findings with severity (blocker|major|minor), where, and a specific fix (GATE-6b — "it's all good" is invalid). Return the structured review.`,
        { phase: 'Persona', schema: REVIEW, label: `persona:${p}` }
      )
    )
  )
).filter(Boolean)
if (reviews.length !== personas.length) log(`WARN persona panel incomplete: ${reviews.length}/${personas.length} (GATE-6a) — re-run missing cells.`)
const blockers = reviews.flatMap((r) => (r.findings || []).filter((f) => f.severity === 'blocker'))
const majors = reviews.flatMap((r) => (r.findings || []).filter((f) => f.severity === 'major'))
if (blockers.length || majors.length) {
  await agent(
    `Apply these persona fixes to the workshop under ${ROOT}, then rebuild. Blockers (must reach 0 — GATE-6c): ${JSON.stringify(blockers)}. Majors: ${JSON.stringify(majors)}. Report which you applied and any blocker you could not resolve (hand off as a known limitation).`,
    { phase: 'Persona', effort: 'high' }
  )
}

// ── Stage 6d: Walkthrough loop (follow for real → author fixes → fresh re-walk) ──
phase('Walkthrough')
let walkClean = false
let lastVerdict = null
for (let round = 1; round <= 3 && !walkClean; round++) {
  // Fresh-eyes participant: a NEW agent each round (never the author checking itself).
  const walk = await agent(
    `You are a first-time participant with NO context of how this workshop was built (round ${round}). Read ${ROOT}/brief.yaml for the audience tech level, then FOLLOW the workshop under ${ROOT}/docs page by page in participant order and EXECUTE every executable instruction: referenced files/datasets exist, links resolve, copy-paste prompts are self-contained, setup commands are correct, \`npm ci && npm run docs:build\` passes, and the deploy instructions work (real deploy only with credentials and a safe target — otherwise dry-run, labeled). Do NOT edit any file. WRITE ${ROOT}/artifacts/06b-walkthrough-round-${round}.md (page | severity blocker/major/minor | step followed | what happened | fix) + a completion verdict ("could I finish alone? where would I give up?"), ending with the exact marker line WALKTHROUGH_RESULT: CLEAN or WALKTHROUGH_RESULT: blockers=<n> majors=<n> minors=<n> (gate.sh 7 checks it). Return the structured review.`,
    { phase: 'Walkthrough', schema: REVIEW, label: `walk:round${round}`, agentType: 'aws-workshop-studio:participant-walker' }
  )
  const found = (walk && walk.findings) || []
  const mustFix = found.filter((f) => f.severity === 'blocker' || f.severity === 'major')
  lastVerdict = walk && walk.persona
  log(`Walkthrough round ${round}: ${found.length} findings (${mustFix.length} blocker/major)`)
  if (!mustFix.length) {
    walkClean = true
    break
  }
  // Author agent applies the fixes and rebuilds.
  await agent(
    `Author-fix round ${round}: apply these walkthrough fixes to the workshop under ${ROOT}, rebuild, and append a "changed in round ${round}" list to ${ROOT}/artifacts/06b-walkthrough-round-${round}.md: ${JSON.stringify(mustFix)}. Anything you cannot decide goes into the artifact as an open question — never silently skipped.`,
    { phase: 'Walkthrough', label: `fix:round${round}`, effort: 'high' }
  )
}
if (!walkClean) log('Walkthrough not clean after 3 rounds — remaining findings go to the handoff as known limitations (GATE-6d).')

// ── Stage 7: QA gate ────────────────────────────────────────────
phase('QA')
await agent(
  `In ${ROOT}: run \`bash scripts/workshop-check.sh --full\` (assets, datasets, presenter-notes, flows + build). Confirm no presenter-only wording leaked into docs/, list unresolved image slots. Fix the mechanical issues; report anything needing judgment. WRITE ${ROOT}/artifacts/07-qa-report.md.`,
  { phase: 'QA' }
)

// ── Stage 8: Handoff ────────────────────────────────────────────
phase('Handoff')
const handoff = await agent(
  `In ${ROOT}: run \`node scripts/image-manifest.mjs .\` to list capture-pending screenshots. WRITE ${ROOT}/artifacts/08-handoff.md with: the capture manifest, a pointer to PRESENTER_NOTES.md, the Amplify deploy steps, and remaining needs-check / known limitations (re-verify any facts past valid_until before deploy — GATE-8). Report the handoff path.`,
  { phase: 'Handoff' }
)

return {
  featureFacts: facts && facts.artifactPath,
  blueprint: blueprint && blueprint.artifactPath,
  scenesWritten: wrote.filter((w) => w.ok).length,
  personaReviews: reviews.length,
  handoff: handoff,
}
