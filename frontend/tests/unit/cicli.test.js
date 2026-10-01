import { describe, expect, it } from 'vitest'
import {
  INTERO,
  PER_SEDUTA,
  comeVa,
  daPrenotare,
  errore,
  laSeduta,
  percentuale,
  perIlServer,
  quota,
  siPrenota,
  tappe,
} from '@/utils/cicli'

const conti = (done, missed, booked, total, perseContano = true) => {
  const used = done + (perseContano ? missed : 0)
  return {
    done,
    missed,
    booked,
    used,
    left: Math.max(total - used - booked, 0),
    total,
  }
}

describe('a cycle of sessions in words', () => {
  it('says which session an appointment is', () => {
    expect(laSeduta({ number: 4, total: 10 })).toBe('Session 4 of 10')
    // a cancelled one, or one out of any cycle, has no number
    expect(laSeduta({ number: null, total: 10 })).toBe('')
    expect(laSeduta(null)).toBe('')
  })

  it('says how far the cycle is, and what is left', () => {
    expect(comeVa(conti(4, 1, 2, 10))).toBe(
      '4 of 10 done · 2 booked · 1 missed',
    )
    expect(comeVa(conti(0, 0, 0, 6))).toBe('0 of 6 done')
    expect(daPrenotare(conti(4, 1, 2, 10))).toBe('3 sessions to book')
    expect(daPrenotare(conti(4, 1, 4, 10))).toBe('1 session to book')
    expect(daPrenotare(conti(4, 1, 5, 10))).toBe('Nothing left to book')
  })

  it('fills the bar with what is used', () => {
    expect(percentuale(conti(4, 1, 2, 10))).toBe(50)
    // a missed session the cycle does not count is not used
    expect(percentuale(conti(4, 1, 2, 10, false))).toBe(40)
    expect(percentuale(null)).toBe(0)
  })

  it('shares the price as the server does', () => {
    expect(quota(400, 10)).toBe(40)
    expect(quota(100, 3)).toBe(33.33)
    expect(quota('', 3)).toBe(0)
    expect(quota(90, 0)).toBe(0)
  })

  it('takes another appointment while it is on and something is left', () => {
    expect(siPrenota({ status: 'Active', counts: conti(1, 0, 1, 3) })).toBe(
      true,
    )
    expect(siPrenota({ status: 'Active', counts: conti(1, 0, 2, 3) })).toBe(
      false,
    )
    expect(siPrenota({ status: 'Expired', counts: conti(1, 0, 0, 3) })).toBe(
      false,
    )
  })
})

describe("a cycle's steps", () => {
  it('draws one segment a session, the used ones done', () => {
    // a missed session is used up like a done one, as in percentuale()
    expect(tappe(conti(2, 1, 1, 5))).toEqual([true, true, true, false, false])
    expect(tappe(conti(0, 0, 0, 3))).toEqual([false, false, false])
    expect(tappe(conti(3, 0, 0, 3))).toEqual([true, true, true])
  })

  it('leaves the bar to a long cycle, and to nothing', () => {
    expect(tappe(conti(5, 0, 0, 31))).toBeNull()
    expect(tappe(conti(5, 0, 0, 31), 40)).toHaveLength(31)
    expect(tappe(null)).toBeNull()
    expect(tappe({ total: 0, used: 0 })).toBeNull()
  })
})

describe('a new cycle', () => {
  const buono = {
    service: 'Fisioterapia',
    sessions: '10',
    starts_on: '2026-10-01',
    valid_until: '2026-12-31',
    price: '400',
    billing: INTERO,
    missed_count: true,
    notes: '  Dopo la visita  ',
  }

  it('says the first thing to put right', () => {
    expect(errore(buono)).toBe('')
    expect(errore({ ...buono, service: '' })).toBe(
      'Choose the service of the sessions',
    )
    expect(errore({ ...buono, sessions: '0' })).toBe(
      'A cycle has from 1 to 100 sessions',
    )
    expect(errore({ ...buono, sessions: '2.5' })).toBe(
      'A cycle has from 1 to 100 sessions',
    )
    expect(errore({ ...buono, valid_until: '2026-09-01' })).toBe(
      'A cycle ends after it starts',
    )
    expect(errore({ ...buono, price: '' })).toBe(
      'A cycle paid as a whole has its price',
    )
    expect(errore({ ...buono, price: '', billing: PER_SEDUTA })).toBe('')
  })

  it('goes to the server as it takes it', () => {
    expect(perIlServer(buono)).toEqual({
      service: 'Fisioterapia',
      sessions: 10,
      starts_on: '2026-10-01',
      valid_until: '2026-12-31',
      price: 400,
      billing: INTERO,
      missed_count: 1,
      practitioner: null,
      notes: 'Dopo la visita',
    })
    expect(
      perIlServer({ ...buono, price: '', billing: 'x', missed_count: false }),
    ).toMatchObject({ price: null, billing: PER_SEDUTA, missed_count: 0 })
  })
})
