// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { describe, expect, it } from 'vitest'
import {
  filtriRicevute,
  mesiDaEsportare,
  scadenzaRicevuta,
  statoRicevuta,
} from '@/utils/ricevute'

// The suppliers' invoices as the «Received» tab reads them.

describe('what the desk did with one', () => {
  it('each state its words and its colour', () => {
    expect(statoRicevuta('ricevuta')).toEqual({
      label: 'To see',
      theme: 'orange',
    })
    expect(statoRicevuta('registrata')).toEqual({
      label: 'To the accountant',
      theme: 'green',
    })
    expect(statoRicevuta('rifiutata').theme).toBe('red')
  })

  it('an unknown state reads as just arrived', () => {
    expect(statoRicevuta('altro').label).toBe('To see')
  })

  it('the filters: all, each state, what is left to pay', () => {
    expect(filtriRicevute().map((f) => f.value)).toEqual([
      '',
      'ricevuta',
      'da_pagare',
      'registrata',
      'rifiutata',
    ])
  })
})

describe('when it is to be paid', () => {
  const oggi = '2026-10-05'
  it('paid, overdue, today, soon, later', () => {
    expect(scadenzaRicevuta({ paid_on: '2026-10-01' }, oggi).label).toBe('Paid')
    expect(scadenzaRicevuta({ due_date: '2026-10-01' }, oggi)).toEqual({
      label: 'Overdue',
      theme: 'red',
    })
    expect(scadenzaRicevuta({ due_date: oggi }, oggi).label).toBe('Due today')
    expect(scadenzaRicevuta({ due_date: '2026-10-08' }, oggi).theme).toBe(
      'orange',
    )
    expect(scadenzaRicevuta({ due_date: '2026-11-04' }, oggi)).toEqual({
      label: 'Due in {0} days',
      theme: 'gray',
    })
  })

  it('nothing without a term, nothing for a disputed one', () => {
    expect(scadenzaRicevuta({}, oggi)).toBeNull()
    expect(
      scadenzaRicevuta({ due_date: '2026-10-01', status: 'rifiutata' }, oggi),
    ).toBeNull()
  })

  it('the days in the sentence', () => {
    const t = (testo, valori) => testo.replace('{0}', valori?.[0])
    expect(scadenzaRicevuta({ due_date: '2026-11-04' }, oggi, t).label).toBe(
      'Due in 30 days',
    )
  })
})

describe('the months for the accountant', () => {
  it('this one and the eleven before, across the year', () => {
    const mesi = mesiDaEsportare('2026-02-15', (m) => `M${m}`)
    expect(mesi).toHaveLength(12)
    expect(mesi[0]).toEqual({
      value: '2026-02',
      label: 'M2 2026',
      year: 2026,
      month: 2,
    })
    expect(mesi[1].value).toBe('2026-01')
    expect(mesi[2]).toMatchObject({ value: '2025-12', year: 2025, month: 12 })
    expect(mesi[11].value).toBe('2025-03')
  })
})
