// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * Countries by their name in the reader's language, for a choice that stores
 * the two letters (ISO 3166-1): the billing details' country, the countries a
 * centre calls. The names are the browser's own (Intl), so nothing is
 * translated here.
 */

/** A country's name in the reader's language; its code when there is none. */
export function nomeDelPaese(codice, lingua = 'it') {
  try {
    return (
      new Intl.DisplayNames([lingua || 'it'], { type: 'region' }).of(codice) ||
      codice
    )
  } catch {
    return codice
  }
}

// what Intl names that is no country of ISO 3166-1: groupings, the codes only
// reserved (Ascension, the Canaries...), the test ones. Kosovo («XK») stays.
// prettier-ignore
const NON_PAESI = new Set([
  'AC', 'CP', 'CQ', 'DG', 'EA', 'EU', 'EZ', 'IC', 'QO', 'TA', 'UN', 'XA', 'XB', 'ZZ',
])

const LETTERE = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

/**
 * Every country, `{ label, value }` sorted by its name in the reader's
 * language. An old code that became another («SU», «YU») is left out: the
 * country is listed once, by its code of today.
 */
export function tuttiIPaesi(lingua = 'it') {
  let nomi
  try {
    nomi = new Intl.DisplayNames([lingua || 'it'], {
      type: 'region',
      fallback: 'none',
    })
  } catch {
    return []
  }
  const elenco = []
  for (const a of LETTERE) {
    for (const b of LETTERE) {
      const codice = a + b
      if (NON_PAESI.has(codice)) continue
      const nome = nomi.of(codice)
      if (!nome || nome === codice || !diOggi(codice)) continue
      elenco.push({ label: nome, value: codice })
    }
  }
  return elenco.sort((x, y) => x.label.localeCompare(y.label, lingua || 'it'))
}

/**
 * The countries to choose from with the one already stored among them: a code
 * that is not a country of today still reads as it was written.
 */
export function paesiConIlScelto(scelto, lingua = 'it') {
  const elenco = tuttiIPaesi(lingua)
  if (scelto && !elenco.some((p) => p.value === scelto)) {
    elenco.unshift({ label: nomeDelPaese(scelto, lingua), value: scelto })
  }
  return elenco
}

// a code is today's when the locale it makes keeps it: «SU» becomes «RU»
function diOggi(codice) {
  try {
    return Intl.getCanonicalLocales(`und-${codice}`)[0] === `und-${codice}`
  } catch {
    return false
  }
}
