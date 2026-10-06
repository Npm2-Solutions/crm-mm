// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * Words a site was given in English when it was made (the default pipeline,
 * «Sales», and its stages, «Qualification»), shown in a field one can edit.
 * The field reads them in the reader's language; what is not changed is saved
 * as it was stored - a stage's name is the deals' link to it - and what one
 * writes is one's own.
 */

/** A shipped word as the reader reads it; nothing for nothing. */
export function inParole(valore, t = (testo) => testo) {
  return valore ? t(valore) : ''
}

/** What to save of a field that showed `originale` in the reader's words. */
export function daSalvare(scritto, originale, t = (testo) => testo) {
  return originale && scritto === inParole(originale, t) ? originale : scritto
}
