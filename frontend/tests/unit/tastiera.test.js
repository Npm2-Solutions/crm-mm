// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// The keyboard a phone opens for a field: the dial pad for a number, the one
// with @ for an email, the digits for a count, capitals for a code.
import { tastiera, tastieraDi } from '@/utils/tastiera'

describe('tastieraDi', () => {
  it('opens the dial pad for a phone number', () => {
    expect(tastieraDi({ fieldtype: 'Data', options: 'Phone' })).toEqual({
      type: 'tel',
    })
    expect(tastieraDi({ fieldtype: 'Phone' }).type).toBe('tel')
  })

  it('opens the email keyboard, never capitalised', () => {
    const email = tastieraDi({ fieldtype: 'Data', options: 'Email' })
    expect(email.type).toBe('email')
    expect(email.autocapitalize).toBe('none')
    expect(tastieraDi({ fieldname: 'pec' }).type).toBe('email')
  })

  it("opens a web address's keyboard for a website", () => {
    expect(tastieraDi({ fieldtype: 'Data', fieldname: 'website' }).type).toBe(
      'url',
    )
    expect(tastieraDi({ fieldtype: 'Data', options: 'URL' }).type).toBe('url')
  })

  it('opens the digits for a whole number, the decimal pad for an amount', () => {
    expect(tastieraDi({ fieldtype: 'Int' })).toEqual({ inputmode: 'numeric' })
    for (const fieldtype of ['Float', 'Currency', 'Percent']) {
      expect(tastieraDi({ fieldtype }).inputmode).toBe('decimal')
    }
  })

  it('writes a code in capitals and never corrects it', () => {
    for (const fieldname of ['fiscal_code', 'tax_id', 'recipient_code']) {
      const codice = tastieraDi({ fieldtype: 'Data', fieldname })
      expect(codice.autocapitalize).toBe('characters')
      expect(codice.autocorrect).toBe('off')
    }
  })

  it('leaves every other field to the ordinary keyboard', () => {
    expect(tastieraDi({ fieldtype: 'Data', fieldname: 'first_name' })).toEqual(
      {},
    )
    // a postal code may hold letters abroad: no digits-only pad
    expect(tastieraDi({ fieldtype: 'Data', fieldname: 'postal_code' })).toEqual(
      {},
    )
    expect(tastieraDi({ fieldtype: 'Small Text', fieldname: 'email' })).toEqual(
      {},
    )
    expect(tastieraDi(null)).toEqual({})
  })
})

describe('tastiera', () => {
  it('gives a keyboard by its name, nothing for one it does not know', () => {
    expect(tastiera('cifre').inputmode).toBe('numeric')
    expect(tastiera('telefono').type).toBe('tel')
    expect(tastiera('nessuna')).toEqual({})
  })
})
