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
