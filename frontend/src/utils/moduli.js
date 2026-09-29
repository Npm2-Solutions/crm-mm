/**
 * The form templates engine in the browser.
 *
 * The same rules as `crm/moduli/schema.py`, proved on the same cases
 * (`crm/moduli/tests/casi_schema.json`, read by `tests/unit/moduli.test.js`):
 * what shows, what is worked out, what is required, where to stop and tell the
 * operator. What a person sees while filling a form is what the server decides.
 *
 * Python and JavaScript disagree on what is "nothing" (`[]` and `{}` are false in
 * Python, true here), so this file asks `truthy()` wherever the Python asks an
 * `if` or an `or`: the two sides answer the same even on a half-written schema.
 *
 * Below the engine, the builder's pure helpers: new fields, keys from labels,
 * renaming a key everywhere it is used, what a condition may look at.
 */

export const OPERATORS = [
  'equals',
  'not_equals',
  'contains',
  'is_set',
  'is_not_set',
  'greater_than',
  'less_than',
]
export const VALUELESS = ['is_set', 'is_not_set']
export const SIGNERS = ['patient', 'operator', 'guardian']
export const SIGNATURE_LEVELS = ['simple', 'advanced', 'qualified']
export const COLUMN_TYPES = ['text', 'number', 'date', 'yesno']
export const SIDE_INPUTS = ['number', 'text']

const MAX_SECTIONS = 50
const MAX_FIELDS = 400
const MAX_OPTIONS = 100
const MAX_COLUMNS = 20
const MAX_DECIMALS = 6

const ID = /^[a-z][a-z0-9_]{0,59}$/
const NUMBER_TEXT = /^\s*-?[0-9]+(?:[.,][0-9]+)?\s*$/
const DATE = /^[0-9]{4}-[0-9]{2}-[0-9]{2}$/

// --- what Python calls true ---------------------------------------------------

const isObject = (value) =>
  value !== null && typeof value === 'object' && !Array.isArray(value)

/** Python's truth: `[]`, `{}`, `''`, `0`, `False` and `None` are false. */
export function truthy(value) {
  if (value === null || value === undefined || value === false) return false
  if (value === 0 || value === '') return false
  if (Array.isArray(value)) return value.length > 0
  if (isObject(value)) return Object.keys(value).length > 0
  return true
}

/** Python's `a or b`. */
const or = (value, otherwise) => (truthy(value) ? value : otherwise)

/** `dict.get`: own keys only, `null` for the rest — never `constructor`. */
function get(object, key) {
  if (!isObject(object) || typeof key !== 'string') return null
  return Object.prototype.hasOwnProperty.call(object, key) ? object[key] : null
}

/** A key set as data, even one called `__proto__`. */
function put(object, key, value) {
  Object.defineProperty(object, key, {
    value,
    enumerable: true,
    writable: true,
    configurable: true,
  })
}

const list = (value) => (Array.isArray(value) ? value : [])
const dict = (value) => (isObject(value) ? value : {})
const text = (value) => (typeof value === 'string' ? value.trim() : '')
const validId = (value) => typeof value === 'string' && ID.test(value)

// --- the components -----------------------------------------------------------

const components = new Map()

/**
 * A component: what its answer is (`value`, null for what only shows), whether
 * the person answers it, how a condition may ask about it ('all', 'presence',
 * null), whether calculations may use it, and what it carries.
 */
export function registerComponent(definition) {
  components.set(definition.type, {
    answer: true,
    condition: 'all',
    numeric: false,
    props: [],
    ...definition,
  })
}

export function component(type) {
  return typeof type === 'string' ? components.get(type) || null : null
}

export function componentList() {
  return [...components.values()]
}

for (const definition of [
  {
    type: 'text',
    label: 'Text',
    value: 'text',
    group: 'Questions',
    description: 'A short answer, or a longer one',
    props: ['placeholder', 'multiline', 'phrases'],
  },
  {
    type: 'number',
    label: 'Number',
    value: 'number',
    group: 'Questions',
    description: 'A measure, with its unit',
    numeric: true,
    props: ['placeholder', 'unit', 'min', 'max', 'decimals'],
  },
  {
    type: 'choice',
    label: 'Choice',
    value: 'choice',
    group: 'Questions',
    description: 'One or more from a list, scored if you like',
    props: ['options', 'multiple', 'display'],
  },
  {
    type: 'yesno',
    label: 'Yes or no',
    value: 'bool',
    group: 'Questions',
    description: 'A plain yes or no',
    props: ['scores'],
  },
  {
    type: 'date',
    label: 'Date',
    value: 'date',
    group: 'Questions',
    description: 'A day',
  },
  {
    type: 'scale',
    label: 'Scale',
    value: 'number',
    group: 'Questions',
    description: 'From 0 to 10, or another range',
    numeric: true,
    props: ['min', 'max', 'min_label', 'max_label'],
  },
  {
    type: 'table',
    label: 'Table',
    value: 'table',
    group: 'Questions',
    description: 'Rows to add: medications, past operations',
    condition: 'presence',
    props: ['columns', 'max_rows'],
  },
  {
    type: 'sides',
    label: 'Left and right',
    value: 'sides',
    group: 'Questions',
    description: 'The two sides next to each other',
    condition: 'presence',
    props: ['input', 'unit'],
  },
  {
    type: 'attachment',
    label: 'Attachment',
    value: 'file',
    group: 'Questions',
    description: 'A file: an exam, a photo',
    condition: 'presence',
    props: ['accept', 'multiple'],
  },
  {
    type: 'paragraph',
    label: 'Text to read',
    value: null,
    group: 'Content',
    description: 'A notice, an explanation',
    answer: false,
    condition: null,
    props: ['text'],
  },
  {
    type: 'calc',
    label: 'Calculation',
    value: 'number',
    group: 'Content',
    description: 'Worked out from the numbers before it, like the BMI',
    answer: false,
    numeric: true,
    props: ['formula', 'decimals', 'unit'],
  },
  {
    type: 'score',
    label: 'Score',
    value: 'number',
    group: 'Content',
    description: "A questionnaire's total, with its bands",
    answer: false,
    numeric: true,
    props: ['sources', 'bands'],
  },
  {
    type: 'consent',
    label: 'Consent',
    value: 'bool',
    group: 'Signing',
    description: 'A consent of the register: privacy, marketing',
    props: ['consent_type', 'must_accept', 'text', 'text_version'],
  },
  {
    type: 'signature',
    label: 'Signature',
    value: 'signature',
    group: 'Signing',
    description: 'The patient, the operator or a parent signs',
    condition: 'presence',
    props: ['signer', 'level'],
  },
]) {
  registerComponent(definition)
}

// --- the values ---------------------------------------------------------------

/** Not answered. A "no" is an answer; an empty row or side is not. */
export function isEmpty(value) {
  if (value === null || value === undefined || value === '') return true
  if (Array.isArray(value)) return value.length === 0
  if (isObject(value)) return Object.values(value).every(isEmpty)
  return false
}

/** A number, from a number or from what a person typed ("70", "70,5"). */
export function toNumber(value) {
  if (typeof value === 'boolean' || value === null || value === undefined) {
    return null
  }
  if (typeof value === 'number') return Number.isFinite(value) ? value : null
  if (typeof value === 'string' && NUMBER_TEXT.test(value)) {
    return parseFloat(value.trim().replace(',', '.'))
  }
  return null
}

/** Half up, as the server rounds it: `floor(x * 10^d + 0.5) / 10^d`. */
export function roundHalfUp(x, decimals) {
  const d = Math.max(0, Math.min(Math.trunc(decimals), 10))
  const factor = 10 ** d
  const scaled = x * factor + 0.5
  if (!Number.isFinite(scaled)) return x
  return Math.floor(scaled) / factor
}

// --- the schema ---------------------------------------------------------------

export function sectionsOf(schema) {
  if (!isObject(schema) || !Array.isArray(schema.sections)) return []
  return schema.sections.filter(isObject)
}

export function fieldsOfSection(section) {
  return Array.isArray(section?.fields) ? section.fields.filter(isObject) : []
}

/** Every field, in the order a person meets them. */
export function fieldsOf(schema) {
  return sectionsOf(schema).flatMap(fieldsOfSection)
}

// --- conditions ---------------------------------------------------------------

function asText(value) {
  if (value === null || value === undefined) return ''
  if (typeof value === 'boolean') return value ? '1' : '0'
  // a condition compares single answers: a list has no words to compare
  if (Array.isArray(value) || isObject(value)) return ''
  if (typeof value === 'number' && Number.isFinite(value)) return String(value)
  return String(value).trim()
}

const composite = (value) => Array.isArray(value) || isObject(value)

function same(actual, expected) {
  if (composite(actual) || composite(expected)) return false
  if (typeof actual === 'boolean') return asText(actual) === asText(expected)
  const a = toNumber(actual)
  const b = toNumber(expected)
  if (a !== null && b !== null) return a === b
  return asText(actual) === asText(expected)
}

function order(actual, expected) {
  const a = toNumber(actual)
  const b = toNumber(expected)
  if (a !== null && b !== null) return (a > b) - (a < b)
  if (typeof actual === 'string' && typeof expected === 'string') {
    const x = actual.trim()
    const y = expected.trim()
    if (DATE.test(x) && DATE.test(y)) return (x > y) - (x < y)
  }
  return null
}

export function conditionHolds(condition, values) {
  const operator = or(get(condition, 'operator'), 'equals')
  const actual = get(values, get(condition, 'field'))
  const expected = get(condition, 'value')
  if (operator === 'is_set') return !isEmpty(actual)
  if (operator === 'is_not_set') return isEmpty(actual)
  // nothing answered is not equal, not different, not bigger: the question
  // that depends on it waits for the answer
  if (isEmpty(actual)) return false
  // a condition compares with one value, as the builder writes it
  if (composite(expected)) return false
  if (Array.isArray(actual)) {
    if (operator === 'equals') return actual.some((v) => same(v, expected))
    if (operator === 'not_equals') return !actual.some((v) => same(v, expected))
    if (operator === 'contains') {
      const wanted = asText(expected).toLowerCase()
      return actual.some((v) => asText(v).toLowerCase().includes(wanted))
    }
    return false
  }
  if (operator === 'equals') return same(actual, expected)
  if (operator === 'not_equals') return !same(actual, expected)
  if (operator === 'contains') {
    return asText(actual).toLowerCase().includes(asText(expected).toLowerCase())
  }
  if (operator === 'greater_than' || operator === 'less_than') {
    const result = order(actual, expected)
    if (result === null) return false
    return operator === 'greater_than' ? result > 0 : result < 0
  }
  return false
}

/** The groups with a question in each row: an empty row asks nothing. */
export function cleanConditionGroups(groups) {
  if (!Array.isArray(groups)) return []
  const cleaned = []
  for (const group of groups) {
    if (!Array.isArray(group)) continue
    const rows = group.filter(
      (c) => isObject(c) && typeof c.field === 'string' && c.field,
    )
    if (rows.length) cleaned.push(rows)
  }
  return cleaned
}

/** Any group whose conditions all hold. None or nothing is always. */
export function groupsHold(groups, values) {
  const cleaned = cleanConditionGroups(groups)
  if (!cleaned.length) return true
  return cleaned.some((group) => group.every((c) => conditionHolds(c, values)))
}

// --- formulas -----------------------------------------------------------------

export class FormulaError extends Error {}

const FUNCTIONS = {
  round: [1, 2],
  min: [1, 20],
  max: [1, 20],
  abs: [1, 1],
  sqrt: [1, 1],
}
const SYMBOLS = '+-*/^(),'
const isDigit = (c) => c >= '0' && c <= '9'
const isLetter = (c) => c >= 'a' && c <= 'z'

function tokens(formula) {
  const found = []
  let i = 0
  while (i < formula.length) {
    const c = formula[i]
    if (/\s/.test(c)) {
      i += 1
      continue
    }
    if (isDigit(c)) {
      let end = i
      while (end < formula.length && isDigit(formula[end])) end += 1
      if (
        end < formula.length - 1 &&
        formula[end] === '.' &&
        isDigit(formula[end + 1])
      ) {
        end += 1
        while (end < formula.length && isDigit(formula[end])) end += 1
      }
      found.push(['num', formula.slice(i, end)])
      i = end
      continue
    }
    if (isLetter(c)) {
      let end = i
      while (
        end < formula.length &&
        (isLetter(formula[end]) || isDigit(formula[end]) || formula[end] === '_')
      ) {
        end += 1
      }
      found.push(['name', formula.slice(i, end)])
      i = end
      continue
    }
    if (SYMBOLS.includes(c)) {
      found.push(['symbol', c])
      i += 1
      continue
    }
    throw new FormulaError(`unexpected '${c}'`)
  }
  return found
}

class Reader {
  constructor(found) {
    this.found = found
    this.i = 0
  }
  peek() {
    return this.found[this.i] || [null, null]
  }
  is(symbol) {
    const [kind, value] = this.peek()
    return kind === 'symbol' && value === symbol
  }
  take() {
    const token = this.peek()
    this.i += 1
    return token
  }
  expect(symbol) {
    const [kind, value] = this.take()
    if (kind !== 'symbol' || value !== symbol) {
      throw new FormulaError(`expected '${symbol}'`)
    }
  }
  // expression := term (("+" | "-") term)*
  expression() {
    let node = this.term()
    while (this.is('+') || this.is('-')) {
      const operator = this.take()[1]
      node = ['bin', operator, node, this.term()]
    }
    return node
  }
  // term := unary (("*" | "/") unary)*
  term() {
    let node = this.unary()
    while (this.is('*') || this.is('/')) {
      const operator = this.take()[1]
      node = ['bin', operator, node, this.unary()]
    }
    return node
  }
  // unary := "-" unary | power   (so -2^2 is -(2^2), as on paper)
  unary() {
    if (this.is('-')) {
      this.take()
      return ['neg', this.unary()]
    }
    return this.power()
  }
  // power := primary ("^" unary)?   (right-associative)
  power() {
    const node = this.primary()
    if (this.is('^')) {
      this.take()
      return ['bin', '^', node, this.unary()]
    }
    return node
  }
  primary() {
    const [kind, value] = this.take()
    if (kind === 'num') return ['num', parseFloat(value)]
    if (kind === 'name') {
      if (this.is('(')) {
        if (!Object.prototype.hasOwnProperty.call(FUNCTIONS, value)) {
          throw new FormulaError(`unknown function ${value}`)
        }
        this.take()
        const args = [this.expression()]
        while (this.is(',')) {
          this.take()
          args.push(this.expression())
        }
        this.expect(')')
        const [least, most] = FUNCTIONS[value]
        if (args.length < least || args.length > most) {
          throw new FormulaError(`${value} takes ${least} to ${most} values`)
        }
        return ['fn', value, args]
      }
      return ['var', value]
    }
    if (kind === 'symbol' && value === '(') {
      const node = this.expression()
      this.expect(')')
      return node
    }
    throw new FormulaError('incomplete formula')
  }
}

/** The formula as a tree; throws FormulaError when it is not one. */
export function parseFormula(formula) {
  if (typeof formula !== 'string' || !formula.trim()) {
    throw new FormulaError('empty formula')
  }
  if (formula.length > 500) throw new FormulaError('formula too long')
  const reader = new Reader(tokens(formula))
  const tree = reader.expression()
  if (reader.i !== reader.found.length) {
    throw new FormulaError('unexpected text after the formula')
  }
  return tree
}

export function formulaReferences(tree) {
  if (tree[0] === 'var') return [tree[1]]
  if (tree[0] === 'neg') return formulaReferences(tree[1])
  if (tree[0] === 'bin') {
    return [...formulaReferences(tree[2]), ...formulaReferences(tree[3])]
  }
  if (tree[0] === 'fn') return tree[2].flatMap(formulaReferences)
  return []
}

const finite = (x) => (Number.isFinite(x) ? x : null)

function compute(tree, values) {
  const kind = tree[0]
  if (kind === 'num') return tree[1]
  if (kind === 'var') return toNumber(get(values, tree[1]))
  if (kind === 'neg') {
    const x = compute(tree[1], values)
    return x === null ? null : -x
  }
  if (kind === 'bin') {
    const a = compute(tree[2], values)
    const b = compute(tree[3], values)
    if (a === null || b === null) return null
    const operator = tree[1]
    if (operator === '+') return finite(a + b)
    if (operator === '-') return finite(a - b)
    if (operator === '*') return finite(a * b)
    if (operator === '/') return b === 0 ? null : finite(a / b)
    return finite(Math.pow(a, b))
  }
  const args = tree[2].map((arg) => compute(arg, values))
  if (args.some((x) => x === null)) return null
  const name = tree[1]
  if (name === 'round') {
    return roundHalfUp(args[0], args.length > 1 ? Math.trunc(args[1]) : 0)
  }
  if (name === 'min') return Math.min(...args)
  if (name === 'max') return Math.max(...args)
  if (name === 'abs') return Math.abs(args[0])
  return args[0] >= 0 ? Math.sqrt(args[0]) : null
}

/**
 * What the formula gives with these answers; null while something it uses is
 * missing, or when it has no answer (a division by zero).
 */
export function computeFormula(formula, values, decimals = null) {
  let result
  try {
    result = compute(parseFormula(formula), values)
  } catch (error) {
    if (error instanceof FormulaError) return null
    throw error
  }
  if (result === null) return null
  const d = toNumber(decimals)
  return roundHalfUp(result, d === null ? 2 : d)
}

// --- scores -------------------------------------------------------------------

function pointsOf(field, value) {
  const type = get(field, 'type')
  if (type === 'choice') {
    const points = new Map()
    for (const option of list(get(field, 'options'))) {
      if (isObject(option) && typeof get(option, 'label') === 'string') {
        points.set(option.label, toNumber(get(option, 'score')) || 0)
      }
    }
    const picked = Array.isArray(value) ? value : [value]
    return picked.reduce(
      (total, v) =>
        total + (typeof v === 'string' ? (points.get(v) ?? 0) : 0),
      0,
    )
  }
  if (type === 'yesno') {
    const scores = dict(get(field, 'scores'))
    return toNumber(get(scores, truthy(value) ? 'yes' : 'no')) || 0
  }
  return toNumber(value)
}

/** The sum of the answers it counts; null while one it counts is missing. */
export function scoreOf(field, values, visible, byId) {
  let total = 0
  let counted = 0
  for (const source of list(get(field, 'sources'))) {
    if (typeof source !== 'string' || !get(visible, source) || !byId.has(source)) {
      continue
    }
    const value = get(values, source)
    if (isEmpty(value)) return null
    const points = pointsOf(byId.get(source), value)
    if (points === null) return null
    total += points
    counted += 1
  }
  return counted ? roundHalfUp(total, 2) : null
}

export function bandOf(field, total) {
  if (total === null) return null
  for (const band of list(get(field, 'bands'))) {
    if (!isObject(band)) continue
    const from = toNumber(get(band, 'from'))
    const to = toNumber(get(band, 'to'))
    if (from !== null && to !== null && from <= total && total <= to) {
      return or(get(band, 'label'), null)
    }
  }
  return null
}

// --- evaluation ---------------------------------------------------------------

/**
 * What these answers mean for the schema: what shows, what is worked out, what
 * is required and missing, where to stop and tell the operator.
 */
export function evaluate(schema, values) {
  values = or(values, {})
  const byId = new Map()
  // the last of a key wins, as a Python dict built from the list keeps it
  for (const field of fieldsOf(schema)) {
    if (typeof field.id === 'string') byId.set(field.id, field)
  }
  const effective = {}
  const visible = {}
  const sections = {}
  const bands = {}
  for (const section of sectionsOf(schema)) {
    const shown = groupsHold(get(section, 'show_if'), effective)
    if (typeof section.id === 'string') put(sections, section.id, shown)
    for (const field of fieldsOfSection(section)) {
      const key = field.id
      if (typeof key !== 'string') continue
      const kind = component(field.type)
      const seen = shown && groupsHold(get(field, 'show_if'), effective)
      put(visible, key, seen)
      let value = null
      if (seen && kind && kind.value !== null) {
        if (field.type === 'calc') {
          value = computeFormula(get(field, 'formula'), effective, get(field, 'decimals'))
        } else if (field.type === 'score') {
          value = scoreOf(field, effective, visible, byId)
          put(bands, key, bandOf(field, value))
        } else {
          value = get(values, key)
        }
      }
      put(effective, key, value)
    }
  }

  const required = []
  const missing = []
  const stops = []
  for (const field of fieldsOf(schema)) {
    const key = field.id
    const kind = component(field.type)
    if (typeof key !== 'string' || !get(visible, key) || !kind) continue
    if (
      kind.answer &&
      (truthy(get(field, 'required')) ||
        truthy(get(field, 'must_accept')) ||
        (truthy(get(field, 'required_if')) &&
          groupsHold(get(field, 'required_if'), effective)))
    ) {
      required.push(key)
      const value = get(effective, key)
      if (isEmpty(value) || (truthy(get(field, 'must_accept')) && value !== true)) {
        missing.push(key)
      }
    }
    if (truthy(get(field, 'stop_if')) && groupsHold(get(field, 'stop_if'), effective)) {
      stops.push({ field: key, message: or(get(field, 'stop_message'), '') })
    }
  }
  return { values: effective, sections, visible, required, missing, stops, bands }
}

// --- validation ---------------------------------------------------------------

const problem = (code, field, message, args = []) => ({ code, field, message, args })

function isGroups(groups) {
  return (
    groups === null ||
    groups === undefined ||
    (Array.isArray(groups) &&
      groups.every((g) => Array.isArray(g) && g.every(isObject)))
  )
}

function checkConditions(found, groups, where, before, all, onlyBefore, label) {
  if (groups === null || groups === undefined) return
  if (Array.isArray(groups) && groups.length === 0) return
  if (!isGroups(groups)) {
    found.push(problem('invalid_condition', where, '{0}: the condition is not valid', [label]))
    return
  }
  for (const group of groups) {
    for (const condition of group) {
      const name = get(condition, 'field')
      if (typeof name !== 'string' || !name) continue
      const operator = or(get(condition, 'operator'), 'equals')
      if (!OPERATORS.includes(operator)) {
        found.push(
          problem('invalid_operator', where, '{0}: unknown operator {1}', [label, operator]),
        )
        continue
      }
      const target = (onlyBefore ? before : all).get(name)
      if (!target) {
        const later = onlyBefore && all.has(name)
        found.push(
          later
            ? problem(
                'later_reference',
                where,
                '{0}: a condition can only use the questions before it ({1})',
                [label, name],
              )
            : problem(
                'unknown_reference',
                where,
                '{0}: the condition uses {1}, which is not in the form',
                [label, name],
              ),
        )
        continue
      }
      const kind = component(target.type)
      if (!kind || kind.condition === null) {
        found.push(
          problem('invalid_condition', where, '{0}: {1} cannot be asked about', [label, name]),
        )
      } else if (kind.condition === 'presence' && !VALUELESS.includes(operator)) {
        found.push(
          problem(
            'invalid_operator',
            where,
            '{0}: of {1} one can only ask whether it was given',
            [label, name],
          ),
        )
      }
    }
  }
}

const hasValue = (value) => value !== null && value !== undefined && value !== ''

function checkField(found, field, before, all) {
  const key = validId(field.id) ? field.id : null
  const kind = component(field.type)
  const label = text(field.label) || key || ''
  if (!kind) {
    found.push(
      problem('unknown_type', key, '{0}: unknown kind of field {1}', [label, field.type]),
    )
    return
  }
  if (kind.value !== null && !text(field.label)) {
    found.push(problem('missing_label', key, 'A question needs its words ({0})', [key]))
  }
  const type = field.type
  if (type === 'number' || type === 'scale') {
    let least = toNumber(get(field, 'min'))
    let most = toNumber(get(field, 'max'))
    if (type === 'scale') {
      least = least === null ? 0 : least
      most = most === null ? 10 : most
      if (
        !(
          Number.isInteger(least) &&
          Number.isInteger(most) &&
          least < most &&
          most - least <= 100
        )
      ) {
        found.push(
          problem('invalid_scale', key, '{0}: a scale goes up in whole steps, at most 100', [
            label,
          ]),
        )
      }
    } else if (least !== null && most !== null && least > most) {
      found.push(problem('min_above_max', key, '{0}: the least is above the most', [label]))
    }
  }
  if ((type === 'number' || type === 'calc') && get(field, 'decimals') !== null) {
    const d = toNumber(get(field, 'decimals'))
    if (d === null || !Number.isInteger(d) || d < 0 || d > MAX_DECIMALS) {
      found.push(problem('invalid_decimals', key, '{0}: decimals go from 0 to 6', [label]))
    }
  }
  if (type === 'choice') {
    const options = get(field, 'options')
    if (!Array.isArray(options) || !options.length) {
      found.push(problem('missing_options', key, '{0}: a choice needs its options', [label]))
    } else {
      const seen = new Set()
      for (const option of options.slice(0, MAX_OPTIONS + 1)) {
        const words = isObject(option) ? text(option.label) : ''
        if (!words || seen.has(words)) {
          found.push(
            problem('duplicate_option', key, '{0}: every option has its own words', [label]),
          )
          break
        }
        seen.add(words)
        const score = get(option, 'score')
        if (hasValue(score) && toNumber(score) === null) {
          found.push(problem('invalid_score', key, '{0}: a score is a number', [label]))
          break
        }
      }
      if (options.length > MAX_OPTIONS) {
        found.push(problem('too_many', key, '{0}: at most {1} options', [label, MAX_OPTIONS]))
      }
    }
  }
  if (type === 'yesno') {
    const scores = or(get(field, 'scores'), {})
    if (
      !isObject(scores) ||
      Object.values(scores).some((v) => hasValue(v) && toNumber(v) === null)
    ) {
      found.push(problem('invalid_score', key, '{0}: a score is a number', [label]))
    }
  }
  if (type === 'table') {
    const columns = get(field, 'columns')
    if (!Array.isArray(columns) || !columns.length) {
      found.push(problem('missing_columns', key, '{0}: a table needs its columns', [label]))
    } else {
      const seen = new Set()
      for (const column of columns) {
        const ok =
          isObject(column) &&
          validId(column.id) &&
          !seen.has(column.id) &&
          text(column.label) &&
          COLUMN_TYPES.includes(or(get(column, 'type'), 'text'))
        if (!ok) {
          found.push(problem('invalid_column', key, '{0}: a column is not valid', [label]))
          break
        }
        seen.add(column.id)
      }
      if (columns.length > MAX_COLUMNS) {
        found.push(problem('too_many', key, '{0}: at most {1} columns', [label, MAX_COLUMNS]))
      }
    }
  }
  if (type === 'paragraph' && !text(field.text)) {
    found.push(problem('missing_text', key, 'A text to read needs its words ({0})', [key]))
  }
  if (type === 'calc') {
    let used = []
    try {
      // once each: "a * a" is one question used twice
      used = [...new Set(formulaReferences(parseFormula(get(field, 'formula'))))]
    } catch (error) {
      if (!(error instanceof FormulaError)) throw error
      found.push(
        problem('invalid_formula', key, '{0}: the formula is not valid ({1})', [
          label,
          error.message,
        ]),
      )
    }
    for (const name of used) {
      if (!before.has(name)) {
        found.push(
          all.has(name)
            ? problem(
                'later_reference',
                key,
                '{0}: a calculation can only use the questions before it ({1})',
                [label, name],
              )
            : problem(
                'unknown_reference',
                key,
                '{0}: the formula uses {1}, which is not in the form',
                [label, name],
              ),
        )
      } else if (!component(before.get(name).type)?.numeric) {
        found.push(
          problem('not_a_number_reference', key, '{0}: {1} is not a number', [label, name]),
        )
      }
    }
  }
  if (type === 'score') {
    const sources = get(field, 'sources')
    if (!Array.isArray(sources) || !sources.length) {
      found.push(problem('missing_sources', key, '{0}: a score counts some questions', [label]))
    } else {
      for (const source of sources) {
        const target = typeof source === 'string' ? before.get(source) : null
        if (!target || !['choice', 'yesno', 'scale', 'number'].includes(target.type)) {
          found.push(
            problem(
              'invalid_source',
              key,
              '{0}: a score counts choices, yes or no, scales and numbers before it ({1})',
              [label, source],
            ),
          )
        }
      }
    }
    for (const band of list(get(field, 'bands'))) {
      const from = isObject(band) ? toNumber(band.from) : null
      const to = isObject(band) ? toNumber(band.to) : null
      if (from === null || to === null || from > to || !text(band.label)) {
        found.push(
          problem(
            'invalid_band',
            key,
            '{0}: a band goes from a number to a bigger one, with a name',
            [label],
          ),
        )
        break
      }
    }
  }
  if (type === 'sides' && !SIDE_INPUTS.includes(or(get(field, 'input'), 'number'))) {
    found.push(
      problem('invalid_sides_input', key, '{0}: each side is a number or a text', [label]),
    )
  }
  if (type === 'signature') {
    if (!SIGNERS.includes(or(get(field, 'signer'), 'patient'))) {
      found.push(problem('invalid_signer', key, '{0}: who signs is not valid', [label]))
    }
    if (!SIGNATURE_LEVELS.includes(or(get(field, 'level'), 'simple'))) {
      found.push(
        problem(
          'invalid_signature_level',
          key,
          '{0}: the level of the signature is not valid',
          [label],
        ),
      )
    }
  }
  if (type === 'consent' && !text(field.consent_type)) {
    found.push(
      problem('missing_consent_type', key, '{0}: which consent it records', [label]),
    )
  }
  checkConditions(found, get(field, 'show_if'), key, before, all, true, label)
  checkConditions(found, get(field, 'required_if'), key, before, all, false, label)
  checkConditions(found, get(field, 'stop_if'), key, before, all, false, label)
}

/** What is wrong with a schema: nothing, or the list, each with its field. */
export function validateSchema(schema) {
  if (!isObject(schema) || !Array.isArray(schema.sections)) {
    return [problem('not_a_schema', null, 'This is not a form')]
  }
  const found = []
  if (schema.sections.length > MAX_SECTIONS) {
    found.push(problem('too_many', null, 'At most {0} sections', [MAX_SECTIONS]))
  }
  const all = new Map()
  for (const field of fieldsOf(schema)) {
    if (validId(field.id) && !all.has(field.id)) all.set(field.id, field)
  }
  if (fieldsOf(schema).length > MAX_FIELDS) {
    found.push(problem('too_many', null, 'At most {0} fields', [MAX_FIELDS]))
  }
  const before = new Map()
  const sectionIds = new Set()
  const fieldIds = new Set()
  for (const section of schema.sections) {
    if (!isObject(section)) {
      found.push(problem('not_a_schema', null, 'This is not a form'))
      continue
    }
    const key = validId(section.id) ? section.id : null
    if (key === null || sectionIds.has(key)) {
      found.push(problem('invalid_id', key, 'Every section has its own key ({0})', [key || '']))
    }
    sectionIds.add(key)
    if ('fields' in section && !Array.isArray(section.fields)) {
      found.push(problem('not_a_schema', key, 'This is not a form'))
    }
    checkConditions(
      found,
      get(section, 'show_if'),
      key,
      before,
      all,
      true,
      text(section.title) || key,
    )
    for (const field of fieldsOfSection(section)) {
      const fieldKey = validId(field.id) ? field.id : null
      if (fieldKey === null || fieldIds.has(fieldKey)) {
        found.push(
          problem(
            'invalid_id',
            fieldKey,
            'Every question has its own key: lowercase letters, digits and _ ({0})',
            [fieldKey || ''],
          ),
        )
      }
      checkField(found, field, before, all)
      if (fieldKey !== null) {
        fieldIds.add(fieldKey)
        if (!before.has(fieldKey)) before.set(fieldKey, field)
      }
    }
  }
  return found
}

/** A version people will fill: valid, and with at least one question. */
export function readyToPublish(schema) {
  const found = validateSchema(schema)
  if (!fieldsOf(schema).some((field) => component(field.type)?.answer)) {
    found.push(problem('empty', null, 'A form asks something: add a question'))
  }
  return found
}

// --- the builder --------------------------------------------------------------

/** A key from words: "Peso (kg)" → "peso_kg", unique among `taken`. */
export function keyFromLabel(label, taken = new Set(), fallback = 'field') {
  const base =
    String(label || '')
      .normalize('NFD')
      .replace(/[̀-ͯ]/g, '')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '_')
      .replace(/^_+|_+$/g, '')
      .replace(/^[0-9_]+/, '')
      .slice(0, 50) || fallback
  let key = base
  let n = 2
  while (taken.has(key)) key = `${base}_${n++}`
  return key
}

export function takenKeys(schema) {
  return new Set(fieldsOf(schema).map((field) => field.id))
}

const DEFAULTS = {
  choice: () => ({
    options: [{ label: __('Option 1') }, { label: __('Option 2') }],
  }),
  scale: () => ({ min: 0, max: 10 }),
  table: () => ({ columns: [{ id: 'column_1', label: __('Column 1'), type: 'text' }] }),
  calc: () => ({ formula: '', decimals: 1 }),
  score: () => ({ sources: [], bands: [] }),
  sides: () => ({ input: 'number' }),
  signature: () => ({ signer: 'patient', level: 'simple', required: true }),
  consent: () => ({ consent_type: '' }),
  paragraph: () => ({ text: '' }),
}

/** A new field of `type`, with a key nobody in the schema has. */
export function newField(type, schema, label = '') {
  const kind = component(type)
  const field = {
    id: keyFromLabel(label || kind?.label || type, takenKeys(schema)),
    type,
    ...(kind?.value !== null ? { label } : {}),
    ...(DEFAULTS[type]?.() || {}),
  }
  return field
}

export function newSection(schema, title = '') {
  const taken = new Set(sectionsOf(schema).map((section) => section.id))
  return { id: keyFromLabel(title, taken, 'section'), title, fields: [] }
}

function renameInGroups(groups, from, to) {
  for (const group of list(groups)) {
    for (const condition of list(group)) {
      if (isObject(condition) && condition.field === from) condition.field = to
    }
  }
}

/** A formula with one name changed, and nothing else touched. */
export function renameInFormula(formula, from, to) {
  if (typeof formula !== 'string') return formula
  return formula.replace(/[a-z][a-z0-9_]*/g, (name, offset) => {
    // part of a longer name, or a function: left alone
    const previous = formula[offset - 1]
    if (previous && /[a-z0-9_]/.test(previous)) return name
    return name === from ? to : name
  })
}

/**
 * Change a field's key everywhere it is used: conditions, formulas, scores.
 * Returns false (and changes nothing) when the new key is not valid or taken.
 */
export function renameKey(schema, from, to) {
  if (!validId(to) || from === to || takenKeys(schema).has(to)) return false
  for (const section of sectionsOf(schema)) {
    renameInGroups(section.show_if, from, to)
    for (const field of fieldsOfSection(section)) {
      if (field.id === from) field.id = to
      renameInGroups(field.show_if, from, to)
      renameInGroups(field.required_if, from, to)
      renameInGroups(field.stop_if, from, to)
      if (field.type === 'calc') field.formula = renameInFormula(field.formula, from, to)
      if (Array.isArray(field.sources)) {
        field.sources = field.sources.map((source) => (source === from ? to : source))
      }
    }
  }
  return true
}

/** Where a key is used: what would break if the field went. */
export function usesOf(schema, key) {
  const uses = []
  const inGroups = (groups) =>
    cleanConditionGroups(groups).some((group) => group.some((c) => c.field === key))
  for (const section of sectionsOf(schema)) {
    if (inGroups(section.show_if)) uses.push({ section: section.id })
    for (const field of fieldsOfSection(section)) {
      if (field.id === key) continue
      let used = inGroups(field.show_if) || inGroups(field.required_if) || inGroups(field.stop_if)
      if (field.type === 'calc') {
        try {
          used = used || formulaReferences(parseFormula(field.formula)).includes(key)
        } catch {
          // a formula being written uses nothing yet
        }
      }
      if (list(field.sources).includes(key)) used = true
      if (used) uses.push({ field: field.id })
    }
  }
  return uses
}

/** The fields before `key` (or before a section, or all): what it may look at. */
export function fieldsBefore(schema, { field = null, section = null } = {}) {
  const found = []
  for (const s of sectionsOf(schema)) {
    if (section !== null && s.id === section) return found
    for (const f of fieldsOfSection(s)) {
      if (field !== null && f.id === field) return found
      found.push(f)
    }
  }
  return found
}

/**
 * Fields a condition may ask about, the way the automations' condition builder
 * wants them: a fieldname, a label and a Frappe fieldtype for its value input.
 */
export function conditionFields(fields) {
  return fields
    .filter((field) => component(field.type)?.condition)
    .map((field) => {
      const kind = component(field.type)
      let fieldtype = 'Data'
      let options = ''
      if (kind.condition === 'presence') fieldtype = 'Attach'
      else if (kind.numeric) fieldtype = 'Float'
      else if (kind.value === 'bool') fieldtype = 'Check'
      else if (field.type === 'date') fieldtype = 'Date'
      else if (field.type === 'choice') {
        fieldtype = 'Select'
        options = list(field.options)
          .map((option) => option?.label)
          .filter(Boolean)
          .join('\n')
      }
      return {
        fieldname: field.id,
        label: field.label || field.id,
        fieldtype,
        options,
      }
    })
}

/** How many sections and questions: for the list of templates. */
export function schemaCounts(schema) {
  return {
    sections: sectionsOf(schema).length,
    questions: fieldsOf(schema).filter((field) => component(field.type)?.answer).length,
  }
}

/**
 * An answer as a person reads it on paper: the signed form shows it this way,
 * as its PDF does (`crm/moduli/pdf.py`, `risposta_in_parole`).
 */
export function answerInWords(field, value, band = null) {
  if (isEmpty(value)) return ''
  const unit = (text) => (field.unit ? `${text} ${field.unit}` : String(text))
  switch (field.type) {
    case 'number':
    case 'calc':
      return unit(value)
    case 'score':
      return band ? `${value} · ${band}` : String(value)
    case 'yesno':
      return value ? __('Yes') : __('No')
    case 'consent':
      return value ? __('Agreed') : __('Did not agree')
    case 'choice':
      return Array.isArray(value) ? value.join(', ') : String(value)
    case 'scale': {
      const ends = [field.min_label, field.max_label].filter(Boolean).join(' – ')
      return ends ? `${value} (${ends})` : String(value)
    }
    case 'sides': {
      const parts = []
      if (!isEmpty(value.left)) parts.push(__('Left: {0}', [unit(value.left)]))
      if (!isEmpty(value.right)) parts.push(__('Right: {0}', [unit(value.right)]))
      return parts.join(' · ')
    }
    case 'attachment':
      return (Array.isArray(value) ? value : [value])
        .map((file) => String(file).split('/').pop())
        .join(', ')
    default:
      return String(value)
  }
}
