// Seeking self-test: drives the real app through its debug port and checks the
// behaviour users feel. Run with `npm run test:seek` (needs ffmpeg-static, no extra deps).
//   - one arrow press = exactly one seek of about +-5s (no replay on key-up)
//   - playback continues after taps, quick bursts, a held key and a timeline click
import { spawn } from 'child_process';
import { createRequire } from 'module';
import fs from 'fs';
import os from 'os';
import path from 'path';
import { fileURLToPath } from 'url';

const require = createRequire(import.meta.url);
const ffmpeg = require('ffmpeg-static');
const electron = require('electron');
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const PORT = 9335;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const procs = [];
const video = path.join(os.tmpdir(), 'doggy-seek-selftest.mp4');
let failed = 0;
const check = (name, ok, detail = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name} ${detail}`); if (!ok) failed++; };

async function cleanup() {
  for (const p of procs) { try { p.kill(); } catch { /* gone */ } }
  if (process.platform === 'win32') { try { spawn('taskkill', ['/F', '/T', '/IM', 'electron.exe'], { stdio: 'ignore' }); } catch { /* ignore */ } }
  try { fs.unlinkSync(video); } catch { /* none */ }
}

async function main() {
  // Long GOP on purpose: that is where seeking used to misbehave.
  await new Promise((res, rej) => {
    const p = spawn(ffmpeg, ['-y', '-hide_banner', '-loglevel', 'error',
      '-f', 'lavfi', '-i', 'testsrc2=size=1280x720:rate=30', '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000',
      '-t', '120', '-c:v', 'libx264', '-preset', 'ultrafast', '-g', '300', '-keyint_min', '300', '-sc_threshold', '0',
      '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-movflags', '+faststart', video]);
    p.on('close', (c) => (c === 0 ? res() : rej(new Error('ffmpeg failed'))));
  });

  const up = await fetch('http://127.0.0.1:3000/').then((r) => r.ok).catch(() => false);
  if (!up) {
    procs.push(spawn(process.execPath, [path.join(root, 'node_modules', 'vite', 'bin', 'vite.js'), '--port=3000', '--host=127.0.0.1'], { cwd: root, stdio: 'ignore' }));
    for (let i = 0; i < 60 && !(await fetch('http://127.0.0.1:3000/').then((r) => r.ok).catch(() => false)); i++) await sleep(500);
  }

  procs.push(spawn(electron, ['.', `--remote-debugging-port=${PORT}`, '--disable-backgrounding-occluded-windows', '--disable-renderer-backgrounding', video], { cwd: root, stdio: 'ignore' }));
  let target;
  for (let i = 0; i < 60 && !target; i++) {
    await sleep(500);
    target = (await fetch(`http://127.0.0.1:${PORT}/json`).then((r) => r.json()).catch(() => [])).find((t) => t.type === 'page');
  }
  if (!target) throw new Error('app did not start');
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((r) => (ws.onopen = r));
  let id = 0; const pend = {};
  ws.onmessage = (e) => { const m = JSON.parse(e.data); pend[m.id]?.(m.result); };
  const send = (method, params = {}) => new Promise((r) => { const i = ++id; pend[i] = r; ws.send(JSON.stringify({ id: i, method, params })); });
  const run = async (expr) => (await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true })).result.value;
  await send('Page.bringToFront');
  await send('Emulation.setFocusEmulationEnabled', { enabled: true });

  for (let i = 0; i < 60 && !(await run(`(()=>{const v=document.querySelector('video');return !!v&&v.readyState>=3&&v.currentTime>0.5})()`)); i++) await sleep(500);

  const page = `
    const v = document.querySelector('video'); const sleep = (ms) => new Promise(r => setTimeout(r, ms));
    const key = (t, c) => window.dispatchEvent(new KeyboardEvent(t, { code: c, key: c, bubbles: true }));
    let seeks = 0; v.addEventListener('seeking', () => seeks++);
    window.__t = { v, sleep, key, get seeks() { return seeks; }, reset() { seeks = 0; } };`;
  await run(`(()=>{${page}; return 1})()`);

  // 1. Taps of a realistic length (~110ms): one seek each, +-5s.
  const taps = JSON.parse(await run(`(async()=>{const {v,sleep,key}=__t;v.currentTime=40;await sleep(1200);const out=[];
    for(let i=0;i<6;i++){__t.reset();const c=i%2?'ArrowLeft':'ArrowRight';const p=v.currentTime;key('keydown',c);await sleep(180);key('keyup',c);await sleep(700);
      out.push({seeks:__t.seeks,moved:v.currentTime-p,playing:!v.paused})}return JSON.stringify(out)})()`));
  check('each tap seeks exactly once', taps.every((t) => t.seeks === 1), JSON.stringify(taps.map((t) => t.seeks)));
  check('each tap moves about 5s', taps.every((t) => Math.abs(Math.abs(t.moved) - 5) < 1.5), JSON.stringify(taps.map((t) => +t.moved.toFixed(1))));
  check('playing after taps', taps.every((t) => t.playing));

  // 2. Quick burst: net position right, resumes once.
  const burst = JSON.parse(await run(`(async()=>{const {v,sleep,key}=__t;v.currentTime=60;await sleep(1200);const p=v.currentTime;
    for(const c of ['ArrowRight','ArrowRight','ArrowLeft','ArrowRight','ArrowRight','ArrowLeft']){key('keydown',c);await sleep(60);key('keyup',c);await sleep(150)}
    await sleep(1200);return JSON.stringify({moved:v.currentTime-p,playing:!v.paused})})()`));
  check('burst lands on the right net position (+10s)', Math.abs(burst.moved - 11.2) < 2.5, `moved ${burst.moved.toFixed(1)}`);
  check('playing after burst', burst.playing);

  // 3. Held key: moves a lot, then resumes.
  const hold = JSON.parse(await run(`(async()=>{const {v,sleep,key}=__t;v.currentTime=20;await sleep(1200);const p=v.currentTime;
    key('keydown','ArrowRight');for(let i=0;i<12;i++){await sleep(150);window.dispatchEvent(new KeyboardEvent('keydown',{code:'ArrowRight',key:'ArrowRight',repeat:true,bubbles:true}))}
    key('keyup','ArrowRight');await sleep(1200);return JSON.stringify({moved:v.currentTime-p,playing:!v.paused})})()`));
  check('held key scrubs forward', hold.moved > 8, `moved ${hold.moved.toFixed(1)}`);
  check('playing after held key', hold.playing);

  // 4. Timeline click: lands and keeps playing.
  const rect = JSON.parse(await run(`(()=>{const b=document.querySelector('input[type=range]').getBoundingClientRect();return JSON.stringify({x:b.left,w:b.width,y:b.top+b.height/2})})()`));
  const x = rect.x + rect.w * 0.5;
  await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y: rect.y });
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y: rect.y, button: 'left', clickCount: 1 });
  await sleep(60);
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y: rect.y, button: 'left', clickCount: 1 });
  await sleep(1500);
  const click = JSON.parse(await run(`JSON.stringify({t:__t.v.currentTime,playing:!__t.v.paused})`));
  check('timeline click lands near the middle', Math.abs(click.t - 60) < 8, `t=${click.t.toFixed(1)}`);
  check('playing after timeline click', click.playing);
}

main()
  .catch((e) => { console.error('ERROR', e.message); failed++; })
  .finally(async () => { await cleanup(); console.log(failed ? `\n${failed} check(s) failed` : '\nall checks passed'); process.exit(failed ? 1 : 0); });
