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
