// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// The phone at hand (components/Telephony/PhonePanel.vue): the keypad's
// number, whether what is typed is a number or a name, a call's moment in a few
// words. Pure, so the panel only draws and the rules are tested.

/** The longest number a keypad takes: E.164 with room for a pause. */
export const MASSIMO = 20

const AMMESSI = /^[0-9*#+]$/

/** The number with one more key: only what a phone dials, `+` only first. */
export function digita(numero, tasto, massimo = MASSIMO) {
  const attuale = String(numero || '')
  const t = String(tasto || '')
  if (!AMMESSI.test(t) || attuale.length >= massimo) return attuale
  if (t === '+' && attuale.length) return attuale
  return attuale + t
}

/** The number with its last key taken away. */
export function cancella(numero) {
  return String(numero || '').slice(0, -1)
}

/**
 * Whether what is typed is a number to dial (digits, a leading +, spaces, the
 * dashes and dots one writes numbers with) or a name to look for.
 */
export function eNumero(testo) {
  const t = String(testo || '').trim()
  return Boolean(t) && /^\+?[0-9\s\-./()*#]+$/.test(t) && /\d/.test(t)
}

/** What the keypad dials: the digits, the + and the tones, nothing else. */
export function daComporre(testo) {
  const t = String(testo || '').trim()
  const segni = t.replace(/[^0-9*#+]/g, '')
  return segni.startsWith('+')
    ? `+${segni.slice(1).replace(/\+/g, '')}`
    : segni.replace(/\+/g, '')
}

/**
 * A number written to be read, never dialled nor saved: an Italian mobile in
 * groups («+39 333 123 4567»), Milan's and Rome's landlines after their prefix
 * («+39 02 1234 5678»), any other Italian number with its country apart; a
 * number of another country, a masked one, anything that is not a number, as
 * it was written. Stored as E.164, a number read «+393331234567».
 */
export function leggibile(numero) {
  const scritto = String(numero || '').trim()
  const m = scritto.replace(/[\s.\-/()]/g, '').match(/^(\+39|0039)?(\d+)$/)
  if (!m || (!m[1] && !/^[03]/.test(m[2]))) return scritto
  const paese = m[1] ? '+39 ' : ''
  const cellulare = m[2].match(/^(3\d{2})(\d{3})(\d{3,4})$/)
  if (cellulare) return paese + cellulare.slice(1).join(' ')
  const fisso = m[2].match(/^(0[26])(\d{4})(\d{2,4})$/)
  if (fisso) return paese + fisso.slice(1).join(' ')
  return m[1] ? paese + m[2] : scritto
}

const GIORNO = 24 * 60 * 60 * 1000

/**
 * A call's moment in a few words: the hour today, «yesterday» (as `ieri`, the
 * word given), the day this week, else the date.
 */
export function quandoChiamata(
  quando,
  adesso = new Date(),
  locale,
  ieri = 'yesterday',
) {
  const momento = new Date(String(quando || '').replace(' ', 'T'))
  if (Number.isNaN(momento.getTime())) return ''
  const inizio = (d) => new Date(d.getFullYear(), d.getMonth(), d.getDate())
  const giorni = Math.round((inizio(adesso) - inizio(momento)) / GIORNO)
  if (giorni <= 0)
    return new Intl.DateTimeFormat(locale, {
      hour: '2-digit',
      minute: '2-digit',
      hourCycle: 'h23',
    }).format(momento)
  if (giorni === 1) return ieri
  if (giorni < 7)
    return new Intl.DateTimeFormat(locale, { weekday: 'long' }).format(momento)
  return new Intl.DateTimeFormat(locale, {
    day: 'numeric',
    month: 'short',
  }).format(momento)
}

/** The page a call's person opens on: their own, or the deal's. */
export function paginaDi(chiamata) {
  if (!chiamata?.reference_docname) return null
  if (chiamata.reference_doctype === 'CRM Lead')
    return { name: 'Lead', params: { leadId: chiamata.reference_docname } }
  if (chiamata.reference_doctype === 'CRM Deal')
    return { name: 'Deal', params: { dealId: chiamata.reference_docname } }
  return null
}
