// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * The centre's locations, read (docs/crm/62): whether there is more than one
 * (else no screen names one), who works where on a day, a location's name and
 * its address. Pure: the agenda, the reception desk and the settings draw what
 * these say. The rules are the server's `crm/scheduling/sedi_regole.py`.
 */

/** Whether the centre has more than one location on: `sedi` as the boot gives them. */
export function piuSedi(sedi) {
  return Array.isArray(sedi) && sedi.length > 1
}

/** A location's name, by its key: '' where it is not one of `sedi`. */
export function nomeDellaSede(sedi = [], nome = '') {
  if (!nome) return ''
  return (sedi || []).find((sede) => sede.name === nome)?.title || ''
}

/** The location chosen, if it is still one of `sedi`; else '' (all of them). */
export function sedeValida(sedi = [], nome = '') {
  return nome && (sedi || []).some((sede) => sede.name === nome) ? nome : ''
}

/**
 * Whether something (a room, a line of a shift) of `sua` serves `sede`: one
 * that names no location serves them all, and no location chosen takes all.
 */
export function serve(sua, sede) {
  return !sede || !sua || sua === sede
}

/**
 * Whether a column of the agenda belongs to the location chosen on its day: a
 * room by its location; a professional by the locations their day's shifts
 * name (`delGiorno`, '' for a line good anywhere), else - their hours not known
 * that day - by the ones their week names (`diSempre`). With no location
 * chosen, everybody.
 */
export function nellaSede(
  sede,
  { stanza = undefined, delGiorno = undefined, diSempre = [] } = {},
) {
  if (!sede) return true
  if (stanza !== undefined) return serve(stanza, sede)
  const sedi = Array.isArray(delGiorno) ? delGiorno : diSempre || []
  if (!sedi.length) return !Array.isArray(delGiorno)
  return sedi.some((sua) => serve(sua, sede))
}

/** The choices of a location chooser: «All locations» first, then each. */
export function opzioniDelleSedi(sedi = [], tutte = 'All locations') {
  return [
    { value: '', label: tutte },
    ...(sedi || []).map((sede) => ({
      value: sede.name,
      label: sede.title,
      nota: sede.city || '',
    })),
  ]
}

/** «Via Roma 1, 20900 Monza (MB)», as an envelope writes it. */
export function indirizzoDellaSede(sede = {}) {
  const via = String(sede?.address_line || '')
    .split(/\s+/)
    .filter(Boolean)
    .join(' ')
  const citta = [
    String(sede?.pincode || '').trim(),
    String(sede?.city || '').trim(),
    sede?.province ? `(${String(sede.province).trim().toUpperCase()})` : '',
  ]
    .filter(Boolean)
    .join(' ')
  return [via, citta].filter(Boolean).join(', ')
}
