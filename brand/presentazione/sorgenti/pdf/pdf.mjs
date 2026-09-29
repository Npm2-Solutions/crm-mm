// Prints deck.html (from tohtml.py) to DottorCloud.pdf, one slide per page.
import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import path from 'node:path';

const dir = path.dirname(new URL(import.meta.url).pathname);
const b = await chromium.launch();
const p = await b.newPage();
await p.goto('file://' + path.join(dir, 'deck.html'));
await p.evaluate(() => document.fonts.ready);
await p.pdf({ path: path.join(dir, '..', '..', 'DottorCloud.pdf'), preferCSSPageSize: true, printBackground: true });
await b.close();
console.log('pdf ok');
