# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Whoever came or bought is a client, whatever the centre's trade, and the person
says who they are to the centre (`CRM Lead.relationship`).

Until now, where the clinic was on, only its patients became clients: whoever came
to a Pilates class was nobody. The clients already there are found again
(`cliente.recupera`, announcing nothing), then every person gets their step: a
client where `client_since` says so, a contact otherwise. The clinic's patients get
theirs from the clinic's own patch, which comes after this one. Where the centre
chose the People list's quick filters, the relationship joins them after the name.
"""

import json

import frappe
from frappe.query_builder.functions import IfNull

from crm.clienti import cliente


def execute():
	cliente.recupera()
	persona = frappe.qb.DocType("CRM Lead")
	(
		frappe.qb.update(persona)
		.set(persona.relationship, cliente.CLIENTE)
		.where(
			persona.client_since.isnotnull() & IfNull(persona.relationship, "").isin(["", cliente.CONTATTO])
		)
	).run()
	(
		frappe.qb.update(persona)
		.set(persona.relationship, cliente.CONTATTO)
		.where(IfNull(persona.relationship, "") == "")
	).run()
	_tra_i_filtri_rapidi()


def _tra_i_filtri_rapidi() -> None:
	nome = frappe.db.exists("CRM Global Settings", {"dt": "CRM Lead", "type": "Quick Filters"})
	if not nome:
		return  # the fields marked as standard filters: the relationship is one
	try:
		campi = json.loads(frappe.db.get_value("CRM Global Settings", nome, "json") or "[]")
	except ValueError:
		return
	if not isinstance(campi, list) or cliente.RAPPORTO in campi:
		return
	campi.insert(campi.index("lead_name") + 1 if "lead_name" in campi else 0, cliente.RAPPORTO)
	frappe.db.set_value("CRM Global Settings", nome, "json", json.dumps(campi), update_modified=False)
