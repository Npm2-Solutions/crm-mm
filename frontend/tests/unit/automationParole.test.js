// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// The automation builder's catalogue is constants translated where they are
// drawn (`__(definition.label)`): the catalogue's extraction never sees them, so
// their Italian is written by hand. A word missing there reads in English on
// the canvas ("Send Email", "Wait").
import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  GOAL_EVENTS,
  MERGE_FIELDS,
  PALETTE,
  STEP_CATALOG,
  STEP_CATEGORIES,
  TRIGGER_CATALOG,
  TRIGGER_CATEGORIES,
  WAIT_MODES,
} from '@/utils/automation'

// the framework's own catalogue translates these, and it reaches the browser too
const DEL_FRAMEWORK = new Set(['Goal', 'Webhook'])

function msgid() {
  const testo = fs.readFileSync(
    path.resolve(import.meta.dirname, '../../../crm/locale/it.po'),
    'utf8',
  )
  return new Set(
    [...testo.matchAll(/^msgid "(.*)"$/gm)].map((m) =>
      m[1].replace(/\\"/g, '"').replace(/\\\\/g, '\\'),
    ),
  )
}

function parole() {
  const tutte = []
  for (const voce of Object.values(STEP_CATALOG))
    tutte.push(voce.label, voce.description)
  for (const voce of PALETTE) tutte.push(voce.label, voce.description)
  for (const voce of [...STEP_CATEGORIES, ...TRIGGER_CATEGORIES])
    tutte.push(voce.label)
  for (const [evento, voce] of Object.entries(TRIGGER_CATALOG))
    tutte.push(evento, voce.hint)
  for (const voce of [...GOAL_EVENTS, ...WAIT_MODES, ...MERGE_FIELDS])
    tutte.push(voce.label)
  return [...new Set(tutte.filter(Boolean))]
}

describe("the automation catalogue's words", () => {
  it('are all in the Italian catalogue', () => {
    const catalogo = msgid()
    const mancano = parole().filter(
      (frase) => !catalogo.has(frase) && !DEL_FRAMEWORK.has(frase),
    )
    expect(mancano).toEqual([])
  })

  it('leave the product name to the translation, never fill it early', () => {
    // filled when the module loads, the sentence no longer matched its msgid
    // and read in English
    const conIlNome = parole().filter((frase) => frase.includes('{brand}'))
    expect(conIlNome.length).toBeGreaterThan(0)
    expect(parole().some((frase) => /DottorCloud/.test(frase))).toBe(false)
  })

  it('never name another product', () => {
    expect(parole().filter((frase) => /\bGHL\b|HighLevel/.test(frase))).toEqual(
      [],
    )
  })
})
