// Copyright (c) 2026, NPM2 Solutions Srl and contributors

/**
 * How far ahead a day is, as the sentence to translate and its values: the
 * singular and the plural apart. Eight days ahead used to read «in 1 weeks», a
 * month and a half «in 1 months»; the past already said «1 week ago».
 *
 * `giorni` is the whole days to go, at least one: less than a day is said in
 * hours and minutes by the caller.
 */
export function traQuanto(giorni) {
  if (giorni <= 1) return ['tomorrow', []]
  if (giorni < 7) return ['in {0} days', [giorni]]
  if (giorni < 14) return ['in 1 week', []]
  if (giorni < 31) return ['in {0} weeks', [Math.floor(giorni / 7)]]
  if (giorni < 62) return ['in 1 month', []]
  if (giorni < 365) return ['in {0} months', [Math.floor(giorni / 30)]]
  if (giorni < 730) return ['in 1 year', []]
  return ['in {0} years', [Math.floor(giorni / 365)]]
}

/**
 * The format of a task's due date: its day and hour, its day alone when it was
 * chosen without an hour (the picker gives it as its midnight). «5 ott, 00:00»
 * read as if it were due at midnight.
 */
export function formatoDellaScadenza(scadenza, conOra, soloGiorno) {
  return /[ T]00:00(:00(\.0+)?)?$/.test(String(scadenza || ''))
    ? soloGiorno
    : conOra
}
