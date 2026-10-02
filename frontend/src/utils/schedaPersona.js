// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// The head of a person's page (components/PersonHeader.vue): the numbers one
// calls them on, how a call can leave, the appointment that comes next. Pure,
// so the page only draws and the rules are tested.

const CIFRE = /\d/g

/** A number's digits, with the leading + of an international one. */
export function soloCifre(numero) {
  const testo = String(numero || '').trim()
  const cifre = (testo.match(CIFRE) || []).join('')
  if (!cifre) return ''
  return testo.startsWith('+') || testo.startsWith('00')
    ? `+${testo.startsWith('00') ? cifre.slice(2) : cifre}`
    : cifre
}

/** The address a device's own dialer opens: `tel:+393401112233`. */
export function indirizzoTel(numero) {
  const cifre = soloCifre(numero)
  return cifre ? `tel:${cifre}` : ''
}

/**
 * The numbers a person is called on, the mobile first: each with the field it
 * comes from and its label. The same number written twice (with spaces, or
 * with 0039 for +39) is one number.
 */
export function numeriDi(doc = {}) {
  const numeri = []
  const visti = new Set()
  for (const [campo, label] of [
    ['mobile_no', 'Mobile'],
    ['phone', 'Phone'],
  ]) {
    const numero = String(doc?.[campo] || '').trim()
    const chiave = soloCifre(numero).replace(/^\+39/, '')
    if (!chiave || visti.has(chiave)) continue
    visti.add(chiave)
    numeri.push({ campo, label, numero })
  }
  return numeri
}

/**
 * How a call can leave, for each number: through the centre's telephony when it
 * is on (the centre's number shown, the call logged), through the device's own
 * dialer on a phone - or on a computer without telephony, where it is the only
 * way. `telefonia`: a provider is on and the user may call with it.
 */
export function modiDiChiamare(
  numeri,
  { telefonia = false, telefono = false } = {},
) {
  const modi = []
  for (const n of numeri) {
    if (telefonia) modi.push({ via: 'centro', ...n })
    if (!telefonia || telefono) modi.push({ via: 'dispositivo', ...n })
  }
  return modi
}

const CHIUSI = ['Cancelled', 'No Show']

/**
 * The next appointment of a person: the first one still to start, not cancelled
 * nor missed. `appuntamenti` as `crm.api.appointments.get_person_appointments`
 * gives them (newest first, `starts_on` as "YYYY-MM-DD HH:mm:ss").
 */
export function prossimoAppuntamento(appuntamenti = [], adesso = new Date()) {
  let prossimo = null
  let quando = null
  for (const a of appuntamenti || []) {
    if (!a?.starts_on || CHIUSI.includes(a.status)) continue
    const inizio = new Date(String(a.starts_on).replace(' ', 'T'))
    if (Number.isNaN(inizio.getTime()) || inizio < adesso) continue
    if (!quando || inizio < quando) {
      prossimo = a
      quando = inizio
    }
  }
  return prossimo
}

/** «gio 9 ott, 10:00»: when an appointment starts, in the language shown. */
export function quandoInBreve(startsOn, locale, adesso = new Date()) {
  const inizio = new Date(String(startsOn || '').replace(' ', 'T'))
  if (Number.isNaN(inizio.getTime())) return ''
  const opzioni = { weekday: 'short', day: 'numeric', month: 'short' }
  if (inizio.getFullYear() !== adesso.getFullYear()) opzioni.year = 'numeric'
  const giorno = new Intl.DateTimeFormat(locale, opzioni).format(inizio)
  const ora = new Intl.DateTimeFormat(locale, {
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  }).format(inizio)
  return `${giorno}, ${ora}`
}

/** «29 set 2026»: a day, in the language shown. */
export function giornoInBreve(data, locale) {
  const giorno = new Date(`${String(data || '').slice(0, 10)}T12:00:00`)
  if (Number.isNaN(giorno.getTime())) return ''
  return new Intl.DateTimeFormat(locale, {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(giorno)
}

/**
 * What an appointment is, on the page of the person it is for: its title
 * without their name («Fisioterapia — Laura Consenso» is «Fisioterapia» there).
 */
export function titoloSenzaPersona(titolo, nome) {
  const testo = String(titolo || '').trim()
  const persona = String(nome || '').trim()
  if (!persona) return testo
  for (const trattino of [' — ', ' - ', ' – ']) {
    if (testo.endsWith(trattino + persona))
      return testo.slice(0, -(trattino + persona).length).trim()
  }
  return testo
}
