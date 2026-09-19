#!/usr/bin/env node
// ─────────────────────────────────────────────────────────────
// image-manifest.mjs — Scan a workshop's image slots and build the pending-capture list.
//
//   node image-manifest.mjs [workshop-root]   (default: current directory)
//
//   Collects:
//     · <Screenshot src="..."> from docs/**/*.md
//     · img: '...' from docs/.vitepress/data/features.ts and flows.ts
//   Decides whether each path exists under docs/public -> writes the missing
//   (pending-capture) list to artifacts/08-image-manifest.json and a console table.
// ─────────────────────────────────────────────────────────────
import { readFileSync, readdirSync, existsSync, mkdirSync, writeFileSync, statSync } from 'node:fs'
import { join, resolve, relative } from 'node:path'

const ROOT = resolve(process.argv[2] || process.cwd())
const DOCS = join(ROOT, 'docs')
const PUBLIC = join(DOCS, 'public')

function walk(dir, filter, out = []) {
  let entries = []
  try { entries = readdirSync(dir, { withFileTypes: true }) } catch { return out }
  for (const e of entries) {
    const p = join(dir, e.name)
    if (e.isDirectory()) {
      if (e.name === 'node_modules' || e.name === 'dist' || e.name === 'cache') continue
      walk(p, filter, out)
    } else if (filter(e.name)) {
      out.push(p)
    }
  }
  return out
}

// Collect: src -> set of source files that reference it
const refs = new Map() // src (string, /images/... form) -> Set(sourceFile)
const addRef = (src, from) => {
  if (!src) return
  // Skip external URLs and data URIs
  if (/^(https?:)?\/\//.test(src) || src.startsWith('data:')) return
  const key = src.trim()
  if (!refs.has(key)) refs.set(key, new Set())
  refs.get(key).add(relative(ROOT, from))
}

// 1) <Screenshot src="..."> in markdown (src='...' also allowed)
const mdFiles = walk(DOCS, (n) => n.endsWith('.md'))
const shotRe = /<Screenshot[^>]*\bsrc\s*=\s*["']([^"']+)["']/g
for (const f of mdFiles) {
  const txt = readFileSync(f, 'utf8')
  let m
  while ((m = shotRe.exec(txt))) addRef(m[1], f)
}

// 2) img: '...' in features.ts / flows.ts
const dataDir = join(DOCS, '.vitepress', 'data')
const imgRe = /\bimg\s*:\s*["']([^"']+)["']/g
for (const name of ['features.ts', 'flows.ts']) {
  const f = join(dataDir, name)
  if (!existsSync(f)) continue
  const txt = readFileSync(f, 'utf8')
  let m
  while ((m = imgRe.exec(txt))) addRef(m[1], f)
}

// Decision: existence relative to docs/public
const entries = [...refs.entries()]
  .map(([src, from]) => {
    const abs = join(PUBLIC, src.replace(/^\//, ''))
    const exists = existsSync(abs) && statSync(abs).isFile()
    return { src, exists, referencedBy: [...from].sort() }
  })
  .sort((a, b) => a.src.localeCompare(b.src))

const missing = entries.filter((e) => !e.exists)
const present = entries.filter((e) => e.exists)

// Output: artifacts/08-image-manifest.json
const manifest = {
  generatedAt: new Date().toISOString(),
  root: ROOT,
  total: entries.length,
  presentCount: present.length,
  missingCount: missing.length,
  missing: missing.map(({ src, referencedBy }) => ({ src, referencedBy })),
  present: present.map(({ src }) => src),
}
const outDir = join(ROOT, 'artifacts')
mkdirSync(outDir, { recursive: true })
const outFile = join(outDir, '08-image-manifest.json')
writeFileSync(outFile, JSON.stringify(manifest, null, 2) + '\n')

// Console table
console.log(`\nImage manifest — ${relative(process.cwd(), outFile) || outFile}`)
console.log(`  ${entries.length} references · ${present.length} present · ${missing.length} pending capture\n`)
if (missing.length) {
  console.log('  Pending capture (not found under docs/public):')
  for (const e of missing) {
    console.log(`    ✗ ${e.src}`)
    console.log(`        ← ${e.referencedBy.join(', ')}`)
  }
} else {
  console.log('  All image references exist.')
}
console.log('')
