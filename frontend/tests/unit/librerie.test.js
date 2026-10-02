import { describe, expect, it } from 'vitest'
import { FONTI, rigaValori } from '@/utils/librerie'

describe('a food of the library', () => {
  it('says its values in one line, without what is not known', () => {
    expect(
      rigaValori({ kcal: 36.5, protein_g: 0.63, carbs_g: null, fat_g: 0 }),
    ).toBe('36.5 kcal · P 0.63 · F 0')
    expect(rigaValori({})).toBe('')
  })

  it('comes from the library, CIQUAL, or a table a centre imported before', () => {
    expect(FONTI[0]).toBe('CIQUAL')
  })
})
