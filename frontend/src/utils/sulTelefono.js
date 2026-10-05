// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * The phone's own screens (docs/progetto-ghl/29), without a screen: what the
 * line under a person's name says, the open tasks by when they are due, the
 * stage a deals board opens on, a deal's value only when it has one, a
 * company's line, a call's. What the server gives is `crm/api/sul_telefono.py`;
 * the words are English, translated where they are drawn.
 */

import { mascherato } from '@/utils/schedaPersona'
import { leggibile } from '@/utils/telefono'

/**
 * The line under a person's name: how to reach them, else their company. A
 * value that came masked (Marketing reads no email nor phone) says nothing.
 */
export function contattoDi(persona = {}) {
  const contatto = [persona.mobile_no, persona.phone, persona.email].find(
    (valore) => valore && !mascherato(valore),
  )
  return contatto ? leggibile(contatto) : persona.organization || ''
}

function inizioDelGiorno(data) {
  return new Date(data.getFullYear(), data.getMonth(), data.getDate())
}

function letta(valore) {
  if (!valore) return null
  const data = new Date(String(valore).replace(' ', 'T'))
  return Number.isNaN(data.getTime()) ? null : data
}

// a day chosen without an hour comes as its midnight: due all that day
function senzaOra(data) {
  return !data.getHours() && !data.getMinutes() && !data.getSeconds()
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
  // past its hour is late, today's morning too; a day without an hour once
  // it is over
  const finoA = senzaOra(scadenza)
    ? new Date(
        scadenza.getFullYear(),
        scadenza.getMonth(),
        scadenza.getDate() + 1,
      )
    : scadenza
  if (finoA <= adesso) return 'late'
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
 * otherwise (the group says which one), nothing without a date, nor for today
 * and tomorrow without an hour. One late since this morning says «oggi» and
 * its hour: «lun 5 ott» under «In ritardo» on Monday the 5th did not say why.
 */
export function scadenzaInBreve(dueDate, locale, adesso = new Date()) {
  const scadenza = letta(dueDate)
  if (!scadenza) return ''
  const gruppo = gruppoDi({ due_date: dueDate }, adesso)
  if ((gruppo === 'today' || gruppo === 'tomorrow') && senzaOra(scadenza))
    return ''
  const ora = new Intl.DateTimeFormat(locale, {
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  }).format(scadenza)
  if (gruppo === 'today' || gruppo === 'tomorrow') return ora
  if (
    gruppo === 'late' &&
    inizioDelGiorno(scadenza).getTime() === inizioDelGiorno(adesso).getTime()
  ) {
    const oggi = new Intl.RelativeTimeFormat(locale, {
      numeric: 'auto',
    }).format(0, 'day')
    return `${oggi}, ${ora}`
  }
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
 * Whom an appointment of the day is for, as its line says it: its person; a
 * class by its service, its people counted under it (their names cut one
 * another off); a cancelled one still names whom it was for - its title starts
 * with the service, and the name was cut off the line.
 */
export function chiDellAppuntamentoDelGiorno(appuntamento = {}) {
  const partecipanti = appuntamento.participants || []
  const ancora = partecipanti.filter((p) => p.status !== 'Cancelled')
  const nomi = (ancora.length ? ancora : partecipanti)
    .map((p) => p.participant_name || p.party)
    .filter(Boolean)
  if (nomi.length > 1)
    return {
      titolo: appuntamento.service || nomi.join(', '),
      persone: nomi.length,
    }
  return {
    titolo: nomi[0] || appuntamento.title || appuntamento.service || '',
    persone: nomi.length,
  }
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

/**
 * An address in two, where it may go on under itself on a narrow screen: up to
 * the «@», and its domain. Broken anywhere it read «crm.manager@example.co /
 * m»; between the two, «crm.manager@ / example.com».
 */
export function partiDellIndirizzo(indirizzo) {
  const testo = String(indirizzo || '')
  const chiocciola = testo.indexOf('@')
  return chiocciola < 0
    ? [testo, '']
    : [testo.slice(0, chiocciola + 1), testo.slice(chiocciola + 1)]
}

// ------------------------------------------------------------------ companies

/** A website as one reads it: `https://www.acme.it/chi-siamo` is `acme.it`. */
export function dominioDi(sito) {
  const testo = String(sito || '').trim()
  if (!testo) return ''
  try {
    const url = new URL(
      /^[a-z]+:\/\//i.test(testo) ? testo : `https://${testo}`,
    )
    return url.hostname.replace(/^www\./, '')
  } catch {
    return testo
  }
}

/** The line under a company's name: what it does and where it is online. */
export function rigaDellAzienda(azienda = {}, t = (testo) => testo) {
  // the sectors are a translated DocType: the shipped ones in the reader's
  // language («Trasporti»), one the centre wrote as written
  return [azienda.industry && t(azienda.industry), dominioDi(azienda.website)]
    .filter(Boolean)
    .join(' · ')
}

// ------------------------------------------------------------------ calls

/**
 * Which way a call went, for its mark: `missed` (an incoming call nobody took,
 * or a message left instead), `incoming`, `outgoing`.
 */
export function versoDellaChiamata(chiamata = {}) {
  if (chiamata.missed) return 'missed'
  return chiamata.type === 'Incoming' ? 'incoming' : 'outgoing'
}

/** How long a call lasted as a clock reads it - `1:49`, `1:02:03` - or ''. */
export function durataDellaChiamata(secondi) {
  const totale = Math.round(Number(secondi) || 0)
  if (totale <= 0) return ''
  const ore = Math.floor(totale / 3600)
  const minuti = Math.floor((totale % 3600) / 60)
  const resto = String(totale % 60).padStart(2, '0')
  return ore
    ? `${ore}:${String(minuti).padStart(2, '0')}:${resto}`
    : `${minuti}:${resto}`
}

// ------------------------------------------------------------------ notes

/**
 * The line under a note's words: who wrote it, about whom, when - what of it is
 * known, `Anna Bianchi · Laura Rossi · 2 ore fa`.
 */
export function rigaDellaNota(nota = {}, { autore = '', quando = '' } = {}) {
  return [autore, nota.reference_title, quando].filter(Boolean).join(' · ')
}

// ------------------------------------------------------------------ tabs

/**
 * How many of a record's tabs the phone's bar holds (`SchedeDelTelefono`):
 * `larghezze` are the tabs' widths in the order the bar takes them, `spazio`
 * the bar's and `altre` the «More» key's. Five or fewer that fit are all there;
 * otherwise as many as fit beside «More», up to `massimo`, one at least. Not
 * measured yet (`spazio` 0), the bar holds what it always did: a page zoomed
 * (large text on Android: 277 points on a 360 phone) gave four tabs and
 * «More» 54 points each, «Detta…», «Eve…», «Preventi…».
 */
export function quanteNellaBarra(
  larghezze = [],
  spazio = 0,
  altre = 0,
  massimo = 4,
) {
  const tutte = larghezze.length
  const somma = (quante) =>
    larghezze.slice(0, quante).reduce((totale, larga) => totale + larga, 0)
  if (tutte <= massimo + 1 && (!spazio || somma(tutte) <= spazio)) return tutte
  let quante = Math.min(massimo, tutte - 1)
  while (spazio && quante > 1 && somma(quante) + altre > spazio) quante--
  return quante
}
