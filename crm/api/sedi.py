# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Settings > The centre > Locations (docs/crm/62): the centre's locations, written
by its manager; where each person usually works, written by themselves."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint

from crm.permissions.livelli import verifica
from crm.scheduling import sedi
from crm.scheduling import sedi_regole as R

CAMPI = (
	"location_name",
	"enabled",
	"address_line",
	"city",
	"pincode",
	"province",
	"phone",
	"email",
	"map_link",
	"opening_hours",
	"company",
)


def _check() -> None:
	verifica("impostazioni.generali", messaggio=_("Only the centre's manager changes its locations"))


def _riga(doc) -> dict:
	riga = {campo: doc.get(campo) for campo in ("name", *CAMPI)}
	riga["enabled"] = cint(riga["enabled"])
	riga["address"] = R.indirizzo(riga)
	riga["rooms"] = frappe.db.count("CRM Resource", {"centre_location": doc.name, "enabled": 1})
	riga["company_name"] = (
		frappe.db.get_value("CRM Invoicing Company", doc.company, "company_name") if doc.company else ""
	)
	return riga


@frappe.whitelist()
def list_locations() -> dict:
	"""Every location, on and off, with its rooms; and the issuing companies one may name."""
	_check()
	return {
		"locations": [
			_riga(doc)
			for doc in frappe.get_all(sedi.SEDE, fields=["name", *CAMPI], order_by="location_name asc")
		],
		"companies": frappe.get_all(
			"CRM Invoicing Company",
			filters={"enabled": 1},
			fields=["name", "company_name"],
			order_by="company_name asc",
		),
	}


@frappe.whitelist(methods=["POST"])
def save_location(location: str | dict, name: str | None = None) -> dict:
	_check()
	dati = frappe.parse_json(location) if isinstance(location, str) else dict(location or {})
	valori = {campo: dati.get(campo) for campo in CAMPI if campo in dati}
	valori["location_name"] = " ".join(str(valori.get("location_name") or "").split())
	if not valori["location_name"]:
		frappe.throw(_("Give the location a name"))
	if "enabled" in valori:
		valori["enabled"] = cint(valori["enabled"])
	if valori.get("company") and not frappe.db.exists("CRM Invoicing Company", valori["company"]):
		valori["company"] = None
	if name:
		doc = frappe.get_doc(sedi.SEDE, name)
		doc.update(valori)
		doc.save()
	else:
		doc = frappe.get_doc({"doctype": sedi.SEDE, **valori}).insert()
	sedi.dimentica()
	return {**_riga(doc), "boot": sedi.per_il_boot()}


@frappe.whitelist(methods=["POST"])
def delete_location(name: str) -> dict:
	_check()
	frappe.delete_doc(sedi.SEDE, name)
	sedi.dimentica()
	return {"boot": sedi.per_il_boot()}


@frappe.whitelist()
def get_my_location() -> dict:
	"""Where the session usually works, and the locations to choose from."""
	return {"location": sedi.sede_abituale(), "locations": sedi.per_il_boot()}


@frappe.whitelist(methods=["POST"])
def set_my_location(location: str | None = None) -> dict:
	"""Where the session usually works: the reception desk opens on it."""
	if frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	sedi.imposta_sede_abituale(location)
	return get_my_location()
