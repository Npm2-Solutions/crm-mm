// Copyright (c) 2026, NPM2 Solutions Srl and contributors
import { describe, expect, it } from 'vitest'
import { fasceDi, graficoDellAndamento, variazione } from '@/utils/andamenti'

const SERIE = {
  title: 'Diario del dolore',
  label: 'Dolore',
  bands: [
    { from: 7, to: 20, label: 'Forte' },
    { from: 0, to: 6, label: 'Lieve' },
  ],
  points: [
    { date: '2026-08-01', value: 12, band: 'Forte' },
    { date: '2026-08-15', value: 8, band: 'Forte' },
    { date: '2026-09-14', value: 4, band: 'Lieve' },
  ],
}

describe('a total followed over time', () => {
  it('puts the bands in order', () => {
    expect(fasceDi(SERIE).map((b) => b.label)).toEqual(['Lieve', 'Forte'])
    expect(fasceDi({ bands: [{ from: 'a', to: 3, label: 'X' }] })).toEqual([])
  })

  it('places each total by its date and its value', () => {
    const g = graficoDellAndamento(SERIE)
    // from 0 to the top of the last band
    expect([g.minimo, g.massimo]).toEqual([0, 20])
    expect(g.punti.map((p) => p.x)).toEqual([30, 101.9, 256])
    // 12 of 20 between 8 and 118
    expect(g.punti[0].y).toBe(52)
    expect(g.linea).toBe('M30 52L101.9 74L256 96')
    expect(g.area).toEqual({ sinistra: 30, destra: 256, sopra: 8, sotto: 118 })
    expect(g.fasce).toEqual([
      { etichetta: 'Lieve', y: 85, altezza: 33, pari: true },
      { etichetta: 'Forte', y: 8, altezza: 71.5, pari: false },
    ])
    expect(g.tacche).toEqual([
      { valore: 20, y: 8 },
      { valore: 0, y: 118 },
    ])
  })

  it('sets one form alone in the middle', () => {
    const g = graficoDellAndamento({
      points: [{ date: '2026-08-01', value: 5 }],
    })
    expect(g.punti[0].x).toBe(143)
    expect([g.minimo, g.massimo]).toEqual([0, 5])
  })

  it('never divides by nothing', () => {
    const g = graficoDellAndamento({
      points: [{ date: '2026-08-01', value: 0 }],
    })
    expect([g.minimo, g.massimo]).toEqual([0, 1])
    expect(g.punti[0].y).toBe(118)
    expect(graficoDellAndamento({ points: [] }).punti).toEqual([])
  })

  it('says how the last total moved', () => {
    expect(variazione(SERIE)).toEqual({ differenza: -4, da: '2026-08-15' })
    expect(variazione({ points: [{ date: '2026-08-01', value: 3 }] })).toBe(
      null,
    )
  })
})
