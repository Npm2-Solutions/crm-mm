# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""An email received reaches the person it is from (doc 51).

The settings page set the inbox of every mailbox to make a person of whoever wrote
("Append To: CRM Lead"): every email that was not a reply made a new one, even from
somebody the centre already knew. The inbox stops doing it: DottorCloud finds the
person who wrote (`crm.posta.ingresso`), and makes a new one only for who writes the
first time - which these mailboxes did, so they keep doing it.

Whoever works with levels stops receiving the framework's copy of a person's email
in their own mailbox: DottorCloud's panel tells them, as for WhatsApp. The agency's
sending service is set up after the migrate (`crm.posta.servizio.assicura`), where
its connection is tried.
"""

import frappe

PERSONA = "CRM Lead"


def execute():
	conti = set()
	for riga in frappe.get_all(
		"IMAP Folder",
		filters={"append_to": PERSONA, "parenttype": "Email Account"},
		fields=["name", "parent"],
	):
		frappe.db.set_value("IMAP Folder", riga.name, "append_to", None, update_modified=False)
		conti.add(riga.parent)
	for nome in frappe.get_all("Email Account", filters={"append_to": PERSONA}, pluck="name"):
		frappe.db.set_value("Email Account", nome, "append_to", None, update_modified=False)
		conti.add(nome)
	for nome in conti:
		frappe.db.set_value(
			"Email Account", nome, "create_lead_from_incoming_email", 1, update_modified=False
		)

	from crm.permissions import utenti
	from crm.permissions.livelli import carica

	carica()
	profili = utenti.profili_crm()
	if profili:
		for user in set(
			frappe.get_all(
				"User Role Profile",
				filters={"role_profile": ["in", sorted(profili)], "parenttype": "User"},
				pluck="parent",
			)
		):
			frappe.db.set_value("User", user, "thread_notify", 0, update_modified=False)
