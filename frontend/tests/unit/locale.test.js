import { afterEach, describe, expect, it } from 'vitest'
import { appLocale } from '@/utils/locale'

describe('appLocale', () => {
  afterEach(() => {
    delete window.lang
  })

  it('speaks the language the boot says the user reads', () => {
    window.lang = 'it'
    expect(appLocale()).toBe('it')
    expect(
      new Intl.DateTimeFormat(appLocale(), { month: 'long' }).format(
        new Date(2026, 8, 1),
      ),
    ).toBe('settembre')
  })

  it('takes a region too, and the POSIX spelling of it', () => {
    expect(appLocale('en-US')).toBe('en-US')
    expect(appLocale('pt_BR')).toBe('pt-BR')
  })

  it('leaves it to the browser when there is nothing to go on', () => {
    expect(appLocale()).toBeUndefined()
    expect(appLocale('')).toBeUndefined()
    expect(appLocale(null)).toBeUndefined()
  })

  it('leaves it to the browser rather than throw on a code Intl cannot read', () => {
    expect(appLocale('not a language!')).toBeUndefined()
    expect(
      () => new Intl.DateTimeFormat(appLocale('not a language!')),
    ).not.toThrow()
  })
})
