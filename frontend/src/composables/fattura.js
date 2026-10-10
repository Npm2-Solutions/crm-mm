// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * The invoice dialog, opened from anywhere (the console, the agenda, a cycle, a
 * subscription, a person's history) and mounted once in GlobalModals.
 */
import { call, toast } from 'frappe-ui'
import { reactive } from 'vue'

const stato = reactive({
  aperto: false,
  // the invoice to open, or nothing for a new one
  nome: null,
  // a new invoice's client: { party_type, party }
  cliente: null,
  // what a new invoice starts from, when something proposes it (an appointment):
  // the client, the lines, the appointment it closes - completed in the dialog
  bozza: null,
  // told when the invoice is saved, issued or thrown away
  alCambio: null,
  // one more each time somebody opens one: the dialog loads it then, and only then
  // (saving a new invoice gives it a name without opening it again)
  richiesta: 0,
})

function apriFattura(nome, { alCambio } = {}) {
  Object.assign(stato, {
    nome,
    cliente: null,
    bozza: null,
    alCambio: alCambio || null,
  })
  stato.aperto = true
  stato.richiesta++
}

function nuovaFattura(cliente = null, { alCambio, bozza } = {}) {
  Object.assign(stato, {
    nome: null,
    cliente,
    bozza: bozza || null,
    alCambio: alCambio || null,
  })
  stato.aperto = true
  stato.richiesta++
}

/**
 * An appointment that happened, invoiced: the agenda knows the client, the
 * service and when. When it cannot tell who performed it, the dialog opens with
 * what it knows and asks only that, instead of an error with nowhere to go;
 * else the draft the agenda filled in opens, to check and issue. The invoices'
 * page and the reception desk invoice an appointment this one way.
 */
async function fatturaDellIncontro(
  appuntamento,
  { alCambio, partecipante } = {},
) {
  // a class is invoiced a place at a time: whose, or the server's next one
  const chi = { appointment: appuntamento, participant: partecipante || '' }
  try {
    const proposta = await call(
      'crm.invoicing.api.appointment_invoice_proposal',
      chi,
    )
    if (!proposta.items.every((riga) => riga.service_provider)) {
      nuovaFattura(null, { alCambio, bozza: proposta })
      return
    }
    const nome = await call('crm.invoicing.api.issue_from_appointment', chi)
    alCambio?.()
    apriFattura(nome, { alCambio })
  } catch (errore) {
    // The commonest one is a service with no fiscal card, and saying so is more
    // use than a generic failure: it names the thing to go and configure.
    toast.error(errore.messages?.[0] || __('Could not open the invoice'))
  }
}

export function useFattura() {
  return {
    stato,
    apriFattura,
    nuovaFattura,
    fatturaDellIncontro,
    chiudiFattura() {
      stato.aperto = false
    },
  }
}
