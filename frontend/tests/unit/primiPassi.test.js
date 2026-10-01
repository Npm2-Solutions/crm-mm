// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { describe, expect, it } from 'vitest'
import { daMostrare, riassunto } from '@/utils/primiPassi'

const passi = (...fatti) => ({
  steps: fatti.map((done, i) => ({ key: `p${i}`, done })),
})

describe('the first steps', () => {
  it('counts what is done and points at the next one', () => {
    const r = riassunto(passi(true, false, true, false))
    expect([
      r.fatti,
      r.totale,
      r.prossimo.key,
      r.percentuale,
      r.finiti,
    ]).toEqual([2, 4, 'p1', 50, false])
  })

  it('is finished when every step is done, never when there are none', () => {
    expect(riassunto(passi(true, true)).finiti).toBe(true)
    expect(riassunto(passi(true, true)).prossimo).toBe(null)
    expect(riassunto(passi()).finiti).toBe(false)
    expect(riassunto(undefined)).toEqual({
      fatti: 0,
      totale: 0,
      prossimo: null,
      percentuale: 0,
      finiti: false,
    })
  })

  it('shows them while some are left, unless hidden', () => {
    expect(daMostrare(passi(true, false))).toBe(true)
    expect(daMostrare(passi(true, false), true)).toBe(false)
  })

  it('shows nothing to a centre that already works, or to who has no step', () => {
    expect(daMostrare(passi(true, true, true))).toBe(false)
    expect(daMostrare(passi())).toBe(false)
    expect(daMostrare(null)).toBe(false)
  })
})
