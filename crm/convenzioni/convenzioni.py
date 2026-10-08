# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Conventions on a real site: the appointment, its pratica, the fund's invoice.

**The appointment** names who pays: the person, or a convention in direct or
indirect form (`convention`, `convention_form`). Its price is the convention's -
its price list's, or the centre's less its discount - and its two shares are
worked out in `validate` (`prezzo`, after the cycles and the subscriptions): in
direct form the person pays their share and the fund the rest; in indirect form
the person pays it all. The person's cover of that convention, valid that day, is
found by itself (`convention_cover`), and its card number goes with the pratica.

**A pratica** is an appointment in direct form: to authorise (the fund's yes is
asked first and nobody wrote its number), authorised, done, in the fund's draft,
billed, paid (`regole.stato`). The person's invoice is their share, the Sistema
TS hears of that only; the fund's is one a month, one line a pratica, to the
company that pays (`fattura_al_fondo`), made by the invoicing engine as any other.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, getdate

from crm.convenzioni import regole as R

CONVENZIONE = "CRM Convention"
COPERTURA = "CRM Convention Cover"
APPUNTAMENTO = "CRM Appointment"


def _convenzione(nome: str) -> dict:
	doc = frappe.get_cached_doc(CONVENZIONE, nome)
	dati = doc.as_dict()
	dati["shares"] = [{"service": r.service, "patient_share": r.patient_share} for r in doc.shares]
	return dati


def _attivi(doc) -> list:
	return [r for r in doc.get("participants") or [] if r.status != "Cancelled"]


def persona_dell_appuntamento(doc) -> str | None:
	"""The one person of the appointment, as a record."""
	from crm.fcrm.doctype.crm_appointment.crm_appointment import person_of

	for riga in _attivi(doc):
		persona = person_of(riga.party_type, riga.party)
		if persona:
			return persona
	return None


def copertura_di(persona: str | None, convenzione: str, giorno) -> dict | None:
	"""The person's cover of a convention on a day: theirs, the most recent."""
	if not persona:
		return None
	for riga in frappe.get_all(
		COPERTURA,
		filters={"person": persona, "convention": convenzione},
		fields=["name", "card_number", "holder", "holder_name", "valid_from", "valid_upto"],
		order_by="creation desc",
	):
		if R.copertura_valida(riga, getdate(giorno)):
			return riga
	return None


# ------------------------------------------------------------------ the appointment


def listino(doc) -> None:
	"""`validate`, before the price: a convention with a price list prices the
	appointment on it; without a convention, a convention's list is not the
	centre's and gives way to the default."""
	from crm.scheduling import pricing

	if doc.get("convention"):
		conv = frappe.get_cached_doc(CONVENZIONE, doc.convention)
		if conv.price_mode == R.LISTINO and conv.price_list:
			doc.price_list = conv.price_list
			return
	liste = set(frappe.get_all(CONVENZIONE, filters={"price_list": ["is", "set"]}, pluck="price_list"))
	if doc.get("price_list") in liste:
		doc.price_list = pricing.default_price_list()


def _cambiato(doc, *campi) -> bool:
	prima = doc.get_doc_before_save()
	if not prima:
		return True
	return any(str(prima.get(c) or "") != str(doc.get(c) or "") for c in campi)


def prezzo(doc) -> None:
	"""`validate`, after the cycles and the subscriptions: the convention's form,
	cover and price; the shares come once the price is final (`quote_dell_appuntamento`)."""
	if not doc.get("convention"):
		doc.convention_form = None
		doc.convention_cover = None
		doc.patient_share = doc.fund_share = 0
		return
	conv = _convenzione(doc.convention)
	attivi = _attivi(doc)
	if len(attivi) > 1:
		frappe.throw(_("A convention is for an appointment of one person"))
	if any(r.get("subscription") for r in attivi):
		frappe.throw(_("A place of a subscription is not paid under a convention"))
	forme = R.forme(conv)
	if not doc.get("convention_form"):
		doc.convention_form = forme[0] if forme else R.INDIRETTA
	if doc.convention_form not in forme:
		frappe.throw(
			_("The convention {0} is not used in direct form").format(conv["convention_name"])
			if doc.convention_form == R.DIRETTA
			else _("The convention {0} is not used in indirect form").format(conv["convention_name"])
		)
	if _cambiato(doc, "convention", "starts_on") and not R.valida_il(conv, getdate(doc.starts_on)):
		frappe.throw(_("The convention {0} does not hold on that day").format(conv["convention_name"]))
	persona = persona_dell_appuntamento(doc)
	copertura = copertura_di(persona, doc.convention, doc.starts_on)
	doc.convention_cover = copertura.name if copertura else None

	totale = flt(doc.total_amount)
	if conv.get("price_mode") == R.SCONTO:
		totale = float(R.prezzo(conv, totale))
		doc.unit_price = doc.total_amount = totale
		for riga in attivi:
			riga.amount = totale
	doc.price_source = conv["convention_name"]


def quote_dell_appuntamento(doc, method=None) -> None:
	"""`validate` (doc_events), after the price is final - an accepted quote's
	agreed price comes after the controller: the person's share and the fund's."""
	if not doc.get("convention"):
		return
	conv = _convenzione(doc.convention)
	persona_paga, fondo_paga = R.quote(conv, doc.convention_form, flt(doc.total_amount), doc.service)
	doc.patient_share, doc.fund_share = float(persona_paga), float(fondo_paga)
	if doc.convention_form != R.DIRETTA:
		doc.authorisation = None
	gia = doc.get("fund_invoice") and frappe.db.get_value("CRM Invoice", doc.fund_invoice, "docstatus")
	if gia in (0, 1) and _cambiato(doc, "convention", "convention_form", "fund_share"):
		frappe.throw(_("This appointment is billed to the fund already: {0}").format(doc.fund_invoice))


def da_pagare_dalla_persona(incontro) -> float:
	"""What the person's own invoice for an appointment is for: their share in
	direct form, the price otherwise."""
	if incontro.get("convention") and incontro.get("convention_form") == R.DIRETTA:
		return flt(incontro.patient_share)
	return flt(incontro.unit_price)


def nulla_per_la_persona(incontro) -> bool:
	return (
		bool(incontro.get("convention"))
		and incontro.get("convention_form") == R.DIRETTA
		and not flt(incontro.get("patient_share"))
	)


# ------------------------------------------------------------------ the pratiche


def _numero_della_fattura(fattura) -> str:
	return fattura.document_number or fattura.name


def pratiche(convenzione: str, dal, al, nomi: list[str] | None = None) -> list[dict]:
	"""The appointments in direct form under a convention between two days, as
	pratiche: who, when, what, the authorisation, the shares, the state."""
	conv = _convenzione(convenzione)
	filtri = [
		["convention", "=", convenzione],
		["convention_form", "=", R.DIRETTA],
		["starts_on", ">=", f"{getdate(dal)} 00:00:00"],
		["starts_on", "<=", f"{getdate(al)} 23:59:59"],
	]
	if nomi is not None:
		filtri.append(["name", "in", nomi or [""]])
	righe = frappe.get_list(
		APPUNTAMENTO,
		filters=filtri,
		fields=[
			"name",
			"service",
			"starts_on",
			"status",
			"total_amount",
			"patient_share",
			"fund_share",
			"authorisation",
			"convention_cover",
			"fund_invoice",
			"currency",
		],
		order_by="starts_on asc",
		limit_page_length=0,
	)
	if not righe:
		return []
	nomi_ = [r.name for r in righe]
	persone: dict[str, dict] = {}
	for p in frappe.get_all(
		"CRM Appointment Participant",
		filters={"parenttype": APPUNTAMENTO, "parent": ["in", nomi_]},
		fields=["parent", "party_type", "party", "participant_name", "status"],
		order_by="idx asc",
	):
		if p.parent not in persone or persone[p.parent]["status"] == "Cancelled":
			persone[p.parent] = p
	fatture = {
		f.name: f
		for f in frappe.get_all(
			"CRM Invoice",
			filters={"name": ["in", [r.fund_invoice for r in righe if r.fund_invoice] or [""]]},
			fields=["name", "docstatus", "collected_on", "document_number"],
		)
	}
	tessere = {
		c.name: c.card_number
		for c in frappe.get_all(
			COPERTURA,
			filters={"name": ["in", [r.convention_cover for r in righe if r.convention_cover] or [""]]},
			fields=["name", "card_number"],
		)
	}
	servizi = {
		s.name: s.service_name
		for s in frappe.get_all(
			"CRM Service",
			filters={"name": ["in", list({r.service for r in righe if r.service})]},
			fields=["name", "service_name"],
		)
	}
	from crm.fcrm.doctype.crm_appointment.crm_appointment import person_of

	fuori = []
	for r in righe:
		p = persone.get(r.name) or {}
		fattura = fatture.get(r.fund_invoice) if r.fund_invoice else None
		docstatus = fattura.docstatus if fattura and fattura.docstatus < 2 else None
		fuori.append(
			{
				"appointment": r.name,
				"date": str(r.starts_on),
				"service": servizi.get(r.service, r.service),
				"patient": p.get("participant_name") or "",
				"person": person_of(p.get("party_type"), p.get("party")),
				"card_number": tessere.get(r.convention_cover) or "",
				"authorisation": r.authorisation or "",
				"total": flt(r.total_amount),
				"patient_share": flt(r.patient_share),
				"fund_share": flt(r.fund_share),
				"currency": r.currency,
				"state": R.stato(
					r.status,
					p.get("status"),
					bool(conv.get("requires_authorisation")),
					r.authorisation,
					docstatus,
					bool(fattura and fattura.collected_on),
				),
				"invoice": _numero_della_fattura(fattura) if docstatus is not None else "",
				"invoice_name": fattura.name if docstatus is not None else "",
			}
		)
	return fuori


def fattura_al_fondo(convenzione: str, mese: str, nomi: list[str] | None = None) -> str:
	"""The fund's draft for a month: one line per pratica done and not billed, at
	the fund's share, to the company that pays. Made by the invoicing engine as any
	other invoice - a company in test makes a test invoice."""
	from crm.invoicing.engine.codici import TipoDestinatario

	conv = frappe.get_doc(CONVENZIONE, convenzione)
	if not conv.organization:
		frappe.throw(
			_("Choose the company that pays for the convention {0} first").format(conv.convention_name)
		)
	dal, al = R.mese(mese)
	da_fare = [p for p in pratiche(convenzione, dal, al, nomi) if R.da_fatturare(p)]
	if not da_fare:
		frappe.throw(_("No pratica of the month is done and still to bill"))

	fattura = frappe.new_doc("CRM Invoice")
	fattura.party_type = "CRM Organization"
	fattura.party = conv.organization
	fattura.recipient_type = TipoDestinatario.SOGGETTO_IVA
	fattura.causale = _("Convention {0}: pratiche of {1}").format(
		conv.convention_name, frappe.utils.formatdate(dal, "MMMM yyyy")
	)
	for p in da_fare:
		incontro = frappe.get_doc(APPUNTAMENTO, p["appointment"])
		carta = frappe.db.get_value(
			"CRM Billable Service", {"crm_service": incontro.service, "enabled": 1}, "name"
		)
		if not carta:
			frappe.throw(
				_("No fiscal card for the service {0}: a service without a card is not billable").format(
					p["service"]
				)
			)
		erogatore = None
		for membro in incontro.staff or []:
			erogatore = frappe.db.get_value(
				"CRM Service Provider", {"user": membro.user, "enabled": 1}, "name"
			)
			if erogatore:
				break
		erogatore = erogatore or frappe.db.get_value("CRM Billable Service", carta, "default_provider")
		fattura.append(
			"items",
			{
				"billable_service": carta,
				"service_provider": erogatore or "",
				"description": R.descrizione(
					p["service"], p["patient"], p["date"], p["authorisation"], p["card_number"]
				),
				"qty": 1,
				"rate": p["fund_share"],
			},
		)
	fattura.insert()
	for p in da_fare:
		frappe.db.set_value(
			APPUNTAMENTO, p["appointment"], "fund_invoice", fattura.name, update_modified=False
		)
	return fattura.name


def fattura_tolta(doc, method=None) -> None:
	"""`on_trash` and `on_cancel` of an invoice: the pratiche it held are to bill again."""
	for nome in frappe.get_all(APPUNTAMENTO, filters={"fund_invoice": doc.name}, pluck="name"):
		frappe.db.set_value(APPUNTAMENTO, nome, "fund_invoice", None, update_modified=False)


# ------------------------------------------------------------------ the person


def coperture_della_persona(persona: str, solo_valide: bool = False) -> list[dict]:
	"""A person's covers, each with its convention's name and kind and whether it
	holds today."""
	oggi = getdate()
	righe = frappe.get_all(
		COPERTURA,
		filters={"person": persona},
		fields=[
			"name",
			"convention",
			"card_number",
			"holder",
			"holder_name",
			"valid_from",
			"valid_upto",
			"notes",
		],
		order_by="creation desc",
	)
	fuori = []
	for riga in righe:
		conv = frappe.db.get_value(
			CONVENZIONE,
			riga.convention,
			["convention_name", "kind", "direct", "indirect", "enabled", "valid_from", "valid_upto"],
			as_dict=True,
		)
		if not conv:
			continue
		valida = R.copertura_valida(riga, oggi) and R.valida_il(conv, oggi)
		if solo_valide and not valida:
			continue
		fuori.append(
			{
				**riga,
				"valid_from": str(riga.valid_from) if riga.valid_from else None,
				"valid_upto": str(riga.valid_upto) if riga.valid_upto else None,
				"convention_name": conv.convention_name,
				"kind": conv.kind,
				"forms": R.forme(conv),
				"valid": valida,
			}
		)
	return fuori


def cancella_con_la_persona(doc, method=None) -> None:
	"""`on_trash` of a person: their covers are part of them."""
	for nome in frappe.get_all(COPERTURA, filters={"person": doc.name}, pluck="name"):
		frappe.delete_doc(COPERTURA, nome, ignore_permissions=True, force=True)
	# a cover they held for somebody else stays that person's, without a holder
	for nome in frappe.get_all(COPERTURA, filters={"holder": doc.name}, pluck="name"):
		frappe.db.set_value(COPERTURA, nome, "holder", None, update_modified=False)


def nelle_righe(righe: list[dict]) -> None:
	"""The reception desk's and the agenda's rows: the convention each is under,
	and whether its authorisation is missing."""
	nomi = [r["name"] for r in righe if r.get("name")]
	if not nomi:
		return
	dati = {
		a.name: a
		for a in frappe.get_all(
			APPUNTAMENTO,
			filters={"name": ["in", nomi], "convention": ["is", "set"]},
			fields=["name", "convention", "convention_form", "authorisation"],
		)
	}
	if not dati:
		return
	richiesta = {
		c.name: c
		for c in frappe.get_all(
			CONVENZIONE,
			filters={"name": ["in", list({a.convention for a in dati.values()})]},
			fields=["name", "convention_name", "requires_authorisation"],
		)
	}
	for r in righe:
		a = dati.get(r.get("name"))
		if not a:
			continue
		conv = richiesta.get(a.convention) or {}
		r["convention"] = {
			"name": a.convention,
			"title": conv.get("convention_name") or a.convention,
			"form": a.convention_form,
			"missing_authorisation": R.manca_l_autorizzazione(
				a.convention_form, bool(conv.get("requires_authorisation")), a.authorisation
			),
		}


def del_appuntamento(doc) -> dict | None:
	"""What the appointment's panel says of its convention: which, in what form,
	the shares, the card, the authorisation missing, the pratica's state."""
	if not doc.get("convention"):
		return None
	conv = frappe.db.get_value(
		CONVENZIONE, doc.convention, ["convention_name", "kind", "requires_authorisation"], as_dict=True
	) or frappe._dict(convention_name=doc.convention)
	fattura = (
		frappe.db.get_value(
			"CRM Invoice",
			doc.fund_invoice,
			["name", "docstatus", "collected_on", "document_number"],
			as_dict=True,
		)
		if doc.get("fund_invoice")
		else None
	)
	docstatus = fattura.docstatus if fattura and fattura.docstatus < 2 else None
	persona = next(iter(_attivi(doc)), None)
	return {
		"title": conv.convention_name,
		"kind": conv.get("kind"),
		"form": doc.convention_form,
		"patient_share": flt(doc.patient_share),
		"fund_share": flt(doc.fund_share),
		"card_number": frappe.db.get_value(COPERTURA, doc.convention_cover, "card_number")
		if doc.get("convention_cover")
		else "",
		"requires_authorisation": bool(conv.get("requires_authorisation")),
		"missing_authorisation": R.manca_l_autorizzazione(
			doc.convention_form, bool(conv.get("requires_authorisation")), doc.authorisation
		),
		"state": R.stato(
			doc.status,
			persona.status if persona else None,
			bool(conv.get("requires_authorisation")),
			doc.authorisation,
			docstatus,
			bool(fattura and fattura.collected_on),
		)
		if doc.convention_form == R.DIRETTA
		else None,
		"fund_invoice": _numero_della_fattura(fattura) if docstatus is not None else "",
	}


def listino_di(convenzione: str) -> str | None:
	"""The price list a convention prices on, when it has one."""
	conv = frappe.db.get_value(CONVENZIONE, convenzione, ["price_mode", "price_list"], as_dict=True)
	return conv.price_list if conv and conv.price_mode == R.LISTINO else None


def anteprima(convenzione: str, forma: str | None, totale, servizio: str | None) -> dict:
	"""The panel's preview under a convention: the price, the two shares, the form."""
	conv = _convenzione(convenzione)
	forme = R.forme(conv)
	forma = forma if forma in forme else (forme[0] if forme else R.INDIRETTA)
	prezzo = R.prezzo(conv, totale) if conv.get("price_mode") == R.SCONTO else R.soldi(totale)
	persona, fondo = R.quote(conv, forma, prezzo, servizio)
	return {
		"total": float(prezzo),
		"rate": float(prezzo),
		"source": conv["convention_name"],
		"convention_form": forma,
		"forms": forme,
		"patient_share": float(persona),
		"fund_share": float(fondo),
		"requires_authorisation": bool(conv.get("requires_authorisation")) and forma == R.DIRETTA,
	}


# ------------------------------------------------------------------ /prenota


def offerte_online() -> list[dict]:
	"""The conventions /prenota offers: switched on, valid today, shown online."""
	oggi = getdate()
	return [
		{"id": c.name, "name": c.convention_name}
		for c in frappe.get_all(
			CONVENZIONE,
			filters={"enabled": 1, "show_online": 1},
			fields=["name", "convention_name", "valid_from", "valid_upto", "enabled"],
			order_by="convention_name asc",
		)
		if R.valida_il(c, oggi)
	]


def scelta_online(nome: str | None) -> str | None:
	"""The convention a visitor chose, only among the ones offered."""
	if not nome:
		return None
	if nome not in {c["id"] for c in offerte_online()}:
		frappe.throw(_("This convention is not offered online: call the centre"))
	return nome


def prenotata_online(appuntamento, convenzione: str, persona: str | None, tessera: str | None) -> None:
	"""An online booking under a convention: in its first form, the person's cover
	written when they had none (their card as they typed it), the desk to check it."""
	conv = frappe.get_cached_doc(CONVENZIONE, convenzione)
	appuntamento.convention = convenzione
	appuntamento.convention_form = R.DIRETTA if conv.direct else R.INDIRETTA
	if persona and not copertura_di(persona, convenzione, appuntamento.starts_on):
		frappe.get_doc(
			{
				"doctype": COPERTURA,
				"person": persona,
				"convention": convenzione,
				"card_number": " ".join((tessera or "").split())[:60] or None,
				"notes": _("Written by the person on the booking page: to check"),
			}
		).insert(ignore_permissions=True)
