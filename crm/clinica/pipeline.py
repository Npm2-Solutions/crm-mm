# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The first seam, from marketing to the centre: a medical centre's two pipelines.

Both are the CRM's (docs/gestionale-medico, "Due pipeline"):

- **New patients**: the CRM's new clients pipeline (`crm.clienti.pipeline`), in
  the clinic's words. Requests from ads, forms and calls, to call back until the
  first visit: a booking moves an open deal to "appointment booked", becoming a
  patient wins it - a patient is a client from the same moment
  (`paziente.assicura_paziente`). The Meta report counts the won deals of each ad,
  so it says what a new patient costs.
- **Quotes**: from the quote delivered to accepted or declined
  (`crm.preventivi.pipeline`).

Switching the clinic on creates them where the centre has none. The patients found
in last year's appointments close nothing and start nothing.
"""

from __future__ import annotations

import frappe

#: The new clients pipeline in the clinic's words, in the site's language: data the
#: board shows, not strings of the interface (`crm.clienti.pipeline.registra_nomi`).
NUOVI_PAZIENTI = {
	"it": (
		"Nuovi pazienti",
		"Le richieste da pubblicità, moduli e telefonate, da richiamare fino alla prima visita.",
		(
			("Richiesta", "gray", "Open", 10),
			("Contattato", "orange", "Ongoing", 30),
			("Appuntamento fissato", "blue", "Ongoing", 60),
			("Venuto", "green", "Won", 100),
			("Non venuto", "red", "Lost", 0),
		),
	),
	"en": (
		"New patients",
		"Requests from ads, forms and calls, to call back until the first visit.",
		(
			("Request", "gray", "Open", 10),
			("Contacted", "orange", "Ongoing", 30),
			("Appointment booked", "blue", "Ongoing", 60),
			("Came", "green", "Won", 100),
			("Did not come", "red", "Lost", 0),
		),
	),
}


def crea_pipeline() -> frappe._dict:
	"""The two pipelines, wherever the settings do not point at one yet: the new
	patients, and the quotes. Idempotent."""
	from crm.clienti import pipeline as clienti
	from crm.preventivi import pipeline as preventivi

	preventivi.crea()
	return clienti.crea()
