import { afterEach, describe, expect, it } from 'vitest'
import { appLocale, conLApostrofo, inFrase } from '@/utils/locale'

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
    expect(appLocale('pt_BR')).toBe('pt-BR')
    expect(appLocale('it_IT')).toBe('it-IT')
  })

  it('writes English the way Europe does: the day first, the 24-hour clock', () => {
    expect(appLocale('en')).toBe('en-GB')
    expect(appLocale('en-US')).toBe('en-GB')
    const giorno = new Date(2026, 9, 5, 14, 30)
    expect(
      new Intl.DateTimeFormat(appLocale('en'), {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
      }).format(giorno),
    ).toBe('05/10/2026')
    expect(
      new Intl.DateTimeFormat(appLocale('en'), {
        hour: '2-digit',
        minute: '2-digit',
      }).format(giorno),
    ).toBe('14:30')
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

describe('inFrase', () => {
  it('lowers a name written with a capital, as after «Aggiungi»', () => {
    expect(inFrase('Codice fiscale')).toBe('codice fiscale')
    expect(inFrase('Città')).toBe('città')
    expect(inFrase('Partita IVA')).toBe('partita IVA')
  })

  it('keeps acronyms, abbreviations and a capital inside as written', () => {
    for (const comeScritto of [
      'IVA',
      'PEC',
      'CAP',
      'N. di dipendenti',
      'WhatsApp',
      'X',
      '',
    ]) {
      expect(inFrase(comeScritto)).toBe(comeScritto)
    }
    expect(inFrase(undefined)).toBe('')
  })
})

describe('conLApostrofo', () => {
  it('drops the vowel before a day read with one, in Italian', () => {
    expect(conLApostrofo('Paziente dal 11 set 2026', 'it')).toBe(
      "Paziente dall'11 set 2026",
    )
    expect(conLApostrofo('Ultima visita il 1 ott 2026', 'it')).toBe(
      "Ultima visita l'1 ott 2026",
    )
    expect(conLApostrofo('fino al 8 novembre', 'it')).toBe(
      "fino all'8 novembre",
    )
    expect(conLApostrofo('Il 11/10 è chiuso', 'it')).toBe("L'11/10 è chiuso")
    expect(conLApostrofo('la seduta del 1 ott', 'it')).toBe(
      "la seduta dell'1 ott",
    )
    // Italy's format writes the day with its zero, a site's may write it with dashes
    expect(conLApostrofo('fino al 08/10/2026', 'it')).toBe(
      "fino all'08/10/2026",
    )
    expect(conLApostrofo('dal 01-10-2026', 'it')).toBe("dall'01-10-2026")
  })

  it('leaves alone every other number, word and language', () => {
    // a day read with a consonant keeps its article
    expect(conLApostrofo('Paziente dal 7 set 2026', 'it')).toBe(
      'Paziente dal 7 set 2026',
    )
    expect(conLApostrofo('il 18 ott', 'it')).toBe('il 18 ott')
    expect(conLApostrofo('il 09/10/2026', 'it')).toBe('il 09/10/2026')
    expect(conLApostrofo('dal 10/01/2026', 'it')).toBe('dal 10/01/2026')
    // not a date
    expect(conLApostrofo('il 1 di 10', 'it')).toBe('il 1 di 10')
    expect(conLApostrofo('al 8%', 'it')).toBe('al 8%')
    // inside a word
    expect(conLApostrofo('Brasil 1 ott', 'it')).toBe('Brasil 1 ott')
    expect(conLApostrofo('Client since 1 Oct', 'en')).toBe('Client since 1 Oct')
    expect(conLApostrofo(null, 'it')).toBe(null)
  })
})
