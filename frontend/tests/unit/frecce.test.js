// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// The arrows in a form's single choice (Moduli/FormFieldInput.vue), drawn as a
// radio group: one stop of the Tab key, and the arrows move and pick.
import { describe, expect, it } from 'vitest'
import { dopoLaFreccia } from '@/utils/frecce'

describe('the arrows in a group of options', () => {
  it('go to the next and to the one before, round the ends', () => {
    expect(dopoLaFreccia('ArrowDown', 0, 3)).toBe(1)
    expect(dopoLaFreccia('ArrowRight', 1, 3)).toBe(2)
    expect(dopoLaFreccia('ArrowDown', 2, 3)).toBe(0)
    expect(dopoLaFreccia('ArrowUp', 2, 3)).toBe(1)
    expect(dopoLaFreccia('ArrowLeft', 0, 3)).toBe(2)
    expect(dopoLaFreccia('ArrowUp', 0, 1)).toBe(0)
  })

  it('take Home and End to the first and the last', () => {
    expect(dopoLaFreccia('Home', 2, 4)).toBe(0)
    expect(dopoLaFreccia('End', 0, 4)).toBe(3)
  })

  it('leave every other key to the browser', () => {
    for (const tasto of ['Tab', 'Enter', ' ', 'a', 'PageDown', 'constructor']) {
      expect(dopoLaFreccia(tasto, 1, 3), tasto).toBeUndefined()
    }
  })

  it('move nothing from a key pressed outside the options', () => {
    expect(dopoLaFreccia('ArrowDown', -1, 3)).toBeUndefined()
    expect(dopoLaFreccia('ArrowDown', 0, 0)).toBeUndefined()
  })
})
