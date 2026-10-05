// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { inOrdine, paginaDellaMancanza } from '@/utils/mancanze'

// What invoicing still misses takes whoever reads it to the page that fills it.

describe('the page a missing row opens', () => {
  it('a field of the company opens the company', () => {
    expect(paginaDellaMancanza({ field: 'tax_id' })).toBe('Issuing company')
    expect(paginaDellaMancanza({ field: 'sender_category' })).toBe(
      'Issuing company',
    )
    expect(paginaDellaMancanza({ field: 'conservation_joined' })).toBe(
      'Issuing company',
    )
  })

  it("the agency's account and Itala's code open the options", () => {
    expect(paginaDellaMancanza({ field: 'itala_recipient_code' })).toBe(
      'Invoicing defaults',
    )
  })

  it('records open their own list', () => {
    expect(
      paginaDellaMancanza({
        field: '',
        link: { doctype: 'CRM Service Provider' },
      }),
    ).toBe('Providers')
    expect(
      paginaDellaMancanza({ link: { doctype: 'CRM Billable Service' } }),
    ).toBe('Billable services')
    expect(
      paginaDellaMancanza({
        link: { doctype: 'CRM Professional Qualification', name: 'Biologo' },
      }),
    ).toBe('Qualification register')
  })

  it('a row with nowhere to go opens nothing', () => {
    expect(paginaDellaMancanza({ field: '' })).toBe('')
    expect(paginaDellaMancanza({ link: { doctype: 'User' } })).toBe('')
    expect(paginaDellaMancanza(null)).toBe('')
  })
})

describe('the order of what is missing', () => {
  it('what stops going live comes first, the rest keeps its place', () => {
    const voci = [
      { title: 'a' },
      { title: 'b', blocking: true },
      { title: 'c' },
      { title: 'd', blocking: true },
    ]
    expect(inOrdine(voci).map((v) => v.title)).toEqual(['b', 'd', 'a', 'c'])
    expect(inOrdine(undefined)).toEqual([])
  })
})
