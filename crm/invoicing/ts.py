# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The Sistema TS side: from invoices to the tracciato, and to the file.

One pipeline, three submission modes, and only the last ten centimetres change.
Everybody is born in `export`, because no onboarding should wait on somebody
else's paperwork, and `export` stays tested even when every company is on
automatic - it is the universal plan B of every other failure.

The rule that shapes this module: **a failure here never stops invoicing.** The
patient gets their invoice whether or not the Sistema TS is reachable, so nothing
in this file is called from the issue path.
"""

from __future__ import annotations

import hashlib
from decimal import Decimal

import frappe
from frappe import _
from frappe.utils import getdate

from crm.invoicing.engine.codici import OperazioneTS, SoggettoInviante
from crm.invoicing.engine.sistema_ts import (
	Cifratore,
	CifratoreFittizio,
	DocumentoSpesa,
	ErroreTS,
	IdSpesa,
	Proprietario,
	VoceSpesa,
	prepara_batch,
	scadenza_invio,
	valida_documento,
)

ZERO = Decimal("0.00")


def _dec(valore) -> Decimal:
	return Decimal(str(valore or 0))


def proprietario(emittente: dict) -> Proprietario:
	"""The owner section, shaped for the subject.

	Natural persons omit codiceRegione, codiceAsl and codiceSSA; facilities,
	pharmacies and opticians use the Codice Proprietario and `cfProprietario` is the
	owner's or legal representative's code.
	"""
	soggetto = emittente.get("sender_category") or SoggettoInviante.NON_SANITARIO
	titolare = Proprietario(
		cf_proprietario=(emittente.get("fiscal_code") or emittente.get("tax_id") or "").strip().upper(),
		soggetto=soggetto,
	)
	if not titolare.e_persona_fisica:
		titolare.codice_regione = emittente.get("region_code")
		titolare.codice_asl = emittente.get("asl_code")
		titolare.codice_ssa = emittente.get("ssa_code")
	return titolare


def documento_spesa(doc, emittente: dict) -> DocumentoSpesa:
	"""Build the tracciato document from an issued invoice.

	The codice fiscale travels in clear from here: the RSA encryption happens later,
	at send time, with the current certificate. A stored ciphertext becomes rubbish
	the first time the certificate is reissued.
	"""
	voci: list[VoceSpesa] = []
	for riga in doc.items:
		if not riga.ts_expense_type or _dec(riga.ts_amount) <= ZERO:
			continue
		voci.append(
			VoceSpesa(
				tipo_spesa=riga.ts_expense_type,
				importo=_dec(riga.ts_amount),
				flag_tipo_spesa=riga.ts_expense_flag or None,
				aliquota_iva=_dec(riga.vat_rate) if not riga.vat_nature else None,
				natura_iva=riga.vat_nature if not riga.vat_rate else None,
			)
		)

	return DocumentoSpesa(
		proprietario=proprietario(emittente),
		id_spesa=IdSpesa(
			p_iva=(emittente.get("tax_id") or "").strip(),
			data_emissione=getdate(doc.posting_date),
			num_documento=doc.document_number,
			# For invoices the cash-register progressive is always 1.
			dispositivo=1,
		),
		data_pagamento=getdate(doc.payment_date or doc.posting_date),
		voci=voci,
		cf_cittadino=None if doc.privacy_opposition else (doc.fiscal_code or None),
		flag_opposizione=bool(doc.privacy_opposition),
		flag_pagamento_anticipato=bool(doc.advance_payment),
		pagamento_tracciato=_tracciato(doc.payment_traced),
		flag_operazione=doc.ts_operation or OperazioneTS.INSERIMENTO,
	)


def _tracciato(valore: str | None) -> bool | None:
	if valore == "yes":
		return True
	if valore == "no":
		return False
	return None


def verifica(doc, emittente: dict):
	"""Validate an invoice against the tracciato, at issue time.

	Every rule caught here is a row that would otherwise be rejected in January,
	when fixing it costs a variation and a phone call.
	"""
	return valida_documento(documento_spesa(doc, emittente))


def contenuto_allegato(url: str) -> bytes:
	"""Raw bytes of an attachment.

	`File.get_content` tries a list of text encodings and hands back a string when
	one of them happens to work. A DER certificate is not text, and a certificate
	that silently became a string fails at encryption time with an error that points
	nowhere. An empty encoding list keeps it binary.
	"""
	allegato = frappe.get_doc("File", {"file_url": url})
	contenuto = allegato.get_content(encodings=[])
	if isinstance(contenuto, str):
		contenuto = contenuto.encode("latin-1", errors="ignore")
	return contenuto


def cifratore(emittente: dict) -> Cifratore:
	"""The encryptor for the company's certificate, or the stand-in.

	Without a certificate the file is still built - `export` mode has to work on day
	one - but it is built with a stand-in that writes `NONCIFRATO` into the field,
	so a file that is not ready to send can never be mistaken for one that is.
	"""
	allegato = emittente.get("ts_certificate")
	if not allegato:
		return CifratoreFittizio()
	try:
		contenuto = contenuto_allegato(allegato)
	except Exception:
		frappe.log_error(title="Sistema TS certificate", message=frappe.get_traceback())
		return CifratoreFittizio()
	return Cifratore.da_certificato(contenuto)


def _veterinario(emittente: dict) -> bool:
	return emittente.get("sender_category") == SoggettoInviante.VETERINARIO


def fatture_da_inviare(azienda: str, anno: int) -> list[str]:
	"""Issued invoices whose expense year is `anno` and that are still pending.

	The year of competence is the **payment** year, not the issue year: a package
	paid in December and invoiced in March belongs to December.
	"""
	return frappe.get_all(
		"CRM Invoice",
		filters={
			"company": azienda,
			"docstatus": 1,
			"ts_status": ["in", ("da_inviare", "pronto_export", "scartato")],
			"ts_year": anno,
		},
		order_by="posting_date asc, document_number asc",
		pluck="name",
	)


def prepara_invio(azienda: str, anno: int) -> dict:
	"""Build the zip (or zips) for a year and record them as submissions.

	It never raises on a single bad invoice: the ones that do not validate are
	listed and left behind, because holding the whole year hostage to one broken row
	is how a deadline is missed.
	"""
	if not frappe.db.exists("CRM Invoicing Company", azienda):
		frappe.throw(_("Unknown company {0}").format(azienda))
	emittente = frappe.get_cached_doc("CRM Invoicing Company", azienda).as_dict()
	if emittente.get("sender_category") in (None, "", SoggettoInviante.NON_SANITARIO):
		frappe.throw(_("{0} is not a Sistema TS subject: there is nothing to report").format(azienda))

	nomi = fatture_da_inviare(azienda, anno)
	documenti: list[DocumentoSpesa] = []
	scartate: list[dict] = []
	for nome in nomi:
		fattura = frappe.get_doc("CRM Invoice", nome)
		spesa = documento_spesa(fattura, emittente)
		esito = valida_documento(spesa)
		if esito.valido:
			documenti.append(spesa)
		else:
			scartate.append({"invoice": nome, "number": fattura.document_number, "errors": esito.errori})

	if not documenti:
		return {"parts": [], "skipped": scartate, "count": 0}

	parti = prepara_batch(documenti, cifratore(emittente), azienda, anno)
	scadenza = scadenza_invio(anno, _veterinario(emittente))
	invii: list[str] = []

	for parte in parti:
		invio = frappe.get_doc(
			{
				"doctype": "CRM TS Submission",
				"company": azienda,
				"fiscal_year": anno,
				"mode": emittente.get("ts_mode") or "export",
				"operation": OperazioneTS.INSERIMENTO,
				"status": "pronto",
				"part": parte.parte,
				"total_parts": parte.parti_totali,
				"deadline": scadenza,
				"document_count": len(parte.documenti),
				"total_amount": float(sum((d.totale for d in parte.documenti), ZERO)),
				"file_name": parte.nome_file,
				"file_hash": hashlib.sha256(parte.zip_bytes).hexdigest(),
			}
		)
		invio.insert(ignore_permissions=True)
		allegato = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": parte.nome_file,
				"attached_to_doctype": "CRM TS Submission",
				"attached_to_name": invio.name,
				"attached_to_field": "file",
				"is_private": 1,
				"content": parte.zip_bytes,
			}
		).insert(ignore_permissions=True)
		invio.db_set("file", allegato.file_url)
		invii.append(invio.name)

		chiavi = {d.id_spesa.num_documento for d in parte.documenti}
		for nome in nomi:
			numero = frappe.db.get_value("CRM Invoice", nome, "document_number")
			if numero in chiavi:
				frappe.db.set_value(
					"CRM Invoice",
					nome,
					{"ts_status": "pronto_export", "ts_submission": invio.name},
					update_modified=False,
				)

	return {"parts": invii, "skipped": scartate, "count": len(documenti), "deadline": str(scadenza)}


def segna_esito(invio: str, codice: str, messaggio: str = "", protocollo: str = "") -> None:
	"""Record the outcome of a submission and move the invoices with it.

	Rejections 105 and 106 are not failures to retry: they are the answer to a
	question nobody could answer honestly. The company drops back to `export` and
	the mandate status is recorded, because invoicing must not stop for a broken
	last mile.
	"""
	from crm.invoicing.engine.codici import (
		CODICE_DELEGA_ASSENTE,
		CODICE_DELEGA_PRESENTE,
		descrivi_esito,
	)

	documento = frappe.get_doc("CRM TS Submission", invio)
	accolto = codice in ("000", "0", "")
	documento.status = "accolto" if accolto else "scartato"
	documento.response_code = codice
	documento.response_message = messaggio or descrivi_esito(codice)
	documento.protocol = protocollo
	documento.sent_on = frappe.utils.now_datetime()
	documento.save(ignore_permissions=True)

	frappe.db.set_value(
		"CRM Invoice",
		{"ts_submission": invio},
		"ts_status",
		"accolto" if accolto else "scartato",
		update_modified=False,
	)

	if codice in (CODICE_DELEGA_ASSENTE, CODICE_DELEGA_PRESENTE):
		frappe.db.set_value(
			"CRM Invoicing Company",
			documento.company,
			{
				"ts_delegation_status": "assente" if codice == CODICE_DELEGA_ASSENTE else "presente",
				"ts_mode": "export",
			},
		)


def stato(azienda: str, anno: int) -> dict:
	"""What is still outstanding for a year, and how long there is left.

	The dangerous failure in this domain produces no error - it produces absence,
	and absence is only noticed in January.
	"""
	emittente = (
		frappe.db.get_value("CRM Invoicing Company", azienda, ["sender_category", "ts_mode"], as_dict=True)
		or {}
	)
	scadenza = scadenza_invio(anno, emittente.get("sender_category") == SoggettoInviante.VETERINARIO)
	conteggi = {}
	for chiave in ("da_inviare", "pronto_export", "inviato", "accolto", "scartato"):
		conteggi[chiave] = frappe.db.count(
			"CRM Invoice", {"company": azienda, "ts_year": anno, "ts_status": chiave, "docstatus": 1}
		)
	ultimo = frappe.db.get_value(
		"CRM TS Submission",
		{"company": azienda, "status": "accolto"},
		"sent_on",
		order_by="sent_on desc",
	)
	return {
		"year": anno,
		"deadline": str(scadenza),
		"days_left": (scadenza - frappe.utils.getdate()).days,
		"mode": emittente.get("ts_mode") or "export",
		"counts": conteggi,
		"last_accepted": str(ultimo) if ultimo else None,
	}


__all__ = ["ErroreTS", "documento_spesa", "prepara_invio", "segna_esito", "stato", "verifica"]
