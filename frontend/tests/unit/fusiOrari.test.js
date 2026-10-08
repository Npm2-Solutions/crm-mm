// Copyright (c) 2026, NPM2 Solutions Srl and contributors
import { describe, expect, it } from 'vitest'
import {
  ITALIA,
  cittaDelFuso,
  europei,
  fusiOrari,
  nomeDelFuso,
} from '@/utils/fusiOrari'

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

  it('names a zone by its city in the reader’s language, never its code', () => {
    const roma = fusiOrari({ zone: ZONE, lingua: 'it' })[0]
    expect(roma.value).toBe(ITALIA)
    expect(roma.label).toBe(`Roma · ${nomeDelFuso(ITALIA, 'it')}`)
    expect(fusiOrari({ zone: ZONE, lingua: 'en-GB' })[0].label).toBe(
      `Rome · ${nomeDelFuso(ITALIA, 'en-GB')}`,
    )
    expect(fusiOrari({ zone: ['America/New_York'] })[0].label).toMatch(
      /^New York · /,
    )
  })

  it('puts the rest in the order of their cities', () => {
    const citta = fusiOrari({
      zone: ['Europe/Warsaw', 'Europe/Athens', 'Europe/Vienna', ITALIA],
      lingua: 'it',
    }).map((scelta) => scelta.label.split(' · ')[0])
    // Varsavia after Vienna in Italian, though Warsaw comes last in English
    expect(citta).toEqual(['Roma', 'Atene', 'Varsavia', 'Vienna'])
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
    // asked again, the same words (kept, not formatted anew)
    expect(nomeDelFuso('Not/A_Zone')).toBe('')
    expect(nomeDelFuso(ITALIA, 'it')).toBe(nomeDelFuso(ITALIA, 'it'))
    expect(nomeDelFuso(ITALIA, 'it', new Date(2026, 0, 15))).toBe(
      nomeDelFuso(ITALIA, 'it'),
    )
  })
})

describe('a zone’s city', () => {
  it('reads Europe’s cities in Italian, the zone’s own name in English', () => {
    expect(cittaDelFuso('Europe/Warsaw', 'it')).toBe('Varsavia')
    expect(cittaDelFuso('Atlantic/Canary', 'it')).toBe('Canarie')
    expect(cittaDelFuso('Europe/Isle_of_Man', 'en-GB')).toBe('Isle of Man')
    expect(cittaDelFuso('Europe/Madrid', 'it')).toBe('Madrid')
    expect(cittaDelFuso('America/Argentina/Buenos_Aires', 'it')).toBe(
      'Buenos Aires',
    )
  })

  it('keeps a zone that is no place as it is written', () => {
    expect(cittaDelFuso('UTC')).toBe('UTC')
    expect(cittaDelFuso('')).toBe('')
    expect(cittaDelFuso(undefined)).toBe('')
  })
})

describe('Europe’s zones', () => {
  it('keeps the continent’s and the Atlantic islands’, in order', () => {
    expect(
      europei([
        'Europe/Rome',
        'Asia/Kolkata',
        'Atlantic/Canary',
        'America/New_York',
        'Europe/Lisbon',
        'Atlantic/Bermuda',
        'Europe/Rome',
      ]),
    ).toEqual(['Atlantic/Canary', 'Europe/Lisbon', 'Europe/Rome'])
    expect(europei()).toEqual([])
  })
})
