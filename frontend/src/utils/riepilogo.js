// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * A person's summary (components/Activities/SummaryArea.vue): what one needs
 * to know of them at a glance, the page they open on from the People list and
 * the agenda (docs/progetto-ghl/54). The server says what each module has for
 * them (`crm.persone.riepilogo.get_summary`); these say which of their
 * appointments to name, the last thing said, when a task is due. Pure, so the
 * page only draws.
 */

// done, cancelled or missed: never what comes next, whatever the clock says
const CHIUSI = ['Completed', 'Cancelled', 'No Show']

/** A moment as the server writes it ("YYYY-MM-DD HH:mm:ss", the centre's clock). */
function momento(valore) {
  const d = new Date(String(valore || '').replace(' ', 'T'))
  return Number.isNaN(d.getTime()) ? null : d
}

/**
 * The appointments still to come, the soonest first, at most `quanti`.
 * `appuntamenti` as `crm.api.appointments.get_person_appointments` gives them;
 * `adesso` is the centre's now (`adessoDelCentro()`).
 */
export function prossimi(appuntamenti = [], adesso = new Date(), quanti = 3) {
  return (appuntamenti || [])
    .filter((a) => {
      const inizio = momento(a?.starts_on)
      return inizio && inizio >= adesso && !CHIUSI.includes(a.status)
    })
    .sort((a, b) => momento(a.starts_on) - momento(b.starts_on))
    .slice(0, quanti)
}

/**
 * The last appointment that was theirs before now, however it went - came,
 * did not come, or not marked yet. A cancelled one was nobody's.
 */
export function ultimo(appuntamenti = [], adesso = new Date()) {
  let fatto = null
  for (const a of appuntamenti || []) {
    const inizio = momento(a?.starts_on)
    if (!inizio || inizio >= adesso || a.status === 'Cancelled') continue
    if (!fatto || inizio > momento(fatto.starts_on)) fatto = a
  }
  return fatto
}

/** An appointment's status in its colour, as the Events tab draws it. */
export const TEMA_DELLO_STATO = {
  Scheduled: 'blue',
  Confirmed: 'green',
  Completed: 'gray',
  'No Show': 'red',
  Cancelled: 'gray',
}

/**
 * The last thing said, from what the person carries
 * (`last_conversation_*`, written as each message arrives or leaves): by
 * which channel, from them or from here, its first words, and whether the
 * conversation waits to be read. Nothing when nobody ever wrote.
 */
export function ultimoMessaggio(persona = {}) {
  if (!persona?.last_conversation_on) return null
  return {
    canale: persona.last_conversation_channel || '',
    loro: persona.last_conversation_direction === 'Incoming',
    testo: String(persona.last_conversation_preview || '').trim(),
    quando: persona.last_conversation_on,
    daLeggere: Boolean(Number(persona.conversation_unread)),
  }
}

/**
 * When a task is due, against today ("YYYY-MM-DD", the centre's): late,
 * today, or later; nothing for a task without a day.
 */
export function scadenza(dueDate, oggi) {
  const giorno = String(dueDate || '').slice(0, 10)
  if (!giorno) return null
  if (giorno < oggi) return 'late'
  if (giorno === oggi) return 'today'
  return 'later'
}

/** Whether there is anything at all to sum up, or the page says so. */
export function qualcosaDaDire({
  messaggio = null,
  appuntamenti = [],
  ultimoAppuntamento = null,
  righe = {},
} = {}) {
  return Boolean(
    messaggio ||
      appuntamenti.length ||
      ultimoAppuntamento ||
      Object.keys(righe || {}).length,
  )
}
