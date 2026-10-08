# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A quote paid in instalments, on the site (docs/crm/63); the rules without a site
are `rate_regole`.

- **Written with the draft**: «Payment» at once, or a deposit and 2 to 36
  instalments a month or two apart from a first day. The schedule is the quote's
  (`CRM Quote Instalment`), made again at every save of the draft; proposed, it is
  printed in the PDF and frozen with the rows, and signed with them.
- **Accepted**, the deposit falls due that day. How it is invoiced was copied from
  the settings when it was proposed (`instalments_invoiced`): DottorCloud makes an
  invoice for each row when it falls due (`ogni_giorno`, issued where the settings
  say so) - then the appointments of its services are paid by them and are not
  invoiced again (`pagati_a_rate`) -, or the centre invoices by itself and marks
  each one paid.
- **How each goes** follows its invoice (`allinea`): issued, collected, cancelled.
- **Closed, declined or replaced** by a new version accepted, the rows not invoiced
  yet are cancelled (`annulla`); **paid off early**, «Pay off the rest» makes one
  invoice of what is left (`salda`).
- **Never the demo's** by the daily round: the demo's part invoices its own.
"""

from __future__ import annotations

import datetime

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate

from crm.preventivi import rate_regole as R
from crm.preventivi import regole as RP

DOCTYPE = "CRM Quote"
RIGA = "CRM Quote Instalment"
FATTURA = "CRM Invoice"
IMPOSTAZIONI = "CRM Quote Settings"
#: The quotes whose instalments still go on: accepted, and done but not paid off.
IN_CORSO = (RP.ACCETTATO, RP.COMPLETATO)


# ------------------------------------------------------------------ the settings


def modo() -> str:
	"""How the centre invoices the instalments."""
	valore = frappe.db.get_single_value(IMPOSTAZIONI, "instalment_invoicing")
	return R.SOLO_SEGUITE if valore == R.SOLO_SEGUITE else R.OGNI_RATA


def si_emettono() -> bool:
	return bool(cint(frappe.db.get_single_value(IMPOSTAZIONI, "issue_instalment_invoices")))


# ------------------------------------------------------------------ the draft


def termini_da(doc, dati: dict) -> None:
	"""The terms of payment as the editor sends them."""
	doc.payment = R.A_RATE if dati.get("payment") == R.A_RATE else R.UNICA
	if doc.payment == R.UNICA:
		doc.deposit_type, doc.deposit_value, doc.instalments_count = R.IMPORTO, 0, 0
		doc.every_months, doc.first_due_on = 1, None
		return
	doc.deposit_type = R.PERCENTUALE if dati.get("deposit_type") == R.PERCENTUALE else R.IMPORTO
	doc.deposit_value = max(flt(dati.get("deposit_value")), 0)
	doc.instalments_count = cint(dati.get("instalments_count"))
	doc.every_months = 2 if cint(dati.get("every_months")) == 2 else 1
	doc.first_due_on = dati.get("first_due_on") or None


def problemi(doc, oggi: datetime.date | None = None) -> list[RP.Problema]:
	"""What is wrong with the terms; a draft may leave the first day for later."""
	if doc.payment != R.A_RATE:
		return []
	fatto = R.problemi(
		doc.total_net,
		doc.deposit_type,
		doc.deposit_value,
		doc.instalments_count,
		doc.every_months,
		getdate(doc.first_due_on) if doc.first_due_on else None,
		oggi,
	)
	if oggi is None:
		fatto = [p for p in fatto if p.messaggio != "Choose the day of the first instalment"]
	return fatto


def calcola(doc) -> None:
	"""`validate` of a draft, after its sums: the schedule from the terms. Past the
	draft it is frozen: only its rows' states move, by their own calls."""
	if doc.status != RP.BOZZA:
		return
	doc.set("instalments", [])
	if doc.payment != R.A_RATE or R.problemi(
		doc.total_net,
		doc.deposit_type,
		doc.deposit_value,
		doc.instalments_count,
		doc.every_months,
		getdate(doc.first_due_on) if doc.first_due_on else None,
	):
		return
	for riga in R.piano(
		doc.total_net,
		R.acconto(doc.total_net, doc.deposit_type, doc.deposit_value),
		cint(doc.instalments_count),
		cint(doc.every_months) or 1,
		getdate(doc.first_due_on),
	):
		doc.append("instalments", {**riga, "status": R.DA_PAGARE, "currency": doc.currency})


def copia(fonte, doc) -> None:
	"""A new version pays as the one it starts from."""
	for campo in (
		"payment",
		"deposit_type",
		"deposit_value",
		"instalments_count",
		"every_months",
		"first_due_on",
	):
		doc.set(campo, fonte.get(campo))


# ------------------------------------------------------------------ the quote moves on


def al_proposto(doc) -> None:
	"""Proposed: how its instalments will be invoiced, as the settings say now."""
	doc.instalments_invoiced = 1 if doc.payment == R.A_RATE and modo() == R.OGNI_RATA else 0


def all_accettazione(doc) -> None:
	"""Accepted: the deposit falls due that day."""
	for riga in doc.instalments:
		if riga.kind == R.ACCONTO and not riga.due_on:
			riga.due_on = getdate()


def annulla(doc) -> int:
	"""The rows not invoiced yet are cancelled: the quote closed, declined or
	replaced. How many."""
	righe = [doc.instalments[n] for n in R.da_annullare(_come_le_regole(doc))]
	for riga in righe:
		riga.db_set("status", R.ANNULLATA, update_modified=False)
	return len(righe)


def _come_le_regole(doc) -> list[dict]:
	return [
		{
			"kind": riga.kind,
			"due_on": getdate(riga.due_on) if riga.due_on else None,
			"amount": flt(riga.amount),
			"status": riga.status or R.DA_PAGARE,
		}
		for riga in doc.instalments
	]


# ------------------------------------------------------------------ the invoices


def _fatture(nomi: set[str]) -> dict[str, frappe._dict]:
	if not nomi:
		return {}
	return {
		riga.name: riga
		for riga in frappe.get_all(
			FATTURA,
			filters={"name": ["in", list(nomi)]},
			fields=["name", "docstatus", "collected_on", "document_number", "test_document"],
		)
	}


def _stato(riga, fattura) -> str:
	viva = bool(fattura) and cint(fattura.docstatus) in (0, 1)
	return R.stato(
		riga.status == R.ANNULLATA,
		viva,
		bool(viva and cint(fattura.docstatus) == 1 and fattura.collected_on),
		segnata=bool(riga.paid_on),
	)


def allinea(fattura, method=None) -> None:
	"""An invoice of instalments issued, collected, cancelled or deleted: its rows
	follow. A row whose invoice went is to pay again."""
	nome = fattura if isinstance(fattura, str) else fattura.name
	via = method in ("on_trash", "on_cancel")
	for riga in frappe.get_all(RIGA, filters={"parenttype": DOCTYPE, "invoice": nome}, fields=["name"]):
		doc = frappe.get_doc(RIGA, riga.name)
		if via:
			doc.db_set({"invoice": None, "status": R.DA_PAGARE}, update_modified=False)
			continue
		nuovo = _stato(doc, _fatture({nome}).get(nome))
		if nuovo != doc.status:
			doc.db_set("status", nuovo, update_modified=False)


def fattura(doc, righe: list, emetti: bool = False) -> str:
	"""One invoice for ``righe`` of the quote: a draft, issued when asked to and it
	can be - what stopped it is said on the rows. Returns the invoice."""
	from crm.invoicing import api as fatture

	nome = fatture.issue_from_quote(doc.name, [riga.name for riga in righe])
	for riga in righe:
		riga.db_set({"invoice": nome, "status": R.FATTURATA, "problem": None}, update_modified=False)
	if emetti:
		bozza = frappe.get_doc(FATTURA, nome)
		frappe.db.savepoint("crm_rata_del_preventivo_emessa")
		try:
			bozza.submit()
		except Exception as errore:
			frappe.db.rollback(save_point="crm_rata_del_preventivo_emessa")
			frappe.clear_last_message()
			for riga in righe:
				riga.db_set(
					"problem", _("Left as a draft: {0}").format(str(errore)[:400]), update_modified=False
				)
	return nome


def dovute(doc, oggi: datetime.date) -> list:
	return [doc.instalments[n] for n in R.dovute(_come_le_regole(doc), oggi)]


def fattura_le_dovute(doc, oggi: datetime.date | None = None) -> list[str]:
	"""Each row due today gets its invoice, one by one: one that cannot open leaves
	nothing behind and says why on its row."""
	fatte = []
	if not cint(doc.instalments_invoiced) or doc.status not in IN_CORSO:
		return fatte
	emetti = si_emettono()
	for riga in dovute(doc, getdate(oggi)):
		frappe.db.savepoint("crm_rata_del_preventivo")
		try:
			fatte.append(fattura(doc, [riga], emetti=emetti))
		except Exception as errore:
			frappe.db.rollback(save_point="crm_rata_del_preventivo")
			frappe.clear_last_message()
			riga.db_set("problem", str(errore)[:400], update_modified=False)
	return fatte


def ogni_giorno() -> None:
	"""Daily: the instalments due get their invoices. Never the demo's: its part
	invoices its own. One quote that fails leaves the others alone."""
	from crm.demo import registro

	oggi = getdate()
	della_demo = registro.nomi_di_prova(DOCTYPE)
	nomi = frappe.get_all(
		RIGA,
		filters={"parenttype": DOCTYPE, "status": R.DA_PAGARE, "due_on": ["<=", oggi]},
		pluck="parent",
		distinct=True,
	)
	for nome in nomi:
		if nome in della_demo:
			continue
		frappe.db.savepoint("crm_preventivo_del_giorno")
		try:
			fattura_le_dovute(frappe.get_doc(DOCTYPE, nome), oggi)
		except Exception:
			frappe.db.rollback(save_point="crm_preventivo_del_giorno")
			frappe.clear_last_message()
			frappe.log_error(
				title="Quote: the instalments of the day failed",
				reference_doctype=DOCTYPE,
				reference_name=nome,
			)


def pagati_a_rate(appuntamenti: list[str]) -> set[str]:
	"""Of ``appuntamenti``, the ones that took a row of a quote whose instalments
	DottorCloud invoices: the instalments pay for them."""
	if not appuntamenti:
		return set()
	Voce = frappe.qb.DocType("CRM Quote Item")
	Preventivo = frappe.qb.DocType(DOCTYPE)
	righe = (
		frappe.qb.from_(Voce)
		.join(Preventivo)
		.on(Preventivo.name == Voce.parent)
		.select(Voce.appointment)
		.where(Voce.parenttype == DOCTYPE)
		.where(Voce.appointment.isin(list(appuntamenti)))
		.where(Preventivo.instalments_invoiced == 1)
		.where(Preventivo.status.isin([RP.ACCETTATO, RP.COMPLETATO, RP.CHIUSO]))
	).run(as_dict=True)
	return {riga.appointment for riga in righe}


def descrizione(doc, righe: list) -> str:
	"""An invoice's line: the deposit, an instalment, or the rest."""
	quante = sum(1 for riga in doc.instalments if riga.kind == R.RATA and riga.status != R.ANNULLATA)
	if len(righe) > 1:
		return _("Balance of the quote «{0}»").format(doc.title)
	riga = righe[0]
	if riga.kind == R.ACCONTO:
		return _("Deposit on the quote «{0}»").format(doc.title)
	return _("Instalment {0} of {1} of the quote «{2}»").format(riga.number, quante, doc.title)


# ------------------------------------------------------------------ reading


def righe(doc, oggi: datetime.date | None = None) -> list[dict]:
	"""The schedule as the page and the area read it, each row as its invoice says."""
	oggi = getdate(oggi)
	fatture = _fatture({riga.invoice for riga in doc.instalments if riga.invoice})
	fatto = []
	for riga in doc.instalments:
		fatt = fatture.get(riga.invoice) if riga.invoice else None
		stato = _stato(riga, fatt)
		fatto.append(
			{
				"name": riga.name,
				"kind": riga.kind,
				"number": cint(riga.number),
				"due_on": str(riga.due_on) if riga.due_on else None,
				"amount": flt(riga.amount),
				"status": stato,
				"late": bool(
					riga.due_on and getdate(riga.due_on) < oggi and stato in (R.DA_PAGARE, R.FATTURATA)
				),
				"invoice": riga.invoice if fatt and cint(fatt.docstatus) in (0, 1) else None,
				"invoice_number": (fatt.document_number if fatt else None) or None,
				"invoice_draft": bool(fatt and cint(fatt.docstatus) == 0),
				"paid_on": str(riga.paid_on) if riga.paid_on else None,
				"problem": riga.problem,
			}
		)
	return fatto


def riassunto(doc, oggi: datetime.date | None = None, lette: list[dict] | None = None) -> dict | None:
	"""How the plan goes, for a line: paid of how many, the next one, the late ones."""
	# while it is only proposed nothing is due yet: the plan, not how it goes
	if doc.payment != R.A_RATE or not doc.instalments or doc.status not in (*IN_CORSO, RP.CHIUSO):
		return None
	lette = lette if lette is not None else righe(doc, oggi)
	fatto = R.riassunto(
		[{**riga, "due_on": getdate(riga["due_on"]) if riga["due_on"] else None} for riga in lette],
		getdate(oggi),
	)
	if not fatto:
		return None
	for chiave in ("next", "deposit"):
		if fatto[chiave]:
			fatto[chiave] = {
				"kind": fatto[chiave]["kind"],
				"due_on": str(fatto[chiave]["due_on"]) if fatto[chiave]["due_on"] else None,
				"amount": fatto[chiave]["amount"],
			}
	return fatto


def leggi(doc, puo_fatturare: bool = False, puo_incassare: bool = False) -> dict:
	"""The payment of a quote for its page: the terms, the schedule, how it goes and
	what the session may do with it."""
	termini = {
		"payment": doc.payment or R.UNICA,
		"deposit_type": doc.deposit_type or R.IMPORTO,
		"deposit_value": flt(doc.deposit_value),
		"instalments_count": cint(doc.instalments_count) or None,
		"every_months": cint(doc.every_months) or 1,
		"first_due_on": str(doc.first_due_on) if doc.first_due_on else None,
		"instalments_invoiced": cint(doc.instalments_invoiced),
	}
	if doc.payment != R.A_RATE:
		return {**termini, "instalments": [], "instalments_summary": None}
	lette = righe(doc)
	in_corso = doc.status in IN_CORSO
	aperte = [riga for riga in lette if riga["status"] == R.DA_PAGARE]
	da_fatturare = in_corso and cint(doc.instalments_invoiced) and puo_fatturare
	da_segnare = in_corso and not cint(doc.instalments_invoiced) and puo_incassare
	return {
		**termini,
		"instalments": lette,
		"instalments_summary": riassunto(doc, lette=lette),
		# a row invoiced now, by hand, before its day
		"can_invoice_instalment": bool(da_fatturare),
		# where the centre invoices by itself: marked paid, or back to pay
		"can_mark_instalment": bool(da_segnare),
		# paid off early: one invoice of the rest, or the rest marked paid
		"can_settle": bool((da_fatturare or da_segnare) and len(aperte) > 1),
		"rest": R.resto(_come_le_regole(doc)) if in_corso else 0,
	}


# ------------------------------------------------------------------ the desk's calls


def _chi_fattura(doc) -> None:
	from crm.preventivi import api

	if doc.practitioner != frappe.session.user and not api.gestisce():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	frappe.has_permission(FATTURA, "create", throw=True)


def _in_corso(name: str):
	from crm.preventivi import api

	doc = api._preventivo(name)
	if doc.payment != R.A_RATE or doc.status not in IN_CORSO:
		frappe.throw(_("This quote has no instalments going on"))
	return doc


@frappe.whitelist(methods=["POST"])
def invoice_instalment(name: str, row: str) -> dict:
	"""A row invoiced now, by hand, before its day: its draft opens."""
	from crm.preventivi import api

	doc = _in_corso(name)
	_chi_fattura(doc)
	if not cint(doc.instalments_invoiced):
		frappe.throw(_("The centre invoices this quote's instalments by itself"))
	riga = next((r for r in doc.instalments if r.name == row), None)
	if not riga or riga.status != R.DA_PAGARE:
		frappe.throw(_("This instalment is not to invoice"))
	nome = fattura(doc, [riga])
	return {"invoice": nome, **api._dettaglio(frappe.get_doc(DOCTYPE, doc.name))}


@frappe.whitelist(methods=["POST"])
def settle_quote(name: str) -> dict:
	"""Paid off early: one invoice of what is left - a draft that opens -, or, where
	the centre invoices by itself, the rest marked paid today."""
	from crm.permissions import livelli
	from crm.preventivi import api

	doc = _in_corso(name)
	aperte = [doc.instalments[n] for n in R.da_annullare(_come_le_regole(doc))]
	if not aperte:
		frappe.throw(_("Nothing is left to pay on this quote"))
	if cint(doc.instalments_invoiced):
		_chi_fattura(doc)
		nome = fattura(doc, aperte)
		return {"invoice": nome, **api._dettaglio(frappe.get_doc(DOCTYPE, doc.name))}
	livelli.verifica_nel_crm("fatture.incassi", messaggio=_("You are not allowed to record payments"))
	for riga in aperte:
		riga.db_set({"status": R.PAGATA, "paid_on": getdate()}, update_modified=False)
	return {"invoice": None, **api._dettaglio(frappe.get_doc(DOCTYPE, doc.name))}


@frappe.whitelist(methods=["POST"])
def mark_instalment(name: str, row: str, paid: int | str = 1) -> dict:
	"""Where the centre invoices by itself: a row paid today, or back to pay."""
	from crm.permissions import livelli
	from crm.preventivi import api

	livelli.verifica_nel_crm("fatture.incassi", messaggio=_("You are not allowed to record payments"))
	doc = _in_corso(name)
	if cint(doc.instalments_invoiced):
		frappe.throw(_("Its invoice says when it is paid"))
	riga = next((r for r in doc.instalments if r.name == row), None)
	if not riga or riga.status == R.ANNULLATA:
		frappe.throw(_("No such instalment"))
	if cint(paid):
		riga.db_set({"status": R.PAGATA, "paid_on": getdate()}, update_modified=False)
	else:
		riga.db_set({"status": R.DA_PAGARE, "paid_on": None}, update_modified=False)
	return api._dettaglio(frappe.get_doc(DOCTYPE, doc.name))
