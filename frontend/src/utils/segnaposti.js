// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * A WhatsApp template's places to fill, «{{1}}», «{{2}}»…, as somebody reads
 * them: never the code. The template picker showed them raw in every card and
 * in the message to fill in, with fields called «Value for {{1}}». Now each
 * place is a chip with its number, and the message to fill in shows in it what
 * was typed for it.
 */

const SEGNAPOSTO = /\{\{\s*(\d+)\s*\}\}/g

/** The text cut into words and places: `{ testo }` and `{ posto: 1 }`. */
export function pezzi(testo) {
  const tutto = String(testo ?? '')
  const out = []
  let dopo = 0
  for (const trovato of tutto.matchAll(SEGNAPOSTO)) {
    if (trovato.index > dopo)
      out.push({ testo: tutto.slice(dopo, trovato.index) })
    out.push({ posto: Number(trovato[1]) })
    dopo = trovato.index + trovato[0].length
  }
  if (dopo < tutto.length) out.push({ testo: tutto.slice(dopo) })
  return out
}

/** A template's HTML with each place drawn as a chip of the given classes. */
export function segnaInHtml(html, classi) {
  return String(html ?? '').replace(
    SEGNAPOSTO,
    (_, numero) => `<span class="${classi}">${Number(numero)}</span>`,
  )
}
