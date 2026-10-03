// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * Android's back, and the browser's, closes what lies on top - a sheet, a
 * menu, a list, a panel of the page - before it leaves the page, as a phone's
 * own apps do. It left the page, and a note half written with it.
 *
 * No entry is added to the history: when a back arrives while something lies
 * on top, the router's guard closes it and cancels the navigation, and the
 * router puts the address back by itself (it moves forward again, silently).
 */

// what lies on top: a dialog (a sheet on a phone), a menu, a select's list, a
// link field's list
const SOPRA = [
  ".dialog-content[data-state='open']",
  "[data-reka-popper-content-wrapper] > [role='menu']",
  "[data-reka-popper-content-wrapper] > [role='listbox']",
  "[data-reka-popper-content-wrapper] > [role='dialog']",
].join(', ')

// panels of a page a back closes first (the agenda's): the last one opened first
const pannelli = []

/**
 * A panel of the page a back closes before leaving it: `chiudi` closes it.
 * Gives back the function that takes it off, when the panel closes.
 */
export function chiudeConIndietro(chiudi) {
  pannelli.push(chiudi)
  return () => {
    const dove = pannelli.lastIndexOf(chiudi)
    if (dove >= 0) pannelli.splice(dove, 1)
  }
}

/** Whether something lies over the page that a back closes first. */
export function qualcosaSopra(documento = document) {
  return Boolean(documento.querySelector(SOPRA)) || pannelli.length > 0
}

/** Closes what lies on top: a dialog or a list as Escape does, else the last panel. */
export function chiudiSopra(documento = document) {
  if (documento.querySelector(SOPRA)) {
    const dove = documento.activeElement || documento.body
    dove.dispatchEvent(
      new KeyboardEvent('keydown', {
        key: 'Escape',
        code: 'Escape',
        keyCode: 27,
        bubbles: true,
        cancelable: true,
      }),
    )
    return
  }
  pannelli.at(-1)?.()
}

/**
 * Whether the router is going to `to` because the history moved (a back, a
 * forward): the browser has already put that entry's state in place, while a
 * navigation of the app's own (a link, a push) runs its guards before its
 * entry exists. The router writes in each entry the address it holds.
 */
export function dallaCronologia(to, stato) {
  return Boolean(stato?.current) && stato.current === to.fullPath
}

/**
 * From now on a back, while something lies on top, closes it instead of
 * leaving the page: the guard cancels the navigation, and the router moves
 * the history forward again by itself. Gives back the function that stops it.
 */
export function chiudiPrimaDiTornare(router, win = window) {
  return router.beforeEach((to, from) => {
    if (to.fullPath === from.fullPath) return true
    if (!dallaCronologia(to, win.history.state)) return true
    if (!qualcosaSopra(win.document)) return true
    chiudiSopra(win.document)
    return false
  })
}
