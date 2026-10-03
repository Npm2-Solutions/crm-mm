// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { describe, expect, it } from 'vitest'
import {
  contattoDi,
  cosePerGruppo,
  faseIniziale,
  gruppoDi,
  quandoTorna,
  scadenzaInBreve,
  valoreDellaTrattativa,
} from '@/utils/sulTelefono'

const ADESSO = new Date('2026-10-03T11:00:00')

describe('a person on one line', () => {
  it('says how to reach them, else their company', () => {
    expect(contattoDi({ mobile_no: '+393401112233', email: 'a@b.it' })).toBe(
      '+393401112233',
    )
    expect(contattoDi({ phone: '0212345678' })).toBe('0212345678')
    expect(contattoDi({ email: 'a@b.it' })).toBe('a@b.it')
    expect(contattoDi({ organization: 'Studio Verdi' })).toBe('Studio Verdi')
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
