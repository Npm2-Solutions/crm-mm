// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * Who a person is to the centre (`CRM Lead.relationship`, crm/clienti): a lead
 * until the first time they come or buy - stored as "Contact", read «Lead» -,
 * then a client; with the clinic, a patient, a step above
 * (crm/clinica/paziente.py). The words are English, translated where they are
 * drawn; the tone is the design system's tag (`CategoryTag`).
 */

export const CONTATTO = 'Contact'
export const CLIENTE = 'Client'
export const PAZIENTE = 'Patient'

/**
 * The context its words are translated in: with the clinic on, the bare
 * "Client" reads "Patient" (the invoice's, crm/clinica/parole.py), and a
 * client of a Pilates class is not one.
 */
export const CONTESTO = 'Relationship'

const TONI = { [CLIENTE]: 'brand', [PAZIENTE]: 'rose' }

/** The step, from what the person carries: the stored one, else its dates. */
export function rapportoDi(persona = {}) {
  if (persona.relationship === PAZIENTE || persona.patient_since)
    return PAZIENTE
  if (persona.relationship === CLIENTE || persona.client_since) return CLIENTE
  return CONTATTO
}

/** Its tag's tone; none for a contact, who is everybody else. */
export function tonoDel(rapporto) {
  return TONI[rapporto] || ''
}

/**
 * The fact that opens the head of a person's page: the step, and since when
 * when the person says so. A sentence and its date, for the translator.
 */
export function fattoDel(persona = {}) {
  const rapporto = rapportoDi(persona)
  if (rapporto === PAZIENTE && persona.patient_since)
    return { frase: 'Patient since {0}', data: persona.patient_since }
  if (rapporto === CLIENTE && persona.client_since)
    return { frase: 'Client since {0}', data: persona.client_since }
  return { frase: rapporto, data: null }
}

/**
 * The People list's quick views (docs/progetto-ghl/54): everybody, then each
 * step, plural - the leads, the clients, with the clinic its patients. One
 * list of people, each a step of theirs: never a list of leads beside it.
 */
const VISTE = {
  [CONTATTO]: 'Leads',
  [CLIENTE]: 'Clients',
  [PAZIENTE]: 'Patients',
}

/**
 * The views, from the steps the field holds here (`opzioni`: its options, as
 * strings or `{ value }`): «All» first, its value empty. Words to translate:
 * the steps' in `CONTESTO`.
 */
export function vistePerRapporto(opzioni = []) {
  const passi = (opzioni || [])
    .map((opzione) =>
      typeof opzione === 'string' ? opzione : opzione?.value || '',
    )
    .filter((valore, i, tutti) => VISTE[valore] && tutti.indexOf(valore) === i)
  return [
    { valore: '', etichetta: 'All', contesto: null },
    ...passi.map((valore) => ({
      valore,
      etichetta: VISTE[valore],
      contesto: CONTESTO,
    })),
  ]
}
