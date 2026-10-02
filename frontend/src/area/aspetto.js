// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt
//
// How the area draws what it shows, as the brand's phone screens do: the time
// heading the next appointment ("ven 2 ott · 10:00", in capitals by its style),
// a day of a plan (its weekday over its number), a kind of plan in its
// category's cloud, and how far today is. Pure: the page's language comes in.

// the design system's categories (cat-*); none of these, the brand's own
export const CATEGORIE = ['amber', 'violet', 'green', 'blue', 'rose']

function data(value) {
  if (!value) return null
  const testo = String(value).replace(' ', 'T')
  // a day alone is that day where the person is, not at midnight in London
  const date = new Date(
    /^\d{4}-\d{2}-\d{2}$/.test(testo) ? `${testo}T00:00` : testo,
  )
  return isNaN(date) ? null : date
}

// "ven 2 ott · 10:00": the day, short, and the time on the 24-hour clock
export function intestazione(value, locale = 'it-IT') {
  const date = data(value)
  if (!date) return ''
  const giorno = date
    .toLocaleDateString(locale, {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
    })
    .replace(/\./g, '')
    .replace(/,/g, '')
  const ora = date.toLocaleTimeString(locale, {
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  })
  return `${giorno} · ${ora}`
}

// a moment's time, as the server sends a time of day ("7:30:00"): "07:30"
export function ora(valore) {
  const [ore, minuti] = String(valore || '').split(':')
  if (!/^\d{1,2}$/.test(ore || '') || !/^\d{2}/.test(minuti || '')) return ''
  return `${ore.padStart(2, '0')}:${minuti.slice(0, 2)}`
}

// a day in the row of a plan's days: "mer" over "14"
export function giorno(value, locale = 'it-IT') {
  const date = data(value)
  if (!date) return { settimana: '', numero: '' }
  return {
    settimana: date
      .toLocaleDateString(locale, { weekday: 'short' })
      .replace(/\./g, ''),
    numero: String(date.getDate()),
  }
}

// a kind of plan as the server describes it (crm.piani.api.descrivi_tipo): its
// category's colour, if it is one of the system's, and its icon
export function aspetto(piano) {
  const colore = CATEGORIE.includes(piano?.colour) ? piano.colour : ''
  return { colore, icona: piano?.icon || '' }
}

// how far the day is: what was done, wholly or partly, of what is planned (as
// crm.piani.area counts it for the first screen)
export function avanzamento(momenti) {
  const voci = (momenti || []).flatMap((m) => m.items || [])
  return {
    fatte: voci.filter((v) => v.outcome === 'Done' || v.outcome === 'Partly')
      .length,
    tutte: voci.length,
  }
}
