const { chromium } = require('playwright');
const path = require('path'), fs = require('fs');
(async () => {
  const [html, outDir, fpsArg, onlyArg] = process.argv.slice(2);
  const fps = +fpsArg || 30;
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.resolve(html));
  await page.waitForFunction(() => window.__ready === true);
  const dur = await page.evaluate(() => window.__hf.duration);
  const frames = onlyArg ? onlyArg.split(',').map(Number) : [...Array(Math.round(dur * fps)).keys()];
  for (const f of frames) {
    await page.evaluate(t => window.__hf.seek(t), f / fps);
    await page.screenshot({ path: path.join(outDir, `f${String(f).padStart(5, '0')}.png`), omitBackground: true });
  }
  await browser.close();
  console.log('frames', frames.length);
})();
