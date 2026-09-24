import { describe, expect, it } from 'vitest'
import { hhmm } from '../../src/utils/scheduler'

describe('hhmm', () => {
  it('pads the hour Frappe sends without a leading zero', () => {
    expect(hhmm('9:00:00')).toBe('09:00')
    expect(hhmm('9:30')).toBe('09:30')
  })
  it('keeps a well formed time', () => {
    expect(hhmm('18:45:00')).toBe('18:45')
    expect(hhmm('00:00')).toBe('00:00')
  })
  it('gives an empty string for nothing or nonsense', () => {
    expect(hhmm(null)).toBe('')
    expect(hhmm(undefined)).toBe('')
    expect(hhmm('')).toBe('')
    expect(hhmm('None')).toBe('')
    expect(hhmm('25:00')).toBe('')
  })
})
