// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * The file the person attaches to a message to the centre (crm.area.messaggi):
 * a photo or a PDF, five megabytes at most - the same rules as the server's
 * (`messaggi_regole`), said before anything is sent. The server reads the
 * file's bytes; here the browser's type and size are enough to say it at once.
 * Pure, so it is tested.
 */

export const MAX_MB = 5
export const MAX_BYTE = MAX_MB * 1024 * 1024
// what the file picker offers: photos (an iPhone's HEIC too) and PDFs
export const ACCETTA =
  'image/png,image/jpeg,image/webp,image/heic,application/pdf'
const TIPI = ACCETTA.split(',')
const ESTENSIONI = /\.(png|jpe?g|webp|heic|pdf)$/i

/**
 * What is wrong with `file` ({ name, type, size }), as a sentence to translate,
 * or null.
 */
export function cosaNonVa(file) {
  if (!file) return null
  const tipo = (file.type || '').toLowerCase()
  if (!TIPI.includes(tipo) && !ESTENSIONI.test(file.name || '')) {
    return 'Only a photo or a PDF can be attached'
  }
  if (Number(file.size) > MAX_BYTE) return 'The file is larger than {0} MB'
  return null
}

/** How big a file is, as a person says it: «850 KB», «2,4 MB». */
export function quantoPesa(byte, locale = 'it-IT') {
  const n = Math.max(Number(byte) || 0, 0)
  if (n < 1024 * 1024) {
    return `${Math.max(Math.round(n / 1024), 1)} KB`
  }
  const mb = new Intl.NumberFormat(locale, { maximumFractionDigits: 1 })
  return `${mb.format(n / (1024 * 1024))} MB`
}
