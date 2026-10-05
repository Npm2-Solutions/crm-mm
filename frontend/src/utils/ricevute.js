// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * The suppliers' invoices as the «Received» tab reads them (crm/invoicing/ricevute.py):
 * what the desk did with one, when it is due, which months go to the accountant.
 * The words come through the translator handed in (`t`), so a test reads them in
 * English and the page in the user's language.
 */

/** What the desk can say of one, in order, with its colour. */
export const STATI = [
  { value: 'ricevuta', label: 'To see', theme: 'orange' },
  { value: 'letta', label: 'Seen', theme: 'blue' },
  { value: 'registrata', label: 'To the accountant', theme: 'green' },
  { value: 'rifiutata', label: 'Disputed', theme: 'red' },
]

/** The state as the badge draws it. */
export function statoRicevuta(stato, t = (testo) => testo) {
  const trovato = STATI.find((s) => s.value === stato) || STATI[0]
  return { label: t(trovato.label), theme: trovato.theme }
}

/** The filters above the list: everything, each state, what is left to pay. */
export function filtriRicevute(t = (testo) => testo) {
  return [
    { value: '', label: t('All') },
    { value: 'ricevuta', label: t('To see') },
    { value: 'da_pagare', label: t('To pay') },
    { value: 'registrata', label: t('To the accountant') },
    { value: 'rifiutata', label: t('Disputed') },
  ]
}

/**
 * When one is to be paid, as a line: paid, overdue, due in some days, or nothing
 * where the supplier wrote no term. `oggi` is the centre's day (YYYY-MM-DD).
 */
export function scadenzaRicevuta(riga, oggi, t = (testo) => testo) {
  if (!riga) return null
  if (riga.paid_on) return { label: t('Paid'), theme: 'green' }
  if (riga.status === 'rifiutata' || !riga.due_date) return null
  const giorni = Math.round(
    (Date.parse(riga.due_date) - Date.parse(oggi)) / 86400000,
  )
  if (giorni < 0) return { label: t('Overdue'), theme: 'red' }
  if (giorni === 0) return { label: t('Due today'), theme: 'orange' }
  return {
    label: t('Due in {0} days', [giorni]),
    theme: giorni <= 7 ? 'orange' : 'gray',
  }
}

/**
 * The months one can hand the accountant: this one and the eleven before it,
 * the newest first. `oggi` is the centre's day (YYYY-MM-DD); `nomeDelMese`
 * names a month (1-12) in the reader's language.
 */
export function mesiDaEsportare(oggi, nomeDelMese) {
  const [anno, mese] = String(oggi).split('-').map(Number)
  const mesi = []
  for (let i = 0; i < 12; i++) {
    const totale = anno * 12 + (mese - 1) - i
    const a = Math.floor(totale / 12)
    const m = (totale % 12) + 1
    mesi.push({
      value: `${a}-${String(m).padStart(2, '0')}`,
      label: `${nomeDelMese(m)} ${a}`,
      year: a,
      month: m,
    })
  }
  return mesi
}
