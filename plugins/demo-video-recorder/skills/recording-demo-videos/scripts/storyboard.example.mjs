// Storyboard for record_demo.mjs: one exported async function that drives the page and the camera.
// Adapt selectors and the probe to the UI being recorded. Fixed rec.sleep holds are enough when you know what happens;
// the probe loop below is for UIs that change at unpredictable times.
export default async function storyboard({ page, rec, tap, siteUrl, maxSeconds }) {
  await page.goto(`${siteUrl}/?paused=1`, { waitUntil: 'networkidle' });   // ?paused=1 is this app's own feature; polling apps: waitForSelector
  await page.waitForTimeout(1500);                                          // fonts, WebGL, layout settle
  await rec.install();                                                      // camera must be installed after load

  await rec.reset('hero', 'Page overview');                                  // label = edit-sheet note; captions come from the script
  await rec.sleep(2500);
  await rec.region('stage', 60, 440, 1800, 1012, { pad: 0, kmax: 1.08 }, 'Robot + decision stack');

  await tap(page.locator('.play-button'));                                  // tap, never click(): click() scrolls
  rec.note('play');

  // Event-driven shots: poll the UI for state changes and cut to the panel that changed.
  const started = rec.now();
  let prev = await probe(page);
  let holdUntil = 0;
  while (rec.now() - started < maxSeconds) {
    await rec.sleep(300);
    const cur = await probe(page);
    if (cur.done) { rec.note('scene_end'); break; }
    const free = rec.now() >= holdUntil;
    if (free && cur.thinking && !prev.thinking) {
      await rec.focus('decision', '.judgment-panel', { pad: 12, kmax: 1.75 }, 'System 2 deciding');
      holdUntil = rec.now() + 5.5;
    } else if (free && rec.since() > 12 && rec.lastKey !== 'stage') {
      await rec.region('stage', 60, 440, 1800, 1012, { pad: 0, kmax: 1.08 });   // return to the wide stage
    }
    prev = cur;
  }
  await rec.focus('trace', '.trace-panel', { pad: 10, kmax: 1.5, anchorTop: true }, 'Every decision leaves a trace');
  await rec.sleep(4500);
}

// Read only cheap DOM facts; keep the probe under ~50 ms so the loop stays responsive.
async function probe(page) {
  return page.evaluate(() => ({
    thinking: !!document.querySelector('.judgment-panel .executing'),
    done: /100 ?%|완료|Done/.test(document.querySelector('.playback-time')?.textContent ?? ''),
  }));
}
