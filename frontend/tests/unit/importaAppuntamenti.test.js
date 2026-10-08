// Copyright (c) 2026, NPM2 Solutions Srl and contributors
import {
  esitoDellaRiga,
  resoconto,
  scelteDaMandare,
  scelteDi,
  statoDellAppuntamento,
} from '@/utils/importaAppuntamenti'

describe('appointments brought over, in words', () => {
  it('says what happens to a row', () => {
    expect(esitoDellaRiga({ outcome: 'left_out', problems: ['No date'] })).toBe(
      'No date',
    )
    expect(esitoDellaRiga({ outcome: 'found', problems: [] })).toBe(
      'Already here',
    )
    expect(
      esitoDellaRiga({
        outcome: 'new_person',
        problems: ['It ends before it starts'],
      }),
    ).toBe('New person · It ends before it starts')
    expect(esitoDellaRiga({ outcome: 'nobody' })).toMatch(/^Nobody here/)
  })

  it('says how it went', () => {
    expect(statoDellAppuntamento('Completed')).toBe('Took place')
    expect(statoDellAppuntamento('No Show')).toBe('Did not come')
    expect(statoDellAppuntamento('Scheduled')).toBe('Booked')
    expect(statoDellAppuntamento('Other')).toBe('Other')
  })

  it('offers the way out last', () => {
    const scelte = scelteDi('services', [{ value: 'Visita', label: 'Visita' }])
    expect(scelte.map((s) => s.value)).toEqual(['Visita', '__other__'])
    expect(scelteDi('rooms', null)).toEqual([{ value: '', label: 'No room' }])
  })

  it('sends the choices by name', () => {
    expect(
      scelteDaMandare({
        services: [{ name: 'Visita', choice: 'Visita' }],
        professionals: [{ name: 'Dott. Rossi', choice: null }],
      }),
    ).toEqual({
      services: { Visita: 'Visita' },
      professionals: { 'Dott. Rossi': '' },
      rooms: {},
    })
  })

  it('reports at the end', () => {
    const r = resoconto({
      created: 3,
      new_people: 1,
      already: 2,
      left_out: 1,
      nobody: 1,
      errors: [{ row: 4, error: 'No' }],
    })
    expect(r.frase).toBe(
      'Appointments brought in: 3. New people: 1. Already brought in before: 2. Left out: 2. Not brought in: 1.',
    )
    expect(r.errori).toEqual(['Row 4: No'])
    expect(resoconto(null)).toBeNull()
  })
})
