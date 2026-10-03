// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * The tab one is on, tapped again in the bar at the bottom, takes its page
 * back to the top, as a phone's own apps do. frappe-ui scrolls the frame it
 * knows (`scrollToTop`), but a phone's list scrolls in a box of its own
 * (components/Mobile/): the tap did nothing one could see.
 */

const BARRA = "nav[data-slot='mobile-nav']"
const SCATOLE = ':is(.overflow-y-auto, .overflow-auto, .overflow-y-scroll)'

// what a page does first when its tab is tapped again (the last one wins)
const azioni = []

/**
 * What the tab of the page one is on does, tapped again, before taking the
 * page to the top: `fai()` gives back true when it did something - a
 * conversation open goes back to the list of them, as a phone's own apps do.
 * Gives back the function that takes it off.
 */
export function alToccoDellaScheda(fai) {
  azioni.push(fai)
  return () => {
    const dove = azioni.lastIndexOf(fai)
    if (dove >= 0) azioni.splice(dove, 1)
  }
}

/** The boxes of the page that are scrolled down: not the bar's, nor a sheet's. */
export function scatoleScorse(radice) {
  return [...radice.querySelectorAll(SCATOLE)].filter(
    (el) =>
      el.scrollTop > 0 &&
      !el.closest(BARRA) &&
      !el.closest('.dialog-scroll-container'),
  )
}

/**
 * From now on a tap on the bar's tab of the page one is on brings what the
 * page scrolled back to the top. Gives back the function that stops it.
 */
export function allaCimaConLaScheda(win = window) {
  const doc = win.document
  function alClic(evento) {
    const voce = evento.target.closest?.(`${BARRA} [aria-current='page']`)
    if (!voce) return
    if (azioni.at(-1)?.()) return
    const radice = doc.querySelector('[data-cornice-telefono]') || doc.body
    for (const el of scatoleScorse(radice)) {
      el.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }
  doc.addEventListener('click', alClic)
  return () => doc.removeEventListener('click', alClic)
}
