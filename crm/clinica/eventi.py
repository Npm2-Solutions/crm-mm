# Copyright (c) 2026, NPM2 Solutions Srl and contributors
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
from frappe.utils import cint, get_datetime

from crm.clinica import paziente, regole


def _senza_fermare(titolo: str, doc, funzione) -> None:
	frappe.db.savepoint("clinica_regola")
	try:
		funzione()
	except Exception:
		frappe.db.rollback(save_point="clinica_regola")
		frappe.log_error(title=titolo, reference_doctype=doc.doctype, reference_name=doc.name)


def appuntamento_aggiornato(doc, method=None) -> None:
	"""Rule 2: the desk checked somebody in. Rule 3: the appointment was completed,
	or a participant came."""
	righe = doc.participants or []
	if not any(
		regole.accolto(riga.get("arrived_at"), riga.status) or regole.presente(doc.status, riga.status)
		for riga in righe
	):
		return
	professionisti = [riga.user for riga in doc.staff or [] if riga.get("status") != "Declined"]
	if not paziente.clinica_accesa() or not paziente.appuntamento_per_la_clinica(doc.service, professionisti):
		return

	# brought over from the previous software: a patient from then, and no news
	annuncia = not doc.flags.get("importato")

	def converti():
		for riga in righe:
			persona = paziente.persona_di(riga.party_type, riga.party)
			if regole.accolto(riga.get("arrived_at"), riga.status):
				paziente.assicura_paziente(
					persona,
					regole.ACCETTAZIONE,
					quando=riga.arrived_at,
					fonte=(doc.doctype, doc.name),
					annuncia=annuncia,
				)
			if regole.presente(doc.status, riga.status):
				paziente.assicura_paziente(
					persona,
					regole.APPUNTAMENTO_SVOLTO,
					quando=doc.starts_on,
					fonte=(doc.doctype, doc.name),
					annuncia=annuncia,
				)

	_senza_fermare(_("Patient not recorded from appointment {0}").format(doc.name), doc, converti)


def fattura_confermata(doc, method=None) -> None:
	"""Rule 4: a confirmed invoice with a healthcare line. A course or a membership
	makes nobody a patient, nor does a credit note."""
	if not any(riga.get("is_healthcare") for riga in doc.items or []):
		return
	if not regole.vendita(doc.get("document_type")) or cint(doc.get("test_document")):
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


def modulo_firmato(doc, method=None) -> None:
	"""Rule 1: a signed form that records health data makes the person a patient."""
	if not doc.get("clinical") or not paziente.clinica_accesa():
		return
	_senza_fermare(
		_("Patient not recorded from form {0}").format(doc.name),
		doc,
		lambda: paziente.assicura_paziente(
			doc.lead,
			regole.INFORMAZIONE_MEDICA,
			quando=get_datetime(doc.signed_on),
			fonte=(doc.doctype, doc.name),
			# signed from a link or the tablet nobody was logged in: whoever sent it
			da=doc.get("filled_by") or _mandato_da(doc),
		),
	)
	# the answers that fill the patient's summary wait for a practitioner to confirm them
	_senza_fermare(
		_("Summary not proposed from form {0}").format(doc.name), doc, lambda: _proponi_dal_modulo(doc)
	)


def _proponi_dal_modulo(doc) -> None:
	from crm.clinica import sintesi
	from crm.moduli import modelli
	from crm.moduli import schema as S

	schema = modelli.carica_schema(frappe.get_cached_doc(modelli.VERSIONE, doc.template_version).schema)
	risposte = frappe.parse_json(doc.answers) if isinstance(doc.answers, str) else (doc.answers or {})
	sintesi.proponi(doc, schema, risposte, S.valuta(schema, risposte))


def _mandato_da(doc) -> str | None:
	if not doc.get("request"):
		return None
	mittente = frappe.db.get_value("CRM Form Request", doc.request, "sent_by")
	# sent by the centre itself, with a booking: nobody in particular
	return None if mittente in ("Guest", "Administrator") else mittente


def messaggio_scritto(doc, method=None) -> None:
	"""Rule 1: a message about the care, on the patient's board, is health data. One
	from the desk is not, nor a question the patient passed on."""
	if doc.get("kind") != "Care" or not paziente.clinica_accesa():
		return
	_senza_fermare(
		_("Patient not recorded from message {0}").format(doc.name),
		doc,
		lambda: paziente.assicura_paziente(
			doc.lead,
			regole.INFORMAZIONE_MEDICA,
			fonte=(doc.doctype, doc.name),
			da=doc.get("practitioner") or doc.get("author"),
		),
	)


def messaggio_eliminato(doc, method=None) -> None:
	"""A message gone: the patient card keeps the rule, not a link to it."""
	paziente.dimentica_fonte(doc.doctype, doc.name)


def sanitario_scritto(doc, method=None) -> None:
	"""Rule 1: a plan, a programme or a document with health data - a diet, a test
	result - makes its person a patient. A training or a contract do not."""
	if not doc.get("clinical") or not paziente.clinica_accesa():
		return
	_senza_fermare(
		_("Patient not recorded from {0} {1}").format(_(doc.doctype), doc.name),
		doc,
		lambda: paziente.assicura_paziente(
			doc.lead,
			regole.INFORMAZIONE_MEDICA,
			fonte=(doc.doctype, doc.name),
			da=doc.get("practitioner") or frappe.session.user,
		),
	)


def sanitario_eliminato(doc, method=None) -> None:
	"""A draft thrown away: the patient card keeps the rule, not a link to it."""
	paziente.dimentica_fonte(doc.doctype, doc.name)


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
