// Render the reel at maximum quality.
//
//  1. Captions: the HyperFrames composition (index.html) is rendered with the footage hidden
//     and a transparent background -> overlay.mov (with alpha).
//  2. Footage: taken straight from the ORIGINAL camera files listed in edl.json
//     (4K iPhone HLG -> BT.709, no grading), scaled once to 1080x1920, short cross-dissolves,
//     captions overlaid, voice-over muxed. One single video encode from the source.
//
// usage: SRC=/path/to/original/files node render.js [out.mp4]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const DIR = __dirname;
const SRC = process.env.SRC || path.join(DIR, 'source');
const OUT = process.argv[2] || path.join(DIR, 'out', 'kuasai-algebra.mp4');
const FPS = 30;
const edl = JSON.parse(fs.readFileSync(path.join(DIR, 'edl.json'), 'utf8'));
const run = (args) => new Promise((res, rej) => {
  const p = spawn('ffmpeg', args, { stdio: ['ignore', 'inherit', 'inherit'] });
  p.on('close', c => c ? rej(new Error('ffmpeg exit ' + c)) : res());
});

async function renderOverlay(file) {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.route('**/@hyperframes/**', r => r.fulfill({ status: 200, contentType: 'text/javascript', body: '' }));
  await page.goto('file://' + path.join(DIR, 'index.html'));
  await page.addStyleTag({ content: '.slide{display:none!important} html,body,#main{background:transparent!important}' });
  await page.evaluate(() => document.fonts.ready);
  const n = Math.round(edl.total * FPS);
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'png', '-i', '-',
    '-c:v', 'qtrle', '-pix_fmt', 'argb', file], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let f = 0; f < n; f++) {
    await page.evaluate(t => { window.__timelines.main.seek(t, false); }, f / FPS);
    const buf = await page.screenshot({ type: 'png', omitBackground: true });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (f % 150 === 0) console.log(`captions ${f}/${n}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
}

(async () => {
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  const overlay = path.join(path.dirname(OUT), 'captions-overlay.mov');
  await renderOverlay(overlay);

  // iPhone HLG (BT.2020) -> BT.709 SDR, matching how the phone shows it in SDR; no grading.
  const CC = 'zscale=pin=bt2020:p=bt709:min=bt2020nc:m=bt709:tin=bt709:t=bt709:filter=lanczos,format=yuv420p';
  const B = edl.boundaries, TR = edl.tr, H = TR / 2;
  const args = ['-v', 'error', '-y'];
  const fc = [];
  edl.clips.forEach((c, i) => {
    const start = i === 0 ? 0 : B[i] - H;
    const end = i === edl.clips.length - 1 ? edl.total : B[i + 1] + H;
    const len = (end - start).toFixed(3);
    let chain;
    if (/\.heic$/i.test(c.src)) {
      args.push('-loop', '1', '-framerate', String(FPS), '-t', len, '-i', path.join(SRC, c.src.replace(/\.heic$/i, '.png')));
      chain = `scale=out_color_matrix=bt709:out_range=tv,format=yuv420p`;
    } else {
      args.push('-ss', String(c.in), '-t', len, '-i', path.join(SRC, c.src));
      chain = CC;
    }
    if (c.crop) chain += `,crop=${c.crop}`;
    chain += `,scale=1080:1920:flags=lanczos+accurate_rnd+full_chroma_int:force_original_aspect_ratio=increase,crop=1080:1920`;
    chain += `,fps=${FPS},setsar=1,settb=AVTB,setpts=PTS-STARTPTS,format=yuv420p`;
    fc.push(`[${i}:v]${chain}[v${i}]`);
  });
  let last = 'v0';
  for (let k = 1; k < edl.clips.length; k++) {
    const o = (B[k] - H).toFixed(3);
    fc.push(`[${last}][v${k}]xfade=transition=fade:duration=${TR}:offset=${o}[x${k}]`);
    last = `x${k}`;
  }
  const oi = edl.clips.length, ai = oi + 1;
  args.push('-i', overlay, '-i', path.join(DIR, 'assets/vo.m4a'));
  fc.push(`[${oi}:v]scale=out_color_matrix=bt709:out_range=tv,format=yuva420p[ov]`);
  fc.push(`[${last}][ov]overlay=0:0:format=yuv420:shortest=0,format=yuv420p[vout]`);
  fc.push(`[${ai}:a]aresample=48000,apad[aout]`);
  args.push('-filter_complex', fc.join(';'), '-map', '[vout]', '-map', '[aout]', '-t', String(edl.total),
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-profile:v', 'high', '-pix_fmt', 'yuv420p',
    '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
    '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', OUT);
  console.log('compositing from original files...');
  await run(args);
  fs.unlinkSync(overlay);
  console.log('done ->', OUT);
})();
