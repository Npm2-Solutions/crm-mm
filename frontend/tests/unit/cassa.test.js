// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import {
  cifreDellaCassa,
  letturaDellaCassa,
  differenzaDiCassa,
  fraseDellaDifferenza,
  tonoDellaDifferenza,
} from '@/utils/cassa'

// The cash closing at the reception desk: the drawer against what it should
// hold, to the cent, and said in words.

describe('the cash closing', () => {
  it('says nothing while nothing was counted', () => {
    expect(differenzaDiCassa('', 100)).toBeNull()
    expect(differenzaDiCassa(null, 100)).toBeNull()
    // a drawer below zero is a typing error, not money missing
    expect(differenzaDiCassa('-5', 60.5)).toBeNull()
    expect(fraseDellaDifferenza(null, (t) => t, String)).toBe('')
    expect(tonoDellaDifferenza(null)).toBe('')
  })

  it('counts to the cent', () => {
    expect(differenzaDiCassa(100, 100)).toBe(0)
    expect(Object.is(differenzaDiCassa(0.3, 0.1 + 0.2), 0)).toBe(true)
    expect(differenzaDiCassa('95.5', 100)).toBe(-4.5)
    expect(differenzaDiCassa(120.1, '120')).toBe(0.1)
    expect(differenzaDiCassa(0, 0)).toBe(0)
  })

  it('says how the drawer stands', () => {
    const t = (testo, valori = []) =>
      testo.replace(/\{(\d)\}/g, (_, i) => valori[i])
    const soldi = (valore) => `${valore.toFixed(2)} €`
    expect(fraseDellaDifferenza(0, t, soldi)).toBe('The drawer is right')
    expect(fraseDellaDifferenza(-4.5, t, soldi)).toBe('4.50 € missing')
    expect(fraseDellaDifferenza(2, t, soldi)).toBe('2.00 € more than expected')
    expect(tonoDellaDifferenza(0)).toBe('green')
    expect(tonoDellaDifferenza(-1)).toBe('amber')
  })
})

describe('the cash counted, typed and shown', () => {
  it('shows the amount to the cent in the reader’s language', () => {
    expect(cifreDellaCassa(60.5, 'it')).toBe('60,50')
    expect(cifreDellaCassa('60.5', 'en-GB')).toBe('60.50')
    expect(cifreDellaCassa(1234.5, 'it')).toBe('1234,50')
    expect(cifreDellaCassa('', 'it')).toBe('')
    expect(cifreDellaCassa(null, 'it')).toBe('')
  })

  it('reads a comma or a point as the decimal separator', () => {
    expect(letturaDellaCassa('60,5')).toBe(60.5)
    expect(letturaDellaCassa('60.50')).toBe(60.5)
    expect(letturaDellaCassa('1.234,50')).toBe(1234.5)
    expect(letturaDellaCassa('1,234.50')).toBe(1234.5)
    expect(letturaDellaCassa(' 45 € ')).toBe(45)
    expect(letturaDellaCassa('-3')).toBe(-3)
    expect(letturaDellaCassa('')).toBe(null)
    expect(letturaDellaCassa('abc')).toBe(null)
  })
})
