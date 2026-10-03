// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * A number of the centre's, verified to be shown on calls (doc 52), without a
 * screen: whether a number is Italian and of which kind, the states of a
 * verification as the list draws them, the code's digits, how often the page asks
 * how it went. The server's rules are `crm/telephony/verificati_regole.py`; the
 * words are English, translated where they are drawn.
 */

/** How a verification stands (`CRM Caller ID.verification_status`). */
export const IN_ATTESA = 'Pending'
export const VERIFICATO = 'Verified'
export const NON_VERIFICATO = 'Failed'

/** Every how many milliseconds the page asks while Twilio's call goes on. */
export const OGNI = 3000

/** The number Twilio's verification call comes from. */
export const DA_TWILIO = '+1 415 723 4000'

/**
 * Whether a number as written is Italian, and of which kind: 'mobile' (3…),
 * 'fisso' (0…), '' when it is not Italian or cannot be told. An Italian number
 * may be written without +39, or with 0039.
 */
export function numeroItaliano(numero = '') {
  let cifre = String(numero || '').replace(/[\s\-.()/]/g, '')
  if (cifre.startsWith('00')) cifre = '+' + cifre.slice(2)
  if (cifre.startsWith('+39')) cifre = cifre.slice(3)
  else if (cifre.startsWith('+')) return ''
  if (!/^\d{6,12}$/.test(cifre)) return ''
  if (cifre.startsWith('3')) return 'mobile'
  if (cifre.startsWith('0')) return 'fisso'
  return ''
}

/** A verification's state as the list draws it: its words and its colour. */
export function statoDellaVerifica(stato) {
  if (stato === IN_ATTESA)
    return { label: 'Waiting for the code', theme: 'orange' }
  if (stato === VERIFICATO) return { label: 'Verified', theme: 'blue' }
  if (stato === NON_VERIFICATO) return { label: 'Not verified', theme: 'red' }
  return null
}

/** The code's digits, one per box. */
export function cifreDelCodice(codice) {
  return String(codice || '')
    .replace(/\D/g, '')
    .split('')
}

/** The digits to dial once Twilio's call is answered, as the server takes them. */
export function internoPulito(valore = '') {
  return String(valore || '')
    .replace(/[\s\-.]/g, '')
    .replace(/W/g, 'w')
}

/** Whether the digits after the answer are fine: digits, * and #, w to wait. */
export function internoValido(valore = '') {
  const pulito = internoPulito(valore)
  return !pulito || /^[0-9*#w]{1,32}$/.test(pulito)
}
