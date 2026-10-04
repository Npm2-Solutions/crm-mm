import { describe, expect, it } from 'vitest'
import {
  AL_MESE,
  A_SETTIMANA,
  ILLIMITATI,
  MENSILE,
  SUBITO,
  cosaDa,
  errore,
  erroreDelTipo,
  fine,
  percentuale,
  piuMesi,
  quantiIngressi,
  questoPeriodo,
  rate,
  rigaDelPosto,
  rimasti,
} from '@/utils/abbonamenti'

describe('a subscription in words', () => {
  it('says what a type gives', () => {
    expect(cosaDa({ months: 1, entries: ILLIMITATI })).toBe(
      '1 month · any number of entries',
    )
    expect(cosaDa({ months: 3, entries: AL_MESE, entries_count: 8 })).toBe(
      '3 months · 8 entries a month',
    )
    expect(quantiIngressi({ entries: A_SETTIMANA, entries_count: 1 })).toBe(
      '1 entry a week',
    )
    expect(quantiIngressi({ entries: A_SETTIMANA, entries_count: 2 })).toBe(
      '2 entries a week',
    )
  })

  it("says how this week's or month's entries stand", () => {
    const mese = { entries: AL_MESE, entries_count: 8, used: 2 }
    expect(questoPeriodo(mese)).toBe('2 of 8 used this month')
    expect(rimasti(mese)).toBe(6)
    expect(percentuale(mese)).toBe(25)
    const settimana = { entries: A_SETTIMANA, entries_count: 2, used: 3 }
    expect(questoPeriodo(settimana)).toBe('3 of 2 used this week')
    // never below none, never past the bar
    expect(rimasti(settimana)).toBe(0)
    expect(percentuale(settimana)).toBe(100)
    // any number: nothing to count
    const libero = { entries: ILLIMITATI, used: null }
    expect(questoPeriodo(libero)).toBe('')
    expect(rimasti(libero)).toBeNull()
    expect(percentuale(libero)).toBe(0)
    // not started yet: nothing counted
    expect(
      questoPeriodo({ entries: AL_MESE, entries_count: 8, used: null }),
    ).toBe('')
  })
})

describe('the days and the instalments, as the server makes them', () => {
  it('moves by months, the last of a shorter month', () => {
    expect(piuMesi('2026-10-05', 1)).toBe('2026-11-05')
    expect(piuMesi('2026-12-15', 12)).toBe('2027-12-15')
    expect(piuMesi('2027-01-31', 1)).toBe('2027-02-28')
    expect(piuMesi('2028-01-31', 1)).toBe('2028-02-29')
    expect(fine('2026-10-05', 1)).toBe('2026-11-04')
    expect(fine('2026-10-01', 3)).toBe('2026-12-31')
    expect(fine('', 3)).toBe('')
  })

  it('makes one instalment, or one a month with the cents at the end', () => {
    expect(rate('2026-10-05', 3, 270, SUBITO)).toEqual([
      { due_on: '2026-10-05', amount: 270 },
    ])
    expect(rate('2026-10-31', 3, 270, MENSILE)).toEqual([
      { due_on: '2026-10-31', amount: 90 },
      { due_on: '2026-11-30', amount: 90 },
      { due_on: '2026-12-31', amount: 90 },
    ])
    expect(rate('2026-10-05', 3, 100, MENSILE).map((r) => r.amount)).toEqual([
      33.33, 33.33, 33.34,
    ])
    expect(rate('', 3, 100, MENSILE)).toEqual([])
  })
})

describe('what a form says before the server', () => {
  it('asks the type and the first day of a sale', () => {
    expect(errore({ subscription_type: '', starts_on: '2026-10-05' })).toBe(
      'Choose the type of subscription',
    )
    expect(errore({ subscription_type: 'Open', starts_on: '' })).toBe(
      'Choose the first day',
    )
    expect(
      errore({ subscription_type: 'Open', starts_on: '2026-10-05', price: -1 }),
    ).toBe('A price is not below zero')
    expect(
      errore({ subscription_type: 'Open', starts_on: '2026-10-05', price: '' }),
    ).toBe('')
  })

  it("asks a type's name, months, services and entries", () => {
    const tipo = {
      type_name: 'Open',
      months: 1,
      services: ['Pilates'],
      entries: ILLIMITATI,
    }
    expect(erroreDelTipo(tipo)).toBe('')
    expect(erroreDelTipo({ ...tipo, type_name: ' ' })).toBe(
      'Give the type a name',
    )
    expect(erroreDelTipo({ ...tipo, months: 0 })).toBe(
      'A subscription lasts from 1 to 36 months',
    )
    expect(erroreDelTipo({ ...tipo, services: [] })).toBe(
      'Choose the services it comprises',
    )
    expect(erroreDelTipo({ ...tipo, entries: AL_MESE })).toBe(
      'Say how many entries',
    )
    expect(erroreDelTipo({ ...tipo, entries: AL_MESE, entries_count: 8 })).toBe(
      '',
    )
  })
})

describe("a person's place in the appointment's panel", () => {
  const opzioni = [{ name: 'SUB-1', type: 'Pilates 8' }]

  it('alone, it says the subscription', () => {
    expect(
      rigaDelPosto({ subscription: 'SUB-1', options: opzioni }, false),
    ).toBe('An entry of Pilates 8')
    expect(rigaDelPosto({ subscription: null, options: opzioni }, false)).toBe(
      'Not in a subscription',
    )
    // one the reader may not open: only that it is in one
    expect(rigaDelPosto({ subscription: 'SUB-9', options: [] }, false)).toBe(
      'In a subscription',
    )
  })

  it('in a class, whose place it is', () => {
    const posto = { participant_name: 'Anna', options: opzioni }
    expect(rigaDelPosto({ ...posto, subscription: 'SUB-1' }, true)).toBe(
      'Anna uses an entry of Pilates 8',
    )
    expect(rigaDelPosto({ ...posto, subscription: null }, true)).toBe(
      'Anna is not in a subscription',
    )
    expect(rigaDelPosto({ ...posto, subscription: 'SUB-9' }, true)).toBe(
      'Anna is in a subscription',
    )
  })

  it('nothing to say for nobody', () => {
    expect(rigaDelPosto(null, true)).toBe('')
  })
})
