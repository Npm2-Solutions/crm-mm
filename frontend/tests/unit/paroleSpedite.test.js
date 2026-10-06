// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { describe, expect, it } from 'vitest'
import { daSalvare, inParole } from '@/utils/paroleSpedite'

const PAROLE = { Sales: 'Vendite', Qualification: 'Qualificazione' }
const t = (testo) => PAROLE[testo] || testo

describe('a shipped word in a field one edits', () => {
  it('reads in the reader’s words', () => {
    expect(inParole('Sales', t)).toBe('Vendite')
    expect(inParole('Visita fissata', t)).toBe('Visita fissata')
    expect(inParole('', t)).toBe('')
    expect(inParole(null, t)).toBe('')
  })

  it('is saved as it was stored while nobody changes it', () => {
    // the stage keeps its name, the deals keep their link to it
    expect(daSalvare('Qualificazione', 'Qualification', t)).toBe(
      'Qualification',
    )
  })

  it('saves what one writes', () => {
    expect(daSalvare('Primo contatto', 'Qualification', t)).toBe(
      'Primo contatto',
    )
    // a new stage has nothing stored
    expect(daSalvare('Visita fissata', '', t)).toBe('Visita fissata')
  })
})
