# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""From a CRM Invoice record to the engine, and back.

The controller stays thin on purpose. Everything that decides a tax outcome lives
in `engine/`, and this module is the translation layer: it reads the service
cards, hands the engine a list of lines, and writes the answer back onto the
document. Nothing here decides anything.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import frappe
from frappe import _
from frappe.utils import flt, getdate

from crm.invoicing import registro
from crm.invoicing.engine import calcolo as motore
from crm.invoicing.engine import codice_fiscale as cf
from crm.invoicing.engine import diciture
from crm.invoicing.engine.classificazione import RigaDaClassificare, classifica
from crm.invoicing.engine.codici import (
	NATURE_REVERSE_CHARGE,
	Canale,
	ModalitaBollo,
	RegimeFiscale,
	TipoDestinatario,
)
from crm.invoicing.engine.numerazione import FormatoNonCompatibile, componi, prossimo, valida_formato

ZERO = Decimal("0.00")


def _dec(valore) -> Decimal:
	return Decimal(str(flt(valore or 0)))


def scheda(nome: str) -> dict:
	"""The fiscal card of a service. Without one, nothing is billable."""
	campi = (
		"name",
		"fiscal_description",
		"is_healthcare",
		"vat_exempt",
		"exemption_reference",
		"vat_rate",
		"vat_nature",
		"ts_expense_type",
		"ts_expense_flag",
		"subject_to_stamp_duty",
		"is_advance",
		"default_rate",
		"uom",
		"default_provider",
		"verified_by_accountant",
		"enabled",
	)
	dati = frappe.db.get_value("CRM Billable Service", nome, campi, as_dict=True)
	if not dati:
		frappe.throw(
			_("The service {0} has no fiscal card: a service without a card is not billable").format(nome)
		)
	return dati


def applica_scheda(riga, dati: dict) -> None:
	"""Prefill the line from the service card, without overwriting a choice.

	The card proposes; the line is what was confirmed. Overwriting a confirmed
	value would silently undo an operator's correction, and on this document a
	silent correction is a rejected row three months later.
	"""
	if not riga.description:
		riga.description = dati.get("fiscal_description")
	if not riga.uom:
		riga.uom = dati.get("uom")
	if not flt(riga.rate) and dati.get("default_rate"):
		riga.rate = dati["default_rate"]
	if not riga.service_provider and dati.get("default_provider"):
		riga.service_provider = dati["default_provider"]
	for campo, chiave in (
		("is_healthcare", "is_healthcare"),
		("vat_exempt", "vat_exempt"),
		("is_advance", "is_advance"),
	):
		if riga.get(campo) is None:
			riga.set(campo, dati.get(chiave))
	if riga.vat_rate in (None, 0) and not riga.vat_exempt and dati.get("vat_rate"):
		riga.vat_rate = dati["vat_rate"]
	if not riga.vat_nature and dati.get("vat_nature"):
		riga.vat_nature = dati["vat_nature"]
	if not riga.ts_expense_type and dati.get("ts_expense_type"):
		riga.ts_expense_type = dati["ts_expense_type"]
	if not riga.ts_expense_flag and dati.get("ts_expense_flag"):
		riga.ts_expense_flag = dati["ts_expense_flag"]


def importo_riga(riga) -> Decimal:
	"""Quantity times rate, less the discount. Rounded once, here."""
	lordo = _dec(riga.qty or 1) * _dec(riga.rate)
	sconto = _dec(riga.discount_amount)
	if not sconto and flt(riga.discount_percentage):
		sconto = motore.arrotonda(lordo * _dec(riga.discount_percentage) / Decimal("100"))
	riga.discount_amount = float(sconto)
	netto = motore.arrotonda(lordo - sconto)
	riga.amount = float(netto)
	return netto


def righe_da_documento(doc) -> list[RigaDaClassificare]:
	righe: list[RigaDaClassificare] = []
	for riga in doc.items:
		dati = scheda(riga.billable_service)
		applica_scheda(riga, dati)
		if not riga.service_provider:
			frappe.throw(
				_(
					"Line {0}: the provider has to be confirmed. It decides the expense type and the "
					"VAT regime, and a wrong one produces no error - it produces rejected rows"
				).format(riga.idx)
			)
		riga.qualification = riga.qualification or frappe.db.get_value(
			"CRM Service Provider", riga.service_provider, "qualification"
		)
		if not dati.get("enabled"):
			frappe.throw(
				_("The service {0} is disabled: re-enable it or pick another one").format(
					riga.billable_service
				)
			)
		righe.append(
			RigaDaClassificare(
				servizio_id=riga.billable_service,
				descrizione_fiscale=riga.description or dati.get("fiscal_description") or "",
				is_sanitaria=bool(riga.is_healthcare),
				esente_iva=bool(riga.vat_exempt),
				erogatore_id=riga.service_provider,
				erogatore_qualifica=riga.qualification,
				imponibile=importo_riga(riga),
				tipo_spesa_catalogo=riga.ts_expense_type or None,
				natura_iva_catalogo=riga.vat_nature or None,
				aliquota_catalogo=_dec(riga.vat_rate) if riga.vat_rate else None,
				flag_tipo_spesa=riga.ts_expense_flag or None,
				quota_non_a_carico=_dec(riga.not_borne_amount) or None,
				e_anticipazione=bool(riga.is_advance),
			)
		)
	return righe


def azienda(doc) -> dict:
	if not doc.company:
		frappe.throw(_("No issuing company on the document"))
	if not frappe.db.exists("CRM Invoicing Company", doc.company):
		frappe.throw(_("The issuing company {0} does not exist").format(doc.company))
	return frappe.get_cached_doc("CRM Invoicing Company", doc.company).as_dict()


def prepara(doc) -> dict:
	"""Classify, compute, and write the answer back onto the document.

	Returns the engine objects so callers that need the detail - the XML builder,
	the preview endpoint - do not have to redo the work.
	"""
	emittente = azienda(doc)
	righe = righe_da_documento(doc)
	regime = emittente.get("tax_regime") or RegimeFiscale.ORDINARIO

	classificazione = classifica(
		righe,
		doc.recipient_type or TipoDestinatario.PERSONA_FISICA,
		regime,
		emittente.get("sender_category"),
		registro.risolutore(),
	)

	soggetto_a_bollo = bool(doc.subject_to_stamp_duty) and any(
		scheda(r.billable_service).get("subject_to_stamp_duty") for r in doc.items
	)
	impostazioni = frappe.get_cached_doc("CRM Invoicing Settings")

	conto = motore.calcola(
		classificazione,
		tipo_cassa=doc.fund_type or None,
		percentuale_cassa=_dec(doc.fund_rate) if doc.fund_rate else None,
		cassa_obbligatoria=bool(doc.fund_mandatory),
		cassa_soggetta_a_ritenuta=bool(doc.fund_subject_to_withholding),
		applica_rivalsa_facoltativa=bool(doc.apply_optional_fund),
		modalita_bollo=doc.stamp_duty_mode or ModalitaBollo.SU_ORIGINALE,
		bollo_riaddebitato=bool(doc.recharge_stamp_duty),
		soggetto_a_bollo=soggetto_a_bollo,
		bollo_pagato_in_contanti=bool(doc.stamp_duty_paid_cash),
		anticipazioni_nella_base_bollo=bool(impostazioni.advances_in_stamp_base),
		applica_ritenuta=bool(doc.apply_withholding),
		aliquota_ritenuta=_dec(doc.withholding_rate) or Decimal("20.00"),
		tipo_ritenuta=doc.withholding_type or "RT01",
		causale_pagamento=doc.payment_reason or "A",
		split_payment=bool(doc.split_payment),
		riferimenti_normativi=_riferimenti(doc, emittente),
	)

	_scrivi_totali(doc, classificazione, conto)
	_scrivi_righe(doc, conto)
	_scrivi_riepilogo(doc, conto)
	doc.legal_notes = "\n".join(annotazioni(doc, emittente, classificazione, conto))
	doc.warnings = "\n".join(classificazione.tutti_avvisi + conto.avvisi)
	return {"classificazione": classificazione, "calcolo": conto, "azienda": emittente}


def _riferimenti(doc, emittente: dict) -> dict[str, str]:
	"""`RiferimentoNormativo` per nature: the human on the other side reads it."""
	data = getdate(doc.posting_date) or date.today()
	struttura = str(emittente.get("sender_category") or "").startswith("struttura")
	riferimenti = {
		"N4": diciture.esenzione(data, struttura),
		"N2.2": diciture.forfettario(includi_ritenuta=False)[0],
		"N2.1": diciture.fuori_campo_territoriale(data),
		"N1": diciture.anticipazione(data),
	}
	for natura in NATURE_REVERSE_CHARGE:
		riferimenti[natura] = diciture.inversione_contabile(natura)
	return riferimenti


def _scrivi_totali(doc, classificazione, conto) -> None:
	doc.channel = classificazione.canale
	doc.net_total = float(conto.imponibile)
	doc.fund_contribution = float(conto.cassa)
	doc.vat_total = float(conto.iva)
	doc.excluded_total = float(conto.anticipazioni)
	doc.stamp_duty = float(conto.bollo)
	doc.stamp_duty_recharged = float(conto.bollo_riaddebitato)
	doc.withholding_base = float(conto.base_ritenuta)
	doc.withholding_amount = float(conto.ritenuta)
	doc.grand_total = float(conto.totale)
	doc.net_payable = float(conto.netto_a_pagare)
	doc.ts_total = float(conto.totale_ts)
	doc.payment_traced = _tracciato(doc.payment_method)
	doc.ts_year = (getdate(doc.payment_date) or getdate(doc.posting_date)).year
	if classificazione.ts_richiesto:
		if doc.ts_status in (None, "", "non_applicabile"):
			doc.ts_status = "da_inviare"
	elif doc.ts_status in (None, "", "da_inviare"):
		doc.ts_status = "non_applicabile"
	if classificazione.canale == Canale.SDI:
		if doc.sdi_status in (None, "", "non_applicabile"):
			doc.sdi_status = "da_inviare"
	elif doc.sdi_status in (None, "", "da_inviare"):
		doc.sdi_status = "non_applicabile"


def _tracciato(metodo: str | None) -> str:
	esito = motore.tracciabile(metodo)
	if esito is None:
		return "not_applicable"
	return "yes" if esito else "no"


def _scrivi_righe(doc, conto) -> None:
	for riga_doc, riga_calcolata in zip(doc.items, conto.righe, strict=False):
		esito = riga_calcolata.esito
		riga_doc.vat_rate = float(esito.aliquota or 0)
		riga_doc.vat_nature = esito.natura_iva or None
		riga_doc.vat_amount = float(riga_calcolata.iva)
		riga_doc.fund_share = float(riga_calcolata.cassa)
		riga_doc.line_total = float(riga_calcolata.totale)
		riga_doc.ts_amount = float(riga_calcolata.importo_ts)
		riga_doc.ts_expense_type = riga_calcolata.tipo_spesa or riga_doc.ts_expense_type


def _scrivi_riepilogo(doc, conto) -> None:
	doc.set("tax_summary", [])
	for riepilogo in conto.riepiloghi:
		doc.append(
			"tax_summary",
			{
				"vat_rate": float(riepilogo.aliquota),
				"vat_nature": riepilogo.natura,
				"taxable_amount": float(riepilogo.imponibile),
				"tax_amount": float(riepilogo.imposta),
				"collectability": riepilogo.esigibilita,
				"legal_reference": riepilogo.riferimento_normativo,
			},
		)


def annotazioni(doc, emittente: dict, classificazione, conto) -> list[str]:
	"""The wording that has to appear on the document.

	On a PDF this is what carries legal weight, not the `N4` code: that is an XML
	field. Every reference is doubled with the Testo Unico applicable from 2027.
	"""
	data = getdate(doc.posting_date) or date.today()
	struttura = str(emittente.get("sender_category") or "").startswith("struttura")
	testi: list[str] = []

	if emittente.get("tax_regime") == RegimeFiscale.FORFETTARIO:
		testi.extend(diciture.forfettario())
	elif any(r.esente_iva for r in classificazione.righe):
		testi.append(diciture.esenzione(data, struttura))

	nature = {r.natura_iva for r in classificazione.righe if r.natura_iva}
	if nature & NATURE_REVERSE_CHARGE:
		testi.append(diciture.inversione_contabile(sorted(nature & NATURE_REVERSE_CHARGE)[0]))
	if "N2.1" in nature:
		testi.append(diciture.fuori_campo_territoriale(data))
	if "N1" in nature:
		testi.append(diciture.anticipazione(data))
	if doc.split_payment:
		testi.append(diciture.scissione_pagamenti(data))

	if conto.bollo_dovuto:
		if doc.stamp_duty_mode == ModalitaBollo.VIRTUALE:
			testi.append(
				diciture.bollo_virtuale(
					data,
					emittente.get("stamp_authorization_number"),
					getdate(emittente.get("stamp_authorization_date")),
					emittente.get("stamp_authorization_office"),
					conto.bollo,
				)
			)
		else:
			testi.append(
				diciture.bollo_su_originale(doc.stamp_identifier, getdate(doc.stamp_date), data, conto.bollo)
			)

	if conto.ritenuta > ZERO:
		testi.append(diciture.ritenuta_acconto(data, conto.aliquota_ritenuta, conto.ritenuta))
	elif doc.recipient_type == TipoDestinatario.PERSONA_FISICA and not doc.privacy_opposition:
		# Not required, but a client who expects a withholding line asks why it is
		# missing, and the answer is on the document instead of on the phone.
		testi.append(diciture.niente_ritenuta())

	if doc.payment_method:
		testi.append(diciture.pagamento(doc.payment_method, motore.tracciabile(doc.payment_method)))
	if doc.privacy_opposition and doc.print_opposition:
		testi.append(diciture.opposizione())
	if emittente.get("document_mode") == "elettronica_extra_sdi":
		testi.append(diciture.conservazione_elettronica())
	if doc.causale:
		testi.append(doc.causale)
	return testi


# ------------------------------------------------------------ blocking checks


def blocchi(doc, classificazione) -> list[str]:
	"""Everything wrong with the document, at once.

	Not the first problem: **all** of them. Whoever is fixing this has the client in
	front of them, and correcting in one pass costs nothing while correcting in five
	costs the appointment.
	"""
	problemi: list[str] = list(classificazione.tutti_errori)

	if doc.recipient_type == TipoDestinatario.PERSONA_FISICA:
		if not doc.billing_name:
			problemi.append(_("The client's name is missing"))
		if classificazione.ts_richiesto and not doc.privacy_opposition and not doc.fiscal_code:
			problemi.append(
				_(
					"Codice fiscale missing: the Sistema TS needs it unless the client has opposed "
					"the use of the expense in the pre-filled return"
				)
			)
		if doc.fiscal_code and not cf.valido(doc.fiscal_code):
			problemi.append(_("The client's codice fiscale fails its check character"))
	else:
		if not doc.billing_name:
			problemi.append(_("The client's name is missing"))
		if not (doc.tax_id or doc.fiscal_code):
			problemi.append(
				_(
					"A document towards a VAT subject, the public administration or abroad needs a VAT "
					"number or a codice fiscale"
				)
			)
		if doc.tax_id and not cf.partita_iva_ue_valida(doc.tax_id, doc.country):
			problemi.append(
				_("The VAT number {0} is not well formed for country {1}").format(doc.tax_id, doc.country)
			)

	if not doc.payment_method:
		problemi.append(_("No payment method: the Sistema TS asks whether the payment was traced"))

	data_documento = getdate(doc.posting_date)
	if doc.payment_date and getdate(doc.payment_date) < data_documento and not doc.advance_payment:
		problemi.append(
			_(
				"The payment date precedes the document date: if this is a prepaid package say so, "
				"otherwise one of the two dates is wrong"
			)
		)

	if doc.document_type in ("TD04", "TD05", "TD08", "TD09") and not doc.reference_invoice:
		problemi.append(_("A credit or debit note has to say which document it corrects"))

	if classificazione.canale == Canale.SDI and not (doc.address_line and doc.postal_code and doc.city):
		# A warning would be wrong here: without an address the XML is not
		# transmissible, and the client is standing at the desk right now.
		problemi.append(_("An electronic invoice needs the client's address: street, postal code and city"))
	return problemi


# ------------------------------------------------------------------ numbering


def numera(doc) -> None:
	"""Assign the fiscal number, locking the counter row.

	The lock is not optional: two concurrent submissions on the same series would
	produce the same number, and a duplicate number is not corrected - it is
	reversed with a credit note.
	"""
	if doc.document_number:
		return
	emittente = azienda(doc)
	serie = (
		emittente.get("series_electronic")
		if doc.channel == Canale.SDI
		else emittente.get("series_healthcare")
	)
	serie = (serie or "E").strip()
	formato = emittente.get("number_format") or "{anno}/{serie}/{numero}"
	anno = getdate(doc.posting_date).year

	try:
		valida_formato(formato, serie, anno)
	except FormatoNonCompatibile as errore:
		frappe.throw(str(errore), title=_("Numbering format"))

	nome = f"{doc.company}-{serie}-{anno}"
	if not frappe.db.exists("CRM Invoice Series", nome):
		contatore = frappe.get_doc(
			{
				"doctype": "CRM Invoice Series",
				"company": doc.company,
				"series": serie,
				"fiscal_year": anno,
				"last_number": 0,
				"number_format": formato,
			}
		)
		contatore.insert(ignore_permissions=True)

	ultimo = frappe.db.get_value("CRM Invoice Series", nome, "last_number", for_update=True)
	progressivo = prossimo(ultimo)
	frappe.db.set_value("CRM Invoice Series", nome, "last_number", progressivo)

	doc.series = serie
	doc.fiscal_year = anno
	doc.sequence = progressivo
	doc.document_number = componi(formato, serie, anno, progressivo)


# ---------------------------------------------------------------------- log


def registra(doc, evento: str, messaggio: str = "", stato: str = "", payload: dict | None = None) -> None:
	"""Append to the invoice log.

	The payload never carries the content of a healthcare document - identifiers and
	hashes only. A log that records what the service was is a second copy of the
	thing being protected.
	"""
	frappe.get_doc(
		{
			"doctype": "CRM Invoice Log",
			"invoice": doc.name,
			"company": doc.company,
			"event": evento,
			"status": stato,
			"actor": frappe.session.user,
			"occurred_on": frappe.utils.now_datetime(),
			"message": messaggio,
			"payload": frappe.as_json(payload) if payload else None,
		}
	).insert(ignore_permissions=True)


# ------------------------------------------------------- a rejected document


def riapri_scartata(doc) -> dict:
	"""Put a rejected invoice back in draft, keeping its number and its date.

	A rejection means the invoice **counts as not issued** (Circolare 13/E del 2
	luglio 2018), so correcting it is not rewriting history - the document does not
	exist yet. The Agenzia's preferred route is to resend it with the **same number
	and the same date** within five days of the notice, and that is only possible if
	the number survives the correction.

	What does not survive is the file: the SdI refuses a file name it has already
	seen, so the XML is discarded and rebuilt with a fresh transmission progressive.
	The courtesy PDF goes with it, because it now describes a document that changed.
	"""
	if doc.docstatus != 1:
		frappe.throw(_("Only an issued invoice can be reopened"))
	if doc.sdi_status != "scartata":
		frappe.throw(
			_(
				"This invoice was not rejected. A document the Sistema di Interscambio accepted is "
				"corrected with a credit note, not by editing it."
			)
		)

	for campo in ("xml_file", "pdf_file"):
		for allegato in frappe.get_all(
			"File",
			filters={
				"attached_to_doctype": doc.doctype,
				"attached_to_name": doc.name,
				"attached_to_field": campo,
			},
			pluck="name",
		):
			frappe.delete_doc("File", allegato, ignore_permissions=True, force=True)

	doc.db_set(
		{
			"docstatus": 0,
			"xml_file": None,
			"xml_hash": None,
			"sdi_filename": None,
			"pdf_file": None,
			"pdf_hash": None,
			"pdf_conformita": None,
			"sdi_status": "da_inviare",
			"sdi_sent_on": None,
		},
		update_modified=False,
	)

	scadenza = None
	if doc.sdi_message:
		# Five days from the notice, and it is a fiscal deadline rather than a
		# technical one: past it the document still has to go out, late.
		scadenza = frappe.utils.add_days(frappe.utils.nowdate(), 5)

	registra(
		doc,
		"sdi_blocked",
		_("Reopened for correction, keeping number {0} and date {1}").format(
			doc.document_number, doc.posting_date
		),
		stato="riaperta",
		payload={"previous_message": doc.sdi_message},
	)
	return {
		"invoice": doc.name,
		"document_number": doc.document_number,
		"posting_date": str(doc.posting_date),
		"deadline": str(scadenza) if scadenza else None,
	}
