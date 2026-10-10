// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * The carriers the centre's phone may go through, one at a time (doc 64):
 * Twilio or Telnyx. Each has its page in Settings > Phone > Telephony
 * (`<name>-settings`). The words are English, translated where they are drawn.
 */

export const OPERATORI = [
  { name: 'twilio', label: 'Twilio' },
  { name: 'telnyx', label: 'Telnyx' },
]

/** Where each carrier's calls live on the server, by what they do. */
const MODULI = {
  twilio: {
    numeri: 'crm.telephony.numeri',
    verificati: 'crm.telephony.verificati',
    trasloco: 'crm.telephony.trasloco',
  },
  telnyx: {
    numeri: 'crm.telephony.telnyx.numeri',
    verificati: 'crm.telephony.telnyx.verificati',
    trasloco: 'crm.telephony.telnyx.trasloco',
  },
}

/** A carrier's module for a kind of call: `moduloDi('telnyx', 'numeri')`. */
export function moduloDi(nome, cosa) {
  return (MODULI[nome] || MODULI.twilio)[cosa]
}

/** A carrier's name as people read it: 'Telnyx'. */
export function nomeDellOperatore(nome) {
  return OPERATORI.find((o) => o.name === nome)?.label || ''
}

/**
 * What the telephony page says of a carrier, as [sentence, values]: connected,
 * waiting for the other one to be disconnected, or to connect.
 */
export function rigaDellOperatore(nome, altroAcceso = '', acceso = false) {
  const etichetta = nomeDellOperatore(nome) || nome
  if (acceso) {
    return ['Connected: calls and messages go through {0}.', [etichetta]]
  }
  if (altroAcceso) {
    return [
      'The phone goes through {0} now: disconnect it to use {1} instead.',
      [altroAcceso, etichetta],
    ]
  }
  return [
    'Connect your {0} account: calls and messages from {brand}.',
    [etichetta],
  ]
}
