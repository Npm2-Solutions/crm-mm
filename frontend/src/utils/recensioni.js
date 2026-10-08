// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * The review requests' settings checked where they are typed, as the server
 * checks them (crm/recensioni/regole.py): each problem under its own field. Pure:
 * tested.
 */

export const MESI_MASSIMI = 60

/** A review link is a web address the browser opens: https only, no spaces. */
export function linkValido(link) {
  const testo = String(link || '').trim()
  return !testo || /^https:\/\/[^\s/]+\.[^\s/]+(\/\S*)?$/.test(testo)
}

/** Google's place ids are letters, digits, dashes and underscores. */
export function placeIdValido(placeId) {
  const testo = String(placeId || '').trim()
  return !testo || /^[A-Za-z0-9_-]{10,}$/.test(testo)
}

/** The months between two requests: a whole number from 1 to 60, never 0. */
export function mesiValidi(mesi) {
  const numero = Number(mesi)
  return (
    String(mesi ?? '').trim() !== '' &&
    Number.isInteger(numero) &&
    numero >= 1 &&
    numero <= MESI_MASSIMI
  )
}

/** What is wrong with the settings, field by field: `{ campo: [message, args] }`. */
export function problemiDelleRecensioni(form) {
  const problemi = {}
  if (!linkValido(form.google_review_link)) {
    problemi.google_review_link = [
      'The review link is a web address starting with https://',
    ]
  }
  if (!placeIdValido(form.google_place_id)) {
    problemi.google_place_id = [
      'A Google Place ID is made of letters, digits, dashes and underscores',
    ]
  }
  if (!mesiValidi(form.months_between)) {
    problemi.months_between = ['From {0} to {1} months', [1, MESI_MASSIMI]]
  }
  return problemi
}
