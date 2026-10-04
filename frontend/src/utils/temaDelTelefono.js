// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// The client area wears the phone's own theme: light or dark as the phone is
// set, and it follows when the phone changes over (at sunset, in a dark room).
// The public pages do the same with their media query; the CRM keeps the theme
// each user picks in it. The design system's dark colours hang on
// `data-theme="dark"`.

export function temaDi(scuro) {
  return scuro ? 'dark' : 'light'
}

/** Sets `data-theme` on `doc`'s root from the phone's setting, and keeps it. */
export function seguiIlTemaDelTelefono(doc = document, win = window) {
  const scuro = win.matchMedia?.('(prefers-color-scheme: dark)')
  const applica = () =>
    doc.documentElement.setAttribute('data-theme', temaDi(scuro?.matches))
  applica()
  scuro?.addEventListener?.('change', applica)
  return applica
}
