import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
const OUT = '../../presentazione/sorgenti/img/';
const J = [
  ['agenda', 14.0, '#ag-w', '#s-agenda > .abs'], ['servizi', 17.8, '#sv-c'], ['clinica', 28.0, '#cl-w'], ['ai', 33.0, '#ai-c'],
  ['chat', 38.8, '#ch-w'], ['auto', 42.2, { x: 90, y: 380, width: 1760, height: 560 }], ['chiamata', 46.0, '#call', '#te-w'],
  ['social', 50.4, '#soc'], ['lead', 50.4, '#lead', '#arrow'], ['fattura', 56.2, { x: 870, y: 90, width: 990, height: 990 }],
  ['livelli-medico', 58.8, '#lv-w'], ['livelli-marketing', 61.2, '#lv-w'],
  ['login', 65.45, '#acp'], ['home', 67.8, '#acp'], ['dieta', 72.6, '#dip'], ['spesa', 72.6, '#shop'],
  ['esercizio', 75.0, '#exp'], ['esercizi', 77.6, '#exp'], ['muscoli', 77.6, '#musc'],
  ['staff', 82.2, '#ph1'], ['firma', 82.2, '#ph2'], ['gdpr', 86.4, { x: 180, y: 220, width: 640, height: 640 }],
  ['logo-orbit', 5.2, { x: 180, y: 120, width: 1560, height: 680 }],
];
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 2 });
await p.goto('file://' + process.cwd() + '/video.html');
await p.evaluate(() => window.ready);
for (const [name, t, sel, hide] of J) {
  const clip = await p.evaluate(({ t, sel, hide }) => {
    window.render(t);
    document.documentElement.style.background = 'transparent'; document.body.style.background = 'transparent';
    document.querySelectorAll('.scene').forEach((s) => { s.style.background = 'transparent'; });
    document.querySelectorAll('.card,.win,.floatb,.stt,.node,.phone').forEach((e) => (e.style.boxShadow = '0 8px 20px -10px rgba(16,40,36,.28), 0 0 0 1px rgba(0,0,0,.06)'));
    document.querySelectorAll('.bgc,.blob,.dots,#bug,#cursor,#touch,#ripple,#wA,#wB,#cl').forEach((e) => (e.style.visibility = 'hidden'));
    if (hide) document.querySelectorAll(hide).forEach((e) => (e.style.visibility = 'hidden'));
    if (typeof sel !== 'string') return sel;
    const el = document.querySelector(sel);
    el.style.boxShadow = '0 8px 20px -10px rgba(16,40,36,.28), 0 0 0 1px rgba(0,0,0,.06)';
    const r = el.getBoundingClientRect(), pad = 36;
    const x = Math.max(0, r.left - pad), y = Math.max(0, r.top - pad);
    return { x, y, width: Math.min(1920, r.right + pad) - x, height: Math.min(1080, r.bottom + pad) - y };
  }, { t, sel, hide });
  await p.screenshot({ path: OUT + name + '.png', clip, omitBackground: true });
  await p.evaluate(() => document.querySelectorAll('[style*="visibility"]').forEach((e) => (e.style.visibility = '')));
}
await b.close(); console.log('ok');
