// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import {
  cambiato,
  daSalvare,
  modulo,
  nomeDellaNumerazione,
  opzioni,
  opzioniDellaNumerazione,
  scelto,
  siPuoAccendere,
  statoDelCollegamento,
} from '@/utils/fattureInCloud'

// Settings > Invoicing > Fatture in Cloud: the page's state, its selects and
// what it sends back, out of what the server says.

const COLLEGATA = {
  configured: true,
  connected: true,
  needs_reconnect: false,
  fic_company: { id: 4242, name: 'Studio Test', vat_number: 'IT00743110157' },
  missing: [],
  vat: [
    {
      key: '22',
      label: 'IVA 22%',
      value: 0,
      options: [{ value: 0, label: '22% · Ordinaria' }],
    },
    {
      key: '0|N4',
      label: 'Esente (art. 10)',
      value: null,
      options: [
        { value: 12, label: '0% · Esente art. 10' },
        { value: 13, label: '0% · Esente art. 10 n. 18' },
      ],
    },
  ],
  accounts: [{ method: 'MP08', label: 'Carta', value: 2, options: [] }],
  numerations: {
    sdi: { value: '', options: ['', '/E'] },
    paper: { value: '/S', options: [''] },
    credit: { value: '', options: [''] },
  },
  ts_by: 'dottorcloud',
}

describe('where the connection is', () => {
  it('reads the steps in order', () => {
    expect(statoDelCollegamento(null)).toBe('')
    expect(statoDelCollegamento({ configured: false })).toBe('agenzia')
    expect(statoDelCollegamento({ configured: true })).toBe('scollegato')
    expect(statoDelCollegamento({ ...COLLEGATA, needs_reconnect: true })).toBe(
      'da_ricollegare',
    )
    expect(statoDelCollegamento({ ...COLLEGATA, fic_company: null })).toBe(
      'da_scegliere',
    )
    expect(statoDelCollegamento(COLLEGATA)).toBe('collegato')
  })

  it('switches on only when nothing is missing', () => {
    expect(siPuoAccendere(COLLEGATA)).toBe(true)
    expect(siPuoAccendere({ ...COLLEGATA, missing: ['Choose…'] })).toBe(false)
    expect(siPuoAccendere({ ...COLLEGATA, needs_reconnect: true })).toBe(false)
  })
})

describe('the choices', () => {
  it('the ordinary rate is 0, and 0 is a choice', () => {
    expect(scelto(0)).toBe(true)
    expect(scelto('')).toBe(false)
    expect(scelto(null)).toBe(false)
    expect(modulo(COLLEGATA).vat).toEqual({ 22: '0', '0|N4': '' })
  })

  it('a select starts with the empty choice, its values as strings', () => {
    expect(opzioni(COLLEGATA.vat[1], 'Scegli…')).toEqual([
      { label: 'Scegli…', value: '' },
      { label: '0% · Esente art. 10', value: '12' },
      { label: '0% · Esente art. 10 n. 18', value: '13' },
    ])
  })

  it('the main numbering by its words, a chosen one kept when gone', () => {
    const t = (s) => (s === 'Main numbering' ? 'Numerazione principale' : s)
    expect(nomeDellaNumerazione('', t)).toBe('Numerazione principale')
    expect(nomeDellaNumerazione('/E', t)).toBe('/E')
    expect(
      opzioniDellaNumerazione(COLLEGATA.numerations.paper, t).map(
        (o) => o.value,
      ),
    ).toEqual(['', '/S'])
  })

  it('what is sent back is numbers again, and only what is chosen', () => {
    const form = modulo(COLLEGATA)
    form.vat['0|N4'] = '13'
    expect(daSalvare(form)).toEqual({
      vat: { 22: 0, '0|N4': 13 },
      accounts: { MP08: 2 },
      numerations: { sdi: '', paper: '/S', credit: '' },
      ts_by: 'dottorcloud',
    })
    expect(cambiato(form, modulo(COLLEGATA))).toBe(true)
    expect(cambiato(modulo(COLLEGATA), modulo(COLLEGATA))).toBe(false)
  })
})
