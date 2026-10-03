// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  PAROLE_DELLE_SCHEDE,
  nomeInAttesa,
  schedaChiusa,
} from '@/utils/schedaChiusa'

function msgid() {
  const testo = fs.readFileSync(
    path.resolve(import.meta.dirname, '../../../crm/locale/it.po'),
    'utf8',
  )
  return new Set(
    [...testo.matchAll(/^msgid "(.*)"$/gm)].map((m) =>
      m[1].replace(/\\"/g, '"').replace(/\\\\/g, '\\'),
    ),
  )
}

describe('a page that does not open', () => {
  it('says nothing while there is no error', () => {
    expect(schedaChiusa(null, 'CRM Lead')).toBe(null)
    expect(schedaChiusa(undefined, 'CRM Deal')).toBe(null)
  })

  it("explains a person one does not follow, never with the framework's words", () => {
    const motivo = schedaChiusa(
      {
        exc_type: 'PermissionError',
        messages: ['Not allowed via controller permission check'],
      },
      'CRM Lead',
    )
    expect(motivo.titolo).toBe('You do not follow this person')
    expect(motivo.testo).toMatch(/front desk/)
    expect(motivo.testo).not.toMatch(/controller/)
  })

  it('tells a record gone from one refused, for every record with a page', () => {
    for (const doctype of [
      'CRM Lead',
      'CRM Deal',
      'Contact',
      'CRM Organization',
    ]) {
      const negata = schedaChiusa({ exc_type: 'PermissionError' }, doctype)
      const sparita = schedaChiusa({ exc_type: 'DoesNotExistError' }, doctype)
      expect(negata.titolo).toBeTruthy()
      expect(sparita.titolo).toBeTruthy()
      expect(negata.titolo).not.toBe(sparita.titolo)
    }
  })

  it("keeps the server's sentence for any other error", () => {
    const motivo = schedaChiusa(
      { exc_type: 'ValidationError', messages: ['Something specific'] },
      'CRM Lead',
    )
    expect(motivo).toEqual({
      titolo: 'Error Occurred',
      testo: 'Something specific',
    })
    expect(schedaChiusa({}, 'CRM Lead').testo).toBe('An error occurred')
  })

  it('names a record by a word while it is not there, never by its code', () => {
    expect(nomeInAttesa('CRM Lead')).toBe('Person')
    expect(nomeInAttesa('CRM Deal')).toBe('Deal')
    expect(nomeInAttesa('Something else')).toBe('Document')
  })

  it('has every sentence in the Italian catalogue', () => {
    const catalogo = msgid()
    const frasi = Object.values(PAROLE_DELLE_SCHEDE).flatMap((casi) =>
      Object.values(casi).flat(),
    )
    expect(frasi.filter((frase) => !catalogo.has(frase))).toEqual([])
  })
})
