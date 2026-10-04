// Copyright (c) 2026, NPM2 Solutions Srl and contributors
import { formatoDellaScadenza, traQuanto } from '@/utils/quando'

describe('traQuanto', () => {
  it('says tomorrow for the next day, however late in it', () => {
    expect(traQuanto(1)).toEqual(['tomorrow', []])
  })

  it('counts days, then weeks, months and years', () => {
    expect(traQuanto(3)).toEqual(['in {0} days', [3]])
    expect(traQuanto(20)).toEqual(['in {0} weeks', [2]])
    expect(traQuanto(100)).toEqual(['in {0} months', [3]])
    expect(traQuanto(800)).toEqual(['in {0} years', [2]])
  })

  it('never says one in the plural', () => {
    expect(traQuanto(8)).toEqual(['in 1 week', []])
    expect(traQuanto(13)).toEqual(['in 1 week', []])
    expect(traQuanto(40)).toEqual(['in 1 month', []])
    expect(traQuanto(400)).toEqual(['in 1 year', []])
    for (let giorni = 1; giorni < 1000; giorni++) {
      const [frase, valori] = traQuanto(giorni)
      if (frase.includes('{0}')) expect(valori[0], frase).toBeGreaterThan(1)
    }
  })
})

describe('a task’s due date', () => {
  it('drops the hour of a day chosen without one', () => {
    expect(
      formatoDellaScadenza('2026-10-05 00:00:00', 'D MMM, HH:mm', 'D MMM'),
    ).toBe('D MMM')
    expect(
      formatoDellaScadenza('2026-10-05T00:00', 'D MMM, HH:mm', 'D MMM'),
    ).toBe('D MMM')
    expect(
      formatoDellaScadenza('2026-10-05 09:30:00', 'D MMM, HH:mm', 'D MMM'),
    ).toBe('D MMM, HH:mm')
    expect(formatoDellaScadenza('', 'D MMM, HH:mm', 'D MMM')).toBe(
      'D MMM, HH:mm',
    )
  })
})
