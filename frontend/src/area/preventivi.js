// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * A quote in the area (crm.preventivi.area, crm.preventivi.firma): what its card
 * offers. The server says whether it is still to answer and whether the session
 * answers quotes (a parent does, whoever only follows does not; the centre's
 * preview never); the card only draws. Pure, so it is tested.
 */

/**
 * What the card offers for `preventivo`, in a list that says `rispondono`
 * (the session answers quotes) and `verificato` (a code read in the last
 * minutes): `risponde` - «Accept and sign» and «I do not accept» -, `pdf` - its
 * PDF, or the signed copy once signed -, and whether a code comes first for
 * signing (`codicePerFirmare`) or for the PDF (`codicePerIlPdf`: health data,
 * as a report).
 */
export function cosaOffre(
  preventivo,
  { rispondono = false, verificato = false, anteprima = false } = {},
) {
  if (!preventivo || preventivo.hidden) {
    return {
      risponde: false,
      pdf: false,
      codicePerFirmare: false,
      codicePerIlPdf: false,
    }
  }
  const risponde = Boolean(rispondono && !anteprima && preventivo.can_answer)
  const pdf = Boolean(preventivo.has_pdf && !anteprima)
  return {
    risponde,
    pdf,
    codicePerFirmare: risponde && !verificato,
    codicePerIlPdf: pdf && Boolean(preventivo.clinical) && !verificato,
  }
}

/** The address of the quote's PDF, for the person whose area it is. */
export function indirizzoDelPdf(persona, preventivo) {
  const parametri = new URLSearchParams({ person: persona, quote: preventivo })
  return `/api/method/crm.preventivi.firma.area_quote_pdf?${parametri}`
}
