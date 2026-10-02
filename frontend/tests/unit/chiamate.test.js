// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { describe, expect, it } from 'vitest'
import {
  PAESI_PROPOSTI,
  TASTI,
  bloccataInItalia,
  comeSalvati,
  conIlPaese,
  nomeDelPaese,
  numeroIniziale,
  paesi,
  paesiDaAggiungere,
  senzaIlPaese,
  siSceglie,
} from '@/utils/chiamate'

// Calls going out (doc 52): the page reads the countries as the server does
// (crm/telephony/uscita_regole.py) and starts each call from the right number.

const NUMERI = [
  { number: '+390212345678', own: true },
  { number: '+390687654321', own: false },
]

describe('the countries that can be called', () => {
  it('as stored, as the server reads them', () => {
    expect(paesi('it, ch')).toEqual(['CH', 'IT'])
    expect(paesi('["IT", "FR"]')).toEqual(['FR', 'IT'])
    expect(paesi('IT\nSM;VA')).toEqual(['IT', 'SM', 'VA'])
    expect(paesi('Italia, 39')).toEqual(['IT'])
  })

  it('Italy when nothing is left', () => {
    expect(paesi('')).toEqual(['IT'])
    expect(paesi(null)).toEqual(['IT'])
    expect(paesi([])).toEqual(['IT'])
  })

  it('kept as the settings keep them', () => {
    expect(comeSalvati(['ch', 'IT', 'IT'])).toBe('CH, IT')
  })

  it('by their name in the reader’s language', () => {
    expect(nomeDelPaese('CH', 'it')).toBe('Svizzera')
    expect(nomeDelPaese('GB', 'en')).toBe('United Kingdom')
  })

  it('Italy among those offered to add', () => {
    expect(PAESI_PROPOSTI).toContain('IT')
    expect(new Set(PAESI_PROPOSTI).size).toBe(PAESI_PROPOSTI.length)
  })

  it('one added, one taken away, never none', () => {
    expect(conIlPaese('IT', 'ch')).toEqual(['CH', 'IT'])
    expect(conIlPaese('IT, CH', 'CH')).toEqual(['CH', 'IT'])
    expect(senzaIlPaese('IT, CH', 'IT')).toEqual(['CH'])
    expect(senzaIlPaese('IT', 'IT')).toEqual(['IT'])
  })

  it('the ones to add, without those chosen, by name', () => {
    const opzioni = paesiDaAggiungere('IT, CH', 'it')
    const codici = opzioni.map((o) => o.value)
    expect(codici).not.toContain('IT')
    expect(codici).not.toContain('CH')
    expect(opzioni.find((o) => o.value === 'DE').label).toBe('Germania')
    const nomi = opzioni.map((o) => o.label)
    expect(nomi).toEqual([...nomi].sort((a, b) => a.localeCompare(b, 'it')))
  })
})

describe('the number a call shows', () => {
  it('the one used last, while it is still the centre’s', () => {
    expect(numeroIniziale(NUMERI, '+390687654321')).toBe('+390687654321')
  })

  it('else one’s own line, else the first', () => {
    expect(numeroIniziale(NUMERI, '+390299999999')).toBe('+390212345678')
    expect(numeroIniziale([{ number: '+390687654321' }])).toBe('+390687654321')
    expect(numeroIniziale([])).toBe('')
  })

  it('is asked only when there is a choice', () => {
    expect(siSceglie(NUMERI)).toBe(true)
    expect(siSceglie(NUMERI.slice(0, 1))).toBe(false)
  })

  it('an Italian mobile shown on a call to Italy is blocked', () => {
    const numeri = [...NUMERI, { number: '+393331234567', mobile: true }]
    expect(bloccataInItalia(numeri, '+393331234567', 'IT')).toBe(true)
    expect(bloccataInItalia(numeri, '+393331234567', 'CH')).toBe(false)
    expect(bloccataInItalia(numeri, '+390212345678', 'IT')).toBe(false)
    expect(bloccataInItalia(numeri, '', 'IT')).toBe(false)
  })
})

describe('the keypad', () => {
  it('twelve keys, as on a phone', () => {
    expect(TASTI.flat()).toEqual([
      '1',
      '2',
      '3',
      '4',
      '5',
      '6',
      '7',
      '8',
      '9',
      '*',
      '0',
      '#',
    ])
  })
})
