// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt
//
// The video's phones, upright and without their shadow, for the website:
// node telefoni.mjs [name #phone seconds] → ../../presentazione/sorgenti/img/telefono-<name>.png
// (then python3 sito/immagini.py makes the WebP)
import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
const OUT = '../../presentazione/sorgenti/img/telefono-';
// [name, phone, seconds into the phone's scene]
const J = process.argv[2]
  ? [[process.argv[2], process.argv[3], +process.argv[4]]]
  : [
      ['login', '#acp', 3.4], ['home', '#acp', 6.3], ['dieta', '#dip', 4.5],
      ['esercizio', '#exp', 2.5], ['esercizi', '#exp', 5.5], ['staff', '#ph1', 5], ['firma', '#ph2', 5],
    ];
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 2 });
await p.goto('file://' + process.cwd() + '/video.html');
await p.evaluate(() => window.ready);
for (const [name, sel, dt] of J) {
  const clip = await p.evaluate(({ dt, sel }) => {
    const i = SCN.indexOf(document.querySelector(sel).closest('.scene'));
    window.render(start(i) + dt);
    document.documentElement.style.background = 'transparent'; document.body.style.background = 'transparent';
    document.querySelectorAll('.scene').forEach((s) => { s.style.background = 'transparent'; });
    document.querySelectorAll('.bgc,.blob,.dots,#bug,#cursor,#touch,#ripple,.shine').forEach((e) => (e.style.visibility = 'hidden'));
    const el = document.querySelector(sel);
    // nothing behind the phone: its round corners on transparency
    for (let a = el.parentElement; a; a = a.parentElement) a.style.background = 'transparent';
    // only this phone, upright, at rest
    document.querySelectorAll('.phone').forEach((e) => { if (e !== el) e.style.visibility = 'hidden'; });
    document.querySelectorAll('.card,.floatb,.stt,.node,.win').forEach((e) => { if (!el.contains(e)) e.style.visibility = 'hidden'; });
    el.style.transform = 'none'; el.style.opacity = '1'; el.style.boxShadow = 'none';
    const r = el.getBoundingClientRect();
    return { x: r.left, y: r.top, width: r.width, height: r.height };
  }, { dt, sel });
  await p.screenshot({ path: OUT + name + '.png', clip, omitBackground: true });
  await p.evaluate(() => document.querySelectorAll('[style*="visibility"]').forEach((e) => (e.style.visibility = '')));
}
await b.close(); console.log('ok');
