// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/*
 * The emoji's names and keywords in Italian, for the picker and the editor's
 * ":" list (src/utils/emoji.js): Unicode's own, the CLDR annotations, kept
 * only for the emoji gemoji has, one line each, «name|keyword|keyword».
 *
 *   npm pack cldr-annotations-full@48.2.0 cldr-annotations-derived-full@48.2.0
 *   (unpack both, then, from frontend/)
 *   node scripts/emoji-italiane.mjs <annotations/it/annotations.json> <annotationsDerived/it/annotations.json>
 *
 * It writes src/assets/emoji/it.json; src/assets/emoji/it.LICENSE.txt says
 * where they come from and carries Unicode's notice. A new gemoji or a new CLDR:
 * run it again, and change the version in the notice.
 */
/* global process, console */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { gemoji } from 'gemoji'

const [base, derivate] = process.argv.slice(2)
if (!base || !derivate) {
  console.error(
    'node scripts/emoji-italiane.mjs <annotations/it/annotations.json> <annotationsDerived/it/annotations.json>',
  )
  process.exit(1)
}
const leggi = (file) => JSON.parse(fs.readFileSync(file, 'utf8'))
// the derived ones (flags, skin tones, keycaps, sequences) first: a base one wins
const annotazioni = {
  ...leggi(derivate).annotationsDerived.annotations,
  ...leggi(base).annotations.annotations,
}
// U+FE0F, the variation selector, is not part of the key: «❤️» is «❤»
const chiave = (emoji) => emoji.replace(/️/g, '')
const perChiave = {}
for (const [emoji, voce] of Object.entries(annotazioni))
  perChiave[chiave(emoji)] = voce

const parole = {}
const mancano = []
for (const { emoji, description } of gemoji) {
  const voce = perChiave[chiave(emoji)]
  if (!voce) {
    mancano.push(`${emoji} ${description}`)
    continue
  }
  const nome = (voce.tts || [])[0] || ''
  parole[chiave(emoji)] = [
    nome,
    ...(voce.default || []).filter((p) => p !== nome),
  ].join('|')
}

const qui = path.dirname(fileURLToPath(import.meta.url))
const destinazione = path.join(qui, '..', 'src', 'assets', 'emoji', 'it.json')
fs.writeFileSync(destinazione, JSON.stringify(parole) + '\n')
console.log(
  `${Object.keys(parole).length} emoji in Italian, ${mancano.length} without: ${mancano.join(', ')}`,
)
