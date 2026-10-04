// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// The words a pure helper hands to the translator it is given (`t('1 month')`,
// `__` in the app) are not seen by the catalog's extraction, which looks for
// `__()`: forty of them read in English on Italian screens - «1 month · any
// number of entries» under a new subscription type. Each one is in it.po.
import fs from 'node:fs'
import path from 'node:path'

const UTILS = path.resolve(import.meta.dirname, '../../src/utils')
const CATALOGO = path.resolve(import.meta.dirname, '../../../crm/locale/it.po')

function msgid() {
  const testo = fs.readFileSync(CATALOGO, 'utf8')
  return new Set(
    [...testo.matchAll(/^msgid "(.*)"$/gm)].map((m) =>
      m[1].replace(/\\"/g, '"').replace(/\\\\/g, '\\'),
    ),
  )
}

function paroleDate(file) {
  const testo = fs.readFileSync(path.join(UTILS, file), 'utf8')
  return [...testo.matchAll(/(?<![\w.$])t\(\s*'((?:[^'\\]|\\.)+)'/g)]
    .map((m) => m[1].replace(/\\'/g, "'"))
    .filter((parola) => /[a-z]/i.test(parola))
}

describe('the words the helpers hand to the translator', () => {
  it('are all in the Italian catalog', () => {
    const catalogo = msgid()
    const mancanti = []
    for (const file of fs.readdirSync(UTILS).filter((f) => f.endsWith('.js'))) {
      for (const parola of paroleDate(file)) {
        if (!catalogo.has(parola)) mancanti.push(`${file}: ${parola}`)
      }
    }
    expect(mancanti).toEqual([])
  })
})
