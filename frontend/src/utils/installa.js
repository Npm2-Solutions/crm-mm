// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * DottorCloud on the phone's home screen: it opens like an app, full screen,
 * without the browser's bars, with its own icon. Android's browser offers to
 * install it (`beforeinstallprompt`), and a button asks; an iPhone has no such
 * offer, so the More page says the two taps that do it in Safari. Nothing is
 * said once it is installed, or once somebody said «not now» on this phone.
 */

import { ref } from 'vue'

/** The browser's offer to install, kept for the button that asks. */
export const offertaDiInstallazione = ref(null)

/**
 * What the More page offers: `pulsante` (the browser's own offer, a tap
 * away), `ios` (Safari's Share, then Add to Home Screen), `android` (the
 * browser's menu) or `nulla` (installed already, dismissed, or a computer).
 */
export function comeInstallare({
  installata,
  scartata,
  offerta,
  ios,
  android,
}) {
  if (installata || scartata) return 'nulla'
  if (offerta) return 'pulsante'
  if (ios) return 'ios'
  if (android) return 'android'
  return 'nulla'
}

/** What this device is, for `comeInstallare`. */
export function questoDispositivo(win = window) {
  const nav = win.navigator || {}
  const agente = nav.userAgent || ''
  return {
    installata:
      nav.standalone === true ||
      Boolean(win.matchMedia?.('(display-mode: standalone)').matches),
    // iPadOS says it is a Mac, with a touch screen
    ios:
      /iPad|iPhone|iPod/.test(agente) ||
      (nav.platform === 'MacIntel' && nav.maxTouchPoints > 1),
    android: /Android/i.test(agente),
  }
}

/**
 * From now on the browser's offer to install is kept for the More page's
 * button, instead of its own bar at the bottom of the page.
 */
export function ascoltaLInstallazione(win = window) {
  win.addEventListener('beforeinstallprompt', (evento) => {
    evento.preventDefault()
    offertaDiInstallazione.value = evento
  })
  win.addEventListener('appinstalled', () => {
    offertaDiInstallazione.value = null
  })
}
