// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { describe, expect, it } from 'vitest'
import {
  CLIENTE,
  CONTATTO,
  PAZIENTE,
  fattoDel,
  rapportoDi,
  tonoDel,
  vistePerRapporto,
} from '@/utils/rapporto'

describe('rapportoDi', () => {
  it('reads the step the person carries', () => {
    expect(rapportoDi({ relationship: 'Contact' })).toBe(CONTATTO)
    expect(rapportoDi({ relationship: 'Client' })).toBe(CLIENTE)
    expect(rapportoDi({ relationship: 'Patient' })).toBe(PAZIENTE)
  })

  it('falls back on the dates, the highest first', () => {
    expect(rapportoDi({})).toBe(CONTATTO)
    expect(rapportoDi({ client_since: '2026-03-04 10:00:00' })).toBe(CLIENTE)
    expect(
      rapportoDi({
        client_since: '2026-03-04 10:00:00',
        patient_since: '2026-03-04 10:00:00',
      }),
    ).toBe(PAZIENTE)
  })

  it('a patient who has not come yet is still a patient', () => {
    expect(rapportoDi({ relationship: 'Patient', client_since: null })).toBe(
      PAZIENTE,
    )
  })
})

describe('tonoDel', () => {
  it('a tag for clients and patients, none for a contact', () => {
    expect(tonoDel(CLIENTE)).toBe('brand')
    expect(tonoDel(PAZIENTE)).toBe('rose')
    expect(tonoDel(CONTATTO)).toBe('')
    expect(tonoDel('')).toBe('')
  })
})

describe('fattoDel', () => {
  it('since when, where the person says so', () => {
    expect(
      fattoDel({ relationship: 'Patient', patient_since: '2025-10-04' }),
    ).toEqual({ frase: 'Patient since {0}', data: '2025-10-04' })
    expect(
      fattoDel({ relationship: 'Client', client_since: '2026-01-08' }),
    ).toEqual({ frase: 'Client since {0}', data: '2026-01-08' })
  })

  it('the step alone, without a date', () => {
    expect(fattoDel({ relationship: 'Contact' })).toEqual({
      frase: 'Contact',
      data: null,
    })
    expect(fattoDel({ relationship: 'Patient' })).toEqual({
      frase: 'Patient',
      data: null,
    })
  })
})

describe('vistePerRapporto', () => {
  it('is everybody, then each step the field holds, plural', () => {
    expect(
      vistePerRapporto(['', 'Contact', 'Client']).map((v) => [
        v.valore,
        v.etichetta,
      ]),
    ).toEqual([
      ['', 'All'],
      ['Contact', 'Leads'],
      ['Client', 'Clients'],
    ])
  })

  it('with the clinic, its patients too; the options as the server gives them', () => {
    const viste = vistePerRapporto([
      { label: '', value: '' },
      { label: 'Contatto', value: 'Contact' },
      { label: 'Cliente', value: 'Client' },
      { label: 'Paziente', value: 'Patient' },
    ])
    expect(viste.map((v) => v.etichetta)).toEqual([
      'All',
      'Leads',
      'Clients',
      'Patients',
    ])
    // the steps read in their context: a client is never a patient's word
    expect(viste[2].contesto).toBe('Relationship')
    expect(viste[0].contesto).toBeNull()
  })

  it('leaves out what is no step, and a step said twice', () => {
    expect(
      vistePerRapporto(['Client', 'Other', 'Client']).map((v) => v.valore),
    ).toEqual(['', 'Client'])
    expect(vistePerRapporto().map((v) => v.valore)).toEqual([''])
  })
})
