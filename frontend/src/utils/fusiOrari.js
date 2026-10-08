// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// The time zones a centre picks its agenda's from: each by its city and what
// it is called in the reader's language («Roma · Ora dell'Europa centrale»,
// never «Europe/Rome»), the device's and Italy's first, the rest by their
// cities. On a phone the list is a sheet of rows: Rome was two hundred down.

export const ITALIA = 'Europe/Rome'

// Europe's cities where Italian names them otherwise than the zone's name
// (CLDR's exemplar cities): the zones a centre in Europe keeps its clock on.
// The rest are read as the zone writes them, in English as in Italian.
const CITTA_IN_ITALIANO = {
  'Atlantic/Azores': 'Azzorre',
  'Atlantic/Canary': 'Canarie',
  'Europe/Athens': 'Atene',
  'Europe/Belgrade': 'Belgrado',
  'Europe/Berlin': 'Berlino',
  'Europe/Brussels': 'Bruxelles',
  'Europe/Bucharest': 'Bucarest',
  'Europe/Busingen': 'Büsingen',
  'Europe/Copenhagen': 'Copenaghen',
  'Europe/Dublin': 'Dublino',
  'Europe/Gibraltar': 'Gibilterra',
  'Europe/Isle_of_Man': 'Isola di Man',
  'Europe/Kiev': 'Kiev',
  'Europe/Kyiv': 'Kiev',
  'Europe/Lisbon': 'Lisbona',
  'Europe/Ljubljana': 'Lubiana',
  'Europe/London': 'Londra',
  'Europe/Luxembourg': 'Lussemburgo',
  'Europe/Moscow': 'Mosca',
  'Europe/Paris': 'Parigi',
  'Europe/Prague': 'Praga',
  'Europe/Rome': 'Roma',
  'Europe/Simferopol': 'Sinferopoli',
  'Europe/Stockholm': 'Stoccolma',
  'Europe/Tirane': 'Tirana',
  'Europe/Vatican': 'Città del Vaticano',
  'Europe/Warsaw': 'Varsavia',
  'Europe/Zagreb': 'Zagabria',
  'Europe/Zurich': 'Zurigo',
}

/**
 * A zone's city in `lingua` («Roma», «Rome», «New York»); a zone that is no
 * place («UTC») as it is written.
 */
export function cittaDelFuso(zona, lingua = 'it') {
  if (!zona) return ''
  if (String(lingua || 'it').startsWith('it') && CITTA_IN_ITALIANO[zona])
    return CITTA_IN_ITALIANO[zona]
  return zona.split('/').pop().replace(/_/g, ' ')
}

// Europe's zones out of the continent's names (the server's `lingue.fusi_europei`)
const ATLANTICO = ['Atlantic/Azores', 'Atlantic/Canary', 'Atlantic/Madeira']

/** The zones of `zone` a centre in Europe keeps its clock on, in order. */
export function europei(zone = []) {
  return [
    ...new Set(
      zone.filter(
        (zona) => zona.startsWith('Europe/') || ATLANTICO.includes(zona),
      ),
    ),
  ].sort()
}

// the generic name does not change with the day: asked once per zone and
// language, as a formatter for each of four hundred zones took a tenth of a
// second of the settings' page every time its list was drawn again
const NOMI = new Map()

/** What a zone is called in `lingua` («Ora dell'Europa centrale»), or nothing. */
export function nomeDelFuso(zona, lingua = 'it', quando) {
  const chiave = `${lingua}|${zona}`
  if (!quando && NOMI.has(chiave)) return NOMI.get(chiave)
  let nome = ''
  try {
    const parti = new Intl.DateTimeFormat(lingua, {
      timeZone: zona,
      timeZoneName: 'longGeneric',
    }).formatToParts(quando || new Date())
    nome = parti.find((parte) => parte.type === 'timeZoneName')?.value || ''
  } catch {
    // a zone the browser does not know: no name
  }
  if (!quando) NOMI.set(chiave, nome)
  return nome
}

/**
 * The choices: the device's zone and Italy's first, then every other by its
 * city; the stored one kept even when the browser does not list it. A name
 * that only says the offset («GMT+00:00») adds nothing and is left out.
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
  const scelta = (zona) => {
    const citta = cittaDelFuso(zona, lingua)
    const nome = nomeDelFuso(zona, lingua)
    return {
      value: zona,
      label: nome && !nome.startsWith('GMT') ? `${citta} · ${nome}` : citta,
    }
  }
  const ordine = new Intl.Collator(lingua)
  return [
    ...prime.map(scelta),
    ...tutte
      .filter((zona) => !prime.includes(zona))
      .map(scelta)
      .sort((a, b) => ordine.compare(a.label, b.label)),
  ]
}
