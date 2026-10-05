// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * Notifications on this phone or computer (crm/notifiche/spinta.py): what the
 * browser can do, in the words the settings page shows, and the server's key as
 * the browser wants it. The browser's side is in `composables/spinta.js`.
 */

/** The service worker, served by the server over DottorCloud's pages. */
export const SERVICE_WORKER = '/api/method/crm.notifiche.spinta.service_worker'
export const AMBITO = '/crm'

/**
 * Where this device stands: `pronto` (it can receive them), `installa-prima`
 * (an iPhone or iPad, where only the app on the home screen can), `bloccato`
 * (notifications refused in the browser's settings), `non-supportato`.
 */
export function statoDelDispositivo({
  serviceWorker,
  pushManager,
  notification,
  permesso,
  ios,
  installata,
}) {
  if (ios && !installata) return 'installa-prima'
  if (!serviceWorker || !pushManager || !notification) return 'non-supportato'
  if (permesso === 'denied') return 'bloccato'
  return 'pronto'
}

/** What `statoDelDispositivo` needs, asked of the browser. */
export function cosaSaFare(win = window, dispositivo = {}) {
  return {
    serviceWorker: Boolean(win.navigator?.serviceWorker),
    pushManager: 'PushManager' in win,
    notification: 'Notification' in win,
    permesso: win.Notification?.permission || 'default',
    ios: Boolean(dispositivo.ios),
    installata: Boolean(dispositivo.installata),
  }
}

/** The server's public key (base64url) as `pushManager.subscribe` takes it. */
export function chiaveDelServer(base64url) {
  const base64 = String(base64url || '')
    .replace(/-/g, '+')
    .replace(/_/g, '/')
  const pieno = base64 + '='.repeat((4 - (base64.length % 4)) % 4)
  const binario = atob(pieno)
  return Uint8Array.from(binario, (carattere) => carattere.charCodeAt(0))
}

/** A digest's bytes as the server writes them: hexadecimal, lower case. */
export function esadecimale(buffer) {
  return Array.from(new Uint8Array(buffer), (byte) =>
    byte.toString(16).padStart(2, '0'),
  ).join('')
}

/**
 * Where a notification touched opens, as the app's router takes it: its path
 * without /crm, never another site's.
 */
export function percorsoDellApp(url) {
  try {
    const indirizzo = new URL(url, 'https://dottorcloud.invalid')
    if (
      indirizzo.origin !== 'https://dottorcloud.invalid' ||
      !/^\/crm(\/|$)/.test(indirizzo.pathname)
    )
      return null
    const percorso = indirizzo.pathname.replace(/^\/crm/, '') || '/'
    return percorso + indirizzo.search + indirizzo.hash
  } catch {
    return null
  }
}
