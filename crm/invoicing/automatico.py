# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What leaves by itself, where the centre switched it on (Settings > Invoicing >
Advanced > Options). Both switches start off: an invoice waits for somebody to
press «Send to the SdI», an expense for «Report».

An invoice issued with `auto_send_sdi` on leaves for the SdI in a job after the
issue is committed: the issue never waits on Itala, and a failure never undoes
it. What the SdI would reject, or a send that fails, waits as it would by hand,
and whoever manages invoicing is told. The Sistema TS's night is its own module's
(`crm.tessera_sanitaria.automatico`): invoicing does not reach into it.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint

from crm.invoicing.engine.codici import Canale

IMPOSTAZIONI = "CRM Invoicing Settings"


def attivo(campo: str) -> bool:
	return bool(cint(frappe.db.get_single_value(IMPOSTAZIONI, campo)))


def da_inviare_allo_sdi(doc) -> bool:
	"""Whether an issued invoice leaves for the SdI by itself: the switch is on, it
	goes through the SdI at all, through Itala, and has not left yet."""
	if not attivo("auto_send_sdi") or doc.channel != Canale.SDI:
		return False
	if doc.sdi_status not in ("da_inviare", "", None):
		return False
	from crm.invoicing import documento
	from crm.invoicing.sdi import itala

	emittente = documento.azienda(doc)
	return (emittente.get("sdi_mode") or itala.CODICE) == itala.CODICE and itala.pronta(emittente)


def dopo_emissione(doc) -> None:
	"""Called at the end of an invoice's `on_submit`. Never raises."""
	try:
		if not da_inviare_allo_sdi(doc):
			return
	except Exception:
		frappe.log_error(title=f"Automatic SdI send {doc.name}", message=frappe.get_traceback())
		return
	frappe.enqueue(
		"crm.invoicing.automatico.invia_allo_sdi",
		invoice=doc.name,
		queue="short",
		enqueue_after_commit=True,
		job_id=f"invia-allo-sdi-{doc.name}",
		deduplicate=True,
	)


def invia_allo_sdi(invoice: str) -> dict | None:
	"""The job: send one issued invoice, as the button would. What stops it is kept
	on the invoice's log by the send itself, and said to whoever manages invoicing."""
	from crm.invoicing import api, monitoraggio

	doc = frappe.get_doc("CRM Invoice", invoice)
	# sent by hand in the meantime, or no longer to send
	if doc.docstatus != 1 or not da_inviare_allo_sdi(doc):
		return None
	try:
		return api.trasmetti(doc)
	except Exception as errore:
		frappe.db.rollback()
		monitoraggio.avvisa(
			_("An invoice did not leave for the SdI by itself"),
			doc.company,
			_("{0}: {1} It waits for «Send to the SdI».").format(
				doc.document_number or doc.name, frappe.utils.strip_html(str(errore))
			),
		)
		return None
