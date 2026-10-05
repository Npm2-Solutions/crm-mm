// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// An event's reminder in words, whole in every language and on the 24-hour clock.
import { oraDelPromemoria, promemoriaInParole } from '@/utils/promemoria'

// an Italian translator over the sentences the helper hands it
const IT = {
  minute: 'minuto',
  minutes: 'minuti',
  hour: 'ora',
  hours: 'ore',
  day: 'giorno',
  days: 'giorni',
  week: 'settimana',
  weeks: 'settimane',
  '{0} {1} before': '{0} {1} prima',
  '{0} {1} before, by email': '{0} {1} prima, per email',
  '{0} {1} before, at {2}': '{0} {1} prima, alle {2}',
  '{0} {1} before, at {2}, by email': '{0} {1} prima, alle {2}, per email',
}
const t = (testo, argomenti = []) =>
  (IT[testo] || testo).replace(/\{(\d)\}/g, (_, i) => argomenti[i])

describe('promemoriaInParole', () => {
  it('says how long before, in the reader’s words', () => {
    expect(promemoriaInParole({ before: 15, interval: 'minutes' }, { t })).toBe(
      '15 minuti prima',
    )
    expect(promemoriaInParole({ before: 1, interval: 'hours' }, { t })).toBe(
      '1 ora prima',
    )
    expect(
      promemoriaInParole(
        { before: 2, interval: 'weeks', type: 'Email' },
        { t },
      ),
    ).toBe('2 settimane prima, per email')
  })

  it('says at what time an all-day event’s reminder leaves, on the 24-hour clock', () => {
    expect(
      promemoriaInParole(
        { before: 1, interval: 'days', time: '20:30' },
        { tuttoIlGiorno: true, t },
      ),
    ).toBe('1 giorno prima, alle 20:30')
    expect(
      promemoriaInParole(
        { before: 3, interval: 'days', type: 'Email' },
        { tuttoIlGiorno: true, t },
      ),
    ).toBe('3 giorni prima, alle 08:00, per email')
  })

  it('reads in English with no translator', () => {
    expect(promemoriaInParole({ before: 1, interval: 'days' })).toBe(
      '1 day before',
    )
    expect(
      promemoriaInParole(
        { before: 10, interval: 'minutes', type: 'Email' },
        { tuttoIlGiorno: true },
      ),
    ).toBe('10 minutes before, at 08:00, by email')
  })
})

describe('oraDelPromemoria', () => {
  it('writes the time as the 24-hour clock does', () => {
    expect(oraDelPromemoria('8:5')).toBe('08:05')
    expect(oraDelPromemoria('20:00:00')).toBe('20:00')
    expect(oraDelPromemoria('')).toBe('08:00')
    expect(oraDelPromemoria(null)).toBe('08:00')
  })
})
