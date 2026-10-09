# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The invoices of what was paid online (doc 60): born the day the money arrives.

Stripe only collects; the invoice is DottorCloud's, through the same engine and the
same door as the desk's (`emissione`, `incassi.segna`), so it reaches the SdI by
the centre's own switch and the Sistema TS as any other. What was paid online is
made out:

- **a deposit at /prenota**: an advance invoice («Acconto per … del …») to the
  person for the amount paid, linked to its appointment by `advance_for` - never by
  `appointment`, which would close the appointment as attended. The desk's invoice
  of that appointment is then its balance, and says which advance it settles;
- **a subscription bought from the area, an instalment charged on the card**: the
  subscription's own instalment invoice (`crm.pagamenti.addebiti`).

Each is issued and collected with MP08 (card) by itself; one the engine would stop
(no codice fiscale, a line without its professional) stays a draft and whoever
manages invoicing is told why. A deposit given back is a credit note on its advance
invoice, issued the same way; an advance still a draft is thrown away. The rules
are `fatture_regole`.
"""

from __future__ import annotations

from contextlib import contextmanager

import frappe
from frappe import _
from frappe.utils import cint, flt, formatdate, getdate, strip_html

from crm.notifiche import regole as NR
from crm.pagamenti import fatture_regole as R

FATTURA = "CRM Invoice"
APPUNTAMENTO = "CRM Appointment"
CARTA = "MP08"
NOTE = ("TD04", "TD08")


@contextmanager
def come_dottorcloud():
	"""What follows writes as DottorCloud, in the centre's language: a job a guest's
	cancellation enqueued has no right to write invoices of its own, and an
	invoice's lines, a notice's reason, an email to the person are the centre's
	words whoever's request it is (Stripe's has none)."""
	from crm import lingue

	prima, lingua = frappe.session.user, getattr(frappe.local, "lang", None)
	if prima != "Administrator":
		frappe.set_user("Administrator")
	frappe.local.lang = lingue.del_centro()
	try:
		yield
	finally:
		frappe.local.lang = lingua
		if frappe.session.user != prima:
			frappe.set_user(prima)


def _giorno(valore) -> str:
	"""A day as a sentence says it, in the centre's language: «12 ottobre 2026»."""
	return formatdate(getdate(valore), "d MMMM yyyy")


# ------------------------------------------------------------------ issued as it was paid


def prepara(doc) -> None:
	"""A new draft as its first save will be: the company's choices, the client's
	details, the defaults - so the engine adds it up now."""
	if doc.is_new():
		doc.before_insert()
	doc.compila_da_controparte()
	doc.applica_predefiniti()


def problemi(doc) -> list[str]:
	"""What stops a draft from being issued, in words: a line not complete, then
	the engine's rules (`documento.da_correggere`)."""
	from crm.invoicing import documento, emissione

	mancano = emissione._da_completare(doc)
	if mancano:
		return mancano
	return documento.da_correggere(doc, documento.prepara(doc))[0]


def al_centesimo(doc, obiettivo) -> bool:
	"""The first line moved until the invoice adds up to ``obiettivo``, the money
	received: the fund and the VAT grow with it. False when it cannot be found."""
	from crm.invoicing import documento, incassi

	riga = doc.items[0]
	for _volta in range(6):
		documento.importo_riga(riga)
		documento.prepara(doc)
		totale = incassi.da_pagare(doc)
		if R.torna(obiettivo, totale):
			return True
		riga.rate = float(R.imponibile_per(obiettivo, riga.rate, totale))
	return False


def emetti_pagata(doc, pagamento, giorno=None) -> bool:
	"""A draft of what ``pagamento`` paid: by card (MP08), on the day it was paid,
	adding up to the money received; issued and collected, or kept as a draft with
	whoever manages invoicing told why. True when issued."""
	from crm.invoicing import incassi

	giorno = getdate(giorno or pagamento.paid_on)
	doc.payment_method = CARTA
	doc.payment_date = giorno
	prepara(doc)
	mancano = problemi(doc)
	if not mancano and not al_centesimo(doc, pagamento.amount):
		mancano = [
			_("It does not add up to the {0} paid: check its amount").format(
				frappe.utils.fmt_money(pagamento.amount, currency=pagamento.currency or "EUR")
			)
		]
	if doc.is_new():
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)
	if mancano:
		avvisa_bozza(doc, pagamento, mancano)
		return False
	frappe.db.savepoint("crm_pagata_online")
	try:
		doc.flags.ignore_permissions = True
		doc.submit()
	except Exception as errore:
		frappe.db.rollback(save_point="crm_pagata_online")
		frappe.clear_last_message()
		avvisa_bozza(doc, pagamento, [strip_html(str(errore))])
		return False
	if incassi.da_incassare(doc):
		incassi.segna(
			doc,
			giorno,
			_("Paid online by card on Stripe ({0})").format(pagamento.payment_intent or pagamento.name),
			payload={
				"payment_intent": pagamento.payment_intent,
				"payment_method": CARTA,
				"payment": pagamento.name,
			},
		)
	return True


def avvisa_bozza(doc, pagamento, mancano: list[str]) -> None:
	"""Whoever manages invoicing is told an invoice of a payment online stayed a
	draft, and why."""
	from crm.pagamenti import pagamenti

	pagamenti._di_a_chi_fattura(
		NR.PAGATA_ONLINE_IN_BOZZA,
		[pagamenti._nome(pagamento.party), "; ".join(m for m in mancano if m)[:300]],
		pagamento,
		oggetto=(FATTURA, doc.name),
	)


# ------------------------------------------------------------------ the deposit's advance invoice


def acconto_pagato(pagamento) -> str | None:
	"""The advance invoice of a deposit just paid at /prenota, issued and collected
	by itself; never twice. Never stops the booking: what goes wrong is logged and
	said."""
	if pagamento.invoice or cint(frappe.db.get_value(APPUNTAMENTO, pagamento.appointment, "docstatus")) == 2:
		return pagamento.invoice
	frappe.db.savepoint("crm_fattura_d_acconto")
	try:
		with come_dottorcloud():
			doc = _bozza_d_acconto(pagamento)
			if not doc:
				return None
			emetti_pagata(doc, pagamento)
			pagamento.db_set("invoice", doc.name)
			return doc.name
	except Exception as errore:
		frappe.db.rollback(save_point="crm_fattura_d_acconto")
		frappe.clear_last_message()
		frappe.log_error(
			title=f"Online payment {pagamento.name}: advance invoice", message=frappe.get_traceback()
		)
		from crm.pagamenti import pagamenti

		pagamenti._di_a_chi_fattura(
			NR.ACCONTO_SENZA_FATTURA,
			[pagamenti._nome(pagamento.party), strip_html(str(errore))[:300]],
			pagamento,
		)
		return None


def _bozza_d_acconto(pagamento):
	"""The advance invoice in memory: the appointment's own proposal (its fiscal
	card, its professional, who pays), for the person whose deposit it is, one line
	of what was paid."""
	from crm.invoicing import anagrafica, api

	appuntamento = frappe.get_doc(APPUNTAMENTO, pagamento.appointment)
	doc = api._fattura_da_appuntamento(appuntamento.name, saldo=False)
	riga = next((r for r in appuntamento.participants if r.access_token == pagamento.access_token), None)
	doc.appointment = None
	doc.advance_for = appuntamento.name
	doc.party_type, doc.party = "CRM Lead", pagamento.party
	doc.billing_name = None
	if not anagrafica.pagante_della_fattura(doc):
		doc.billing_name = (riga.participant_name if riga else None) or None
	servizio = (
		frappe.db.get_value("CRM Service", appuntamento.service, "service_name") or appuntamento.service or ""
	)
	from crm.lingue import con_l_apostrofo

	linea = doc.items[0]
	linea.description = con_l_apostrofo(
		_("Advance for {0} of {1}").format(servizio, _giorno(appuntamento.starts_on))
	)
	linea.rate = flt(pagamento.amount)
	return doc


def acconti(appuntamento: str, persona: str | None = None) -> list[dict]:
	"""The advance invoices of an appointment (issued, or drafts), each with its
	credit notes, for ``persona`` when given."""
	filtri = {"advance_for": appuntamento, "docstatus": ("<", 2), "document_type": ("not in", NOTE)}
	if persona:
		filtri.update({"party_type": "CRM Lead", "party": persona})
	fatte = frappe.get_all(
		FATTURA,
		filters=filtri,
		fields=[
			"name",
			"document_number",
			"posting_date",
			"net_total",
			"grand_total",
			"net_payable",
			"docstatus",
		],
		order_by="posting_date asc, creation asc",
	)
	if not fatte:
		return []
	note = frappe.get_all(
		FATTURA,
		filters={
			"reference_invoice": ("in", [f.name for f in fatte]),
			"docstatus": 1,
			"document_type": ("in", NOTE),
		},
		fields=["name", "reference_invoice", "net_total"],
	)
	for fattura in fatte:
		fattura["notes"] = [n for n in note if n.reference_invoice == fattura.name]
	return fatte


def _anticipato(fatte: list[dict]) -> float:
	righe = []
	for fattura in fatte:
		if fattura.docstatus != 1:
			continue
		righe.append({"net_total": fattura.net_total})
		righe.extend({"net_total": n.net_total, "nota": True} for n in fattura["notes"])
	return float(R.anticipato(righe))


def saldo(fattura, appuntamento) -> None:
	"""`_fattura_da_appuntamento`: the invoice the desk makes of an appointment paid
	in advance online is its balance - its price less the advances invoiced to the
	same person - and its causale says which advance it settles. Nothing is left:
	the appointment is invoiced already."""
	fatte = [f for f in acconti(appuntamento.name, fattura.party) if f.docstatus == 1]
	if not fatte:
		return
	riga = fattura.items[0]
	anticipato = _anticipato(fatte)
	numeri = ", ".join(f.document_number or f.name for f in fatte)
	if R.coperto(riga.rate, anticipato):
		frappe.throw(_("This appointment is invoiced already: advance invoice {0}").format(numeri))
	riga.rate = float(R.saldo(riga.rate, anticipato))
	from crm.lingue import con_l_apostrofo

	fattura.causale = "; ".join(
		[_("Balance")]
		+ [
			con_l_apostrofo(
				_("advance invoice no. {0} of {1}").format(
					f.document_number or f.name, _giorno(f.posting_date)
				)
			)
			for f in fatte
		]
	)


def coperti(incontri: list) -> set[str]:
	"""Of the appointments (with ``name`` and ``unit_price``), the ones whose advance
	invoices cover the whole price: nothing is left to invoice."""
	nomi = [i.name for i in incontri]
	if not nomi:
		return set()
	con = set(
		frappe.get_all(FATTURA, filters={"advance_for": ("in", nomi), "docstatus": 1}, pluck="advance_for")
	)
	fatto = set()
	for incontro in incontri:
		if incontro.name in con and R.coperto(incontro.unit_price, _anticipato(acconti(incontro.name))):
			fatto.add(incontro.name)
	return fatto


def per_la_fattura(appuntamento: str | None) -> list[dict]:
	"""The advance invoices the dialog names on an appointment's invoice."""
	if not appuntamento:
		return []
	return [
		{
			"name": f.name,
			"number": f.document_number or f.name,
			"date": str(f.posting_date) if f.posting_date else None,
			"amount": flt(f.net_payable) or flt(f.grand_total),
			"formatted_amount": frappe.utils.fmt_money(
				flt(f.net_payable) or flt(f.grand_total), currency="EUR"
			),
			"issued": f.docstatus == 1,
		}
		for f in acconti(appuntamento)
	]


# ------------------------------------------------------------------ a deposit given back


def acconto_rimborsato(pagamento) -> str | None:
	"""A deposit given back, all or part: a credit note on its advance invoice for
	that share, issued by itself; an advance still a draft is thrown away. Once for
	each amount given back."""
	if not pagamento.invoice or not frappe.db.exists(FATTURA, pagamento.invoice):
		return None
	frappe.db.savepoint("crm_nota_dell_acconto")
	try:
		with come_dottorcloud():
			return _storna(pagamento)
	except Exception as errore:
		frappe.db.rollback(save_point="crm_nota_dell_acconto")
		frappe.clear_last_message()
		frappe.log_error(
			title=f"Online payment {pagamento.name}: credit note", message=frappe.get_traceback()
		)
		from crm.pagamenti import pagamenti

		pagamenti._di_a_chi_fattura(
			NR.NOTA_DELL_ACCONTO_NON_FATTA,
			[pagamenti._nome(pagamento.party), strip_html(str(errore))[:300]],
			pagamento,
		)
		return None


def _storna(pagamento) -> str | None:
	from crm.invoicing import emissione

	acconto = frappe.get_doc(FATTURA, pagamento.invoice)
	cosa = R.al_rimborso(cint(acconto.docstatus))
	if cosa == R.TOGLI:
		if not acconto.document_number:
			frappe.delete_doc(FATTURA, acconto.name, ignore_permissions=True, force=True)
			pagamento.db_set("invoice", None)
		return None
	if cosa != R.NOTA:
		return None
	gia = frappe.get_all(
		FATTURA,
		filters={"reference_invoice": acconto.name, "docstatus": ("<", 2), "document_type": ("in", NOTE)},
		fields=["name", "net_total", "docstatus"],
	)
	quanto = R.da_stornare(
		pagamento.refunded_amount, pagamento.amount, acconto.net_total, sum(flt(n.net_total) for n in gia)
	)
	if quanto <= 0:
		return None
	nota = frappe.get_doc(FATTURA, emissione.credit_note(acconto.name)["name"])
	# one line, the share given back: the advance had one
	nota.set("items", nota.items[:1])
	nota.items[0].rate = float(quanto)
	nota.payment_method = CARTA
	nota.save(ignore_permissions=True)
	pagamento.db_set("credit_note", nota.name)
	mancano = problemi(nota)
	if mancano:
		avvisa_bozza(nota, pagamento, mancano)
		return nota.name
	frappe.db.savepoint("crm_nota_emessa")
	try:
		nota.flags.ignore_permissions = True
		nota.submit()
	except Exception as errore:
		frappe.db.rollback(save_point="crm_nota_emessa")
		frappe.clear_last_message()
		avvisa_bozza(nota, pagamento, [strip_html(str(errore))])
	return nota.name
