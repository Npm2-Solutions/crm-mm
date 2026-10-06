// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * Settings > Invoicing > Fatture in Cloud (crm/invoicing/fic): what the page
 * draws, decided once. The server says what is connected and what stands for
 * what (`collegamento.get_fic`); here, which of the page's states that is, the
 * selects' options and what is sent back when saving.
 *
 * Fatture in Cloud's own ids are numbers, the ordinary rate's is 0: never read
 * one as «nothing chosen».
 */

/**
 * Where the connection is:
 * - `agenzia`: the agency has not set the app up on this server
 * - `scollegato`: nobody connected it yet
 * - `da_ricollegare`: the access is gone, somebody has to sign in again
 * - `da_scegliere`: connected, the company there still to choose
 * - `collegato`: connected to a company
 */
export function statoDelCollegamento(dati) {
  if (!dati) return ''
  if (!dati.configured) return 'agenzia'
  if (!dati.connected) return 'scollegato'
  if (dati.needs_reconnect) return 'da_ricollegare'
  if (!dati.fic_company) return 'da_scegliere'
  return 'collegato'
}

/** Whether a value is a choice: 0 is Fatture in Cloud's ordinary rate. */
export function scelto(valore) {
  return valore !== null && valore !== undefined && valore !== ''
}

/** A select's options, the empty one first, every value a string. */
export function opzioni(riga, vuota) {
  return [
    { label: vuota, value: '' },
    ...((riga && riga.options) || []).map((opzione) => ({
      label: opzione.label,
      value: String(opzione.value),
    })),
  ]
}

/** A numeration as a person reads it: the main one by its words. */
export function nomeDellaNumerazione(numerazione, t = (s) => s) {
  return numerazione ? numerazione : t('Main numbering')
}

/** The numerations as a select's options, what is chosen kept even when gone. */
export function opzioniDellaNumerazione(voce, t = (s) => s) {
  const valori = [...((voce && voce.options) || [])]
  const attuale = (voce && voce.value) || ''
  if (!valori.includes(attuale)) valori.push(attuale)
  return valori.map((valore) => ({
    label: nomeDellaNumerazione(valore, t),
    value: valore,
  }))
}

/** What the page edits, out of what the server says. */
export function modulo(dati) {
  const valori = (righe, chiave) =>
    Object.fromEntries(
      ((dati && dati[righe]) || []).map((riga) => [
        riga[chiave],
        scelto(riga.value) ? String(riga.value) : '',
      ]),
    )
  const numerazioni = (dati && dati.numerations) || {}
  return {
    vat: valori('vat', 'key'),
    accounts: valori('accounts', 'method'),
    numerations: {
      sdi: numerazioni.sdi?.value || '',
      paper: numerazioni.paper?.value || '',
      credit: numerazioni.credit?.value || '',
    },
    ts_by: (dati && dati.ts_by) || 'dottorcloud',
  }
}

/** What is sent when saving: each choice as Fatture in Cloud's number again. */
export function daSalvare(form) {
  const numeri = (oggetto) =>
    Object.fromEntries(
      Object.entries(oggetto || {})
        .filter(([, valore]) => scelto(valore))
        .map(([chiave, valore]) => [chiave, Number(valore)]),
    )
  return {
    vat: numeri(form.vat),
    accounts: numeri(form.accounts),
    numerations: { ...form.numerations },
    ts_by: form.ts_by,
  }
}

/** Whether what the page shows differs from what was saved. */
export function cambiato(form, salvato) {
  return JSON.stringify(daSalvare(form)) !== JSON.stringify(daSalvare(salvato))
}

/** Whether the switch may be turned on: connected to a company, nothing missing. */
export function siPuoAccendere(dati) {
  return (
    statoDelCollegamento(dati) === 'collegato' &&
    !((dati && dati.missing) || []).length
  )
}
