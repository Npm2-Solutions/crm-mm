# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The calls of the conventions' screens (doc 61).

- Settings > Invoicing > Conventions and funds (`convenzioni.gestisci`): the list,
  one convention, saving and deleting it.
- The person's Data tab: their covers, read with the person, written with
  `persone.scrivi` (`get_covers`, `save_cover`, `remove_cover`).
- The appointment's panel: what the person may come under (`options_for`) and the
  price under it (`quote`).
- The Invoices page's Conventions tab (`fatture.vedi`, billing with
  `fatture.emetti`): a convention's pratiche of a month, the fund's invoice, the
  month as a CSV for the fund's portal.
"""

from __future__ import annotations

import json
import re

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate

from crm.convenzioni import convenzioni as C
from crm.convenzioni import regole as R
from crm.permissions import livelli, org_hierarchy

CONVENZIONE = C.CONVENZIONE
COPERTURA = C.COPERTURA

#: What the settings write of a convention.
_CAMPI = (
	"convention_name",
	"kind",
	"enabled",
	"organization",
	"valid_from",
	"valid_upto",
	"direct",
	"indirect",
	"requires_authorisation",
	"show_online",
	"price_mode",
	"price_list",
	"discount_percent",
	"share_mode",
	"share_amount",
	"share_percent",
	"notes",
)


def _carica(valore):
	return json.loads(valore) if isinstance(valore, str) else (valore or {})


def _gestisce() -> None:
	livelli.verifica_nel_crm("convenzioni.gestisci")


def _di_chi_paga(nome: str | None) -> str:
	return (frappe.db.get_value("CRM Organization", nome, "organization_name") or nome) if nome else ""


def _riga(doc) -> dict:
	dati = {campo: doc.get(campo) for campo in _CAMPI}
	for campo in ("valid_from", "valid_upto"):
		dati[campo] = str(dati[campo]) if dati[campo] else None
	dati.update(
		{
			"name": doc.name,
			"organization_name": _di_chi_paga(doc.organization),
			"price_list_name": frappe.db.get_value("CRM Price List", doc.price_list, "price_list_name")
			if doc.price_list
			else "",
			"shares": [{"service": r.service, "patient_share": flt(r.patient_share)} for r in doc.shares],
			"covers": frappe.db.count(COPERTURA, {"convention": doc.name}),
			"used": frappe.db.count(C.APPUNTAMENTO, {"convention": doc.name}),
		}
	)
	return dati


# ------------------------------------------------------------------ settings


@frappe.whitelist()
def list_conventions() -> dict:
	"""Every convention, for the settings; the companies and price lists to pick."""
	_gestisce()
	return {
		"conventions": [
			_riga(frappe.get_doc(CONVENZIONE, nome))
			for nome in frappe.get_all(CONVENZIONE, order_by="convention_name asc", pluck="name")
		],
		"price_lists": frappe.get_all(
			"CRM Price List",
			filters={"enabled": 1},
			fields=["name", "price_list_name"],
			order_by="price_list_name asc",
		),
	}


@frappe.whitelist(methods=["POST"])
def save_convention(data: str | dict, name: str | None = None) -> dict:
	_gestisce()
	dati = _carica(data)
	problemi = R.problemi(dati)
	if problemi:
		frappe.throw("\n".join(p.testo(_) for p in problemi))
	doc = frappe.get_doc(CONVENZIONE, name) if name else frappe.new_doc(CONVENZIONE)
	for campo in _CAMPI:
		if campo in dati:
			doc.set(campo, dati.get(campo) if dati.get(campo) not in ("",) else None)
	for campo in ("enabled", "direct", "indirect", "requires_authorisation", "show_online"):
		doc.set(campo, cint(dati.get(campo)))
	if not doc.direct:
		doc.requires_authorisation = 0
	doc.set(
		"shares",
		[
			{"service": r.get("service"), "patient_share": flt(r.get("patient_share"))}
			for r in dati.get("shares") or []
			if r.get("service")
		],
	)
	doc.save() if name else doc.insert()
	return _riga(doc)


@frappe.whitelist(methods=["POST"])
def delete_convention(name: str) -> None:
	"""Only a convention nobody used: one that was is switched off instead."""
	_gestisce()
	if frappe.db.exists(C.APPUNTAMENTO, {"convention": name}):
		frappe.throw(_("Appointments were booked under this convention: switch it off instead"))
	for cover in frappe.get_all(COPERTURA, filters={"convention": name}, pluck="name"):
		frappe.delete_doc(COPERTURA, cover)
	frappe.delete_doc(CONVENZIONE, name)


# ------------------------------------------------------------------ the person's covers


def _della_persona(lead: str) -> None:
	livelli.verifica_nel_crm("persone.vedi")
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)


def _puo_scrivere() -> bool:
	if livelli.nel_crm() and not livelli.puo("persone.scrivi"):
		return False
	return bool(frappe.has_permission(COPERTURA, "create"))


def _convenzioni_attive() -> list[dict]:
	oggi = getdate()
	return [
		{"name": c.name, "convention_name": c.convention_name, "kind": c.kind, "forms": R.forme(c)}
		for c in frappe.get_all(
			CONVENZIONE,
			filters={"enabled": 1},
			fields=[
				"name",
				"convention_name",
				"kind",
				"direct",
				"indirect",
				"valid_from",
				"valid_upto",
				"enabled",
			],
			order_by="convention_name asc",
		)
		if R.valida_il(c, oggi)
	]


@frappe.whitelist()
def get_covers(lead: str) -> dict:
	_della_persona(lead)
	return {
		"covers": C.coperture_della_persona(lead),
		"conventions": _convenzioni_attive(),
		"can_edit": _puo_scrivere(),
	}


@frappe.whitelist(methods=["POST"])
def save_cover(lead: str, data: str | dict, name: str | None = None) -> dict:
	livelli.verifica_nel_crm("persone.scrivi")
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	dati = _carica(data)
	problemi = R.problemi_della_copertura(dati)
	if problemi:
		frappe.throw("\n".join(p.testo(_) for p in problemi))
	if name:
		doc = frappe.get_doc(COPERTURA, name)
		if doc.person != lead:
			frappe.throw(_("This cover is not this person's"))
	else:
		doc = frappe.new_doc(COPERTURA)
		doc.person = lead
	holder = dati.get("holder") or None
	if holder == lead:
		holder = None
	if holder:
		frappe.has_permission("CRM Lead", "read", doc=holder, throw=True)
	doc.update(
		{
			"convention": dati.get("convention"),
			"card_number": (dati.get("card_number") or "").strip() or None,
			"holder": holder,
			"valid_from": dati.get("valid_from") or None,
			"valid_upto": dati.get("valid_upto") or None,
			"notes": dati.get("notes") or None,
		}
	)
	doc.save()
	return get_covers(lead)


@frappe.whitelist(methods=["POST"])
def remove_cover(lead: str, name: str) -> dict:
	livelli.verifica_nel_crm("persone.scrivi")
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	doc = frappe.get_doc(COPERTURA, name)
	if doc.person != lead:
		frappe.throw(_("This cover is not this person's"))
	doc.delete()
	return get_covers(lead)


def nel_riepilogo(lead: str) -> dict | None:
	"""The summary's line: the covers that hold today."""
	coperture = C.coperture_della_persona(lead, solo_valide=True)
	if not coperture:
		return None
	return {
		"covers": [
			{
				"convention_name": c["convention_name"],
				"kind": c["kind"],
				"card_number": c["card_number"],
				"holder_name": c["holder_name"] if c.get("holder") else "",
				"valid_upto": c["valid_upto"],
			}
			for c in coperture
		]
	}


# ------------------------------------------------------------------ the appointment


@frappe.whitelist()
def options_for(person: str | None = None, when: str | None = None) -> dict:
	"""What the appointment's panel offers: the conventions in force, the person's
	covers first."""
	if not (livelli.puo("agenda.vedi") or livelli.puo("agenda.prenota")):
		livelli.verifica_nel_crm("agenda.vedi")
	giorno = getdate(when) if when else getdate()
	coperte = {}
	if person and frappe.has_permission("CRM Lead", "read", doc=person):
		for c in C.coperture_della_persona(person):
			if R.copertura_valida(c, giorno):
				coperte.setdefault(c["convention"], c)
	fuori = []
	for c in _convenzioni_attive():
		copertura = coperte.get(c["name"])
		requires = frappe.db.get_value(CONVENZIONE, c["name"], "requires_authorisation")
		fuori.append(
			{
				**c,
				"covered": bool(copertura),
				"card_number": copertura["card_number"] if copertura else "",
				"requires_authorisation": cint(requires),
			}
		)
	fuori.sort(key=lambda c: (not c["covered"], c["convention_name"]))
	return {"conventions": fuori}


@frappe.whitelist()
def quote(convention: str, form: str, total: float, service: str | None = None) -> dict:
	"""The price under a convention and its two shares, from the centre's price as
	the agenda resolved it on the convention's price list."""
	if not (livelli.puo("agenda.vedi") or livelli.puo("agenda.prenota")):
		livelli.verifica_nel_crm("agenda.vedi")
	risposta = C.anteprima(convention, form, total, service)
	return {k: risposta[k] for k in ("total", "patient_share", "fund_share", "requires_authorisation")}


# ------------------------------------------------------------------ the pratiche


def _vede_le_fatture() -> None:
	livelli.verifica_nel_crm("fatture.vedi")


@frappe.whitelist()
def get_claims(convention: str | None = None, month: str | None = None) -> dict:
	"""A convention's pratiche of a month in direct form, and their totals; the
	conventions in direct form to choose from."""
	_vede_le_fatture()
	dirette = frappe.get_all(
		CONVENZIONE,
		filters={"direct": 1},
		fields=["name", "convention_name", "organization", "enabled"],
		order_by="enabled desc, convention_name asc",
	)
	mese = (month or str(getdate()))[:7]
	convention = convention or (dirette[0].name if dirette else None)
	if not convention:
		return {"conventions": [], "month": mese, "claims": [], "totals": R.totali([])}
	dal, al = R.mese(mese)
	pratiche = C.pratiche(convention, dal, al)
	conv = next((c for c in dirette if c.name == convention), None)
	return {
		"conventions": [
			{"name": c.name, "convention_name": c.convention_name, "enabled": c.enabled} for c in dirette
		],
		"convention": convention,
		"payer": _di_chi_paga(conv.organization) if conv else "",
		"month": mese,
		"claims": pratiche,
		"totals": R.totali(pratiche),
		"can_bill": livelli.puo("fatture.emetti") and bool(conv and conv.organization),
	}


@frappe.whitelist(methods=["POST"])
def bill_fund(convention: str, month: str, appointments: str | list | None = None) -> str:
	"""The fund's draft invoice for the month's pratiche done and not billed (all of
	them, or the ones chosen); its name, to open in the invoice dialog."""
	livelli.verifica_nel_crm("fatture.emetti")
	frappe.has_permission("CRM Invoice", "create", throw=True)
	nomi = _carica(appointments) if appointments else None
	return C.fattura_al_fondo(convention, month, nomi)


@frappe.whitelist()
def export_month(convention: str, month: str) -> dict:
	"""The month's statement as a CSV, for the fund's portal."""
	_vede_le_fatture()
	dal, al = R.mese(month)
	nome = frappe.db.get_value(CONVENZIONE, convention, "convention_name") or convention
	return {
		"filename": f"{re.sub(r'[^a-z0-9]+', '-', nome.lower()).strip('-') or 'convenzione'}-{str(month)[:7]}.csv",
		"content": R.csv_del_mese(C.pratiche(convention, dal, al)),
	}


# ------------------------------------------------------------------ permissions


def get_cover_permission_query_conditions(user: str | None = None) -> str:
	"""A cover follows its person."""
	visibili = org_hierarchy.visible_leads(user)
	if visibili is None:
		return ""
	riga = frappe.qb.DocType(COPERTURA)
	return riga.person.isin(visibili).get_sql(with_namespace=True, quote_char="`", secondary_quote_char="'")


def has_cover_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	user = user or frappe.session.user
	if not doc.get("person"):
		return (
			(ptype or "read") in ("read", "create")
			or not livelli.nel_crm(user)
			or livelli.puo("persone.scrivi", user)
		)
	legge = bool(frappe.has_permission("CRM Lead", "read", doc=doc.person, user=user))
	if (ptype or "read") in ("read", "print", "export", "report", "email", "share"):
		return legge
	if livelli.nel_crm(user) and not livelli.puo("persone.scrivi", user):
		return False
	return legge
