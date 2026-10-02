# Copyright (c) 2026, NPM2 Solutions Srl and contributors
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
from frappe.utils import add_days, flt, getdate

from crm.invoicing import anagrafica, connessione, documento, prova
from crm.invoicing.engine.classificazione import GuardiaSdI
from crm.invoicing.engine.codici import Canale, TipoDestinatario
from crm.invoicing.engine.fatturapa import bloccanti

# a cycle of sessions paid as a whole (`crm.scheduling.cicli`): one invoice for it,
# none for its sessions. Named, not imported, like the appointment it comes from.
CICLO_INTERO = "The whole cycle"


def _fattura(name: str):
	fattura = frappe.get_doc("CRM Invoice", name)
	fattura.check_permission("read")
	return fattura


def _verifica_invio() -> None:
	"""Transmitting is its own capability: the front desk issues invoices, and sends
	them to the SdI or the Sistema TS only where the manager allowed it (doc 30)."""
	from crm.permissions.livelli import verifica_nel_crm

	verifica_nel_crm("fatture.invia", messaggio=_("You are not allowed to transmit invoices"))


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
	errori, avvisi = documento.da_correggere(fattura, preparato)
	return {
		"channel": classificazione.canale,
		"sdi_allowed": classificazione.sdi_consentito,
		"ts_required": classificazione.ts_richiesto,
		"errors": errori,
		"warnings": avvisi,
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
	_verifica_invio()
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
	# a test invoice goes nowhere once the company is live: it is about to be gone
	prova.fuori_dalla_prova(fattura, emittente)
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
			# the intermediary renames the file it transmits: the SdI's notices answer
			# to its name, and its own identifier is the key its updates carry
			"sdi_filename": esito.nome_file or fattura.sdi_filename,
			"sdi_provider_id": esito.dettagli.get("provider_id") or fattura.sdi_provider_id,
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
	if (
		incontro.get("session_cycle")
		and frappe.db.get_value("CRM Session Cycle", incontro.session_cycle, "billing") == CICLO_INTERO
	):
		frappe.throw(_("This session is paid with its cycle: invoice the cycle"))
	if incontro.get("subscription"):
		frappe.throw(_("This appointment is comprised in a subscription: its instalments are invoiced"))

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
				"No provider for this appointment: the qualification decides the expense type and the VAT regime, so it cannot be left to a default"
			)
		)

	fattura = frappe.new_doc("CRM Invoice")
	fattura.appointment = appointment
	fattura.recipient_type = TipoDestinatario.PERSONA_FISICA
	partecipante = (incontro.participants or [None])[0]
	if partecipante and partecipante.party_type and partecipante.party:
		fattura.party_type = partecipante.party_type
		fattura.party = partecipante.party
		# the name on the booking, unless somebody pays for them: then the invoice
		# is made out to that person, name included
		if not anagrafica.pagante_della_fattura(fattura):
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
def issue_from_cycle(cycle: str, billable_service: str = "", service_provider: str = "") -> str:
	"""Open a draft invoice for a cycle of sessions paid as a whole: one line, the
	cycle's service, at the cycle's price, over the cycle's days.

	The same proposals as from an appointment: the fiscal card of the cycle's
	service, the provider of whoever follows it, the person as the client - or
	whoever pays for them.
	"""
	frappe.has_permission("CRM Invoice", "create", throw=True)
	ciclo = frappe.get_doc("CRM Session Cycle", cycle)
	ciclo.check_permission("read")
	if ciclo.billing != CICLO_INTERO or not flt(ciclo.price):
		frappe.throw(_("This cycle is invoiced session by session"))
	gia = frappe.db.get_value("CRM Invoice", {"session_cycle": cycle, "docstatus": ("<", 2)}, "name")
	if gia:
		frappe.throw(_("This cycle is invoiced already: {0}").format(gia))
	if not billable_service:
		billable_service = frappe.db.get_value(
			"CRM Billable Service", {"crm_service": ciclo.service, "enabled": 1}, "name"
		)
	if not billable_service:
		frappe.throw(_("No fiscal card for this cycle's service: a service without a card is not billable"))
	if not service_provider and ciclo.practitioner:
		service_provider = frappe.db.get_value(
			"CRM Service Provider", {"user": ciclo.practitioner, "enabled": 1}, "name"
		)
	if not service_provider:
		service_provider = frappe.db.get_value("CRM Billable Service", billable_service, "default_provider")
	if not service_provider:
		frappe.throw(
			_(
				"No provider for this cycle: the qualification decides the expense type and the VAT regime, so it cannot be left to a default"
			)
		)

	fattura = frappe.new_doc("CRM Invoice")
	fattura.session_cycle = cycle
	fattura.recipient_type = TipoDestinatario.PERSONA_FISICA
	fattura.party_type = "CRM Lead"
	fattura.party = ciclo.lead
	if not anagrafica.pagante_della_fattura(fattura):
		fattura.billing_name = ciclo.lead_name
	servizio = frappe.db.get_value("CRM Billable Service", billable_service, "fiscal_description")
	fattura.append(
		"items",
		{
			"billable_service": billable_service,
			"service_provider": service_provider,
			"description": _("{0}: cycle of {1} sessions").format(servizio or ciclo.service, ciclo.sessions),
			"qty": 1,
			"rate": flt(ciclo.price),
			"period_from": ciclo.starts_on,
			"period_to": ciclo.valid_until,
		},
	)
	fattura.insert()
	return fattura.name


@frappe.whitelist(methods=["POST"])
def issue_from_subscription(subscription: str, instalment: str, service_provider: str = "") -> str:
	"""Open a draft invoice for one instalment of a subscription: one line, the
	fiscal card of its type, the instalment's amount, over the days it pays for.

	The person is the client - or whoever pays for them - and the provider is the
	one of whoever follows the subscription, else the card's own. Its appointments
	are not invoiced one by one: they are paid here.
	"""
	frappe.has_permission("CRM Invoice", "create", throw=True)
	abbonamento = frappe.get_doc("CRM Subscription", subscription)
	abbonamento.check_permission("read")
	rata = next((r for r in abbonamento.instalments if r.name == instalment), None)
	if not rata:
		frappe.throw(_("No such instalment"))
	if rata.invoice and frappe.db.get_value("CRM Invoice", rata.invoice, "docstatus") in (0, 1):
		frappe.throw(_("This instalment is invoiced already: {0}").format(rata.invoice))
	billable_service = abbonamento.billable_service
	if not billable_service:
		frappe.throw(_("This subscription has no fiscal card: its instalments are not invoiced"))
	if not service_provider and abbonamento.practitioner:
		service_provider = frappe.db.get_value(
			"CRM Service Provider", {"user": abbonamento.practitioner, "enabled": 1}, "name"
		)
	if not service_provider:
		service_provider = frappe.db.get_value("CRM Billable Service", billable_service, "default_provider")
	if not service_provider:
		frappe.throw(
			_(
				"No provider for this subscription: the qualification decides the expense type and the VAT regime, so it cannot be left to a default"
			)
		)
	# the days the instalment pays for: until the next one, or the last day
	dopo = sorted(
		getdate(r.due_on) for r in abbonamento.instalments if getdate(r.due_on) > getdate(rata.due_on)
	)
	fino = add_days(dopo[0], -1) if dopo else abbonamento.ends_on

	fattura = frappe.new_doc("CRM Invoice")
	fattura.subscription = subscription
	fattura.recipient_type = TipoDestinatario.PERSONA_FISICA
	fattura.party_type = "CRM Lead"
	fattura.party = abbonamento.lead
	if not anagrafica.pagante_della_fattura(fattura):
		fattura.billing_name = abbonamento.lead_name
	servizio = frappe.db.get_value("CRM Billable Service", billable_service, "fiscal_description")
	fattura.append(
		"items",
		{
			"billable_service": billable_service,
			"service_provider": service_provider,
			"description": _("{0}: subscription {1}").format(
				servizio or abbonamento.subscription_type, abbonamento.subscription_type
			),
			"qty": 1,
			"rate": flt(rata.amount),
			"period_from": rata.due_on,
			"period_to": fino,
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
	document will not reach the Sistema TS". The same list says what going live
	needs (`crm.invoicing.prova`); the agency's rows only the agency reads.
	"""
	frappe.has_permission("CRM Invoicing Company", "read", throw=True)
	if not frappe.db.exists("CRM Invoicing Company", company):
		frappe.throw(_("Unknown company {0}").format(company))
	return prova.mancanze(frappe.get_cached_doc("CRM Invoicing Company", company).as_dict())


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

	# What the desk needs to read in one glance, before issuing rather than after.
	# A document that turns out to be un-issuable at submit has already cost the
	# time of whoever typed it, with the client still standing there.
	etichette = {
		Canale.SDI: _("Electronic invoice, through the SdI"),
		Canale.PDF_TS: _("PDF to the client, reported to the Sistema TS"),
		Canale.PDF_SOLO: _("PDF to the client. Nothing is transmitted"),
	}
	return {
		"channel": classificazione.canale,
		"label": etichette.get(classificazione.canale, classificazione.canale),
		"sdi_allowed": classificazione.sdi_consentito,
		"sdi_required": classificazione.sdi_obbligatorio,
		"ts_required": classificazione.ts_richiesto,
		"is_healthcare": classificazione.canale == Canale.PDF_TS,
		"deadline": str(getdate(fattura.posting_date)),
		# Everything wrong with it as it stands, so the interface can say it beside
		# the line that caused it instead of in a dialog at the end.
		"blocking": [documento.in_parole(errore) for errore in classificazione.tutti_errori],
		"warnings": [documento.in_parole(avviso) for avviso in classificazione.avvisi],
		"issuable": classificazione.valido,
	}


# Guest by necessity: the accredited provider pushes notices from its own
# infrastructure and has no session here. It is not unauthenticated - every delivery
# presents a per-company shared secret, compared in constant time, and a refused one
# is told nothing about why. See crm/invoicing/sdi/webhook.py.
@frappe.whitelist(allow_guest=True, methods=["POST"])  # nosemgrep: guest-whitelisted-method
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
			"In the provider's configuration set the authentication token to the secret you generated here, as a header named X-Acube-Token or as a query parameter named token."
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
	# the provider's webhook is the agency's plumbing, like every integration's (doc 30)
	from crm.permissions.livelli import verifica_nel_crm

	verifica_nel_crm("fatture.segreti")
	segreto = frappe.generate_hash(length=48)
	azienda = frappe.get_doc("CRM Invoicing Company", company)
	azienda.sdi_webhook_secret = segreto
	azienda.save(ignore_permissions=True)
	return {
		"secret": segreto,
		**webhook_endpoint(company),
		"warning": _(
			"Copy it now: it is stored encrypted and will not be shown again. Any secret configured at the provider before this call has just stopped working."
		),
	}


@frappe.whitelist(methods=["POST"])
def reconcile_provider(company: str = "") -> dict:
	"""Fetch and apply everything the provider is holding for us.

	The webhook does this too, on the way in. This is the same work on demand, and
	on a schedule - because a webhook that was never delivered leaves no trace, and
	an invoice stuck in `inviato` looks exactly like one that went through.
	"""
	from crm.invoicing import sdi
	from crm.invoicing.sdi import itala, riconciliazione

	frappe.has_permission("CRM Invoice", "write", throw=True)
	aziende = (
		[company]
		if company
		else [riga.name for riga in frappe.get_all("CRM Invoicing Company", filters={"sdi_mode": "provider"})]
	)
	esiti = {}
	for nome in aziende:
		emittente = frappe.get_cached_doc("CRM Invoicing Company", nome).as_dict()
		if not itala.pronta(emittente) or not riconciliazione.da_chiedere(emittente):
			continue
		try:
			esiti[nome] = riconciliazione.riconcilia(emittente)
		except (sdi.ErroreCanale, connessione.ErroreProvider) as errore:
			# one company the provider cannot answer for does not cost the others theirs
			esiti[nome] = {"notices": 0, "incoming": 0, "skipped": 0, "problems": [str(errore)[:200]]}
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


@frappe.whitelist()
def practice_shape(company: str = "") -> dict:
	"""Solo practitioner or centre, worked out rather than asked.

	Whoever performed a service decides the VAT regime, the fund and - where the
	healthcare module is installed - whether the SdI may carry the document at all.
	In a centre that makes it the most important field on the line. For somebody
	working alone it is the same name every time, on a field that has exactly one
	possible value, and asking is pure friction sixty times a day.

	So it is derived from how many providers are actually enabled, not set in a
	screen. A practice that hires its second physiotherapist does not have to
	remember to flip anything: the field appears the day the second provider does.
	"""
	frappe.has_permission("CRM Service Provider", "read", throw=True)
	filtri = {"enabled": 1}
	if company:
		filtri["company"] = ["in", [company, ""]]
	erogatori = frappe.get_all(
		"CRM Service Provider", filters=filtri, fields=["name", "provider_name", "qualification"], limit=2
	)
	solo = len(erogatori) == 1
	return {
		"solo": solo,
		"count": len(erogatori),
		"provider": erogatori[0].name if solo else None,
		"provider_name": erogatori[0].provider_name if solo else None,
		"qualification": erogatori[0].qualification if solo else None,
	}


@frappe.whitelist()
def appointments_to_invoice(company: str = "", days: int = 14, limit: int = 100) -> list[dict]:
	"""Appointments that happened and have no invoice yet.

	The agenda already knows the three things routing depends on - who the client
	is, who performed, which service - plus the date. Retyping them into an invoice
	form is the difference between a system somebody uses between patients and one
	they stop using by Thursday.

	Past only, and only what is still open: a list that shows tomorrow's bookings is
	a list nobody trusts.
	"""
	frappe.has_permission("CRM Invoice", "create", throw=True)
	da = frappe.utils.add_days(frappe.utils.nowdate(), -int(days))
	fatturati = {
		riga.appointment
		for riga in frappe.get_all(
			"CRM Invoice",
			filters={"appointment": ["is", "set"], "docstatus": ["<", 2]},
			fields=["appointment"],
		)
	}
	# a session of a cycle paid as a whole is invoiced with its cycle
	interi = set(frappe.get_all("CRM Session Cycle", filters={"billing": CICLO_INTERO}, pluck="name"))
	incontri = frappe.get_all(
		"CRM Appointment",
		filters={
			"starts_on": ["between", [da, frappe.utils.now_datetime()]],
			"status": ["not in", ("Cancelled", "No Show")],
		},
		fields=[
			"name",
			"title",
			"starts_on",
			"service",
			"unit_price",
			"status",
			"session_cycle",
			"subscription",
		],
		order_by="starts_on desc",
		limit_page_length=int(limit),
	)
	return [
		dict(i)
		for i in incontri
		if i.name not in fatturati
		and not (i.session_cycle and i.session_cycle in interi)
		# an entry of a subscription is paid with its instalments
		and not i.subscription
	]
