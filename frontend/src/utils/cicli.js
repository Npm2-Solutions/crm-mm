// Cycles of sessions in words: how far a cycle is, which session an appointment
// is, what a new cycle may be. The rules are crm/scheduling/cicli_regole.py's.

export const MAX_SEDUTE = 100
export const PER_SEDUTA = 'Per session'
export const INTERO = 'The whole cycle'

// Active, Expired, Completed, Closed: where a cycle stands
export const TEMA_DELLO_STATO = {
  Active: 'green',
  Expired: 'orange',
  Completed: 'blue',
  Closed: 'gray',
}

// how each appointment went, for the cycle
export const SEDUTA = {
  done: { label: 'Done', theme: 'green' },
  missed: { label: 'Missed', theme: 'red' },
  booked: { label: 'Booked', theme: 'blue' },
  cancelled: { label: 'Cancelled', theme: 'gray' },
}

// "Session 4 of 10", or nothing when the appointment has no number
export function laSeduta(ciclo, t = (s, a) => format(s, a)) {
  if (!ciclo?.number || !ciclo?.total) return ''
  return t('Session {0} of {1}', [ciclo.number, ciclo.total])
}

// "4 of 10 done · 2 booked · 1 missed"
export function comeVa(conti, t = (s, a) => format(s, a)) {
  if (!conti) return ''
  // sessions: «fatte», where the first steps are «fatti»
  const parti = [
    t('{0} of {1} done', [conti.done, conti.total], 'Cycle sessions'),
  ]
  if (conti.booked) parti.push(t('{0} booked', [conti.booked]))
  if (conti.missed) parti.push(t('{0} missed', [conti.missed]))
  return parti.join(' · ')
}

// what is left to book, in words
export function daPrenotare(conti, t = (s, a) => format(s, a)) {
  if (!conti) return ''
  if (!conti.left) return t('Nothing left to book')
  return conti.left === 1
    ? t('1 session to book')
    : t('{0} sessions to book', [conti.left])
}

// a session's share of the cycle's price, in cents as the server rounds it
export function quota(prezzo, sedute) {
  const p = Number(prezzo)
  const n = Number(sedute)
  if (!(p > 0) || !(n > 0)) return 0
  return Math.round((p / n) * 100) / 100
}

// the used part, for the bar: done and missed that count, over the total
export function percentuale(conti) {
  if (!conti?.total) return 0
  return Math.min(100, Math.round((conti.used / conti.total) * 100))
}

// The sessions as the design system's steps: one segment each, the used ones
// in the brand's colour. Past `massimo` the segments would be slivers, and the
// bar of percentuale() says it better: null.
export function tappe(conti, massimo = 30) {
  if (!conti?.total || conti.total > massimo) return null
  const usate = Math.min(conti.used || 0, conti.total)
  return Array.from({ length: conti.total }, (_, i) => i < usate)
}

// another appointment fits in it
export function siPrenota(ciclo) {
  return ciclo?.status === 'Active' && (ciclo.counts?.left || 0) > 0
}

// what the form says before the server does: the first thing to put right
export function errore(modulo, t = (s, a) => format(s, a)) {
  const sedute = Number(modulo.sessions)
  if (!modulo.service) return t('Choose the service of the sessions')
  if (!Number.isInteger(sedute) || sedute < 1 || sedute > MAX_SEDUTE)
    return t('A cycle has from 1 to {0} sessions', [MAX_SEDUTE])
  if (
    modulo.valid_until &&
    modulo.starts_on &&
    modulo.valid_until < modulo.starts_on
  )
    return t('A cycle ends after it starts')
  if (modulo.billing === INTERO && !(Number(modulo.price) > 0))
    return t('A cycle paid as a whole has its price')
  return ''
}

// the form as the server takes it
export function perIlServer(modulo) {
  return {
    service: modulo.service,
    sessions: Number(modulo.sessions),
    starts_on: modulo.starts_on || null,
    valid_until: modulo.valid_until || null,
    price: Number(modulo.price) > 0 ? Number(modulo.price) : null,
    billing: modulo.billing === INTERO ? INTERO : PER_SEDUTA,
    missed_count: modulo.missed_count ? 1 : 0,
    practitioner: modulo.practitioner || null,
    notes: (modulo.notes || '').trim() || null,
  }
}

function format(testo, argomenti = []) {
  return testo.replace(/{(\d+)}/g, (tutto, n) =>
    argomenti[n] === undefined ? tutto : String(argomenti[n]),
  )
}
