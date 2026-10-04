// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * Calls going out from DottorCloud (doc 52), without a screen: the countries the
 * centre may call as the server reads them (`crm/telephony/uscita_regole.py`),
 * a country's name in the reader's language, the number a call shows to start
 * with, the keypad. The words are English, translated where they are drawn.
 */

import { nomeDelPaese } from './paesi'

export { nomeDelPaese }

/** Italy, where a centre calls to start with. */
export const ITALIA = 'IT'

/** The countries offered to add: Europe's and the ones a centre in Italy calls. */
// prettier-ignore
export const PAESI_PROPOSTI = [
  'AL', 'AT', 'BE', 'BG', 'CA', 'CH', 'CY', 'CZ', 'DE', 'DK', 'EE', 'ES',
  'FI', 'FR', 'GB', 'GR', 'HR', 'HU', 'IE', 'IT', 'LI', 'LT', 'LU', 'LV',
  'MA', 'MC', 'MT', 'NL', 'NO', 'PL', 'PT', 'RO', 'RS', 'SE', 'SI', 'SK',
  'SM', 'TN', 'UA', 'US', 'VA',
]

/** The countries as stored - "IT, CH", a JSON list - as codes, sorted, Italy when none. */
export function paesi(valore) {
  let elenco = valore
  if (typeof valore === 'string') {
    try {
      elenco = JSON.parse(valore)
    } catch {
      elenco = valore.split(/[\s,;]+/)
    }
  }
  const codici = new Set(
    (Array.isArray(elenco) ? elenco : [])
      .map((c) => String(c).trim().toUpperCase())
      .filter((c) => /^[A-Z]{2}$/.test(c)),
  )
  return codici.size ? [...codici].sort() : [ITALIA]
}

/** The countries as the settings keep them. */
export function comeSalvati(codici) {
  return paesi(codici).join(', ')
}

/** The countries chosen with one more, or one less: never none, Italy then. */
export function conIlPaese(scelti, codice) {
  return paesi([...paesi(scelti), codice])
}

export function senzaIlPaese(scelti, codice) {
  return paesi(paesi(scelti).filter((c) => c !== codice))
}

/** The countries one may add, by their name in the reader's language. */
export function paesiDaAggiungere(scelti, lingua = 'it') {
  const gia = new Set(paesi(scelti))
  return PAESI_PROPOSTI.filter((c) => !gia.has(c))
    .map((c) => ({ label: nomeDelPaese(c, lingua), value: c }))
    .sort((a, b) => a.label.localeCompare(b.label, lingua || 'it'))
}

/**
 * The number a call shows to start with: the one used last, while it is still
 * the centre's; else one's own line; else the first.
 */
export function numeroIniziale(numeri = [], ricordato = '') {
  if (ricordato && numeri.some((n) => n.number === ricordato)) return ricordato
  return (numeri.find((n) => n.own) || numeri[0])?.number || ''
}

/**
 * Whether the call would be blocked in Italy: an Italian mobile shown on a call
 * to Italy from abroad - Twilio's - since 19/11/2025 (AGCOM 106/25/CONS).
 * `numeri` as the server gives them, `paese` the called number's.
 */
export function bloccataInItalia(numeri = [], mostrato = '', paese = '') {
  return (
    paese === ITALIA &&
    Boolean(numeri.find((n) => n.number === mostrato)?.mobile)
  )
}

/**
 * Whether the call may arrive without the number shown, or not arrive: an
 * Italian landline of another operator's, only verified in Twilio, shown on a
 * call to Italy - since 19/08/2025 an Italian operator may block it (AGCOM
 * 106/25/CONS). The server's `uscita_regole.incerta_in_italia`.
 */
export function incertaInItalia(numeri = [], mostrato = '', paese = '') {
  const numero = numeri.find((n) => n.number === mostrato)
  return Boolean(
    paese === ITALIA &&
      numero?.verified &&
      !numero.mobile &&
      numero.number.startsWith('+39'),
  )
}

/** Whether to ask which number to show: only when there is more than one. */
export function siSceglie(numeri = []) {
  return numeri.length > 1
}

/** The keypad, row by row. */
export const TASTI = [
  ['1', '2', '3'],
  ['4', '5', '6'],
  ['7', '8', '9'],
  ['*', '0', '#'],
]
