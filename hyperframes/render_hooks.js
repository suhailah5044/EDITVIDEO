// Render the 20 hook variants (hooks/hook-NN) at full quality.
//
//  body   : everything after the intro (t >= 2.25s) is identical in all variants, so it is rendered
//           once from the ORIGINAL files with its captions, as a near-lossless intermediate.
//  variant: intro clip from the ORIGINAL file + its hook title (HyperFrames overlay), cross-dissolved
//           into the body, voice-over muxed, one final encode.
//
// usage: SRC=/path/to/original/files node render_hooks.js [first] [last]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const DIR = __dirname;
const SRC = process.env.SRC || path.join(DIR, 'source');
const OUTDIR = path.join(DIR, 'out', 'hooks');
const WORK = path.join(OUTDIR, '_work');
const FPS = 30;
const first = +(process.argv[2] || 1), last = +(process.argv[3] || 20);
const CC = 'zscale=pin=bt2020:p=bt709:min=bt2020nc:m=bt709:tin=bt709:t=bt709:filter=lanczos,format=yuv420p';
const SCALE = 'scale=1080:1920:flags=lanczos+accurate_rnd+full_chroma_int:force_original_aspect_ratio=increase,crop=1080:1920';
const COLOR = ['-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv'];

const run = (args) => new Promise((res, rej) => {
  const p = spawn('ffmpeg', args, { stdio: ['ignore', 'inherit', 'inherit'] });
  p.on('close', c => c ? rej(new Error('ffmpeg exit ' + c)) : res());
});
const clipChain = (c) => `${CC}${c.crop ? ',crop=' + c.crop : ''},${SCALE},fps=${FPS},setsar=1,settb=AVTB,setpts=PTS-STARTPTS,format=yuv420p`;

// render a time range of a composition's captions/hook as a transparent overlay movie
async function overlay(html, t0, t1, hideCss, file) {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.route('**/@hyperframes/**', r => r.fulfill({ status: 200, contentType: 'text/javascript', body: '' }));
  await page.goto('file://' + html);
  await page.addStyleTag({ content: '.slide{display:none!important} html,body,#main{background:transparent!important}' + hideCss });
  await page.evaluate(() => document.fonts.ready);
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'png', '-i', '-',
    '-c:v', 'qtrle', '-pix_fmt', 'argb', file], { stdio: ['pipe', 'inherit', 'inherit'] });
  const n = Math.round((t1 - t0) * FPS);
  for (let f = 0; f < n; f++) {
    await page.evaluate(t => { window.__timelines.main.seek(t, false); }, t0 + f / FPS);
    const buf = await page.screenshot({ type: 'png', omitBackground: true });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
}

async function renderBody(edl, hookHtml, bodyFile) {
  const B = edl.boundaries, H = edl.tr / 2, T0 = B[1] - H;
  const ov = path.join(WORK, 'body-overlay.mov');
  console.log('body: captions overlay');
  await overlay(hookHtml, T0, edl.total, '#hook{display:none!important}', ov);
  const args = ['-v', 'error', '-y'], fc = [];
  const clips = edl.clips.slice(1);
  clips.forEach((c, j) => {
    const i = j + 1;
    const start = B[i] - H, end = i === edl.clips.length - 1 ? edl.total : B[i + 1] + H;
    args.push('-ss', String(c.in), '-t', (end - start).toFixed(3), '-i', path.join(SRC, c.src));
    fc.push(`[${j}:v]${clipChain(c)}[v${j}]`);
  });
  let lastL = 'v0';
  for (let j = 1; j < clips.length; j++) {
    fc.push(`[${lastL}][v${j}]xfade=transition=fade:duration=${edl.tr}:offset=${(B[j + 1] - H - T0).toFixed(3)}[x${j}]`);
    lastL = `x${j}`;
  }
  args.push('-i', ov);
  fc.push(`[${clips.length}:v]scale=out_color_matrix=bt709:out_range=tv,format=yuva420p[ov]`);
  fc.push(`[${lastL}][ov]overlay=0:0:format=yuv420,format=yuv420p[vout]`);
  args.push('-filter_complex', fc.join(';'), '-map', '[vout]', '-t', (edl.total - T0).toFixed(3),
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '6', '-pix_fmt', 'yuv420p', ...COLOR, bodyFile);
  console.log('body: compositing from original files');
  await run(args);
  fs.unlinkSync(ov);
}

async function renderVariant(n, bodyFile) {
  const id = `hook-${String(n).padStart(2, '0')}`;
  const dir = path.join(DIR, 'hooks', id);
  const edl = JSON.parse(fs.readFileSync(path.join(dir, 'edl.json'), 'utf8'));
  const B = edl.boundaries, H = edl.tr / 2, introEnd = B[1] + H, T0 = B[1] - H;
  const ov = path.join(WORK, `${id}-overlay.mov`);
  await overlay(path.join(dir, 'index.html'), 0, introEnd, '#box{display:none!important}', ov);
  const c = edl.clips[0];
  const out = path.join(OUTDIR, `menolak-algebra-${id}.mp4`);
  const args = ['-v', 'error', '-y',
    '-ss', String(c.in), '-t', introEnd.toFixed(3), '-i', path.join(SRC, c.src),
    '-i', ov, '-i', bodyFile, '-i', path.join(DIR, 'assets/vo.m4a'),
    '-filter_complex', [
      `[0:v]${clipChain(c)}[iv]`,
      `[1:v]scale=out_color_matrix=bt709:out_range=tv,format=yuva420p[ov]`,
      `[iv][ov]overlay=0:0:format=yuv420,format=yuv420p[intro]`,
      `[2:v]settb=AVTB,setpts=PTS-STARTPTS,format=yuv420p[body]`,
      `[intro][body]xfade=transition=fade:duration=${edl.tr}:offset=${T0.toFixed(3)}[vout]`,
      `[3:a]aresample=48000,apad[aout]`].join(';'),
    '-map', '[vout]', '-map', '[aout]', '-t', String(edl.total),
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-profile:v', 'high', '-pix_fmt', 'yuv420p', ...COLOR,
    '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', out];
  await run(args);
  fs.unlinkSync(ov);
  console.log(`done ${id} -> ${out}`);
}

(async () => {
  fs.mkdirSync(WORK, { recursive: true });
  const bodyFile = path.join(WORK, 'body.mp4');
  if (!fs.existsSync(bodyFile)) {
    const edl = JSON.parse(fs.readFileSync(path.join(DIR, 'hooks', 'hook-01', 'edl.json'), 'utf8'));
    await renderBody(edl, path.join(DIR, 'hooks', 'hook-01', 'index.html'), bodyFile);
  }
  for (let n = first; n <= last; n++) await renderVariant(n, bodyFile);
  console.log('all done');
})().catch(e => { console.error(e); process.exit(1); });
