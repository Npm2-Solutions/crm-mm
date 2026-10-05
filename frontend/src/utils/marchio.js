// The product's brand - the vertical's (crm.marchio) - as the page came with it:
// its name, icon, logos, favicon and colours; and the centre's mark, which leads
// where a person deals with the centre (the top of the sidebar, the client area):
// its logo, the logo's shape, its name. The product signs at the foot: the two
// never stand side by side.

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
  centre_logo_shape: '',
  centre_name: '',
}

export function marchio(boot = globalThis.window?.brand) {
  return { ...DI_RISERVA, ...boot }
}

// The account the product works with by itself - an import from Meta, an
// automation, a webhook, a job - signs as the product: «Administrator» is the
// framework's word, never somebody's name.
export const ACCOUNT_DEL_SISTEMA = 'Administrator'

export function nomeDiUnUtente(utente, prodotto = marchio().name) {
  const nome = utente?.name || utente?.email || ''
  if (nome === ACCOUNT_DEL_SISTEMA) return prodotto
  return utente?.full_name?.trim() || nome
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
  // the brand's own look over frappe-ui's (espresso.css hangs on it)
  if (dati.key) radice.dataset.marchio = dati.key
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

// A logo this many times wider than high is drawn on its own, wide: it carries the
// centre's name. Below it, square, it goes beside the name. As crm.marchio.LARGO.
export const LARGO = 1.5

// How a logo is drawn: 'wide' on its own, 'square' beside the centre's name; ''
// when its size is not known, and then it goes beside the name, never lost.
export function formaDelLogo(larghezza, altezza) {
  const l = Number(larghezza) || 0
  const a = Number(altezza) || 0
  if (l <= 0 || a <= 0) return ''
  return l >= LARGO * a ? 'wide' : 'square'
}

// The words a centre's initials skip: "Studio di Fisioterapia" is SF.
const LEGAMI = new Set([
  'di',
  'del',
  'della',
  'dei',
  'delle',
  'e',
  'ed',
  'la',
  'il',
  'lo',
  'per',
  'the',
  'of',
  'and',
  '&',
])

// The centre's initials, for its tile without a logo: the first letters of its
// first two words that are not a link between them.
export function iniziali(nome) {
  const parole = (String(nome || '').match(/[\p{L}\p{N}&]+/gu) || []).filter(
    (p) => !LEGAMI.has(p.toLowerCase()),
  )
  return parole
    .slice(0, 2)
    .map((p) => p[0].toLocaleUpperCase())
    .join('')
}

// The centre's own name, or nothing where it is the software's: a name left to
// the framework or the product's (as crm.marchio.nome_scelto).
export function nomeDelCentro(nome, prodotto = marchio().name) {
  const scelto = String(nome || '').trim()
  const software = ['frappe', 'frappe framework', 'frappe crm', DI_RISERVA.name]
    .concat(prodotto || [])
    .map((n) => n.toLowerCase())
  return software.includes(scelto.toLowerCase()) ? '' : scelto
}

// An SVG's width and height: its own, in pixels, else its viewBox's. As
// crm.marchio.misure_svg: a browser sizes an SVG without its own size as it likes.
export function misureSvg(testo) {
  const radice = String(testo || '').match(/<svg\b[^>]*>/i)
  if (!radice) return null
  const tag = radice[0]
  const misura = (nome) => {
    const trovata = tag.match(
      new RegExp(`\\s${nome}\\s*=\\s*["']\\s*([\\d.]+)\\s*(?:px)?\\s*["']`),
    )
    return trovata ? parseFloat(trovata[1]) : null
  }
  const larghezza = misura('width')
  const altezza = misura('height')
  if (larghezza && altezza) return [larghezza, altezza]
  const vista = tag.match(/viewBox\s*=\s*["']([^"']+)["']/i)
  const numeri = vista ? vista[1].trim().split(/[\s,]+/) : []
  if (numeri.length !== 4) return null
  const [l, a] = [parseFloat(numeri[2]), parseFloat(numeri[3])]
  return Number.isNaN(l) || Number.isNaN(a) ? null : [l, a]
}

// The shape of the logo at an address: what the server measured (`nota`), else
// an SVG's own words, else what the image says once the browser has it; '' when
// none knows.
export async function misuraIlLogo(url, nota = '') {
  if (!url || nota) return nota || ''
  if (/\.svg$/i.test(url.split(/[?#]/)[0])) {
    try {
      const risposta = await fetch(url)
      const misure = risposta.ok ? misureSvg(await risposta.text()) : null
      if (misure) return formaDelLogo(...misure)
    } catch {
      // the image may still say it
    }
  }
  if (typeof Image === 'undefined') return ''
  return new Promise((risolvi) => {
    const immagine = new Image()
    immagine.onload = () =>
      risolvi(formaDelLogo(immagine.naturalWidth, immagine.naturalHeight))
    immagine.onerror = () => risolvi('')
    immagine.src = url
  })
}
