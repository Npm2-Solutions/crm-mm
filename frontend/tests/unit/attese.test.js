import { describe, expect, it } from 'vitest'
import {
  GIORNI,
  PARTI,
  comeStaLOfferta,
  errore,
  formatoDellaScadenza,
  giornoBreve,
  inFila,
  perIlServer,
  quandoPuo,
  scegli,
} from '@/utils/attese'

describe('when the person can', () => {
  it('says the days and the parts of the day', () => {
    const voce = {
      choice: { days: ['Monday', 'Wednesday'], parts: ['morning'] },
    }
    expect(quandoPuo(voce, undefined, 'en-GB')).toBe('Mon, Wed · Morning')
    expect(
      quandoPuo(
        { choice: { days: [], parts: ['evening'] } },
        undefined,
        'en-GB',
      ),
    ).toBe('Any day · Evening')
    expect(
      quandoPuo(
        { choice: { days: ['Friday'], parts: [] } },
        undefined,
        'en-GB',
      ),
    ).toBe('Fri · Any time')
    expect(quandoPuo({ choice: { days: [], parts: [] } })).toBe(
      'Any day, any time',
    )
    // every day is no day in particular
    expect(quandoPuo({ choice: { days: GIORNI, parts: [] } })).toBe(
      'Any day, any time',
    )
  })

  it('reads the hours written by hand as they are', () => {
    const voce = {
      choice: null,
      days: [
        { workday: 'Tuesday', start_time: '15:00:00', end_time: '17:00:00' },
      ],
    }
    expect(quandoPuo(voce, undefined, 'en-GB')).toBe('Tue 15:00–17:00')
  })

  it('reads a morning hour the server sends without its zero', () => {
    // a Time column comes as a timedelta: nine o'clock is "9:00:00"
    const voce = {
      choice: null,
      days: [
        { workday: 'Tuesday', start_time: '9:00:00', end_time: '12:30:00' },
      ],
    }
    expect(quandoPuo(voce, undefined, 'en-GB')).toBe('Tue 09:00–12:30')
  })

  it('names a weekday in the language shown', () => {
    expect(giornoBreve('Monday', 'it-IT')).toBe('lun')
    expect(giornoBreve('Sunday', 'en-GB')).toBe('Sun')
    expect(giornoBreve('Someday', 'en-GB')).toBe('Someday')
  })

  it('translates through the function it is given', () => {
    const t = (text) =>
      ({ Morning: 'Mattina', 'Any day': 'Ogni giorno' })[text] || text
    expect(quandoPuo({ choice: { days: [], parts: ['morning'] } }, t)).toBe(
      'Ogni giorno · Mattina',
    )
  })
})

describe('choosing days and parts', () => {
  it('turns one on or off and keeps the week in order', () => {
    expect(scegli(['Wednesday'], 'Monday', GIORNI)).toEqual([
      'Monday',
      'Wednesday',
    ])
    expect(scegli(['Monday', 'Wednesday'], 'Monday', GIORNI)).toEqual([
      'Wednesday',
    ])
    expect(scegli([], 'evening', PARTI)).toEqual(['evening'])
  })
})

describe('a new entry', () => {
  const base = { service: 'Massaggio', seats: 1 }

  it('wants a service, sensible places and days in order', () => {
    expect(errore({})).toBe('Choose a service')
    expect(errore(base)).toBe('')
    expect(errore({ ...base, seats: 0 })).toBe(
      'An entry waits for 1 to 20 places',
    )
    expect(errore({ ...base, seats: 2.5 })).toBe(
      'An entry waits for 1 to 20 places',
    )
    expect(
      errore({ ...base, from_date: '2026-10-10', until: '2026-10-01' }),
    ).toBe('The last day comes after the first')
  })

  it('goes to the server without the days for a class', () => {
    const form = {
      ...base,
      weekdays: ['Monday'],
      parts: ['morning'],
      channel: 'SMS',
      urgent: true,
    }
    expect(JSON.parse(perIlServer(form))).toMatchObject({
      service: 'Massaggio',
      weekdays: ['Monday'],
      parts: ['morning'],
      channel: 'SMS',
      urgent: 1,
      seats: 1,
      staff: null,
    })
    const lezione = JSON.parse(
      perIlServer({ ...form, class_session: 'APPT-00007' }),
    )
    expect([lezione.weekdays, lezione.parts]).toEqual([[], []])
  })
})

describe('an offer', () => {
  it('says when to answer, or that nobody was told', () => {
    const ora = (value) => value.slice(11, 16)
    expect(
      comeStaLOfferta(
        { status: 'Sent', channel: 'Email', expires_on: '2026-10-05 12:30:00' },
        undefined,
        ora,
      ),
    ).toBe('Answer by 12:30')
    expect(comeStaLOfferta({ status: 'Sent', channel: '' })).toBe(
      'Not sent: call them',
    )
    expect(comeStaLOfferta({ status: 'Taken' })).toBe('Taken by somebody else')
    expect(comeStaLOfferta(null)).toBe('')
  })
})

describe('the line', () => {
  it('puts the urgent first, then who joined first', () => {
    const voci = [
      { name: 'b', urgent: 0, since: '2026-10-02 09:00:00' },
      { name: 'a', urgent: 0, since: '2026-10-01 09:00:00' },
      { name: 'c', urgent: 1, since: '2026-10-03 09:00:00' },
    ]
    expect(inFila(voci).map((v) => v.name)).toEqual(['c', 'a', 'b'])
  })
})

describe('when an offer is to be answered', () => {
  it('says the hour today, the day too otherwise', () => {
    expect(formatoDellaScadenza('2026-10-05 13:35:00', '2026-10-05')).toBe(
      'HH:mm',
    )
    // tomorrow morning: «05:00» alone read as already gone
    expect(formatoDellaScadenza('2026-10-06 05:00:00', '2026-10-05')).toBe(
      'ddd D MMM, HH:mm',
    )
    expect(formatoDellaScadenza('', '2026-10-05')).toBe('ddd D MMM, HH:mm')
  })
})
