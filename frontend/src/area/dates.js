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
        hourCycle: 'h23',
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

// How a date field shows the day it holds: the day first, as the patient
// writes it (a field given no format showed «2026-11-03»)
export const FORMATO_DEL_CAMPO = 'DD/MM/YYYY'
