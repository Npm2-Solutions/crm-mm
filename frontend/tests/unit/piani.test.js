import { describe, expect, it } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'
import {
  aggiungiAlternativa,
  alternativeEquivalenti,
  aspettoDelCibo,
  conLaDose,
  grammiEquivalenti,
  misuraCasalinga,
  nomeBreve,
  ripartizioneEnergia,
  testoDellaDose,
  DOSI,
  chiLoScrive,
  copiaGiorno,
  copiaMomento,
  grammiIniziali,
  momentiDelGiorno,
  momentiPerGiorno,
  perOgniGiorno,
  totaleDelGiorno,
  versoGliObiettivi,
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

describe('the week', () => {
  const casuale = (() => {
    let n = 0
    return () => (n++ % 97) / 97
  })()
  const momenti = [
    { key: 'cola', label: 'Colazione', day: 'Every day' },
    { key: 'pran', label: 'Pranzo', day: 'Monday' },
    { key: 'cena', label: 'Cena', day: 'Monday' },
  ]
  const voci = [
    { key: 'a', moment: 'cola', kind: 'Food', food: 'latte', quantity_g: 200 },
    { key: 'b', moment: 'pran', kind: 'Food', food: 'pasta', quantity_g: 80 },
    { key: 'c', moment: 'cena', kind: 'Food', food: 'pasta', quantity_g: 50 },
  ]
  const cibi = {
    latte: { kcal: 50, protein_g: 3.3 },
    pasta: { kcal: 350, protein_g: 12 },
  }

  it('shows a day its own moments, and counts them', () => {
    expect(momentiDelGiorno(momenti, 'Monday').map((m) => m.key)).toEqual([
      'pran',
      'cena',
    ])
    expect(momentiDelGiorno(momenti, 'Every day')).toHaveLength(1)
    const conti = momentiPerGiorno(momenti)
    expect(conti[0]).toEqual({ day: 'Every day', count: 1 })
    expect(conti.find((c) => c.day === 'Monday').count).toBe(2)
    expect(conti.find((c) => c.day === 'Sunday').count).toBe(0)
  })

  it('copies a meal with new keys, its items with it', () => {
    const { momento, voci: nuove } = copiaMomento(
      momenti[1],
      voci,
      'Tuesday',
      casuale,
    )
    expect(momento.day).toBe('Tuesday')
    expect(momento.key).not.toBe('pran')
    expect(momento.label).toBe('Pranzo')
    expect(nuove).toHaveLength(1)
    expect(nuove[0].moment).toBe(momento.key)
    expect(nuove[0].key).not.toBe('b')
    expect(nuove[0].quantity_g).toBe(80)
  })

  it('copies a day into others, never into itself', () => {
    const copia = copiaGiorno(
      momenti,
      voci,
      'Monday',
      ['Monday', 'Wednesday', 'Friday'],
      casuale,
    )
    expect(copia.momenti.map((m) => m.day)).toEqual([
      'Wednesday',
      'Wednesday',
      'Friday',
      'Friday',
    ])
    expect(copia.voci).toHaveLength(4)
  })

  it('starts a food from its portion, its group’s, else 100 g', () => {
    expect(grammiIniziali({ portion_g: 80 })).toBe(80)
    expect(
      grammiIniziali({ portion_g: null, food_group: 'Oils and fats' }),
    ).toBe(10)
    expect(grammiIniziali({ food_group: 'Fruit' })).toBe(150)
    expect(grammiIniziali({ portion_g: null, food_group: 'Other' })).toBe(100)
    expect(grammiIniziali(null)).toBe(100)
  })

  it('makes an every-day moment one of each weekday', () => {
    const { momenti: nuovi, voci: sue } = perOgniGiorno(
      momenti[0],
      voci,
      casuale,
    )
    expect(nuovi.map((m) => m.day)).toEqual([
      'Monday',
      'Tuesday',
      'Wednesday',
      'Thursday',
      'Friday',
      'Saturday',
      'Sunday',
    ])
    expect(new Set(nuovi.map((m) => m.key)).size).toBe(7)
    expect(sue).toHaveLength(7)
  })

  it('counts a weekday with every day’s moments', () => {
    expect(totaleDelGiorno(momenti, voci, cibi, 'Monday').kcal).toBe(
      100 + 280 + 175,
    )
    expect(totaleDelGiorno(momenti, voci, cibi, 'Tuesday').kcal).toBe(100)
    expect(totaleDelGiorno(momenti, voci, cibi, 'Every day').kcal).toBe(100)
  })

  it('says how far the day is from its targets', () => {
    const [kcal, proteine, carboidrati] = versoGliObiettivi(
      { kcal: 1500, protein_g: 90, carbs_g: 10 },
      { kcal: 1800, protein_g: 80, carbs_g: '' },
    )
    expect(kcal).toMatchObject({ value: 1500, target: 1800, left: 300 })
    expect(kcal.share).toBeCloseTo(1500 / 1800)
    // over the target: the bar full, what is over said as a negative left
    expect(proteine).toMatchObject({ share: 1, left: -10 })
    expect(carboidrati).toMatchObject({ target: null, share: null })
  })
})

describe('how a food looks', () => {
  it('takes its mark from its name, else from its group', () => {
    expect(
      aspettoDelCibo({ food_name: 'Banana, polpa', food_group: 'Fruit' }),
    ).toEqual({ icona: 'lucide-banana', colore: 'rose' })
    expect(
      aspettoDelCibo({ food_name: 'Petto di pollo', food_group: 'Meat' }),
    ).toEqual({ icona: 'lucide-drumstick', colore: 'rose' })
    // «mela» is not the start of «melanzana»
    expect(
      aspettoDelCibo({
        food_name: 'Melanzana, cotta',
        food_group: 'Vegetables',
      }).icona,
    ).toBe('lucide-carrot')
    expect(
      aspettoDelCibo({ food_name: 'Acqua minerale', food_group: 'Drinks' })
        .icona,
    ).toBe('lucide-glass-water')
    expect(
      aspettoDelCibo({ food_name: 'Cosa', food_group: 'Unknown' }),
    ).toEqual({ icona: 'lucide-utensils', colore: 'violet' })
  })
})

describe('a household measure', () => {
  const olio = {
    food_name: 'Olio extravergine di oliva',
    food_group: 'Oils and fats',
  }
  it('says the grams as a kitchen measures them, in halves', () => {
    expect(misuraCasalinga(olio, 10)).toBe('1 tablespoon')
    expect(misuraCasalinga(olio, 20)).toBe('2 tablespoons')
    expect(misuraCasalinga({ food_name: 'Pane comune' }, 80)).toBe('1½ slices')
    expect(misuraCasalinga({ food_name: 'Pane comune' }, 25)).toBe('½ slice')
    expect(misuraCasalinga({ food_name: 'Uovo intero' }, 120)).toBe('2 eggs')
    expect(
      misuraCasalinga({ food_name: 'Mela', food_group: 'Fruit' }, 150),
    ).toBe('1 medium fruit')
  })
  it('says nothing far from a measure, or for what is weighed', () => {
    expect(misuraCasalinga(olio, 7)).toBe('')
    expect(
      misuraCasalinga({ food_name: 'Fragole', food_group: 'Fruit' }, 150),
    ).toBe('')
    expect(
      misuraCasalinga(
        { food_name: 'Pasta di semola', food_group: 'Cereals and tubers' },
        80,
      ),
    ).toBe('')
    expect(misuraCasalinga(olio, 0)).toBe('')
  })
  it('is said in the patient’s line', () => {
    expect(
      descrivi({
        kind: CIBO,
        food_name: 'Olio extravergine',
        food_group: 'Oils and fats',
        quantity_g: 10,
      }),
    ).toBe('Olio extravergine · 10 g (1 tablespoon)')
  })
})

describe('the same, another food', () => {
  const banana = { name: 'b', food_name: 'Banana, cruda', kcal: 89 }
  const voce = { food: 'b', quantity_g: 150, food_detail: banana }
  it('gives the grams of the same energy, to 5 g', () => {
    expect(grammiEquivalenti(133.5, { kcal: 50 })).toBe(265)
    expect(grammiEquivalenti(100, { kcal: 0 })).toBe(null)
  })
  it('offers each food of the group once, never itself', () => {
    const cibi = [
      banana,
      { name: 'p', food_name: 'Pera, cruda', kcal: 58 },
      { name: 'p2', food_name: 'Pera, cotta', kcal: 60 },
      { name: 'm', food_name: 'Mela', kcal: 52 },
      { name: 'x', food_name: 'Senza energia', kcal: 0 },
    ]
    expect(alternativeEquivalenti(voce, cibi)).toEqual([
      { name: 'p', food_name: 'Pera', grams: 230 },
      { name: 'm', food_name: 'Mela', grams: 255 },
    ])
    expect(alternativeEquivalenti({ ...voce, quantity_g: 0 }, cibi)).toEqual([])
  })
  it('puts the most alike first, one of each kind', () => {
    const olio = {
      name: 'o',
      food_name: 'Olio extravergine',
      kcal: 899,
      fat_g: 99.9,
    }
    const cibi = [
      { name: 'b1', food_name: 'Burro', kcal: 717, fat_g: 81, protein_g: 0.9 },
      {
        name: 'b2',
        food_name: 'Burro light',
        kcal: 400,
        fat_g: 40,
        protein_g: 3,
      },
      { name: 'p', food_name: 'Pancetta', kcal: 300, fat_g: 25, protein_g: 18 },
      { name: 's', food_name: 'Olio di semi', kcal: 900, fat_g: 100 },
    ]
    expect(
      alternativeEquivalenti(
        { food: 'o', quantity_g: 10, food_detail: olio },
        cibi,
      ),
    ).toEqual([
      { name: 's', food_name: 'Olio di semi', grams: 10 },
      { name: 'b1', food_name: 'Burro', grams: 15 },
      { name: 'p', food_name: 'Pancetta', grams: 30 },
    ])
  })
  it('writes them one after another, once', () => {
    const pera = { food_name: 'Pera', grams: 230 }
    expect(aggiungiAlternativa('', pera)).toBe('Pera 230 g')
    expect(aggiungiAlternativa('Mela 255 g', pera)).toBe(
      'Mela 255 g; Pera 230 g',
    )
    expect(aggiungiAlternativa('Pera 230 g', pera)).toBe('Pera 230 g')
    expect(nomeBreve('Mandorla, pelata, senza sale')).toBe('Mandorla')
    expect(nomeBreve('Latte intero (alimento medio)')).toBe('Latte intero')
  })
})

describe('where the energy comes from', () => {
  it('shares the energy of proteins, carbohydrates and fats', () => {
    const [proteine, carboidrati, grassi] = ripartizioneEnergia({
      protein_g: 90,
      carbs_g: 220,
      fat_g: 60,
    })
    expect(proteine).toMatchObject({ share: 20, within: null })
    expect(carboidrati).toMatchObject({
      share: 49,
      min: 45,
      max: 60,
      within: true,
    })
    expect(grassi).toMatchObject({ share: 30, within: true })
    expect(ripartizioneEnergia({ fat_g: 50, carbs_g: 10 })[2].within).toBe(
      false,
    )
    expect(ripartizioneEnergia({})).toEqual([])
  })
})

describe('an exercise’s dose', () => {
  it('is one tap: sets with reps, or held for a time', () => {
    expect(DOSI.map(testoDellaDose)).toContain('3 × 30 s')
    const voce = { kind: ESERCIZIO, sets: 3, reps: '10', duration: '' }
    expect(conLaDose(voce, { sets: 1, duration: '60 s' })).toMatchObject({
      sets: 1,
      reps: '',
      duration: '60 s',
    })
  })
  it('says the side in its line', () => {
    expect(
      descrivi({
        kind: ESERCIZIO,
        exercise_name: 'Affondo',
        sets: 3,
        reps: '10',
        side: 'Each side',
      }),
    ).toBe('Affondo · 3 × 10 · each side')
  })
})
