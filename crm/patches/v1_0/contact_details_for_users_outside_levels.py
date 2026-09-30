# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Email and phone numbers are masked for whoever lacks the Contact Details role
(doc 30, PR 4).

Users with levels get it from their Role Profiles. Those the level migration left as
they were, with the roles of before, saw email and phone until today: they get the
role here, and nothing else changes for them. The row is written straight to the
table: saving the user would rebuild their roles from any profile of another app.
"""

import frappe

from crm.permissions import livelli
from crm.permissions.utenti import assicura_ruoli, profili_crm


def execute():
	livelli.carica()
	assicura_ruoli()
	ruolo = livelli.RUOLO_RECAPITI
	con_livelli = set(
		frappe.get_all(
			"User Role Profile",
			filters={"parenttype": "User", "role_profile": ["in", sorted(profili_crm())]},
			pluck="parent",
		)
	)
	nel_crm = set(
		frappe.get_all(
			"Has Role",
			filters={"parenttype": "User", "role": ["in", sorted(livelli.ruoli_di_accesso())]},
			pluck="parent",
		)
	)
	gia = set(frappe.get_all("Has Role", filters={"parenttype": "User", "role": ruolo}, pluck="parent"))
	for user in sorted(nel_crm - con_livelli - gia - {"Administrator", "Guest"}):
		frappe.get_doc(
			{
				"doctype": "Has Role",
				"parenttype": "User",
				"parentfield": "roles",
				"parent": user,
				"role": ruolo,
			}
		).db_insert()
		frappe.clear_cache(user=user)
