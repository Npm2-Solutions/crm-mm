// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * The phone's own screens (docs/progetto-ghl/29), without a screen: what the
 * line under a person's name says, the open tasks by when they are due, the
 * stage a deals board opens on, a deal's value only when it has one. What the
 * server gives is `crm/api/sul_telefono.py`; the words are English, translated
 * where they are drawn.
 */

import { mascherato } from '@/utils/schedaPersona'

/**
 * The line under a person's name: how to reach them, else their company. A
 * value that came masked (Marketing reads no email nor phone) says nothing.
 */
export function contattoDi(persona = {}) {
  return (
    [persona.mobile_no, persona.phone, persona.email].find(
      (valore) => valore && !mascherato(valore),
    ) ||
    persona.organization ||
    ''
  )
}

function inizioDelGiorno(data) {
  return new Date(data.getFullYear(), data.getMonth(), data.getDate())
}

function letta(valore) {
  if (!valore) return null
  const data = new Date(String(valore).replace(' ', 'T'))
  return Number.isNaN(data.getTime()) ? null : data
}

/** The groups of the open tasks, in the order they are shown. */
export const GRUPPI_DI_COSE = [
  { key: 'late', label: 'Late' },
  { key: 'today', label: 'Today' },
  { key: 'tomorrow', label: 'Tomorrow' },
  { key: 'later', label: 'Later' },
  { key: 'undated', label: 'Without a day' },
]

/** Which group a task falls in, from its due date and now. */
export function gruppoDi(cosa, adesso = new Date()) {
  const scadenza = letta(cosa?.due_date)
  if (!scadenza) return 'undated'
  const oggi = inizioDelGiorno(adesso)
  const domani = new Date(oggi)
  domani.setDate(oggi.getDate() + 1)
  const dopodomani = new Date(oggi)
  dopodomani.setDate(oggi.getDate() + 2)
  // past its hour is late, today's morning too
  if (scadenza < adesso) return 'late'
  if (scadenza < domani) return 'today'
  if (scadenza < dopodomani) return 'tomorrow'
  return 'later'
}

/** The open tasks in their groups, empty groups left out, each in its order. */
export function cosePerGruppo(cose = [], adesso = new Date()) {
  const gruppi = Object.fromEntries(GRUPPI_DI_COSE.map((g) => [g.key, []]))
  for (const cosa of cose) gruppi[gruppoDi(cosa, adesso)].push(cosa)
  return GRUPPI_DI_COSE.filter((g) => gruppi[g.key].length).map((g) => ({
    ...g,
    rows: gruppi[g.key],
  }))
}

/**
 * When a task is due, said briefly: the hour for today and tomorrow, the day
 * otherwise (the group says which one), nothing without a date.
 */
export function scadenzaInBreve(dueDate, locale, adesso = new Date()) {
  const scadenza = letta(dueDate)
  if (!scadenza) return ''
  const gruppo = gruppoDi({ due_date: dueDate }, adesso)
  const ora = new Intl.DateTimeFormat(locale, {
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  }).format(scadenza)
  if (gruppo === 'today' || gruppo === 'tomorrow') return ora
  const opzioni = { weekday: 'short', day: 'numeric', month: 'short' }
  if (scadenza.getFullYear() !== adesso.getFullYear()) opzioni.year = 'numeric'
  return new Intl.DateTimeFormat(locale, opzioni).format(scadenza)
}

/**
 * The stage a deals board opens on: the one asked for when it has deals, else
 * the first open stage with deals, else the first stage.
 */
export function faseIniziale(fasi = [], conteggi = {}, chiesta = '') {
  if (chiesta && fasi.some((f) => f.name === chiesta)) return chiesta
  const conTrattative = (f) => (conteggi[f.name] || 0) > 0
  const aperta = (f) => !['Won', 'Lost'].includes(f.type)
  return (
    fasi.find((f) => aperta(f) && conTrattative(f))?.name ||
    fasi.find(conTrattative)?.name ||
    fasi[0]?.name ||
    ''
  )
}

/** A deal's value as a card shows it: nothing when it has none yet. */
export function valoreDellaTrattativa(trattativa = {}, locale) {
  const valore = Number(trattativa.deal_value) || 0
  if (!valore) return ''
  try {
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: trattativa.currency || 'EUR',
      maximumFractionDigits: valore >= 100 ? 0 : 2,
    }).format(valore)
  } catch {
    return new Intl.NumberFormat(locale).format(valore)
  }
}

/**
 * When a person comes next, for the chip on their line: `today` or `tomorrow`
 * with the hour, else the day; null without an appointment.
 */
export function quandoTorna(startsOn, locale, adesso = new Date()) {
  const inizio = letta(startsOn)
  if (!inizio) return null
  const ora = new Intl.DateTimeFormat(locale, {
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  }).format(inizio)
  const giorno = Math.round(
    (inizioDelGiorno(inizio) - inizioDelGiorno(adesso)) / 86400000,
  )
  if (giorno === 0) return { quando: 'today', ora }
  if (giorno === 1) return { quando: 'tomorrow', ora }
  return {
    quando: 'day',
    ora,
    giorno: new Intl.DateTimeFormat(locale, {
      day: 'numeric',
      month: 'short',
    }).format(inizio),
  }
}

// ------------------------------------------------------------------ the day

/** A day written YYYY-MM-DD as local midnight (not UTC's, a day earlier west). */
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

/** The seven days of the week a day falls in, Monday first, as YYYY-MM-DD. */
export function settimanaDi(giorno) {
  const data = giornoLocale(giorno)
  if (!data) return []
  const lunedi = new Date(data)
  lunedi.setDate(data.getDate() - ((data.getDay() + 6) % 7))
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(lunedi)
    d.setDate(lunedi.getDate() + i)
    return scritto(d)
  })
}

/** A day moved by some days, as YYYY-MM-DD. */
export function spostaGiorno(giorno, giorni) {
  const data = giornoLocale(giorno)
  if (!data) return giorno
  data.setDate(data.getDate() + giorni)
  return scritto(data)
}

/**
 * A day's appointments and events as one list, as a phone shows the agenda:
 * what lasts the whole day first, then by when it starts. Appointments come as
 * `crm.api.appointments.get_calendar` gives them, events as the calendar draws
 * them (`fromDate`, `fromTime`, `isFullDay`); whatever overlaps the day is in.
 */
export function elencoDelGiorno(appuntamenti = [], eventi = [], giorno) {
  const inizioGiorno = giornoLocale(giorno)
  if (!inizioGiorno) return []
  const fineGiorno = new Date(inizioGiorno)
  fineGiorno.setDate(inizioGiorno.getDate() + 1)
  const dentro = (inizio, fine) =>
    inizio && fine && inizio < fineGiorno && fine > inizioGiorno

  const righe = []
  for (const appuntamento of appuntamenti) {
    const inizio = letta(appuntamento.starts_on)
    const fine = letta(appuntamento.ends_on)
    if (!dentro(inizio, fine)) continue
    righe.push({
      id: `appt:${appuntamento.name}`,
      tipo: 'appointment',
      inizio,
      fine,
      intero: false,
      dati: appuntamento,
    })
  }
  for (const evento of eventi) {
    const intero = Boolean(evento.isFullDay)
    const inizio = letta(
      `${evento.fromDate} ${intero ? '00:00' : evento.fromTime || '00:00'}`,
    )
    let fine = letta(
      `${evento.toDate || evento.fromDate} ${intero ? '23:59' : evento.toTime || '23:59'}`,
    )
    if (fine && inizio && fine <= inizio) fine = new Date(inizio.getTime() + 1)
    if (!dentro(inizio, fine)) continue
    righe.push({
      id: evento.id,
      tipo: 'event',
      inizio,
      fine,
      intero,
      dati: evento,
    })
  }
  return righe.sort(
    (a, b) =>
      Number(b.intero) - Number(a.intero) ||
      a.inizio - b.inizio ||
      a.fine - b.fine,
  )
}

/**
 * Where "now" falls in a day's list: before the first item still to start;
 * -1 when the day is not today or everything has started.
 */
export function doveAdesso(righe = [], giorno, adesso = new Date()) {
  if (scritto(adesso) !== String(giorno).slice(0, 10)) return -1
  return righe.findIndex((riga) => !riga.intero && riga.inizio > adesso)
}
