// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * Calls going out from DottorCloud (doc 52), without a screen: the countries the
 * centre may call as the server reads them (`crm/telephony/uscita_regole.py`),
 * a country's name in the reader's language, the number a call shows to start
 * with, the keypad; and for every call, in or out, who calls and whether the
 * window is taken by another. The words are English, translated where they are
 * drawn.
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

/**
 * Whether the call's window is taken (Twilio's and Telnyx's): by a call it
 * shows, ringing or on, other than `nuova`, or by one being placed (`stato`
 * 'initiating': the server or the carrier has not answered yet, and there is no
 * call object). One call at a time: no call goes out over it, and one coming in
 * rings on the centre's other phones. A call coming in while another was being
 * placed took the window and its name, then the call going out took them back,
 * and the window lost the call it had shown.
 */
export function finestraOccupata(attuale, stato, nuova = null) {
  if (attuale) return attuale !== nuova
  return stato === 'initiating'
}

/**
 * What Twilio's window does with a call coming in: 'mostra' where the window is
 * free; 'aspetta' while the call it shows still rings in this browser
 * (`squilla`: that call's `status() === 'pending'`) and none is being placed;
 * 'ignora' else - a call on, or one going out - and it rings on the centre's
 * other phones. Twilio plays one looping tone for every call ringing in the
 * browser, and ignoring any of them stops it: a second call ignored while the
 * first rang left the first in the window with no sound. A call that waits
 * rings on, is shown when the one before it ends unanswered, and is ignored
 * once that one is answered (the tone stopped then).
 */
export function nuovaChiamata(attuale, stato, nuova, squilla = false) {
  if (!finestraOccupata(attuale, stato, nuova)) return 'mostra'
  if (attuale && squilla && stato !== 'initiating') return 'aspetta'
  return 'ignora'
}

/**
 * Who calls, asked one number at a time, for the call's window (Twilio's and
 * Telnyx's): `chiedi(numero)` asks the server, `aggiorna(contatto, cercando)`
 * tells the window. What it gives back is called with the call's number each
 * time a call starts or its number changes: the window hears nobody at once,
 * while the server is asked, then whom it found for that number - nobody where
 * it found nobody or could not answer. An answer about a number the call no
 * longer has is dropped. The window kept the last call's caller until the
 * server answered, and for the whole call where it did not.
 */
export function cercaChiChiama(chiedi, aggiorna) {
  let ultima = 0
  return async function cerca(numero) {
    const questa = ++ultima
    aggiorna(null, Boolean(numero))
    if (!numero) return
    let trovato = null
    try {
      trovato = (await chiedi(numero)) || null
    } catch {
      // nobody named: the window says it does not know who it is
    }
    if (questa === ultima) aggiorna(trovato, false)
  }
}

/**
 * The name the call's window gives whoever calls: the one the server found;
 * nothing yet while it is asked (`cercando`); «Unknown» once it found nobody or
 * could not say (`t`, the translator).
 */
export function nomeDiChiChiama(contatto, cercando, t) {
  if (contatto?.full_name) return contatto.full_name
  return cercando ? '' : t('Unknown')
}
