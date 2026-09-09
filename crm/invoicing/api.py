# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The endpoints the interface talks to.

The one that matters is `send_to_sdi`. It is the barrier, not a button state: it
runs the guard server-side and answers **403** on a healthcare document towards a
natural person, for every user and every override. In the interface the button
does not exist on those documents at all - a greyed-out button invites somebody to
go looking for how to turn it on.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import getdate

from crm.invoicing import documento, registro, ts
from crm.invoicing.engine.classificazione import GuardiaSdI
from crm.invoicing.engine.codici import Canale, TipoDestinatario
from crm.invoicing.engine.fatturapa import bloccanti
from crm.invoicing.engine.professioni import elenco as professioni_di_serie


def _fattura(name: str):
	fattura = frappe.get_doc("CRM Invoice", name)
	fattura.check_permission("read")
	return fattura


@frappe.whitelist(methods=["POST"])
def preview(invoice: str) -> dict:
	"""Classification and totals of a draft, without saving anything.

	What the desk needs before issuing: which channel this is going to take, what it
	adds up to, and everything that is still wrong - all of it, not the first item.
	"""
	fattura = _fattura(invoice)
	preparato = documento.prepara(fattura)
	classificazione = preparato["classificazione"]
	conto = preparato["calcolo"]
	return {
		"channel": classificazione.canale,
		"sdi_allowed": classificazione.sdi_consentito,
		"ts_required": classificazione.ts_richiesto,
		"errors": documento.blocchi(fattura, classificazione),
		"warnings": classificazione.tutti_avvisi + conto.avvisi,
		"totals": {
			"net_total": float(conto.imponibile),
			"fund_contribution": float(conto.cassa),
			"vat_total": float(conto.iva),
			"advances": float(conto.anticipazioni),
			"stamp_duty": float(conto.bollo),
			"stamp_duty_recharged": float(conto.bollo_riaddebitato),
			"withholding": float(conto.ritenuta),
			"grand_total": float(conto.totale),
			"net_payable": float(conto.netto_a_pagare),
			"ts_total": float(conto.totale_ts),
			"reconciles": conto.quadra,
		},
		"legal_notes": [riga for riga in (fattura.legal_notes or "").splitlines() if riga],
	}


@frappe.whitelist(methods=["POST"])
def send_to_sdi(invoice: str) -> dict:
	"""Route an invoice to the Sistema di Interscambio.

	The guard runs first and raises `PermissionError`, which Frappe answers as 403.
	It is not an input problem, it is a forbidden operation: since 2026 the
	electronic invoice through the SdI for healthcare services towards natural
	persons is structurally forbidden (D.Lgs. 12 giugno 2025 n. 81).
	"""
	fattura = _fattura(invoice)
	fattura.check_permission("submit")
	if fattura.docstatus != 1:
		frappe.throw(_("Only an issued invoice can be transmitted"))

	try:
		fattura.guardia()
	except GuardiaSdI as blocco:
		frappe.throw(
			blocco.motivo + ("<br><br>" + "<br>".join(blocco.righe) if blocco.righe else ""),
			frappe.PermissionError,
			title=_("Transmission not allowed"),
		)

	if not fattura.xml_file:
		frappe.throw(_("The XML has not been generated for this invoice"))

	rilievi = bloccanti((fattura.sdi_message or "").splitlines())
	if rilievi:
		# A rejection is not free: the invoice counts as not issued and the five days
		# to resubmit run from the notice. Better to stop here than to find out then.
		frappe.throw(
			_("The file would be rejected:") + "<br>" + "<br>".join(rilievi),
			title=_("Not transmissible"),
		)

	emittente = documento.azienda(fattura)
	if (emittente.get("sdi_mode") or "export") == "export":
		# The file is written and handed over. The XML is generated here either way;
		# the accredited channel is the only part a provider sells.
		documento.registra(
			fattura, "sdi_sent", _("XML made available for manual transmission"), stato="export"
		)
		return {"mode": "export", "file": fattura.xml_file, "file_name": fattura.sdi_filename}

	frappe.throw(
		_(
			"No transmission adapter is configured for provider {0}. The XML is ready at {1}: "
			"download it, or configure the provider."
		).format(emittente.get("sdi_provider") or "-", fattura.xml_file)
	)


@frappe.whitelist(methods=["POST"])
def record_sdi_outcome(invoice: str, status: str, message: str = "", identifier: str = "") -> dict:
	"""Record a notice coming back from the SdI.

	A rejection is not a footnote: the invoice counts as not issued, and the five
	days to resubmit run from the notice.
	"""
	fattura = _fattura(invoice)
	fattura.check_permission("submit")
	ammessi = (
		"inviato",
		"consegnata",
		"scartata",
		"mancata_consegna",
		"esito_pa",
		"decorrenza_termini",
		"errore",
	)
	if status not in ammessi:
		frappe.throw(_("Unknown SdI status {0}").format(status))
	fattura.db_set(
		{
			"sdi_status": status,
			"sdi_message": message or None,
			"sdi_identifier": identifier or fattura.sdi_identifier,
			"sdi_sent_on": fattura.sdi_sent_on or frappe.utils.now_datetime(),
		},
		update_modified=False,
	)
	documento.registra(fattura, "sdi_receipt", message, stato=status)
	return {"status": status}


@frappe.whitelist(methods=["POST"])
def issue_from_deal(deal: str, billable_service: str, service_provider: str, rate: float = 0) -> str:
	"""Open a draft invoice from a deal, with the client already filled in."""
	trattativa = frappe.get_doc("CRM Deal", deal)
	trattativa.check_permission("read")
	fattura = frappe.new_doc("CRM Invoice")
	fattura.party_type = "CRM Deal"
	fattura.party = deal
	fattura.deal = deal
	fattura.recipient_type = TipoDestinatario.SOGGETTO_IVA
	fattura.append(
		"items",
		{
			"billable_service": billable_service,
			"service_provider": service_provider,
			"qty": 1,
			"rate": rate or 0,
		},
	)
	fattura.insert()
	return fattura.name


@frappe.whitelist(methods=["POST"])
def issue_from_appointment(appointment: str, billable_service: str = "", service_provider: str = "") -> str:
	"""Open a draft invoice from an appointment.

	The agenda proposes: the service from the appointment's service, the provider
	from whoever is on the staff list, the client from the first participant. All
	three are proposals - **the provider still has to be confirmed**, because in a
	shared calendar a wrong assignment produces no error, it produces rejected rows
	in January.

	The appointment lives in this CRM, in Europe, next to the record it belongs to.
	The original design had to leave it in a third-party calendar and treat the whole
	arrangement as an art. 9 processing to be declared, covered by transfer clauses
	and a documented impact assessment. Here there is nothing to declare, because
	nothing crosses a border.
	"""
	incontro = frappe.get_doc("CRM Appointment", appointment)
	incontro.check_permission("read")

	if not billable_service and incontro.service:
		billable_service = frappe.db.get_value(
			"CRM Billable Service", {"crm_service": incontro.service, "enabled": 1}, "name"
		)
	if not billable_service:
		frappe.throw(
			_("No fiscal card for this appointment's service: a service without a card is not billable")
		)
	if not service_provider:
		for membro in incontro.staff or []:
			service_provider = frappe.db.get_value(
				"CRM Service Provider", {"user": membro.user, "enabled": 1}, "name"
			)
			if service_provider:
				break
	if not service_provider:
		service_provider = frappe.db.get_value("CRM Billable Service", billable_service, "default_provider")
	if not service_provider:
		frappe.throw(
			_(
				"No provider for this appointment: the qualification decides the expense type and the "
				"VAT regime, so it cannot be left to a default"
			)
		)

	fattura = frappe.new_doc("CRM Invoice")
	fattura.appointment = appointment
	fattura.recipient_type = TipoDestinatario.PERSONA_FISICA
	partecipante = (incontro.participants or [None])[0]
	if partecipante and partecipante.party_type and partecipante.party:
		fattura.party_type = partecipante.party_type
		fattura.party = partecipante.party
		fattura.billing_name = partecipante.participant_name
	fattura.append(
		"items",
		{
			"billable_service": billable_service,
			"service_provider": service_provider,
			"qty": 1,
			"rate": incontro.unit_price or 0,
		},
	)
	fattura.insert()
	return fattura.name


@frappe.whitelist(methods=["POST"])
def prepare_ts_submission(company: str, year: int) -> dict:
	"""Build the Sistema TS file for a year.

	Invoices that do not validate are listed and left behind rather than holding the
	whole year hostage: a single broken row must not cost the deadline.
	"""
	frappe.has_permission("CRM TS Submission", "create", throw=True)
	return ts.prepara_invio(company, int(year))


@frappe.whitelist(methods=["POST"])
def record_ts_outcome(submission: str, code: str, message: str = "", protocol: str = "") -> dict:
	"""Record the outcome of a Sistema TS submission."""
	frappe.has_permission("CRM TS Submission", "write", throw=True)
	ts.segna_esito(submission, code, message, protocol)
	return {"submission": submission, "code": code}


@frappe.whitelist()
def ts_status(company: str, year: int) -> dict:
	"""What is still outstanding for a year, and how long there is left."""
	frappe.has_permission("CRM TS Submission", "read", throw=True)
	return ts.stato(company, int(year))


@frappe.whitelist()
def onboarding_checklist(company: str) -> list[dict]:
	"""What is still missing, and what each gap costs.

	A live list rather than a document nobody opens: it gets shorter, and every row
	says the consequence of leaving it open - "the agenda will not propose it", "this
	document will not reach the Sistema TS".
	"""
	frappe.has_permission("CRM Invoicing Company", "read", throw=True)
	if not frappe.db.exists("CRM Invoicing Company", company):
		frappe.throw(_("Unknown company {0}").format(company))
	emittente = frappe.get_cached_doc("CRM Invoicing Company", company).as_dict()

	voci: list[dict] = []

	def manca(condizione: bool, titolo: str, conseguenza: str, campo: str = "") -> None:
		if condizione:
			voci.append({"title": titolo, "consequence": conseguenza, "field": campo})

	manca(
		not emittente.get("tax_id"),
		_("VAT number"),
		_("No invoice can be issued: FatturaPA requires it on the issuer."),
		"tax_id",
	)
	manca(
		not (emittente.get("address_line") and emittente.get("postal_code") and emittente.get("city")),
		_("Registered office"),
		_("Electronic invoices cannot be transmitted without it."),
		"address_line",
	)
	manca(
		emittente.get("stamp_duty_mode") == "virtuale" and not emittente.get("stamp_authorization_number"),
		_("Stamp duty authorisation"),
		_("The wording would not satisfy art. 15 DPR 642/72."),
		"stamp_authorization_number",
	)
	manca(
		not frappe.db.count("CRM Service Provider", {"enabled": 1}),
		_("At least one provider"),
		_("Nothing can be billed: the line has no qualification and therefore no VAT regime."),
	)
	manca(
		not frappe.db.count("CRM Billable Service", {"enabled": 1}),
		_("At least one service card"),
		_("A service without a card is not billable."),
	)
	if emittente.get("sender_category") not in (None, "", "non_sanitario"):
		manca(
			not emittente.get("ts_certificate"),
			_("Sistema TS certificate"),
			_("The expense file is built with a stand-in and cannot be submitted."),
			"ts_certificate",
		)
		manca(
			emittente.get("ts_mode") != "export" and not emittente.get("ts_username"),
			_("Sistema TS credentials"),
			_("Submission falls back to export until they arrive."),
			"ts_username",
		)

	for qualifica in registro.da_verificare(company):
		voci.append(
			{
				"title": _("Verify {0}").format(qualifica["qualification_name"]),
				"consequence": qualifica["needs_verification"],
				"field": "",
				"link": {"doctype": "CRM Professional Qualification", "name": qualifica["name"]},
			}
		)
	return voci


@frappe.whitelist()
def shipped_qualifications() -> list[dict]:
	"""The register as it ships, for comparison with what is stored.

	Useful when a rule moves: the file is where the research lives, the records are
	what the practice runs on, and seeing them side by side is how a change gets
	noticed instead of silently diverging.
	"""
	frappe.has_permission("CRM Professional Qualification", "read", throw=True)
	return [
		{
			"code": p.codice,
			"label": p.etichetta,
			"category": p.categoria,
			"vat_exempt": p.esente_iva,
			"sdi_rule": p.regola_sdi,
			"ts_required": p.obbligo_ts,
			"needs_verification": list(p.da_verificare),
			"stored": bool(frappe.db.exists("CRM Professional Qualification", p.codice)),
		}
		for p in professioni_di_serie()
	]


@frappe.whitelist()
def pending_actions(company: str = "") -> list[dict]:
	"""Everything issued that still has a button waiting to be pressed.

	A button not pressed produces no error: it produces absence, and absence is
	found in January. This is the list that makes yesterday's absences visible today.
	"""
	frappe.has_permission("CRM Invoice", "read", throw=True)
	filtri = {"docstatus": 1}
	if company:
		filtri["company"] = company

	da_fare: list[dict] = []
	for stato, etichetta in (
		("da_inviare", _("waiting to be transmitted to the SdI")),
		("scartata", _("rejected by the SdI")),
	):
		for riga in frappe.get_all(
			"CRM Invoice",
			filters={**filtri, "sdi_status": stato},
			fields=["name", "document_number", "posting_date", "billing_name", "grand_total"],
			order_by="posting_date asc",
			limit=200,
		):
			da_fare.append({**riga, "action": "sdi", "state": stato, "label": etichetta})

	for stato, etichetta in (
		("da_inviare", _("waiting to be reported to the Sistema TS")),
		("scartato", _("rejected by the Sistema TS")),
	):
		for riga in frappe.get_all(
			"CRM Invoice",
			filters={**filtri, "ts_status": stato},
			fields=["name", "document_number", "posting_date", "billing_name", "ts_total", "ts_year"],
			order_by="posting_date asc",
			limit=200,
		):
			da_fare.append({**riga, "action": "ts", "state": stato, "label": etichetta})
	return da_fare


@frappe.whitelist()
def invoice_channel(invoice: str) -> dict:
	"""Which channel a document takes, and whether the SdI is open to it.

	The interface asks this to decide whether the transmit action exists at all. The
	answer is authoritative here and re-checked server-side before anything moves.
	"""
	fattura = _fattura(invoice)
	preparato = documento.prepara(fattura)
	classificazione = preparato["classificazione"]
	return {
		"channel": classificazione.canale,
		"sdi_allowed": classificazione.sdi_consentito,
		"ts_required": classificazione.ts_richiesto,
		"is_healthcare": classificazione.canale == Canale.PDF_TS,
		"deadline": str(getdate(fattura.posting_date)),
	}
