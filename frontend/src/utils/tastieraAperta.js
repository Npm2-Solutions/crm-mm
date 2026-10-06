// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * Writing on a phone. The keyboard comes up over the bottom of the screen and
 * the page takes what is left, as a phone's own apps do: the header stays
 * where it was, the box one writes in sits on the keyboard, the list between
 * them gets shorter. A conversation keeps its top still: only its bottom
 * rises.
 *
 * Android does it by itself, asked by the viewport's meta
 * (`interactive-widget=resizes-content`: Chrome 108, Firefox 132): the page
 * gets shorter while the keyboard is up. An iPhone does not (Safari ignores
 * the meta): the page stays as tall as the screen under the keyboard, Safari
 * slides it up to show the field one taps - the header off the top - and with
 * the keyboard up a finger at the end of a list, or on what does not scroll,
 * slides the whole page again.
 *
 * So while somebody writes the root says how much one sees
 * (`data-tastiera="aperta"`, `--altezza-con-tastiera`, and `--tastiera` what
 * the keyboard covers: 0 where the page got shorter by itself): the frame is
 * that tall, the bar at the bottom steps aside, a sheet and a list sit on the
 * keyboard (`telefono.css` «8», `area/area.css`). It changes when the keyboard
 * comes, goes or changes its height, never at each frame of a gesture: that
 * made the whole page's style be computed again under a finger, and a list
 * stuttered.
 *
 * On an iPhone the page does not slide at all. A field takes the focus without
 * Safari scrolling to it (`focus({ preventScroll })`, also when a finger
 * taps it: the focus it leaves hands it over) and is brought into view inside
 * its own box once the keyboard is up (`inVista`); while the keyboard is up a
 * finger moves only a box that has something to scroll (`overscroll-behavior:
 * contain` in the CSS, and `touchmove` stopped where WebKit lets it through).
 * What slid anyway goes back to the top once the page is still. These are
 * react-aria's ways on iOS 26 (Adobe, Apache 2.0: `usePreventScroll`).
 */

import { questoDispositivo } from '@/utils/installa'

// a keyboard is taller than this; the address bar showing or hiding is not
export const SOGLIA_TASTIERA = 150
// the room left above and below a field brought into view
export const MARGINE = 16
// how long the page stays still before what slid goes back to the top
export const QUIETE = 150
// how long a field waits for the keyboard before it is shown anyway (a focus
// that opens none)
export const ATTESA_TASTIERA = 600
// what a page left slid by the keyboard is still given back, after it went
// (iOS 26: WebKit 297779)
const DOPO_LA_CHIUSURA = 1000

const NON_SI_SCRIVE = new Set([
  'button',
  'checkbox',
  'color',
  'file',
  'hidden',
  'image',
  'radio',
  'range',
  'reset',
  'submit',
])

/** Whether the element in focus is one a keyboard writes in. */
export function siScrive(elemento) {
  if (!elemento) return false
  if (elemento.isContentEditable) return true
  const tag = elemento.tagName
  if (tag === 'TEXTAREA') return !elemento.readOnly && !elemento.disabled
  if (tag !== 'INPUT') return false
  return (
    !NON_SI_SCRIVE.has((elemento.type || 'text').toLowerCase()) &&
    !elemento.readOnly &&
    !elemento.disabled
  )
}

/**
 * What the keyboard leaves of the screen, from the browser's numbers: the
 * page's height now and without a keyboard at this width (`altezzaPiena`),
 * the height one sees and how far down it begins (`scostamento`), whether
 * somebody is writing. `aperta` when a keyboard is up; then `altezza` is the
 * frame's height, `sopra` where what one sees begins and `sotto` what the
 * keyboard covers of the page: nothing where it made the page shorter.
 */
export function vistaConTastiera({
  altezzaPiena = 0,
  altezzaPagina,
  altezzaVista,
  scostamento = 0,
  scrivendo,
}) {
  const chiusa = { aperta: false, altezza: null, sopra: 0, sotto: 0 }
  if (!scrivendo) return chiusa
  const coperta = altezzaPagina - altezzaVista
  if (coperta > SOGLIA_TASTIERA) {
    const sopra = Math.max(0, Math.round(scostamento))
    return {
      aperta: true,
      altezza: Math.round(altezzaVista),
      sopra,
      sotto: Math.max(0, Math.round(coperta) - sopra),
    }
  }
  if (altezzaPiena - altezzaPagina > SOGLIA_TASTIERA) {
    return {
      aperta: true,
      altezza: Math.round(altezzaPagina),
      sopra: 0,
      sotto: 0,
    }
  }
  return chiusa
}

/**
 * How far a box scrolls to show what lies from `alto` to `basso` where it
 * shows from `cima` to `fondo`, room left around it (`sopra`, `sotto`): as
 * little as it takes, as a browser's `block: 'nearest'`. Taller than the
 * room, its top is shown where it begins below, its end where it ends above;
 * already across the room, it stays.
 */
export function spostamentoPerVedere({
  alto,
  basso,
  cima,
  fondo,
  sopra = 0,
  sotto = 0,
}) {
  const da = cima + sopra
  const a = fondo - sotto
  if (alto >= da && basso <= a) return 0
  if (basso - alto > a - da) {
    if (alto > da) return alto - da
    if (basso < a) return basso - a
    return 0
  }
  return alto < da ? alto - da : basso - a
}

const SCORRE = /(auto|scroll)/

/** Whether `box` scrolls up and down, with something to scroll. */
function scorreInVerticale(box, win) {
  if (box.scrollHeight <= box.clientHeight) return false
  return SCORRE.test(win.getComputedStyle(box).overflowY)
}

/**
 * The box that takes a finger put on `elemento`: the nearest one (itself
 * included) that scrolls either way and has something to scroll; none when
 * only the page is left.
 */
export function scatolaCheScorre(elemento, win = window) {
  const doc = win.document
  for (let box = elemento; box; box = box.parentElement) {
    if (box === doc.documentElement || box === doc.body) return null
    if (
      box.scrollHeight <= box.clientHeight &&
      box.scrollWidth <= box.clientWidth
    )
      continue
    const stile = win.getComputedStyle(box)
    if (SCORRE.test(stile.overflowX + stile.overflowY)) return box
  }
  return null
}

// where the caret is in an editor taller than what shows: there is what one
// writes, not the editor's top
function rettangoloDi(elemento, win) {
  const tutto = elemento.getBoundingClientRect()
  if (!elemento.isContentEditable) return tutto
  const selezione = win.getSelection?.()
  if (!selezione?.rangeCount) return tutto
  const intervallo = selezione.getRangeAt(0)
  if (!elemento.contains(intervallo.startContainer)) return tutto
  const cursore = intervallo.getBoundingClientRect?.()
  return cursore && cursore.height ? cursore : tutto
}

/**
 * Brings `elemento` into view inside the boxes that hold it, never by moving
 * the page: each box from the nearest scrolls as little as it takes, so that
 * it shows within what one sees above the keyboard, with room around it (the
 * box's own `scroll-padding`, where a sheet's title and actions stay, else
 * `margine`).
 */
export function inVista(elemento, win = window, margine = MARGINE) {
  if (!elemento?.isConnected) return
  const doc = win.document
  const vista = win.visualViewport
  const cimaVista = vista ? vista.offsetTop : 0
  const fondoVista = vista ? vista.offsetTop + vista.height : win.innerHeight
  for (
    let box = elemento.parentElement;
    box && box !== doc.body && box !== doc.documentElement;
    box = box.parentElement
  ) {
    if (!scorreInVerticale(box, win)) continue
    const stile = win.getComputedStyle(box)
    const scatola = box.getBoundingClientRect()
    const cima = Math.max(scatola.top, cimaVista)
    const fondo = Math.min(scatola.bottom, fondoVista)
    if (fondo <= cima) continue
    const dove = rettangoloDi(elemento, win)
    const di = spostamentoPerVedere({
      alto: dove.top,
      basso: dove.bottom,
      cima,
      fondo,
      sopra: Math.max(margine, parseFloat(stile.scrollPaddingTop) || 0),
      sotto: Math.max(margine, parseFloat(stile.scrollPaddingBottom) || 0),
    })
    if (!di) continue
    const massimo = box.scrollHeight - box.clientHeight
    box.scrollTop = Math.max(0, Math.min(massimo, box.scrollTop + di))
  }
}

const VARIABILI = {
  altezza: '--altezza-con-tastiera',
  sopra: '--vista-sopra',
  sotto: '--tastiera',
}
const CAMPI = 'input, textarea, [contenteditable]'

/**
 * Follows the keyboard on this page until the function it returns is called:
 * on the root, `data-tastiera="aperta"` with the frame's height
 * (`--altezza-con-tastiera`), where what one sees begins (`--vista-sopra`)
 * and what the keyboard covers (`--tastiera`). On an iPhone, from now on the
 * page does not slide.
 */
export function seguiLaTastiera(win = window) {
  const vista = win.visualViewport
  if (!vista) return () => {}
  const doc = win.document
  const radice = doc.documentElement
  const ios = questoDispositivo(win).ios
  // the page's height without a keyboard, by width: upright and sideways
  const piena = new Map()
  let ultima = null
  let frame = 0
  let quiete = 0
  let chiusaAlle = -Infinity
  // fingers on the screen, and whether the page slid under one
  let dita = 0
  let slittataSottoIlDito = false
  // a field waiting for the keyboard to be shown
  let inAttesa = null
  let attesa = 0

  const ingrandita = () => Math.abs((vista.scale || 1) - 1) > 0.01

  function misura(ferma = false) {
    frame = 0
    // two fingers enlarged the page: what one sees is a part of it, and the
    // frame stays as it was
    if (ingrandita()) return
    const larghezza = Math.round(win.innerWidth)
    const altezzaPiena = Math.max(piena.get(larghezza) || 0, win.innerHeight)
    piena.set(larghezza, altezzaPiena)
    const attivo = doc.activeElement
    const ora = vistaConTastiera({
      altezzaPiena,
      altezzaPagina: win.innerHeight,
      altezzaVista: vista.height,
      // where what one sees begins moves the frame only once the page is
      // still: under a finger it changed at every frame
      scostamento: ferma ? vista.offsetTop : ultima?.sopra ?? 0,
      scrivendo: siScrive(attivo),
    })
    if (!ora.aperta) {
      if (ultima) chiudi()
      return
    }
    const prima = ultima
    if (
      prima &&
      Object.keys(VARIABILI).every((chiave) => prima[chiave] === ora[chiave])
    )
      return
    for (const [chiave, nome] of Object.entries(VARIABILI)) {
      radice.style.setProperty(nome, `${ora[chiave]}px`)
    }
    radice.dataset.tastiera = 'aperta'
    ultima = ora
    guardia(ios && ora.sotto > 0)
    // the box the field is in got shorter: it may have gone under the keyboard
    if (!prima || ora.altezza < prima.altezza) {
      inAttesa = null
      win.clearTimeout(attesa)
      mostra(attivo)
    }
  }

  function chiudi() {
    delete radice.dataset.tastiera
    for (const nome of Object.values(VARIABILI))
      radice.style.removeProperty(nome)
    ultima = null
    chiusaAlle = win.performance?.now?.() ?? Date.now()
    guardia(false)
    // iOS 26 leaves the page slid by what the keyboard took
    if (win.scrollY > 0 || vista.offsetTop > 0) fermaPoi()
  }

  function pianifica() {
    if (!frame) frame = win.requestAnimationFrame(() => misura())
  }

  // a field, in view once what is around it has its new size
  function mostra(elemento) {
    if (!elemento) return
    win.requestAnimationFrame(() => {
      if (doc.activeElement === elemento) inVista(elemento, win)
    })
  }

  // a field focused by DottorCloud's code or handed the focus, on an iPhone:
  // shown once the keyboard is up, or if none comes
  function mostraDopo(elemento) {
    if (ultima) return mostra(elemento)
    inAttesa = elemento
    win.clearTimeout(attesa)
    attesa = win.setTimeout(() => {
      const campo = inAttesa
      inAttesa = null
      mostra(campo)
    }, ATTESA_TASTIERA)
  }

  // what slid goes back to the top once the page is still, and the frame
  // follows what one sees if it stayed slid
  function fermaPoi() {
    if (dita) {
      slittataSottoIlDito = true
      return
    }
    win.clearTimeout(quiete)
    quiete = win.setTimeout(ferma, QUIETE)
  }

  function ferma() {
    quiete = 0
    if (ingrandita()) return
    if (win.scrollY > 0 || vista.offsetTop > 0) win.scrollTo(0, 0)
    win.requestAnimationFrame(() => {
      if (ultima) misura(true)
      // what WebKit leaves slid after a scroll to the top: a pixel each way
      else if (vista.offsetTop > 0) {
        win.scrollBy(0, -1)
        win.scrollBy(0, 1)
      }
    })
  }

  function scorre() {
    const ora = win.performance?.now?.() ?? Date.now()
    if (!ultima && ora - chiusaAlle > DOPO_LA_CHIUSURA) return
    if (win.scrollY > 0 || vista.offsetTop > 0 || ultima?.sopra) fermaPoi()
  }

  // the search key closes the keyboard over the results, as a phone's own
  // searches do: they are there already, found as one typed
  function invio(evento) {
    if (evento.key !== 'Enter' || evento.defaultPrevented) return
    if (evento.isComposing) return
    if (evento.target?.matches?.("input[type='search']")) evento.target.blur()
  }

  // --- iPhone: the page never slides -------------------------------------

  let guardiaAttiva = false
  let scatolaDelDito = null
  let ditoLibero = false
  // where the focus waits a moment when nothing holds it and a finger is on a
  // field: the field takes it from there, handed over without Safari's scroll
  let sosta = null

  // while the keyboard covers the page, a finger moves only a box that has
  // something to scroll: the rest of it slid the page
  function guardia(si) {
    if (si === guardiaAttiva) return
    guardiaAttiva = si
    if (si) {
      doc.addEventListener('touchmove', toccoMuove, {
        passive: false,
        capture: true,
      })
    } else {
      doc.removeEventListener('touchmove', toccoMuove, { capture: true })
    }
  }

  function toccoInizia(evento) {
    dita = evento.touches.length
    if (!ios) return
    if (guardiaAttiva) {
      scatolaDelDito = scatolaCheScorre(evento.target, win)
      ditoLibero = siSceglie(evento)
    }
    passaIlFuoco(evento.target)
  }

  function toccoFinisce(evento) {
    dita = evento.touches.length
    if (dita || !slittataSottoIlDito) return
    slittataSottoIlDito = false
    fermaPoi()
  }

  function toccoMuove(evento) {
    // two fingers enlarge, a selection or a slider moves with the finger
    if (evento.touches.length > 1 || ditoLibero || !evento.cancelable) return
    const box = scatolaDelDito
    if (
      !box ||
      !box.isConnected ||
      (box.scrollHeight <= box.clientHeight &&
        box.scrollWidth <= box.clientWidth)
    )
      evento.preventDefault()
  }

  // words selected under the finger, a slider, a field's selected words
  function siSceglie(evento) {
    const bersaglio = evento.target
    const selezione = win.getSelection?.()
    if (
      selezione &&
      !selezione.isCollapsed &&
      selezione.containsNode?.(bersaglio, true)
    )
      return true
    if (bersaglio?.matches?.("input[type='range']")) return true
    try {
      return (
        bersaglio === doc.activeElement &&
        bersaglio.selectionStart < bersaglio.selectionEnd
      )
    } catch {
      return false
    }
  }

  // a finger on a field nobody writes in yet, with the focus nowhere: it
  // waits on the box around the field that holds a focus (a sheet: its
  // focus stays inside) or on the page's own place, so the field's focus
  // comes as a handing over
  function passaIlFuoco(bersaglio) {
    const campo = bersaglio?.closest?.(CAMPI)
    if (!campo || !siScrive(campo) || campo === doc.activeElement) return
    const attivo = doc.activeElement
    if (attivo && attivo !== doc.body && attivo !== radice) return
    const dove =
      campo.parentElement?.closest('[tabindex="-1"]') || sostaDellaPagina()
    dove.focus({ preventScroll: true })
  }

  function sostaDellaPagina() {
    if (sosta?.isConnected) return sosta
    sosta = doc.createElement('div')
    sosta.tabIndex = -1
    sosta.dataset.sostaDelFuoco = ''
    sosta.style.cssText =
      'position:fixed;top:0;left:0;width:1px;height:1px;overflow:hidden;outline:none;pointer-events:none'
    doc.body.append(sosta)
    return sosta
  }

  // the focus leaves for a field: the field takes it from DottorCloud, so
  // Safari does not scroll to it (the keyboard's arrows too)
  function perdeIlFuoco(evento) {
    const verso = evento.relatedTarget
    if (verso && verso !== doc.activeElement && siScrive(verso)) verso.focus()
  }

  // every focus asked of a field never scrolls the page: the field is shown
  // in its own box once the keyboard is up
  function senzaScorrere() {
    const prototipo = win.HTMLElement.prototype
    const originale = prototipo.focus
    Object.defineProperty(prototipo, 'focus', {
      configurable: true,
      writable: true,
      value(opzioni) {
        originale.call(this, { ...opzioni, preventScroll: true })
        if (opzioni?.preventScroll) return
        if (siScrive(this)) mostraDopo(this)
        else inVista(this, win)
      },
    })
    return () =>
      Object.defineProperty(prototipo, 'focus', {
        configurable: true,
        writable: true,
        value: originale,
      })
  }

  const ascolti = [
    [vista, 'resize', pianifica],
    [vista, 'scroll', scorre],
    [win, 'resize', pianifica],
    [win, 'scroll', scorre],
    [doc, 'focusin', pianifica],
    [doc, 'focusout', pianifica],
    [doc, 'keydown', invio],
  ]
  for (const [chi, evento, fn] of ascolti) chi.addEventListener(evento, fn)
  const dito = { passive: true, capture: true }
  doc.addEventListener('touchstart', toccoInizia, dito)
  doc.addEventListener('touchend', toccoFinisce, dito)
  doc.addEventListener('touchcancel', toccoFinisce, dito)
  let ripristina = () => {}
  if (ios) {
    ripristina = senzaScorrere()
    doc.addEventListener('blur', perdeIlFuoco, true)
  }
  misura()

  return () => {
    for (const [chi, evento, fn] of ascolti) chi.removeEventListener(evento, fn)
    doc.removeEventListener('touchstart', toccoInizia, dito)
    doc.removeEventListener('touchend', toccoFinisce, dito)
    doc.removeEventListener('touchcancel', toccoFinisce, dito)
    doc.removeEventListener('blur', perdeIlFuoco, true)
    ripristina()
    if (ultima) chiudi()
    guardia(false)
    if (frame) win.cancelAnimationFrame(frame)
    win.clearTimeout(quiete)
    win.clearTimeout(attesa)
    sosta?.remove()
  }
}
