// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * Where a document linked to a record being deleted opens in DottorCloud, or
 * null when it has no page of its own: the delete dialog draws the link only
 * where it leads somewhere. It opened `/crm//` for a deal, an appointment or
 * anything it did not know, a task's or a note's list without the task or the
 * note, and the Desk for a notification.
 */
const PAGINE = {
  'CRM Lead': (nome) => `/crm/persone/${nome}`,
  'CRM Deal': (nome) => `/crm/deals/${nome}`,
  Contact: (nome) => `/crm/contacts/${nome}`,
  'CRM Organization': (nome) => `/crm/organizations/${nome}`,
  // the agenda opens it on its panel
  'CRM Appointment': (nome) => `/crm/calendar?appointment=${nome}`,
}

export function indirizzoDelCollegato(collegato) {
  const pagina = PAGINE[collegato?.reference_doctype]
  const nome = collegato?.reference_docname
  return pagina && nome ? pagina(encodeURIComponent(nome)) : null
}
