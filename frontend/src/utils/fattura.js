// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * The invoice the dialog edits (crm/invoicing/emissione.py): what goes back to the
 * server, the totals worth a line, and what the dialog is called.
 */

const CAMPI_CLIENTE = [
  'party_type',
  'party',
  'billing_name',
  'first_name',
  'last_name',
  'fiscal_code',
  'tax_id',
  'recipient_type',
  'recipient_code',
  'pec',
  'address_line',
  'civic_number',
  'postal_code',
  'city',
  'province',
  'country',
]
const CAMPI_PAGAMENTO = [
  'payment_method',
  'payment_date',
  'advance_payment',
  'privacy_opposition',
  'causale',
]

function scegli(oggetto, campi) {
  const scelti = {}
  for (const campo of campi) {
    if (oggetto && campo in oggetto) scelti[campo] = oggetto[campo]
  }
  return scelti
}

/** What the dialog sends: the client, how it was paid, the lines that have a service. */
export function datiDaInviare(vista) {
  return {
    ...scegli(vista?.client, CAMPI_CLIENTE),
    ...scegli(vista?.payment, CAMPI_PAGAMENTO),
    items: (vista?.items || [])
      .filter((riga) => riga.billable_service)
      .map((riga) => ({
        billable_service: riga.billable_service,
        service_provider: riga.service_provider || '',
        description: riga.description || '',
        qty: Number(riga.qty) || 1,
        rate: Number(riga.rate) || 0,
      })),
  }
}

const TOTALI = [
  ['net_total', 'Taxable amount'],
  ['fund_contribution', 'Fund contribution'],
  ['vat_total', 'VAT'],
  ['advances', 'Advances (art. 15)'],
  ['stamp_duty', 'Stamp duty'],
  ['grand_total', 'Total'],
  ['withholding', 'Withholding'],
  ['net_payable', 'Net payable'],
]

/**
 * The totals worth a line: the total always, the others when they are not zero,
 * and what is left to pay only when a withholding makes it differ from the total.
 */
export function righeDeiTotali(totali = {}) {
  return TOTALI.filter(([chiave]) => {
    const valore = Number(totali[chiave]) || 0
    if (chiave === 'grand_total') return true
    if (chiave === 'net_payable') {
      return valore !== (Number(totali.grand_total) || 0)
    }
    return valore !== 0
  }).map(([chiave, etichetta]) => ({
    chiave,
    etichetta,
    valore: Number(totali[chiave]) || 0,
    forte: chiave === 'grand_total' || chiave === 'net_payable',
  }))
}

/**
 * What the dialog is called: a new invoice, a draft, or the document by its
 * number - a credit note saying it is one.
 */
export function titoloDellaFattura(vista) {
  const nota = Boolean(vista?.is_note)
  if (!vista?.name) return nota ? 'New credit note' : 'New invoice'
  if (!vista.document_number) {
    return nota ? 'Draft credit note' : 'Draft invoice'
  }
  return nota ? 'Credit note {0}' : 'Invoice {0}'
}

/** A line nobody has filled yet. */
export function rigaVuota(professionista = '') {
  return {
    billable_service: '',
    service_provider: professionista || '',
    description: '',
    qty: 1,
    rate: 0,
  }
}
