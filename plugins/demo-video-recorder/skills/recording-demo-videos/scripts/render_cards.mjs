#!/usr/bin/env node
/**
 * Render every cards/*.html to a 1920x1080 PNG next to it (one-take intro, architecture and summary cards).
 *
 *   node render_cards.mjs <cards-dir> [--playwright-root <dir>]
 *
 * HTML cards beat text-only cards when a card needs real layout: service icons, product photos, a grid of
 * features. Start from assets/card-template.html; reference images and fonts with file:// paths or data URIs
 * (the page is opened from disk). Read every PNG before assembling.
 */
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const argv = process.argv.slice(2);
const dir = path.resolve(argv.find(a => !a.startsWith('--')) ?? 'cards');
const i = argv.indexOf('--playwright-root');
const root = path.resolve(i >= 0 ? argv[i + 1] : process.env.PLAYWRIGHT_ROOT || process.cwd());
const { chromium } = createRequire(path.join(root, 'package.json'))('playwright');

const files = fs.readdirSync(dir).filter(f => f.endsWith('.html')).sort();
if (!files.length) { console.error(`no .html cards in ${dir}`); process.exit(2); }
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
for (const f of files) {
  await page.goto('file://' + path.join(dir, f), { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  const overflow = await page.evaluate(() => document.documentElement.scrollHeight > 1081 || document.documentElement.scrollWidth > 1921);
  const out = path.join(dir, f.replace(/\.html$/, '.png'));
  await page.screenshot({ path: out });
  console.log(out + (overflow ? '  ⚠ content overflows 1920x1080' : ''));
}
await browser.close();
