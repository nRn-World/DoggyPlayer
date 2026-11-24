/**
 * Format self-test for Doggy Player — "every format must work".
 *
 * Generates one tiny sample per (container, video codec, audio codec) class
 * with the bundled ffmpeg, opens each sample in the RUNNING app exactly the way
 * Explorer/CLI does (`__initialVideoInfo` + `electron-file-opened`), and checks
 * the real <video> element for a decoded picture and decoded audio. Anything
 * Chromium cannot decode must come up through the re-encoding pipe — the test
 * only cares that the user sees and hears the file.
 *
 * Usage:
 *   1. start the app with a debug port:
 *        npm run dev          (in one terminal, or dev:electron)
 *        electron . --remote-debugging-port=9222 --autoplay-policy=no-user-gesture-required
 *   2. node scripts/format-selftest.mjs [--only=<substring>] [--keep] [--timeout=15000]
 *
 * Exit code 0 = every generated sample played with picture + audio.
 */
import { spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const here = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(here, '..');

const arg = (name, dflt) => {
  const hit = process.argv.find((a) => a.startsWith(`--${name}=`));
  return hit ? hit.slice(name.length + 3) : dflt;
};
const KEEP = process.argv.includes('--keep');
const ONLY = arg('only', '');
const TIMEOUT = Number(arg('timeout', '15000'));
const PORT = Number(arg('port', '9222'));

const ffmpegExe = process.platform === 'win32'
  ? path.join(projectRoot, 'node_modules', 'ffmpeg-static', 'ffmpeg.exe')
  : path.join(projectRoot, 'node_modules', 'ffmpeg-static', 'ffmpeg');

const outDir = path.join(os.tmpdir(), 'doggy-format-lab');
fs.rmSync(outDir, { recursive: true, force: true });
fs.mkdirSync(outDir, { recursive: true });

/** 2s testsrc2 + 440 Hz sine; tiny on purpose so generation is fast. */
const sources = (size = '320x240', rate = 15) => ([
  '-f', 'lavfi', '-i', `testsrc2=size=${size}:rate=${rate}:duration=2`,
  '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000:duration=2'
]);
const X264 = ['-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '28', '-pix_fmt', 'yuv420p'];
const VP9 = ['-c:v', 'libvpx-vp9', '-deadline', 'realtime', '-cpu-used', '8', '-crf', '45', '-b:v', '0'];
const AV1 = ['-c:v', 'libaom-av1', '-cpu-used', '8', '-crf', '45', '-b:v', '0'];

const SAMPLES = [
  // MP4 family — the everyday container.
  { name: 'mp4_h264_aac', ext: 'mp4', args: [...sources(), ...X264, '-c:a', 'aac'] },
  { name: 'mp4_hevc_aac', ext: 'mp4', args: [...sources(), '-c:v', 'libx265', '-preset', 'ultrafast', '-crf', '36', '-pix_fmt', 'yuv420p', '-tag:v', 'hvc1', '-c:a', 'aac'] },
  { name: 'mp4_mpeg4_aac', ext: 'mp4', args: [...sources(), '-c:v', 'mpeg4', '-q:v', '8', '-c:a', 'aac'] },
  // ffmpeg's MP4 muxer refuses H.263, so this is written with the 3gp muxer
  // (same ISO base media format) under a .mp4 name — exactly the shape of the
  // Android/WhatsApp files that used to come up black.
  { name: 'mp4_h263_aac', ext: 'mp4', args: [...sources('176x144', 12), '-c:v', 'h263', '-c:a', 'aac', '-f', '3gp'] },
  { name: 'mp4_mjpeg_aac', ext: 'mp4', args: [...sources(), '-c:v', 'mjpeg', '-pix_fmt', 'yuvj420p', '-q:v', '10', '-c:a', 'aac'] },
  { name: 'mp4_av1_aac', ext: 'mp4', args: [...sources(), ...AV1, '-c:a', 'aac'] },
  { name: 'mp4_vp9_aac', ext: 'mp4', args: [...sources(), ...VP9, '-c:a', 'aac'] },
  { name: 'mp4_h264_ac3', ext: 'mp4', args: [...sources(), ...X264, '-c:a', 'ac3', '-b:a', '192k'] },
  { name: 'mp4_h264_mp3', ext: 'mp4', args: [...sources(), ...X264, '-c:a', 'libmp3lame', '-b:a', '128k'] },
  { name: 'mp4_h264_flac', ext: 'mp4', args: [...sources(), ...X264, '-c:a', 'flac'] },
  { name: 'mp4_h264_alac', ext: 'mp4', args: [...sources(), ...X264, '-c:a', 'alac'] },
  { name: 'mp4_h264_dts', ext: 'mp4', args: [...sources(), ...X264, '-c:a', 'dca', '-strict', '-2', '-b:a', '768k'] },
  { name: 'mp4_h264_pcm', ext: 'mp4', args: [...sources(), ...X264, '-c:a', 'pcm_s16le'] },
  { name: 'm4v_h264_aac', ext: 'm4v', args: [...sources(), ...X264, '-c:a', 'aac'] },
  // MOV / QuickTime — camera files.
  { name: 'mov_h264_aac', ext: 'mov', args: [...sources(), ...X264, '-c:a', 'aac'] },
  { name: 'mov_mjpeg_pcm', ext: 'mov', args: [...sources(), '-c:v', 'mjpeg', '-pix_fmt', 'yuvj420p', '-q:v', '10', '-c:a', 'pcm_s16le'] },
  { name: 'mov_prores_pcm', ext: 'mov', args: [...sources(), '-c:v', 'prores_ks', '-profile:v', '0', '-c:a', 'pcm_s16le'] },
  // Matroska / WebM.
  { name: 'mkv_h264_aac', ext: 'mkv', args: [...sources(), ...X264, '-c:a', 'aac'] },
  { name: 'mkv_hevc_ac3', ext: 'mkv', args: [...sources(), '-c:v', 'libx265', '-preset', 'ultrafast', '-crf', '36', '-pix_fmt', 'yuv420p', '-c:a', 'ac3'] },
  { name: 'webm_vp9_opus', ext: 'webm', args: [...sources(), ...VP9, '-c:a', 'libopus'] },
  { name: 'webm_vp8_vorbis', ext: 'webm', args: [...sources(), '-c:v', 'libvpx', '-deadline', 'realtime', '-cpu-used', '8', '-b:v', '200k', '-c:a', 'libvorbis'] },
  { name: 'webm_av1_opus', ext: 'webm', args: [...sources(), ...AV1, '-c:a', 'libopus'] },
  // AVI — old desktop files.
  { name: 'avi_mpeg4_mp3', ext: 'avi', args: [...sources(), '-c:v', 'mpeg4', '-q:v', '8', '-c:a', 'libmp3lame'] },
  { name: 'avi_mpeg2_mp2', ext: 'avi', args: [...sources(), '-c:v', 'mpeg2video', '-q:v', '8', '-c:a', 'mp2'] },
  { name: 'avi_mjpeg_pcm', ext: 'avi', args: [...sources(), '-c:v', 'mjpeg', '-pix_fmt', 'yuvj420p', '-q:v', '10', '-c:a', 'pcm_s16le'] },
  { name: 'avi_h264_aac', ext: 'avi', args: [...sources(), ...X264, '-c:a', 'aac'] },
  // Broadcast / transport streams.
  { name: 'ts_h264_aac', ext: 'ts', args: [...sources(), ...X264, '-c:a', 'aac'] },
  { name: 'ts_mpeg2_mp2', ext: 'ts', args: [...sources(), '-c:v', 'mpeg2video', '-q:v', '8', '-c:a', 'mp2'] },
  { name: 'm2ts_h264_ac3', ext: 'm2ts', args: [...sources(), ...X264, '-c:a', 'ac3'] },
  { name: 'vob_mpeg2_ac3', ext: 'vob', args: [...sources('720x576', 25), '-c:v', 'mpeg2video', '-b:v', '3M', '-c:a', 'ac3', '-b:a', '192k', '-f', 'dvd'] },
  { name: 'mxf_mpeg2_pcm', ext: 'mxf', args: [...sources('720x576', 25), '-c:v', 'mpeg2video', '-q:v', '8', '-c:a', 'pcm_s16le'] },
  { name: 'dv_dvvideo_pcm', ext: 'dv', args: [...sources('720x576', 25), '-c:v', 'dvvideo', '-pix_fmt', 'yuv420p', '-c:a', 'pcm_s16le', '-ar', '48000', '-ac', '2'] },
  // Flash, Windows Media, MPEG program stream.
  { name: 'flv_flv1_mp3', ext: 'flv', args: [...sources(), '-c:v', 'flv', '-q:v', '8', '-c:a', 'libmp3lame', '-ar', '44100'] },
  { name: 'wmv_wmv2_wma', ext: 'wmv', args: [...sources(), '-c:v', 'wmv2', '-b:v', '300k', '-c:a', 'wmav2', '-b:a', '96k', '-f', 'asf'] },
  { name: 'mpg_mpeg2_mp2', ext: 'mpg', args: [...sources(), '-c:v', 'mpeg2video', '-q:v', '8', '-c:a', 'mp2', '-f', 'mpeg'] },
  // Old phones / Ogg.
  { name: '3gp_h263_amr', ext: '3gp', args: [...sources('176x144', 12), '-c:v', 'h263', '-c:a', 'libopencore_amrnb', '-ar', '8000', '-ac', '1', '-b:a', '12.2k', '-strict', '-2'] },
  { name: '3gp_h264_aac', ext: '3gp', args: [...sources('320x240', 12), ...X264, '-c:a', 'aac'] },
  { name: 'ogv_theora_vorbis', ext: 'ogv', args: [...sources(), '-c:v', 'libtheora', '-q:v', '5', '-c:a', 'libvorbis', '-f', 'ogg'] }
];

// ---- generate --------------------------------------------------------------
console.log(`Generating ${SAMPLES.length} samples in ${outDir} …\n`);
const generated = [];
let genFailed = 0;
for (const s of SAMPLES) {
  if (ONLY && !s.name.includes(ONLY)) continue;
  const file = path.join(outDir, `${s.name}.${s.ext}`);
  const r = spawnSync(ffmpegExe, ['-y', '-hide_banner', '-loglevel', 'error', ...s.args, file], { encoding: 'utf8' });
  if (r.status === 0 && fs.existsSync(file) && fs.statSync(file).size > 0) {
    generated.push({ ...s, file });
  } else {
    genFailed++;
    const why = (r.stderr || r.error?.message || 'unknown').trim().split('\n').slice(-2).join(' | ');
    console.log(`  GEN-FAIL ${s.name}.${s.ext}: ${why}`);
  }
}
console.log(`Generated ${generated.length}/${SAMPLES.length} (${genFailed} could not be produced by this ffmpeg build)\n`);

// ---- connect to the app ----------------------------------------------------
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let targets = [];
for (let i = 0; i < 40; i++) {
  try {
    targets = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json();
    if (targets.some((t) => t.type === 'page' && /3000/.test(t.url))) break;
  } catch { /* not up yet */ }
  await sleep(500);
}
const page = targets.find((t) => t.type === 'page' && /3000/.test(t.url)) || targets.find((t) => t.type === 'page');
if (!page) {
  console.log(`No Electron page on debug port ${PORT}. Start the app with --remote-debugging-port=${PORT} first.`);
  process.exit(2);
}
const ws = new WebSocket(page.webSocketDebuggerUrl);
let msgId = 1;
const pending = new Map();
ws.addEventListener('message', (ev) => {
  const m = JSON.parse(ev.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
});
const send = (method, params = {}) => new Promise((res) => { const i = msgId++; pending.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
const evaluate = async (expr) => {
  const r = await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true });
  return r.result?.exceptionDetails ? { __exception: r.result.exceptionDetails.text } : r.result?.result?.value;
};
await new Promise((r) => ws.addEventListener('open', r));
await send('Runtime.enable');

const videoState = () => evaluate(`
  (() => {
    const v = document.querySelector('video');
    if (!v) return null;
    const src = v.currentSrc || '';
    let dec = src;
    try { dec = decodeURIComponent(src); } catch {}
    return {
      dec: dec.replace(/\\//g, '\\\\').toLowerCase(),
      pipe: src.includes('&transcode=true'),
      w: v.videoWidth, h: v.videoHeight, rs: v.readyState, paused: v.paused,
      ct: +v.currentTime.toFixed(2),
      vb: v.webkitVideoDecodedByteCount, ab: v.webkitAudioDecodedByteCount,
      err: v.error ? v.error.code : null
    };
  })()
`);

// ---- run -------------------------------------------------------------------
const results = [];
console.log('Sample                              route  picture   audio   verdict');
console.log('----------------------------------  -----  --------  ------  -------');
for (const s of generated) {
  const base = path.basename(s.file);
  const t0 = Date.now();
  await evaluate(`window.__initialVideoInfo = ${JSON.stringify(s.file)}; window.dispatchEvent(new Event('electron-file-opened'));`);
  let pictureAt = null;
  let audioOk = false;
  let sawRepair = false;
  let last = null;
  let verdict = 'FAIL';
  let note = '';
  let forcedPlay = false;
  while (Date.now() - t0 < TIMEOUT) {
    const st = await videoState();
    last = st;
    const mine = st && st.dec.includes(base.toLowerCase());
    if (mine) {
      if (st.pipe) sawRepair = true; // a routed file went through the pipe, not a failure
      if (st.w > 0 && st.vb > 0 && pictureAt === null) pictureAt = Date.now() - t0;
      if (st.ab > 0) audioOk = true;
      if (pictureAt !== null && audioOk) { verdict = 'PASS'; break; }
      // A silent file that sits paused would never satisfy the checks.
      if (st.paused && st.rs >= 2 && !forcedPlay) {
        forcedPlay = true;
        await evaluate(`document.querySelector('video').play().catch(()=>{})`);
      }
    }
    await sleep(150);
  }
  if (verdict !== 'PASS' && last) {
    if (!(last.dec || '').includes(base.toLowerCase())) note = 'never became current source';
    else if (last.err) note = `media error ${last.err}`;
    else if (pictureAt === null) note = `no picture (w=${last.w}, vb=${last.vb}, rs=${last.rs})`;
    else note = `no audio (ab=${last.ab}, rs=${last.rs}, paused=${last.paused})`;
  }
  const route = last?.pipe ? 'pipe' : 'file';
  const pic = pictureAt === null ? '   -   ' : `${pictureAt}ms`.padStart(7);
  const aud = audioOk ? '  yes ' : '  no  ';
  results.push({ sample: base, route, pictureMs: pictureAt, audio: audioOk, verdict, note });
  console.log(`${base.padEnd(34)}  ${route.padEnd(5)}  ${pic}  ${aud}  ${verdict}${note ? '  (' + note + ')' : ''}`);
}

const failed = results.filter((r) => r.verdict !== 'PASS');
console.log(`\n${results.length - failed.length}/${results.length} passed`);
if (failed.length) {
  console.log('Failures:');
  for (const f of failed) console.log(`  - ${f.sample}: ${f.note}`);
}
const report = path.join(projectRoot, 'format-selftest-report.json');
fs.writeFileSync(report, JSON.stringify({ when: new Date().toISOString(), results }, null, 2));
console.log(`Report: ${report}`);
if (!KEEP) {
  // The app may still hold a sample open — cleanup failing is not a test result.
  try { fs.rmSync(outDir, { recursive: true, force: true }); }
  catch { console.log(`(samples left in ${outDir} — app still holding them)`); }
}
ws.close();
process.exit(failed.length ? 1 : 0);
