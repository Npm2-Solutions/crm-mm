// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * An event's reminder in words, whole in every language: «1 giorno prima,
 * alle 08:00», «15 minuti prima, per email». The event's panel glued the
 * English unit and «as email» into the sentence («15 minutes prima, as
 * email»), and the editor of an all-day event said «1 giorno before at
 * 8:00 am».
 */
const UNITA = {
  minutes: ['minute', 'minutes'],
  hours: ['hour', 'hours'],
  days: ['day', 'days'],
  weeks: ['week', 'weeks'],
}

/** The time an all-day event's reminder leaves, on the 24-hour clock. */
export function oraDelPromemoria(time) {
  const [ore, minuti] = String(time || '08:00')
    .split(':')
    .map((parte) => Number(parte) || 0)
  return `${String(ore).padStart(2, '0')}:${String(minuti).padStart(2, '0')}`
}

// with no translator, English: the sentence filled as `__` fills it
function inglese(testo, argomenti = []) {
  return testo.replace(/\{(\d)\}/g, (_, i) => argomenti[i] ?? '')
}

/**
 * A reminder `{ before, interval, time, type }` in words; `t` is the
 * translator (`__`), an all-day event's reminder says at what time it leaves.
 */
export function promemoriaInParole(
  avviso,
  { tuttoIlGiorno = false, t = inglese } = {},
) {
  const quanti = Number(avviso?.before) || 0
  const [uno, molti] = UNITA[avviso?.interval] || UNITA.minutes
  const unita = t(quanti === 1 ? uno : molti)
  const perEmail = avviso?.type === 'Email'
  if (tuttoIlGiorno) {
    const ora = oraDelPromemoria(avviso?.time)
    return perEmail
      ? t('{0} {1} before, at {2}, by email', [quanti, unita, ora])
      : t('{0} {1} before, at {2}', [quanti, unita, ora])
  }
  return perEmail
    ? t('{0} {1} before, by email', [quanti, unita])
    : t('{0} {1} before', [quanti, unita])
}
