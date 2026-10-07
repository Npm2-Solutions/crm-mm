// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * The agenda, read (docs/crm/56-agenda.md): how tall an hour is, what
 * an appointment's block says at its height, who works when, which columns a
 * day or a week shows, the period a view covers. Pure: no DOM, no Vue, no
 * network - the grid and the month draw what these say.
 */

import { rispostaDellAppuntamento } from '@/utils/promemoriaAppuntamenti'
import { appointmentColor, formatMinutes } from '@/utils/scheduler'
import { chiDellAppuntamentoDelGiorno, settimanaDi } from '@/utils/sulTelefono'

// ------------------------------------------------------------------ heights

/** How tall a minute is, in px, at the agenda's three heights. */
export const ALTEZZE = { compatta: 1.2, normale: 1.6, ampia: 2.4 }
export const ALTEZZA_PREDEFINITA = 'normale'

/** A line of a block: its words are 11 to 13px on 16px. */
export const RIGA = 16
// the block's padding above and below its lines, together
const MARGINI = 4

/**
 * How many whole lines an appointment of `minuti` minutes has room for, at
 * `pxPerMinuto`: never half a line - a 30-minute block 33px tall drew its time
 * and the top half of its title. 0 is a sliver, shorter than a line: it says
 * its time and its name in small type.
 */
export function righeDelBlocco(minuti, pxPerMinuto) {
  const alto = Math.max(Number(minuti) || 0, 0) * (Number(pxPerMinuto) || 0)
  if (alto < RIGA + MARGINI) return 0
  return Math.floor((alto - MARGINI) / RIGA)
}

// ------------------------------------------------------------------ the block

const fmt = (testo, valori = []) =>
  String(testo).replace(/\{(\d+)\}/g, (_, i) => valori[i] ?? '')

/**
 * What an appointment's block says, as the design system's AgendaEvent does:
 * the person first («Mario Rossi»; a class by its service), then what and
 * where («Visita cardiologica · Studio 2»). `modo` is what the columns are: a
 * professional's column (`staff`, the day's and a week's) names the rooms, a
 * room's (`resource`) the professionals. `nomeDi` gives a professional's
 * name, `nomeStanza` a room's, `t` translates (`__`).
 */
export function testoDelBlocco(
  appuntamento = {},
  {
    modo = 'staff',
    nomeDi = (utente) => utente,
    nomeStanza = (stanza) => stanza,
    t = fmt,
  } = {},
) {
  const { titolo, persone } = chiDellAppuntamentoDelGiorno(appuntamento)
  const classe = persone > 1
  const chi = titolo || appuntamento.service || t('Appointment')
  const cosa = classe
    ? t('{0} people', [persone])
    : appuntamento.service && appuntamento.service !== chi
      ? appuntamento.service
      : ''
  const dove =
    modo === 'resource'
      ? (appuntamento.staff || []).map((riga) => nomeDi(riga.user))
      : (appuntamento.resources || []).map((riga) => nomeStanza(riga.resource))
  return {
    chi,
    cosa,
    dove: dove.filter(Boolean).join(', '),
    dettagli: [cosa, ...dove].filter(Boolean).join(' · '),
  }
}

/**
 * The marks a block carries beside its time, each an icon and its words (the
 * words are its name for a screen reader and its tooltip): a conflict, how it
 * is going (confirmed, in the waiting room, done, did not come), a first
 * visit, booked online or on a platform. A cancelled one says so by its
 * struck name, and in its words.
 */
export function segniDelBlocco(appuntamento = {}, { t = fmt } = {}) {
  const segni = []
  if (appuntamento.conflict_note)
    segni.push({
      chiave: 'conflitto',
      icona: 'lucide-triangle-alert',
      testo: appuntamento.conflict_note,
    })
  const stato = statoDelBlocco(appuntamento)
  const DEL_STATO = {
    Confirmed: ['lucide-check', 'Confirmed'],
    Arrived: ['lucide-armchair', 'In the waiting room'],
    Completed: ['lucide-check-check', 'Completed'],
    'No Show': ['lucide-user-x', 'No Show'],
  }
  if (DEL_STATO[stato])
    segni.push({
      chiave: 'stato',
      icona: DEL_STATO[stato][0],
      testo: t(DEL_STATO[stato][1]),
    })
  // what the person answered the reminder, on an appointment of one person
  const risposta = rispostaDellAppuntamento(appuntamento, t)
  if (risposta) segni.push(risposta)
  if (appuntamento.first_visit)
    segni.push({
      chiave: 'prima',
      icona: 'lucide-user-plus',
      testo: t('First visit'),
    })
  if (appuntamento.source === 'Online')
    segni.push({
      chiave: 'online',
      icona: 'lucide-globe',
      testo: t('Booked online'),
    })
  else if (appuntamento.source === 'External')
    segni.push({
      chiave: 'piattaforma',
      icona: 'lucide-plug-zap',
      testo: appuntamento.external_platform
        ? t('Booked on {0}', [appuntamento.external_platform])
        : t('Booked on a platform'),
    })
  return segni
}

/**
 * Where an appointment stands, for its mark and its colour: its own status,
 * and «Arrived» while somebody of it sits in the waiting room.
 */
export function statoDelBlocco(appuntamento = {}) {
  const stato = appuntamento.status || 'Scheduled'
  if (['Cancelled', 'Completed', 'No Show'].includes(stato)) return stato
  const arrivati = (appuntamento.participants || []).some(
    (p) => p.status === 'Arrived',
  )
  return arrivati ? 'Arrived' : stato
}

/** The block's whole words, for a screen reader and the pointer's tooltip. */
export function paroleDelBlocco(appuntamento = {}, opzioni = {}) {
  const t = opzioni.t || fmt
  const testo = testoDelBlocco(appuntamento, opzioni)
  const ore = [appuntamento.starts_on, appuntamento.ends_on]
    .map((quando) => String(quando || '').slice(11, 16))
    .filter(Boolean)
    .join('–')
  return [
    ore,
    testo.chi,
    testo.cosa,
    testo.dove,
    appuntamento.status === 'Cancelled' ? t('Cancelled') : '',
    ...segniDelBlocco(appuntamento, { t }).map((segno) => segno.testo),
  ]
    .filter(Boolean)
    .join(', ')
}

/**
 * How a block lays its words out, by the lines it has room for:
 * - `sottile`, less than a line: its time and its person, in small type;
 * - `una`: «09:00 Mario Rossi · Visita · Studio 2» on one line;
 * - `due`: «09:00 Mario Rossi», then «Visita · Studio 2»;
 * - `tre`: «09:00 – 09:30», «Mario Rossi», «Visita · Studio 2»;
 * - `piena`: the time, the person, what, where on a line each, and as many
 *   lines of its notes as are left (`note`).
 */
export function formaDelBlocco(righe) {
  if (righe < 1) return { forma: 'sottile', note: 0 }
  if (righe === 1) return { forma: 'una', note: 0 }
  if (righe === 2) return { forma: 'due', note: 0 }
  if (righe === 3) return { forma: 'tre', note: 0 }
  return { forma: 'piena', note: righe - 4 }
}

// ------------------------------------------------------------------ colours

/** An appointment's colour by how it is going, the legend's when coloured by state. */
export const COLORI_DEGLI_STATI = {
  Scheduled: 'var(--cat-blue)',
  Confirmed: 'var(--cat-green)',
  Arrived: 'var(--cat-amber)',
  Completed: 'var(--ink-gray-5)',
  'No Show': 'var(--cat-rose)',
  Cancelled: 'var(--outline-gray-3)',
}

/** Its colour: by the service (the agenda's own, or its own) or by its state. */
export function coloreDelBlocco(
  appuntamento = {},
  { per = 'servizio', serviceColors = {} } = {},
) {
  if (per === 'stato')
    return (
      COLORI_DEGLI_STATI[statoDelBlocco(appuntamento)] ||
      COLORI_DEGLI_STATI.Scheduled
    )
  return appointmentColor(appuntamento, serviceColors)
}

/**
 * What the grid draws: a cancelled appointment leaves its place free, unless
 * cancelled ones were asked for (`annullati`, or the status filter names them).
 */
export function daDisegnare(
  appuntamenti = [],
  { annullati = false, stati = [] } = {},
) {
  if (annullati || stati.includes('Cancelled')) return appuntamenti
  return appuntamenti.filter((a) => a.status !== 'Cancelled')
}

// ------------------------------------------------------------------ hours

// 1440 is the end of the day, «24:00», not tomorrow's «00:00»
const ora = (minuti) => (minuti >= 24 * 60 ? '24:00' : formatMinutes(minuti))

/** Open around the clock: nothing to say, nothing to grey out. */
function sempreAperto(aperto) {
  return aperto.reduce((somma, [da, a]) => somma + (a - da), 0) >= 24 * 60 - 1
}

/**
 * A column's hours on its day, as its header says them: «08:00–13:00 ·
 * 14:00–19:00»; '' where nothing is known or it is open around the clock.
 */
export function orarioDelGiorno(aperto) {
  if (!Array.isArray(aperto) || !aperto.length || sempreAperto(aperto))
    return ''
  return [...aperto]
    .sort((x, y) => x[0] - y[0])
    .map(([da, a]) => `${ora(da)}–${ora(a)}`)
    .join(' · ')
}

/**
 * Where a column is closed inside the hours the grid shows: what its open
 * windows leave of `finestra`, as bands `{ from, to }` in minutes. Nothing
 * where its hours are not known (`aperto` not a list).
 */
export function chiusure(aperto, finestra) {
  if (!Array.isArray(aperto)) return []
  const bande = []
  let da = finestra.startMinutes
  for (const [inizio, fine] of [...aperto].sort((x, y) => x[0] - y[0])) {
    if (inizio > da)
      bande.push({ from: da, to: Math.min(inizio, finestra.endMinutes) })
    da = Math.max(da, fine)
  }
  if (da < finestra.endMinutes)
    bande.push({ from: da, to: finestra.endMinutes })
  return bande.filter((banda) => banda.to > banda.from)
}

/**
 * The hours a grid shows: from the first opening to the last closing of the
 * columns it draws, whole hours, widened by whatever is booked outside them;
 * 08:00–20:00 where nobody's hours are known. `aperture` holds each column's
 * open windows; `cose` anything with `startMinutes` and `endMinutes`.
 */
export function finestraDellaGiornata(
  cose = [],
  aperture = [],
  { da = 8 * 60, a = 20 * 60 } = {},
) {
  const finestre = aperture
    .filter(
      (aperto) =>
        Array.isArray(aperto) && aperto.length && !sempreAperto(aperto),
    )
    .flat()
  let inizio = finestre.length ? Math.min(...finestre.map(([i]) => i)) : da
  let fine = finestre.length ? Math.max(...finestre.map(([, f]) => f)) : a
  for (const cosa of cose) {
    if (Number.isFinite(cosa.startMinutes))
      inizio = Math.min(inizio, cosa.startMinutes)
    if (Number.isFinite(cosa.endMinutes)) fine = Math.max(fine, cosa.endMinutes)
  }
  inizio = Math.max(0, Math.floor(inizio / 60) * 60)
  fine = Math.min(24 * 60, Math.ceil(fine / 60) * 60)
  if (fine - inizio < 60) fine = Math.min(24 * 60, inizio + 60)
  return { startMinutes: inizio, endMinutes: fine }
}

/**
 * Whether somebody (a professional, a room) works on a day, by the hours the
 * server gave: `undefined` while they are coming, `null` where none were ever
 * set (open whenever) - both count as working.
 */
export function lavora(orari, giorno) {
  if (orari === undefined || orari === null) return true
  return (orari?.[giorno]?.open?.length ?? 0) > 0
}

/**
 * The columns a day shows, in their order: whoever was chosen; else, of
 * `tutti`, who works that day or has something in it (`occupati`, the keys
 * with something drawn) - a column of somebody off duty is one more to scroll
 * past. `mostraTutti` keeps everybody.
 */
export function colonneDelGiorno(
  tutti = [],
  {
    giorno,
    orari = {},
    occupati = new Set(),
    scelti = [],
    mostraTutti = false,
  } = {},
) {
  if (scelti.length) return tutti.filter((chi) => scelti.includes(chi))
  if (mostraTutti) return tutti
  return tutti.filter((chi) => occupati.has(chi) || lavora(orari[chi], giorno))
}

/**
 * The days a week shows for one professional or room: Monday to Friday, and
 * Saturday and Sunday when they work or have something in them.
 */
export function giorniDellaSettimana(
  giorno,
  { orari, occupati = new Set() } = {},
) {
  return settimanaDi(giorno).filter(
    (data, i) =>
      i < 5 ||
      occupati.has(data) ||
      (orari !== undefined && orari !== null && lavora(orari, data)),
  )
}

// ------------------------------------------------------------------ periods

/** The views a desk has; a phone has the day's list instead of the week. */
export const VISTE = ['giorno', 'settimana', 'mese']

function giornoLocale(giorno) {
  const [anno, mese, giornoDelMese] = String(giorno || '')
    .slice(0, 10)
    .split('-')
    .map(Number)
  if (!anno || !mese || !giornoDelMese) return null
  return new Date(anno, mese - 1, giornoDelMese)
}

function scritto(data) {
  const due = (n) => String(n).padStart(2, '0')
  return `${data.getFullYear()}-${due(data.getMonth() + 1)}-${due(data.getDate())}`
}

/** The weeks of a day's month, Monday first, each seven YYYY-MM-DD. */
export function meseDi(giorno) {
  const data = giornoLocale(giorno)
  if (!data) return []
  const primo = new Date(data.getFullYear(), data.getMonth(), 1)
  const ultimo = new Date(data.getFullYear(), data.getMonth() + 1, 0)
  const settimane = []
  let lunedi = giornoLocale(settimanaDi(scritto(primo))[0])
  while (lunedi <= ultimo) {
    const settimana = settimanaDi(scritto(lunedi))
    settimane.push(settimana)
    lunedi = giornoLocale(settimana[6])
    lunedi.setDate(lunedi.getDate() + 1)
  }
  return settimane
}

/** The days a view covers, for the server: `{ start, end }` as YYYY-MM-DD. */
export function periodoDi(vista, giorno) {
  if (vista === 'settimana') {
    const settimana = settimanaDi(giorno)
    return { start: settimana[0], end: settimana[6] }
  }
  if (vista === 'mese') {
    const settimane = meseDi(giorno)
    if (settimane.length)
      return { start: settimane[0][0], end: settimane.at(-1)[6] }
  }
  return { start: giorno, end: giorno }
}

/**
 * The day a view's arrows lead to: a day, a week, a month on (`verso` 1) or
 * back (-1); the 31st a month on is the next month's last day.
 */
export function spostaPeriodo(vista, giorno, verso = 1) {
  const data = giornoLocale(giorno)
  if (!data) return giorno
  if (vista === 'mese') {
    const giornoDelMese = data.getDate()
    const dopo = new Date(data.getFullYear(), data.getMonth() + verso, 1)
    const ultimo = new Date(
      dopo.getFullYear(),
      dopo.getMonth() + 1,
      0,
    ).getDate()
    dopo.setDate(Math.min(giornoDelMese, ultimo))
    return scritto(dopo)
  }
  data.setDate(data.getDate() + (vista === 'settimana' ? 7 : 1) * verso)
  return scritto(data)
}

const maiuscola = (testo) => testo.charAt(0).toUpperCase() + testo.slice(1)

/**
 * The period a view shows, as its heading says it: «Martedì 6 ottobre 2026»,
 * «5 – 11 ottobre 2026» (a week across two months names both), «Ottobre 2026».
 */
export function etichettaDelPeriodo(vista, giorno, lingua = 'it-IT') {
  const data = giornoLocale(giorno)
  if (!data) return ''
  const formato = (opzioni) => new Intl.DateTimeFormat(lingua, opzioni)
  if (vista === 'mese')
    return maiuscola(formato({ month: 'long', year: 'numeric' }).format(data))
  if (vista === 'settimana') {
    const [primo, ultimo] = [
      settimanaDi(giorno)[0],
      settimanaDi(giorno)[6],
    ].map(giornoLocale)
    // the first day says only what the last does not (Intl's own range writes
    // «05–11 ottobre» in Italian)
    const inizio =
      primo.getFullYear() !== ultimo.getFullYear()
        ? formato({ day: 'numeric', month: 'long', year: 'numeric' }).format(
            primo,
          )
        : primo.getMonth() !== ultimo.getMonth()
          ? formato({ day: 'numeric', month: 'long' }).format(primo)
          : formato({ day: 'numeric' }).format(primo)
    const fine = formato({
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    }).format(ultimo)
    return `${inizio} – ${fine}`
  }
  return maiuscola(
    formato({
      weekday: 'long',
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    }).format(data),
  )
}

// ------------------------------------------------------------------ the month

/**
 * A day of the month as its cell says it: how many appointments, the first
 * few by their time and their person, how many more. `cose` are the day's
 * rows as the grid takes them (`startMinutes`, the appointment or the event).
 */
export function giornoDelMese(cose = [], quanti = 3) {
  const ordinate = [...cose].sort(
    (x, y) =>
      x.startMinutes - y.startMinutes ||
      String(x.name).localeCompare(String(y.name)),
  )
  return {
    totale: ordinate.filter((cosa) => cosa.tipo !== 'evento').length,
    primi: ordinate.slice(0, quanti),
    altri: Math.max(ordinate.length - quanti, 0),
  }
}

// ------------------------------------------------------------------ columns

const giornoDi = (quando) => String(quando || '').slice(0, 10)

function minutiDi(quando) {
  const ora = /(\d{1,2}):(\d{2})/.exec(String(quando || '').slice(10))
  return ora ? Number(ora[1]) * 60 + Number(ora[2]) : 0
}

/**
 * The part of a span `[da, a)` that falls on `giorno`, in minutes from its
 * midnight: an appointment from 23:00 to 01:00 is drawn on both days. A span of
 * nothing is still drawn ten minutes long, to be seen and touched.
 */
export function sulGiorno(da, a, giorno) {
  const primo = giornoDi(da)
  const ultimo = giornoDi(a) || primo
  if (!primo || primo > giorno || ultimo < giorno) return null
  const inizio = primo < giorno ? 0 : minutiDi(da)
  const fine = ultimo > giorno ? 24 * 60 : minutiDi(a)
  if (primo !== ultimo && fine <= inizio) return null
  return [inizio, Math.min(Math.max(fine, inizio + 10), 24 * 60)]
}

// an event as the calendar list gives it, as two moments
const daEvento = (evento) => [
  `${evento.fromDate} ${evento.isFullDay ? '00:00' : evento.fromTime || '00:00'}`,
  `${evento.toDate || evento.fromDate} ${evento.isFullDay ? '24:00' : evento.toTime || '24:00'}`,
]

/**
 * What each column of the grid draws: `{ blocchi, bande, intere }` by its key.
 * A day's columns are people or rooms (`modo`), each `{ key, data }`; a week's
 * (`settimana`) are the days of `chi`, keyed by their date. An appointment goes
 * where its professional or its room is; one's own events (`io`) in one's own
 * column, a whole-day one above the hours (`intere`); the time busy with what
 * one may not read (`occupato`) and the colleagues' engagements (`impegni`,
 * `{ name, users }`) as bands, but never over an event drawn as itself.
 */
export function cosePerColonna(colonne = [], opzioni = {}) {
  const {
    modo = 'staff',
    settimana = false,
    chi = '',
    io = '',
    appuntamenti = [],
    eventi = [],
    occupato = [],
    impegni = [],
  } = opzioni
  const mappa = new Map(
    colonne.map((colonna) => [
      colonna.key,
      { blocchi: [], bande: [], intere: [] },
    ]),
  )
  const diChi = (riga) =>
    modo === 'resource'
      ? (riga.resources || []).map((r) => r.resource)
      : (riga.staff || []).map((s) => s.user)
  // the columns somebody's row goes to
  const colonneDi = (persone) =>
    settimana
      ? persone.includes(chi)
        ? colonne
        : []
      : colonne.filter((colonna) => persone.includes(colonna.key))
  const metti = (colonna, dove, cosa, da, a) => {
    const span = sulGiorno(da, a, colonna.data)
    if (span)
      mappa.get(colonna.key)[dove].push({
        ...cosa,
        startMinutes: span[0],
        endMinutes: span[1],
      })
  }

  for (const appuntamento of appuntamenti)
    for (const colonna of colonneDi(diChi(appuntamento)))
      metti(
        colonna,
        'blocchi',
        {
          id: `appt:${appuntamento.name}`,
          tipo: 'appuntamento',
          dati: appuntamento,
        },
        appuntamento.starts_on,
        appuntamento.ends_on,
      )

  const mie = modo === 'resource' ? [] : colonneDi([io])
  for (const evento of eventi)
    for (const colonna of mie) {
      const [da, a] = daEvento(evento)
      if (evento.isFullDay) {
        if (sulGiorno(da, a, colonna.data))
          mappa
            .get(colonna.key)
            .intere.push({ id: evento.id, tipo: 'evento', dati: evento })
      } else
        metti(
          colonna,
          'blocchi',
          { id: evento.id, tipo: 'evento', dati: evento },
          da,
          a,
        )
    }

  occupato.forEach((riga, i) => {
    for (const colonna of colonneDi(diChi(riga)))
      metti(
        colonna,
        'bande',
        { id: `busy:${i}`, tipo: 'occupato' },
        riga.starts_on,
        riga.ends_on,
      )
  })

  const disegnati = new Set(eventi.map((evento) => evento.id))
  for (const impegno of impegni) {
    if (modo === 'resource') break
    for (const colonna of colonneDi(impegno.users || [])) {
      // one's own column draws one's events whole
      const mia = settimana ? chi === io : colonna.key === io
      if (mia && disegnati.has(impegno.name)) continue
      if (impegno.all_day)
        mappa.get(colonna.key).bande.push({
          id: `imp:${impegno.name}`,
          tipo: 'impegno',
          startMinutes: 0,
          endMinutes: 24 * 60,
        })
      else
        metti(
          colonna,
          'bande',
          { id: `imp:${impegno.name}`, tipo: 'impegno' },
          impegno.starts_on,
          impegno.ends_on,
        )
    }
  }
  return mappa
}

/**
 * What each day of a month holds, as its cell reads it: by date, the
 * appointments and one's own events that touch it, a whole-day event first.
 */
export function cosePerGiorno(
  giorni = [],
  { appuntamenti = [], eventi = [] } = {},
) {
  const mappa = new Map(giorni.map((giorno) => [giorno, []]))
  const primo = giorni[0] || ''
  const ultimo = giorni.at(-1) || ''
  const metti = (cosa, da, a, intero = false) => {
    // only the days it touches
    if (giornoDi(da) > ultimo || (giornoDi(a) || giornoDi(da)) < primo) return
    for (const giorno of giorni) {
      const span = sulGiorno(da, a, giorno)
      if (span)
        mappa.get(giorno).push({
          ...cosa,
          startMinutes: intero ? -1 : span[0],
          endMinutes: span[1],
        })
    }
  }
  for (const appuntamento of appuntamenti)
    metti(
      {
        id: `appt:${appuntamento.name}`,
        tipo: 'appuntamento',
        dati: appuntamento,
      },
      appuntamento.starts_on,
      appuntamento.ends_on,
    )
  for (const evento of eventi) {
    const [da, a] = daEvento(evento)
    metti(
      { id: evento.id, tipo: 'evento', dati: evento },
      da,
      a,
      evento.isFullDay,
    )
  }
  return mappa
}
