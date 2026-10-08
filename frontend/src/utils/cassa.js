// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// The desk's cash closing (crm/invoicing/cassa.py): the drawer counted against
// what it should hold, to the cent, and the words for it.

/** An amount to the cent: never a float's tail, never «-0». */
function centesimi(valore) {
  const numero = Number(valore)
  return Number.isFinite(numero) ? Math.round(numero * 100) / 100 + 0 : 0
}

/**
 * The cash counted less the cash expected; null while nothing was counted.
 * Above zero the drawer holds more, below zero less.
 */
export function differenzaDiCassa(contati, attesi) {
  if (contati === null || contati === undefined || contati === '') return null
  // a drawer holds nothing below zero: no difference to say about it
  if (Number(contati) < 0) return null
  return centesimi(centesimi(contati) - centesimi(attesi))
}

/** How the drawer stands, in words: `t` translates, `soldi` writes an amount. */
export function fraseDellaDifferenza(differenza, t, soldi) {
  if (differenza === null || differenza === undefined) return ''
  if (differenza === 0) return t('The drawer is right')
  return differenza < 0
    ? t('{0} missing', [soldi(-differenza)])
    : t('{0} more than expected', [soldi(differenza)])
}

/** The tone of the difference: nothing to say, or something to look into. */
export function tonoDellaDifferenza(differenza) {
  if (differenza === null || differenza === undefined) return ''
  return differenza === 0 ? 'green' : 'amber'
}

/**
 * The cash counted as the reader writes it, to the cent («60,50» in Italian,
 * «60.50» in English): a number field showed the server's «60.5».
 */
export function cifreDellaCassa(valore, lingua) {
  if (valore === null || valore === undefined || valore === '') return ''
  const numero = Number(valore)
  if (!Number.isFinite(numero)) return String(valore)
  try {
    return new Intl.NumberFormat(lingua || 'it', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
      useGrouping: false,
    }).format(numero)
  } catch {
    return numero.toFixed(2)
  }
}

/**
 * The cash typed, read whatever the separator («60,5», «60.50», «1.234,50»):
 * the last comma or point is the decimal one. Null for nothing or not a number.
 */
export function letturaDellaCassa(testo) {
  let cifre = String(testo ?? '').replace(/[\s\u00a0€]/g, '')
  if (!cifre) return null
  const ultimo = Math.max(cifre.lastIndexOf(','), cifre.lastIndexOf('.'))
  if (ultimo >= 0) {
    const intero = cifre.slice(0, ultimo).replace(/[.,]/g, '')
    cifre = `${intero}.${cifre.slice(ultimo + 1)}`
  }
  const numero = Number(cifre)
  return Number.isFinite(numero) ? numero : null
}
