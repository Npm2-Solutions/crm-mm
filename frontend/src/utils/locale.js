// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * The language the CRM speaks to this user, for `Intl`.
 *
 * Dates and numbers were written in the browser's language while the words
 * around them were in the user's: «Domenica 16 agosto» under «Appointment»,
 * «2,8 Mio USD» on an English dashboard, «lun 28» in an English rota. The boot
 * says which language the words are in (`window.lang`, the Frappe user
 * language), and the dates and numbers follow it. A code `Intl` does not know
 * falls back to the browser's, which is what every caller did before.
 */
export function appLocale(lang = globalThis.window?.lang) {
  if (!lang) return undefined
  // Frappe writes some codes the POSIX way («pt_BR»); Intl wants «pt-BR».
  const tag = String(lang).trim().replace(/_/g, '-')
  try {
    return Intl.DateTimeFormat.supportedLocalesOf([tag]).length
      ? tag
      : undefined
  } catch {
    // a malformed tag makes Intl throw rather than say no
    return undefined
  }
}

/**
 * A field's name inside a sentence: «Codice fiscale» reads «codice fiscale»
 * after «Aggiungi», while an acronym («IVA», «PEC»), an abbreviation («N.») or a
 * name with a capital inside («WhatsApp») stays as it is written. The same rule
 * as the server's `in_frase` (`crm_fields_layout.py`).
 */
export function inFrase(label) {
  const testo = String(label || '')
  const primo = testo.split(' ', 1)[0]
  const resto = primo.slice(1)
  const maiuscola = primo[0] !== primo[0]?.toLowerCase()
  if (
    primo.length > 1 &&
    maiuscola &&
    resto === resto.toLowerCase() &&
    !primo.endsWith('.')
  ) {
    return testo[0].toLowerCase() + testo.slice(1)
  }
  return testo
}
