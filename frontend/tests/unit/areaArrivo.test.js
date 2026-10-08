// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// «I'm here» on the next appointment: when the button shows.
import { describe, expect, it } from 'vitest'
import { prossimoCambio, statoDellArrivo } from '@/area/arrivo'

const fra = (apre, chiude) => ({
  check_in: { opens_in: apre, closes_in: chiude },
})

describe('statoDellArrivo', () => {
  it('opens half an hour before, closes at the end', () => {
    expect(statoDellArrivo(fra(600, 4200), 0)).toBe('presto')
    expect(statoDellArrivo(fra(600, 4200), 600_000)).toBe('aperto')
    expect(statoDellArrivo(fra(0, 4200), 0)).toBe('aperto')
    expect(statoDellArrivo(fra(0, 4200), 4_200_000)).toBeNull()
  })

  it('says when they already said it, nothing without a window', () => {
    expect(statoDellArrivo({ arrived: true }, 0)).toBe('arrivato')
    expect(statoDellArrivo({}, 0)).toBeNull()
    expect(statoDellArrivo(null, 0)).toBeNull()
  })
})

describe('prossimoCambio', () => {
  it('looks again when it opens, then when it closes', () => {
    expect(prossimoCambio(fra(600, 4200), 0)).toBe(600_000)
    expect(prossimoCambio(fra(600, 4200), 700_000)).toBe(3_500_000)
    expect(prossimoCambio(fra(600, 4200), 4_300_000)).toBeNull()
    expect(prossimoCambio({ arrived: true, ...fra(0, 10) }, 0)).toBeNull()
  })
})
