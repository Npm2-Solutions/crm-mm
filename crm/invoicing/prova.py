# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Invoicing in test, then live.

A centre tries its invoicing before the first real invoice: every company starts in
test. There an invoice is written, issued and sent exactly as it will be, and it is
a test invoice - numbered on a series of its own (`2026/PROVA-S/1`), a band across
its PDF, its electronic copy sent to Itala's test environment, its Sistema TS report
checked and kept back. Nothing of it reaches the SdI, the Sistema TS or a patient.

Going live is one act (`go_live`): what the company cannot invoice without is
checked, the test invoices go away - the real numbering starts at one and no test
invoice sits among the real ones - and from then on every invoice is real. Back to
test is the agency's, and only while no real invoice exists: the numbering of real
invoices is a fiscal fact, not a setting.

What is still missing is one list (`mancanze`), for the company's page and for
going live: each row says what it costs, whether it stops the company from going
live, and whether it is the centre's to do or the agency's.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, now_datetime

from crm.invoicing import connessione, estensioni
from crm.invoicing.engine.numerazione import PREFISSO_PROVA
from crm.invoicing.fic import collegamento as fic
from crm.invoicing.sdi import itala
from crm.invoicing.sdi.base import ErroreCanale
from crm.permissions.livelli import puo, richiede

AZIENDA = "CRM Invoicing Company"
FATTURA = "CRM Invoice"
#: the agency's own capability on invoicing: keys, registrations, back to test
AGENZIA = "fatture.segreti"


def in_prova(emittente: dict) -> bool:
	return not connessione.in_produzione(emittente)


def segna(doc, emittente: dict) -> None:
	"""At issue, before the number: a test company's invoice is a test invoice, and
	its Sistema TS report is checked and kept back."""
	doc.test_document = 1 if in_prova(emittente) else 0
	if doc.test_document and doc.ts_status == "da_inviare":
		doc.ts_status = "prova"
	if doc.reference_invoice:
		corretta = cint(frappe.db.get_value(FATTURA, doc.reference_invoice, "test_document"))
		if corretta and not doc.test_document:
			frappe.throw(
				_("The invoice it corrects was a test: it has no fiscal value, and needs no credit note."),
				title=_("Test invoice"),
			)
		if doc.test_document and not corretta:
			frappe.throw(_("A test credit note cannot correct a real invoice."), title=_("Test invoice"))


def fuori_dalla_prova(doc, emittente: dict) -> None:
	"""A test invoice of a company gone live leaves for nowhere."""
	if cint(doc.get("test_document")) and connessione.in_produzione(emittente):
		frappe.throw(
			_("This is a test invoice and the company is live now: it does not leave."),
			title=_("Test invoice"),
		)


def _riga(
	titolo: str,
	conseguenza: str,
	campo: str = "",
	blocca: bool = False,
	agenzia: bool = False,
	doctype: str = "",
	pagina: str = "",
) -> dict:
	"""One gap. `field` is the company's field that fills it, `link` the records
	that do (with a `name`, the one record, opened on its `field`), `page` the
	settings page that does: the screen takes whoever reads it there."""
	riga = {
		"title": titolo,
		"consequence": conseguenza,
		"field": campo,
		"blocking": blocca,
		"agency": agenzia,
	}
	if doctype:
		riga["link"] = {"doctype": doctype}
	if pagina:
		riga["page"] = pagina
	return riga


def mancanze(emittente: dict, agenzia: bool | None = None) -> list[dict]:
	"""What is still missing, what each gap costs, and whose it is to fill.

	A row that `blocking` keeps the company from going live: without it no invoice
	is right. The others are said and stop nothing. The agency's rows are shown to
	the agency only: the centre cannot act on them.
	"""
	if agenzia is None:
		agenzia = puo(AGENZIA)
	righe: list[dict] = []

	def manca(condizione, *argomenti, **opzioni):
		if condizione:
			righe.append(_riga(*argomenti, **opzioni))

	manca(
		not emittente.get("tax_id"),
		_("VAT number"),
		_("No invoice can be issued: FatturaPA requires it on the issuer."),
		"tax_id",
		blocca=True,
	)
	manca(
		not (emittente.get("address_line") and emittente.get("postal_code") and emittente.get("city")),
		_("Registered office"),
		_("It goes on every invoice, and electronic invoices cannot be transmitted without it."),
		"address_line",
		blocca=True,
	)
	manca(
		emittente.get("stamp_duty_mode") == "virtuale" and not emittente.get("stamp_authorization_number"),
		_("Stamp duty authorisation"),
		_("The wording would not satisfy art. 15 DPR 642/72."),
		"stamp_authorization_number",
		blocca=True,
	)
	manca(
		not frappe.db.count("CRM Service Provider", {"enabled": 1}),
		_("At least one provider"),
		_("Nothing can be billed: the line has no qualification and therefore no VAT regime."),
		blocca=True,
		doctype="CRM Service Provider",
	)
	manca(
		not frappe.db.count("CRM Billable Service", {"enabled": 1}),
		_("At least one service card"),
		_("A service without a card is not billable."),
		blocca=True,
		doctype="CRM Billable Service",
	)

	# a company that invoices with Fatture in Cloud needs Fatture in Cloud, not Itala
	con_fic = fic.emette_con_fic(emittente.get("name"))
	if con_fic:
		manca(
			not fic.collegata(emittente.get("name")),
			_("Fatture in Cloud"),
			_("The access to Fatture in Cloud is gone: connect it again, or no invoice can be issued."),
			blocca=True,
			pagina=fic.PAGINA,
		)
		for testo in fic.da_fare(emittente.get("name")):
			manca(True, _("Fatture in Cloud"), testo, blocca=True, pagina=fic.PAGINA)
	modo = "fatture_in_cloud" if con_fic else (emittente.get("sdi_mode") or itala.CODICE)
	manca(
		modo == itala.CODICE and not itala.pronta(emittente),
		_("Itala"),
		_(
			"Electronic invoices, the ones to companies and public bodies, leave once Itala is connected: "
			"the agency does it, the centre sets up nothing."
		),
	)
	# the invoices the suppliers send come here only once Itala's recipient code is
	# the centre's address at the Agenzia: the centre's to do, once, as preservation
	codice = connessione.codice_destinatario()
	manca(
		modo == itala.CODICE and not codice,
		_("Itala's recipient code"),
		_(
			"Itala gives it with the account: without it the centre cannot be told what to register to receive its suppliers' invoices here."
		),
		"itala_recipient_code",
		agenzia=True,
	)
	manca(
		modo == itala.CODICE and bool(codice) and not emittente.get("recipient_code_registered"),
		_("Your suppliers' invoices"),
		_(
			"Register the recipient code {0} once in Fatture e Corrispettivi (ivaservizi.agenziaentrate.gov.it), you or your accountant, then tick it on the Invoicing tab: from that day the invoices your suppliers send arrive here."
		).format(codice),
		"recipient_code_registered",
	)
	# a copy of the site reads nothing of Itala's, so as not to take the updates
	# away from the site that reads them
	sito = (emittente.get("itala_site") or "").strip()
	manca(
		modo == itala.CODICE and bool(sito) and sito != frappe.local.site,
		_("Itala's updates"),
		_(
			"This site is not {0}, the one that reads the company's updates at Itala: it reads none, so as not to take them away from that one. If this is the company's site now, clear Reads Itala's updates on the company."
		).format(sito),
		"itala_site",
		agenzia=True,
	)
	# the Agenzia's free service keeps the SdI documents: joining it is the centre's,
	# once, in Fatture e Corrispettivi, and nobody can do it from here
	manca(
		not emittente.get("conservation_joined"),
		_("Preservation of the SdI documents"),
		_(
			"Ten years is mandatory, and transmitting does not provide it. Join the Agenzia's free service once, in Fatture e Corrispettivi (you or your accountant), then tick it on the Invoicing tab: it keeps the invoices from that day on."
		),
		"conservation_joined",
	)

	# what the modules add (the Sistema TS: credentials, certificate, qualifications)
	for riga in estensioni.controlli_aggiuntivi(emittente):
		righe.append({"blocking": False, "agency": False, **riga})

	return [riga for riga in righe if agenzia or not riga["agency"]]


def _predefinita() -> str | None:
	return (
		frappe.db.get_single_value("CRM Invoicing Settings", "default_company")
		or frappe.db.get_value(AZIENDA, {"is_default": 1, "enabled": 1}, "name")
		or frappe.db.get_value(AZIENDA, {"enabled": 1}, "name")
	)


@frappe.whitelist()
def get_status(company: str | None = None) -> dict:
	"""Where the company is - in test, or live since when - and what going live needs."""
	frappe.has_permission(AZIENDA, "read", throw=True)
	nome = company or _predefinita()
	if not nome or not frappe.db.exists(AZIENDA, nome):
		return {"company": None}
	emittente = frappe.get_doc(AZIENDA, nome).as_dict()
	agenzia = puo(AGENZIA)
	dal_vivo = connessione.in_produzione(emittente)
	righe = mancanze(emittente, agenzia)
	reali = frappe.db.count(FATTURA, {"company": nome, "test_document": 0, "docstatus": 1})
	stato = {
		"company": nome,
		"company_name": emittente.get("company_name")
		or " ".join(p for p in (emittente.get("first_name"), emittente.get("last_name")) if p),
		"live": dal_vivo,
		"live_since": emittente.get("live_since"),
		"test_invoices": frappe.db.count(FATTURA, {"company": nome, "test_document": 1}),
		"real_invoices": reali,
		"missing": righe,
		"ready": not any(riga["blocking"] for riga in righe),
		"itala": (emittente.get("sdi_mode") or itala.CODICE) == itala.CODICE and itala.pronta(emittente),
		# invoices born in Fatture in Cloud: they leave from there
		"fic": fic.emette_con_fic(nome),
		# how its expenses reach the Sistema TS: the invoices page offers to send them
		"ts_mode": emittente.get("ts_mode") or "export",
		# whether it reports healthcare expenses: the Sistema TS is said only then
		"healthcare": emittente.get("sender_category") not in (None, "", "non_sanitario"),
		"can": {
			"go_live": not dal_vivo and puo("fatture.configura"),
			"back_to_test": dal_vivo and agenzia and not reali,
			"register": agenzia,
		},
	}
	if agenzia:
		stato["agency"] = {
			"mode": emittente.get("sdi_mode") or itala.CODICE,
			"account": connessione.da_dove_l_account(),
			"own_account": connessione.ha_un_account_proprio(emittente),
			"registered": {
				"test": emittente.get(itala.CAMPO_ID[connessione.SANDBOX]),
				"production": emittente.get(itala.CAMPO_ID[connessione.PRODUZIONE]),
			},
		}
	return stato


def togli_le_fatture_di_prova(company: str) -> int:
	"""Take the company's test invoices away, with what hangs on them.

	They were never issued: what pointed at one (an instalment of a subscription, a
	profile filled from it) points at nothing again, and can be invoiced for real.
	"""
	righe = frappe.get_all(
		FATTURA, filters={"company": company, "test_document": 1}, fields=["name", "reference_invoice"]
	)
	# the credit notes first: they point at the invoices they correct
	righe.sort(key=lambda riga: 0 if riga.reference_invoice else 1)
	for riga in righe:
		frappe.db.set_value(
			"CRM Subscription Instalment", {"invoice": riga.name}, "invoice", None, update_modified=False
		)
		frappe.db.set_value(
			"CRM Billing Profile",
			{"filled_from_invoice": riga.name},
			"filled_from_invoice",
			None,
			update_modified=False,
		)
		frappe.db.delete("CRM Invoice Log", {"invoice": riga.name})
		# a test invoice was never issued: nothing about it is kept, not even as cancelled
		frappe.db.set_value(FATTURA, riga.name, "docstatus", 2, update_modified=False)
		frappe.delete_doc(FATTURA, riga.name, ignore_permissions=True, force=True, delete_permanently=True)
	frappe.db.delete("CRM Invoice Series", {"company": company, "series": ["like", f"{PREFISSO_PROVA}-%"]})
	return len(righe)


@frappe.whitelist(methods=["POST"])
@richiede("fatture.configura")
def go_live(company: str) -> dict:
	"""From now on every invoice of the company is real."""
	doc = frappe.get_doc(AZIENDA, company)
	doc.check_permission("write")
	emittente = doc.as_dict()
	if connessione.in_produzione(emittente):
		frappe.throw(_("This company is live already."))
	bloccano = [riga for riga in mancanze(emittente, agenzia=True) if riga["blocking"]]
	if bloccano:
		frappe.throw(
			"<br>".join(f"{riga['title']}: {riga['consequence']}" for riga in bloccano),
			title=_("Not ready to go live"),
		)

	tolte = togli_le_fatture_di_prova(company)
	frappe.db.set_value(
		AZIENDA,
		company,
		{"provider_environment": connessione.PRODUZIONE, "live_since": now_datetime()},
		update_modified=False,
	)
	frappe.clear_document_cache(AZIENDA, company)
	doc = frappe.get_doc(AZIENDA, company)
	doc.add_comment("Info", _("Invoicing went live: from now on every invoice is real."))

	# registered now, when Itala is connected: the first invoice to a company does not
	# wait for it. If it cannot be done now, the first invoice does it.
	nota = ""
	emittente = doc.as_dict()
	if (
		(emittente.get("sdi_mode") or itala.CODICE) == itala.CODICE
		and itala.pronta(emittente)
		and not fic.emette_con_fic(company)
	):
		try:
			itala.registra_azienda(emittente, connessione.PRODUZIONE)
		except (ErroreCanale, connessione.ErroreProvider) as errore:
			nota = _("Itala will register the company with its first electronic invoice: {0}").format(
				str(errore)
			)
	return {"live": True, "removed": tolte, "note": nota, "status": get_status(company)}


@frappe.whitelist(methods=["POST"])
@richiede(AGENZIA)
def back_to_test(company: str) -> dict:
	"""Back to test: the agency's, and only while no real invoice exists."""
	doc = frappe.get_doc(AZIENDA, company)
	doc.check_permission("write")
	reali = frappe.db.count(FATTURA, {"company": company, "test_document": 0, "docstatus": 1})
	if reali:
		frappe.throw(
			_(
				"{0} real invoices are issued: the company stays live, their numbering is a fiscal fact."
			).format(reali)
		)
	frappe.db.set_value(
		AZIENDA,
		company,
		{"provider_environment": connessione.SANDBOX, "live_since": None},
		update_modified=False,
	)
	frappe.clear_document_cache(AZIENDA, company)
	frappe.get_doc(AZIENDA, company).add_comment("Info", _("Invoicing is back in test."))
	return get_status(company)


@frappe.whitelist(methods=["POST"])
@richiede(AGENZIA)
def register_at_itala(company: str, environment: str | None = None) -> dict:
	"""Register the company under the agency's account now, rather than with its
	first invoice."""
	doc = frappe.get_doc(AZIENDA, company)
	doc.check_permission("write")
	emittente = doc.as_dict()
	try:
		identificativo = itala.registra_azienda(emittente, environment or connessione.ambiente(emittente))
	except (ErroreCanale, connessione.ErroreProvider) as errore:
		frappe.throw(str(errore), title=_("Itala"))
	return {"id": identificativo, "status": get_status(company)}


@frappe.whitelist(methods=["POST"])
@richiede(AGENZIA)
def remove_from_itala(company: str, environment: str | None = None) -> dict:
	"""Take the company away from the agency's account at Itala: a centre that
	leaves stops sending and receiving through it. In production by default."""
	doc = frappe.get_doc(AZIENDA, company)
	doc.check_permission("write")
	emittente = doc.as_dict()
	try:
		tolta = itala.rimuovi_azienda(emittente, environment or connessione.PRODUZIONE)
	except (ErroreCanale, connessione.ErroreProvider) as errore:
		frappe.throw(str(errore), title=_("Itala"))
	if tolta:
		doc.add_comment("Info", _("Removed from the agency's account at Itala."))
	return {"removed": tolta, "status": get_status(company)}
