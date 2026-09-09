# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Build the FatturaPA document from a CRM Invoice.

The XML is generated in this system, not bought from a converter, so the invoice
can be produced, inspected and kept without a round trip to anybody's API. What a
provider still sells is the last mile - the accredited channel to the SdI - and
that is a swappable adapter, not the shape of the data.

Two arrangements worth knowing about, because they are what makes the totals
reconcile against checks 00422 and 00423:

* the **fund levy** does not sit on a line. It travels in `DatiCassaPrevidenziale`
  and the summary block counts it, so the lines and the summary only add up once
  the levy blocks are there;
* the **re-charged stamp duty** does get a line, because it is part of the
  compensation (Risposta AdE 428/2022) and follows the VAT regime of the service.
  Leaving it out of the lines is how the summary ends up two euros over.
"""

from __future__ import annotations

from decimal import Decimal

import frappe
from frappe.utils import getdate

from crm.invoicing.engine.codici import (
	CODICE_DESTINATARIO_ESTERO,
	LUNGHEZZA_CODICE_PA,
	CondizioniPagamento,
	TipoDestinatario,
)
from crm.invoicing.engine.fatturapa import (
	Anagrafica,
	Cedente,
	Cessionario,
	Contatti,
	DettaglioPagamento,
	DocumentoCollegato,
	FatturaElettronica,
	IscrizioneREA,
	Sede,
	casse_da_calcolo,
	codice_destinatario,
	linee_da_calcolo,
	progressivo_alfanumerico,
	riepiloghi_da_calcolo,
	ritenute_da_calcolo,
	valida,
)

ZERO = Decimal("0.00")


def _dec(valore) -> Decimal:
	return Decimal(str(valore or 0))


def _cedente(emittente: dict) -> Cedente:
	anagrafica = Anagrafica(
		denominazione=emittente.get("company_name") if not emittente.get("last_name") else None,
		nome=emittente.get("first_name"),
		cognome=emittente.get("last_name"),
		id_paese=emittente.get("country") or "IT",
		id_codice=emittente.get("tax_id"),
		codice_fiscale=emittente.get("fiscal_code"),
	)
	rea = None
	if emittente.get("rea_office") and emittente.get("rea_number"):
		rea = IscrizioneREA(
			ufficio=emittente["rea_office"],
			numero_rea=emittente["rea_number"],
			stato_liquidazione=emittente.get("liquidation_state") or "LN",
			capitale_sociale=_dec(emittente.get("share_capital")) or None,
			socio_unico=emittente.get("sole_shareholder") or None,
		)
	return Cedente(
		anagrafica=anagrafica,
		sede=Sede(
			indirizzo=emittente.get("address_line") or "",
			numero_civico=emittente.get("civic_number"),
			cap=emittente.get("postal_code") or "",
			comune=emittente.get("city") or "",
			provincia=emittente.get("province"),
			nazione=emittente.get("country") or "IT",
		),
		regime_fiscale=emittente.get("tax_regime") or "RF01",
		albo_professionale=emittente.get("professional_register"),
		provincia_albo=emittente.get("register_province"),
		numero_iscrizione_albo=emittente.get("register_number"),
		data_iscrizione_albo=getdate(emittente.get("register_date"))
		if emittente.get("register_date")
		else None,
		contatti=Contatti(telefono=emittente.get("phone"), email=emittente.get("email")),
		iscrizione_rea=rea,
	)


def _cessionario(doc) -> Cessionario:
	persona = doc.recipient_type == TipoDestinatario.PERSONA_FISICA
	anagrafica = Anagrafica(
		denominazione=None if (persona and doc.last_name) else doc.billing_name,
		nome=doc.first_name if persona else None,
		cognome=doc.last_name if persona else None,
		id_paese=(doc.country or "IT").upper() if doc.tax_id else None,
		id_codice=(doc.tax_id or "").replace(" ", "") or None,
		codice_fiscale=doc.fiscal_code,
	)
	if anagrafica.id_codice and anagrafica.id_codice[:2].isalpha():
		# The client typed the number with its country prefix. FatturaPA wants the
		# two apart, and a prefix left inside IdCodice comes back as a rejection.
		anagrafica.id_paese = anagrafica.id_codice[:2].upper()
		anagrafica.id_codice = anagrafica.id_codice[2:]
	return Cessionario(
		anagrafica=anagrafica,
		sede=Sede(
			indirizzo=doc.address_line or "",
			numero_civico=doc.civic_number,
			cap=doc.postal_code or "",
			comune=doc.city or "",
			provincia=doc.province,
			nazione=(doc.country or "IT").upper(),
		),
	)


def _dettagli(doc) -> list[dict]:
	"""What the arithmetic does not know: description, quantity, unit, period."""
	return [
		{
			"descrizione": riga.description,
			"quantita": riga.qty or 1,
			"prezzo_unitario": _dec(riga.rate),
			"unita_misura": riga.uom or None,
			"ritenuta": bool(doc.apply_withholding),
			"data_inizio_periodo": getdate(riga.period_from) if riga.period_from else None,
			"data_fine_periodo": getdate(riga.period_to) if riga.period_to else None,
		}
		for riga in doc.items
	]


def _pagamenti(doc, conto, emittente: dict) -> list[DettaglioPagamento]:
	if doc.payments:
		return [
			DettaglioPagamento(
				modalita_pagamento=riga.payment_method,
				importo_pagamento=_dec(riga.amount),
				data_scadenza=getdate(riga.due_date) if riga.due_date else None,
				beneficiario=riga.beneficiary or None,
				istituto_finanziario=riga.bank_name or emittente.get("bank_name"),
				iban=riga.iban or emittente.get("iban"),
			)
			for riga in doc.payments
		]
	return [
		DettaglioPagamento(
			modalita_pagamento=doc.payment_method or "MP05",
			importo_pagamento=conto.netto_a_pagare,
			data_scadenza=getdate(doc.payment_date) if doc.payment_date else None,
			istituto_finanziario=emittente.get("bank_name"),
			iban=emittente.get("iban"),
		)
	]


def costruisci(doc, preparato: dict, progressivo: str | None = None) -> FatturaElettronica:
	"""Assemble the electronic invoice. Raises nothing - `valida` reports."""
	emittente = preparato["azienda"]
	conto = preparato["calcolo"]

	pa = doc.recipient_type == TipoDestinatario.PUBBLICA_AMMINISTRAZIONE
	estero = (doc.country or "IT").upper() != "IT"
	codice, pec = codice_destinatario(doc.recipient_code, doc.pec, estero=estero, pubblica_amministrazione=pa)

	progressivo = progressivo or progressivo_alfanumerico(int(emittente.get("sdi_last_progressive") or 0) + 1)

	collegati = []
	if doc.reference_invoice:
		numero, data = frappe.db.get_value(
			"CRM Invoice", doc.reference_invoice, ["document_number", "posting_date"]
		)
		collegati.append(DocumentoCollegato(numero or doc.reference_invoice, getdate(data)))

	ordini = []
	if doc.purchase_order or doc.cig or doc.cup:
		ordini.append(
			DocumentoCollegato(
				id_documento=doc.purchase_order or doc.document_number,
				codice_cig=doc.cig or None,
				codice_cup=doc.cup or None,
			)
		)

	return FatturaElettronica(
		cedente=_cedente(emittente),
		cessionario=_cessionario(doc),
		numero=doc.document_number,
		data=getdate(doc.posting_date),
		linee=linee_da_calcolo(conto, _dettagli(doc)),
		riepiloghi=riepiloghi_da_calcolo(conto),
		importo_totale=conto.totale,
		tipo_documento=doc.document_type or "TD01",
		codice_destinatario=codice,
		pec_destinatario=pec,
		progressivo_invio=progressivo,
		formato_trasmissione="FPA12" if len(codice) == LUNGHEZZA_CODICE_PA else None,
		contatti_trasmittente=Contatti(email=emittente.get("email"), telefono=emittente.get("phone")),
		dati_ritenuta=ritenute_da_calcolo(conto),
		bollo_virtuale=bool(conto.bollo_dovuto and doc.stamp_duty_mode == "virtuale"),
		importo_bollo=conto.bollo if conto.bollo_dovuto else None,
		dati_cassa=casse_da_calcolo(
			conto, bool(doc.apply_withholding) and bool(doc.fund_subject_to_withholding)
		),
		causale=[riga for riga in (doc.legal_notes or "").splitlines() if riga.strip()],
		documenti_collegati=collegati,
		ordini_acquisto=ordini,
		condizioni_pagamento=doc.payment_terms or CondizioniPagamento.COMPLETO,
		pagamenti=_pagamenti(doc, conto, emittente),
	)


def genera(doc, preparato: dict, progressivo: str | None = None) -> tuple[str, str, list[str]]:
	"""Return `(xml, file name, findings)` for an invoice.

	The findings are the SdI's own rejection codes, read before anybody sends the
	file: a rejection means the invoice counts as not issued, and the five days to
	resubmit run from the notice.
	"""
	fattura = costruisci(doc, preparato, progressivo)
	return fattura.xml(), fattura.nome_file(), valida(fattura)


def prossimo_progressivo(azienda: str) -> str:
	"""Bump and return the transmission progressive.

	The SdI refuses a file name it has already seen, and it does not forget, so the
	counter is bumped when the file is written and never reused.
	"""
	ultimo = frappe.db.get_value("CRM Invoicing Company", azienda, "sdi_last_progressive", for_update=True)
	nuovo = int(ultimo or 0) + 1
	frappe.db.set_value("CRM Invoicing Company", azienda, "sdi_last_progressive", nuovo)
	return progressivo_alfanumerico(nuovo)


__all__ = ["CODICE_DESTINATARIO_ESTERO", "costruisci", "genera", "prossimo_progressivo"]
