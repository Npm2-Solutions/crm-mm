# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""An invoice of a company that issues with Fatture in Cloud: born there.

At issue (`CRMInvoice.before_submit`, after the document's own checks and before
its number): what was computed here is handed over (`regole.documento`), Fatture in
Cloud adds it up first and its totals must be ours to the cent; then it is made
there, and the number it takes there is the invoice's. A transaction undone after
that takes it away from Fatture in Cloud too (`after_rollback`); one that was not
undone in time, or an answer lost on the way, is found again by its mark before
anything is made twice (`_gia_fatta`), and the invoice made there is used.

Then: the e-invoice leaves for the SdI from Fatture in Cloud (`trasmetti`: the
button, or the switch that sends at issue); every ten minutes the invoices on
their way are asked how they are (`riconcilia`); a collection marked here is
marked there (`segna_incasso`); an invoice cancelled here before it left is
deleted there (`annulla`).

A test invoice never reaches Fatture in Cloud, nor does anything of the demo's.
"""

from __future__ import annotations

from functools import partial

import frappe
from frappe import _
from frappe.utils import cint, getdate, now_datetime

from crm.invoicing.engine.codici import Canale
from crm.invoicing.fic import collegamento, regole
from crm.invoicing.fic.client import ErroreFiC, chiama

FATTURA = "CRM Invoice"
#: Each round of `riconcilia` asks at most this many invoices.
PER_GIRO = 100


def marcatore(doc) -> str:
	"""What the invoice made there carries in its subject, which the PDF does not
	show: the site and the invoice it came from, to find it again."""
	from crm.marchio import nome

	return f"{nome()} · {frappe.local.site} · {doc.name}"


def _cerca(doc) -> str:
	return f"{frappe.local.site} · {doc.name}"


def tocca_a_fic(doc) -> bool:
	"""Whether this invoice is Fatture in Cloud's: its company issues there, it is
	real, and it is not the demo's."""
	from crm.demo import guardie

	if cint(doc.get("test_document")):
		return False
	if not collegamento.emette_con_fic(doc.company):
		return False
	return not guardie.mai_fuori(FATTURA, doc.name)


# --------------------------------------------------------------------- the data


def _ts_da_fic(doc) -> bool:
	return doc.ts_status in ("da_inviare", "fatture_in_cloud") and (
		frappe.db.get_value(collegamento.DOCTYPE, doc.company, "ts_by") == "fatture_in_cloud"
	)


def fattura_per_fic(doc, preparato) -> dict:
	"""The invoice as `regole.documento` reads it: what was computed here, in plain
	values, with the words of its VAT and payment for what goes wrong."""
	conto = preparato["calcolo"]
	righe = []
	chiave_bollo = None
	for riga_doc, riga in zip(doc.items, conto.righe, strict=False):
		chiave = regole.chiave_iva(riga.aliquota, riga.natura)
		if chiave_bollo is None and (riga.natura or riga.esito.esente_iva) and not riga.fuori_base_iva:
			chiave_bollo = chiave
		righe.append(
			{
				"descrizione": riga_doc.description
				or frappe.db.get_value("CRM Billable Service", riga_doc.billable_service, "service_name")
				or riga_doc.billable_service,
				"quantita": riga_doc.qty or 1,
				"prezzo": riga_doc.rate,
				"sconto": riga_doc.discount_percentage,
				"sconto_importo": riga_doc.discount_amount if not riga_doc.discount_percentage else 0,
				"importo": riga_doc.amount,
				"chiave_iva": chiave,
				"anticipazione": bool(riga_doc.is_advance),
				"tipo_spesa": riga.tipo_spesa or riga_doc.ts_expense_type,
				"al_ts": bool(riga.esito.va_al_ts),
				"bandiera_spesa": riga_doc.ts_expense_flag,
			}
		)
	riferimento = {}
	if doc.reference_invoice:
		originale = frappe.db.get_value(
			FATTURA, doc.reference_invoice, ["document_number", "posting_date"], as_dict=True
		)
		if originale:
			riferimento = {"numero": originale.document_number, "data": str(getdate(originale.posting_date))}
	cassa = None
	if conto.tipo_cassa and conto.percentuale_cassa:
		cassa = {
			"tipo": conto.tipo_cassa,
			"percentuale": conto.percentuale_cassa,
			"soggetta_a_ritenuta": conto.cassa_soggetta_a_ritenuta,
		}
	ritenuta = None
	if conto.ritenuta:
		ritenuta = {
			"percentuale": conto.aliquota_ritenuta,
			"tipo": conto.tipo_ritenuta,
			"causale": conto.causale_pagamento,
		}
	pagato = None
	if getattr(doc.flags, "pagata_alla_cassa", False) or doc.collected_on:
		pagato = str(getdate(doc.collected_on or doc.payment_date or doc.posting_date))
	chiavi = {riga["chiave_iva"] for riga in righe} | ({chiave_bollo} if chiave_bollo else set())
	return {
		"tipo": doc.document_type or "TD01",
		"data": str(getdate(doc.posting_date)),
		"elettronica": doc.channel == Canale.SDI,
		"marcatore": marcatore(doc),
		"causale": (doc.causale or "").strip(),
		"destinatario": {
			"tipo": doc.recipient_type,
			"nome": doc.billing_name,
			"nome_proprio": doc.first_name,
			"cognome": doc.last_name,
			"partita_iva": doc.tax_id,
			"codice_fiscale": doc.fiscal_code,
			"indirizzo": doc.address_line,
			"civico": doc.civic_number,
			"cap": doc.postal_code,
			"citta": doc.city,
			"provincia": doc.province,
			"paese": doc.country or "IT",
			"codice_destinatario": doc.recipient_code,
			"pec": doc.pec,
		},
		"righe": righe,
		"chiave_iva_bollo": chiave_bollo,
		"iva_in_parole": {chiave: collegamento.iva_in_parole(chiave) for chiave in chiavi},
		"metodi_in_parole": {doc.payment_method: collegamento.metodo_in_parole(doc.payment_method)}
		if doc.payment_method
		else {},
		"bollo": conto.bollo,
		"bollo_riaddebitato": conto.bollo_riaddebitato,
		"cassa": cassa,
		"ritenuta": ritenuta,
		"split_payment": bool(conto.split_payment),
		"metodo_pagamento": doc.payment_method,
		"pagamento": {
			"importo": conto.netto_a_pagare,
			"scadenza": str(getdate(doc.payment_date or doc.posting_date)),
			"pagato_il": pagato,
		},
		"riferimento": riferimento,
		"cig": doc.cig,
		"cup": doc.cup,
		"ordine": doc.purchase_order,
		"ts": {
			"tracciato": doc.payment_traced == "yes",
			"opposizione": bool(doc.privacy_opposition),
		}
		if _ts_da_fic(doc)
		else None,
	}


def _nostri_totali(conto) -> dict:
	return {"iva": conto.iva, "ritenuta": conto.ritenuta, "da_pagare": conto.netto_a_pagare}


def _in_euro(valore) -> str:
	from crm.invoicing.documento import in_euro

	return in_euro(regole.decimale(valore))


def _parole(problemi: list[regole.Problema]) -> list[str]:
	parole = []
	for problema in problemi:
		argomenti = tuple(
			_in_euro(argomento) if hasattr(argomento, "quantize") else argomento
			for argomento in problema.argomenti
		)
		parole.append(_(problema.messaggio).format(*argomenti))
	return parole


def _ferma(righe: list[str], titolo: str | None = None) -> None:
	frappe.throw("<br>".join(righe), title=titolo or _("Fatture in Cloud"))


# ------------------------------------------------------------------- the issue


def emetti(doc, preparato) -> None:
	"""Make the invoice in Fatture in Cloud and give it the number it takes there.

	Called by `before_submit` for an invoice that is Fatture in Cloud's
	(`tocca_a_fic`). Nothing is made there unless its totals are ours."""
	connessione = collegamento.connessione(doc.company)
	dati, problemi = regole.documento(fattura_per_fic(doc, preparato), collegamento.mappa(connessione))
	if problemi:
		_ferma(_parole(problemi), _("The document cannot be issued"))
	if doc.ts_status == "da_inviare" and dati.get("extra_data", {}).get("ts_communication"):
		doc.ts_status = "fatture_in_cloud"

	try:
		totali = (
			collegamento.chiama_per(
				doc.company, "POST", "/c/{c}/issued_documents/totals", json={"data": dati}
			)
			or {}
		).get("data") or {}
	except ErroreFiC as errore:
		_ferma([str(errore), *errore.rilievi])
	diversi = regole.totali_diversi(_nostri_totali(preparato["calcolo"]), totali)
	if diversi:
		_ferma(_parole(diversi), _("The totals do not match"))

	try:
		# reopened after a rejection it is the same invoice there, with its number
		fatta = {"id": doc.fic_document_id} if doc.fic_document_id else _gia_fatta(doc)
		if fatta:
			# made by an attempt whose answer was lost: brought up to date, kept
			fatta = (
				collegamento.chiama_per(
					doc.company, "PUT", f"/c/{{c}}/issued_documents/{fatta['id']}", json={"data": dati}
				)
				or {}
			).get("data") or fatta
		else:
			fatta = (
				collegamento.chiama_per(
					doc.company,
					"POST",
					"/c/{c}/issued_documents",
					json={"data": dati, "options": {"fix_payments": False}},
				)
				or {}
			).get("data") or {}
	except ErroreFiC as errore:
		if errore.incerto:
			_ferma(
				[
					str(errore),
					_(
						"It may have been made in Fatture in Cloud all the same: issuing it again first looks for it there."
					),
				]
			)
		_ferma([str(errore), *errore.rilievi])
	if not fatta.get("id"):
		_ferma([_("Fatture in Cloud answered something unreadable.")])

	# undone after this, a new invoice goes from Fatture in Cloud too: it never left.
	# What it takes is read now - after the rollback the connection may not be there
	if not doc.fic_document_id:
		connessione = collegamento.connessione(doc.company)
		frappe.db.after_rollback.add(
			partial(
				_togli_dopo_rollback,
				connessione.fic_company_id,
				collegamento.token(doc.company),
				int(fatta["id"]),
			)
		)
	_numera(doc, fatta)


def _numera(doc, fatta: dict) -> None:
	numerazione = fatta.get("numeration") or ""
	doc.fic_document_id = str(fatta["id"])
	doc.series = numerazione
	doc.sequence = cint(fatta.get("number"))
	doc.fiscal_year = getdate(fatta.get("date") or doc.posting_date).year
	doc.document_number = regole.numero_stampato(fatta.get("number"), numerazione)


def _gia_fatta(doc) -> dict | None:
	"""The invoice an earlier attempt made there, found by its mark: an answer lost on
	the way, or a transaction undone before it could take it away."""
	tipo = regole.TIPI.get(doc.document_type or "TD01")
	try:
		trovate = (
			collegamento.chiama_per(
				doc.company,
				"GET",
				"/c/{c}/issued_documents",
				params={
					"type": tipo,
					"q": f"subject contains '{_cerca(doc)}'",
					"fields": "id,number,numeration,date,subject",
					"per_page": 5,
				},
			)
			or {}
		).get("data") or []
	except ErroreFiC as errore:
		if errore.incerto or errore.stato in (401, 429) or (errore.stato or 0) >= 500:
			raise
		# a filter Fatture in Cloud does not take: nothing to find, and said in the log
		frappe.log_error(title=f"Fatture in Cloud: looking for {doc.name}", message=str(errore))
		return None
	return next((voce for voce in trovate if _cerca(doc) in (voce.get("subject") or "")), None)


def _togli_dopo_rollback(azienda_fic: int, access_token: str, identificativo: int) -> None:
	try:
		chiama("DELETE", f"/c/{azienda_fic}/issued_documents/{identificativo}", access_token)
	except Exception:
		# found again by its mark at the next attempt
		frappe.log_error(
			title=f"Fatture in Cloud: invoice {identificativo} left there", message=frappe.get_traceback()
		)


# -------------------------------------------------------------------- the SdI


def pronta(company: str | None) -> bool:
	return collegamento.emette_con_fic(company) and collegamento.collegata(company)


def trasmetti(doc) -> dict:
	"""Send the e-invoice to the SdI from Fatture in Cloud: its own check first,
	whose findings are said as Fatture in Cloud says them."""
	from crm.invoicing import documento

	if not doc.fic_document_id:
		frappe.throw(_("This invoice was not made in Fatture in Cloud: it cannot leave from there."))
	percorso = f"/c/{{c}}/issued_documents/{doc.fic_document_id}/e_invoice"
	try:
		collegamento.chiama_per(doc.company, "GET", f"{percorso}/xml_verify")
	except ErroreFiC as errore:
		if errore.incerto or (errore.stato or 0) >= 500 or errore.stato == 429:
			_ferma([str(errore)], _("Transmission"))
		righe = errore.rilievi or [str(errore)]
		documento.registra(doc, "sdi_blocked", "\n".join(righe), stato="fatture_in_cloud")
		if not frappe.flags.in_test:
			frappe.db.commit()  # nosemgrep: frappe-manual-commit — what was found stays in the log
		_ferma(
			[_("Fatture in Cloud found something to correct before sending it:"), *righe],
			_("Not transmissible"),
		)
	corpo = {"data": {}}
	if doc.fund_type:
		corpo["data"]["cassa_type"] = doc.fund_type
	if cint(doc.apply_withholding) and doc.payment_reason:
		corpo["data"]["withholding_tax_causal"] = doc.payment_reason
	try:
		risposta = (collegamento.chiama_per(doc.company, "POST", f"{percorso}/send", json=corpo) or {}).get(
			"data"
		) or {}
	except ErroreFiC as errore:
		documento.registra(doc, "sdi_sent", str(errore), stato="incerto" if errore.incerto else "errore")
		if not frappe.flags.in_test:
			frappe.db.commit()  # nosemgrep: frappe-manual-commit — the attempt stays in the log
		_ferma([str(errore), *errore.rilievi], _("Transmission"))
	messaggio = _("Sent to the SdI from Fatture in Cloud")
	doc.db_set(
		{
			"sdi_status": "inviato",
			"sdi_sent_on": now_datetime(),
			"sdi_message": None,
			"sdi_environment": "fatture_in_cloud",
		},
		update_modified=False,
	)
	documento.registra(
		doc, "sdi_sent", messaggio, stato="fatture_in_cloud", payload={"answer": risposta.get("name")}
	)
	_conserva_xml(doc)
	return {"mode": "fatture_in_cloud", "sent": True, "message": messaggio}


def _conserva_xml(doc) -> None:
	"""The e-invoice as Fatture in Cloud made it, kept on the invoice. It never
	raises: Fatture in Cloud keeps it too, and it is asked again at the next round."""
	try:
		xml = collegamento.chiama_per(
			doc.company, "GET", f"/c/{{c}}/issued_documents/{doc.fic_document_id}/e_invoice/xml", testo=True
		)
	except ErroreFiC:
		return
	if not xml or "<" not in xml:
		return
	import hashlib

	nome = f"{(doc.document_number or doc.name).replace('/', '-')}.xml"
	allegato = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": nome,
			"attached_to_doctype": FATTURA,
			"attached_to_name": doc.name,
			"attached_to_field": "sdi_sent_file",
			"is_private": 1,
			"content": xml,
		}
	).insert(ignore_permissions=True)
	doc.db_set(
		{
			"sdi_sent_file": allegato.file_url,
			"xml_file": doc.xml_file or allegato.file_url,
			"xml_hash": hashlib.sha256(xml.encode()).hexdigest(),
		},
		update_modified=False,
	)


def _avvisa(doc, ei_status: str, motivo: str) -> None:
	from crm.invoicing.monitoraggio import avvisa

	if ei_status == "not_delivered":
		avvisa(
			_("Invoice {0} is issued but not delivered").format(doc.document_number),
			doc.company,
			_(
				"The Sistema di Interscambio has it and filed it in the client's reserved area. "
				"The client has to be told: send them the PDF."
			),
		)
	elif ei_status == "discarded":
		avvisa(
			_("Invoice {0} was rejected").format(doc.document_number),
			doc.company,
			_(
				"It counts as not issued, and the five days to correct and resend run from the notice. {0}"
			).format(motivo),
		)
	elif regole.da_correggere(ei_status):
		avvisa(
			_("The public body refused invoice {0}").format(doc.document_number),
			doc.company,
			motivo or _("Correct it with a credit note and issue it again."),
		)


def aggiorna(doc) -> str | None:
	"""Ask Fatture in Cloud how one invoice is doing on its way, and keep it."""
	from crm.invoicing import documento

	risposta = (
		collegamento.chiama_per(
			doc.company,
			"GET",
			f"/c/{{c}}/issued_documents/{doc.fic_document_id}",
			params={"fields": "id,ei_status"},
		)
		or {}
	).get("data") or {}
	ei_status = risposta.get("ei_status")
	stato = regole.stato_sdi(ei_status)
	if not stato or stato == doc.sdi_status:
		return None
	motivo = ""
	if regole.da_correggere(ei_status):
		try:
			ragione = (
				collegamento.chiama_per(
					doc.company,
					"GET",
					f"/c/{{c}}/issued_documents/{doc.fic_document_id}/e_invoice/error_reason",
				)
				or {}
			).get("data") or {}
			motivo = " ".join(parte for parte in (ragione.get("reason"), ragione.get("solution")) if parte)
		except ErroreFiC:
			motivo = ""
	doc.db_set({"sdi_status": stato, "sdi_message": motivo or None}, update_modified=False)
	documento.registra(doc, "sdi_receipt", motivo or ei_status, stato=stato, payload={"ei_status": ei_status})
	_avvisa(doc, ei_status, motivo)
	if not doc.sdi_sent_file:
		_conserva_xml(doc)
	return stato


def riconcilia() -> dict:
	"""Every ten minutes: the invoices on their way through Fatture in Cloud, asked
	how they are - only when something waits, and each company on its own."""
	esito = {"asked": 0, "moved": 0}
	for company in frappe.get_all(
		collegamento.DOCTYPE, filters={"fic_company_id": ["is", "set"]}, pluck="name"
	):
		if not collegamento.collegata(company):
			continue
		nomi = frappe.get_all(
			FATTURA,
			filters={
				"company": company,
				"docstatus": 1,
				"fic_document_id": ["is", "set"],
				"sdi_status": ["in", ("inviato", "consegnata")],
			},
			pluck="name",
			order_by="sdi_sent_on asc",
			limit=PER_GIRO,
		)
		for nome in nomi:
			doc = frappe.get_doc(FATTURA, nome)
			# delivered to a company: nothing more comes; to a public body, its answer
			if doc.sdi_status == "consegnata" and doc.recipient_type != "pubblica_amministrazione":
				continue
			esito["asked"] += 1
			try:
				if aggiorna(doc):
					esito["moved"] += 1
				_conferma()
			except ErroreFiC as errore:
				_annulla()
				if errore.stato == 401 or errore.stato == 429:
					break
			except Exception:
				_annulla()
				frappe.log_error(title=f"Fatture in Cloud: state of {nome}", message=frappe.get_traceback())
	return esito


def _conferma() -> None:
	"""Each invoice of a round on its own: a later one that fails undoes only itself."""
	if not frappe.flags.in_test:
		frappe.db.commit()  # nosemgrep: frappe-manual-commit — each invoice of the round on its own


def _annulla() -> None:
	if not frappe.flags.in_test:
		frappe.db.rollback()


# ---------------------------------------------------------------- after issue


def segna_incasso(doc) -> None:
	"""A collection marked here, marked there: the payment paid on its day, on the
	account of its method; back to collect, not paid. It never raises: the invoice
	here is right, and Fatture in Cloud is told again at the next change."""
	if not doc.fic_document_id or not collegamento.collegata(doc.company):
		return
	connessione = collegamento.connessione(doc.company)
	conto = collegamento.mappa(connessione)["conti"].get(doc.payment_method)
	pagamento = {
		"amount": float(regole.decimale(doc.net_payable)),
		"due_date": str(getdate(doc.payment_date or doc.posting_date)),
		"status": "not_paid",
	}
	if doc.collected_on and conto is not None:
		pagamento.update(
			{
				"status": "paid",
				"paid_date": str(getdate(doc.collected_on)),
				"payment_account": {"id": int(conto)},
			}
		)
	try:
		collegamento.chiama_per(
			doc.company,
			"PUT",
			f"/c/{{c}}/issued_documents/{doc.fic_document_id}",
			json={"data": {"payments_list": [pagamento]}},
		)
	except ErroreFiC as errore:
		frappe.log_error(title=f"Fatture in Cloud: payment of {doc.name}", message=str(errore))


def annulla(doc) -> None:
	"""An invoice cancelled here before it left goes from Fatture in Cloud too. With
	the access lost it is cancelled here all the same, and the invoice says so."""
	if not doc.fic_document_id:
		return
	if not collegamento.collegata(doc.company):
		avviso = _(
			"Fatture in Cloud is not connected: invoice {0} stays there. Delete it in Fatture in Cloud too."
		).format(doc.document_number)
		doc.add_comment("Info", avviso)
		frappe.msgprint(avviso, title=_("Fatture in Cloud"), indicator="orange")
		return
	try:
		collegamento.chiama_per(doc.company, "DELETE", f"/c/{{c}}/issued_documents/{doc.fic_document_id}")
	except ErroreFiC as errore:
		frappe.throw(
			_(
				"Fatture in Cloud did not delete it: {0} Cancel it there, or correct it with a credit note."
			).format(str(errore)),
			title=_("Fatture in Cloud"),
		)
