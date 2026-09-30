import { describe, expect, it } from 'vitest'
import {
  ABITUDINE,
  ABITUDINI,
  ALLENAMENTO,
  CIBO,
  ESERCIZI,
  ESERCIZIO,
  GRUPPO,
  MENU,
  OGNI_GIORNO,
  SCAMBI,
  descrivi,
  generiPer,
  giorniDellaVoce,
  isDieta,
  momentiIniziali,
  nuovaChiave,
  nuovaVoce,
  perMomento,
} from '@/utils/piani'

// a random that repeats: keys are predictable in a test
const sempre = (valore) => () => valore

describe('what a plan holds', () => {
  it('follows the server: a habit fits anywhere', () => {
    expect(generiPer(MENU)).toEqual([CIBO, ABITUDINE])
    expect(generiPer(SCAMBI)).toEqual([GRUPPO, CIBO, ABITUDINE])
    expect(generiPer(ALLENAMENTO)).toEqual([ESERCIZIO, ABITUDINE])
    expect(generiPer(ESERCIZI)).toEqual([ESERCIZIO, ABITUDINE])
    expect(generiPer(ABITUDINI)).toEqual([ABITUDINE])
    expect(generiPer('Horoscope')).toEqual([])
  })

  it('knows a diet', () => {
    expect(isDieta(MENU)).toBe(true)
    expect(isDieta(SCAMBI)).toBe(true)
    expect(isDieta(ALLENAMENTO)).toBe(false)
  })
})

describe('the rows', () => {
  it('keys of eight hex characters', () => {
    expect(nuovaChiave(sempre(0.5))).toBe('88888888')
    expect(nuovaChiave()).toMatch(/^[0-9a-f]{8}$/)
  })

  it('a diet starts from the day’s meals, a training from a session', () => {
    const nomi = {
      pasti: ['Colazione', 'Pranzo', 'Cena'],
      seduta: 'Seduta A',
      giorno: 'Ogni giorno',
    }
    expect(momentiIniziali(MENU, nomi).map((m) => m.label)).toEqual([
      'Colazione',
      'Pranzo',
      'Cena',
    ])
    expect(momentiIniziali(ALLENAMENTO, nomi)).toMatchObject([
      { label: 'Seduta A', day: OGNI_GIORNO },
    ])
    expect(momentiIniziali(ABITUDINI, nomi)[0].label).toBe('Ogni giorno')
  })

  it('a new item has what its kind needs to start', () => {
    expect(nuovaVoce(ESERCIZIO, 'm1', sempre(0))).toEqual({
      key: '00000000',
      moment: 'm1',
      kind: ESERCIZIO,
      times_per_week: '0',
      sets: 3,
      reps: '10',
    })
    expect(nuovaVoce(GRUPPO, 'm1').portions).toBe(1)
  })

  it('groups the items under their moment, in order', () => {
    const momenti = [{ key: 'a' }, { key: 'b' }]
    const voci = [
      { key: '1', moment: 'b' },
      { key: '2', moment: 'a' },
      { key: '3', moment: 'b' },
    ]
    expect(
      perMomento(momenti, voci).map((m) => m.items.map((v) => v.key)),
    ).toEqual([['2'], ['1', '3']])
  })
})

describe('how an item reads', () => {
  it('a food and how much', () => {
    expect(
      descrivi({ kind: CIBO, food_name: 'Pasta di semola', quantity_g: 80 }),
    ).toBe('Pasta di semola · 80 g')
  })

  it('portions of a group', () => {
    expect(descrivi({ kind: GRUPPO, food_group: 'Fish', portions: 1 })).toBe(
      '1 portion of Fish',
    )
    expect(
      descrivi({
        kind: GRUPPO,
        food_group: 'Fish',
        portions: 2,
        times_per_week: 3,
      }),
    ).toBe('2 portions of Fish · 3 times a week')
  })

  it('an exercise with its sets', () => {
    expect(
      descrivi({
        kind: ESERCIZIO,
        exercise_name: 'Ponte gluteo',
        sets: 3,
        reps: '12',
        rest: '60 s',
      }),
    ).toBe('Ponte gluteo · 3 × 12 · rest 60 s')
    expect(
      descrivi({
        kind: ESERCIZIO,
        exercise_name: 'Plank',
        sets: 2,
        duration: '30 s',
      }),
    ).toBe('Plank · 2 sets · 30 s')
  })

  it('a habit, in words', () => {
    expect(descrivi({ kind: ABITUDINE, text: 'Camminare 30 minuti' })).toBe(
      'Camminare 30 minuti',
    )
  })

  it('in the reader’s words', () => {
    const it = { '{0} portion of {1}': '{0} porzione di {1}', Fish: 'pesce' }
    const t = (s, a = []) =>
      (it[s] || s).replace(/{(\d+)}/g, (x, n) => String(a[n]))
    expect(descrivi({ kind: GRUPPO, food_group: 'Fish', portions: 1 }, t)).toBe(
      '1 porzione di pesce',
    )
  })
})

describe('how the days went', () => {
  it('each day its outcome, or nothing', () => {
    const logs = [
      { item_key: 'a', log_date: '2026-09-28', outcome: 'Done' },
      { item_key: 'b', log_date: '2026-09-28', outcome: 'Skipped' },
      { item_key: 'a', log_date: '2026-09-30', outcome: 'Partly' },
    ]
    expect(
      giorniDellaVoce(logs, 'a', ['2026-09-28', '2026-09-29', '2026-09-30']),
    ).toEqual([
      { day: '2026-09-28', outcome: 'Done' },
      { day: '2026-09-29', outcome: null },
      { day: '2026-09-30', outcome: 'Partly' },
    ])
  })
})
