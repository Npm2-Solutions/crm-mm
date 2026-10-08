import { describe, expect, test } from 'vitest'
import {
  DIRETTA,
  INDIRETTA,
  daFatturare,
  meseAccanto,
  nomeDellaForma,
  prezzo,
  problemaDellaConvenzione,
  quote,
  rigaDellaConvenzione,
  rigaDellaCopertura,
  statoInParole,
} from '@/utils/convenzioni'

const t = (s, args = []) => s.replace(/\{(\d)\}/g, (_, i) => args[i])

const FONDO = {
  convention_name: 'Salute+',
  kind: 'Insurance',
  direct: 1,
  indirect: 1,
  organization: 'Salute+ S.p.A.',
  price_mode: 'Price list',
  price_list: 'Salute+',
  price_list_name: 'Salute+',
  share_mode: 'Percentage',
  share_percent: 20,
  shares: [{ service: 'Osteopatia', patient_share: 15 }],
}

describe('the price and the shares, as the server makes them', () => {
  test('the price list, a discount half up, the centre', () => {
    expect(prezzo(FONDO, 70, 42)).toBe(42)
    expect(prezzo(FONDO, 70, null)).toBe(70)
    expect(prezzo({ price_mode: 'Discount', discount_percent: 15 }, 33.3)).toBe(
      28.31,
    )
    expect(prezzo({}, 55)).toBe(55)
  })

  test('direct and indirect', () => {
    expect(quote(FONDO, INDIRETTA, 42)).toEqual([42, 0])
    expect(quote(FONDO, DIRETTA, 42.25)).toEqual([8.45, 33.8])
    expect(
      quote({ share_mode: 'Percentage', share_percent: 10 }, DIRETTA, 0.25),
    ).toEqual([0.03, 0.22])
    expect(quote(FONDO, DIRETTA, 60, 'Osteopatia')).toEqual([15, 45])
    const franchigia = { share_mode: 'Fixed', share_amount: 50 }
    expect(quote(franchigia, DIRETTA, 40)).toEqual([40, 0])
    expect(quote(franchigia, DIRETTA, 80)).toEqual([50, 30])
    expect(quote({}, DIRETTA, 80)).toEqual([0, 80])
  })
})

describe('the convention', () => {
  test('what stops it', () => {
    expect(problemaDellaConvenzione(FONDO, t)).toBe('')
    expect(problemaDellaConvenzione({ ...FONDO, organization: '' }, t)).toBe(
      'In direct form the fund is billed: choose the company that pays',
    )
    expect(
      problemaDellaConvenzione({ ...FONDO, direct: 0, indirect: 0 }, t),
    ).toBe('Choose the direct form, the indirect form or both')
    expect(
      problemaDellaConvenzione(
        { ...FONDO, price_mode: 'Discount', discount_percent: 120 },
        t,
      ),
    ).toBe('The discount is a percentage between 0 and 100')
    expect(
      problemaDellaConvenzione(
        { ...FONDO, valid_from: '2026-02-01', valid_upto: '2026-01-01' },
        t,
      ),
    ).toBe('It ends before it starts')
  })

  test('in one line', () => {
    expect(rigaDellaConvenzione(FONDO, t, (n) => `${n} €`)).toBe(
      'Insurance · Direct and indirect form · prices of Salute+ · the person pays 20%',
    )
    expect(
      rigaDellaConvenzione(
        {
          kind: 'Company',
          indirect: 1,
          price_mode: 'Discount',
          discount_percent: 10,
        },
        t,
        (n) => n,
      ),
    ).toBe('Company convention · Indirect form · 10% off')
    expect(
      rigaDellaConvenzione(
        { kind: 'Health fund', direct: 1, share_mode: 'None' },
        t,
        (n) => n,
      ),
    ).toBe('Health fund · Direct form · the fund pays it all')
  })
})

describe('the words', () => {
  test('a form, a state', () => {
    expect(nomeDellaForma(DIRETTA, t)).toBe('Direct form')
    expect(nomeDellaForma('', t)).toBe('')
    expect(statoInParole('To authorise', t)).toEqual({
      label: 'To authorise',
      theme: 'orange',
    })
    expect(statoInParole('Paid', t).label).toBe('Paid by the fund')
  })

  test('a cover', () => {
    expect(
      rigaDellaCopertura(
        { card_number: 'SP1', holder_name: 'Mario', valid_upto: '2027-01-31' },
        t,
        (g) => `il ${g}`,
      ),
    ).toBe('Card SP1 · holder Mario · until il 2027-01-31')
    expect(rigaDellaCopertura({}, t, (g) => g)).toBe('')
  })

  test('the months beside', () => {
    expect(meseAccanto('2026-01', -1)).toBe('2025-12')
    expect(meseAccanto('2026-12', 1)).toBe('2027-01')
  })

  test('what is to bill', () => {
    expect(
      daFatturare([
        { state: 'Done', fund_share: 30 },
        { state: 'Done', fund_share: 0 },
        { state: 'Billed', fund_share: 30 },
      ]),
    ).toHaveLength(1)
  })
})
