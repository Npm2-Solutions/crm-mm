/**
 * What an invoice looks like when it is read rather than edited.
 *
 * The console and the conversation both show the same invoice, so the words and
 * the colours live here once. Two screens deciding on their own what `scartata`
 * means is how the same document ends up orange on one and red on the other.
 */

/**
 * What a transmission state means, as a colour.
 *
 * Green is settled, red is refused, blue is on its way, orange is still ours to
 * do. The states are Italian because they are the words the Agenzia delle
 * Entrate and the Sistema TS use, and translating them would break the only
 * link somebody has between this screen and a portal receipt.
 */
export function invoiceStatusTheme(status) {
  if (['accolto', 'consegnata', 'scaricato'].includes(status)) return 'green'
  if (['scartato', 'scartata', 'errore', 'mancata_consegna'].includes(status))
    return 'red'
  if (['inviato', 'pronto', 'pronto_export'].includes(status)) return 'blue'
  return 'orange'
}

/** Whether a state is worth showing at all. */
export function isRealStatus(status) {
  return Boolean(status) && status !== 'non_applicabile'
}

/**
 * The one state that matters most, of the two an invoice carries.
 *
 * An invoice can be going to the SdI and to the Sistema TS at once, and a row in
 * a conversation has room for one badge. A refusal outranks everything: it is
 * the only one of these states that is somebody's job to fix today.
 */
export function worstStatus(invoice = {}) {
  const both = [invoice.sdi_status, invoice.ts_status].filter(isRealStatus)
  if (!both.length) return ''
  const refused = both.find((s) => invoiceStatusTheme(s) === 'red')
  return refused || both[0]
}

/**
 * Credit notes read as money going the other way, and TD04 says so to nobody.
 *
 * Only the few types that change how the amount should be read are named; the
 * rest are ordinary invoices and do not need a caption to say so.
 */
const CREDIT_NOTES = ['TD04', 'TD08']

export function isCreditNote(documentType) {
  return CREDIT_NOTES.includes(documentType)
}

/** Euros, the way Italy writes them. */
export function formatEuro(value) {
  return new Intl.NumberFormat('it-IT', {
    style: 'currency',
    currency: 'EUR',
  }).format(value || 0)
}

/**
 * What to call the document in one line: its number when it has one, and a
 * draft says it is a draft rather than showing a number it has not been given.
 */
export function invoiceLabel(invoice = {}) {
  if (invoice.docstatus === 0) return 'Draft'
  return invoice.document_number || invoice.name || ''
}
