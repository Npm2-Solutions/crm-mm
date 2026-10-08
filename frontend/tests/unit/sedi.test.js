// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { describe, expect, it } from 'vitest'
import { colonneDelGiorno, testoDelBlocco } from '@/utils/agenda'
import {
  indirizzoDellaSede,
  nellaSede,
  nomeDellaSede,
  opzioniDelleSedi,
  piuSedi,
  sedeValida,
  serve,
} from '@/utils/sedi'

const SEDI = [
  { name: 'MI', title: 'Sede di Milano', city: 'Milano' },
  { name: 'MB', title: 'Sede di Monza', city: 'Monza' },
]

describe('one location is no location', () => {
  it('asks for two', () => {
    expect(piuSedi([])).toBe(false)
    expect(piuSedi(undefined)).toBe(false)
    expect(piuSedi([SEDI[0]])).toBe(false)
    expect(piuSedi(SEDI)).toBe(true)
  })

  it('keeps a choice only while it is one of them', () => {
    expect(sedeValida(SEDI, 'MB')).toBe('MB')
    expect(sedeValida(SEDI, 'gone')).toBe('')
    expect(sedeValida(SEDI, '')).toBe('')
    expect(nomeDellaSede(SEDI, 'MB')).toBe('Sede di Monza')
    expect(nomeDellaSede(SEDI, '')).toBe('')
  })

  it('offers «all» first', () => {
    const opzioni = opzioniDelleSedi(SEDI, 'Tutte le sedi')
    expect(opzioni[0]).toEqual({ value: '', label: 'Tutte le sedi' })
    expect(opzioni[2]).toEqual({
      value: 'MB',
      label: 'Sede di Monza',
      nota: 'Monza',
    })
  })
})

describe('who belongs to a location', () => {
  it('a room by its location, one with none everywhere', () => {
    expect(serve('', 'MI')).toBe(true)
    expect(nellaSede('MI', { stanza: 'MI' })).toBe(true)
    expect(nellaSede('MI', { stanza: 'MB' })).toBe(false)
    expect(nellaSede('MI', { stanza: '' })).toBe(true)
    expect(nellaSede('', { stanza: 'MB' })).toBe(true)
  })

  it("a professional by the day's shifts, else the week's", () => {
    expect(nellaSede('MB', { delGiorno: ['MB'] })).toBe(true)
    expect(nellaSede('MI', { delGiorno: ['MB'] })).toBe(false)
    // a line good anywhere
    expect(nellaSede('MI', { delGiorno: [''] })).toBe(true)
    // not working that day
    expect(nellaSede('MI', { delGiorno: [] })).toBe(false)
    // the day not known: the week says
    expect(nellaSede('MI', { diSempre: ['MB'] })).toBe(false)
    expect(nellaSede('MI', { diSempre: ['MB', 'MI'] })).toBe(true)
    expect(nellaSede('MI', {})).toBe(true)
  })

  it('narrows the columns of a day, never what has something there', () => {
    const tutti = ['luca', 'giulia', 'elena']
    const orari = {
      luca: { '2026-10-06': { open: [[840, 1200]], sedi: ['MB'] } },
      giulia: { '2026-10-06': { open: [[510, 1140]], sedi: ['MI'] } },
      elena: { '2026-10-06': { open: [[540, 1080]], sedi: ['MI'] } },
    }
    const qui = (sede) => (chi) =>
      nellaSede(sede, { delGiorno: orari[chi]['2026-10-06'].sedi })
    expect(
      colonneDelGiorno(tutti, {
        giorno: '2026-10-06',
        orari,
        nellaSede: qui('MB'),
      }),
    ).toEqual(['luca'])
    expect(
      colonneDelGiorno(tutti, {
        giorno: '2026-10-06',
        orari,
        occupati: new Set(['elena']),
        nellaSede: qui('MB'),
      }),
    ).toEqual(['luca', 'elena'])
    // «show everybody» keeps the location
    expect(
      colonneDelGiorno(tutti, {
        giorno: '2026-10-06',
        orari,
        mostraTutti: true,
        nellaSede: qui('MI'),
      }),
    ).toEqual(['giulia', 'elena'])
    // nothing chosen: as before
    expect(colonneDelGiorno(tutti, { giorno: '2026-10-06', orari })).toEqual(
      tutti,
    )
  })
})

describe('what a block and an envelope say', () => {
  it('names the location while every location is shown', () => {
    const appuntamento = {
      service: 'Osteopatia',
      participants: [{ participant_name: 'Mario Rossi', status: 'Booked' }],
      resources: [{ resource: 'Monza A' }],
    }
    expect(testoDelBlocco(appuntamento).dove).toBe('Monza A')
    expect(
      testoDelBlocco(appuntamento, { nomeSede: 'Sede di Monza' }).dove,
    ).toBe('Monza A, Sede di Monza')
  })

  it('writes the address as an envelope does', () => {
    expect(
      indirizzoDellaSede({
        address_line: 'Via  Italia 12',
        pincode: '20900',
        city: 'Monza',
        province: 'mb',
      }),
    ).toBe('Via Italia 12, 20900 Monza (MB)')
    expect(indirizzoDellaSede({})).toBe('')
    expect(indirizzoDellaSede(null)).toBe('')
  })
})
