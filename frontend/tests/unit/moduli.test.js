import { describe, expect, it } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'
import {
  answerInWords,
  BODY_OUTLINES,
  bodyChartInWords,
  bodyViews,
  cleanBodyChart,
  computeFormula,
  conditionFields,
  evaluate,
  fieldsBefore,
  groupsHold,
  keyFromLabel,
  newField,
  newSection,
  numberedMarks,
  readyToPublish,
  renameInFormula,
  renameKey,
  schemaCounts,
  smoothPath,
  truthy,
  usesOf,
  validateSchema,
} from '@/utils/moduli'
import { STARTERS } from '@/utils/moduliStarters'

// the cases the server proves too: crm/moduli/tests/test_schema.py reads them
const CASES = JSON.parse(
  fs.readFileSync(
    path.resolve(
      import.meta.dirname,
      '../../../crm/moduli/tests/casi_schema.json',
    ),
    'utf8',
  ),
)
const schemaOf = (c) =>
  structuredClone(
    typeof c.schema === 'string' ? CASES.schemas[c.schema] : c.schema,
  )

describe('the cases shared with the server', () => {
  it.each(CASES.conditions.map((c) => [c.name, c]))('condition: %s', (_, c) => {
    expect(groupsHold(c.groups, c.values)).toBe(c.expected)
  })

  it.each(CASES.formulas.map((c) => [c.formula || '(empty)', c]))(
    'formula: %s',
    (_, c) => {
      expect(computeFormula(c.formula, c.values, c.decimals ?? null)).toBe(
        c.expected,
      )
    },
  )

  it.each(CASES.evaluations.map((c) => [c.name, c]))(
    'evaluation: %s',
    (_, c) => {
      expect(evaluate(schemaOf(c), c.values)).toEqual(c.expected)
    },
  )

  it.each(CASES.body_charts.map((c) => [c.name, c]))(
    'body chart: %s',
    (_, c) => {
      const field = { id: 'b', type: 'body_chart', label: 'B', ...c.field }
      const { value, error } = cleanBodyChart(field, structuredClone(c.value))
      expect(value).toEqual(c.expected)
      expect(error !== null).toBe(c.error)
    },
  )

  it.each(CASES.validations.map((c) => [c.name, c]))(
    'validation: %s',
    (_, c) => {
      expect(validateSchema(schemaOf(c)).map((p) => p.code)).toEqual(c.expected)
    },
  )
})

describe('what Python calls true', () => {
  it('holds empty lists and objects false, as the server does', () => {
    expect([null, undefined, false, 0, '', [], {}].map(truthy)).toEqual(
      Array(7).fill(false),
    )
    expect([true, 1, 'x', [0], { a: 1 }, '0'].map(truthy)).toEqual(
      Array(6).fill(true),
    )
  })

  it('treats an empty stop list as no stop', () => {
    const schema = {
      sections: [
        {
          id: 's',
          fields: [
            {
              id: 'a',
              type: 'yesno',
              label: 'A',
              stop_if: [],
              required_if: [],
            },
          ],
        },
      ],
    }
    const state = evaluate(schema, { a: true })
    expect(state.stops).toEqual([])
    expect(state.required).toEqual([])
  })

  it('never reads a key off the prototype', () => {
    const schema = {
      sections: [
        { id: 's', fields: [{ id: 'constructor', type: 'text', label: 'C' }] },
      ],
    }
    expect(evaluate(schema, {}).values.constructor).toBe(null)
  })
})

describe('the builder', () => {
  it('makes keys from words, unique', () => {
    expect(keyFromLabel('Peso (kg)')).toBe('peso_kg')
    expect(keyFromLabel('Città di nascita')).toBe('citta_di_nascita')
    expect(keyFromLabel('1° visita')).toBe('visita')
    expect(keyFromLabel('', new Set(), 'field')).toBe('field')
    expect(keyFromLabel('Peso', new Set(['peso', 'peso_2']))).toBe('peso_3')
  })

  it('makes new fields and sections the schema accepts', () => {
    const schema = { sections: [newSection({ sections: [] }, 'About you')] }
    expect(schema.sections[0].id).toBe('about_you')
    for (const type of [
      'text',
      'number',
      'choice',
      'yesno',
      'date',
      'scale',
      'table',
      'sides',
    ]) {
      schema.sections[0].fields.push(newField(type, schema, `A ${type}`))
    }
    schema.sections[0].fields.push({
      ...newField('paragraph', schema),
      text: 'Read me',
    })
    schema.sections[0].fields.push(newField('signature', schema, 'Signature'))
    expect(validateSchema(schema)).toEqual([])
    expect(readyToPublish(schema)).toEqual([])
    expect(new Set(schema.sections[0].fields.map((f) => f.id)).size).toBe(10)
    expect(schemaCounts(schema)).toEqual({ sections: 1, questions: 9 })
  })

  it('renames a key everywhere it is used', () => {
    const schema = {
      sections: [
        {
          id: 's',
          fields: [
            { id: 'w', type: 'number', label: 'Weight' },
            { id: 'h', type: 'number', label: 'Height' },
            {
              id: 'bmi',
              type: 'calc',
              label: 'BMI',
              formula: 'w / (h / 100) ^ 2 + round(w)',
            },
            {
              id: 'q',
              type: 'scale',
              label: 'Q',
              show_if: [[{ field: 'w', operator: 'is_set' }]],
            },
            { id: 't', type: 'score', label: 'T', sources: ['w', 'q'] },
          ],
        },
      ],
    }
    expect(usesOf(schema, 'w')).toEqual([
      { field: 'bmi' },
      { field: 'q' },
      { field: 't' },
    ])
    expect(renameKey(schema, 'w', 'weight')).toBe(true)
    const [, , bmi, q, t] = schema.sections[0].fields
    expect(bmi.formula).toBe('weight / (h / 100) ^ 2 + round(weight)')
    expect(q.show_if[0][0].field).toBe('weight')
    expect(t.sources).toEqual(['weight', 'q'])
    expect(validateSchema(schema)).toEqual([])
    // taken or not a key: nothing changes
    expect(renameKey(schema, 'h', 'weight')).toBe(false)
    expect(renameKey(schema, 'h', 'Height')).toBe(false)
  })

  it('renames a name in a formula and not the names around it', () => {
    expect(renameInFormula('a + ab + ba + a_1 * a', 'a', 'x')).toBe(
      'x + ab + ba + a_1 * x',
    )
    expect(renameInFormula('max(a, 2)', 'max', 'x')).toBe('x(a, 2)')
  })

  it('offers a condition only the questions before it', () => {
    const schema = CASES.schemas.visit
    expect(fieldsBefore(schema, { field: 'smoker' }).map((f) => f.id)).toEqual([
      'weight',
      'height',
      'bmi',
    ])
    expect(fieldsBefore(schema, { section: 'risks' }).map((f) => f.id)).toEqual(
      ['weight', 'height', 'bmi', 'smoker', 'cigarettes'],
    )
    const fields = conditionFields(fieldsBefore(schema, { section: 'mood' }))
    expect(fields.find((f) => f.fieldname === 'smoker').fieldtype).toBe('Check')
    expect(fields.find((f) => f.fieldname === 'bmi').fieldtype).toBe('Float')
    const history = conditionFields(CASES.schemas.history.sections[0].fields)
    expect(history.find((f) => f.fieldname === 'allergies')).toMatchObject({
      fieldtype: 'Select',
      options: 'Penicillin\nLatex\nNone',
    })
    expect(history.find((f) => f.fieldname === 'drugs').fieldtype).toBe(
      'Attach',
    )
  })
})

describe('the forms to start from', () => {
  it.each(STARTERS.map((starter) => [starter.key, starter]))(
    '%s is ready to publish',
    (_, starter) => {
      expect(readyToPublish(starter.schema())).toEqual([])
    },
  )

  it('the history works out the BMI and asks which allergy', () => {
    const history = STARTERS.find((s) => s.key === 'history').schema()
    const state = evaluate(history, {
      weight: 70,
      height: 175,
      allergies: ['Latex'],
    })
    expect(state.values.bmi).toBe(22.9)
    expect(state.visible.allergies_which).toBe(true)
    expect(
      evaluate(history, { allergies: ['None'] }).visible.allergies_which,
    ).toBe(false)
  })

  it('the informed consent stops on a pacemaker and without the yes', () => {
    const informed = STARTERS.find((s) => s.key === 'informed').schema()
    const stops = evaluate(informed, { pacemaker: true, agree: false }).stops
    expect(stops.map((stop) => stop.field)).toEqual(['pacemaker', 'agree'])
  })

  it('the questionnaire adds up to a band', () => {
    const questionnaire = STARTERS.find(
      (s) => s.key === 'questionnaire',
    ).schema()
    const state = evaluate(questionnaire, {
      q1: 'Some days',
      q2: 'Nearly every day',
      q3: 'Never',
    })
    expect(state.values.total).toBe(4)
    expect(state.bands.total).toBe('Moderate')
  })
})

describe('a signed answer in words', () => {
  it('says what was answered, as the PDF does', () => {
    expect(answerInWords({ type: 'number', unit: 'kg' }, 70.5)).toBe('70.5 kg')
    expect(answerInWords({ type: 'yesno' }, false)).toBe('No')
    expect(answerInWords({ type: 'consent' }, true)).toBe('Agreed')
    expect(answerInWords({ type: 'choice' }, ['Latex', 'Food'])).toBe(
      'Latex, Food',
    )
    // a scale says how far it goes: its ends' numbers, then their words
    expect(
      answerInWords(
        { type: 'scale', min_label: 'None', max_label: 'Worst' },
        3,
      ),
    ).toBe('3 (0 None – 10 Worst)')
    expect(answerInWords({ type: 'scale', min: 1, max: 5 }, 4)).toBe(
      '4 (1 – 5)',
    )
    expect(
      answerInWords({ type: 'sides', unit: '°' }, { left: 120, right: '' }),
    ).toBe('Left: 120 °')
    expect(answerInWords({ type: 'score' }, 4, 'Moderate')).toBe('4 · Moderate')
    expect(
      answerInWords({ type: 'attachment' }, '/private/files/exam.pdf'),
    ).toBe('exam.pdf')
    expect(answerInWords({ type: 'text' }, null)).toBe('')
  })
})

describe('the body chart', () => {
  it('draws the outlines the server draws in the PDF', () => {
    const server = JSON.parse(
      fs.readFileSync(
        path.resolve(
          import.meta.dirname,
          '../../../crm/moduli/sagome_corpo.json',
        ),
        'utf8',
      ),
    )
    delete server._what
    expect({ ...BODY_OUTLINES }).toEqual(server)
  })

  it('shows both outlines unless the question names its own', () => {
    expect(bodyViews({})).toEqual(['front', 'back'])
    expect(bodyViews({ views: ['back'] })).toEqual(['back'])
    expect(bodyViews({ views: ['back', 'front'] })).toEqual(['front', 'back'])
    expect(bodyViews({ views: 'front' })).toEqual(['front', 'back'])
  })

  it('numbers the points in the order they were put', () => {
    const value = {
      marks: [
        { view: 'back', x: 0.5, y: 0.4 },
        { view: 'front', x: 0.2, y: 0.3 },
      ],
    }
    expect(numberedMarks(value).map((m) => [m.number, m.view])).toEqual([
      [1, 'back'],
      [2, 'front'],
    ])
    expect(numberedMarks(null)).toEqual([])
  })

  it('draws a stroke through the middles of its points', () => {
    expect(smoothPath([])).toBe('')
    expect(smoothPath([[0.5, 0.5]])).toBe('M100 230l0.1 0')
    expect(
      smoothPath([
        [0, 0],
        [0.5, 0.5],
        [1, 1],
      ]),
    ).toBe('M0 0Q100 230 150 345L200 460')
  })

  it('says each point in words, as the PDF does', () => {
    expect(
      bodyChartInWords({
        marks: [
          { view: 'back', x: 0.5, y: 0.4, label: 'Lower back', intensity: 7 },
          { view: 'front', x: 0.2, y: 0.3 },
        ],
        strokes: [{ view: 'back', points: [[0.1, 0.1]] }],
      }),
    ).toBe('1. Back · Lower back · 7/10\n2. Front\nDrawn by hand: Back')
    expect(answerInWords({ type: 'body_chart' }, null)).toBe('')
    expect(
      answerInWords(
        { type: 'body_chart' },
        { marks: [{ view: 'front', x: 0, y: 0, intensity: 0 }] },
      ),
    ).toBe('1. Front · 0/10')
  })

  it('starts a new one on both outlines, drawn by hand too', () => {
    const field = newField('body_chart', { sections: [] }, 'Dove fa male')
    expect(field).toMatchObject({
      id: 'dove_fa_male',
      type: 'body_chart',
      views: ['front', 'back'],
      drawing: true,
    })
    expect(
      readyToPublish({ sections: [{ id: 's', fields: [field] }] }),
    ).toEqual([])
  })
})

describe('the engine the /modulo page loads', () => {
  it('is this very file, copied where the website serves it', () => {
    const here = path.resolve(import.meta.dirname, '../..')
    const source = fs.readFileSync(
      path.join(here, 'src/utils/moduli.js'),
      'utf8',
    )
    const served = fs.readFileSync(
      path.join(here, '../crm/public/js/moduli_engine.js'),
      'utf8',
    )
    // run `yarn sync-moduli-engine` after changing src/utils/moduli.js
    expect(served === source).toBe(true)
  })
})

// a question without words is named by its place in the form, never its key
describe('a question left without words', () => {
  it('is said by its number across the sections', () => {
    const schema = {
      sections: [
        { id: 's1', fields: [{ id: 'a', type: 'text', label: 'A' }] },
        { id: 's2', fields: [{ id: 'signature', type: 'signature' }] },
      ],
    }
    const [problema] = validateSchema(schema).filter(
      (p) => p.code === 'missing_label',
    )
    expect(problema.field).toBe('signature')
    expect(problema.message).toBe('Question {0} needs its words')
    expect(problema.args).toEqual([2])
  })
})
