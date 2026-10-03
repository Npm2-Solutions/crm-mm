// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * A dialog on a phone is a sheet with a grabber on top (telefono.css), and a
 * phone's hand takes a sheet by its top and drags it down to put it away. The
 * grabber was only drawn: the sheet did not move. Now it follows the finger;
 * let go far enough down, or flicked, it closes as Escape closes it; else it
 * slides back up. A dialog that may not close yet (a page of the settings with
 * changes not saved) slides back up as well.
 *
 * Only by its top - the grabber, the title - and only while the sheet is at
 * rest, not scrolled: a finger in the form scrolls it, writes in it, signs. A
 * screen of its own (the settings) shows no grabber and is not dragged.
 */

// how far from the sheet's top a finger takes it: the grabber and the title
export const ZONA_MANIGLIA = 64
// how far the finger goes before the sheet moves: a tap on the title's cross
// stays a tap
export const PASSO_MINIMO = 8

const APERTO = ".dialog-content[data-state='open']"
const CAMPI = 'input, textarea, select, [contenteditable="true"], canvas'
const SCIVOLA_VIA = 180
const TORNA_SU = 220

/**
 * Whether a sheet `altezza` tall, let go `spostamento` pixels down while the
 * finger went `velocita` pixels a millisecond, closes: past a third of it (no
 * more than 140 pixels for a tall one), or flicked.
 */
export function siChiude({ spostamento, altezza, velocita = 0 }) {
  if (!(spostamento > 0)) return false
  if (velocita > 0.5 && spostamento > 24) return true
  return spostamento > Math.min(140, (altezza || 0) * 0.3)
}

// a sheet shows its grabber (telefono.css); one that is a screen of its own,
// the settings, draws none and is not dragged away
function haManiglia(win, foglio) {
  const segno = win.getComputedStyle(foglio, '::before').content
  return segno !== 'none' && segno !== 'normal'
}

// the dimmed screen behind the sheet: the element before its scroll box
function sfondoDi(foglio) {
  const prima = foglio.closest(
    '.dialog-scroll-container',
  )?.previousElementSibling
  return prima?.classList.contains('dialog-overlay') ? prima : null
}

/**
 * From now on a sheet follows a finger that takes it by its top. Gives back
 * the function that stops it.
 */
export function trascinaIFogli(
  win = window,
  ora = () => win.performance.now(),
) {
  const doc = win.document
  let gesto = null

  function torna(foglio) {
    const sfondo = sfondoDi(foglio)
    foglio.style.transition = `transform ${TORNA_SU}ms cubic-bezier(0.2, 0.8, 0.2, 1)`
    foglio.style.transform = ''
    if (sfondo) {
      sfondo.style.transition = `opacity ${TORNA_SU}ms ease-out`
      sfondo.style.opacity = ''
    }
    win.setTimeout(() => {
      foglio.style.transition = ''
      if (sfondo) sfondo.style.transition = ''
    }, TORNA_SU)
  }

  function chiudi(foglio, altezza) {
    const sfondo = sfondoDi(foglio)
    foglio.style.transition = `transform ${SCIVOLA_VIA}ms ease-in`
    foglio.style.transform = `translateY(${altezza}px)`
    if (sfondo) {
      sfondo.style.transition = `opacity ${SCIVOLA_VIA}ms ease-in`
      sfondo.style.opacity = '0'
    }
    win.setTimeout(() => {
      // already down: no closing animation of its own after this one
      foglio.style.animation = 'none'
      if (sfondo) sfondo.style.animation = 'none'
      if (foglio.contains(doc.activeElement)) doc.activeElement.blur?.()
      foglio.dispatchEvent(
        new win.KeyboardEvent('keydown', {
          key: 'Escape',
          code: 'Escape',
          keyCode: 27,
          bubbles: true,
          cancelable: true,
        }),
      )
      // a dialog that may not close yet comes back up, as it opened
      win.setTimeout(() => {
        if (!foglio.isConnected || foglio.dataset.state !== 'open') return
        foglio.style.transition = ''
        foglio.style.transform = ''
        foglio.style.animation = ''
        if (sfondo) {
          sfondo.style.animation = ''
          sfondo.style.transition = ''
          sfondo.style.opacity = ''
        }
      }, 80)
    }, SCIVOLA_VIA)
  }

  function inizio(evento) {
    gesto = null
    if (evento.touches.length !== 1) return
    const aperti = doc.querySelectorAll(APERTO)
    const foglio = aperti[aperti.length - 1]
    if (!foglio || !foglio.contains(evento.target)) return
    if (!haManiglia(win, foglio)) return
    if (evento.target.closest?.(CAMPI)) return
    if (foglio.closest('.dialog-scroll-container')?.scrollTop > 0) return
    const y = evento.touches[0].clientY
    if (y - foglio.getBoundingClientRect().top > ZONA_MANIGLIA) return
    gesto = { foglio, y0: y, y, t: ora(), dy: 0, velocita: 0, mosso: false }
  }

  function muovi(evento) {
    if (!gesto) return
    const y = evento.touches[0].clientY
    const t = ora()
    if (t > gesto.t) gesto.velocita = (y - gesto.y) / (t - gesto.t)
    gesto.y = y
    gesto.t = t
    const dy = Math.max(0, y - gesto.y0)
    if (!gesto.mosso && dy < PASSO_MINIMO) return
    gesto.mosso = true
    gesto.dy = dy
    const { foglio } = gesto
    foglio.style.transition = 'none'
    foglio.style.transform = dy ? `translateY(${dy}px)` : ''
    const sfondo = sfondoDi(foglio)
    if (sfondo) {
      const altezza = foglio.offsetHeight || 1
      sfondo.style.transition = 'none'
      sfondo.style.opacity = String(Math.max(0, 1 - dy / altezza))
    }
  }

  function fine() {
    if (!gesto) return
    const { foglio, dy, velocita, mosso } = gesto
    gesto = null
    if (!mosso) return
    const altezza = foglio.offsetHeight
    if (siChiude({ spostamento: dy, altezza, velocita }))
      chiudi(foglio, altezza)
    else torna(foglio)
  }

  // the phone took the gesture back (a call, a swipe of the system)
  function annulla() {
    if (!gesto) return
    const { foglio, mosso } = gesto
    gesto = null
    if (mosso) torna(foglio)
  }

  const ascolti = [
    ['touchstart', inizio],
    ['touchmove', muovi],
    ['touchend', fine],
    ['touchcancel', annulla],
  ]
  for (const [nome, fn] of ascolti) {
    doc.addEventListener(nome, fn, { passive: true })
  }
  return () => {
    for (const [nome, fn] of ascolti) doc.removeEventListener(nome, fn)
  }
}
