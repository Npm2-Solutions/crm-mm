import { describe, expect, it } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'
import {
  chiLoScrive,
  ABITUDINE,
  CIBO,
  ESERCIZIO,
  GRUPPO,
  OGNI_GIORNO,
  descrivi,
  giorniDellaVoce,
  momentiIniziali,
  offre,
  nuovaChiave,
  nuovaVoce,
  nutrienti,
  perGiorno,
  perMomento,
  arrotondaGrammi,
  rigaNutrienti,
  comeSiArriva,
  daComprare,
  perGruppo,
  quantitaDaComprare,
  testoDellaSpesa,
} from '@/utils/piani'

// the cases the server proves too: crm/clinica/tests/test_piani_regole.py reads them
const CASI = JSON.parse(
  fs.readFileSync(
    path.resolve(
      import.meta.dirname,
      '../../../crm/clinica/tests/casi_nutrienti.json',
    ),
    'utf8',
  ),
)

describe('the nutrients, from the tables, as the server counts them', () => {
  it.each(CASI.nutrients.map((c) => [c.name, c]))('%s', (_, c) => {
    expect(nutrienti(c.items, CASI.foods)).toEqual(c.expected)
  })

  it.each(CASI.days.map((c) => [c.name, c]))('days: %s', (_, c) => {
    expect(perGiorno(c.moments, c.items, CASI.foods)).toEqual(c.expected)
  })

  it('reads a total in words', () => {
    expect(rigaNutrienti(CASI.nutrients[1].expected)).toBe(
      '448 kcal · proteins 15.5 g · carbohydrates 70.2 g · fats 11.2 g · fibre 8.5 g',
    )
    expect(rigaNutrienti(null)).toBe('')
  })

  it.each(CASI.grams.map(([g, atteso]) => [String(g), g, atteso]))(
    'grams as weighed: %s',
    (_, g, atteso) => {
      expect(arrotondaGrammi(g)).toBe(atteso)
    },
  )
})

// a random that repeats: keys are predictable in a test
const sempre = (valore) => () => valore

// the kinds as the server describes them (crm.piani.api.descrivi_tipo)
const MENU = 'Meal plan'
const ALLENAMENTO = 'Training'
const ABITUDINI = 'Habits'
const TIPO = {
  [MENU]: {
    key: MENU,
    items: [CIBO, ABITUDINE],
    features: [
      'calories',
      'meals',
      'nutrients',
      'recipes',
      'shopping',
      'targets',
    ],
  },
  [ALLENAMENTO]: {
    key: ALLENAMENTO,
    items: [ESERCIZIO, ABITUDINE],
    features: [],
  },
  [ABITUDINI]: { key: ABITUDINI, items: [ABITUDINE], features: [] },
}

describe('what a kind offers', () => {
  it('reads it from what the server says', () => {
    expect(offre(TIPO[MENU], 'targets')).toBe(true)
    expect(offre(TIPO[ALLENAMENTO], 'targets')).toBe(false)
    expect(offre(undefined, 'meals')).toBe(false)
    expect(offre({ key: 'x' }, 'meals')).toBe(false)
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
    expect(momentiIniziali(TIPO[MENU], nomi).map((m) => m.label)).toEqual([
      'Colazione',
      'Pranzo',
      'Cena',
    ])
    expect(momentiIniziali(TIPO[ALLENAMENTO], nomi)).toMatchObject([
      { label: 'Seduta A', day: OGNI_GIORNO },
    ])
    expect(momentiIniziali(TIPO[ABITUDINI], nomi)[0].label).toBe('Ogni giorno')
    // a kind the editor does not know yet starts from a session
    expect(momentiIniziali(undefined, nomi)[0].label).toBe('Seduta A')
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

describe('the shopping list', () => {
  it('rounds up what to buy, to 10 g or to 100 g past the kilo', () => {
    expect(daComprare(552)).toEqual({ value: 560, unit: 'g' })
    expect(daComprare(560)).toEqual({ value: 560, unit: 'g' })
    expect(daComprare(1400)).toEqual({ value: 1.4, unit: 'kg' })
    expect(daComprare(1401)).toEqual({ value: 1.5, unit: 'kg' })
    expect(daComprare(null)).toBeNull()
    expect(daComprare(0)).toBeNull()
    expect(quantitaDaComprare(1400, 'it')).toBe('1,4 kg')
    expect(quantitaDaComprare(75, 'en')).toBe('80 g')
    expect(quantitaDaComprare(null)).toBe('')
  })

  it('says how the sum is made', () => {
    expect(comeSiArriva({ each: 80, times: 7 })).toBe('80 g, 7 times')
    expect(comeSiArriva({ each: null, times: 4 })).toBe('4 times')
    expect(comeSiArriva({ each: 80, times: 1 })).toBe('')
  })

  it('keeps the groups in the server’s order and pastes as words', () => {
    const lista = {
      foods: [
        { food_name: 'Pasta', food_group: 'Cereals and tubers', grams: 560 },
        { food_name: 'Riso', food_group: 'Cereals and tubers', grams: 80 },
        { food_name: 'Olio', food_group: 'Oils and fats', grams: null },
      ],
      groups: [{ food_group: 'Fish', portions: 3 }],
    }
    expect(
      perGruppo(lista.foods).map((g) => [g.group, g.items.length]),
    ).toEqual([
      ['Cereals and tubers', 2],
      ['Oils and fats', 1],
    ])
    expect(testoDellaSpesa(lista, undefined, 'en')).toBe(
      [
        'CEREALS AND TUBERS',
        '- Pasta: 560 g',
        '- Riso: 80 g',
        'OILS AND FATS',
        '- Olio',
        'Fish: 3 portions',
      ].join('\n'),
    )
  })
})

describe('chiLoScrive', () => {
  it('lists who writes a kind, one or the other', () => {
    expect(chiLoScrive(['Medico chirurgo', 'Biologo', 'Dietista'], 'it')).toBe(
      'Medico chirurgo, Biologo o Dietista',
    )
    expect(chiLoScrive(['Doctor', 'Dietitian'], 'en-GB')).toBe(
      'Doctor or Dietitian',
    )
    expect(chiLoScrive(['Fisioterapista'], 'it')).toBe('Fisioterapista')
  })

  it('says nothing without names', () => {
    expect(chiLoScrive([], 'it')).toBe('')
    expect(chiLoScrive(null)).toBe('')
  })
})
