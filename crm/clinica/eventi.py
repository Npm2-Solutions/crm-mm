# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Where the rules listen: the agenda, invoicing, the plan, a deletion.

Wired in `crm/hooks.py` as document events, so neither the agenda nor invoicing
knows the clinic exists. A rule that fails is logged and never stops what
triggered it: an appointment that cannot be saved, or an invoice that cannot be
issued, because a patient card could not be written would be the wrong way round.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import get_datetime

from crm.clinica import paziente, regole


def _senza_fermare(titolo: str, doc, funzione) -> None:
	frappe.db.savepoint("clinica_regola")
	try:
		funzione()
	except Exception:
		frappe.db.rollback(save_point="clinica_regola")
		frappe.log_error(title=titolo, reference_doctype=doc.doctype, reference_name=doc.name)


def appuntamento_creato(doc, method=None) -> None:
	"""A booking moves the person's new patients deal to "appointment booked"."""
	if doc.status in ("Cancelled", "No Show") or not paziente.clinica_accesa():
		return
	from crm.clinica import pipeline

	def sposta():
		for riga in doc.participants or []:
			persona = paziente.persona_di(riga.party_type, riga.party)
			if persona and riga.status != "Cancelled":
				pipeline.prenotata(persona)

	_senza_fermare(_("New patients deal not moved for appointment {0}").format(doc.name), doc, sposta)


def appuntamento_aggiornato(doc, method=None) -> None:
	"""Rule 2: the desk checked somebody in. Rule 3: the appointment was completed,
	or a participant came."""
	righe = doc.participants or []
	if not any(riga.get("arrived_at") or regole.presente(doc.status, riga.status) for riga in righe):
		return
	if not paziente.clinica_accesa() or not paziente.appuntamento_per_la_clinica(doc.service):
		return

	def converti():
		for riga in righe:
			persona = paziente.persona_di(riga.party_type, riga.party)
			if riga.get("arrived_at") and riga.status not in regole.PARTECIPANTE_ASSENTE:
				paziente.assicura_paziente(
					persona, regole.ACCETTAZIONE, quando=riga.arrived_at, fonte=(doc.doctype, doc.name)
				)
			if regole.presente(doc.status, riga.status):
				paziente.assicura_paziente(
					persona,
					regole.APPUNTAMENTO_SVOLTO,
					quando=doc.starts_on,
					fonte=(doc.doctype, doc.name),
				)

	_senza_fermare(_("Patient not recorded from appointment {0}").format(doc.name), doc, converti)


def fattura_confermata(doc, method=None) -> None:
	"""Rule 4: a confirmed invoice with a healthcare line. A course or a membership
	makes nobody a patient."""
	if not any(riga.get("is_healthcare") for riga in doc.items or []):
		return
	if not paziente.clinica_accesa():
		return
	_senza_fermare(
		_("Patient not recorded from invoice {0}").format(doc.name),
		doc,
		lambda: paziente.assicura_paziente(
			paziente.persona_di(doc.party_type, doc.party),
			regole.FATTURA_SANITARIA,
			quando=get_datetime(doc.posting_date),
			fonte=(doc.doctype, doc.name),
		),
	)


def piano_aggiornato(doc, method=None) -> None:
	"""The clinic was switched on: the patients already there are found once, in the
	background, from the appointments and the invoices."""
	# the plan's own on_update already dropped its cached copy: this reads the new one
	if paziente.clinica_accesa():
		from crm.clinica import pipeline

		# the two pipelines of a medical centre, where there are none yet
		_senza_fermare(_("Medical centre pipelines not created"), doc, pipeline.crea_pipeline)
		# and the centre's dashboard
		_senza_fermare(_("Medical centre dashboard not created"), doc, _cruscotto_del_centro)
	if paziente.clinica_accesa() and not frappe.db.get_default(paziente.RECUPERO_FATTO):
		frappe.enqueue(
			"crm.clinica.paziente.recupera",
			queue="long",
			job_id="crm-clinica-recupero",
			deduplicate=True,
			enqueue_after_commit=True,
		)


def _cruscotto_del_centro() -> None:
	from crm.dashboard import store

	store.create_template_dashboards(only=("medical_centre",))


def persona_in_cancellazione(doc, method=None) -> None:
	"""A patient's record is kept: the person is not deleted.

	Clinical documents have to be kept even when the person asks to be forgotten,
	for as long as the law and the centre's policy say. Said here, in words, rather
	than as a broken link.
	"""
	if paziente.e_paziente(doc.name):
		frappe.throw(
			_(
				"{0} is a patient of the centre: their clinical record has to be kept, so the "
				"person cannot be deleted. Their data stays out of marketing."
			).format(frappe.bold(doc.lead_name or doc.name)),
			frappe.LinkExistsError,
		)
