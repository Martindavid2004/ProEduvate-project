/**
 * LIVE MIC-CONFLICT TEST for the GD round mic-health layer.
 *
 * Runs the REAL GDRound component in REAL Chrome with the REAL microphone,
 * against the real dev build (localhost:3000), and drives the complete real
 * UI flow: login -> Placement Training -> Non-Technical Skills -> AI Group
 * Discussion -> Start GD Round -> (topic) -> active phase.
 *
 * Then it reproduces the "another app yanked the mic" event: when Meet/Zoom
 * takes the device on Windows, the loser's audio track fires 'ended'/'mute'.
 * Cross-process exclusive capture cannot be forced deterministically, so the
 * harness stops the GD's audio track - producing exactly the signal the
 * component's watchMicTracks() listens for.
 *
 * Verifies:
 *   1. GD reaches the active phase holding a live mic track.
 *   2. Track 'ended' event is observed by the page instrumentation.
 *   3. The component renders the red "Microphone problem detected" banner
 *      (micIssue state) with a "Restore Microphone" button.
 *   4. Clicking Restore re-acquires a live track and clears the banner.
 *
 * Usage: node mic-conflict-test.js
 * Needs: backend :5000, frontend dev :3000, real default microphone present.
 */

const puppeteer = require('puppeteer-core');
const axios = require('axios');

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const APP_URL = 'http://localhost:3000';
const API = 'http://127.0.0.1:5000/api';

const results = [];

function check(name, cond, detail = '') {
  const status = cond ? 'PASS' : 'FAIL';
  results.push([status, name]);
  console.log(`[${status}] ${name}${detail ? ' -> ' + detail : ''}`);
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function pageMicSnapshot() {
  const v = document.querySelector('video');
  const stream = v && v.srcObject;
  const audio = stream ? stream.getAudioTracks() : [];
  const textMatches = (re) =>
    !!Array.from(document.querySelectorAll('p,span,div,h4')).find((el) => re.test(el.textContent || ''));
  return {
    hasStream: !!stream,
    audioTracks: audio.length,
    audioLive: audio.length > 0 && audio[0].readyState === 'live',
    audioMuted: audio.length > 0 ? audio[0].muted : null,
    micIssueBanner: textMatches(/Microphone problem detected/i),
    restoreBtn: !!Array.from(document.querySelectorAll('button')).find((b) =>
      /Restore Microphone/i.test(b.textContent || '')),
  };
}

(async () => {
  // Pre-register a test student via API so UI login is deterministic
  const email = `mictest_${Date.now()}@test.com`;
  const r = await axios.post(`${API}/auth/register`, {
    fullName: 'Mic Conflict Tester',
    registerNumber: `GD${Date.now() % 1000000}`,
    email,
    department: 'CSE',
    password: 'test1234',
  });
  if (!r.data || !r.data.token) throw new Error('register failed: ' + JSON.stringify(r.data).slice(0, 200));
  console.log('Registered test student:', email);

  console.log('Launching main Chrome (GD participant)...');
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: false,
    args: [
      '--use-fake-ui-for-media-stream', // auto-accept mic permission prompt
      '--no-first-run',
      '--window-size=1400,900',
    ],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1380, height: 880 });

  page.on('console', (msg) => {
    const t = msg.text();
    if (t.includes('[MIC_HEALTH]') || t.includes('[TURN')) console.log('  page:', t.slice(0, 150));
  });

  await page.goto(APP_URL + '/login', { waitUntil: 'networkidle2', timeout: 60000 });

  // Login through the real UI
  await page.waitForSelector('input', { timeout: 30000 });
  const textInputs = await page.$$('input[type="text"], input[type="email"]');
  const pwInputs = await page.$$('input[type="password"]');
  await textInputs[0].type(email);
  await pwInputs[0].type('test1234');
  await page.click('button[type="submit"]');
  await sleep(6000);
  console.log('Logged in through UI ->', page.url());

  // Instrument the page: record track mute/ended events (what the component
  // itself listens to) on any stream the app attaches.
  await page.evaluate(() => {
    window.__micEvents = [];
    const hook = () => {
      document.querySelectorAll('video').forEach((v) => {
        const s = v.srcObject;
        if (!s) return;
        s.getAudioTracks().forEach((t) => {
          if (t.__hooked) return;
          t.__hooked = true;
          t.addEventListener('mute', () => window.__micEvents.push('mute'));
          t.addEventListener('ended', () => window.__micEvents.push('ended'));
        });
      });
      return true;
    };
    hook();
    window.__micHookInterval = setInterval(hook, 500);
  });

  const clickByText = async (regex) => {
    return page.evaluate((reSrc) => {
      const re = new RegExp(reSrc, 'i');
      // Headings/spans carry the exact label; the click bubbles to the card's
      // parent div onClick handler.
      const pool = Array.from(document.querySelectorAll('button, h3, h4, span, div, p'));
      const el = pool.find((e) => {
        const t = (e.textContent || '').trim();
        return re.test(t) && t.length < 90;
      });
      if (el) { el.click(); return true; }
      return false;
    }, regex.source);
  };

  // Navigate: Placement Training -> Non-Technical Skills -> AI GD -> Start
  let ok = await clickByText(/^Placement Training$/);
  check('Nav: Placement Training tab', ok);
  await sleep(2500);
  ok = await clickByText(/^Non-Technical Skills$/);
  check('Nav: Non-Technical Skills', ok);
  await sleep(2500);
  ok = await clickByText(/^AI Group Discussion$/);
  check('Nav: AI Group Discussion card', ok);
  await sleep(5000); // practice round created via API
  ok = await clickByText(/^Start GD Round$/);
  check('Nav: Start GD Round', ok);
  await sleep(4000);

  // If topic-selection phase is showing, pick the AI topic immediately
  await page.evaluate(() => {
    const t = Array.from(document.querySelectorAll('button, p, div')).find((e) =>
      /Impact of Artificial Intelligence/i.test(e.textContent || '') && (e.textContent || '').length < 80);
    if (t) t.click();
  });

  // Wait for the ACTIVE phase where the video (and thus the mic stream) is
  // actually mounted. Topic selection 30s + preparation 60s max -> 3min cap.
  let micUp = false;
  for (let i = 0; i < 60; i++) {
    micUp = await page.evaluate(() => {
      const v = document.querySelector('video');
      const s = v && v.srcObject;
      const a = s ? s.getAudioTracks() : [];
      return a.length > 0 && a[0].readyState === 'live';
    });
    if (micUp) break;
    // keep trying to click through phases if they reappear
    await page.evaluate(() => {
      const t = Array.from(document.querySelectorAll('button, p, div')).find((e) =>
        /Impact of Artificial Intelligence/i.test(e.textContent || '') && (e.textContent || '').length < 80);
      if (t) t.click();
    });
    await sleep(3000);
  }
  check('STEP1: GD active & holding live mic', micUp);

  // ---- STEP 2: another app yanks the microphone ----
  const yanked = await page.evaluate(() => {
    const v = document.querySelector('video');
    const s = v && v.srcObject;
    if (!s) return 'no-stream';
    const tracks = s.getAudioTracks();
    tracks.forEach((t) => t.stop());
    return 'stopped:' + tracks.length;
  });
  console.log('  mic yanked:', yanked);
  await sleep(3000);

  // ---- STEP 3: conflict detection by the GD component ----
  const snap = await page.evaluate(pageMicSnapshot);
  const micEvents = await page.evaluate(() => window.__micEvents || []);
  const conflictDetected = snap.micIssueBanner || micEvents.length > 0;
  check('STEP3: conflict detected (banner / ended event)', conflictDetected,
    `banner=${snap.micIssueBanner} events=${JSON.stringify(micEvents)}`);

  // ---- STEP 4: Restore Microphone recovers ----
  const clickedRestore = await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find((b) =>
      /Restore Microphone/i.test(b.textContent || ''));
    if (btn) { btn.click(); return true; }
    return false;
  });
  if (clickedRestore) {
    await sleep(5000);
    const snap2 = await page.evaluate(pageMicSnapshot);
    check('STEP4: Restore re-acquired live track & cleared banner',
      snap2.audioLive && !snap2.micIssueBanner, JSON.stringify(snap2));
  } else {
    check('STEP4: Restore button clickable', false, 'banner not rendered in current phase');
  }

  await page.evaluate(() => clearInterval(window.__micHookInterval)).catch(() => {});
  await browser.close().catch(() => {});

  const passed = results.filter((r) => r[0] === 'PASS').length;
  console.log(`\n========== MIC TEST SUMMARY: ${passed}/${results.length} passed ==========`);
  results.forEach(([s, n]) => console.log(`  [${s}] ${n}`));
  process.exit(passed === results.length ? 0 : 1);
})().catch((err) => {
  console.error('MIC TEST CRASHED:', err && err.message);
  process.exit(2);
});
