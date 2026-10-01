// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// The client area speaks to its people from its own dictionary (src/area/it.js),
// whatever language the staff use: a sentence missing there reaches a patient in
// English. Every sentence the area hands to __() has to be in it.
import fs from 'node:fs'
import path from 'node:path'
import parole from '@/area/it'

const AREA = path.resolve(import.meta.dirname, '../../src/area')

function sorgenti(cartella) {
  return fs.readdirSync(cartella, { withFileTypes: true }).flatMap((voce) => {
    const percorso = path.join(cartella, voce.name)
    if (voce.isDirectory()) return sorgenti(percorso)
    return /\.(vue|js)$/.test(voce.name) && voce.name !== 'it.js'
      ? [percorso]
      : []
  })
}

// __('…'), __("…") and __(`…`): the sentences, not a variable or a template
// with ${} in it.
const CHIAMATA = /\b__\(\s*(['"`])((?:\\.|(?!\1)[^\\])*)\1/g

function frasi(testo) {
  return [...testo.matchAll(CHIAMATA)]
    .map(([, , frase]) => frase)
    .filter((frase) => !frase.includes('${'))
    .map((frase) => frase.replace(/\\(['"`\\])/g, '$1'))
}

describe("the client area's dictionary", () => {
  it('reads the sentences out of the calls', () => {
    expect(frasi(`__('Your area') + __("It's here", [1]) + __(x)`)).toEqual([
      'Your area',
      "It's here",
    ])
    expect(frasi("__('Don\\'t') __(`Hi ${name}`)")).toEqual(["Don't"])
  })

  it('has every sentence the area says', () => {
    const mancano = sorgenti(AREA).flatMap((file) =>
      frasi(fs.readFileSync(file, 'utf8'))
        .filter((frase) => !(frase in parole))
        .map((frase) => `${path.relative(AREA, file)}: ${frase}`),
    )
    expect(mancano).toEqual([])
  })
})
