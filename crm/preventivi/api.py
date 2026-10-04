# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Quotes on the person's page (docs/gestionale-medico/design.md, "Tre strati": "Il
preventivo"); the rules without a site are `regole`.

- **A draft is its author's**: services from the price list, each with its
  quantity, price and discount, in phases; whoever writes quotes
  (`preventivi.scrivi`) writes one. Made from the page of a deal of the quotes
  pipeline, it is that deal's: the deal's page lists its quotes.
- **Proposed**, it is frozen: its PDF is made to hand over, and the person's deal in
  the quotes pipeline goes to "quote delivered". It is read by whoever reads the
  person's quotes (`preventivi.vedi`) and sees the person; the author or who
  handles quotes (`preventivi.gestisci`, the desk) records it accepted - how, in a
  few words - or declined, and why: the deal is won or lost.
- **Accepted**, it is done service by service (`crm.preventivi.appuntamenti`); every
  one done or cancelled, it is completed. Stopped half-way, it is closed. A new
  version starts from it as a draft.
- **Health data**: with the clinic on, what a health professional writes carries
  the mark (`clinical`) - a dentist's care plan. It is read like the clinical record
  by the rule the clinic registers (`crm.permissions.sanitari`), and by who handles
  quotes once proposed; every opening goes in the access log.
- **What a module adds** (`registra_estensione`): the fields of its rows and how
  they read - the clinic's tooth and surfaces - and what it checks.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, get_fullname, getdate, now_datetime

from crm.permissions import livelli, org_hierarchy, sanitari
from crm.preventivi import regole as R

DOCTYPE = "CRM Quote"
VOCE = "CRM Quote Item"
IMPOSTAZIONI = "CRM Quote Settings"
#: What a row keeps from the editor; the rest is the quote's to decide.
CAMPI_VOCE = ("service", "description", "phase", "qty", "rate", "discount")


# ------------------------------------------------------------------ what a module adds


@dataclass(frozen=True)
class Estensione:
	"""What a module adds to the quotes: the fields of its rows, and its checks."""

	#: The fields of a row it keeps from the editor.
	campi_voce: tuple[str, ...] = ()
	#: A row put right before it is kept: (quote, row).
	pulisci_voce: Callable[[object, object], None] | None = None
	#: What a row adds for the page and the area.
	legge_voce: Callable[[object], dict] | None = None
	#: A row in words besides its service, for the PDF: "Tooth 36 · OM".
	dettaglio: Callable[[object], str | None] | None = None
	#: What is wrong with the rows the session writes, on top of the CRM's checks.
	valida: Callable[[list[dict]], list[R.Problema]] | None = None
	#: What the editor offers the session: {"teeth": True}.
	offre: Callable[[], dict] | None = None
	#: What a quote adds for the page: the clinic's "obscured".
	legge: Callable[[object], dict] | None = None


_estensioni: list[Estensione] = []


def registra_estensione(estensione: Estensione) -> None:
	if estensione not in _estensioni:
		_estensioni.append(estensione)


def campi_voce() -> tuple[str, ...]:
	return CAMPI_VOCE + tuple(campo for e in _estensioni for campo in e.campi_voce)


# ------------------------------------------------------------------ who


def scrive(user: str | None = None) -> bool:
	return livelli.puo("preventivi.scrivi", user or frappe.session.user)


def gestisce(user: str | None = None) -> bool:
	return livelli.puo("preventivi.gestisci", user or frappe.session.user)


def _sql(condizione) -> str:
	return condizione.get_sql(with_namespace=True, quote_char="`", secondary_quote_char="'")


def _vede_la_persona(doc, user: str) -> bool:
	return bool(frappe.has_permission("CRM Lead", "read", doc=doc.get("lead"), user=user))


def puo_leggere(doc, user: str | None = None) -> bool:
	"""Its author, always. Proposed: who handles quotes, for the people they see; the
	others who read the person's quotes - with health data, by the clinic's rule."""
	user = user or frappe.session.user
	if doc.get("practitioner") == user:
		return True
	if doc.get("status") == R.BOZZA:
		return False
	vede = _vede_la_persona(doc, user)
	if gestisce(user) and vede:
		return True
	if cint(doc.get("clinical")):
		return sanitari.legge(doc, user)
	return livelli.puo("preventivi.vedi", user) and vede


def has_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	user = user or frappe.session.user
	ptype = ptype or "read"
	if ptype == "create":
		return scrive(user)
	if ptype in ("write", "delete"):
		# a draft is its author's; what is proposed goes on through its own calls
		return doc.get("practitioner") == user and doc.get("status") == R.BOZZA
	if ptype in ("submit", "cancel", "amend"):
		return False
	return puo_leggere(doc, user)


def condizione(tabella, user: str):
	"""Who reads a quote, as a condition on its table: the same rule."""
	condizione = tabella.practitioner == user
	proposti = tabella.status != R.BOZZA
	visibili = org_hierarchy.visible_leads(user)
	persone = tabella.lead.isin(visibili) if visibili is not None else tabella.lead.isnotnull()
	if gestisce(user):
		condizione = condizione | (proposti & persone)
	elif livelli.puo("preventivi.vedi", user):
		condizione = condizione | (proposti & (tabella.clinical == 0) & persone)
	clinici = sanitari.condizione(tabella, user)
	if clinici is not None:
		condizione = condizione | (proposti & (tabella.clinical == 1) & clinici)
	return condizione


def get_permission_query_conditions(user: str | None = None) -> str:
	user = user or frappe.session.user
	return _sql(condizione(frappe.qb.DocType(DOCTYPE), user))


def _della_persona(lead: str) -> None:
	if not (livelli.puo("preventivi.vedi") or scrive() or gestisce()):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)


def _preventivo(name: str):
	doc = frappe.get_doc(DOCTYPE, name)
	frappe.has_permission("CRM Lead", "read", doc=doc.lead, throw=True)
	if not puo_leggere(doc):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return doc


def _mio(name: str, stato: str | None = None):
	doc = _preventivo(name)
	if doc.practitioner != frappe.session.user:
		frappe.throw(_("A quote is changed by whoever wrote it"), frappe.PermissionError)
	if stato and doc.status != stato:
		frappe.throw(_("This quote is {0}: it does not go that way").format(_(doc.status)))
	return doc


def _problemi(problemi: list) -> None:
	if problemi:
		frappe.throw("<br>".join(p.testo(_) for p in problemi))


def valida(voci: list[dict]) -> None:
	"""The CRM's checks on the rows, and every module's."""
	problemi = R.valida(voci)
	for estensione in _estensioni:
		if estensione.valida and voci:
			problemi += estensione.valida(voci)
	_problemi(problemi)


def qualifica_di(user: str) -> str | None:
	return frappe.db.get_value("CRM Service Provider", {"user": user, "enabled": 1}, "qualification")


def marca(doc) -> None:
	"""The mark "health data": what a health professional writes, with the clinic on."""
	doc.clinical = 1 if sanitari.per_chi_scrive(doc) else 0


def aperto(doc) -> None:
	"""A quote with health data read: in the access log, with the record's."""
	if cint(doc.get("clinical")):
		doc.add_viewed()


# ------------------------------------------------------------------ the sums


def nome_del_servizio(servizio: str | None) -> str | None:
	if not servizio:
		return None
	return frappe.db.get_value("CRM Service", servizio, "service_name") or servizio


def calcola(doc) -> None:
	"""`validate` of a quote: each row's amount, and the quote's sums."""
	if not doc.currency:
		doc.currency = (
			frappe.db.get_value("CRM Price List", doc.price_list, "currency") if doc.price_list else None
		) or "EUR"
	for voce in doc.items:
		voce.phase = max(cint(voce.phase), 1)
		voce.qty = flt(voce.qty) or 1
		voce.discount = min(max(flt(voce.discount), 0), 100)
		voce.amount = R.importo(voce.qty, voce.rate, voce.discount)
		voce.currency = doc.currency
		voce.status = voce.status or R.DA_FARE
		voce.description = (voce.description or "").strip() or nome_del_servizio(voce.service)
		for estensione in _estensioni:
			if estensione.pulisci_voce:
				estensione.pulisci_voce(doc, voce)
	somme = R.totali([voce.as_dict() for voce in doc.items])
	doc.total_gross = somme["gross"]
	doc.total_discount = somme["discount"]
	doc.total_net = somme["net"]
	doc.total_done = somme["done"]


# ------------------------------------------------------------------ reading


def dettaglio_della_voce(voce) -> str | None:
	parole = [testo for e in _estensioni if e.dettaglio and (testo := e.dettaglio(voce))]
	return " · ".join(parole) or None


def leggi_voce(voce) -> dict:
	riga = {
		"name": voce.name,
		"service": voce.service,
		"description": voce.description,
		"phase": cint(voce.phase) or 1,
		"qty": flt(voce.qty),
		"rate": flt(voce.rate),
		"discount": flt(voce.discount),
		"amount": flt(voce.amount),
		"status": voce.status or R.DA_FARE,
		"appointment": voce.appointment,
		"done_on": str(voce.done_on) if voce.done_on else None,
		"done_by_name": get_fullname(voce.done_by) if voce.done_by else None,
		"detail": dettaglio_della_voce(voce),
	}
	for estensione in _estensioni:
		if estensione.legge_voce:
			riga.update(estensione.legge_voce(voce))
	return riga


def _riga(doc) -> dict:
	fatte = sum(1 for voce in doc.items if voce.status == R.FATTA)
	contano = sum(1 for voce in doc.items if voce.status != R.ANNULLATA)
	riga = {
		"name": doc.name,
		"title": doc.title,
		"status": doc.status,
		"practitioner": doc.practitioner,
		"practitioner_name": get_fullname(doc.practitioner),
		"proposed_on": str(doc.proposed_on) if doc.proposed_on else None,
		"accepted_on": str(doc.accepted_on) if doc.accepted_on else None,
		"total_net": flt(doc.total_net),
		"total_done": flt(doc.total_done),
		"currency": doc.currency,
		"services": contano,
		"done": fatte,
		"clinical": cint(doc.clinical),
		"mine": doc.practitioner == frappe.session.user,
	}
	for estensione in _estensioni:
		if estensione.legge:
			riga.update(estensione.legge(doc))
	return riga


def _dettaglio(doc) -> dict:
	mio = doc.practitioner == frappe.session.user
	decide = doc.status == R.PROPOSTO and (mio or gestisce())
	return {
		**_riga(doc),
		"lead": doc.lead,
		"lead_name": doc.lead_name,
		"price_list": doc.price_list,
		"valid_until": str(doc.valid_until) if doc.valid_until else None,
		"patient_notes": doc.patient_notes,
		"items": [leggi_voce(voce) for voce in doc.items],
		"totals": R.totali([voce.as_dict() for voce in doc.items]),
		"quote_pdf": doc.quote_pdf,
		"deal": doc.deal,
		"deal_label": _trattativa(doc.deal),
		"accepted_by_name": get_fullname(doc.accepted_by) if doc.accepted_by else None,
		"acceptance_note": doc.acceptance_note,
		"declined_on": str(doc.declined_on) if doc.declined_on else None,
		"decline_reason": doc.decline_reason,
		"closed_on": str(doc.closed_on) if doc.closed_on else None,
		"replaces": doc.replaces,
		"can_edit": mio and doc.status == R.BOZZA,
		"can_withdraw": mio and doc.status == R.PROPOSTO,
		"can_decide": decide,
		# the deal's lost reasons, for a quote declined
		"lost_reasons": frappe.get_all("CRM Lost Reason", pluck="name", order_by="name") if decide else [],
		"can_mark": doc.status in (R.ACCETTATO, R.COMPLETATO) and (mio or scrive()),
		"can_close": doc.status == R.ACCETTATO and (mio or gestisce()),
		"can_copy": scrive() and doc.status != R.BOZZA,
		"offers": offre(),
	}


def _trattativa(deal: str | None) -> str | None:
	"""A deal as the quote names it: its stage, in the reader's words."""
	if not deal:
		return None
	stadio = frappe.db.get_value("CRM Deal", deal, "status")
	return _(stadio) if stadio else None


def offre() -> dict:
	"""What the editor offers the session besides the CRM's rows: a module's fields."""
	fatto = {}
	for estensione in _estensioni:
		if estensione.offre:
			fatto.update(estensione.offre())
	return fatto


def _della_trattativa(lead: str, deal: str | None) -> str | None:
	"""The deal whose quotes these are: one of the person's, in the quotes pipeline.
	The page of a deal of another pipeline shows the person's quotes, and a quote
	made there finds its deal when it is proposed."""
	if not deal:
		return None
	if frappe.db.get_value("CRM Deal", deal, "lead") != lead:
		frappe.throw(_("This deal belongs to somebody else"), frappe.PermissionError)
	from crm.preventivi import pipeline

	return deal if pipeline.prende_preventivi(deal) else None


@frappe.whitelist()
def get_quotes(lead: str, deal: str | None = None) -> dict:
	"""The person's quotes the session reads, the most recent first; from the page of
	a deal of the quotes pipeline, the deal's."""
	_della_persona(lead)
	filtri = {"lead": lead}
	deal = _della_trattativa(lead, deal)
	if deal:
		filtri["deal"] = deal
	preventivi = [
		doc
		for doc in (
			frappe.get_doc(DOCTYPE, nome)
			for nome in frappe.get_all(DOCTYPE, filters=filtri, pluck="name", order_by="creation desc")
		)
		if puo_leggere(doc)
	]
	return {
		"quotes": [_riga(doc) for doc in preventivi],
		# the deal a new quote made here belongs to
		"deal": deal,
		"can_write": scrive(),
		"offers": offre(),
		"price_lists": frappe.get_all(
			"CRM Price List",
			filters={"enabled": 1},
			fields=["name", "price_list_name"],
			order_by="price_list_name",
		)
		if scrive()
		else [],
	}


@frappe.whitelist()
def get_quote(name: str) -> dict:
	doc = _preventivo(name)
	aperto(doc)
	return _dettaglio(doc)


@frappe.whitelist()
def price_of(service: str, price_list: str | None = None) -> dict:
	"""A service's price from the price list, to start from."""
	if not scrive():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	from crm.scheduling import pricing

	prezzo = pricing.resolve_price(service, now_datetime(), price_list=price_list or None)
	return {"rate": flt(prezzo.rate), "currency": prezzo.currency, "description": nome_del_servizio(service)}


# ------------------------------------------------------------------ writing


def _voci_dal_modulo(dati: dict) -> list[dict]:
	"""The rows as the editor sends them: one of each, unless it says how many; a
	row nobody wrote in is left out."""
	campi = campi_voce()
	voci = []
	for voce in dati.get("items") or []:
		riga = {campo: voce.get(campo) for campo in campi}
		if R.vuota(riga):
			continue
		if riga["qty"] in (None, ""):
			riga["qty"] = 1
		voci.append(riga)
	return voci


def giorni_di_validita() -> int:
	return cint(frappe.db.get_single_value(IMPOSTAZIONI, "valid_days")) or R.GIORNI_VALIDITA


def nuovo(lead: str):
	"""A new draft of the session's for ``lead``."""
	doc = frappe.new_doc(DOCTYPE)
	doc.lead = lead
	doc.practitioner = frappe.session.user
	doc.discipline = qualifica_di(frappe.session.user)
	doc.status = R.BOZZA
	return doc


@frappe.whitelist(methods=["POST"])
def save_quote(lead: str, data: str | dict, name: str | None = None, deal: str | None = None) -> dict:
	"""A draft, new or put right, by its author; made from a deal's page, it is that
	deal's quote."""
	_della_persona(lead)
	dati = frappe.parse_json(data) if isinstance(data, str) else (data or {})
	if name:
		doc = _mio(name, R.BOZZA)
		if doc.lead != lead:
			frappe.throw(_("This quote belongs to somebody else"))
	else:
		if not scrive():
			frappe.throw(_("Not permitted"), frappe.PermissionError)
		doc = nuovo(lead)
		doc.deal = _della_trattativa(lead, deal)
	voci = _voci_dal_modulo(dati)
	# a draft may be unfinished, never wrong
	if voci:
		valida(voci)
	doc.title = (dati.get("title") or "").strip() or _("Quote")
	doc.price_list = dati.get("price_list") or None
	doc.valid_until = dati.get("valid_until") or None
	doc.patient_notes = (dati.get("patient_notes") or "").strip() or None
	doc.set("items", [])
	for voce in voci:
		doc.append("items", {**voce, "status": R.DA_FARE})
	marca(doc)
	if doc.is_new():
		doc.insert()
	else:
		doc.save()
	return _dettaglio(doc)


@frappe.whitelist(methods=["POST"])
def delete_quote_draft(name: str) -> None:
	doc = _mio(name, R.BOZZA)
	frappe.delete_doc(DOCTYPE, doc.name)


def salva(doc) -> None:
	"""A quote moved on by its own calls: past the draft, the calls decide."""
	doc.flags.dal_preventivo = True
	doc.save(ignore_permissions=True)


@frappe.whitelist(methods=["POST"])
def propose_quote(name: str) -> dict:
	"""Handed to the person: frozen, its PDF made, the quotes deal moved."""
	doc = _mio(name, R.BOZZA)
	valida([voce.as_dict() for voce in doc.items])
	doc.status = R.PROPOSTO
	doc.proposed_on = now_datetime()
	doc.valid_until = doc.valid_until or add_days(getdate(), giorni_di_validita())
	salva(doc)
	from crm.preventivi import documento, pipeline

	documento.fai_il_pdf(doc)
	pipeline.segui(doc, consegnato=True)
	return _dettaglio(frappe.get_doc(DOCTYPE, doc.name))


@frappe.whitelist(methods=["POST"])
def withdraw_quote(name: str) -> dict:
	"""Back to a draft, to change it before the person says yes: the PDF handed over
	is no longer the quote's."""
	doc = _mio(name, R.PROPOSTO)
	vecchio = doc.quote_pdf
	doc.status = R.BOZZA
	doc.proposed_on = None
	doc.quote_pdf = None
	salva(doc)
	if vecchio:
		for file in frappe.get_all(
			"File", filters={"file_url": vecchio, "attached_to_name": doc.name}, pluck="name"
		):
			frappe.delete_doc("File", file, ignore_permissions=True)
	return _dettaglio(doc)


def _decide(name: str):
	doc = _preventivo(name)
	if doc.status != R.PROPOSTO:
		frappe.throw(_("Only a proposed quote is accepted or declined"))
	if doc.practitioner != frappe.session.user and not gestisce():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return doc


@frappe.whitelist(methods=["POST"])
def accept_quote(name: str, note: str | None = None) -> dict:
	"""The person said yes: how, in a few words. The appointments already booked for
	its services take them."""
	from crm.preventivi import appuntamenti, pipeline

	doc = _decide(name)
	doc.status = R.ACCETTATO
	doc.accepted_on = now_datetime()
	doc.accepted_by = frappe.session.user
	doc.acceptance_note = (note or "").strip() or None
	salva(doc)
	pipeline.segui(doc, accettato=True)
	appuntamenti.raccogli(doc.name)
	return _dettaglio(frappe.get_doc(DOCTYPE, doc.name))


@frappe.whitelist(methods=["POST"])
def decline_quote(name: str, reason: str | None = None, note: str | None = None) -> dict:
	"""The person said no, and maybe why: the reason is the deal's lost reason."""
	from crm.preventivi import pipeline

	doc = _decide(name)
	doc.status = R.RIFIUTATO
	doc.declined_on = now_datetime()
	doc.decline_reason = ", ".join(v for v in ((reason or "").strip(), (note or "").strip()) if v) or None
	salva(doc)
	pipeline.segui(doc, accettato=False, motivo=reason, note=note)
	return _dettaglio(doc)


@frappe.whitelist(methods=["POST"])
def mark_item(name: str, item: str, status: str) -> dict:
	"""A row done, back to do, or cancelled: the appointments do it by themselves,
	this is for what happened otherwise."""
	from crm.preventivi import appuntamenti

	doc = _preventivo(name)
	if doc.status not in (R.ACCETTATO, R.COMPLETATO):
		frappe.throw(_("Services are marked on an accepted quote"))
	if doc.practitioner != frappe.session.user and not scrive():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	if status not in (R.DA_FARE, R.FATTA, R.ANNULLATA):
		frappe.throw(_("Unknown status {0}").format(status))
	voce = next((riga for riga in doc.items if riga.name == item), None)
	if not voce:
		frappe.throw(_("This service is not in the quote"))
	if status == R.FATTA:
		voce.status, voce.done_on, voce.done_by = R.FATTA, getdate(), frappe.session.user
	elif status == R.DA_FARE:
		voce.status = R.PRENOTATA if voce.appointment else R.DA_FARE
		voce.done_on = voce.done_by = None
	else:
		voce.status, voce.appointment = R.ANNULLATA, None
		voce.done_on = voce.done_by = None
	salva(doc)
	appuntamenti.completa(doc.name)
	return _dettaglio(frappe.get_doc(DOCTYPE, doc.name))


@frappe.whitelist(methods=["POST"])
def close_quote(name: str) -> dict:
	"""Stopped half-way: by its author, or who handles quotes. What was done stays."""
	doc = _preventivo(name)
	if doc.status != R.ACCETTATO:
		frappe.throw(_("Only an accepted quote is closed"))
	if doc.practitioner != frappe.session.user and not gestisce():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	doc.status = R.CHIUSO
	doc.closed_on = now_datetime()
	salva(doc)
	return _dettaglio(doc)


@frappe.whitelist(methods=["POST"])
def copy_quote(name: str) -> dict:
	"""A new version: a draft of the session's with the same services."""
	fonte = _preventivo(name)
	if not scrive():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	doc = nuovo(fonte.lead)
	doc.title = fonte.title
	doc.price_list = fonte.price_list
	doc.patient_notes = fonte.patient_notes
	doc.replaces = fonte.name
	# the same deal while it is open: a closed one is never opened again by a quote
	from crm.preventivi import pipeline

	if pipeline.si_puo_spostare(fonte.deal):
		doc.deal = fonte.deal
	campi = campi_voce()
	for voce in fonte.items:
		if voce.status == R.ANNULLATA:
			continue
		doc.append("items", {campo: voce.get(campo) for campo in campi} | {"status": R.DA_FARE})
	marca(doc)
	doc.insert()
	return _dettaglio(doc)
