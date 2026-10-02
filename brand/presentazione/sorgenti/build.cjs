// Builds DottorCloud.pptx. Run with NODE_PATH pointing at a folder that has
// pptxgenjs, react, react-dom, react-icons and sharp installed.
const path = require('path');
const pptxgen = require('pptxgenjs');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');
const lu = require('react-icons/lu');
const sharp = require('sharp');

const ROOT = path.resolve(__dirname, '../../..');
const IMG = (n) => path.join(__dirname, 'img', n + '.png');
const LOGO = (n) => path.join(ROOT, 'brand/logo/png', n + '.png');

const C = {
  night: '111413', ink: '16201E', teal: '12A594', tealD: '0B6F64', tealS: 'E1F5F1', mint: '5FE0CC',
  bg: 'F6F9F8', card: 'FFFFFF', muted: '4E5352', faint: '959B99', mintText: '9FD8CE', deep: '0B2E2A', line: 'E0E3E2',
};
// the brand's signs (design-system/espresso): the cloud with its almost straight corner, the cross, the motif
const NUVOLA = (n, c) => `<svg xmlns="http://www.w3.org/2000/svg" width="${n}" height="${n}" viewBox="0 0 256 256"><path d="M128 0A128 128 0 0 1 256 128A128 128 0 0 1 128 256H56A56 56 0 0 1 0 200V128A128 128 0 0 1 128 0Z" fill="#${c}"/></svg>`;
const CROSS = (c) => `<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 12 12"><path d="M4 0h4v4h4v4H8v4H4V8H0V4h4z" fill="#${c}"/></svg>`;
const MOTIF = (c, w, h, p = 40) => `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}"><defs><pattern id="m" width="${p}" height="${p}" patternUnits="userSpaceOnUse"><path transform="scale(${p / 40})" d="M16.5 10h7v6.5H30v7h-6.5V30h-7v-6.5H10v-7h6.5z" fill="#${c}"/></pattern></defs><rect width="${w}" height="${h}" fill="url(#m)"/></svg>`;
const png64 = async (svg) => 'image/png;base64,' + (await sharp(Buffer.from(svg)).png().toBuffer()).toString('base64');
const FONT = 'Calibri';

const iconCache = {};
async function icon(name, color) {
  const key = name + color;
  if (!iconCache[key]) {
    const svg = renderToStaticMarkup(React.createElement(lu[name], { color: '#' + color, size: 256, strokeWidth: 2 }));
    const png = await sharp(Buffer.from(svg)).resize(256, 256).png().toBuffer();
    iconCache[key] = 'image/png;base64,' + png.toString('base64');
  }
  return iconCache[key];
}
const sizes = {};
async function dims(file) { if (!sizes[file]) { const m = await sharp(file).metadata(); sizes[file] = [m.width, m.height]; } return sizes[file]; }
// place an image inside a box, keeping its proportions
async function img(slide, file, x, y, w, h, align = 'center') {
  const [iw, ih] = await dims(file);
  const s = Math.min(w / iw, h / ih), W = iw * s, H = ih * s;
  const X = align === 'left' ? x : align === 'right' ? x + w - W : x + (w - W) / 2;
  slide.addImage({ path: file, x: X, y: y + (h - H) / 2, w: W, h: H });
  return { x: X, y: y + (h - H) / 2, w: W, h: H };
}
const T = (slide, text, o) => slide.addText(text, { fontFace: FONT, isTextBox: true, margin: 0, valign: 'top', ...o });

// an icon inside the cloud (avatars and small signs are whole clouds: 50% 50% 50% 22%)
async function circleIcon(slide, x, y, d, fill, name, color) {
  slide.addImage({ data: await png64(NUVOLA(256, fill)), x, y, w: d, h: d });
  const p = d * 0.26;
  slide.addImage({ data: await icon(name, color), x: x + p, y: y + p, w: d - 2 * p, h: d - 2 * p });
}
// the site's section label: no pill, the cross and the small capitals
async function chip(slide, text, x, y, dark = false) {
  slide.addImage({ data: await png64(CROSS(dark ? C.mint : C.teal)), x, y: y + 0.105, w: 0.15, h: 0.15 });
  T(slide, text.toUpperCase(), { x: x + 0.26, y, w: 6, h: 0.36, fontSize: 12, bold: true, charSpacing: 1.5, color: dark ? C.mint : C.tealD, valign: 'middle' });
}
// a block of the cover: rounded, the bottom-left corner almost straight, with the motif or the hump
async function block(slide, x, y, w, h, color, { motif = null, hump = false } = {}) {
  const r = Math.min(w, h) * 0.12, pw = Math.round(w * 100), ph = Math.round(h * 100), rr = r * 100, t = 6;
  slide.addImage({ data: await png64(`<svg xmlns="http://www.w3.org/2000/svg" width="${pw}" height="${ph}"><path d="M${rr} 0H${pw - rr}A${rr} ${rr} 0 0 1 ${pw} ${rr}V${ph - rr}A${rr} ${rr} 0 0 1 ${pw - rr} ${ph}H${t}A${t} ${t} 0 0 1 0 ${ph - t}V${rr}A${rr} ${rr} 0 0 1 ${rr} 0Z" fill="#${color}"/></svg>`), x, y, w, h });
  if (motif) slide.addImage({ data: await png64(MOTIF(motif, pw, ph, 48)), x, y, w, h });
  if (hump) { const d = w * 0.5; slide.addShape('ellipse', { x: x + (w - d) / 2, y: y - d * 0.38, w: d, h: d, fill: { color }, line: { color } }); }
}
async function row(slide, x, y, w, ic, title, desc, dark = false) {
  await circleIcon(slide, x, y, 0.52, dark ? C.deep : C.tealS, ic, dark ? C.mint : C.tealD);
  T(slide, title, { x: x + 0.72, y: y - 0.02, w: w - 0.72, h: 0.3, fontSize: 15, bold: true, color: dark ? 'FFFFFF' : C.ink });
  T(slide, desc, { x: x + 0.72, y: y + 0.29, w: w - 0.72, h: 0.5, fontSize: 12, color: dark ? C.mintText : C.muted });
}
let page = 0;
function footer(slide, dark = false) {
  page++;
  slide.addImage({ path: LOGO(dark ? 'dottorcloud-marchio-bianco' : 'dottorcloud-marchio'), x: 0.6, y: 7.02, w: 0.27, h: 0.24 });
  T(slide, 'DottorCloud', { x: 0.95, y: 7.02, w: 2, h: 0.26, fontSize: 10, bold: true, color: dark ? C.faint : C.muted, valign: 'middle' });
  T(slide, String(page), { x: 12.2, y: 7.02, w: 0.55, h: 0.26, fontSize: 10, color: dark ? C.faint : C.muted, align: 'right', valign: 'middle' });
}
function base(pres, dark = false, color) {
  const s = pres.addSlide();
  s.background = { color: color || (dark ? C.night : C.bg) };
  return s;
}
// the standard page: text on one side, the product on the other
async function feature(pres, o) {
  const s = base(pres, o.dark);
  const left = o.side !== 'left';
  const tx = left ? 0.6 : 7.25, tw = left ? 5.35 : 5.5;
  await chip(s, o.chip, tx, 0.6, o.dark);
  T(s, o.title, { x: tx, y: 1.1, w: tw, h: 1.25, fontSize: 30, bold: true, color: o.dark ? 'FFFFFF' : C.ink, valign: 'top' });
  T(s, o.sub, { x: tx, y: 2.4, w: tw, h: 0.7, fontSize: 14, color: o.dark ? C.mintText : C.muted });
  for (let i = 0; i < o.rows.length; i++) await row(s, tx, 3.3 + i * 0.9, tw, ...o.rows[i], o.dark);
  if (o.image) await img(s, IMG(o.image), left ? 6.3 : 0.45, 0.45, 6.55, 6.4);
  if (o.extra) await o.extra(s);
  s.addNotes(o.notes);
  footer(s, o.dark);
  return s;
}

(async () => {
  const pres = new pptxgen();
  pres.layout = 'LAYOUT_WIDE';
  pres.author = 'NPM2 Solutions Srl';
  pres.company = 'NPM2 Solutions Srl';
  pres.title = 'DottorCloud — il gestionale per il tuo centro medico';

  // 1 · cover
  {
    const s = base(pres);
    s.addImage({ path: LOGO('dottorcloud-orizzontale'), x: 0.7, y: 0.75, w: 3.4, h: 3.4 * 244 / 1200 });
    T(s, [{ text: 'Il gestionale per ', options: { color: C.ink } }, { text: 'il tuo centro medico', options: { color: C.tealD } }], { x: 0.7, y: 2.05, w: 6.0, h: 2.0, fontSize: 44, bold: true });
    T(s, 'Agende, cartelle, fatture, messaggi e l\'app per i pazienti. In un posto solo.', { x: 0.7, y: 4.25, w: 5.6, h: 0.9, fontSize: 18, color: C.muted });
    T(s, 'NPM2 Solutions Srl', { x: 0.7, y: 6.55, w: 4, h: 0.35, fontSize: 13, bold: true, color: C.muted });
    // the cover's composition: the slab with the motif, the logo's green, the mint with the hump, the ink
    await block(s, 7.2, -0.3, 2.3, 6.2, C.tealD, { motif: C.mint });
    await block(s, 9.7, -0.3, 4.0, 2.6, C.teal);
    await block(s, 9.7, 2.95, 2.25, 2.95, C.mint, { hump: true });
    await block(s, 12.15, 2.95, 1.6, 2.95, C.night);
    s.addNotes('Presentiamo DottorCloud: un gestionale unico per tutto il centro medico. Il messaggio di fondo è uno: tutto quello che oggi sta in programmi, fogli e telefoni diversi finisce in un posto solo, e ognuno vede la sua parte.');
    page++;
  }

  // 2 · overview
  {
    const s = base(pres);
    await chip(s, 'Panoramica', 0.6, 0.6);
    T(s, 'Tutto il centro, in un posto solo', { x: 0.6, y: 1.1, w: 12, h: 0.7, fontSize: 32, bold: true, color: C.ink });
    T(s, 'Un solo gestionale per segreteria, medici, amministrazione e pazienti. Si accendono i moduli che servono.', { x: 0.6, y: 1.85, w: 12, h: 0.45, fontSize: 15, color: C.muted });
    const M = [
      ['LuCalendarDays', 'Agende e stanze', 'Medici, stanze, attrezzature, lista d\'attesa'],
      ['LuStethoscope', 'Cartella clinica', 'Schede, note di visita, referti, consensi'],
      ['LuReceipt', 'Fatture e Sistema TS', 'Fattura elettronica che nasce dalla visita'],
      ['LuMessageCircle', 'WhatsApp e promemoria', 'Conferme, promemoria, note interne'],
      ['LuPhoneCall', 'Telefono integrato', 'Chi chiama lo sai prima di rispondere'],
      ['LuMegaphone', 'Campagne e social', 'Richieste da Meta, post programmati'],
      ['LuSmartphone', 'App e area pazienti', 'Accesso, piani, esercizi, documenti, firme'],
      ['LuShieldCheck', 'Permessi e privacy', 'Livelli per ruolo, dati in Europa'],
    ];
    const w = 2.86, h = 2.05, g = 0.25;
    for (let i = 0; i < M.length; i++) {
      const x = 0.6 + (i % 4) * (w + g), y = 2.65 + Math.floor(i / 4) * (h + g);
      s.addShape('roundRect', { x, y, w, h, rectRadius: 0.14, fill: { color: C.card }, line: { color: C.line, width: 0.75 }, shadow: { type: 'outer', color: '0B3B35', opacity: 0.08, blur: 10, offset: 3, angle: 90 } });
      await circleIcon(s, x + 0.28, y + 0.28, 0.6, C.tealS, M[i][0], C.tealD);
      T(s, M[i][1], { x: x + 0.28, y: y + 1.05, w: w - 0.5, h: 0.35, fontSize: 16, bold: true, color: C.ink });
      T(s, M[i][2], { x: x + 0.28, y: y + 1.42, w: w - 0.5, h: 0.5, fontSize: 12, color: C.muted });
    }
    s.addNotes('Gli otto blocchi che vedremo. Non serve usarli tutti dal primo giorno: il centro accende quelli che gli servono e aggiunge gli altri quando vuole. Tutti lavorano sulla stessa scheda del paziente, quindi nessun dato va ricopiato da un programma all\'altro.');
    footer(s);
  }

  // 3 · levels
  await feature(pres, {
    chip: '01 · Organizza', title: 'Ognuno vede solo quello che gli serve',
    sub: 'Stessa scheda del paziente, viste diverse a seconda di chi la apre. I livelli si danno persona per persona.',
    rows: [
      ['LuUsers', 'Segreteria', 'Agenda di tutti, arrivi, moduli da firmare, fatture e incassi'],
      ['LuStethoscope', 'Medici e operatori', 'La propria agenda, i propri pazienti, la cartella clinica'],
      ['LuUserCog', 'Amministrazione e direzione', 'Impostazioni, utenti, numeri del centro, fatture'],
      ['LuLock', 'Marketing', 'Campagne e richieste, senza dati clinici né codice fiscale'],
    ],
    extra: async (s) => { await img(s, IMG('livelli-medico'), 6.3, 0.45, 5.2, 3.9); await img(s, IMG('livelli-marketing'), 7.75, 3.1, 5.1, 3.85); },
    notes: 'Risponde a "ogni utente vede tutto?". No: ogni persona ha un livello (segreteria, medico, amministrazione, marketing, direzione sanitaria, sola lettura) e i livelli si combinano, per esempio il titolare che visita è amministrazione più medico. A destra la stessa paziente vista dal medico e dal marketing: il marketing vede da quale campagna arriva, ma non visite, referti o fatture.',
  });

  // 4 · unlimited
  {
    const s = base(pres, false, C.tealD);
    s.addImage({ data: await png64(MOTIF('19907F', 420, 230, 48)), x: 9.0, y: 0, w: 4.2, h: 2.3 });
    await chip(s, '01 · Organizza', 0.6, 0.6, true);
    T(s, 'Utenti illimitati, agende infinite', { x: 0.6, y: 1.1, w: 12, h: 0.8, fontSize: 36, bold: true, color: 'FFFFFF' });
    T(s, 'Il centro cresce senza cambiare gestionale: si aggiungono persone e agende quando servono.', { x: 0.6, y: 1.95, w: 12, h: 0.45, fontSize: 16, color: 'CFF3EC' });
    const B = [['∞', 'Utenti', 'Medici, segreteria, collaboratori esterni: aggiungi chi serve, quando serve.', 'LuUsers'],
      ['∞', 'Agende', 'Un\'agenda per ogni medico, stanza o attrezzatura, tutte insieme.', 'LuCalendarDays'],
      ['1', 'Scheda per persona', 'Contatto e paziente sono la stessa scheda: niente doppioni da riconciliare.', 'LuContact' in lu ? 'LuContact' : 'LuUserCheck']];
    for (let i = 0; i < 3; i++) {
      const x = 0.6 + i * 4.1, y = 2.95;
      s.addShape('roundRect', { x, y, w: 3.8, h: 3.55, rectRadius: 0.16, fill: { color: '0E8073' }, line: { color: '0E8073' } });
      await circleIcon(s, x + 0.35, y + 0.35, 0.6, C.deep, B[i][3], C.mint);
      T(s, B[i][0], { x: x + 0.35, y: y + 0.98, w: 3.1, h: 1.22, fontSize: 72, bold: true, color: C.mint });
      T(s, B[i][1], { x: x + 0.35, y: y + 2.2, w: 3.1, h: 0.4, fontSize: 20, bold: true, color: 'FFFFFF' });
      T(s, B[i][2], { x: x + 0.35, y: y + 2.65, w: 3.1, h: 0.75, fontSize: 13, color: 'CFF3EC' });
    }
    s.addNotes('Nessun limite al numero di utenti o di agende: il centro non deve contare le persone prima di aggiungerle. E ogni persona ha una scheda sola: quando un contatto diventa paziente non si crea una seconda anagrafica.');
    footer(s, true);
  }

  // 5 · agenda
  {
    const s = base(pres);
    await chip(s, '01 · Organizza', 0.6, 0.6);
    T(s, 'Più agende, stanze e attrezzature, insieme', { x: 0.6, y: 1.1, w: 12, h: 0.7, fontSize: 32, bold: true, color: C.ink });
    await img(s, IMG('agenda'), 0.4, 2.0, 8.4, 4.85, 'left');
    const R = [['LuCalendarDays', 'Agenda per risorse', 'Colonne per medico, stanza, ecografo o palestra'],
      ['LuClock', 'Lista d\'attesa', 'Un posto si libera e il primo in lista viene avvisato'],
      ['LuRepeat', 'Abbonamenti e pacchetti', 'Sedute contate: "4 di 10" direttamente in agenda'],
      ['LuUsers', 'Sedute di gruppo', 'Più partecipanti nello stesso appuntamento']];
    for (let i = 0; i < R.length; i++) await row(s, 9.05, 2.2 + i * 1.15, 3.8, ...R[i]);
    s.addNotes('Risponde a "gestisce più calendari, stanze, attrezzature?". Sì: ogni medico, stanza o attrezzatura è una risorsa con la sua agenda, e una visita può occupare insieme il medico, lo studio e l\'ecografo. Qui si vede un appuntamento annullato e il posto riempito dalla lista d\'attesa, e una seduta di fisioterapia dentro un abbonamento da dieci.');
    footer(s);
  }

  // 6 · services and staff
  await feature(pres, {
    side: 'left', chip: '01 · Organizza', title: 'Servizi e personale: chi fa cosa, e dove',
    sub: 'Ogni servizio sa quanto dura, chi lo può fare e che stanza o attrezzatura gli serve.',
    rows: [
      ['LuListChecks', 'Chi fa cosa', 'Una griglia servizi × persone, modificabile in un clic'],
      ['LuDoorOpen', 'Durata, stanza, attrezzatura', 'L\'agenda propone solo gli orari davvero liberi'],
      ['LuGlobe', 'Prenotazione online', 'Il paziente prenota dal sito, a qualsiasi ora'],
      ['LuRepeat', 'Pacchetti e abbonamenti', 'Cicli di sedute venduti e seguiti nel tempo'],
    ],
    image: 'servizi',
    notes: 'Il catalogo dei servizi è il cuore dell\'agenda: per ogni prestazione si dice quanto dura, chi la può erogare e dove. Da qui nascono gli orari liberi della prenotazione online, che il paziente usa dal sito del centro senza telefonare.',
  });

  // 7 · clinical record
  await feature(pres, {
    chip: '02 · Cura', title: 'La cartella clinica, dentro il gestionale',
    sub: 'Sulla scheda della persona compare la sezione Clinica, solo per chi cura.',
    rows: [
      ['LuHeartPulse', 'Allergie, terapie, parametri', 'La sintesi del paziente sempre in alto'],
      ['LuPenLine', 'Note di visita firmate', 'Scritte dal medico, firmate e poi solo integrate'],
      ['LuFolderHeart', 'Referti e documenti', 'Archiviati sulla scheda, con il lucchetto'],
      ['LuFileCheck', 'Consensi', 'Chi ha firmato cosa, quando, e con quale firma'],
    ],
    image: 'clinica',
    notes: 'Risponde a "gestisce o crea una cartella clinica?". Sì: la persona diventa paziente da sola al primo dato clinico, all\'arrivo o alla prima fattura sanitaria, e sulla sua scheda compare la sezione Clinica, visibile solo ai ruoli clinici. Ogni apertura della cartella resta registrata.',
  });

  // 8 · AI assistant (coming soon)
  await feature(pres, {
    dark: true, chip: 'In arrivo', title: 'L\'assistente IA per il medico',
    sub: 'Il medico detta la visita, l\'assistente scrive la bozza nei campi della scheda. Ospitato in Europa, conforme al GDPR.',
    rows: [
      ['LuMic', 'Dettatura', 'La visita detta diventa la bozza della nota'],
      ['LuCheck', 'Decide il medico', 'Niente si salva da solo: il medico conferma e firma'],
      ['LuServer', 'In Europa', 'Modello ospitato in UE, senza addestramento sui dati'],
    ],
    image: 'ai',
    notes: 'È in arrivo, non ancora disponibile: dirlo chiaramente. L\'assistente aiuta nell\'operatività, non fa diagnosi: trascrive quello che il medico dice e lo mette nei campi; farmaci e allergie il medico li conferma uno per uno, poi firma. Il modello gira in Europa e i dati non servono ad addestrarlo.',
  });

  // 9 · messages
  await feature(pres, {
    chip: '03 · Comunica', title: 'WhatsApp, promemoria e conferme',
    sub: 'Tutta la conversazione sta sulla scheda del paziente, insieme alle note interne dello staff.',
    rows: [
      ['LuMessageCircle', 'WhatsApp nel gestionale', 'La segreteria risponde dalla scheda del paziente'],
      ['LuBellRing', 'Promemoria automatici', 'Prima della visita, senza che nessuno se ne ricordi'],
      ['LuCheck', 'Conferme', 'Il paziente risponde "Sì" e l\'appuntamento è confermato'],
      ['LuPenLine', 'Note interne', 'Visibili solo allo staff, nella stessa conversazione'],
    ],
    image: 'chat',
    notes: 'Risponde a "che comunicazioni esterne ha?". WhatsApp, SMS ed email arrivano tutti sulla scheda della persona, in una conversazione sola. Promemoria e richieste di conferma partono da soli; la risposta del paziente aggiorna l\'appuntamento.',
  });

  // 10 · automations
  {
    const s = base(pres);
    await chip(s, '03 · Comunica', 0.6, 0.6);
    T(s, 'Automazioni che lavorano al posto tuo', { x: 0.6, y: 1.1, w: 12, h: 0.7, fontSize: 32, bold: true, color: C.ink });
    T(s, 'Un evento, un\'attesa, un messaggio: i flussi si disegnano una volta e girano da soli.', { x: 0.6, y: 1.85, w: 12, h: 0.45, fontSize: 15, color: C.muted });
    await img(s, IMG('auto'), 0.4, 2.45, 12.5, 3.3);
    const E = [['LuBellRing', 'Promemoria e conferme', 'prima di ogni visita'], ['LuCalendarClock' in lu ? 'LuCalendarClock' : 'LuClock', 'Richiami', 'per i controlli periodici'], ['LuSend', 'Dopo la visita', 'un messaggio e una recensione'], ['LuListChecks', 'Attività', 'alla segreteria, se serve una persona']];
    for (let i = 0; i < 4; i++) {
      const x = 0.6 + i * 3.1;
      await circleIcon(s, x, 6.05, 0.46, C.tealS, E[i][0], C.tealD);
      T(s, E[i][1], { x: x + 0.6, y: 6.0, w: 2.4, h: 0.28, fontSize: 13, bold: true, color: C.ink });
      T(s, E[i][2], { x: x + 0.6, y: 6.28, w: 2.4, h: 0.3, fontSize: 11.5, color: C.muted });
    }
    s.addNotes('Le automazioni tolgono lavoro ripetitivo alla segreteria: promemoria, richiami per i controlli, messaggi dopo la visita. Quando serve una persona, l\'automazione crea un\'attività invece di mandare un messaggio.');
    footer(s);
  }

  // 11 · phone
  await feature(pres, {
    chip: '03 · Comunica', title: 'Il telefono, dentro il gestionale',
    sub: 'Quando il telefono squilla, sullo schermo c\'è già la scheda di chi chiama.',
    rows: [
      ['LuPhoneCall', 'Chi chiama, prima di rispondere', 'Nome, prossima visita, ultimo messaggio, fatture'],
      ['LuPhone', 'Chiamare con un clic', 'Dalla scheda del paziente, dal computer'],
      ['LuHistory', 'Storico e registrazioni', 'Ogni chiamata resta sulla scheda della persona'],
    ],
    extra: async (s) => { await img(s, IMG('chiamata'), 6.4, 1.2, 6.4, 4.8); },
    notes: 'Risponde a "che integrazione ha con la telefonia?". Il centralino è dentro il gestionale: chiamate in entrata e in uscita dal computer, con la scheda del paziente aperta mentre squilla, e lo storico delle chiamate sulla scheda.',
  });

  // 12 · marketing
  await feature(pres, {
    chip: '03 · Comunica', title: 'Campagne Meta e post social, dallo stesso posto',
    sub: 'Chi compila il modulo di un\'inserzione entra fra le persone, con la campagna da cui arriva.',
    rows: [
      ['LuMegaphone', 'Richieste da Facebook e Instagram', 'Arrivano da sole, senza copiarle a mano'],
      ['LuTarget', 'Da dove arrivano i pazienti', 'Ogni paziente con la sua campagna d\'origine'],
      ['LuShare2', 'Post programmati', 'Il calendario dei social del centro'],
    ],
    extra: async (s) => { await img(s, IMG('social'), 9.35, 0.45, 3.6, 3.75); await img(s, IMG('lead'), 6.2, 4.5, 5.2, 2.0); },
    notes: 'Per i centri che fanno pubblicità: le richieste delle campagne Meta entrano da sole nel gestionale e restano collegate alla campagna, così si sa da dove arrivano i nuovi pazienti. I post dei social si programmano dallo stesso posto.',
  });

  // 13 · invoicing
  await feature(pres, {
    side: 'left', chip: '04 · Gestisci', title: 'La fattura nasce dalla visita',
    sub: 'Al paziente in PDF, le spese al Sistema TS, allo SdI quando va.',
    rows: [
      ['LuReceipt', 'Dall\'appuntamento', 'Paziente, prestazioni e professionista sono già lì'],
      ['LuSend', 'SdI', 'Per aziende ed enti, con le ricevute nel gestionale'],
      ['LuFileCheck', 'Sistema TS', 'Le spese sanitarie trasmesse per la precompilata'],
      ['LuStamp', 'Bollo e numerazione', 'Li mette il gestionale'],
    ],
    image: 'fattura',
    notes: 'Risponde a "gestisce la fatturazione?". Sì: dalla visita svolta nasce la fattura. Al paziente va in PDF e le spese al Sistema TS, perché per legge una prestazione sanitaria a una persona non passa dallo SdI; ad aziende ed enti va elettronica allo SdI. La segreteria vede anche le visite svolte e non ancora fatturate.',
  });

  // 14 · the app
  {
    const s = base(pres);
    await chip(s, '05 · Il paziente', 0.6, 0.6);
    T(s, 'Un\'app per lo staff, un\'area per i pazienti', { x: 0.6, y: 1.1, w: 4.3, h: 1.9, fontSize: 30, bold: true, color: C.ink });
    T(s, 'Medici e segreteria lavorano anche dal telefono. I pazienti hanno la loro area, con il nome del centro.', { x: 0.6, y: 3.05, w: 4.2, h: 0.95, fontSize: 14, color: C.muted });
    const R = [['LuKeyRound', 'Accesso sicuro', 'Codice via SMS, poi viso o impronta'], ['LuPenLine', 'Prepara la visita', 'Moduli e consensi firmati dal telefono'], ['LuFileText', 'Documenti e messaggi', 'Referti, fatture, comunicazioni del medico']];
    for (let i = 0; i < R.length; i++) await row(s, 0.6, 4.25 + i * 0.85, 4.3, ...R[i]);
    await img(s, IMG('login'), 4.95, 0.5, 2.95, 6.4);
    await img(s, IMG('home'), 7.6, 0.5, 2.95, 6.4);
    await img(s, IMG('firma'), 10.25, 0.5, 2.95, 6.4);
    s.addNotes('Risponde a "il gestionale ha un\'app sul telefono?". Sì, due: quella dello staff, con agenda e pazienti, e l\'area del paziente. Il paziente entra solo su invito, la prima volta con un codice e poi con il viso o l\'impronta; prima di ogni visita trova la lista delle cose da preparare e firma i moduli dal telefono. Anche i familiari possono seguire un minore o un genitore anziano.');
    footer(s);
  }

  // 15 · plans and exercises
  {
    const s = base(pres);
    await chip(s, '05 · Il paziente', 0.6, 0.6);
    T(s, 'Piani alimentari ed esercizi, sul telefono del paziente', { x: 0.6, y: 1.1, w: 4.3, h: 1.9, fontSize: 28, bold: true, color: C.ink });
    T(s, 'Li scrive il professionista, il paziente li segue e segna cosa ha fatto.', { x: 0.6, y: 3.05, w: 4.2, h: 0.7, fontSize: 14, color: C.muted });
    const R = [['LuApple', 'Piano alimentare', 'Pasti con un tocco, alternative equivalenti, lista della spesa'], ['LuDumbbell', 'Esercizi a casa', 'Animazioni, serie e ripetizioni, muscoli che lavorano'], ['LuActivity', 'Il professionista vede', 'Cosa è stato fatto, e risponde dall\'app']];
    for (let i = 0; i < R.length; i++) await row(s, 0.6, 4.0 + i * 0.9, 4.3, ...R[i]);
    await img(s, IMG('dieta'), 4.95, 0.5, 2.95, 6.4);
    await img(s, IMG('esercizio'), 7.6, 0.5, 2.95, 6.4);
    await img(s, IMG('muscoli'), 10.45, 1.1, 2.5, 3.4);
    await img(s, IMG('spesa'), 10.45, 4.5, 2.5, 2.4);
    s.addNotes('Per nutrizionisti, fisioterapisti e preparatori: il piano alimentare e gli esercizi a casa arrivano sul telefono del paziente. Il paziente segna i pasti con un tocco, sceglie fra alternative equivalenti decise dal professionista e ha la lista della spesa; gli esercizi hanno l\'animazione, le serie e la mappa dei muscoli. La dieta la firma solo chi ha la qualifica per farlo.');
    footer(s);
  }

  // 16 · privacy
  await feature(pres, {
    dark: true, side: 'left', chip: 'Privacy e GDPR', title: 'I dati dei pazienti, protetti',
    sub: 'Dati sanitari trattati come tali: separati, tracciati e in Europa.',
    rows: [
      ['LuServer', 'Server in Europa', 'I dati dei pazienti non escono dall\'Unione europea'],
      ['LuFlag', 'Un\'azienda italiana', 'Vicina, raggiungibile, che parla la tua lingua'],
      ['LuEye', 'Ogni accesso registrato', 'Chi ha aperto la cartella, e quando'],
      ['LuShieldCheck', 'Consensi e confini', 'Nessun dato clinico nel marketing o nelle notifiche'],
    ],
    extra: async (s) => { await img(s, IMG('gdpr'), 0.8, 0.9, 5.4, 5.4); },
    notes: 'I dati stanno su server in Europa e dietro c\'è un\'azienda italiana. I dati clinici li vedono solo i ruoli clinici, ogni lettura della cartella resta registrata, e nessun dato sanitario finisce in una campagna, in una chat o in una notifica.',
  });

  // 17 · summary
  {
    const s = base(pres);
    await chip(s, 'In sintesi', 0.6, 0.6);
    T(s, 'Quello che un centro medico chiede, c\'è', { x: 0.6, y: 1.1, w: 12, h: 0.7, fontSize: 32, bold: true, color: C.ink });
    const A = [['LuLock', 'Permessi per ruolo', 'Ognuno vede la sua parte'], ['LuCalendarDays', 'Agende senza limiti', 'Medici, stanze, attrezzature'], ['LuStethoscope', 'Cartella clinica', 'Schede, note, referti archiviati'], ['LuReceipt', 'Fatturazione', 'Elettronica, SdI e Sistema TS'],
      ['LuMessageCircle', 'Comunicazione', 'WhatsApp, promemoria, conferme'], ['LuPhoneCall', 'Telefono integrato', 'La scheda si apre mentre squilla'], ['LuSmartphone', 'App', 'Per lo staff e per i pazienti'], ['LuServer', 'Dati protetti', 'Server europei, azienda italiana']];
    const w = 2.86, h = 2.2, g = 0.25;
    for (let i = 0; i < A.length; i++) {
      const x = 0.6 + (i % 4) * (w + g), y = 2.1 + Math.floor(i / 4) * (h + g);
      s.addShape('roundRect', { x, y, w, h, rectRadius: 0.14, fill: { color: C.card }, line: { color: C.line, width: 0.75 }, shadow: { type: 'outer', color: '0B3B35', opacity: 0.08, blur: 10, offset: 3, angle: 90 } });
      await circleIcon(s, x + 0.28, y + 0.3, 0.6, C.tealS, A[i][0], C.tealD);
      await circleIcon(s, x + w - 0.62, y + 0.34, 0.34, C.teal, 'LuCheck', 'FFFFFF');
      T(s, A[i][1], { x: x + 0.28, y: y + 1.1, w: w - 0.5, h: 0.4, fontSize: 17, bold: true, color: C.ink });
      T(s, A[i][2], { x: x + 0.28, y: y + 1.52, w: w - 0.5, h: 0.5, fontSize: 12.5, color: C.muted });
    }
    s.addNotes('Il riepilogo delle domande che ogni centro fa: chi vede cosa, quante agende, cartella clinica, fatturazione, comunicazione, telefono, app e dove stanno i dati. Per ognuna la risposta è sì, ed è tutto nello stesso gestionale.');
    footer(s);
  }

  // 18 · close
  {
    const s = base(pres, true);
    await block(s, 11.3, -0.5, 2.3, 3.4, C.tealD, { motif: C.mint });
    await block(s, 10.0, -0.5, 1.1, 2.1, C.mint);
    s.addImage({ data: await png64(MOTIF('1F4E47', 360, 200, 48)), x: 0, y: 5.6, w: 3.6, h: 2.0 });
    s.addImage({ path: LOGO('dottorcloud-orizzontale-negativo'), x: (13.333 - 4.4) / 2, y: 1.5, w: 4.4, h: 4.4 * 244 / 1200 });
    T(s, 'Vediamolo sul vostro centro', { x: 0.6, y: 2.85, w: 12.13, h: 0.9, fontSize: 40, bold: true, color: 'FFFFFF', align: 'center' });
    T(s, 'Una demo con i vostri servizi, le vostre agende e il vostro modo di lavorare.', { x: 1.6, y: 3.85, w: 10.13, h: 0.5, fontSize: 18, color: C.mintText, align: 'center' });
    s.addShape('roundRect', { x: (13.333 - 3.2) / 2, y: 4.75, w: 3.2, h: 0.62, rectRadius: 0.14, fill: { color: C.mint }, line: { color: C.mint } });
    T(s, 'Richiedi una demo  →', { x: (13.333 - 3.2) / 2, y: 4.75, w: 3.2, h: 0.62, fontSize: 17, bold: true, color: '0B2E2A', align: 'center', valign: 'middle' });
    T(s, 'NPM2 Solutions Srl', { x: 0.6, y: 6.2, w: 12.13, h: 0.4, fontSize: 15, bold: true, color: C.faint, align: 'center' });
    s.addNotes('Chiudere proponendo una demo sui dati e sui servizi del centro: è lì che il gestionale si vede davvero.');
  }

  await pres.writeFile({ fileName: path.join(__dirname, '..', 'DottorCloud.pptx') });
  console.log('written');
})();
