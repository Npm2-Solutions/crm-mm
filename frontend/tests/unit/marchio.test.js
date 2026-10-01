// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// The product's brand - the vertical's (crm.marchio) - as the pages wear it:
// its name in the sentences that say "{brand}", its colours as CSS variables,
// its icons in the head. And the centre's mark, which leads at the top: its
// logo drawn as it is, its initials, its name - never the software's.
import {
  DI_RISERVA,
  conMarchio,
  formaDelLogo,
  iniziali,
  indossa,
  marchio,
  misuraIlLogo,
  misureSvg,
  nomeDelCentro,
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
  document.documentElement.removeAttribute('data-marchio')
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
    // the brand's own look over frappe-ui's hangs on its key (espresso.css)
    expect(document.documentElement.dataset.marchio).toBe('prova')
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

// the same cases as crm/tests/test_marchio.py: the browser and the server draw a
// logo the same way
describe('formaDelLogo', () => {
  it('is wide from one and a half times as wide as high', () => {
    expect(formaDelLogo(220, 60)).toBe('wide')
    expect(formaDelLogo(150, 100)).toBe('wide')
    expect(formaDelLogo(149, 100)).toBe('square')
    expect(formaDelLogo(64, 64)).toBe('square')
    expect(formaDelLogo(80, 120)).toBe('square')
  })

  it('knows nothing of a logo without a size', () => {
    expect(formaDelLogo(0, 60)).toBe('')
    expect(formaDelLogo(undefined, undefined)).toBe('')
    expect(formaDelLogo('x', 3)).toBe('')
  })
})

describe('misureSvg', () => {
  it("reads an SVG's own size, else its viewBox", () => {
    expect(
      misureSvg(
        '<svg xmlns="http://www.w3.org/2000/svg" width="220" height="60">',
      ),
    ).toEqual([220, 60])
    expect(misureSvg("<?xml version='1.0'?><svg viewBox='0,0,64,48'>")).toEqual(
      [64, 48],
    )
    // a size in percent says nothing: the viewBox does
    expect(
      misureSvg('<svg width="100%" height="100%" viewBox="0 0 300 100">'),
    ).toEqual([300, 100])
    // a stroke's width is not the drawing's
    expect(
      misureSvg('<svg stroke-width="2" width="48px" height="40px">'),
    ).toEqual([48, 40])
  })

  it('says nothing it cannot read', () => {
    expect(misureSvg("<svg><rect width='10' height='90'/></svg>")).toBe(null)
    expect(misureSvg('not an svg')).toBe(null)
    expect(misureSvg(undefined)).toBe(null)
  })
})

describe('misuraIlLogo', () => {
  it('takes what the server measured', async () => {
    expect(await misuraIlLogo('/files/aurora.svg', 'wide')).toBe('wide')
  })

  it('reads an SVG the server did not measure', async () => {
    const prima = globalThis.fetch
    globalThis.fetch = vi.fn(async () => ({
      ok: true,
      text: async () => '<svg viewBox="0 0 220 60"></svg>',
    }))
    try {
      expect(await misuraIlLogo('/files/nuovo.svg?v=1')).toBe('wide')
      expect(globalThis.fetch).toHaveBeenCalledWith('/files/nuovo.svg?v=1')
    } finally {
      globalThis.fetch = prima
    }
  })

  it('has nothing to measure without an address', async () => {
    expect(await misuraIlLogo('')).toBe('')
  })
})

describe('iniziali', () => {
  it("takes the first letters of the centre's first two words", () => {
    expect(iniziali('Centro Aurora')).toBe('CA')
    expect(iniziali('Studio di Fisioterapia Rossi')).toBe('SF')
    expect(iniziali('poliambulatorio san luca')).toBe('PS')
    expect(iniziali('Rossi & Bianchi')).toBe('RB')
    expect(iniziali('Ègida')).toBe('È')
    expect(iniziali('3D Dental')).toBe('3D')
  })

  it('has none without a name', () => {
    expect(iniziali('')).toBe('')
    expect(iniziali(undefined)).toBe('')
    expect(iniziali(' · ')).toBe('')
  })
})

describe('nomeDelCentro', () => {
  it("is the centre's own name, trimmed", () => {
    expect(nomeDelCentro(' Centro Aurora ', 'DottorCloud')).toBe(
      'Centro Aurora',
    )
  })

  it("is nothing where the name is the software's", () => {
    for (const nome of [
      '',
      'Frappe',
      'frappe crm',
      'Frappe Framework',
      'DottorCloud',
      ' dottorcloud ',
      'Marchio di Prova',
    ]) {
      expect(nomeDelCentro(nome, 'Marchio di Prova')).toBe('')
    }
    expect(nomeDelCentro(null)).toBe('')
  })
})
