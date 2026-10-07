import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
const OUT = '../../presentazione/sorgenti/img/';
// [image, scene, the scene's own time, what to frame, what to hide]
const J = [
  ['agenda', 's-agenda', 4.6, '#ag-w', '#s-agenda .left, #s-agenda .cam > .abs'], ['servizi', 's-serv', 3.5, '#sv-c'], ['clinica', 's-clin', 4.3, '#cl-w'], ['ai', 's-ai', 3.9, '#ai-c'],
  ['chat', 's-chat', 3.8, '#ch-w'], ['auto', 's-auto', 3.0, { x: 90, y: 380, width: 1760, height: 560 }], ['chiamata', 's-tel', 3.2, '#call', '#te-w'],
  ['social', 's-mkt', 3.4, '#soc'], ['lead', 's-mkt', 3.4, '#lead', '#arrow'], ['fattura', 's-fatt', 3.5, { x: 870, y: 90, width: 990, height: 990 }],
  ['livelli-medico', 's-liv', 3.2, '#lv-w'], ['livelli-marketing', 's-liv', 4.6, '#lv-w'],
  ['login', 's-acc', 1.95, '#acp'], ['home', 's-acc', 4.3, '#acp'], ['dieta', 's-diet', 3.7, '#dip'], ['spesa', 's-diet', 3.7, '#shop'],
  ['esercizio', 's-ex', 3.0, '#exp'], ['esercizi', 's-ex', 4.6, '#exp'], ['muscoli', 's-ex', 4.6, '#musc'],
  ['staff', 's-app', 3.9, '#ph1'], ['firma', 's-app', 3.9, '#ph2'], ['gdpr', 's-gdpr', 3.5, { x: 180, y: 220, width: 640, height: 640 }],
  ['logo-orbit', 's-hook', 5.2, { x: 180, y: 120, width: 1560, height: 680 }],
];
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 2 });
await p.goto('file://' + process.cwd() + '/video.html');
await p.evaluate(() => window.ready);
for (const [name, scene, lt, sel, hide] of J) {
  const clip = await p.evaluate(({ scene, lt, sel, hide }) => {
    window.render(window.at(scene, lt));
    document.documentElement.style.background = 'transparent'; document.body.style.background = 'transparent'; document.getElementById('stage').style.background = 'transparent';
    document.querySelectorAll('.scene').forEach((s) => { s.style.background = 'transparent'; });
    document.querySelectorAll('.card,.win,.floatb,.stt,.node,.phone').forEach((e) => (e.style.boxShadow = '0 8px 20px -10px rgba(11,46,42,.28), 0 0 0 1px rgba(11,46,42,.07)'));
    document.querySelectorAll('.blk,.dots,#bug,#trk,#cursor,#touch,#ripple,#wA,#wB,#cl').forEach((e) => (e.style.visibility = 'hidden'));
    if (hide) document.querySelectorAll(hide).forEach((e) => (e.style.visibility = 'hidden'));
    if (typeof sel !== 'string') return sel;
    const el = document.querySelector(sel);
    el.style.boxShadow = '0 8px 20px -10px rgba(11,46,42,.28), 0 0 0 1px rgba(11,46,42,.07)';
    const r = el.getBoundingClientRect(), pad = 36;
    const x = Math.max(0, r.left - pad), y = Math.max(0, r.top - pad);
    return { x, y, width: Math.min(1920, r.right + pad) - x, height: Math.min(1080, r.bottom + pad) - y };
  }, { scene, lt, sel, hide });
  await p.screenshot({ path: OUT + name + '.png', clip, omitBackground: true });
  await p.evaluate(() => document.querySelectorAll('[style*="visibility"]').forEach((e) => (e.style.visibility = '')));
}
await b.close(); console.log('ok');
