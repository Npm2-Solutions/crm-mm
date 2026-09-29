// Single frames for checking: node shoot.mjs [fmt] [plan] t1 t2 … → stills/<plan>-<fmt>-t<t>.jpg
// (with only times, it shoots the full landscape cut: node shoot.mjs 12.5 40)
import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
let args = process.argv.slice(2), fmt = 'h', plan = 'full';
if (isNaN(+args[0])) { [fmt, plan] = args; args = args.slice(2); }
const [W, H] = { h: [1920, 1080], v: [1080, 1920], p: [1080, 1350] }[fmt];
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: W, height: H } });
p.on('pageerror', (e) => console.log('ERR', e.message));
await p.goto(`file://${process.cwd()}/video.html?fmt=${fmt}&plan=${plan}`);
await p.evaluate(() => window.ready);
const pre = fmt === 'h' && plan === 'full' ? '' : `${plan}-${fmt}-`;
for (const t of args.map(Number)) {
  await p.evaluate((t) => window.render(t), t);
  await p.screenshot({ path: `stills/${pre}t${t.toFixed(2)}.jpg`, type: 'jpeg', quality: 70 });
}
console.log('DUR', await p.evaluate(() => window.DUR));
await b.close();
