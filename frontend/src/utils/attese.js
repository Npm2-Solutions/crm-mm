// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * Waiting lists in words: where an entry stands, when the person can, how an
 * offer went, what a new entry may be. The rules are
 * crm/scheduling/attese_regole.py's. Pure: tested.
 */

import { hhmm } from './scheduler'

export const IN_ATTESA = 'Waiting'
export const PROPOSTA = 'Offered'
export const PRENOTATA = 'Booked'
export const SCADUTA = 'Expired'
export const TOLTA = 'Removed'
/** The ones still in the line. */
export const APERTE = [IN_ATTESA, PROPOSTA]

export const GIORNI = [
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
  'Sunday',
]
/** The parts of the day: /prenota groups its times the same way. */
export const PARTI = ['morning', 'afternoon', 'evening']
export const NOMI_DELLE_PARTI = {
  morning: 'Morning',
  afternoon: 'Afternoon',
  evening: 'Evening',
}

/** Where an entry stands. */
export const STATO = {
  Waiting: { label: 'Waiting', theme: 'orange' },
  Offered: { label: 'Place offered', theme: 'blue' },
  Booked: { label: 'Booked', theme: 'green' },
  Expired: { label: 'Expired', theme: 'gray' },
  Removed: { label: 'Off the list', theme: 'gray' },
}

/** How an offer went. */
export const OFFERTA = {
  Sent: { label: 'Waiting for an answer', theme: 'blue' },
  Accepted: { label: 'Accepted', theme: 'green' },
  Declined: { label: 'Declined', theme: 'gray' },
  Expired: { label: 'No answer', theme: 'orange' },
  Taken: { label: 'Taken by somebody else', theme: 'gray' },
}

export const MASSIMO_POSTI = 20

const format = (text, args = []) =>
  args.reduce((out, arg, i) => out.replace(`{${i}}`, arg), text)

/** A weekday's short name in the language shown: Monday is lun. */
export function giornoBreve(giorno, locale) {
  const i = GIORNI.indexOf(giorno)
  if (i < 0) return giorno
  return new Intl.DateTimeFormat(locale, {
    weekday: 'short',
    timeZone: 'UTC',
  }).format(new Date(Date.UTC(2024, 0, 1 + i)))
}

/**
 * When the person can, in words: "Mon, Wed · Morning", "Any day, any time",
 * or the hours written by hand ("Tue 15:00–17:00"); a seat in a class, its day.
 * ``voce`` has `choice` (days and parts, or null) and `days` (the rows).
 */
export function quandoPuo(voce, t = format, locale) {
  const scelte = voce?.choice
  if (!scelte) {
    return (voce?.days || [])
      .map(
        (riga) =>
          `${giornoBreve(riga.workday, locale)} ${hhmm(riga.start_time)}–${hhmm(riga.end_time)}`,
      )
      .join(', ')
  }
  const giorni =
    scelte.days.length && scelte.days.length < GIORNI.length
      ? scelte.days.map((giorno) => giornoBreve(giorno, locale)).join(', ')
      : ''
  const parti = scelte.parts.map((parte) => t(NOMI_DELLE_PARTI[parte]))
  if (!giorni && !parti.length) return t('Any day, any time')
  return [giorni || t('Any day'), parti.join(', ') || t('Any time')].join(' · ')
}

/** What a new entry, or one put right, lacks: the first problem, in words. */
export function errore(form, t = format) {
  if (!form.service) return t('Choose a service')
  const posti = form.seats === '' || form.seats == null ? 1 : Number(form.seats)
  if (!Number.isInteger(posti) || posti < 1 || posti > MASSIMO_POSTI)
    return t('An entry waits for 1 to {0} places', [MASSIMO_POSTI])
  if (form.from_date && form.until && form.until < form.from_date)
    return t('The last day comes after the first')
  return ''
}

/** The entry as the server takes it (`attese.save_entry`). */
export function perIlServer(form) {
  return JSON.stringify({
    service: form.service,
    staff: form.staff || null,
    class_session: form.class_session || null,
    seats: Number(form.seats || 1),
    weekdays: form.class_session ? [] : form.weekdays || [],
    parts: form.class_session ? [] : form.parts || [],
    from_date: form.from_date || null,
    until: form.until || null,
    channel: form.channel,
    urgent: form.urgent ? 1 : 0,
    notes: form.notes || '',
  })
}

/** Turn a day or a part on or off, keeping the week's order. */
export function scegli(elenco, valore, ordine) {
  const scelti = new Set(elenco || [])
  if (scelti.has(valore)) scelti.delete(valore)
  else scelti.add(valore)
  return ordine.filter((voce) => scelti.has(voce))
}

/**
 * How an offer stands, in a line: "Answer by 12:30", "Not sent: call them",
 * or how it went. ``adesso`` and ``scadenza`` are comparable strings or dates.
 */
export function comeStaLOfferta(offerta, t = format, ora = (v) => v) {
  if (!offerta) return ''
  if (offerta.status === 'Sent') {
    if (!offerta.channel) return t('Not sent: call them')
    return t('Answer by {0}', [ora(offerta.expires_on)])
  }
  return t(OFFERTA[offerta.status]?.label || offerta.status)
}

/**
 * How an offer's answer time is written: its hour when it falls today, its day
 * too otherwise - «Risposta entro 05:00» for tomorrow morning read as already
 * gone. ``scadenza`` as the agenda keeps it, ``oggi`` the centre's day.
 */
export function formatoDellaScadenza(scadenza, oggi) {
  return String(scadenza || '').slice(0, 10) === oggi
    ? 'HH:mm'
    : 'ddd D MMM, HH:mm'
}

/** The entries in the line's order: the urgent first, then who joined first. */
export function inFila(voci) {
  return [...(voci || [])].sort(
    (a, b) =>
      Number(b.urgent || 0) - Number(a.urgent || 0) ||
      String(a.since).localeCompare(String(b.since)),
  )
}
