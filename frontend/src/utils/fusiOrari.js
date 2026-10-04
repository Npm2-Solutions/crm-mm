// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// The time zones a centre picks its agenda's from: each by its IANA name and
// what it is called in the reader's language («Europe/Rome · Ora dell'Europa
// centrale»), the device's and Italy's first. On a phone the list is a sheet of
// four hundred rows that starts at «Africa/Abidjan»: Rome was two hundred down.

export const ITALIA = 'Europe/Rome'

/** What a zone is called in `lingua` («Ora dell'Europa centrale»), or nothing. */
export function nomeDelFuso(zona, lingua = 'it', quando = new Date()) {
  try {
    const parti = new Intl.DateTimeFormat(lingua, {
      timeZone: zona,
      timeZoneName: 'longGeneric',
    }).formatToParts(quando)
    return parti.find((parte) => parte.type === 'timeZoneName')?.value || ''
  } catch {
    return ''
  }
}

/**
 * The choices: the device's zone and Italy's first, then every other in the
 * order given; the stored one kept even when the browser does not list it.
 * A name that only says the offset («GMT+00:00») adds nothing and is left out.
 */
export function fusiOrari({
  zone = [],
  scelto = '',
  dispositivo = '',
  lingua = 'it',
} = {}) {
  const tutte = [...new Set(zone)]
  if (scelto && !tutte.includes(scelto)) tutte.unshift(scelto)
  const prime = [...new Set([dispositivo, ITALIA])].filter(
    (zona) => zona && tutte.includes(zona),
  )
  return [...prime, ...tutte.filter((zona) => !prime.includes(zona))].map(
    (zona) => {
      const etichetta = zona.replace(/_/g, ' ')
      const nome = nomeDelFuso(zona, lingua)
      return {
        value: zona,
        label:
          nome && !nome.startsWith('GMT')
            ? `${etichetta} · ${nome}`
            : etichetta,
      }
    },
  )
}
