import { describe, expect, it } from 'vitest'
import { importo, perIlServer, totali } from '@/utils/preventivi'

describe('a quote', () => {
  it('sums as the server does', () => {
    expect(importo(2, 80, 10)).toBe(144)
    expect(importo(1, 99.99, 33)).toBe(66.99)
    expect(importo(1, 100, 150)).toBe(0)
    expect(
      totali([
        { qty: 1, rate: 100, discount: 10, status: 'Done' },
        { qty: 6, rate: 200 },
        { qty: 1, rate: 70, status: 'Cancelled' },
      ]),
    ).toEqual({ gross: 1300, discount: 10, net: 1290, done: 90, left: 1200 })
  })

  it('goes to the server as it takes it', () => {
    expect(
      perIlServer({
        title: '  Trattamenti di ottobre ',
        items: [
          { service: 'Pulizia viso', rate: '60' },
          { service: 'Laser', phase: 0, qty: 0, discount: '10' },
        ],
      }),
    ).toEqual({
      title: 'Trattamenti di ottobre',
      price_list: null,
      valid_until: null,
      patient_notes: null,
      items: [
        {
          service: 'Pulizia viso',
          description: null,
          phase: 1,
          qty: 1,
          rate: 60,
          discount: 0,
        },
        {
          service: 'Laser',
          description: null,
          phase: 1,
          qty: 1,
          rate: 0,
          discount: 10,
        },
      ],
    })
  })

  it("takes a module's fields on its rows along", () => {
    const [voce, altra] = perIlServer(
      {
        items: [
          { service: 'Otturazione', tooth: ' 36 ', surfaces: 'MO' },
          { service: 'Igiene', tooth: '', surfaces: undefined },
        ],
      },
      ['tooth', 'surfaces'],
    ).items
    expect([voce.tooth, voce.surfaces]).toEqual(['36', 'MO'])
    expect([altra.tooth, altra.surfaces]).toEqual([null, null])
  })
})
