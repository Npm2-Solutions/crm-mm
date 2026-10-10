// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * The centre's Telnyx account on Settings > Phone > Telephony > Telnyx and in the
 * browser's phone (doc 64), without a page.
 *
 * The two codes checked before Telnyx is asked, as the server checks them
 * (`crm/telephony/telnyx/regole.py`); whose account it is, in words; what «Check»
 * found; the states of a call in Telnyx's WebRTC SDK. The words are English,
 * translated where they are drawn.
 */

/** Where the centre goes on Telnyx's own site: the places it needs. */
export const TELNYX = {
  registrazione: 'https://telnyx.com/sign-up',
  portale: 'https://portal.telnyx.com',
  chiavi: 'https://portal.telnyx.com/#/app/api-keys',
  pubblica: 'https://portal.telnyx.com/#/app/account/public-key',
  // the account's balance, where it is topped up
  bilancio: 'https://portal.telnyx.com/#/app/billing',
  // the messages' log, where Telnyx says every detail
  registro: 'https://portal.telnyx.com/#/app/messaging/mdr-search',
  // how a number of another Italian operator comes to Telnyx
  portabilita:
    'https://support.telnyx.com/en/articles/3267012-italy-number-porting',
}

const CHIAVE = /^KEY[0-9A-Fa-f]{20,}_[A-Za-z0-9_-]{8,}$/

/** A code as copied: without the spaces and the lines around it or inside it. */
export function pulito(codice) {
  return String(codice || '').replace(/\s+/g, '')
}

/** Whether a public key is 32 bytes in base64. */
export function pubblicaValida(valore) {
  const testo = pulito(valore)
  if (!/^[A-Za-z0-9+/]+={0,2}$/.test(testo)) return false
  try {
    return atob(testo).length === 32
  } catch {
    return false
  }
}

/** What stops asking Telnyx with these two codes; '' when nothing does. */
export function cosaManca(chiave, pubblica) {
  if (!pulito(chiave)) return 'Paste the API key.'
  if (!CHIAVE.test(pulito(chiave))) {
    return 'The API key starts with KEY and holds an underscore: copy it again from the portal.'
  }
  if (!pulito(pubblica)) return 'Paste the public key.'
  if (!pubblicaValida(pubblica)) {
    return 'The public key is 44 letters, digits and signs ending with =: copy it again from the portal.'
  }
  return ''
}

/** Who pays the calls and the messages, by whose account it is. */
export function chiPaga(owner) {
  return (
    {
      Centre: 'The centre, to Telnyx',
      Agency: 'The agency',
    }[owner] || ''
  )
}

/**
 * What «Check» found, as lines to show: what was put back, what stays on the
 * centre's switchboard or another application. Each line is [sentence, count].
 */
export function righeDelControllo(esito) {
  if (!esito?.ok) return []
  const righe = []
  const rimessi = esito.repaired?.length || 0
  const altrove = esito.trunked?.length || 0
  if (rimessi === 1) {
    righe.push([
      'One number changed in the portal is pointed at {brand} again.',
      1,
    ])
  } else if (rimessi > 1) {
    righe.push([
      '{0} numbers changed in the portal are pointed at {brand} again.',
      rimessi,
    ])
  }
  if (altrove === 1) {
    righe.push([
      'One number of the account answers elsewhere - a switchboard, another application - and stays as it is.',
      1,
    ])
  } else if (altrove > 1) {
    righe.push([
      '{0} numbers of the account answer elsewhere - a switchboard, another application - and stay as they are.',
      altrove,
    ])
  }
  if (!righe.length) righe.push(['Everything is in place.', 0])
  return righe
}

/**
 * How many of a kind this month, as [sentence, values]: the calls with their
 * minutes where Telnyx counted them, the SMS, the numbers; null for none.
 */
export function quantiNellaVoce(voce) {
  const quanti = Number(voce?.count) || 0
  if (!quanti) return null
  if (voce.key === 'calls') {
    const minuti = voce.minutes
    if (minuti === null || minuti === undefined) {
      return quanti === 1 ? ['One call', []] : ['{0} calls', [quanti]]
    }
    return quanti === 1
      ? ['One call · {0} min', [Number(minuti) || 0]]
      : ['{0} calls · {1} min', [quanti, Number(minuti) || 0]]
  }
  if (voce.key === 'sms') {
    return quanti === 1 ? ['One SMS', []] : ['{0} SMS', [quanti]]
  }
  if (voce.key === 'numbers') {
    return quanti === 1 ? ['One number', []] : ['{0} numbers', [quanti]]
  }
  return null
}

/** The states of a call in Telnyx's SDK while it goes on, before it is answered. */
export const STATI_IN_CORSO = [
  'new',
  'requesting',
  'trying',
  'recovering',
  'early',
  'ringing',
  'answering',
]
/** The states of a call that is over. */
export const STATI_FINITI = ['hangup', 'destroy', 'purge']

/** Whether a call of the SDK is one ringing the browser, not answered yet. */
export function inArrivo(chiamata) {
  return chiamata?.direction === 'inbound' && chiamata?.state === 'ringing'
}

/** Whether a warning of the SDK says the token ends soon (34001, two minutes before). */
export function scadeIlGettone(evento) {
  return Number(evento?.warning?.code) === 34001
}
