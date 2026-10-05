// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * What scrolls `elemento`: the nearest box around it that scrolls and has more than
 * it shows (a form's box may say it scrolls and take its whole height), else the
 * page.
 */
export function cheLoScorre(elemento, win = window) {
  for (let su = elemento?.parentElement; su; su = su.parentElement) {
    if (
      /(auto|scroll)/.test(win.getComputedStyle(su).overflowY) &&
      su.scrollHeight > su.clientHeight
    ) {
      return su
    }
  }
  return win.document.scrollingElement || win.document.documentElement
}

/**
 * Brings `elemento` to the middle of what scrolls it, and keeps it there while the
 * page around it is still drawing: a settings page's cards come with calls of
 * their own, and a field scrolled to once stopped where the page ended at that
 * moment (on a phone, behind the save bar). A finger, a wheel or a key leaves it
 * where the person takes it. Gives back the function that stops following.
 */
export function tieniInVista(elemento, { attesa = 1500, win = window } = {}) {
  if (!elemento?.scrollIntoView) return () => {}
  const centra = () =>
    elemento.scrollIntoView({ block: 'center', behavior: 'smooth' })
  centra()
  const box = cheLoScorre(elemento, win)
  let fotogramma = null
  let tempo = null
  // what came in moves the field: in the middle again, once per frame
  const osserva = new win.MutationObserver(() => {
    if (fotogramma === null) {
      fotogramma = win.requestAnimationFrame(() => {
        fotogramma = null
        centra()
      })
    }
  })
  const EVENTI = ['touchstart', 'wheel', 'keydown']
  function smetti() {
    osserva.disconnect()
    win.clearTimeout(tempo)
    if (fotogramma !== null) win.cancelAnimationFrame(fotogramma)
    fotogramma = null
    for (const evento of EVENTI) box.removeEventListener(evento, smetti)
  }
  osserva.observe(box, { childList: true, subtree: true })
  tempo = win.setTimeout(smetti, attesa)
  for (const evento of EVENTI) {
    box.addEventListener(evento, smetti, { passive: true })
  }
  return smetti
}
