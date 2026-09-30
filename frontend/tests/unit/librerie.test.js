import { describe, expect, it } from 'vitest'
import {
  CAMPI_TABELLA,
  filtra,
  mappaDalServer,
  mappaPerIlServer,
  normalizza,
  rigaValori,
  sceltiAllInizio,
} from '@/utils/librerie'

const CIBI = [
  { key: '9811', code: '9811', name: 'Pâtes, cuites', category: 'pâtes' },
  { key: '20047', code: '20047', name: 'Carotte, crue', category: 'légumes' },
  { key: 'name:oeuf', code: null, name: 'Œuf entier', category: 'œufs' },
]

describe('the columns of a table', () => {
  it('come from the server as one index each, the group its first', () => {
    const scelta = mappaDalServer({ name: 3, group: [4, 1], kcal: 10 })
    expect(scelta.name).toBe('3')
    expect(scelta.group).toBe('4')
    expect(scelta.kcal).toBe('10')
    expect(scelta.fat_g).toBe('')
    expect(Object.keys(scelta)).toEqual(CAMPI_TABELLA.map((c) => c.key))
  })

  it('go back with the group’s other columns, unless it was changed', () => {
    const originale = { name: 3, group: [4, 1] }
    expect(
      mappaPerIlServer({ name: '3', group: '4', kcal: '' }, originale),
    ).toEqual({ name: 3, group: [4, 1] })
    expect(mappaPerIlServer({ name: '3', group: '7' }, originale)).toEqual({
      name: 3,
      group: [7],
    })
    expect(mappaPerIlServer({ name: 'x', kcal: '-1' })).toEqual({})
  })
})

describe('the foods of a table', () => {
  it('are found by their words without accents, and by their code', () => {
    expect(normalizza('Pâtes, Œuf')).toBe('pates oeuf')
    expect(filtra(CIBI, 'pates').map((c) => c.key)).toEqual(['9811'])
    expect(filtra(CIBI, 'oeuf').map((c) => c.key)).toEqual(['name:oeuf'])
    expect(filtra(CIBI, '20047').map((c) => c.key)).toEqual(['20047'])
    expect(filtra(CIBI, 'carotte crue').length).toBe(1)
    expect(filtra(CIBI, '', 'légumes').map((c) => c.key)).toEqual(['20047'])
    expect(filtra(CIBI).length).toBe(3)
  })

  it('are all chosen from an Italian table, none from one that fills gaps', () => {
    expect([...sceltiAllInizio(CIBI, 'BDA-IEO')]).toEqual([
      '9811',
      '20047',
      'name:oeuf',
    ])
    expect(sceltiAllInizio(CIBI, 'CIQUAL').size).toBe(0)
    expect(sceltiAllInizio(CIBI, 'USDA').size).toBe(0)
  })

  it('say their values in one line, without what is not known', () => {
    expect(
      rigaValori({ kcal: 36.5, protein_g: 0.63, carbs_g: null, fat_g: 0 }),
    ).toBe('36.5 kcal · P 0.63 · F 0')
    expect(rigaValori({})).toBe('')
  })
})
