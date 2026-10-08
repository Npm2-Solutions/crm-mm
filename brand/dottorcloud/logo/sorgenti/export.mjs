import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import fs from 'node:fs';
const jobs = [
  ['dottorcloud-orizzontale.svg', 'png/dottorcloud-orizzontale.png', 1200],
  ['dottorcloud-orizzontale-negativo.svg', 'png/dottorcloud-orizzontale-negativo.png', 1200],
  ['dottorcloud-verticale.svg', 'png/dottorcloud-verticale.png', 1000],
  ['dottorcloud-verticale-negativo.svg', 'png/dottorcloud-verticale-negativo.png', 1000],
  ['dottorcloud-marchio.svg', 'png/dottorcloud-marchio.png', 1024],
  ['dottorcloud-marchio-bianco.svg', 'png/dottorcloud-marchio-bianco.png', 1024],
  ['dottorcloud-icona-app.svg', 'png/dottorcloud-icona-1024.png', 1024],
  ['dottorcloud-icona-app.svg', 'png/dottorcloud-icona-512.png', 512],
  ['dottorcloud-icona-app.svg', 'png/dottorcloud-icona-192.png', 192],
  ['dottorcloud-icona-app.svg', 'png/favicon-32.png', 32],
];
fs.mkdirSync('../png', { recursive: true });
const b = await chromium.launch();
for (const [src, out, w] of jobs) {
  const svg = fs.readFileSync('../' + src, 'utf8');
  const [, vw, vh] = svg.match(/viewBox="0 0 ([\d.]+) ([\d.]+)"/);
  const h = Math.round((w * vh) / vw);
  const p = await b.newPage({ viewport: { width: w, height: h } });
  await p.setContent(`<html><body style="margin:0;background:transparent">${svg.replace(/width="[\d.]+" height="[\d.]+"/, `width="${w}" height="${h}"`)}</body></html>`);
  await p.screenshot({ path: '../' + out, omitBackground: true });
  await p.close();
}
await b.close();
console.log('ok');
