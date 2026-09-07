"""Rewrite the numbers already stored so they carry their country prefix.

`370 340 0189` is a number only if you already know which country it belongs to.
The same person is `+39 370 340 0189` in the chat, and to anything that compares
the two they are two people — which is how an Italian number came to be read as
Indian. From now on a contact is saved in E.164; this brings the ones that were
saved before along.

Saving the contact is what does the work: the same hook that normalises a number
also carries it out to the leads and the deals that mirror it, so nothing has to
be updated twice here.

Idempotent: a contact whose numbers are already written properly is not touched,
so an interrupted run — and on a large site there will be one — can simply be
run again.
"""

import frappe

from crm.utils import to_e164

CHUNK = 200


def execute():
	names = frappe.get_all("Contact", pluck="name")
	for index, name in enumerate(names, start=1):
		try:
			write_with_prefix(name)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Patch: could not rewrite numbers of {name}")
		if index % CHUNK == 0:
			frappe.db.commit()
	frappe.db.commit()


def write_with_prefix(name: str) -> None:
	doc = frappe.get_doc("Contact", name)
	if not any(row.phone != to_e164(row.phone) for row in doc.phone_nos if row.phone):
		return

	# the numbers themselves are rewritten by the validate hook on save
	doc.save(ignore_permissions=True)
