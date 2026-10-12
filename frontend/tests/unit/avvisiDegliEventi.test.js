// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt
// An event's reminder in the browser: only the session's, only what the popup
// draws, gone once closed or over.
import { describe, expect, it } from 'vitest'
import {
  CAMPI,
  avvisiDaTenere,
  eDellUtente,
  filtriDegliEventi,
  fineDellEvento,
  soloIlNecessario,
  tipoDellEvento,
} from '@/utils/avvisiDegliEventi'
import { adessoDelCentro, oraDelCentro } from '@/utils/scheduler'

const NOTE = 'Dolore lombare, peggiora la sera'

// Dott.ssa Neri's appointment with Anna Bianchi, as its reminder arrives
const VISITA = {
  event_name: 'EV-0001',
  subject: 'Fisioterapia — Anna Bianchi',
  description: NOTE,
  starts_on: '2026-10-12 17:30:00',
  ends_on: '2026-10-12 18:15:00',
  all_day_event: 0,
  owner: 'neri@centro.it',
  event_participants: ['neri@centro.it', 'verdi@centro.it'],
  notification_type: 'Notification',
}

function avviso(utente, notification = VISITA, campi = {}) {
  return {
    id: notification.event_name,
    utente,
    completed: false,
    notification,
    createdAt: '2026-10-12T15:20:00.000Z',
    ...campi,
  }
}

describe('whose a reminder is', () => {
  it('is its owner’s and its participants’', () => {
    expect(eDellUtente(VISITA, 'neri@centro.it')).toBe(true)
    expect(eDellUtente(VISITA, 'verdi@centro.it')).toBe(true)
    // the reception, marketing, another professional
    expect(eDellUtente(VISITA, 'accoglienza@centro.it')).toBe(false)
    expect(eDellUtente(VISITA, null)).toBe(false)
    expect(eDellUtente(null, 'neri@centro.it')).toBe(false)
  })

  it('finds a participant by their email, whatever their name', () => {
    const riunione = {
      ...VISITA,
      owner: 'neri@centro.it',
      event_participants: ['admin@example.com'],
    }
    expect(eDellUtente(riunione, 'Administrator')).toBe(false)
    expect(eDellUtente(riunione, 'Administrator', 'admin@example.com')).toBe(
      true,
    )
    expect(eDellUtente(riunione, 'Administrator', 'Admin@Example.com')).toBe(
      true,
    )
    expect(
      eDellUtente({ ...VISITA, owner: 'Administrator' }, 'Administrator'),
    ).toBe(true)
  })

  it('has no participants to read where none came', () => {
    const senza = { ...VISITA, event_participants: undefined }
    expect(eDellUtente(senza, 'neri@centro.it')).toBe(true)
    expect(eDellUtente(senza, 'verdi@centro.it')).toBe(false)
  })
})

describe('what the browser keeps of an event', () => {
  it('keeps what the popup draws, never the description', () => {
    const tenuto = soloIlNecessario(VISITA)
    expect(Object.keys(tenuto).sort()).toEqual([...CAMPI].sort())
    expect(tenuto).not.toHaveProperty('description')
    expect(JSON.stringify(tenuto)).not.toContain(NOTE)
    expect(tenuto.subject).toBe(VISITA.subject)
  })

  it('keeps nothing of nothing', () => {
    expect(soloIlNecessario(undefined)).toEqual({})
  })
})

describe('when an event is over', () => {
  it('at its end, else at its start', () => {
    expect(fineDellEvento(VISITA)).toBe('2026-10-12 18:15:00')
    expect(fineDellEvento({ starts_on: '2026-10-12 17:30:00' })).toBe(
      '2026-10-12 17:30:00',
    )
    expect(fineDellEvento({ ends_on: '2026-10-12T18:15:00.000' })).toBe(
      '2026-10-12 18:15:00',
    )
  })

  it('at the end of its day when it lasts all day, or says no hour', () => {
    expect(
      fineDellEvento({
        starts_on: '2026-10-12 00:00:00',
        ends_on: '2026-10-12 00:00:00',
        all_day_event: 1,
      }),
    ).toBe('2026-10-12 23:59:59')
    expect(fineDellEvento({ starts_on: '2026-10-13' })).toBe(
      '2026-10-13 23:59:59',
    )
  })

  it('never where it says no day', () => {
    expect(fineDellEvento({})).toBeNull()
    expect(fineDellEvento(undefined)).toBeNull()
  })
})

describe('the reminders a browser keeps', () => {
  const PRIMA = '2026-10-12 17:20:00'
  const DOPO = '2026-10-12 18:20:00'

  it('keeps the session’s, without the description', () => {
    const tenuti = avvisiDaTenere([avviso('neri@centro.it')], {
      utente: 'neri@centro.it',
      adesso: PRIMA,
    })
    expect(tenuti).toHaveLength(1)
    expect(tenuti[0].id).toBe('EV-0001')
    expect(tenuti[0].notification).not.toHaveProperty('description')
    expect(JSON.stringify(tenuti)).not.toContain(NOTE)
  })

  it('drops whoever signed in before on the same browser', () => {
    const avvisi = [
      avviso('verdi@centro.it'),
      // kept before a reminder said whom it was taken for
      { ...avviso('neri@centro.it'), utente: undefined },
    ]
    expect(
      avvisiDaTenere(avvisi, { utente: 'neri@centro.it', adesso: PRIMA }),
    ).toEqual([])
    // nobody signed in: nothing stays
    expect(
      avvisiDaTenere([avviso('neri@centro.it')], { utente: null }),
    ).toEqual([])
  })

  it('drops what was closed, here or in the settings', () => {
    const chiuso = avviso('neri@centro.it', VISITA, { completed: true })
    expect(
      avvisiDaTenere([chiuso], { utente: 'neri@centro.it', adesso: PRIMA }),
    ).toEqual([])
    expect(
      avvisiDaTenere([avviso('neri@centro.it')], {
        utente: 'neri@centro.it',
        completati: ['EV-0001'],
        adesso: PRIMA,
      }),
    ).toEqual([])
  })

  it('drops an event once it is over, on the centre’s clock', () => {
    const avvisi = [avviso('neri@centro.it')]
    expect(
      avvisiDaTenere(avvisi, { utente: 'neri@centro.it', adesso: DOPO }),
    ).toEqual([])
    // still on until its last minute
    expect(
      avvisiDaTenere(avvisi, {
        utente: 'neri@centro.it',
        adesso: '2026-10-12 18:15:00',
      }),
    ).toHaveLength(1)
  })

  it('reads a list that is not one as empty', () => {
    expect(avvisiDaTenere(null, { utente: 'neri@centro.it' })).toEqual([])
    expect(
      avvisiDaTenere([null, { utente: 'neri@centro.it' }], {
        utente: 'neri@centro.it',
      }),
    ).toEqual([])
  })
})

// The Events tab of the notifications, in Rome at 14:05 of 12 October 2026
// (summer time): 12:05 in UTC
const ISTANTE = new Date('2026-10-12T12:05:00Z')
const ADESSO = oraDelCentro(adessoDelCentro('Europe/Rome', ISTANTE))

function evento(starts_on, ends_on) {
  return { name: 'EV-0002', subject: 'Riunione', starts_on, ends_on }
}

describe('what the Events tab asks the server for', () => {
  it('the session’s open events not over on the centre’s clock', () => {
    expect(ADESSO).toBe('2026-10-12 14:05:00')
    expect(filtriDegliEventi('neri@centro.it', ADESSO)).toEqual({
      status: 'Open',
      owner: 'neri@centro.it',
      ends_on: ['>=', '2026-10-12 14:05:00'],
    })
  })

  it('leaves out what ended before now, never as a UTC instant', () => {
    const [, da] = filtriDegliEventi('neri@centro.it', ADESSO).ends_on
    expect(da).not.toContain('T')
    // the server compares an event's end, kept on the centre's clock, as text
    const finita = '2026-10-12 13:00:00'
    expect(finita >= da).toBe(false)
    // the UTC instant was read as 12:05: an hour after its end, still in
    expect(finita >= '2026-10-12 12:05:00').toBe(true)
    expect('2026-10-12 14:30:00' >= da).toBe(true)
  })
})

describe('under which heading the Events tab files an event', () => {
  it('upcoming when it starts more than five minutes from now', () => {
    expect(
      tipoDellEvento(
        evento('2026-10-12 14:30:00', '2026-10-12 15:00:00'),
        ADESSO,
      ),
    ).toBe('upcoming')
    expect(
      tipoDellEvento(
        evento('2026-10-13 09:00:00', '2026-10-13 10:00:00'),
        ADESSO,
      ),
    ).toBe('upcoming')
  })

  it('starting now within five minutes of its start, before or after', () => {
    expect(
      tipoDellEvento(
        evento('2026-10-12 14:08:00', '2026-10-12 15:00:00'),
        ADESSO,
      ),
    ).toBe('startingNow')
    expect(
      tipoDellEvento(
        evento('2026-10-12 14:02:00', '2026-10-12 15:00:00'),
        ADESSO,
      ),
    ).toBe('startingNow')
  })

  it('ongoing from then until its end', () => {
    expect(
      tipoDellEvento(
        evento('2026-10-12 13:30:00', '2026-10-12 14:30:00'),
        ADESSO,
      ),
    ).toBe('ongoing')
    // until its last minute
    expect(
      tipoDellEvento(
        evento('2026-10-12 13:30:00', '2026-10-12 14:05:00'),
        ADESSO,
      ),
    ).toBe('ongoing')
  })

  it('nowhere once it is over: it went under «Upcoming»', () => {
    // ended an hour before, which the UTC instant let through
    expect(
      tipoDellEvento(
        evento('2026-10-12 12:00:00', '2026-10-12 13:00:00'),
        ADESSO,
      ),
    ).toBeNull()
    // a short one over within five minutes of its start
    expect(
      tipoDellEvento(
        evento('2026-10-12 14:01:00', '2026-10-12 14:04:00'),
        ADESSO,
      ),
    ).toBeNull()
  })

  it('without an end, a moment: starting now, then over', () => {
    expect(tipoDellEvento(evento('2026-10-12 14:03:00'), ADESSO)).toBe(
      'startingNow',
    )
    expect(tipoDellEvento(evento('2026-10-12 13:50:00'), ADESSO)).toBeNull()
    expect(tipoDellEvento(evento('2026-10-12 16:00:00'), ADESSO)).toBe(
      'upcoming',
    )
  })

  it('across midnight, and however the server writes the time', () => {
    expect(
      tipoDellEvento(
        evento('2026-10-12 23:50:00', '2026-10-13 00:30:00'),
        '2026-10-13 00:10:00',
      ),
    ).toBe('ongoing')
    expect(
      tipoDellEvento(
        evento('2026-10-12T14:30:00', '2026-10-12 15:00:00.000000'),
        ADESSO,
      ),
    ).toBe('upcoming')
    expect(tipoDellEvento(evento('2026-10-12 14:30'), ADESSO)).toBe('upcoming')
  })

  it('nowhere where it says no time, or now is not one', () => {
    expect(
      tipoDellEvento(evento(null, '2026-10-12 15:00:00'), ADESSO),
    ).toBeNull()
    expect(tipoDellEvento(evento('2026-10-12'), ADESSO)).toBeNull()
    expect(tipoDellEvento(undefined, ADESSO)).toBeNull()
    expect(
      tipoDellEvento(
        evento('2026-10-12 14:30:00', '2026-10-12 15:00:00'),
        null,
      ),
    ).toBeNull()
  })
})
