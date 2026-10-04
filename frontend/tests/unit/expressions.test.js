// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// An expression compiled once is still evaluated on each call's values
// (src/utils/expressions.js)
import { _eval, evaluateDependsOnValue } from '@/utils/expressions'

describe('an expression evaluated again', () => {
  it('reads the values of each call, not the first', () => {
    const quando = 'eval:doc.status == "Open"'
    expect(evaluateDependsOnValue(quando, { status: 'Open' })).toBe(true)
    expect(evaluateDependsOnValue(quando, { status: 'Closed' })).toBe(false)
    expect(_eval('a + b', { a: 1, b: 2 })).toBe(3)
    expect(_eval('a + b', { a: 5, b: 2 })).toBe(7)
  })

  it('takes the same words with other names as another expression', () => {
    expect(_eval('a - b', { a: 10, b: 1 })).toBe(9)
    expect(_eval('a - b', { b: 10, a: 1 })).toBe(-9)
  })

  it('still fails on a broken expression, every time', () => {
    vi.spyOn(console, 'log').mockImplementation(() => {})
    vi.spyOn(console, 'error').mockImplementation(() => {})
    expect(() => _eval('doc.', { doc: {} })).toThrow()
    expect(() => _eval('doc.', { doc: {} })).toThrow()
    expect(evaluateDependsOnValue('eval:doc.', { a: 1 })).toBe(true)
  })
})
