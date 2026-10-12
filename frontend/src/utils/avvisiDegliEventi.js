// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// An event's reminder on the screen (docs/crm/43), without a screen: whose it
// is, what of it the browser keeps, when it goes. The server sends each person
// the reminders of their own events (`crm/api/event.py`); the browser keeps them
// in localStorage, one list per browser and not per user, so it keeps only the
// session's, only what the popup draws - never the description, which on an
// appointment's calendar copy is its notes - and nothing done or over.

/** What the popup draws of an event: all the browser keeps of it. */
export const CAMPI = [
  'event_name',
  'subject',
  'starts_on',
  'ends_on',
  'all_day_event',
  'owner',
  'event_participants',
]

function chiave(valore) {
  return String(valore ?? '')
    .trim()
    .toLowerCase()
}

/**
 * Whether an event's reminder is for `utente`, the session's user: they own it
 * or take part in it, by their name or by their `email` (the event keeps its
 * participants by email, and Administrator's name is not one).
 */
export function eDellUtente(evento, utente, email) {
  if (!evento || !utente) return false
  const io = new Set([utente, email].map(chiave).filter(Boolean))
  const partecipanti = Array.isArray(evento.event_participants)
    ? evento.event_participants
    : []
  return [evento.owner, ...partecipanti].some(
    (chi) => chiave(chi) && io.has(chiave(chi)),
  )
}

/** The event as the browser keeps it: what the popup draws, nothing else. */
export function soloIlNecessario(evento) {
  const tenuto = {}
  for (const campo of CAMPI) {
    if (evento?.[campo] !== undefined) tenuto[campo] = evento[campo]
  }
  return tenuto
}

/**
 * When the event is over, as the centre's clock writes it ("2026-10-12
 * 18:30:00"): its end, else its start; an all-day one, or a day without an
 * hour, at the end of its day. Null where it says no day.
 */
export function fineDellEvento(evento) {
  const quando = String(evento?.ends_on || evento?.starts_on || '')
    .replace('T', ' ')
    .slice(0, 19)
  if (!/^\d{4}-\d{2}-\d{2}/.test(quando)) return null
  if (evento.all_day_event || quando.length <= 10)
    return `${quando.slice(0, 10)} 23:59:59`
  return quando
}

/**
 * The reminders a browser keeps, read again: the session's user's (`utente`,
 * whom each was taken for), neither put away - closed on the screen, or among
 * the events they closed, kept in their settings (`completati`) - nor of an
 * event over at `adesso` (the centre's clock, as `fineDellEvento` writes it),
 * each with only what the popup draws.
 */
export function avvisiDaTenere(
  avvisi,
  { utente, completati = [], adesso } = {},
) {
  if (!utente || !Array.isArray(avvisi)) return []
  const chiusi = new Set(completati)
  return avvisi
    .filter((avviso) => {
      if (!avviso?.id || avviso.completed || chiusi.has(avviso.id)) return false
      if (avviso.utente !== utente) return false
      const fine = fineDellEvento(avviso.notification)
      return !(fine && adesso && fine < adesso)
    })
    .map((avviso) => ({
      id: avviso.id,
      utente: avviso.utente,
      completed: false,
      notification: soloIlNecessario(avviso.notification),
      createdAt: avviso.createdAt,
    }))
}
