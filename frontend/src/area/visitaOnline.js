// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * «Enter the visit» on an online visit (crm.area.api.enter_online_visit): whether
 * the button shows now. The server says in how many seconds the door opens and
 * closes from when it answered (`online_visit`), and at what time of the centre's
 * clock it opens: the phone's clock may not be the centre's. The room's link
 * comes only from the call, when the person taps. Pure, so the card only draws.
 */

/**
 * Where the door stands, `trascorsi` milliseconds after the server answered:
 * 'aperta' while one enters, 'presto' before, 'senza' for an online visit with
 * no room yet, null when there is nothing to say (over, not online, cancelled).
 */
export function statoDellaVisita(appuntamento, trascorsi = 0) {
  if (!appuntamento?.online || appuntamento.status === 'Cancelled') return null
  const finestra = appuntamento.online_visit
  if (!finestra) return appuntamento.hidden ? null : 'senza'
  const secondi = Math.max(Number(trascorsi) || 0, 0) / 1000
  if (secondi >= Number(finestra.closes_in || 0)) return null
  if (secondi < Number(finestra.opens_in || 0)) return 'presto'
  return 'aperta'
}

/** In how many milliseconds the state changes next: to look again then. */
export function prossimoCambioDellaVisita(appuntamento, trascorsi = 0) {
  const finestra = appuntamento?.online_visit
  if (!finestra || appuntamento.status === 'Cancelled') return null
  const adesso = Math.max(Number(trascorsi) || 0, 0)
  const cambi = [finestra.opens_in, finestra.closes_in]
    .map((s) => Number(s || 0) * 1000 - adesso)
    .filter((ms) => ms > 0)
  return cambi.length ? Math.min(...cambi) : null
}

/**
 * Opens the room: in a new tab where the browser allows one opened before the
 * call answered (a tab opened after an await is a popup it blocks), else in
 * this one. `scheda` is that tab, or null.
 */
export function apriLaStanza(url, scheda, finestra = globalThis.window) {
  if (!url || !/^https:\/\//i.test(url)) {
    scheda?.close?.()
    return false
  }
  if (scheda && !scheda.closed) {
    scheda.location.href = url
    return true
  }
  finestra.location.assign(url)
  return true
}
