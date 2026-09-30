import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
const [src, out, w, h] = process.argv.slice(2);
const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: +w, height: +h } });
await p.goto('file://' + process.cwd() + '/' + src); await p.waitForTimeout(300);
await p.screenshot({ path: out, omitBackground: true }); await b.close();
