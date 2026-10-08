// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * The reminders of the appointments (crm/scheduling/promemoria.py) as the
 * screens read them: what the person answered, as a mark with its words; how a
 * reminder went, in one line; the templates that can carry the answers.
 *
 * The answers and the states are stored in English (`CRM Appointment Reminder`):
 * here they become words, never shown as they are.
 */

const fmt = (s) => s

/** The answers, as the server keeps them. */
export const CONFERMA = 'Confirmed'
export const NON_VIENE = 'Cannot come'
export const SPOSTA = 'Wants to move'

/** How a reminder went. */
export const INVIATO = 'Sent'

/**
 * The mark of a person's answer, for an appointment's block: an icon with its
 * words. Nothing while the reminder waits for an answer - every block of
 * tomorrow would carry a bell -, and a mark that calls for a call when it did
 * not arrive.
 */
export function segnoDelPromemoria(promemoria, t = fmt) {
  if (!promemoria) return null
  const segno = (icona, testo) => ({ chiave: 'promemoria', icona, testo })
  if (promemoria.answer === CONFERMA)
    return segno('lucide-thumbs-up', t('Confirmed they are coming'))
  if (promemoria.answer === NON_VIENE)
    return segno(
      'lucide-calendar-x',
      promemoria.cancelled ? t('Cannot come: cancelled') : t('Cannot come'),
    )
  if (promemoria.answer === SPOSTA)
    return segno('lucide-calendar-clock', t('Would like to move it'))
  if (promemoria.status && promemoria.status !== INVIATO)
    return segno('lucide-bell-off', t('Reminder not delivered'))
  return null
}

/**
 * What the person of an appointment of one answered the reminder, as its mark:
 * the grid's block and the phone's day list say the same. A class says nothing
 * here: each of its people answered on their own row.
 */
export function rispostaDellAppuntamento(appuntamento, t = fmt) {
  const persone = appuntamento?.participants || []
  return persone.length === 1
    ? segnoDelPromemoria(persone[0].reminder, t)
    : null
}

/**
 * A reminder in one line, for the appointment's panel and the settings' list:
 * how it went and what was answered - «Reminder sent by WhatsApp · Confirmed
 * they are coming».
 */
export function rigaDelPromemoria(promemoria, t = fmt) {
  if (!promemoria) return ''
  // one whole sentence for each way: the way is never glued into another
  const andato =
    promemoria.status === INVIATO
      ? t(
          {
            WhatsApp: 'Reminder sent by WhatsApp',
            SMS: 'Reminder sent by SMS',
            Email: 'Reminder sent by email',
          }[promemoria.channel] || 'Reminder sent',
        )
      : t('Reminder not delivered')
  const segno = segnoDelPromemoria({ ...promemoria, status: INVIATO }, t)
  return segno ? `${andato} · ${segno.testo}` : andato
}

/** The templates whose buttons say the answers: the only ones to choose. */
export function modelliAdatti(modelli) {
  return (modelli || []).filter((modello) => modello.suitable)
}

/**
 * Where DottorCloud's own template is with Meta: to be made, waiting for its
 * review, refused, approved.
 */
export function statoDelNostro(nostro) {
  if (!nostro) return 'da_fare'
  const stato = String(nostro.status || '').toUpperCase()
  if (stato === 'APPROVED') return 'approvato'
  if (stato === 'REJECTED') return 'rifiutato'
  return 'in_attesa'
}

/**
 * What is wrong with the second reminder's hours, the same day's (empty: none):
 * 1 to 12, and fewer than the first's - the server says the same on saving.
 */
export function problemaDelSecondo(secondo, primo, t = fmt) {
  if (secondo === '' || secondo === null || secondo === undefined) return ''
  const ore = Number(secondo)
  if (!Number.isInteger(ore) || ore < 0 || ore > 12)
    return t('From 1 to 12 hours before.')
  if (ore && ore >= Number(primo))
    return t('Fewer hours than the first reminder.')
  return ''
}
