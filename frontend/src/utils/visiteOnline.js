// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * Online visits on the staff's screens (crm.scheduling.visite_online): the
 * agenda's panel and the reception desk start one from its room's link, which
 * the server made or the desk pasted. The person enters from their area, never
 * from here. Pure, so the screens only draw.
 */

const HTTPS = /^https:\/\/[^\s/?#]+[^\s]*$/i

/** Whether a link may be a room's: an https address, as the server checks. */
export function linkValido(link) {
  return HTTPS.test(String(link || '').trim())
}

/**
 * The room to start, for an appointment not cancelled that has its link;
 * null otherwise.
 */
export function linkDellaVisita(appuntamento) {
  if (!appuntamento || appuntamento.status === 'Cancelled') return null
  const link = String(appuntamento.video_link || '').trim()
  return linkValido(link) ? link : null
}

/**
 * What the panel says of an appointment's online visit: 'avvia' with a room to
 * start, 'senza' for an online visit without one yet, null for the rest.
 */
export function statoDellaVisitaOnline(appuntamento) {
  if (!appuntamento || appuntamento.status === 'Cancelled') return null
  if (linkDellaVisita(appuntamento)) return 'avvia'
  return appuntamento.online_visit ? 'senza' : null
}

/** Opens the room in a tab of its own, which knows nothing of DottorCloud's. */
export function avviaLaVisita(link, finestra = globalThis.window) {
  const url = linkDellaVisita({ video_link: link })
  if (!url) return false
  finestra.open(url, '_blank', 'noopener')
  return true
}
