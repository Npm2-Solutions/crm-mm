// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// The notifications panel, without a screen (docs/progetto-ghl/43-notifiche.md):
// how each kind looks, which day a notification is filed under, the time on its
// row. The server says what a notification is (`kind`), what it says and where
// it opens; here is only how it is drawn.

import { clockOf, wallClock } from '@/utils/conversation'

// Each kind in a cloud of a category of the design system, with its icon and
// the word that names it: amber a mention (the internal notes' colour), the
// brand what is given to you, gray what is taken back, green WhatsApp, blue
// the messages and documents, violet an automation (marketing's).
export const ASPETTI = {
  mention: { colore: 'amber', icona: 'at-sign', parola: 'Mention' },
  assigned: { colore: 'brand', icona: 'user-check', parola: 'Assignment' },
  unassigned: { colore: 'gray', icona: 'user-x', parola: 'Assignment' },
  task: { colore: 'brand', icona: 'square-check', parola: 'Task' },
  task_removed: { colore: 'gray', icona: 'square-x', parola: 'Task' },
  whatsapp: { colore: 'green', icona: 'whatsapp', parola: 'WhatsApp' },
  sms: { colore: 'blue', icona: 'message-square-text', parola: 'SMS' },
  area: {
    colore: 'blue',
    icona: 'message-circle-question',
    parola: 'Client area',
  },
  agenda: { colore: 'amber', icona: 'calendar-clock', parola: 'Agenda' },
  invoicing: { colore: 'blue', icona: 'receipt-text', parola: 'Invoicing' },
  automation: { colore: 'violet', icona: 'zap', parola: 'Automation' },
  other: { colore: 'gray', icona: 'bell', parola: 'Notification' },
}

/** How a kind looks; one the panel does not know, as a plain notification. */
export function aspetto(kind) {
  return ASPETTI[kind] || ASPETTI.other
}

// The days a notification is filed under, newest first.
export const SEZIONI = [
  { key: 'today', label: 'Today' },
  { key: 'yesterday', label: 'Yesterday' },
  { key: 'week', label: 'This week' },
  { key: 'older', label: 'Earlier' },
]

function midnight(date) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate())
}

function daysBetween(then, now) {
  // rounded: a day with a clock change in it is 23 or 25 hours long
  return Math.round((midnight(now) - midnight(then)) / 86400000)
}

/** Which day a moment is filed under, seen from `now`: both on the reader's clock. */
export function sezioneDi(at, now) {
  const date = wallClock(at)
  const reference = wallClock(now)
  if (!date || !reference) return 'older'
  const days = daysBetween(date, reference)
  if (days <= 0) return 'today'
  if (days === 1) return 'yesterday'
  if (days < 7) return 'week'
  return 'older'
}

/**
 * The rows in their days, newest first, a day only when it has some.
 * `momento(row)` is the row's moment on the reader's clock.
 */
export function sezioni(rows = [], now, momento = (row) => row.creation) {
  const perGiorno = {}
  for (const row of rows || []) {
    const key = sezioneDi(momento(row), now)
    ;(perGiorno[key] ||= []).push(row)
  }
  return SEZIONI.filter((s) => perGiorno[s.key]).map((s) => ({
    ...s,
    rows: perGiorno[s.key],
  }))
}

/**
 * The time on a row, under its day: the clock today and yesterday, the weekday
 * and the clock this week, the date before that (with the year once it is not
 * this one).
 */
export function orario(at, now, locale) {
  const date = wallClock(at)
  const reference = wallClock(now)
  if (!date || !reference) return ''
  const days = daysBetween(date, reference)
  const clock = clockOf(at, locale)
  if (days <= 1) return clock
  if (days < 7) {
    const day = new Intl.DateTimeFormat(locale, { weekday: 'short' }).format(
      date,
    )
    return `${day} ${clock}`
  }
  return new Intl.DateTimeFormat(locale, {
    day: 'numeric',
    month: 'short',
    year:
      date.getFullYear() === reference.getFullYear() ? undefined : 'numeric',
  }).format(date)
}

/** The words of a notification without its markup: a toast, a title. */
export function soloTesto(html) {
  return String(html || '')
    .replace(/<[^>]*>/g, '')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#x27;|&#39;/g, "'")
    .replace(/&amp;/g, '&')
    .replace(/\s+/g, ' ')
    .trim()
}

/** How many unread, as the sidebar's badge says it: «99+» past ninety-nine. */
export function conteggio(unread) {
  const n = Number(unread) || 0
  if (n <= 0) return ''
  return n > 99 ? '99+' : String(n)
}
