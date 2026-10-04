// Copyright (c) 2026, NPM2 Solutions Srl and contributors
import { describe, expect, it } from 'vitest'
import { ITALIA, fusiOrari, nomeDelFuso } from '@/utils/fusiOrari'

const ZONE = ['Africa/Abidjan', 'America/New_York', 'Asia/Kolkata', ITALIA]

describe('the time zones a centre picks from', () => {
  it('puts the device and Italy first, then the rest in order', () => {
    const valori = fusiOrari({ zone: ZONE, dispositivo: 'Asia/Kolkata' }).map(
      (scelta) => scelta.value,
    )
    expect(valori).toEqual([
      'Asia/Kolkata',
      ITALIA,
      'Africa/Abidjan',
      'America/New_York',
    ])
  })

  it('names a zone in the reader language beside its IANA name', () => {
    const roma = fusiOrari({ zone: ZONE, lingua: 'it' })[0]
    expect(roma.value).toBe(ITALIA)
    expect(roma.label).toBe(`Europe/Rome · ${nomeDelFuso(ITALIA, 'it')}`)
    expect(fusiOrari({ zone: ['America/New_York'] })[0].label).toMatch(
      /^America\/New York/,
    )
  })

  it('keeps the stored zone the browser does not list', () => {
    const scelte = fusiOrari({ zone: ZONE, scelto: 'UTC' })
    expect(scelte.map((scelta) => scelta.value)).toContain('UTC')
    // «GMT+00:00» says nothing more than UTC
    expect(scelte.find((scelta) => scelta.value === 'UTC').label).toBe('UTC')
  })

  it('does not repeat the device when it is Italy', () => {
    const valori = fusiOrari({ zone: ZONE, dispositivo: ITALIA }).map(
      (scelta) => scelta.value,
    )
    expect(valori.filter((zona) => zona === ITALIA)).toHaveLength(1)
    expect(valori[0]).toBe(ITALIA)
  })

  it('names nothing it cannot', () => {
    expect(nomeDelFuso('Not/A_Zone')).toBe('')
  })
})
