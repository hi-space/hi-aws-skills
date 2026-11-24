// One-take storyboard for a chat assistant inside a real web app (references/onetake.md).
// Copy next to your take, set the selectors and the turn endpoint, then:
//   node record_demo.mjs --url <site> --storyboard storyboard.mjs --name take --out raw --camera zoom --max-seconds 1500
//
// Conventions the editor relies on (onetake.py "turns"): for every chat turn <k> the storyboard notes
//   <k>_typing  <k>_typed  <k>_working  <k>_result  <k>_answer  <k>_card_<i>
// so typing plays at speeds.type, the model wait at speeds.wait with the badge, and the answer at 1x.
import fs from 'node:fs/promises';

// ------------------------------------------------------------------ app-specific (edit these)
const CHAT = '[aria-label="Assistant"]';            // the chat panel
const INPUT = '#chat-input';                         // its textbox
const SEND = { role: 'button', name: '보내기' };      // send button
const STOP = { role: 'button', name: '응답 멈추기' }; // visible while a reply streams
const ANSWERS = CHAT + ' ol > li';                   // one element per message; the last is the newest
const CARD = 'article';                              // a result card inside an answer (product, document, …)
const TURN_URL = /\/v1\/invocations$/;               // the request that carries one chat turn
const creds = JSON.parse(await fs.readFile(new URL('./.login.json', import.meta.url), 'utf8')); // chmod 600, never in git
const qa = name => new URL('./qa/' + name, import.meta.url).pathname;

export default async function ({ page, rec, tap, siteUrl }) {
  // Every turn is captured from the network, so the take can refuse to continue on a bad answer
  // instead of filming it: a 4xx/5xx, an error frame, or a guardrail stop.
  const turns = [], byReq = new Map();
  page.on('request', r => {
    if (TURN_URL.test(r.url()) && r.method() === 'POST') {
      const t = { number: turns.length + 1, body: r.postDataJSON?.() ?? null, start: rec.now() };
      turns.push(t); byReq.set(r, t);
    }
  });
  page.on('response', async r => {
    const t = byReq.get(r.request()); if (!t) return;
    try {
      t.http = r.status();
      const body = await r.text();
      // SSE: "data: {...}" lines. Adapt the frame names to your API.
      const frames = body.split('\n').filter(x => x.startsWith('data:')).map(x => { try { return JSON.parse(x.slice(5)); } catch { return {}; } });
      t.text = frames.filter(x => x.type === 'textDelta').map(x => x.data?.text ?? '').join('');
      t.tools = frames.filter(x => x.type === 'toolUse').map(x => x.data?.name);
      t.stopReason = frames.find(x => x.data?.stopReason)?.data.stopReason;
      t.error = frames.find(x => x.type === 'error')?.data;
    } catch { t.aborted = true; }
    t.done = true; t.end = rec.now();
  });
  const save = () => fs.writeFile(qa('turns.json'), JSON.stringify(turns, null, 2));
  const wait = async (pred, ms = 180000) => { const end = Date.now() + ms; while (!pred()) { if (Date.now() > end) throw Error('timeout'); await rec.sleep(250); } };

  // Fail the take early and loudly: a filmed refusal or an empty answer cannot be fixed in the edit.
  const finish = async (n, { cards = true, tool } = {}) => {
    await wait(() => turns.length >= n && turns[n - 1].done);
    const t = turns[n - 1]; await save();
    if (t.http !== 200 || t.error || t.aborted) throw Error(`turn ${n} failed: ${JSON.stringify({ http: t.http, error: t.error })}`);
    if (t.stopReason && /guardrail|content_filter/i.test(t.stopReason)) throw Error(`turn ${n} blocked by a guardrail: diagnose with the provider's apply/test API before re-recording`);
    if (tool && !t.tools?.some(x => x.includes(tool))) throw Error(`turn ${n} did not call ${tool}`);
    await page.getByRole(STOP.role, { name: STOP.name, exact: true }).waitFor({ state: 'hidden' });
    if (cards) {
      const ok = await page.locator(ANSWERS).last().locator(CARD).first().waitFor({ timeout: 8000 }).then(() => true, () => false);
      if (!ok) throw Error(`turn ${n} rendered no cards; the data may not contain a match: ${t.text?.slice(0, 300)}`);
    }
    return t;
  };
  const type = async (sel, text, delay = 55) => {
    await page.locator(sel).evaluate(e => e.focus({ preventScroll: true }));
    await page.keyboard.press('Control+A');
    for (const ch of text) { await page.keyboard.insertText(ch); await rec.sleep(delay); }
  };
  // Scroll inside the chat, not the page: the camera zoom stays put and the panel shows the new answer.
  const scrollTo = async (loc, center = false) => {
    await loc.evaluate((e, center) => {
      const c = e.closest('.overflow-y-auto') ?? e.parentElement; const z = parseFloat(document.documentElement.style.zoom) || 1;
      let y = (e.getBoundingClientRect().top - c.getBoundingClientRect().top) / z + c.scrollTop;
      if (center) y -= (c.clientHeight - e.offsetHeight) / 2;
      c.scrollTo({ top: y, behavior: 'smooth' });
    }, center);
    await rec.sleep(1300);
  };
  const showAnswer = async (key, maxCards = 2, hold = 5200) => {
    const fresh = page.locator(ANSWERS).last();
    await scrollTo(fresh); rec.note(key + '_answer'); await rec.sleep(4200);
    const cards = fresh.locator(CARD); const n = await cards.count();
    for (let i = 0; i < Math.min(n, maxCards); i++) {
      await scrollTo(cards.nth(i), true); rec.note(`${key}_card_${i}`); await rec.sleep(hold);
    }
    await page.screenshot({ path: qa(key + '.png') });
  };
  const send = async (key, text, opts = {}) => {
    await rec.focus(key + '_input', CHAT, { kmax: 1.12 }); rec.note(key + '_typing');
    await type(INPUT, text); rec.note(key + '_typed'); await rec.sleep(1500);
    const n = turns.length + 1;
    await tap(page.getByRole(SEND.role, { name: SEND.name, exact: true }));
    rec.note(key + '_working');
    const t = await finish(n, opts); rec.note(key + '_result');
    return t;
  };

  try {
    await page.goto(siteUrl, { waitUntil: 'domcontentloaded' });
    await page.evaluate(() => document.fonts.ready); await rec.sleep(2500);
    await rec.install(); await rec.reset('home'); rec.note('home'); await rec.sleep(6000);

    // … sign in here if the story needs it (note 'cognito' / 'signed_in' around it, ramp it at 2.5x) …

    await send('first', '겨울 출근용 네이비 코트를 90만 원 이하로 두 벌 추천해 주세요.');
    await showAnswer('first', 2);
    await send('followup', '예산을 80만 원으로 낮춰서 한 벌만 다시 찾아 주세요.');
    await showAnswer('followup', 1);

    // Deleting data on camera: identify the item by an ID you recorded in this take, never by position.
    // const tag = 'ID ···' + turns.at(-1).body.session_id.slice(-8);
    // const target = page.locator('li').filter({ hasText: tag });
    // if (await target.count() !== 1) throw Error('refusing to delete ' + tag);

    await rec.reset('final'); rec.note('end'); await rec.sleep(3000);
  } finally { await save(); }
}
