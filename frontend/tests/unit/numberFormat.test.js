// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { describe, expect, it } from 'vitest'
import { flt } from '@/utils/numberFormat'

// An amount typed in a field is read in the site's number format; a phone's
// decimal pad has only the separator of its own language.
describe('an amount typed on a phone', () => {
  it('on a site that writes 1,234.56, an Italian keyboard’s comma is the decimal point', () => {
    expect(flt('12,5', null, '#,###.##')).toBe(12.5)
    expect(flt('12,50', null, '#,###.##')).toBe(12.5)
    expect(flt('-0,75', null, '#,###.##')).toBe(-0.75)
    expect(flt('€ 45,00', null, '#,###.##')).toBe(45)
  })

  it('on a site that writes 1.234,56, an English keyboard’s point is the decimal point', () => {
    expect(flt('12.5', null, '#.###,##')).toBe(12.5)
    expect(flt('12.50', null, '#.###,##')).toBe(12.5)
    expect(flt('12,5', null, '#.###,##')).toBe(12.5)
  })

  it('keeps the site’s thousands where three digits follow, or the decimal separator is there', () => {
    expect(flt('1,234', null, '#,###.##')).toBe(1234)
    expect(flt('1,234.5', null, '#,###.##')).toBe(1234.5)
    expect(flt('1,234,567', null, '#,###.##')).toBe(1234567)
    expect(flt('1.234', null, '#.###,##')).toBe(1234)
    expect(flt('1.234,56', null, '#.###,##')).toBe(1234.56)
    expect(flt('1.234.567', null, '#.###,##')).toBe(1234567)
  })

  it('reads numbers as numbers', () => {
    expect(flt(12.5, null, '#.###,##')).toBe(12.5)
    expect(flt('', null, '#,###.##')).toBe(0)
  })
})
