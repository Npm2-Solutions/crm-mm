// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * The emoji in the reader's words. gemoji and the editor's list know them by
 * English words only: «smile» found 😄, «sorriso» found nothing. Their Italian
 * names and keywords are Unicode's (CLDR, src/assets/emoji/it.json, made by
 * scripts/emoji-italiane.mjs): «sorriso», «grazie», «cuore» find them, and the
 * English words still do.
 */

/** An emoji's key: without U+FE0F, the variation selector («❤️» is «❤»). */
export function chiave(emoji) {
  return String(emoji || '').replace(/️/g, '')
}

/**
 * Words as they are compared: lower case, without accents and with one kind of
 * apostrophe, since a phone types «felicita» or «d'accordo» as often as
 * «felicità» or «d’accordo».
 */
export function semplice(testo) {
  return String(testo || '')
    .normalize('NFD')
    .replace(/\p{M}/gu, '')
    .replace(/[’‘`´]/g, "'")
    .toLowerCase()
}

/** An emoji's Italian name and keywords, from the dictionary («name|word|word»). */
export function paroleDi(dizionario, emoji) {
  const riga = dizionario?.[chiave(emoji)]
  if (!riga) return { nome: '', parole: [] }
  const [nome, ...parole] = riga.split('|')
  return { nome, parole }
}

/** Every word that finds an emoji, its own (English) and the dictionary's, as compared. */
export function testoDiRicerca(proprie, dizionario, emoji) {
  const { nome, parole } = paroleDi(dizionario, emoji)
  return semplice([...(proprie || []), nome, ...parole].join(' | '))
}

/** Whether what was typed is among an emoji's words (made by `testoDiRicerca`). */
export function trova(testo, cercato) {
  const ago = semplice(cercato).trim()
  return !ago || String(testo || '').includes(ago)
}

/**
 * The emoji whose words hold what was typed, the closest first: the one named
 * so; one whose name starts with that word («cuore rosso» for «cuore»), then
 * one whose name has it («faccina con un gran sorriso» for «sorriso»); one with
 * exactly that keyword; then the ones where a word starts so; then the rest.
 * Among equals the list's own order, the common ones first: a name's length
 * said nothing in Italian (the cats came before 😀).
 */
export function cercaLeEmoji(voci, cercato) {
  const ago = semplice(cercato).trim()
  if (!ago) return [...(voci || [])]
  const trovate = []
  for (const voce of voci || []) {
    if (String(voce.cerca || '').includes(ago))
      trovate.push({ voce, vicinanza: vicinanza(voce, ago) })
  }
  // a stable sort: among equals the list's order stays
  return trovate
    .sort((a, b) => a.vicinanza - b.vicinanza)
    .map(({ voce }) => voce)
}

const PEZZI = /[\s'_]+/

function vicinanza(voce, ago) {
  const nome = semplice(voce.name)
  if (nome === ago) return 0
  if (nome.startsWith(`${ago} `)) return 1
  const pezziDelNome = nome.split(PEZZI)
  if (pezziDelNome.includes(ago)) return 2
  const parole = String(voce.cerca || '').split(' | ')
  if (parole.includes(ago)) return 3
  if (
    pezziDelNome.some((pezzo) => pezzo.startsWith(ago)) ||
    parole.some((parola) =>
      parola.split(PEZZI).some((pezzo) => pezzo.startsWith(ago)),
    )
  )
    return 4
  return 5
}

/**
 * The Italian words, fetched the first time a picker or the editor's list needs
 * them, and only for a reader in Italian: nobody else downloads them.
 */
let dizionario = null
export function caricaLeParole(lingua = globalThis.window?.lang) {
  if (
    !String(lingua || '')
      .toLowerCase()
      .startsWith('it')
  )
    return Promise.resolve({})
  dizionario ||= import('@/assets/emoji/it.json').then(
    (modulo) => modulo.default,
  )
  return dizionario
}
