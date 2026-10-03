// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { describe, expect, it } from 'vitest'
import {
  cifreDelCodice,
  internoPulito,
  internoValido,
  numeroItaliano,
  statoDellaVerifica,
} from '@/utils/verificati'
import { incertaInItalia } from '@/utils/chiamate'

describe('a number of the centre, verified', () => {
  it('tells an Italian number and its kind, written as people write it', () => {
    expect(numeroItaliano('+39 02 1234 5678')).toBe('fisso')
    expect(numeroItaliano('0039 06 12345678')).toBe('fisso')
    expect(numeroItaliano('02-1234-5678')).toBe('fisso')
    expect(numeroItaliano('+39 333 123 4567')).toBe('mobile')
    expect(numeroItaliano('333 1234567')).toBe('mobile')
    expect(numeroItaliano('+44 20 7946 0958')).toBe('')
    expect(numeroItaliano('')).toBe('')
    expect(numeroItaliano('abc')).toBe('')
  })

  it('draws the states of a verification', () => {
    expect(statoDellaVerifica('Pending').theme).toBe('orange')
    expect(statoDellaVerifica('Verified').label).toBe('Verified')
    expect(statoDellaVerifica('Failed').label).toBe('Not verified')
    expect(statoDellaVerifica('')).toBeNull()
  })

  it('splits the code into its digits', () => {
    expect(cifreDelCodice('123456')).toEqual(['1', '2', '3', '4', '5', '6'])
    expect(cifreDelCodice(482913)).toHaveLength(6)
    expect(cifreDelCodice(null)).toEqual([])
  })

  it('takes the extension as Twilio does', () => {
    expect(internoPulito(' 1 W 2 ')).toBe('1w2')
    expect(internoValido('ww1#')).toBe(true)
    expect(internoValido('')).toBe(true)
    expect(internoValido('interno 3')).toBe(false)
    expect(internoValido('1'.repeat(33))).toBe(false)
  })
})

describe('a call to Italy showing a verified number', () => {
  const numeri = [
    { number: '+390212345678', verified: true, mobile: false },
    { number: '+390687654321', verified: false, mobile: false },
    { number: '+393331234567', verified: true, mobile: true },
    { number: '+442079460958', verified: true, mobile: false },
  ]

  it('warns only for an Italian landline only verified, to Italy', () => {
    expect(incertaInItalia(numeri, '+390212345678', 'IT')).toBe(true)
    expect(incertaInItalia(numeri, '+390212345678', 'CH')).toBe(false)
    // a number of Twilio's is shown for certain
    expect(incertaInItalia(numeri, '+390687654321', 'IT')).toBe(false)
    // a mobile is blocked outright: another warning says so
    expect(incertaInItalia(numeri, '+393331234567', 'IT')).toBe(false)
    expect(incertaInItalia(numeri, '+442079460958', 'IT')).toBe(false)
    expect(incertaInItalia(numeri, '', 'IT')).toBe(false)
  })
})
