// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import {
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
