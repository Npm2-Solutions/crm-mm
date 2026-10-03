// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * Back to a list finds it as it was left - the words in its search, the rows
 * it had loaded, how far down it was - as a phone's own apps do. Opening a
 * person and coming back started again from the top, the search gone.
 *
 * Only a back (or a forward) puts a list back: opened from the menu or a link
 * it starts from the top, as a page does in a browser. What is kept stays in
 * memory for the session: what was searched (a name) is never written on the
 * device.
 */

import { dallaCronologia } from '@/utils/indietro'

const liste = new Map()
let dallaCronologiaUltima = false

/**
 * From now on every navigation notes whether the history moved (a back, a
 * forward): only then does a list come back as it was. Gives back the
 * function that stops it.
 */
export function segnaIRitorni(router, win = window) {
  return router.beforeEach((to) => {
    dallaCronologiaUltima = dallaCronologia(to, win.history.state)
  })
}

/** Keeps what list `chiave` was like, for when a back returns to it. */
export function conserva(chiave, stato) {
  liste.set(chiave, stato)
}

/** What list `chiave` was like, when a back is returning to it; else null. */
export function ritrova(chiave) {
  return (dallaCronologiaUltima && liste.get(chiave)) || null
}

/** Forgets every list (a test, a session that ends). */
export function dimenticaTutto() {
  liste.clear()
  dallaCronologiaUltima = false
}

/**
 * The rows of pages asked one by one, each once: a row that moved from one
 * page to the next while they were asked (a person just changed goes to the
 * top) is not drawn twice.
 */
export function senzaDoppioni(righe, chiave = 'name') {
  const viste = new Set()
  return righe.filter((riga) => {
    const nome = riga?.[chiave]
    if (nome == null) return true
    if (viste.has(nome)) return false
    viste.add(nome)
    return true
  })
}

/**
 * Brings `box` back down to `y`: at once when its rows are there, else as they
 * come, for a few seconds. A finger on the box, or a wheel, leaves it where the
 * person takes it. Gives back the function that stops waiting.
 */
export function rimettiLoScorrimento(box, y, attesa = 3000) {
  if (!box || !(y > 0)) return () => {}
  const prova = () => {
    box.scrollTop = y
    return box.scrollTop >= y - 1
  }
  if (prova()) return () => {}
  let osserva = null
  let tempo = null
  function smetti() {
    osserva?.disconnect()
    clearTimeout(tempo)
    box.removeEventListener('touchstart', smetti)
    box.removeEventListener('wheel', smetti)
  }
  osserva = new MutationObserver(() => {
    if (prova()) smetti()
  })
  osserva.observe(box, { childList: true, subtree: true })
  tempo = setTimeout(smetti, attesa)
  box.addEventListener('touchstart', smetti, { passive: true })
  box.addEventListener('wheel', smetti, { passive: true })
  return smetti
}
