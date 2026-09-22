// The translator is the one function every screen calls, so a throw in it is
// never a small bug: it happens inside a render function, and Vue answers a
// throw in a render function with a blank page. A forgotten second argument
// used to do exactly that — and the stack trace pointed at translation.js
// rather than at the component that forgot it.
vi.mock('frappe-ui', () => ({ getConfig: () => translations }))

import translationPlugin from '@/translation'

let translations = {}
let __

beforeEach(() => {
  translations = {}
  translationPlugin({ config: { globalProperties: {} } })
  __ = window.__
})

describe('__ with placeholders', () => {
  it('fills them from the array', () => {
    expect(__('{0} seats', [4])).toBe('4 seats')
    expect(__('{0} of {1}', [2, 7])).toBe('2 of 7')
  })

  it('does not throw when the caller forgot the array', () => {
    // This is the whole point: wrong on screen beats a page that never renders.
    expect(() => __('{0} seats')).not.toThrow()
    expect(__('{0} seats')).toBe('{0} seats')
  })

  it('accepts a bare value, because half the call sites pass one', () => {
    expect(__('{0} seats', 4)).toBe('4 seats')
  })

  it('leaves a placeholder nobody supplied', () => {
    expect(__('{0} of {1}', [2])).toBe('2 of {1}')
  })

  it('keeps a zero, which is a value and not an absence', () => {
    expect(__('{0} seats', [0])).toBe('0 seats')
  })

  it('substitutes into the translation, not into the source string', () => {
    translations = { '{0} seats': '{0} posti' }
    expect(__('{0} seats', [4])).toBe('4 posti')
  })
})

describe('__ without placeholders', () => {
  it('returns the translation untouched', () => {
    translations = { Save: 'Salva' }
    expect(__('Save')).toBe('Salva')
  })

  it('returns the message when there is no translation', () => {
    expect(__('Save')).toBe('Save')
  })

  it('prefers a context-specific translation', () => {
    translations = { Save: 'Salva', 'Save:button': 'Conferma' }
    expect(__('Save', null, 'button')).toBe('Conferma')
  })
})
