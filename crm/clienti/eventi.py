# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Where the CRM's rules listen: the agenda and invoicing.

Wired in `crm/hooks.py` as document events. A rule that fails is logged and never
stops what triggered it: an appointment that cannot be saved, or an invoice that
cannot be issued, because a deal could not move would be the wrong way round.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, get_datetime

from crm.clienti import cliente, pipeline, regole
from crm.fcrm.doctype.crm_appointment.crm_appointment import person_of


def _senza_fermare(titolo: str, doc, funzione) -> None:
	frappe.db.savepoint("clienti_regola")
	try:
		funzione()
	except Exception:
		frappe.db.rollback(save_point="clienti_regola")
		frappe.log_error(title=titolo, reference_doctype=doc.doctype, reference_name=doc.name)


def appuntamento_creato(doc, method=None) -> None:
	"""A booking moves the person's new clients deal to "appointment booked"; one
	brought over from the previous software is no news."""
	if doc.status in ("Cancelled", "No Show") or doc.flags.get("importato"):
		return

	def sposta():
		for riga in doc.participants or []:
			persona = person_of(riga.party_type, riga.party)
			if persona and riga.status != "Cancelled":
				pipeline.prenotata(persona)

	_senza_fermare(_("New clients deal not moved for appointment {0}").format(doc.name), doc, sposta)


def appuntamento_aggiornato(doc, method=None) -> None:
	"""Checked in at the desk, or an appointment attended: a client from that moment."""
	righe = doc.participants or []
	if not any(
		regole.accolto(riga.get("arrived_at"), riga.status) or regole.presente(doc.status, riga.status)
		for riga in righe
	):
		return

	# brought over from the previous software: a client from then, and no news
	annuncia = not doc.flags.get("importato")

	def registra():
		for riga in righe:
			persona = person_of(riga.party_type, riga.party)
			if regole.accolto(riga.get("arrived_at"), riga.status):
				cliente.diventa_cliente(
					persona, regole.ACCETTAZIONE, quando=riga.arrived_at, annuncia=annuncia
				)
			if regole.presente(doc.status, riga.status):
				cliente.diventa_cliente(
					persona, regole.APPUNTAMENTO_SVOLTO, quando=doc.starts_on, annuncia=annuncia
				)

	_senza_fermare(_("Client not recorded from appointment {0}").format(doc.name), doc, registra)


def fattura_confermata(doc, method=None) -> None:
	"""The first confirmed invoice made out to the person. A credit note sells nothing,
	nor does a deposit's advance invoice (they have not come yet), nor a test invoice:
	it is gone the day invoicing goes live."""
	if not regole.vendita(doc.get("document_type"), doc.get("advance_for")):
		return
	if cint(doc.get("test_document")):
		return
	_senza_fermare(
		_("Client not recorded from invoice {0}").format(doc.name),
		doc,
		lambda: cliente.diventa_cliente(
			person_of(doc.party_type, doc.party), regole.FATTURA, quando=get_datetime(doc.posting_date)
		),
	)
