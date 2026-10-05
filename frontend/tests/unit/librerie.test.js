import { describe, expect, it } from 'vitest'
import { FONTI, numeroDelCibo, rigaValori } from '@/utils/librerie'

describe('a food of the library', () => {
  it('says its values in one line, in words, without what is not known', () => {
    expect(
      rigaValori(
        { kcal: 36.5, protein_g: 0.63, carbs_g: null, fat_g: 0 },
        undefined,
        'en',
      ),
    ).toBe('36.5 kcal · proteins 0.6 g · fats 0 g')
    expect(rigaValori({})).toBe('')
  })

  it('writes its numbers as the reader does, to one decimal', () => {
    expect(numeroDelCibo(27.1, 'it')).toBe('27,1')
    expect(numeroDelCibo(0.083, 'it')).toBe('0,1')
    expect(numeroDelCibo(393, 'it')).toBe('393')
    expect(rigaValori({ fibre_g: 0.083 }, undefined, 'it')).toBe('fibre 0,1 g')
  })

  it('comes from the library, CIQUAL, or a table a centre imported before', () => {
    expect(FONTI[0]).toBe('CIQUAL')
  })
})
