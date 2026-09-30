// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// The product's brand - the vertical's (crm.marchio) - as the pages wear it:
// its name in the sentences that say "{brand}", its colours as CSS variables,
// its icons in the head. The centre's logo is only ever beside it.
import {
  DI_RISERVA,
  conMarchio,
  indossa,
  marchio,
  variabili,
} from '@/utils/marchio'

const PROVA = {
  key: 'prova',
  name: 'Marchio di Prova',
  favicon: '/p/favicon.png',
  touch_icon: '/p/180.png',
  colors: { '--brand': '#3355ff', '--brand-strong': '#1a2fa0' },
  centre_logo: '/files/aurora.png',
}

afterEach(() => {
  delete window.brand
  document.head.innerHTML = ''
  document.title = ''
  document.documentElement.removeAttribute('style')
})

describe('marchio', () => {
  it('is the boot brand over the fallback', () => {
    const dati = marchio(PROVA)
    expect(dati.name).toBe('Marchio di Prova')
    expect(dati.centre_logo).toBe('/files/aurora.png')
    // what the boot did not say comes from the fallback, never undefined
    expect(dati.logo).toBe(DI_RISERVA.logo)
  })

  it("reads the page's boot by default", () => {
    window.brand = PROVA
    expect(marchio().name).toBe('Marchio di Prova')
  })

  it('still has a brand without a boot', () => {
    expect(marchio(undefined).name).toBe(DI_RISERVA.name)
    expect(marchio(null).favicon).toBe(DI_RISERVA.favicon)
  })
})

describe('conMarchio', () => {
  it('puts the brand where a sentence names the product', () => {
    expect(conMarchio('Open {brand}', 'Marchio di Prova')).toBe(
      'Open Marchio di Prova',
    )
    expect(conMarchio('{brand} and {brand}', 'X')).toBe('X and X')
  })

  it("leaves the translator's placeholders alone", () => {
    expect(conMarchio('{0} in {brand}', 'X')).toBe('{0} in X')
  })

  it('names the booted brand when no name is given', () => {
    window.brand = PROVA
    expect(conMarchio('Welcome to {brand}')).toBe('Welcome to Marchio di Prova')
  })

  it('passes anything that is not a sentence through', () => {
    expect(conMarchio(undefined, 'X')).toBe(undefined)
    expect(conMarchio(3, 'X')).toBe(3)
  })
})

describe('variabili', () => {
  it("keeps only the brand's custom properties with a colour", () => {
    expect(
      variabili({
        '--brand': '#3355ff',
        '--brand-soft': 'oklch(0.9 0.02 250)',
        '--brand-strong': 'red; background: url(x)',
        '--other': '#000000',
        color: '#ffffff',
      }),
    ).toEqual({ '--brand': '#3355ff', '--brand-soft': 'oklch(0.9 0.02 250)' })
    expect(variabili(undefined)).toEqual({})
  })
})

describe('indossa', () => {
  it("dresses the page in the brand's colours, icons and name", () => {
    indossa(document, marchio(PROVA))
    const radice = document.documentElement.style
    expect(radice.getPropertyValue('--brand')).toBe('#3355ff')
    expect(radice.getPropertyValue('--brand-strong')).toBe('#1a2fa0')
    expect(
      document.querySelector('link[rel="icon"]').getAttribute('href'),
    ).toBe('/p/favicon.png')
    expect(
      document
        .querySelector('link[rel="apple-touch-icon"]')
        .getAttribute('href'),
    ).toBe('/p/180.png')
    expect(document.title).toBe('Marchio di Prova')
  })

  it('replaces the icons the page came with, without adding more', () => {
    document.head.innerHTML =
      '<link rel="icon" href="/old.png"><link rel="apple-touch-icon" href="/old-180.png">'
    indossa(document, marchio(PROVA))
    expect(document.querySelectorAll('link[rel="icon"]')).toHaveLength(1)
    expect(
      document.querySelector('link[rel="icon"]').getAttribute('href'),
    ).toBe('/p/favicon.png')
  })

  it("keeps a title of the page's own, and names the phone's home screen", () => {
    document.head.innerHTML =
      '<meta name="apple-mobile-web-app-title" content="Old">'
    document.title = 'Centro Aurora · Marchio di Prova'
    indossa(document, marchio(PROVA))
    expect(document.title).toBe('Centro Aurora · Marchio di Prova')
    expect(
      document.querySelector('meta[name="apple-mobile-web-app-title"]').content,
    ).toBe('Marchio di Prova')
  })
})
