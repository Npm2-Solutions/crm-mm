// Dates as the patient reads them, in their language.
import { locale } from './translation'

function parse(value) {
  if (!value) return null
  const date = new Date(String(value).replace(' ', 'T'))
  return isNaN(date) ? null : date
}

export function day(value) {
  const date = parse(value)
  return date
    ? date.toLocaleDateString(locale, {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
      })
    : ''
}

export function when(value) {
  const date = parse(value)
  return date
    ? date.toLocaleString(locale, {
        weekday: 'long',
        day: 'numeric',
        month: 'long',
        hour: '2-digit',
        minute: '2-digit',
      })
    : ''
}

export function money(value) {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: 'EUR',
  }).format(Number(value || 0))
}

// a day in a row of days: "mer 30"
export function shortDay(value) {
  const date = parse(value)
  return date
    ? date.toLocaleDateString(locale, { weekday: 'short', day: 'numeric' })
    : ''
}
