#!/usr/bin/env node
/**
 * Record a web UI with Playwright while an in-page "virtual camera" pans and zooms.
 *
 *   node record_demo.mjs --url https://site --storyboard ./storyboard.mjs --name intro [--out raw] [--max-seconds 150]
 *
 * Output: <out>/<name>.webm (1920x1080, wall-clock video) + <out>/<name>.camlog.json (every shot with
 * its time and label, used by edit_demo.py to place captions).
 *
 * The camera is a CSS transform on <body> (scale + translate, 1.4 s eased transition) applied while
 * Playwright records the full 1920x1080 viewport. Cropping the recording afterwards is blurry; the
 * in-page transform re-rasterizes text at the new scale so zoomed shots stay crisp.
 *
 * Playwright is resolved from --playwright-root / $PLAYWRIGHT_ROOT / cwd (a dir with node_modules).
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';

const argv = process.argv.slice(2);
const option = (name, fallback) => { const i = argv.indexOf(name); return i < 0 ? fallback : argv[i + 1]; };

const siteUrl = option('--url', process.env.DEMO_URL);
const storyboardPath = option('--storyboard');
if (!siteUrl || !storyboardPath) { console.error('usage: record_demo.mjs --url <site> --storyboard <file.mjs> [--name n] [--out dir] [--max-seconds n]'); process.exit(2); }
const name = option('--name', path.basename(storyboardPath, path.extname(storyboardPath)));
const outDir = path.resolve(option('--out', 'raw'));
const maxSeconds = Number(option('--max-seconds', 150));
await fs.mkdir(outDir, { recursive: true });

const pwRoot = path.resolve(option('--playwright-root', process.env.PLAYWRIGHT_ROOT || process.cwd()));
const { chromium } = createRequire(path.join(pwRoot, 'package.json'))('playwright');

// Output is always 1920x1080 and the viewport must be exactly that: Playwright's recordVideo captures CSS
// pixels, so a smaller viewport with deviceScaleFactor > 1 lands top-left in the frame with blank margins.
const W = 1920, H = 1080;

// ---------------------------------------------------------------- camera (runs inside the page)
const CAMERA_JS = `
(() => {
  if (window.__cam) return;
  const style = document.createElement('style');
  style.textContent = 'html{overflow:hidden!important;background:#0b0f14}body{overflow:visible!important;transform-origin:0 0;transition:transform var(--cam-dur,1.4s) cubic-bezier(.5,0,.15,1);will-change:transform}::-webkit-scrollbar{display:none}';
  document.head.appendChild(style);
  const W = ${W}, H = ${H};
  const state = { x: 0, y: 0, k: 1 };
  const pageSize = () => ({ w: Math.max(document.body.offsetWidth, W), h: Math.max(document.body.offsetTop + document.body.offsetHeight, H) });
  // Element rect in untransformed page coordinates: invert the current body transform and fold in scroll,
  // otherwise the second shot measures a rect that is already scaled by the first.
  const untransformed = el => {
    const r = el.getBoundingClientRect(), sx = window.scrollX, sy = window.scrollY;
    const m = new DOMMatrix(getComputedStyle(document.body).transform).inverse();
    const a = m.transformPoint(new DOMPoint(r.left + sx, r.top + sy)), b = m.transformPoint(new DOMPoint(r.right + sx, r.bottom + sy));
    return { x: a.x, y: a.y, w: b.x - a.x, h: b.y - a.y };
  };
  const apply = (x, y, k, dur) => {
    const page = pageSize();
    if (window.scrollX || window.scrollY) window.scrollTo(0, 0);
    k = Math.max(1, Math.min(k, 2.6));
    x = Math.max(0, Math.min(x, page.w - W / k));
    y = Math.max(0, Math.min(y, page.h - H / k));
    document.body.style.setProperty('--cam-dur', (dur ?? 1.4) + 's');
    document.body.style.transform = 'scale(' + k + ') translate(' + (-x) + 'px,' + (-y) + 'px)';
    Object.assign(state, { x, y, k });
    return { x, y, k };
  };
  const fitRect = (r, opts = {}) => {
    const pad = opts.pad ?? 24, kmax = opts.kmax ?? 2.2;
    let k = Math.min(W / (r.w + 2 * pad), H / (r.h + 2 * pad), kmax);
    k = Math.max(1, k);
    const cx = r.x + r.w / 2, cy = (opts.anchorTop ? r.y + H / k / 2 - pad : r.y + r.h / 2);
    return apply(cx - W / k / 2, cy - H / k / 2, k, opts.dur);
  };
  const focus = (selector, opts = {}) => {
    const els = typeof selector === 'string' ? [...document.querySelectorAll(selector)] : [selector];
    const el = els[opts.index ?? 0];
    if (!el) return null;
    const r = untransformed(el);
    if (r.w < 2 || r.h < 2) return null;
    return fitRect(r, opts);
  };
  const region = (x, y, w, h, opts = {}) => fitRect({ x, y, w, h }, opts);
  const reset = dur => apply(0, 0, 1, dur);
  const rect = selector => { const el = document.querySelector(selector); return el ? untransformed(el) : null; };
  window.__cam = { focus, region, reset, rect, apply, state, pageSize };
})();`;

// Playwright's click()/fill() scroll the target into view, which fights the camera transform. Dispatch instead.
const tap = async locator => { await locator.first().waitFor({ state: 'visible' }); await locator.first().dispatchEvent('click'); };

class Recorder {
  constructor(page, name) { this.page = page; this.name = name; this.log = []; this.t0 = Date.now(); this.lastShot = 0; this.lastKey = ''; }
  now() { return (Date.now() - this.t0) / 1000; }
  note(kind, data = {}) { this.log.push({ t: +this.now().toFixed(2), kind, ...data }); }
  async install() { await this.page.evaluate(CAMERA_JS); }
  async shot(key, fn, label) {
    const result = await this.page.evaluate(fn).catch(error => ({ error: String(error) }));
    this.lastShot = this.now(); this.lastKey = key;
    // null = selector matched nothing (or a 0-size element): the camera did not move. Say so loudly; a silent
    // no-op here means a whole take with the wrong framing.
    const missing = result === null;
    this.note('shot', { key, label, camera: result, ...(missing ? { missing: true } : {}) });
    if (missing) console.warn(`[${this.now().toFixed(1)}s] shot ${key}: selector matched nothing, camera unchanged`);
    else console.log(`[${this.now().toFixed(1)}s] shot ${key}${label ? ' — ' + label : ''}`);
    return result;
  }
  /** Zoom to fit an element. opts: pad (px), kmax (zoom cap), index, anchorTop, dur (s). label → caption. */
  async focus(key, selector, opts = {}, label) { return this.shot(key, `window.__cam.focus(${JSON.stringify(selector)}, ${JSON.stringify(opts)})`, label); }
  /** Zoom to fit a page-coordinate rectangle. */
  async region(key, x, y, w, h, opts = {}, label) { return this.shot(key, `window.__cam.region(${x},${y},${w},${h},${JSON.stringify(opts)})`, label); }
  async reset(key = 'wide', label) { return this.shot(key, 'window.__cam.reset()', label); }
  since() { return this.now() - this.lastShot; }
  async sleep(ms) { await this.page.waitForTimeout(ms); }
}

// ---------------------------------------------------------------- main
const browser = await chromium.launch({ headless: true, args: ['--disable-dev-shm-usage', '--autoplay-policy=no-user-gesture-required'] });
const context = await browser.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: 1, acceptDownloads: true, recordVideo: { dir: outDir, size: { width: W, height: H } } });
const page = await context.newPage();
page.setDefaultTimeout(30000);
const errors = [];
page.on('pageerror', e => errors.push(e.message));
const rec = new Recorder(page, name);
let ok = false;
try {
  const { default: storyboard } = await import(pathToFileURL(path.resolve(storyboardPath)).href);
  await storyboard({ page, rec, tap, siteUrl, maxSeconds, option });
  ok = true;
} catch (error) {
  rec.note('error', { message: String(error) });
  console.error(error);
  await page.screenshot({ path: path.join(outDir, `${name}.error.png`) }).catch(() => {});
} finally {
  await rec.sleep(1200);
  const video = page.video();
  await context.close();
  const recorded = await video.path();
  const target = path.join(outDir, `${name}.webm`);
  await fs.copyFile(recorded, target);
  await fs.unlink(recorded).catch(() => {});
  await fs.writeFile(path.join(outDir, `${name}.camlog.json`), JSON.stringify({ name, url: siteUrl, ok, errors, duration_s: rec.now(), log: rec.log }, null, 2));
  await browser.close();
  console.log(JSON.stringify({ video: target, ok, seconds: rec.now(), errors: errors.length }));
}
process.exit(ok ? 0 : 1);
