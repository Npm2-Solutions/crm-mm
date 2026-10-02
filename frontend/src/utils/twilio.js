// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * The centre's Twilio account on Settings > Phone > Telephony > Twilio (doc 52),
 * without a page.
 *
 * The two codes checked before Twilio is asked, as the server checks them
 * (`crm/telephony/collegamento_regole.py`); whose account the space lives in, in
 * words; what «Check» found. The words are English, translated where they are
 * drawn.
 */

/** Where the centre goes on Twilio's own site: the only two places it needs. */
export const TWILIO = {
  registrazione: 'https://www.twilio.com/try-twilio',
  console: 'https://console.twilio.com',
  // the log of the account's problems, where Twilio says every detail
  registro: 'https://console.twilio.com/us1/monitor/logs/debugger/errors',
}

const SID = /^AC[0-9a-fA-F]{32}$/
const TOKEN = /^[0-9a-fA-F]{32}$/

/** A code as copied: without the spaces and the lines around it or inside it. */
export function pulito(codice) {
  return String(codice || '').replace(/\s+/g, '')
}

/** What stops asking Twilio with these two codes; '' when nothing does. */
export function cosaManca(sid, token) {
  if (!pulito(sid)) return 'Paste the Account SID.'
  if (!SID.test(pulito(sid))) {
    return 'The Account SID starts with AC and has 34 characters: copy it again from the console.'
  }
  if (!pulito(token)) return 'Paste the Auth Token.'
  if (!TOKEN.test(pulito(token))) {
    return 'The Auth Token has 32 letters and digits: copy it again from the console.'
  }
  return ''
}

/** Who pays the calls and the messages, by whose account the space lives in. */
export function chiPaga(owner) {
  return (
    {
      Centre: 'The centre, to Twilio',
      Agency: 'The agency',
      Manual: 'Connected by hand by the agency',
    }[owner] || ''
  )
}

/** The account as Twilio describes it, in a word. */
export function statoDelConto(status) {
  return (
    {
      active: 'Active',
      suspended: 'Suspended',
      closed: 'Closed',
    }[status] || ''
  )
}

/**
 * What «Check» found, as lines to show: what was put back, what a SIP trunk
 * takes. Each line is [sentence, count].
 */
export function righeDelControllo(esito) {
  if (!esito?.ok) return []
  const righe = []
  const rimessi = esito.repaired?.length || 0
  const tronco = esito.trunked?.length || 0
  if (rimessi === 1) {
    righe.push([
      'One number changed in the console is pointed at {brand} again.',
      1,
    ])
  } else if (rimessi > 1) {
    righe.push([
      '{0} numbers changed in the console are pointed at {brand} again.',
      rimessi,
    ])
  }
  if (tronco === 1) {
    righe.push([
      'One number goes to a SIP trunk: its calls do not reach {brand}, and it stays as it is.',
      1,
    ])
  } else if (tronco > 1) {
    righe.push([
      '{0} numbers go to a SIP trunk: their calls do not reach {brand}, and they stay as they are.',
      tronco,
    ])
  }
  if (!righe.length) righe.push(['Everything is in place.', 0])
  return righe
}

/**
 * What a kind of this month's spend counted, as [sentence, values] to translate
 * where it is drawn: «40 calls · 310 min», «One SMS», «2 numbers». Nothing for a
 * kind that counts nothing, or that Twilio counts only in money.
 */
export function quantiNellaVoce(voce) {
  const quanti = Number(voce?.count) || 0
  if (!quanti) return null
  if (voce.key === 'calls') {
    const minuti = Number(voce.minutes) || 0
    return quanti === 1
      ? ['One call · {0} min', [minuti]]
      : ['{0} calls · {1} min', [quanti, minuti]]
  }
  if (voce.key === 'sms') {
    return quanti === 1 ? ['One SMS', []] : ['{0} SMS', [quanti]]
  }
  if (voce.key === 'numbers') {
    return quanti === 1 ? ['One number', []] : ['{0} numbers', [quanti]]
  }
  return null
}

/**
 * How often a problem came back in the last days, as [sentence, values]: «Once»,
 * «3 times».
 */
export function quanteVolte(volte) {
  const quante = Number(volte) || 0
  return quante <= 1 ? ['Once', []] : ['{0} times', [quante]]
}
