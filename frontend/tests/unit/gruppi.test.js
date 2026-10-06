// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { describe, expect, it } from 'vitest'
import { intestazioneDelGruppo } from '@/utils/gruppi'
import { CONTESTO } from '@/utils/rapporto'

const PAROLE = {
  'Not set': 'Non impostato',
  Yes: 'Sì',
  No: 'No',
  New: 'Nuovo',
}
const t = (testo, _valori, contesto) =>
  contesto === CONTESTO && testo === 'Contact' ? 'Lead' : PAROLE[testo] || testo

describe('intestazioneDelGruppo', () => {
  it('reads a choice and a linked name in the reader’s words', () => {
    expect(
      intestazioneDelGruppo(
        'New',
        { fieldname: 'status', fieldtype: 'Link' },
        { t },
      ),
    ).toBe('Nuovo')
    // what the centre wrote stays as written
    expect(
      intestazioneDelGruppo(
        'Passaparola',
        { fieldname: 'source', fieldtype: 'Link' },
        { t },
      ),
    ).toBe('Passaparola')
  })

  it('reads a person’s step in its own context', () => {
    expect(
      intestazioneDelGruppo(
        'Contact',
        { fieldname: 'relationship', fieldtype: 'Select' },
        { t },
      ),
    ).toBe('Lead')
  })

  it('says yes or no for a tick', () => {
    const campo = { fieldname: 'converted', fieldtype: 'Check' }
    expect(intestazioneDelGruppo(1, campo, { t })).toBe('Sì')
    expect(intestazioneDelGruppo('0', campo, { t })).toBe('No')
    // the list groups the unticked with the empty ones
    expect(intestazioneDelGruppo('', campo, { t })).toBe('No')
  })

  it('names a colleague, and keeps the address when it knows nobody', () => {
    const campo = {
      fieldname: 'owner',
      fieldtype: 'Link',
      link_doctype: 'User',
    }
    const utente = (u) => ({ 'anna@example.com': 'Anna Bianchi' })[u]
    expect(
      intestazioneDelGruppo('anna@example.com', campo, { t, utente }),
    ).toBe('Anna Bianchi')
    expect(intestazioneDelGruppo('x@example.com', campo, { t, utente })).toBe(
      'x@example.com',
    )
  })

  it('writes a day as a date', () => {
    const giorno = (d) => `il ${d.slice(8)}/${d.slice(5, 7)}`
    expect(
      intestazioneDelGruppo(
        '2026-10-06',
        { fieldname: 'last_visit', fieldtype: 'Date' },
        { t, giorno },
      ),
    ).toBe('il 06/10')
  })

  it('says a group has nothing in that field', () => {
    for (const vuoto of ['', null, undefined]) {
      expect(
        intestazioneDelGruppo(
          vuoto,
          { fieldname: 'source', fieldtype: 'Link' },
          { t },
        ),
      ).toBe('Non impostato')
    }
  })

  it('leaves a free text as it is', () => {
    expect(
      intestazioneDelGruppo(
        'google',
        { fieldname: 'first_touch_source', fieldtype: 'Data' },
        { t: () => 'tradotto' },
      ),
    ).toBe('google')
  })
})
