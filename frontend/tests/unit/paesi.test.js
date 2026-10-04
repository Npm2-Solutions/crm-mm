// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt
import { describe, expect, it } from 'vitest'
import { nomeDelPaese, paesiConIlScelto, tuttiIPaesi } from '@/utils/paesi'

describe('tuttiIPaesi', () => {
  const paesi = tuttiIPaesi('it')
  const codici = paesi.map((p) => p.value)

  it('lists every country of ISO 3166-1 once, Kosovo too', () => {
    expect(paesi.length).toBe(250)
    expect(new Set(codici).size).toBe(codici.length)
    expect(new Set(paesi.map((p) => p.label)).size).toBe(paesi.length)
    for (const c of ['IT', 'SM', 'VA', 'CH', 'FR', 'US', 'XK'])
      expect(codici).toContain(c)
  })

  it("names them in the reader's language, in its order", () => {
    expect(paesi.find((p) => p.value === 'IT').label).toBe('Italia')
    expect(paesi.find((p) => p.value === 'DE').label).toBe('Germania')
    const nomi = paesi.map((p) => p.label)
    expect(nomi).toEqual([...nomi].sort((a, b) => a.localeCompare(b, 'it')))
    expect(tuttiIPaesi('en').find((p) => p.value === 'DE').label).toBe(
      'Germany',
    )
  })

  it('leaves out groupings, reserved codes and the old ones', () => {
    for (const c of [
      'EU',
      'UN',
      'EZ',
      'ZZ',
      'IC',
      'EA',
      'AC',
      'SU',
      'YU',
      'DD',
      'AN',
    ]) {
      expect(codici).not.toContain(c)
    }
  })
})

describe('paesiConIlScelto', () => {
  it('keeps a stored code that is no country of today', () => {
    expect(paesiConIlScelto('IT', 'it').length).toBe(250)
    const conVecchio = paesiConIlScelto('YU', 'it')
    expect(conVecchio[0]).toEqual({
      label: nomeDelPaese('YU', 'it'),
      value: 'YU',
    })
    expect(conVecchio.length).toBe(251)
  })

  it('gives each caller its own copy of the list kept per language', () => {
    paesiConIlScelto('YU', 'it')
    const dopo = paesiConIlScelto('IT', 'it')
    expect(dopo.length).toBe(250)
    expect(dopo.some((p) => p.value === 'YU')).toBe(false)
  })
})
