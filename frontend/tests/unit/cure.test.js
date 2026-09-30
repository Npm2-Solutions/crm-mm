import { describe, expect, it } from 'vitest'
import {
  DECIDUA,
  MISTA,
  arcate,
  delDente,
  eDente,
  mancante,
  sulDente,
  superfici,
  suSuperfici,
} from '@/utils/cure'

describe('the teeth', () => {
  it('reads the FDI notation', () => {
    for (const dente of [11, 18, 21, 28, 31, 38, 41, 48, 51, 55, 65, 85, '36'])
      expect(eDente(dente)).toBe(true)
    for (const dente of [10, 19, 56, 91, 9, '3a', null, ''])
      expect(eDente(dente)).toBe(false)
  })

  it('draws the arches as the dentist sees them', () => {
    const [sopra, sotto] = arcate()
    expect(sopra.slice(0, 3)).toEqual([18, 17, 16])
    expect(sopra.slice(7, 9)).toEqual([11, 21])
    expect(sotto.slice(7, 9)).toEqual([41, 31])
    expect(sopra.length + sotto.length).toBe(32)
    expect(arcate(DECIDUA)[0]).toEqual([55, 54, 53, 52, 51, 61, 62, 63, 64, 65])
    expect(arcate(MISTA).map((riga) => riga.length)).toEqual([16, 10, 10, 16])
  })

  it('puts the surfaces in their order', () => {
    expect(superfici('dom')).toBe('MOD')
    expect(superfici('b, p')).toBe('VL')
    expect(superfici('I')).toBe('O')
    expect(superfici('')).toBe('')
    expect(superfici('MX')).toBe(null)
    expect(suSuperfici('Caries')).toBe(true)
    expect(suSuperfici('Crown')).toBe(false)
  })

  it('knows what a tooth is now', () => {
    const righe = [
      { tooth: '36', condition: 'Caries', surfaces: 'O' },
      { tooth: '18', condition: 'Missing' },
    ]
    expect(delDente(righe, 36)).toHaveLength(1)
    expect(mancante(righe, '18')).toBe(true)
    expect(mancante(righe, '36')).toBe(false)
  })
})

describe('a care plan', () => {
  it('writes a row on its tooth', () => {
    expect(sulDente({ tooth: '36', surfaces: 'MOD' })).toBe('36 MOD')
    expect(sulDente({ tooth: null })).toBe('')
  })
})
