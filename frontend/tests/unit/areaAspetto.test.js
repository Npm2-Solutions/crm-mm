// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt
import { describe, expect, it } from 'vitest'
import { aspetto, avanzamento, giorno, intestazione, ora } from '@/area/aspetto'

describe('the time heading the next appointment', () => {
  it('says the day short and the time on the 24-hour clock', () => {
    expect(intestazione('2026-10-02 16:30:00')).toBe('ven 2 ott · 16:30')
    expect(intestazione('2026-10-15T09:05:00')).toBe('gio 15 ott · 09:05')
  })

  it('has nothing to say without a date', () => {
    expect(intestazione('')).toBe('')
    expect(intestazione('not a date')).toBe('')
  })
})

describe("a moment's time", () => {
  it('reads the time of day the server sends, the hour on two digits', () => {
    expect(ora('7:30:00')).toBe('07:30')
    expect(ora('13:00:00')).toBe('13:00')
    expect(ora('20:05')).toBe('20:05')
  })

  it('says nothing for what is not a time', () => {
    expect(ora(null)).toBe('')
    expect(ora('mattina')).toBe('')
  })
})

describe('a day of a plan', () => {
  it('is its weekday over its number, the day where the person is', () => {
    expect(giorno('2026-10-14')).toEqual({ settimana: 'mer', numero: '14' })
    expect(giorno('2026-10-18')).toEqual({ settimana: 'dom', numero: '18' })
  })
})

describe('a kind of plan', () => {
  it('takes its category from the system, never a colour of its own', () => {
    expect(aspetto({ colour: 'amber', icon: 'apple' })).toEqual({
      colore: 'amber',
      icona: 'apple',
    })
    expect(aspetto({ colour: '#ff0000', icon: 'apple' }).colore).toBe('')
    expect(aspetto(null)).toEqual({ colore: '', icona: '' })
  })
})

describe('how far the day is', () => {
  it('counts what was done, wholly or partly, of all that is planned', () => {
    const momenti = [
      { items: [{ outcome: 'Done' }, { outcome: null }] },
      { items: [{ outcome: 'Partly' }, { outcome: 'Skipped' }] },
      { items: [] },
    ]
    expect(avanzamento(momenti)).toEqual({ fatte: 2, tutte: 4 })
    expect(avanzamento(undefined)).toEqual({ fatte: 0, tutte: 0 })
  })
})
