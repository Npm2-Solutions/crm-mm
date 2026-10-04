// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { describe, expect, it } from 'vitest'
import {
  MASSIMO,
  cancella,
  daComporre,
  digita,
  eNumero,
  leggibile,
  paginaDi,
  quandoChiamata,
} from '@/utils/telefono'

describe('digita', () => {
  it('adds what a phone dials', () => {
    expect(digita('', '3')).toBe('3')
    expect(digita('34', '7')).toBe('347')
    expect(digita('1', '*')).toBe('1*')
    expect(digita('1', '#')).toBe('1#')
  })

  it('takes the + only first', () => {
    expect(digita('', '+')).toBe('+')
    expect(digita('39', '+')).toBe('39')
  })

  it('ignores anything else and stops at the longest number', () => {
    expect(digita('3', 'a')).toBe('3')
    expect(digita('3', '12')).toBe('3')
    const lungo = '1'.repeat(MASSIMO)
    expect(digita(lungo, '2')).toBe(lungo)
  })
})

describe('cancella', () => {
  it('takes the last key away', () => {
    expect(cancella('347')).toBe('34')
    expect(cancella('')).toBe('')
    expect(cancella(null)).toBe('')
  })
})

describe('eNumero', () => {
  it('tells a number from a name', () => {
    expect(eNumero('+39 347 555 1234')).toBe(true)
    expect(eNumero('02-1234.5678')).toBe(true)
    expect(eNumero('(02) 1234')).toBe(true)
    expect(eNumero('Laura')).toBe(false)
    expect(eNumero('Laura 3')).toBe(false)
    expect(eNumero('+')).toBe(false)
    expect(eNumero('')).toBe(false)
  })
})

describe('daComporre', () => {
  it('keeps the digits, the leading + and the tones', () => {
    expect(daComporre('+39 347-555.1234')).toBe('+393475551234')
    expect(daComporre('(02) 1234 5678')).toBe('0212345678')
    expect(daComporre('12+34')).toBe('1234')
    expect(daComporre('1234#')).toBe('1234#')
  })
})

describe('quandoChiamata', () => {
  const adesso = new Date('2026-10-02T18:00:00')

  it('says the hour of a call today', () => {
    expect(quandoChiamata('2026-10-02 09:05:00', adesso, 'it-IT')).toBe('09:05')
  })

  it('says yesterday in the word given', () => {
    expect(quandoChiamata('2026-10-01 23:59:00', adesso, 'it-IT', 'ieri')).toBe(
      'ieri',
    )
  })

  it('says the day this week, the date before it', () => {
    expect(quandoChiamata('2026-09-28 10:00:00', adesso, 'it-IT')).toBe(
      'lunedì',
    )
    expect(quandoChiamata('2026-09-12 10:00:00', adesso, 'it-IT')).toBe(
      '12 set',
    )
  })

  it('is empty for no moment', () => {
    expect(quandoChiamata('', adesso, 'it-IT')).toBe('')
  })
})

describe('paginaDi', () => {
  it("opens the person's page, or the deal's", () => {
    expect(
      paginaDi({ reference_doctype: 'CRM Lead', reference_docname: 'L-1' }),
    ).toEqual({ name: 'Lead', params: { leadId: 'L-1' } })
    expect(
      paginaDi({ reference_doctype: 'CRM Deal', reference_docname: 'D-1' }),
    ).toEqual({ name: 'Deal', params: { dealId: 'D-1' } })
  })

  it('opens nothing for an unknown number', () => {
    expect(paginaDi({})).toBeNull()
    expect(paginaDi(null)).toBeNull()
  })
})

describe('leggibile', () => {
  it('writes an Italian mobile in groups, with its country or without', () => {
    expect(leggibile('+393331234567')).toBe('+39 333 123 4567')
    expect(leggibile('+39 351 7861795')).toBe('+39 351 786 1795')
    expect(leggibile('3331234567')).toBe('333 123 4567')
    expect(leggibile('0039 333 123 456')).toBe('+39 333 123 456')
  })

  it('writes Milan and Rome after their prefix, other landlines whole', () => {
    expect(leggibile('+390212345678')).toBe('+39 02 1234 5678')
    expect(leggibile('06 1234 5678')).toBe('06 1234 5678')
    expect(leggibile('+390331123456')).toBe('+39 0331123456')
    expect(leggibile('0331 123456')).toBe('0331 123456')
  })

  it('leaves as written what it cannot read', () => {
    expect(leggibile('+14155552671')).toBe('+14155552671')
    expect(leggibile('+39XXXXXX')).toBe('+39XXXXXX')
    expect(leggibile('anna@example.com')).toBe('anna@example.com')
    expect(leggibile('')).toBe('')
    expect(leggibile(null)).toBe('')
  })
})
