// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * «I'm here» on the next appointment (crm.area.api.check_in): whether the
 * button shows now. The server says in how many seconds it opens and closes
 * from when it answered (`check_in`), never a time of day: the phone's clock
 * may not be the centre's. Pure, so the card only draws.
 */

/**
 * Where «I'm here» stands, `trascorsi` milliseconds after the server answered:
 * 'arrivato' once they said it, 'aperto' while it is offered, 'presto' before,
 * null when it is not (over, not offered, not theirs).
 */
export function statoDellArrivo(appuntamento, trascorsi = 0) {
  if (!appuntamento) return null
  if (appuntamento.arrived) return 'arrivato'
  const finestra = appuntamento.check_in
  if (!finestra) return null
  const secondi = Math.max(Number(trascorsi) || 0, 0) / 1000
  if (secondi >= Number(finestra.closes_in || 0)) return null
  if (secondi < Number(finestra.opens_in || 0)) return 'presto'
  return 'aperto'
}

/** In how many milliseconds the state changes next: to look again then. */
export function prossimoCambio(appuntamento, trascorsi = 0) {
  const finestra = appuntamento?.check_in
  if (!finestra || appuntamento.arrived) return null
  const adesso = Math.max(Number(trascorsi) || 0, 0)
  const cambi = [finestra.opens_in, finestra.closes_in]
    .map((s) => Number(s || 0) * 1000 - adesso)
    .filter((ms) => ms > 0)
  return cambi.length ? Math.min(...cambi) : null
}
