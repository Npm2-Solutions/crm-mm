// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { describe, expect, it } from 'vitest'
import {
  nomeDellaValuta,
  prezzo,
  simboloDellaValuta,
  valuteDaScegliere,
} from '@/utils/valute'

describe('a currency’s name', () => {
  it('names it in the reader’s language, with a capital as a choice', () => {
    expect(nomeDellaValuta('EUR', 'it')).toBe('Euro')
    expect(nomeDellaValuta('CHF', 'it')).toBe('Franco svizzero')
    expect(nomeDellaValuta('GBP', 'en-GB')).toBe('British Pound')
  })

  it('keeps a code nobody names, and says nothing of none', () => {
    expect(nomeDellaValuta('XYZ', 'it')).toBe('XYZ')
    expect(nomeDellaValuta('', 'it')).toBe('')
    expect(nomeDellaValuta(undefined, 'it')).toBe('')
  })
})

describe('the currencies to choose from', () => {
  it('lists them by name, never by code, in the reader’s order', () => {
    const scelte = valuteDaScegliere({
      codici: ['USD', 'EUR', 'CHF', 'EUR'],
      lingua: 'it',
    })
    expect(scelte).toEqual([
      { label: 'Dollaro statunitense', value: 'USD' },
      { label: 'Euro', value: 'EUR' },
      { label: 'Franco svizzero', value: 'CHF' },
    ])
  })

  it('keeps the stored one the site no longer offers', () => {
    const valori = valuteDaScegliere({
      codici: ['EUR'],
      scelta: 'SEK',
      lingua: 'it',
    }).map((scelta) => scelta.value)
    // «Corona svedese» before «Euro»
    expect(valori).toEqual(['SEK', 'EUR'])
  })
})

describe('a price', () => {
  it('is written as the reader writes it, never «65 EUR»', () => {
    expect(prezzo(65, 'EUR', 'it')).toBe('65,00 €')
    expect(prezzo('12.5', 'EUR', 'en-GB')).toBe('€12.50')
  })

  it('counts in euros where the currency is not said', () => {
    expect(prezzo(10, '', 'it')).toBe('10,00 €')
  })

  it('falls back to the amount and the code on a currency Intl refuses', () => {
    expect(prezzo(10, 'euro', 'it')).toBe('10 euro')
  })
})

describe('a currency’s sign', () => {
  it('stands beside an amount one types, its code where it has none', () => {
    expect(simboloDellaValuta('USD', 'it')).toBe('$')
    expect(simboloDellaValuta('EUR', 'it')).toBe('€')
    expect(simboloDellaValuta('CHF', 'it')).toBe('CHF')
    expect(simboloDellaValuta('euro', 'it')).toBe('euro')
    expect(simboloDellaValuta('', 'it')).toBe('')
  })
})
