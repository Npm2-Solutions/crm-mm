// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { CONTESTO } from '@/utils/rapporto'

// the values a field reads in a context of their own: a person's step says
// «Lead» and «Cliente», never the address book's «Contatto»
export const CONTESTI_DEI_CAMPI = { relationship: CONTESTO }

/**
 * The heading of a group, in a list grouped by one of its fields (the People
 * and the Deals lists): the value as a row reads it. A choice or a linked
 * name in the reader's words (a status, a source: what the centre wrote
 * stays as written), a person's step in its own context, a yes or a no, a
 * colleague by name, a day as a date; a group with nothing in that field
 * says so.
 *
 * `campo` is the list's `group_by_field` (`fieldname`, `fieldtype` and, for
 * a link, `link_doctype`); `t` translates, `utente` names a user, `giorno`
 * writes a day.
 */
export function intestazioneDelGruppo(valore, campo = {}, aiuti = {}) {
  const { t = (testo) => testo, utente, giorno } = aiuti
  const tipo = campo?.fieldtype
  // a tick is never «not set»: the list groups the unticked with the empty
  if (tipo === 'Check') return Number(valore) ? t('Yes') : t('No')
  if (valore === null || valore === undefined || valore === '') {
    return t('Not set')
  }
  if (campo?.link_doctype === 'User' && utente) return utente(valore) || valore
  if (tipo === 'Date' && giorno) return giorno(valore)
  if (tipo === 'Select' || tipo === 'Link') {
    return t(String(valore), null, CONTESTI_DEI_CAMPI[campo.fieldname])
  }
  return String(valore)
}
