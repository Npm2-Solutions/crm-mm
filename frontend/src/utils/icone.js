// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * The Lucide icons DottorCloud draws by name - `<Icon icon="settings">`, the
 * icon a centre gave a view or a dashboard, the picker's - from one sprite in
 * the page (`#lucide-sprite`, the one frappe-ui's icons read too).
 *
 * frappe-ui's `spritePlugin` put the whole of lucide-static in it at the start:
 * 1,737 icons, 82 KB compressed in the first download of every page, 130 ms to
 * build on a slow phone, and 8,673 elements - nine in ten of a person's page -
 * that the browser walked through whenever something searched the page. The
 * everyday screens draw five of them. Now the sprite's text comes when the app
 * is idle, or when an icon asks for it, and the page holds only the icons
 * drawn; the picker puts all of them in when it opens, to choose among them.
 */

const ID = 'lucide-sprite'
const SVG = 'http://www.w3.org/2000/svg'

let testo = null
let arrivo = null
const messe = new Set()
let tutte = false

/** The symbol named `nome` in the sprite's text, or '' when it has none. */
export function simbolo(testo, nome) {
  if (!testo || !nome) return ''
  // the closing quote too: "phone" is not the start of "phone-call"
  const inizio = testo.indexOf(`<symbol id="${nome}"`)
  if (inizio < 0) return ''
  const fine = testo.indexOf('</symbol>', inizio)
  return fine < 0 ? '' : testo.slice(inizio, fine + '</symbol>'.length)
}

/** Every symbol of the sprite's text, in one piece. */
export function simboli(testo) {
  const inizio = (testo || '').indexOf('<symbol')
  const fine = (testo || '').lastIndexOf('</symbol>')
  if (inizio < 0 || fine < inizio) return ''
  return testo.slice(inizio, fine + '</symbol>'.length)
}

// the sprite's place, as frappe-ui made it: a hidden div at the top of the
// page, now with an empty svg the icons go into
function contenitore() {
  let div = document.getElementById(ID)
  if (!div) {
    div = document.createElement('div')
    div.id = ID
    div.style.display = 'none'
    document.body.prepend(div)
  }
  let svg = div.firstElementChild
  if (!svg) {
    svg = document.createElementNS(SVG, 'svg')
    div.appendChild(svg)
  }
  return svg
}

/** The sprite's text, fetched once; asked again after a failed fetch. */
export function caricaIcone() {
  if (!arrivo) {
    arrivo = import('lucide-static/sprite.svg?raw').then(
      (modulo) => (testo = modulo.default),
      (errore) => {
        arrivo = null
        throw errore
      },
    )
  }
  return arrivo
}

/** Whether the icon `nome` is in the page, ready to be drawn. */
export function inPagina(nome) {
  return tutte || messe.has(nome)
}

/** Puts the icon `nome` in the page, once; resolves when it is there. */
export async function mettiIcona(nome) {
  if (!nome || inPagina(nome)) return
  await caricaIcone()
  if (inPagina(nome)) return
  messe.add(nome)
  const pezzo = simbolo(testo, nome)
  if (pezzo) contenitore().insertAdjacentHTML('beforeend', pezzo)
}

/** Every icon in the page: the picker lists them from it. */
export async function mettiTutteLeIcone() {
  if (tutte) return
  await caricaIcone()
  if (tutte) return
  // all of them, the ones put one by one included
  contenitore().innerHTML = simboli(testo)
  tutte = true
}

/** Once the app is up and the phone idle, the sprite's text comes: the next
 * icon drawn by name does not wait for it. */
export function caricaQuandoLibero() {
  const via = () => caricaIcone().catch(() => {})
  if (typeof requestIdleCallback === 'function') {
    requestIdleCallback(via, { timeout: 8000 })
  } else {
    setTimeout(via, 4000)
  }
}
