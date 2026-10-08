import { describe, expect, it } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'
import {
  acconto,
  fraseDelleRate,
  importo,
  perIlServer,
  pianoDelleRate,
  problemiDelleRate,
  quote,
  totali,
} from '@/utils/preventivi'

// the cases the server proves too: crm/preventivi/tests/test_rate_regole.py
const CASI = JSON.parse(
  fs.readFileSync(
    path.resolve(
      import.meta.dirname,
      '../../../crm/preventivi/tests/casi_rate.json',
    ),
    'utf8',
  ),
)

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
      payment: 'Single payment',
      deposit_type: 'Amount',
      deposit_value: 0,
      instalments_count: 0,
      every_months: 1,
      first_due_on: null,
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

describe('a quote paid in instalments, on the cases shared with the server', () => {
  it('the deposit', () => {
    for (const caso of CASI.acconto)
      expect(acconto(caso.totale, caso.tipo, caso.valore)).toBe(caso.atteso)
  })

  it('the instalments to the cent', () => {
    for (const caso of CASI.quote) {
      const fatto = quote(caso.resto, caso.numero)
      expect(fatto).toHaveLength(caso.numero)
      if (caso.atteso) expect(fatto).toEqual(caso.atteso)
      else {
        expect(fatto[0]).toBe(caso.atteso_prima)
        expect(fatto.at(-1)).toBe(caso.atteso_ultima)
      }
    }
  })

  it('the schedule', () => {
    for (const caso of CASI.piano)
      expect(
        pianoDelleRate(
          caso.totale,
          caso.acconto,
          caso.numero,
          caso.ogni,
          caso.primo,
        ),
      ).toEqual(caso.atteso)
  })

  it('what is wrong', () => {
    for (const caso of CASI.problemi)
      expect(
        problemiDelleRate(
          caso.totale,
          caso.tipo,
          caso.valore,
          caso.numero,
          caso.ogni,
          caso.primo,
          caso.oggi || null,
        ),
      ).toEqual(caso.atteso)
  })
})

describe('how the instalments go, in one line', () => {
  const t = (s, a = []) => s.replace(/\{(\d)\}/g, (_, i) => a[i])
  const giorno = (d) => `il ${d}`
  const soldi = (n) => `${n.toFixed(2)} €`

  it('the paid ones and the next', () => {
    expect(
      fraseDelleRate(
        {
          count: 10,
          paid: 3,
          next: { kind: 'Instalment', due_on: '2026-11-01', amount: 250 },
          late: 0,
        },
        t,
        giorno,
        soldi,
      ),
    ).toEqual({
      testo: 'Instalments: 3 of 10 paid · next il 2026-11-01, 250.00 €',
      ritardo: false,
    })
  })

  it('the deposit first, and the late ones', () => {
    expect(
      fraseDelleRate(
        {
          count: 4,
          paid: 0,
          next: { kind: 'Deposit', due_on: null, amount: 400 },
          late: 2,
          late_amount: 720,
        },
        t,
        giorno,
        soldi,
      ),
    ).toEqual({
      testo:
        'Instalments: 0 of 4 paid · next the deposit, 400.00 € · 2 late, 720.00 €',
      ritardo: true,
    })
  })

  it('all paid, or nothing to say', () => {
    expect(
      fraseDelleRate({ count: 3, paid: 3, next: null }, t, giorno, soldi).testo,
    ).toBe('Instalments: all 3 paid')
    expect(fraseDelleRate(null, t, giorno, soldi)).toBeNull()
  })
})
