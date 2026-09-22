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

from crm.invoicing import connessione, documento, estensioni
from crm.invoicing.engine.classificazione import GuardiaSdI
from crm.invoicing.engine.codici import Canale, TipoDestinatario
from crm.invoicing.engine.fatturapa import bloccanti


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

	Then the channel takes it - export, the practice's own PEC mailbox, or an
	accredited provider. Which one is configuration; the XML is the same file either
	way, and it was built and checked here.
	"""
	from crm.invoicing import sdi

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
	try:
		esito = sdi.invia(fattura, emittente)
	except sdi.ErroreCanale as errore:
		documento.registra(fattura, "sdi_sent", str(errore), stato="errore")
		frappe.throw(str(errore), title=_("Transmission"))

	fattura.db_set(
		{
			"sdi_status": "inviato" if esito.canale != "export" else fattura.sdi_status,
			"sdi_sent_on": frappe.utils.now_datetime(),
			"sdi_identifier": esito.identificativo or fattura.sdi_identifier,
			"sdi_message": esito.messaggio,
			# Stamped on the document, not read back from the company: by the time
			# somebody asks whether this one was real, the switch will have moved.
			"sdi_environment": esito.dettagli.get("environment") or fattura.sdi_environment,
		},
		update_modified=False,
	)
	documento.registra(fattura, "sdi_sent", esito.messaggio, stato=esito.canale)
	return esito.come_dizionario()


@frappe.whitelist(methods=["POST"])
def reopen_rejected(invoice: str) -> dict:
	"""Reopen a rejected invoice for correction, keeping its number and date.

	A rejection means the invoice counts as not issued, so this is not editing
	history - the document does not exist yet. Five days from the notice to correct
	and resend, with the same number and the same date, which is the route the
	Agenzia calls preferable (Circolare 13/E del 2 luglio 2018).
	"""
	fattura = _fattura(invoice)
	fattura.check_permission("submit")
	return documento.riapri_scartata(fattura)


@frappe.whitelist(methods=["POST"])
def apply_sdi_notice(invoice: str = "", file_url: str = "") -> dict:
	"""Apply a notice downloaded from the portal, or pushed by a provider.

	One path for every channel: a notice is a file whose name says which document it
	answers. Applying the same one twice is a no-op - a PEC mailbox re-delivers and a
	webhook retries.
	"""
	from crm.invoicing.sdi import ricezione

	frappe.has_permission("CRM Invoice", "write", throw=True)
	if not file_url:
		frappe.throw(_("No notice file"))
	allegato = frappe.get_doc("File", {"file_url": file_url})
	contenuto = allegato.get_content(encodings=[])
	if isinstance(contenuto, str):
		contenuto = contenuto.encode()
	return ricezione.applica_file(contenuto, allegato.file_name, invoice or None)


@frappe.whitelist(methods=["POST"])
def scan_sdi_mailbox(days: int = 7) -> list[dict]:
	"""Look through incoming mail for notices nobody has applied yet.

	The PEC route has no webhook. If nothing reads the mailbox the invoices stay in
	`inviato` forever, which looks like nothing is wrong.
	"""
	from crm.invoicing.sdi import ricezione

	frappe.has_permission("CRM Invoice", "write", throw=True)
	return ricezione.scansiona_posta(int(days))


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
def generate_pdf(invoice: str) -> dict:
	"""Produce the PDF/A for an issued invoice that has none.

	It will not overwrite one: the file that was handed over is the one stored, and
	its hash is what proves that years later. A second call on a document that
	already has a PDF says so and changes nothing.
	"""
	from crm.invoicing import pdf

	fattura = _fattura(invoice)
	fattura.check_permission("write")
	if fattura.docstatus != 1:
		frappe.throw(_("Only an issued invoice has a document to produce"))
	return pdf.genera_e_allega(fattura)


def _riga_mancante(condizione: bool, titolo: str, conseguenza: str, campo: str = "") -> dict | None:
	"""One checklist row, or nothing when the gap is not there.

	Public shape rather than a closure: a module that registers extra duties builds
	its rows the same way, so the list reads as one list and not as two.
	"""
	if not condizione:
		return None
	return {"title": titolo, "consequence": conseguenza, "field": campo}


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
		riga = _riga_mancante(condizione, titolo, conseguenza, campo)
		if riga:
			voci.append(riga)

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
		not emittente.get("conservation_service"),
		_("Preservation of the SdI documents"),
		_(
			"Ten years is mandatory, and transmitting does not provide it. The Agenzia's service "
			"is free but needs an explicit adhesion in Fatture e Corrispettivi, and it only covers "
			"invoices from that day on."
		),
		"conservation_service",
	)
	manca(
		emittente.get("document_mode") == "elettronica_extra_sdi" and not emittente.get("conservation_local"),
		_("Preservation of the documents outside the SdI"),
		_(
			"Healthcare invoices towards a natural person never transit the SdI, so the Agenzia's "
			"free service cannot reach them. Either name a provider for these, or switch back to a "
			"paper original and keep that."
		),
		"conservation_local",
	)
	manca(
		emittente.get("sdi_mode") == "provider" and not emittente.get("sdi_endpoint"),
		_("Transmission channel"),
		_(
			"The channel is set to an accredited provider but has no endpoint: the XML is written "
			"and nothing carries it. Configure it, or fall back to export and upload by hand."
		),
		"sdi_endpoint",
	)
	manca(
		emittente.get("sdi_mode") == "provider"
		and emittente.get("sdi_endpoint")
		and not connessione.in_produzione(emittente),
		_("Still on the sandbox"),
		_(
			"The channel is configured and working, but aimed at the provider's sandbox: "
			"documents sent from here reach nobody. Switch the environment to production "
			"once the rehearsal is done."
		),
		"provider_environment",
	)
	manca(
		emittente.get("sdi_mode") == "provider"
		and emittente.get("sdi_endpoint")
		and not connessione.segreto(emittente, "sdi_webhook_secret"),
		_("Webhook secret"),
		_(
			"Without it the provider has no authenticated way to push notices here, so "
			"nobody learns whether an invoice was accepted until somebody looks by hand - "
			"which is the failure an intermediary was chosen to prevent."
		),
		"sdi_webhook_secret",
	)
	manca(
		emittente.get("sdi_mode") == "pec" and not emittente.get("pec"),
		_("PEC mailbox"),
		_("The channel is set to PEC and the company has none: nothing can leave."),
		"pec",
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
	voci.extend(estensioni.controlli_aggiuntivi(emittente))


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


@frappe.whitelist(allow_guest=True, methods=["POST"])
def provider_webhook():
	"""The provider's way in with a notice. Guest by necessity, secret by design.

	This is the only endpoint in the module that answers an unauthenticated caller,
	so it answers as little as possible: a refused delivery learns nothing about why.

	The status code is the contract with the provider's retry queue - it retries
	fifteen times over about ten hours on anything that is not a 200. So a delivery
	that was understood returns 200 even when there was nothing to apply, because
	sending the same bytes again would reach the same answer; an unexpected failure
	returns 500, because that one is worth trying again.
	"""
	from crm.invoicing.sdi import webhook

	try:
		esito = webhook.gestisci(frappe.request)
	except webhook.Rifiutata:
		frappe.local.response["http_status_code"] = 401
		return {"ok": False}
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title=_("Provider webhook failed"))
		frappe.local.response["http_status_code"] = 500
		return {"ok": False}
	return {"ok": True, **esito}


@frappe.whitelist()
def webhook_endpoint(company: str) -> dict:
	"""The URL to paste into the provider's configuration, and whether it is armed.

	The secret itself is never returned. It is written once, to the provider and to
	the encrypted field, and a value that can be read back out of a settings screen
	is one that can be read out of a screenshot.
	"""
	frappe.has_permission("CRM Invoicing Company", "write", doc=company, throw=True)
	from urllib.parse import quote

	url = frappe.utils.get_url(
		f"/api/method/crm.invoicing.api.provider_webhook?company={quote(company, safe='')}"
	)
	configurato = bool(connessione.segreto({"name": company}, "sdi_webhook_secret"))
	return {
		"url": url,
		"configured": configurato,
		"header": "X-Provider-Token",
		"hint": _(
			"In the provider's configuration set the authentication token to the secret you "
			"generated here, as a header named X-Acube-Token or as a query parameter named token."
		),
	}


@frappe.whitelist(methods=["POST"])
def generate_webhook_secret(company: str) -> dict:
	"""Mint a new secret and hand it over exactly once.

	Rotating is the same call: the old secret stops working the moment this returns,
	so the provider's configuration has to be updated in the same sitting. That is
	said out loud rather than discovered when the notices go quiet.
	"""
	frappe.has_permission("CRM Invoicing Company", "write", doc=company, throw=True)
	segreto = frappe.generate_hash(length=48)
	azienda = frappe.get_doc("CRM Invoicing Company", company)
	azienda.sdi_webhook_secret = segreto
	azienda.save(ignore_permissions=True)
	return {
		"secret": segreto,
		**webhook_endpoint(company),
		"warning": _(
			"Copy it now: it is stored encrypted and will not be shown again. Any secret "
			"configured at the provider before this call has just stopped working."
		),
	}


@frappe.whitelist(methods=["POST"])
def reconcile_provider(company: str = "") -> dict:
	"""Fetch and apply everything the provider is holding for us.

	The webhook does this too, on the way in. This is the same work on demand, and
	on a schedule - because a webhook that was never delivered leaves no trace, and
	an invoice stuck in `inviato` looks exactly like one that went through.
	"""
	from crm.invoicing.sdi import riconciliazione

	frappe.has_permission("CRM Invoice", "write", throw=True)
	aziende = (
		[company]
		if company
		else [riga.name for riga in frappe.get_all("CRM Invoicing Company", filters={"sdi_mode": "provider"})]
	)
	esiti = {}
	for nome in aziende:
		emittente = frappe.get_cached_doc("CRM Invoicing Company", nome).as_dict()
		if not (emittente.get("sdi_endpoint") or "").strip():
			continue
		esiti[nome] = riconciliazione.riconcilia(emittente)
	return esiti


@frappe.whitelist()
def supplier_invoices(company: str = "", limit: int = 50) -> list[dict]:
	"""The passive cycle, as a list. Empty where the company only issues."""
	frappe.has_permission("CRM Supplier Invoice", "read", throw=True)
	filtri = {"company": company} if company else {}
	return frappe.get_all(
		"CRM Supplier Invoice",
		filters=filtri,
		fields=[
			"name",
			"supplier_name",
			"supplier_tax_id",
			"document_type",
			"document_number",
			"document_date",
			"total_amount",
			"currency",
			"status",
			"xml_file",
			"received_on",
		],
		order_by="document_date desc, received_on desc",
		limit_page_length=int(limit),
	)
