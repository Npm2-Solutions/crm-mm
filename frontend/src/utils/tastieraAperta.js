// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * The keyboard of a phone covers the bottom of the screen without making the
 * page any shorter: iPhone, and Chrome on Android, shrink only the part one
 * sees (the "visual viewport") and slide it towards the field being written
 * in. The app's frame stayed as tall as the screen, so what sits at its
 * bottom went under the keyboard - a sheet's Save, the chat's box, the agenda
 * panel's buttons - and the frame slid up, its header out of sight.
 *
 * While somebody writes, the frame is as tall as what one sees and stays at
 * the top: the header stays, the bar at the bottom steps aside, a sheet and a
 * list sit on the keyboard (`telefono.css`, `:root[data-tastiera]`). Where the
 * browser makes the page itself shorter (Firefox, an app's web view that
 * resizes) nothing is covered and nothing changes.
 */

// a keyboard is taller than this; the address bar showing or hiding is not
export const SOGLIA_TASTIERA = 150

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
 * page's height, the height one sees and how far down the browser slid it
 * (`scostamento`), whether somebody is writing. `aperta` when a keyboard
 * covers part of the page; then `altezza` is the frame's height, `sopra`
 * where what one sees begins and `sotto` what lies under it.
 */
export function vistaConTastiera({
  altezzaPagina,
  altezzaVista,
  scostamento = 0,
  scrivendo,
}) {
  const tastiera = altezzaPagina - altezzaVista
  if (!scrivendo || tastiera <= SOGLIA_TASTIERA) {
    return { aperta: false, altezza: null, sopra: 0, sotto: 0 }
  }
  const sopra = Math.max(0, Math.round(scostamento))
  return {
    aperta: true,
    altezza: Math.round(altezzaVista),
    sopra,
    sotto: Math.max(0, Math.round(tastiera) - sopra),
  }
}

const VARIABILI = {
  altezza: '--altezza-con-tastiera',
  sopra: '--vista-sopra',
  sotto: '--tastiera',
}

/**
 * Follows the keyboard on this page until the function it returns is called:
 * on the root, `data-tastiera="aperta"` with the frame's height
 * (`--altezza-con-tastiera`), where what one sees begins (`--vista-sopra`)
 * and what the keyboard covers (`--tastiera`).
 */
export function seguiLaTastiera(win = window) {
  const vista = win.visualViewport
  if (!vista) return () => {}
  const documento = win.document
  const radice = documento.documentElement
  let frame = 0
  let ultima = null

  function chiudi() {
    delete radice.dataset.tastiera
    for (const nome of Object.values(VARIABILI)) {
      radice.style.removeProperty(nome)
    }
    ultima = null
  }

  function aggiorna() {
    frame = 0
    const attivo = documento.activeElement
    // the browser slid the page towards the field: the frame becomes as tall
    // as what one sees, so the page goes back to the top
    if (ultima && win.scrollY > 0) win.scrollTo(0, 0)
    const ora = vistaConTastiera({
      altezzaPagina: win.innerHeight,
      altezzaVista: vista.height,
      scostamento: vista.offsetTop,
      scrivendo: siScrive(attivo),
    })
    if (!ora.aperta) {
      if (ultima) chiudi()
      return
    }
    const cambiata =
      !ultima ||
      Object.keys(VARIABILI).some((chiave) => ultima[chiave] !== ora[chiave])
    if (!cambiata) return
    for (const [chiave, nome] of Object.entries(VARIABILI)) {
      radice.style.setProperty(nome, `${ora[chiave]}px`)
    }
    const prima = !ultima
    radice.dataset.tastiera = 'aperta'
    ultima = ora
    if (prima && win.scrollY > 0) win.scrollTo(0, 0)
    // the field may have gone out of its box as the box got shorter
    attivo?.scrollIntoView?.({ block: 'nearest' })
  }

  function pianifica() {
    if (!frame) frame = win.requestAnimationFrame(aggiorna)
  }

  // the search key closes the keyboard over the results, as a phone's own
  // searches do: they are there already, found as one typed
  function invio(evento) {
    if (evento.key !== 'Enter' || evento.defaultPrevented) return
    if (evento.isComposing) return
    if (evento.target?.matches?.("input[type='search']")) evento.target.blur()
  }

  const ascolti = [
    [vista, 'resize'],
    [vista, 'scroll'],
    [win, 'scroll'],
    [documento, 'focusin'],
    [documento, 'focusout'],
  ]
  for (const [chi, evento] of ascolti) chi.addEventListener(evento, pianifica)
  documento.addEventListener('keydown', invio)
  return () => {
    for (const [chi, evento] of ascolti) {
      chi.removeEventListener(evento, pianifica)
    }
    documento.removeEventListener('keydown', invio)
    if (frame) win.cancelAnimationFrame(frame)
    chiudi()
  }
}
