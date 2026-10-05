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
 *
 * DottorCloud is European: English is written the way Europe writes it - the
 * day before the month, the 24-hour clock, the week from Monday - which is
 * «en-GB», not the United States' «en».
 */
export function appLocale(lang = globalThis.window?.lang) {
  if (!lang) return undefined
  // Frappe writes some codes the POSIX way («pt_BR»); Intl wants «pt-BR».
  let tag = String(lang).trim().replace(/_/g, '-')
  if (/^en(-US)?$/i.test(tag)) tag = 'en-GB'
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

// In Italian an article, or a preposition with its article, drops its vowel
// before a number read with one: «l'1 ottobre», «dall'8 marzo», «all'11
// settembre». A sentence that puts a date after «il {0}» or «dal {0}» read «dal
// 11 set»: the date is known only once the sentence is filled, so it is put
// right here, for every sentence, and only before a day of a date: written
// 11/10, 11-10 or 11.10 as the site's format may write it, with its zero too
// («dall'08/10/2026»: Italy's format writes it).
const ELISIONI = {
  il: "l'",
  dal: "dall'",
  al: "all'",
  del: "dell'",
  nel: "nell'",
  sul: "sull'",
}
const MESI = 'gen|feb|mar|apr|mag|giu|lug|ago|set|ott|nov|dic'
const DAVANTI_A_UNA_DATA = new RegExp(
  `(^|[^\\p{L}'])(il|dal|al|del|nel|sul) (0?1|0?8|11)(?= (?:${MESI})|[/.-]\\d)`,
  'giu',
)

export function conLApostrofo(testo, lingua = globalThis.window?.lang) {
  if (typeof testo !== 'string') return testo
  if (
    !String(lingua || '')
      .toLowerCase()
      .startsWith('it')
  )
    return testo
  return testo.replace(DAVANTI_A_UNA_DATA, (_, prima, articolo, giorno) => {
    const eliso = ELISIONI[articolo.toLowerCase()]
    const maiuscolo = articolo[0] !== articolo[0].toLowerCase()
    return (
      prima +
      (maiuscolo ? eliso[0].toUpperCase() + eliso.slice(1) : eliso) +
      giorno
    )
  })
}
