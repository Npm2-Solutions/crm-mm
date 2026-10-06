// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * A select whose choices come in words (crm/invoicing/scelte.py hands them over
 * as `{ value, label, description }`): what the field says under it, and a value
 * stored before that the list no longer suggests.
 */

/**
 * The options, with the stored value among them. A profile hides choices, it
 * never loses one: a value saved before stays visible in its own field, by its
 * name where the server gave the family's names (`nomi`), else as it is.
 */
export function conValoreAttuale(options, valore, nomi = {}) {
  if (!valore || !Array.isArray(options)) return options
  if (options.some((opzione) => opzione?.value === valore)) return options
  return [...options, { label: nomi?.[valore] || valore, value: valore }]
}

/** The line that says when the chosen value applies, or nothing. */
export function spiegazioneDi(options, valore) {
  if (!valore || !Array.isArray(options)) return ''
  return options.find((opzione) => opzione?.value === valore)?.description || ''
}

/** The name of a stored code, from the vocabulary by family, or the code itself. */
export function nomeDi(vocabolario, famiglia, valore) {
  if (!valore) return ''
  return vocabolario?.[famiglia]?.[valore] || valore
}

/**
 * What a read-only field shows: a choice by its name («Non nota»), never its
 * code (`sconosciuta`); any other value as it is.
 */
export function daLeggere(field, valore) {
  if (field?.fieldtype !== 'Select' || !Array.isArray(field.options)) {
    return valore
  }
  const scelta = field.options.find((opzione) => opzione?.value === valore)
  return scelta?.label || valore
}
