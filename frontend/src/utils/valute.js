// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * Currencies by their name in the reader's language, for a choice that stores
 * the code (ISO 4217): a service's, a room's, a price list's, the dashboard's.
 * The names are the browser's own (Intl), so nothing is translated here; a
 * price is written as the rest of DottorCloud writes it, «65,00 €», never
 * «65 EUR».
 */

/** A currency's name in the reader's language («Euro»), its code when there is none. */
export function nomeDellaValuta(codice, lingua = 'it') {
  if (!codice) return ''
  let nome
  try {
    nome =
      new Intl.DisplayNames([lingua || 'it'], { type: 'currency' }).of(
        codice,
      ) || codice
  } catch {
    return codice
  }
  // Italian writes «euro» in a sentence; a choice starts with a capital
  return nome.charAt(0).toLocaleUpperCase(lingua || 'it') + nome.slice(1)
}

/**
 * The currencies to choose from, `{ label, value }` by their names in the
 * reader's language, the one stored kept among them even when it is no longer
 * offered.
 */
export function valuteDaScegliere({
  codici = [],
  scelta = '',
  lingua = 'it',
} = {}) {
  const tutte = [...new Set(codici.filter(Boolean))]
  if (scelta && !tutte.includes(scelta)) tutte.push(scelta)
  const ordine = new Intl.Collator(lingua || 'it')
  return tutte
    .map((codice) => ({
      label: nomeDellaValuta(codice, lingua),
      value: codice,
    }))
    .sort((a, b) => ordine.compare(a.label, b.label))
}

/** A currency's sign beside an amount one types («$», «€», «CHF»). */
export function simboloDellaValuta(codice, lingua = 'it') {
  if (!codice) return ''
  try {
    return (
      new Intl.NumberFormat(lingua || 'it', {
        style: 'currency',
        currency: codice,
        currencyDisplay: 'narrowSymbol',
      })
        .formatToParts(0)
        .find((parte) => parte.type === 'currency')?.value || codice
    )
  } catch {
    return codice
  }
}

/** An amount in a currency as the reader writes it («65,00 €»). */
export function prezzo(importo, valuta, lingua = 'it') {
  try {
    return new Intl.NumberFormat(lingua || 'it', {
      style: 'currency',
      currency: valuta || 'EUR',
    }).format(Number(importo) || 0)
  } catch {
    return `${importo ?? ''} ${valuta || ''}`.trim()
  }
}
