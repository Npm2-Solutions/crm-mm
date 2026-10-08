// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// The clinical record on the person's page, the pure part.

/**
 * The last signed visit on a sheet among the records the reader reads (newest
 * first, as the server sends them): what «Start from the last visit» copies.
 * An addendum is not a visit.
 */
export function ultimaVisitaSu(records, template) {
  return (
    (records || []).find(
      (r) => r.template === template && r.docstatus === 1 && !r.addendum_to,
    ) || null
  )
}

/**
 * The sheets offered for a new visit: each sheet, and after it the same sheet
 * started from its last visit where there is one the reader reads.
 */
export function vociDelleSchede(sheets, records, t = (s) => s) {
  const voci = []
  for (const sheet of sheets || []) {
    voci.push({ sheet, fromLast: false, label: sheet.title })
    if (ultimaVisitaSu(records, sheet.name))
      voci.push({
        sheet,
        fromLast: true,
        label: t('{0}: start from the last visit', [sheet.title]),
      })
  }
  return voci
}
