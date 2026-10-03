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

import { unref } from 'vue'

// what lies on top: a dialog (a sheet on a phone), a menu, a select's list, a
// link field's list
const SOPRA = [
  ".dialog-content[data-state='open']",
  "[data-reka-popper-content-wrapper] > [role='menu']",
  "[data-reka-popper-content-wrapper] > [role='listbox']",
  "[data-reka-popper-content-wrapper] > [role='dialog']",
].join(', ')

// panels a back closes first (the agenda's, a page of the settings): the last
// one opened first
const pannelli = []

/**
 * A panel a back closes before leaving the page: `chiudi` closes it (or takes
 * it one step back). A panel inside a sheet (the settings) gives its element,
 * a ref or a node: a back closes it before the sheet that holds it. Gives
 * back the function that takes it off, when the panel closes.
 */
export function chiudeConIndietro(chiudi, elemento = null) {
  const voce = { chiudi, elemento }
  pannelli.push(voce)
  return () => {
    const dove = pannelli.lastIndexOf(voce)
    if (dove >= 0) pannelli.splice(dove, 1)
  }
}

/** Whether something lies over the page that a back closes first. */
export function qualcosaSopra(documento = document) {
  return Boolean(documento.querySelector(SOPRA)) || pannelli.length > 0
}

/**
 * Closes what lies on top: a panel inside the sheet on top, else the sheet or
 * the list as Escape does, else the last panel of the page.
 */
export function chiudiSopra(documento = document) {
  const sopra = [...documento.querySelectorAll(SOPRA)].at(-1)
  if (sopra) {
    // [...].reverse(): toReversed() is missing on an older phone's browser
    const dentro = [...pannelli]
      .reverse()
      .find((voce) => sopra.contains(unref(voce.elemento) || null))
    if (dentro) {
      dentro.chiudi()
      return
    }
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
  pannelli.at(-1)?.chiudi()
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

/**
 * Whether the crumb at `percorso` leads where the history came from
 * (`indietro`, the router's `history.state.back`): the same page, and the same
 * view of it when the crumb names one.
 */
export function stessoPosto(router, percorso, indietro) {
  if (!percorso || !indietro) return false
  const crumb = router.resolve(percorso)
  const prima = router.resolve(indietro)
  if (!crumb.name || crumb.name !== prima.name) return false
  if ((crumb.query.view || '') !== (prima.query.view || '')) return false
  const tipo = crumb.params.viewType
  return !tipo || tipo === prima.params.viewType
}

/**
 * On a phone the crumb a page came from («People» over a person) takes it
 * back, to the list as it was left (utils/ritorno.js), instead of opening that
 * page anew from the top. An iPhone's installed app has no swipe back: the
 * crumb is the way back. A tab of the bar at the bottom does the same: from a
 * person opened from the list, «People» is the list as it was. A crumb or a
 * tab that leads anywhere else goes there as it always did. Gives back the
 * function that stops it.
 */
export function tornaConLeBriciole(router, win = window) {
  const base = router.options.history?.base || ''
  function alClic(evento) {
    if (evento.defaultPrevented || evento.button !== 0) return
    if (evento.metaKey || evento.ctrlKey || evento.shiftKey || evento.altKey)
      return
    const link = evento.target.closest?.(
      "#app-header a[href], nav[data-slot='mobile-nav'] a[href]",
    )
    if (!link) return
    let percorso = link.getAttribute('href')
    if (base && percorso.startsWith(base)) {
      percorso = percorso.slice(base.length) || '/'
    }
    const qui = router.currentRoute.value
    if (router.resolve(percorso).name === qui.name) return
    if (!stessoPosto(router, percorso, win.history.state?.back)) return
    evento.preventDefault()
    router.back()
  }
  win.document.addEventListener('click', alClic, true)
  return () => win.document.removeEventListener('click', alClic, true)
}
