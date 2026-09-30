// The product's brand - the vertical's (crm.marchio) - as the page came with it:
// its name, icon, logos, favicon and colours, and the centre's logo that may go
// beside it. The same in every screen; the centre never takes its place.

// A page opened without a boot (a test, an error page) still has a brand.
export const DI_RISERVA = {
  key: 'dottorcloud',
  name: 'DottorCloud',
  icon: '/assets/crm/images/dottorcloud-icona.svg',
  logo: '/assets/crm/images/dottorcloud-orizzontale.svg',
  logo_dark: '/assets/crm/images/dottorcloud-orizzontale-negativo.svg',
  favicon: '/assets/crm/images/favicon.png',
  touch_icon: '/assets/crm/manifest/apple-icon-180.png',
  description: '',
  colors: {
    '--brand': '#12a594',
    '--brand-strong': '#0b6f64',
    '--brand-soft': '#e1f5f1',
    '--brand-on-dark': '#5fe0cc',
  },
  centre_logo: '',
}

export function marchio(boot = globalThis.window?.brand) {
  return { ...DI_RISERVA, ...boot }
}

// A sentence that names the product says "{brand}": here it gets the brand's name.
export function conMarchio(testo, nome = marchio().name) {
  return typeof testo === 'string' ? testo.replaceAll('{brand}', nome) : testo
}

// Only CSS custom properties of the brand, with a colour a browser can read.
export function variabili(colori) {
  return Object.fromEntries(
    Object.entries(colori || {}).filter(
      ([nome, valore]) =>
        /^--brand(-[a-z-]+)?$/.test(nome) &&
        /^#[0-9a-f]{3,8}$|^rgb|^oklch/i.test(String(valore || '')),
    ),
  )
}

// The page wears the brand: its colours as CSS variables, its favicon, its icon
// on the phone's home screen, its name in the tab. Before the app mounts, so the
// pages' own titles and icons start from it.
export function indossa(documento = document, dati = marchio()) {
  const radice = documento.documentElement
  for (const [nome, valore] of Object.entries(variabili(dati.colors))) {
    radice.style.setProperty(nome, valore)
  }
  const link = (rel, href) => {
    if (!href) return
    let el = documento.querySelector(`link[rel="${rel}"]`)
    if (!el) {
      el = documento.createElement('link')
      el.rel = rel
      documento.head.appendChild(el)
    }
    el.href = href
  }
  link('icon', dati.favicon)
  link('apple-touch-icon', dati.touch_icon)
  const meta = documento.querySelector(
    'meta[name="apple-mobile-web-app-title"]',
  )
  if (meta) meta.content = dati.name
  if (!documento.title || documento.title === DI_RISERVA.name) {
    documento.title = dati.name
  }
}
