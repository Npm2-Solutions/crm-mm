// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// The person's journey on their page (crm/clienti/percorso.py, the design
// system's PatientJourney): the five steps' names and the words under each.
// The steps and their state come from the server, from the centre's data.

// what each step is called; the clinic says «Visit» for «Comes in»
export const NOMI = {
  arrived: 'Arrives',
  booked: 'Books',
  came: 'Comes in',
  after: 'After',
  home: 'At home',
}

// Under a step done: through what, and when - «Instagram · 2 Sep». Under the
// one under way, when the person is expected - «Today, 10:30». Nothing under
// the next ones. `giorno` formats a date, `t` translates.
export function sottotitolo(tappa, { oggi, giorno, t = (testo) => testo }) {
  if (!tappa) return ''
  if (tappa.state === 'done') {
    const cosa = tappa.detail ? maiuscola(t(tappa.detail)) : ''
    const quando = tappa.on ? giorno(tappa.on.slice(0, 10)) : ''
    return [cosa, quando].filter(Boolean).join(' · ')
  }
  if (tappa.expected) {
    const [data, ora] = tappa.expected.split(' ')
    return data === oggi
      ? t('Today, {0}', [ora])
      : [giorno(data), ora].filter(Boolean).join(', ')
  }
  return ''
}

// «instagram» as a campaign tags it reads «Instagram»
function maiuscola(testo) {
  return testo ? testo.charAt(0).toUpperCase() + testo.slice(1) : testo
}
