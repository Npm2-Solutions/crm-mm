import { describe, expect, it } from 'vitest'
import {
  DECIDUA,
  MISTA,
  arcate,
  delDente,
  eDente,
  importo,
  mancante,
  perIlServer,
  sulDente,
  superfici,
  suSuperfici,
  totali,
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
  it('sums as the server does', () => {
    expect(importo(2, 80, 10)).toBe(144)
    expect(importo(1, 99.99, 33)).toBe(66.99)
    expect(
      totali([
        { qty: 1, rate: 100, discount: 10, status: 'Done' },
        { qty: 1, rate: 1200 },
        { qty: 1, rate: 70, status: 'Cancelled' },
      ]),
    ).toEqual({ gross: 1300, discount: 10, net: 1290, done: 90, left: 1200 })
  })

  it('writes a treatment on its tooth', () => {
    expect(sulDente({ tooth: '36', surfaces: 'MOD' })).toBe('36 MOD')
    expect(sulDente({ tooth: null })).toBe('')
  })

  it('goes to the server as it takes it', () => {
    expect(
      perIlServer({
        title: '  Piano 2026 ',
        items: [
          { service: 'Otturazione', tooth: ' 36 ', surfaces: 'MO', rate: '90' },
          { service: 'Igiene', surfaces: 'O', phase: 0, qty: 0, discount: '5' },
        ],
      }),
    ).toEqual({
      title: 'Piano 2026',
      price_list: null,
      valid_until: null,
      patient_notes: null,
      items: [
        {
          service: 'Otturazione',
          description: null,
          tooth: '36',
          surfaces: 'MO',
          phase: 1,
          qty: 1,
          rate: 90,
          discount: 0,
        },
        {
          service: 'Igiene',
          description: null,
          tooth: null,
          surfaces: null,
          phase: 1,
          qty: 1,
          rate: 0,
          discount: 5,
        },
      ],
    })
  })
})
