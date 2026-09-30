# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Which invoices, and whose billing details, someone reads (doc 30).

The document permissions say who reads invoices at all: the front desk and the
manager through the invoicing roles, the practitioner through Practitioner. A line
of an invoice says what was done - "seduta di psicoterapia" - and that is health
data, so the Sales User no longer reads them.

This narrows it for whoever reads only their own: the practitioner sees the invoices
of their own services, those with a line where they are the provider, and nothing
else. Anyone else keeps exactly what their roles give: a scope here narrows, it
never widens.
"""

from __future__ import annotations

import frappe

from crm.permissions import livelli, org_hierarchy


def _suoi(user: str) -> bool:
	return livelli.ambito("fatture.vedi", user) == livelli.SUOI


def _erogatori(user: str) -> list[str]:
	"""The providers who are ``user``: the practitioner, as invoicing knows them."""
	return frappe.get_all("CRM Service Provider", filters={"user": user}, pluck="name")


def get_permission_query_conditions(user: str | None = None) -> str:
	user = user or frappe.session.user
	if not _suoi(user):
		return ""
	erogatori = _erogatori(user)
	if not erogatori:
		return "1=0"
	elenco = ", ".join(frappe.db.escape(nome) for nome in erogatori)
	return (
		"`tabCRM Invoice`.`name` in (select `parent` from `tabCRM Invoice Item` "
		f"where `parenttype` = 'CRM Invoice' and `service_provider` in ({elenco}))"
	)


def has_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	user = user or frappe.session.user
	if not _suoi(user):
		return True
	erogatori = set(_erogatori(user))
	return any(riga.service_provider in erogatori for riga in doc.get("items") or [])


# ------------------------------------------------------------ billing details


def get_profile_permission_query_conditions(user: str | None = None) -> str:
	"""A person's billing details follow the person: listed to whoever sees them.

	The document permissions already say who reads billing details at all - the
	invoicing roles and the practitioner, not marketing - and this says whose.
	"""
	visibili = org_hierarchy.visible_leads(user)
	if visibili is None:
		return ""
	profilo = frappe.qb.DocType("CRM Billing Profile")
	condizione = (profilo.party_type != "CRM Lead") | profilo.party.isin(visibili)
	return condizione.get_sql(with_namespace=True, quote_char="`", secondary_quote_char="'")


def has_profile_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	if not (doc.get("party_type") and doc.get("party")):
		return True
	return bool(frappe.has_permission(doc.party_type, "read", doc=doc.party, user=user))
