// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { describe, expect, it } from 'vitest'
import {
  MASSIMO,
  campiDelDocumento,
  chiedeIndirizzo,
  cosaMancaPerMandare,
  documentiDaMandare,
  documentoScelto,
  fileAccettato,
  nomeDellaRichiesta,
  prefisso,
  prezzoAlMese,
  statoDellaRichiesta,
} from '@/utils/numeri'

// A new Italian number (doc 52): the page checks here what the server checks in
// crm/telephony/numeri_regole.py, before Twilio is asked.

const INDIRIZZO = {
  requirement: 'address_info',
  accepted: [
    { type: 'address', address: true, fields: ['address_sids'], inputs: [] },
  ],
}
const REGISTRO = {
  requirement: 'registration_info',
  accepted: [
    {
      type: 'business_registration',
      address: false,
      fields: ['business_name', 'document_number'],
      inputs: [
        { name: 'business_name', value: 'Centro Aurora srl' },
        { name: 'document_number', value: '' },
      ],
    },
    {
      type: 'commercial_registrar_excerpt',
      address: false,
      fields: ['business_name'],
      inputs: [{ name: 'business_name', value: 'Centro Aurora srl' }],
    },
  ],
}
const DOCUMENTI = [INDIRIZZO, REGISTRO]
const VISURA = { name: 'f1', file_name: 'visura.pdf' }
const SEDE = { street: 'Via Roma 1', city: 'Milano', postal_code: '20121' }

describe('a month of a number', () => {
  it('in the reader’s money words', () => {
    expect(prezzoAlMese(45, 'USD', 'en')).toBe('$45.00')
    expect(prezzoAlMese('4.25', 'EUR', 'it')).toMatch(/4,25/)
  })

  it('says nothing without a price', () => {
    expect(prezzoAlMese(null)).toBe('')
    expect(prezzoAlMese(undefined)).toBe('')
  })
})

describe('an area’s prefix', () => {
  it('as written, as the server reads it', () => {
    for (const scritto of ['02', ' 02 ', '+39 02', '0039 02', '39 02']) {
      expect(prefisso(scritto), scritto).toBe('02')
    }
    expect(prefisso('0471')).toBe('0471')
  })

  it('is no prefix otherwise', () => {
    for (const scritto of ['', null, '2', '333', '01234']) {
      expect(prefisso(scritto), String(scritto)).toBe('')
    }
  })
})

describe('the files Twilio takes', () => {
  it('a PDF, a JPEG or a PNG of 5 MB at most', () => {
    expect(fileAccettato('visura.PDF', 1000)).toBe('')
    expect(fileAccettato('bolletta.jpeg', MASSIMO)).toBe('')
    expect(fileAccettato('visura.docx', 1000)).toContain('PDF')
    expect(fileAccettato('senza', 1000)).toContain('PDF')
    expect(fileAccettato('visura.pdf', MASSIMO + 1)).toContain('5 MB')
  })
})

describe('where a request is', () => {
  it('in review, with the carrier and where it writes', () => {
    const stato = statoDellaRichiesta({
      status: 'In review',
      email: 'info@aurora.example',
    })
    expect(stato.theme).toBe('orange')
    expect(stato.riga[1]).toEqual(['Twilio', 'info@aurora.example'])
    expect(
      statoDellaRichiesta(
        { status: 'In review', email: 'info@aurora.example' },
        'Telnyx',
      ).riga[1],
    ).toEqual(['Telnyx', 'info@aurora.example'])
    // Telnyx asks no email of its own: the sentence names nobody
    const senza = statoDellaRichiesta({ status: 'In review' }, 'Telnyx').riga
    expect(senza[0]).not.toContain('{1}')
    expect(senza[1]).toEqual(['Telnyx'])
  })

  it('approved: choose the number, then another', () => {
    expect(
      statoDellaRichiesta({ status: 'Approved', numbers: [] }).riga[0],
    ).toContain('choose the number')
    expect(
      statoDellaRichiesta({
        status: 'Approved',
        numbers: [{ number: '+393331234567' }],
      }).riga[0],
    ).toContain('another number')
  })

  it('refused and draft, naming the carrier', () => {
    expect(statoDellaRichiesta({ status: 'Rejected' }).theme).toBe('red')
    expect(statoDellaRichiesta({ status: 'Draft' }).label).toBe('Draft')
    expect(statoDellaRichiesta({ status: 'Draft' }, 'Telnyx').riga[1]).toEqual([
      'Telnyx',
    ])
  })

  it('named with its area', () => {
    expect(
      nomeDellaRichiesta({ kind: 'Geographic number', area_code: '02' }),
    ).toBe('Geographic number 02')
    expect(nomeDellaRichiesta({ kind: 'Mobile number', area_code: '' })).toBe(
      'Mobile number',
    )
  })
})

describe('the documents', () => {
  it('the first accepted, unless one was picked', () => {
    expect(documentoScelto(REGISTRO).type).toBe('business_registration')
    expect(
      documentoScelto(REGISTRO, {
        registration_info: 'commercial_registrar_excerpt',
      }).type,
    ).toBe('commercial_registrar_excerpt')
    expect(
      documentoScelto(REGISTRO, { registration_info: 'mystery' }).type,
    ).toBe('business_registration')
  })

  it('ask only what whose the number is does not already', () => {
    expect(
      campiDelDocumento(REGISTRO.accepted[0], [{ name: 'business_name' }]).map(
        (c) => c.name,
      ),
    ).toEqual(['document_number'])
  })

  it('need the address when one of them proves it', () => {
    expect(chiedeIndirizzo(DOCUMENTI)).toBe(true)
    expect(chiedeIndirizzo([REGISTRO])).toBe(false)
  })

  it('say what is missing before sending', () => {
    const base = {
      documenti: DOCUMENTI,
      file: { registration_info: VISURA },
      indirizzo: SEDE,
      email: 'info@aurora.example',
    }
    expect(cosaMancaPerMandare(base)).toBe('')
    expect(cosaMancaPerMandare({ ...base, file: {} })).toContain('file')
    expect(
      cosaMancaPerMandare({ ...base, indirizzo: { street: 'Via Roma 1' } }),
    ).toContain('address')
    expect(cosaMancaPerMandare({ ...base, email: 'info' })).toContain('email')
    // the address is asked only when a document needs it
    expect(
      cosaMancaPerMandare({ ...base, documenti: [REGISTRO], indirizzo: {} }),
    ).toBe('')
  })

  it('go as the server takes them', () => {
    const mandati = documentiDaMandare({
      documenti: DOCUMENTI,
      file: { registration_info: VISURA },
      valori: { 'registration_info:document_number': ' 12345 ' },
    })
    expect(mandati).toEqual([
      {
        requirement: 'address_info',
        type: 'address',
        fields: ['address_sids'],
        address: true,
        values: {},
        file: null,
      },
      {
        requirement: 'registration_info',
        type: 'business_registration',
        fields: ['business_name', 'document_number'],
        address: false,
        values: { document_number: '12345' },
        file: 'f1',
      },
    ])
  })
})
