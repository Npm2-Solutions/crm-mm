// Renders every ad graphic: node grafiche.mjs → ../grafiche/<concept>-<format>.png
import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import fs from 'node:fs';

const CONCEPTS = ['tutto', 'livelli', 'fattura', 'conferme', 'casa', 'privacy'];
const FORMATS = { '1x1': 1080, '4x5': 1350, '9x16': 1920 };
fs.mkdirSync('../grafiche', { recursive: true });
const b = await chromium.launch();
for (const [f, h] of Object.entries(FORMATS)) {
  const p = await b.newPage({ viewport: { width: 1080, height: h } });
  for (const c of CONCEPTS) {
    await p.goto(`file://${process.cwd()}/grafiche.html?c=${c}&f=${f}`);
    await p.evaluate(() => window.ready);
    await p.screenshot({ path: `../grafiche/${c}-${f}.png` });
  }
  await p.close();
}
await b.close();
console.log('ok', CONCEPTS.length * Object.keys(FORMATS).length, 'grafiche');
