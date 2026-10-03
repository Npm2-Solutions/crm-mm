// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * The keyboard a phone opens for a field: the dial pad for a number to call,
 * the one with @ for an email, a web address's, the digits for a count, the
 * decimal pad for an amount, capitals for a code. Only the keyboard changes:
 * what the field keeps is the same, and no form of the app hands the value to
 * the browser's own checks. Nothing here offers the operator's own email or
 * phone (the inputs keep frappe-ui's autocomplete="off"): the field is somebody
 * else's.
 */

const TASTIERE = {
  // the dial pad, with + * #
  telefono: { type: 'tel' },
  email: { type: 'email', autocapitalize: 'none', spellcheck: 'false' },
  url: { type: 'url', autocapitalize: 'none', spellcheck: 'false' },
  // digits only: a count of days, places, minutes
  intero: { inputmode: 'numeric' },
  // digits and the separator of the phone's language: an amount, a percent
  decimale: { inputmode: 'decimal' },
  // letters and digits, in capitals, never corrected: a codice fiscale, a VAT number
  codice: {
    autocapitalize: 'characters',
    autocorrect: 'off',
    spellcheck: 'false',
  },
  // a code made only of digits: the Sistema TS's region, ASL, facility
  cifre: { inputmode: 'numeric', autocorrect: 'off', spellcheck: 'false' },
}

/** The attributes of a keyboard by its name (`telefono`, `email`, `url`, `intero`, `decimale`, `codice`, `cifre`). */
export function tastiera(nome) {
  return TASTIERE[nome] || {}
}

// fields whose value is a code written in capitals, whatever DocType holds them
const CODICI = new Set([
  'fiscal_code',
  'tax_id',
  'vat_number',
  'recipient_code',
  'iban',
])
const INDIRIZZI_WEB = new Set(['website', 'video_url'])
// emails named so where the field is no DocType's (a PEC is an email too)
const EMAIL = new Set(['email', 'email_id', 'pec'])

/** The keyboard for a field of a DocType's meta, from its type, options and name. */
export function tastieraDi(field) {
  if (!field) return {}
  const tipo = field.fieldtype
  if (tipo === 'Int') return tastiera('intero')
  if (['Float', 'Currency', 'Percent'].includes(tipo))
    return tastiera('decimale')
  if (tipo === 'Phone' || field.options === 'Phone') return tastiera('telefono')
  if (!['Data', undefined].includes(tipo)) return {}
  if (field.options === 'Email' || EMAIL.has(field.fieldname)) {
    return tastiera('email')
  }
  if (field.options === 'URL' || INDIRIZZI_WEB.has(field.fieldname)) {
    return tastiera('url')
  }
  if (field.options === 'IBAN' || CODICI.has(field.fieldname)) {
    return tastiera('codice')
  }
  return {}
}
