import { describe, expect, it } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'
import {
  answerInWords,
  computeFormula,
  conditionFields,
  evaluate,
  fieldsBefore,
  groupsHold,
  keyFromLabel,
  newField,
  newSection,
  readyToPublish,
  renameInFormula,
  renameKey,
  schemaCounts,
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
    expect(answerInWords({ type: 'choice' }, ['Latex', 'Food'])).toBe('Latex, Food')
    expect(answerInWords({ type: 'scale', min_label: 'None', max_label: 'Worst' }, 3)).toBe(
      '3 (None – Worst)',
    )
    expect(answerInWords({ type: 'sides', unit: '°' }, { left: 120, right: '' })).toBe(
      'Left: 120 °',
    )
    expect(answerInWords({ type: 'score' }, 4, 'Moderate')).toBe('4 · Moderate')
    expect(answerInWords({ type: 'attachment' }, '/private/files/exam.pdf')).toBe('exam.pdf')
    expect(answerInWords({ type: 'text' }, null)).toBe('')
  })
})
