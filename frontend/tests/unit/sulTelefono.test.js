// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { describe, expect, it } from 'vitest'
import {
  contattoDi,
  cosePerGruppo,
  dominioDi,
  doveAdesso,
  durataDellaChiamata,
  elencoDelGiorno,
  faseIniziale,
  gruppoDi,
  quandoTorna,
  rigaDellAzienda,
  rigaDellaNota,
  scadenzaInBreve,
  settimanaDi,
  spostaGiorno,
  valoreDellaTrattativa,
  versoDellaChiamata,
} from '@/utils/sulTelefono'

const ADESSO = new Date('2026-10-03T11:00:00')

describe('a person on one line', () => {
  it('says how to reach them, else their company', () => {
    // the number as one reads it, the stored one in groups
    expect(contattoDi({ mobile_no: '+393401112233', email: 'a@b.it' })).toBe(
      '+39 340 111 2233',
    )
    expect(contattoDi({ phone: '0212345678' })).toBe('02 1234 5678')
    expect(contattoDi({ email: 'a@b.it' })).toBe('a@b.it')
    expect(contattoDi({ organization: 'Studio Verdi' })).toBe('Studio Verdi')
    // masked (Marketing): nothing to reach them on, the company if any
    expect(
      contattoDi({
        mobile_no: '+39XXXXXX',
        email: 'XXXXXXXX',
        organization: 'Studio Verdi',
      }),
    ).toBe('Studio Verdi')
    expect(contattoDi({})).toBe('')
  })
})

describe('the open tasks by when they are due', () => {
  it('puts each in its group', () => {
    expect(gruppoDi({ due_date: '2026-10-01 09:00:00' }, ADESSO)).toBe('late')
    // this morning, past its hour: late
    expect(gruppoDi({ due_date: '2026-10-03 09:00:00' }, ADESSO)).toBe('late')
    expect(gruppoDi({ due_date: '2026-10-03 17:00:00' }, ADESSO)).toBe('today')
    expect(gruppoDi({ due_date: '2026-10-04 08:00:00' }, ADESSO)).toBe(
      'tomorrow',
    )
    expect(gruppoDi({ due_date: '2026-10-09 08:00:00' }, ADESSO)).toBe('later')
    expect(gruppoDi({ due_date: null }, ADESSO)).toBe('undated')
  })

  it('keeps a day chosen without an hour due all that day', () => {
    // its midnight is past, the day is not
    expect(gruppoDi({ due_date: '2026-10-03 00:00:00' }, ADESSO)).toBe('today')
    expect(gruppoDi({ due_date: '2026-10-04 00:00:00' }, ADESSO)).toBe(
      'tomorrow',
    )
    expect(gruppoDi({ due_date: '2026-10-02 00:00:00' }, ADESSO)).toBe('late')
    // no «00:00» under it: the group says the day
    expect(scadenzaInBreve('2026-10-04 00:00:00', 'it-IT', ADESSO)).toBe('')
    expect(scadenzaInBreve('2026-10-03 00:00:00', 'it-IT', ADESSO)).toBe('')
    expect(scadenzaInBreve('2026-10-09 00:00:00', 'it-IT', ADESSO)).toBe(
      'ven 9 ott',
    )
  })

  it('leaves out the empty groups and keeps the order', () => {
    const gruppi = cosePerGruppo(
      [
        { name: 1, due_date: null },
        { name: 2, due_date: '2026-10-03 17:00:00' },
        { name: 3, due_date: '2026-09-30 10:00:00' },
      ],
      ADESSO,
    )
    expect(gruppi.map((g) => g.key)).toEqual(['late', 'today', 'undated'])
    expect(gruppi[0].rows.map((r) => r.name)).toEqual([3])
  })

  it('says the hour for today and tomorrow, the day otherwise', () => {
    expect(scadenzaInBreve('2026-10-03 17:00:00', 'it-IT', ADESSO)).toBe(
      '17:00',
    )
    expect(scadenzaInBreve('2026-10-09 08:00:00', 'it-IT', ADESSO)).toBe(
      'ven 9 ott',
    )
    expect(scadenzaInBreve('2027-01-04 08:00:00', 'it-IT', ADESSO)).toBe(
      'lun 4 gen 2027',
    )
    expect(scadenzaInBreve('', 'it-IT', ADESSO)).toBe('')
  })

  it('says «today» and the hour of one late since this morning', () => {
    // late by its hour: the day alone did not say why it is late
    expect(scadenzaInBreve('2026-10-03 09:00:00', 'it-IT', ADESSO)).toBe(
      'oggi, 09:00',
    )
    expect(scadenzaInBreve('2026-10-03 09:00:00', 'en-GB', ADESSO)).toBe(
      'today, 09:00',
    )
    // late since an earlier day: its day
    expect(scadenzaInBreve('2026-10-02 18:00:00', 'it-IT', ADESSO)).toBe(
      'ven 2 ott',
    )
  })
})

describe('the deals board on a phone', () => {
  const fasi = [
    { name: 'Lead', type: 'Open' },
    { name: 'Offerta', type: 'Ongoing' },
    { name: 'Won', type: 'Won' },
  ]

  it('opens on the first open stage with deals', () => {
    expect(faseIniziale(fasi, { Offerta: 3, Won: 9 })).toBe('Offerta')
    expect(faseIniziale(fasi, { Won: 9 })).toBe('Won')
    expect(faseIniziale(fasi, {})).toBe('Lead')
    expect(faseIniziale([], {})).toBe('')
  })

  it('keeps the stage asked for', () => {
    expect(faseIniziale(fasi, { Offerta: 3 }, 'Won')).toBe('Won')
    expect(faseIniziale(fasi, { Offerta: 3 }, 'Altro')).toBe('Offerta')
  })

  it('shows a value only when there is one', () => {
    expect(valoreDellaTrattativa({ deal_value: 0, currency: 'USD' })).toBe('')
    expect(
      valoreDellaTrattativa({ deal_value: 1200, currency: 'EUR' }, 'it-IT'),
    ).toBe('1200\u00a0€')
    expect(valoreDellaTrattativa({ deal_value: 80.5 }, 'it-IT')).toBe(
      '80,50\u00a0€',
    )
  })
})

describe('when a person comes next', () => {
  it('says today or tomorrow with the hour, else the day', () => {
    expect(quandoTorna('2026-10-03 16:30:00', 'it-IT', ADESSO)).toEqual({
      quando: 'today',
      ora: '16:30',
    })
    expect(quandoTorna('2026-10-04 09:00:00', 'it-IT', ADESSO).quando).toBe(
      'tomorrow',
    )
    expect(quandoTorna('2026-10-09 09:00:00', 'it-IT', ADESSO)).toEqual({
      quando: 'day',
      ora: '09:00',
      giorno: '9 ott',
    })
    expect(quandoTorna(null, 'it-IT', ADESSO)).toBeNull()
  })
})

describe('the day on a phone', () => {
  it('gives the week a day falls in, Monday first', () => {
    const settimana = settimanaDi('2026-10-03') // a Saturday
    expect(settimana).toHaveLength(7)
    expect(settimana[0]).toBe('2026-09-28')
    expect(settimana[5]).toBe('2026-10-03')
    expect(settimana[6]).toBe('2026-10-04')
    expect(settimanaDi('2026-10-05')[0]).toBe('2026-10-05') // a Monday
    expect(settimanaDi('')).toEqual([])
  })

  it('moves a day across months', () => {
    expect(spostaGiorno('2026-10-31', 1)).toBe('2026-11-01')
    expect(spostaGiorno('2026-03-01', -1)).toBe('2026-02-28')
    expect(spostaGiorno('2026-10-03', 7)).toBe('2026-10-10')
  })

  it('lists the whole-day events first, then by when things start', () => {
    const righe = elencoDelGiorno(
      [
        {
          name: 'B',
          starts_on: '2026-10-03 17:00:00',
          ends_on: '2026-10-03 17:30:00',
        },
        {
          name: 'A',
          starts_on: '2026-10-03 09:00:00',
          ends_on: '2026-10-03 09:45:00',
        },
        // another day: out
        {
          name: 'C',
          starts_on: '2026-10-04 09:00:00',
          ends_on: '2026-10-04 10:00:00',
        },
        // from the night before into this morning: in
        {
          name: 'D',
          starts_on: '2026-10-02 23:30:00',
          ends_on: '2026-10-03 00:30:00',
        },
      ],
      [
        {
          id: 'EV1',
          fromDate: '2026-10-03',
          toDate: '2026-10-03',
          fromTime: '12:00',
          toTime: '13:00',
        },
        {
          id: 'EV2',
          fromDate: '2026-10-03',
          toDate: '2026-10-03',
          isFullDay: true,
        },
        {
          id: 'EV3',
          fromDate: '2026-10-01',
          toDate: '2026-10-01',
          fromTime: '12:00',
          toTime: '13:00',
        },
      ],
      '2026-10-03',
    )
    expect(righe.map((r) => r.id)).toEqual([
      'EV2',
      'appt:D',
      'appt:A',
      'EV1',
      'appt:B',
    ])
    expect(righe[0].intero).toBe(true)
    expect(righe[2].tipo).toBe('appointment')
    expect(righe[3].tipo).toBe('event')
  })

  it('puts now before the first thing still to start, on today only', () => {
    const righe = elencoDelGiorno(
      [
        {
          name: 'A',
          starts_on: '2026-10-03 09:00:00',
          ends_on: '2026-10-03 09:45:00',
        },
        {
          name: 'B',
          starts_on: '2026-10-03 17:00:00',
          ends_on: '2026-10-03 17:30:00',
        },
      ],
      [],
      '2026-10-03',
    )
    expect(doveAdesso(righe, '2026-10-03', new Date(2026, 9, 3, 12, 0))).toBe(1)
    expect(doveAdesso(righe, '2026-10-03', new Date(2026, 9, 3, 8, 0))).toBe(0)
    expect(doveAdesso(righe, '2026-10-03', new Date(2026, 9, 3, 18, 0))).toBe(
      -1,
    )
    expect(doveAdesso(righe, '2026-10-04', new Date(2026, 9, 3, 12, 0))).toBe(
      -1,
    )
  })
})

describe('a company on one line', () => {
  it('reads a website by its name', () => {
    expect(dominioDi('https://www.acme.it/chi-siamo')).toBe('acme.it')
    expect(dominioDi('studioverdi.com')).toBe('studioverdi.com')
    expect(dominioDi('http://clinica.example:8080')).toBe('clinica.example')
    expect(dominioDi('')).toBe('')
    expect(dominioDi(null)).toBe('')
  })

  it('says what it does and where it is online', () => {
    expect(
      rigaDellAzienda({ industry: 'Healthcare', website: 'https://acme.it' }),
    ).toBe('Healthcare · acme.it')
    expect(rigaDellAzienda({ website: 'www.acme.it' })).toBe('acme.it')
    expect(rigaDellAzienda({})).toBe('')
  })

  it('names its sector in the language of whoever reads', () => {
    const t = (testo) => ({ Transportation: 'Trasporti' })[testo] || testo
    expect(rigaDellAzienda({ industry: 'Transportation' }, t)).toBe('Trasporti')
    expect(rigaDellAzienda({ industry: 'Odontoiatria' }, t)).toBe(
      'Odontoiatria',
    )
  })
})

describe('a call on one line', () => {
  it('goes one way, or was missed', () => {
    expect(versoDellaChiamata({ type: 'Incoming', missed: true })).toBe(
      'missed',
    )
    expect(versoDellaChiamata({ type: 'Incoming' })).toBe('incoming')
    expect(versoDellaChiamata({ type: 'Outgoing' })).toBe('outgoing')
  })

  it('lasts as a clock reads it', () => {
    expect(durataDellaChiamata(109)).toBe('1:49')
    expect(durataDellaChiamata(7)).toBe('0:07')
    expect(durataDellaChiamata(3723)).toBe('1:02:03')
    expect(durataDellaChiamata(0)).toBe('')
    expect(durataDellaChiamata(null)).toBe('')
  })
})

describe('a note on one line', () => {
  it('says who wrote it, about whom and when, what of it is known', () => {
    expect(
      rigaDellaNota(
        { reference_title: 'Laura Rossi' },
        { autore: 'Anna Bianchi', quando: '2 ore fa' },
      ),
    ).toBe('Anna Bianchi · Laura Rossi · 2 ore fa')
    expect(rigaDellaNota({}, { quando: 'ieri' })).toBe('ieri')
    expect(rigaDellaNota()).toBe('')
  })
})
