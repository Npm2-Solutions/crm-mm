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

/**
 * Where this browser remembers whose its notifications are: one memo for the
 * browser, not one per person. Kept per person (`crm-spinta:<user>`), a memo
 * still said «synced» to whoever signed in again after a colleague had been
 * handed the device, nothing was asked, and the colleague's notifications went
 * on arriving while they worked.
 */
export const MEMORIA = 'crm-spinta'

/**
 * What the memo says once the server knows this browser as `utente`'s: who,
 * and which subscription (its fingerprint).
 */
export function memoriaDi(utente, impronta) {
  return `${utente || ''}|${impronta || ''}`
}

/**
 * Whether an opening asks the server whose this browser is: unless the memo
 * says it is this person's, with this subscription. Somebody else was the
 * last to sync it, or nobody is remembered: the server is asked, and hands the
 * device over where it is not theirs.
 */
export function daChiedere(memoria, utente, impronta) {
  return memoria !== memoriaDi(utente, impronta)
}

/** The memos older versions kept, one per person: `crm-spinta:<user>`. */
export function memorieVecchie(chiavi) {
  return (chiavi || []).filter((chiave) =>
    String(chiave).startsWith(`${MEMORIA}:`),
  )
}

/**
 * Whether this browser keeps its subscription at a logout: only when the
 * server forgot it for the session in time (`dimenticato`), and the memo does
 * not say it was somebody else's - the server forgets only the session's own,
 * and another's would go on arriving. Kept, the device waits for whoever signs
 * in next, who is handed it at their first opening; let go, nothing reaches it.
 */
export function tieneLAbbonamento({ memoria, utente, impronta, dimenticato }) {
  return (
    Boolean(dimenticato) && (!memoria || !daChiedere(memoria, utente, impronta))
  )
}

/**
 * Whether `promessa` is kept within `millisecondi`: true when it resolves in
 * time, false when it fails or takes longer - then it is no longer waited
 * for, and goes on by itself.
 */
export function entroIlTempo(promessa, millisecondi) {
  return new Promise((risolvi) => {
    const scaduto = setTimeout(() => risolvi(false), millisecondi)
    Promise.resolve(promessa).then(
      () => {
        clearTimeout(scaduto)
        risolvi(true)
      },
      () => {
        clearTimeout(scaduto)
        risolvi(false)
      },
    )
  })
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
