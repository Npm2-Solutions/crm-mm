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
