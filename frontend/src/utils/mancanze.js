// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * What invoicing still misses (crm.invoicing.prova.mancanze), and where each gap
 * is filled: a row names the company's field that fills it, or the records that
 * do. The settings page that opens is the one the menu has for them.
 */

/** The records a row may point at, and the page that keeps them. */
const PAGINA_DEI_RECORD = {
  'CRM Billable Service': 'Billable services',
  'CRM Service Provider': 'Providers',
  'CRM Professional Qualification': 'Qualification register',
}

/** The fields kept on the site's invoicing settings, not on the company. */
const CAMPI_DELLE_OPZIONI = new Set([
  'itala_client_id',
  'itala_client_secret',
  'itala_recipient_code',
])

/** The settings page where a missing row is filled, or '' when there is none. */
export function paginaDellaMancanza(voce) {
  if (!voce) return ''
  const doctype = voce.link?.doctype
  if (doctype) return PAGINA_DEI_RECORD[doctype] || ''
  if (!voce.field) return ''
  return CAMPI_DELLE_OPZIONI.has(voce.field)
    ? 'Invoicing defaults'
    : 'Issuing company'
}

/** What stops going live first, then the rest, each kept in the server's order. */
export function inOrdine(voci) {
  const righe = Array.isArray(voci) ? voci : []
  return [
    ...righe.filter((voce) => voce?.blocking),
    ...righe.filter((voce) => voce && !voce.blocking),
  ]
}
