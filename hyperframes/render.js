// Local frame-accurate renderer for the HyperFrames composition.
// Seeks the GSAP timeline + every <video> per frame, screenshots, pipes to ffmpeg,
// then muxes the voice-over + SFX.   usage: node render.js [out.mp4] [fps]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');

const OUT = process.argv[2] || path.join(__dirname, 'out', 'kuasai-algebra.mp4');
const FPS = +(process.argv[3] || 30);
const DIR = __dirname;

(async () => {
  const browser = await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  // the HyperFrames runtime owns playback in the cloud; locally we drive the timeline ourselves
  await page.route('**/@hyperframes/**', r => r.fulfill({ status: 200, contentType: 'text/javascript', body: '' }));
  await page.goto('file://' + path.join(DIR, 'index.html'));
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all([...document.querySelectorAll('video')].map(v => v.readyState >= 2 ? 0 :
      new Promise(r => v.addEventListener('loadeddata', r, { once: true }))));
  });
  const total = await page.evaluate(() => +document.getElementById('main').dataset.duration);
  const n = Math.round(total * FPS);

  const silent = OUT.replace(/\.mp4$/, '.silent.mp4');
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-vf', 'scale=out_color_matrix=bt709:out_range=tv', '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv', silent], { stdio: ['pipe', 'inherit', 'inherit'] });

  for (let f = 0; f < n; f++) {
    const t = f / FPS;
    await page.evaluate(async (t) => {
      window.__timelines.main.seek(t, false);
      const vids = [...document.querySelectorAll('video')];
      await Promise.all(vids.map(v => {
        const s = +v.dataset.start, d = +v.dataset.duration;
        if (t < s - 0.05 || t > s + d) return 0;
        const lt = Math.min(Math.max(0, t - s), v.duration - 0.04);
        if (Math.abs(v.currentTime - lt) < 0.001) return 0;
        return new Promise(r => { v.addEventListener('seeked', r, { once: true }); v.currentTime = lt; });
      }));
    }, t);
    const buf = await page.screenshot({ type: 'jpeg', quality: 100 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (f % 60 === 0) process.stdout.write(`frame ${f}/${n}\n`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();

  // mix VO (main) + SFX (under) and mux
  await new Promise((res, rej) => {
    const m = spawn('ffmpeg', ['-v', 'error', '-y', '-i', silent, '-i', path.join(DIR, 'assets/vo.m4a'), '-i', path.join(DIR, 'assets/sfx.wav'),
      '-filter_complex', '[1:a]aresample=48000,volume=1.0[vo];[2:a]aresample=48000,volume=0.9[fx];[vo][fx]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95[a]',
      '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-t', String(total), '-movflags', '+faststart', OUT], { stdio: 'inherit' });
    m.on('close', c => c ? rej(c) : res());
  });
  console.log('done ->', OUT);
})();
