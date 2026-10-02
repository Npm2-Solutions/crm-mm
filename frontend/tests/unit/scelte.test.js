// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import {
  conValoreAttuale,
  daLeggere,
  nomeDi,
  spiegazioneDi,
} from '@/utils/scelte'

// A select of invoicing offers its choices in words (crm/invoicing/scelte.py): the
// name, and a line on when it applies. The value stored before is never lost.

const NATURE = [
  { value: '', label: '', description: '' },
  {
    value: 'N4',
    label: 'Esente (art. 10)',
    description: 'Prestazioni sanitarie di diagnosi, cura e riabilitazione…',
  },
  { value: 'N2.2', label: 'Non soggetta', description: '' },
]

describe('a select in words', () => {
  it('says when the chosen value applies', () => {
    expect(spiegazioneDi(NATURE, 'N4')).toContain('Prestazioni sanitarie')
    expect(spiegazioneDi(NATURE, 'N2.2')).toBe('')
    expect(spiegazioneDi(NATURE, '')).toBe('')
    expect(spiegazioneDi('N1\nN4', 'N4')).toBe('')
  })

  it('keeps a value the profile no longer suggests', () => {
    const opzioni = conValoreAttuale(NATURE, 'N6.4')
    expect(opzioni.at(-1)).toEqual({ label: 'N6.4', value: 'N6.4' })
    expect(conValoreAttuale(NATURE, 'N4')).toBe(NATURE)
    expect(conValoreAttuale(NATURE, '')).toBe(NATURE)
  })

  it('names a stored code, or leaves it as it is', () => {
    const vocabolario = { natura: { N4: 'Esente (art. 10)' } }
    expect(nomeDi(vocabolario, 'natura', 'N4')).toBe('Esente (art. 10)')
    expect(nomeDi(vocabolario, 'natura', 'N9')).toBe('N9')
    expect(nomeDi(vocabolario, 'cassa', 'TC21')).toBe('TC21')
    expect(nomeDi(null, 'natura', 'N4')).toBe('N4')
    expect(nomeDi(vocabolario, 'natura', '')).toBe('')
  })

  it('reads a choice by its name where it cannot be changed', () => {
    const delega = {
      fieldtype: 'Select',
      options: [{ value: 'sconosciuta', label: 'Non ancora nota' }],
    }
    expect(daLeggere(delega, 'sconosciuta')).toBe('Non ancora nota')
    expect(daLeggere(delega, 'presente')).toBe('presente')
    expect(daLeggere({ fieldtype: 'Data' }, 'IT0123')).toBe('IT0123')
    expect(daLeggere({ fieldtype: 'Select', options: 'a\nb' }, 'a')).toBe('a')
  })
})
