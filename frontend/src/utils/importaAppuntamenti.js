// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// The appointments brought over from the previous software
// (crm/importazione/appuntamenti.py), in words: what each column was read as,
// what happens to a row, how it went, the choices for what the sheet names, the
// report at the end.

/** A column the sheet was read by, in the reader's words. */
export const CAMPI = {
  full_name: 'Full name',
  first_name: 'First name',
  last_name: 'Last name',
  email: 'Email',
  mobile_no: 'Mobile',
  phone: 'Phone',
  fiscal_code: 'Fiscal code',
  birth_date: 'Date of birth',
  date: 'Day',
  start: 'Start time',
  end: 'End time',
  duration: 'Duration',
  service: 'Service',
  professional: 'Professional',
  room: 'Room',
  status: 'How it went',
  notes: 'Notes',
  external_id: 'Code in the previous software',
}

/** What happens to a row of the preview. */
export function esitoDellaRiga(riga, t = (s) => s) {
  if (riga.outcome === 'left_out') return riga.problems?.join('; ') || ''
  const parole = {
    already: t('Already brought in'),
    found: t('Already here'),
    new_person: t('New person'),
    nobody: t(
      'Nobody here by this name: bring the people over first, or add their fiscal code, email or mobile',
    ),
  }
  const testo = parole[riga.outcome] || ''
  return riga.problems?.length
    ? `${testo} · ${riga.problems.join('; ')}`
    : testo
}

/** How an appointment went, as the import reads it. */
export function statoDellAppuntamento(stato, t = (s) => s) {
  return (
    {
      Completed: t('Took place'),
      'No Show': t('Did not come', null, 'One person'),
      Cancelled: t('Cancelled'),
      Scheduled: t('Booked'),
    }[stato] || stato
  )
}

/** The choices of a name the sheet writes: what the centre has, and the way out. */
export function scelteDi(tipo, opzioni, t = (s) => s) {
  const fuori = {
    services: {
      value: '__other__',
      label: t('Other (a new service)'),
    },
    professionals: { value: '', label: t('Nobody') },
    rooms: { value: '', label: t('No room') },
  }[tipo]
  return [...(opzioni || []), fuori]
}

/** The choices as the server takes them: `{services: {name: value}, …}`. */
export function scelteDaMandare(anteprima) {
  const di = (righe) =>
    Object.fromEntries((righe || []).map((r) => [r.name, r.choice || '']))
  return {
    services: di(anteprima?.services),
    professionals: di(anteprima?.professionals),
    rooms: di(anteprima?.rooms),
  }
}

/** The report at the end, in one sentence and the rows not brought in. */
export function resoconto(esito, t = (s) => s) {
  if (!esito) return null
  const errori = esito.errors || []
  return {
    frase: t(
      'Appointments brought in: {0}. New people: {1}. Already brought in before: {2}. Left out: {3}. Not brought in: {4}.',
    )
      .replace('{0}', esito.created || 0)
      .replace('{1}', esito.new_people || 0)
      .replace('{2}', esito.already || 0)
      .replace('{3}', (esito.left_out || 0) + (esito.nobody || 0))
      .replace('{4}', errori.length),
    errori: errori.map((e) =>
      t('Row {0}: {1}').replace('{0}', e.row).replace('{1}', e.error),
    ),
  }
}
