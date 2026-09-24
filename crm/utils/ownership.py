# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Who a record belongs to when nobody was logged in.

A lead that arrives from a Meta form, a WhatsApp message from a stranger, a
booking made on the public page: all of them are created while the session user
is **Guest**, because that is who the caller is. Frappe stamps that on the
record, and the history then says «Guest created this lead».

Which is technically true and useless. Guest is not a person, nobody can be
asked about it, and on a screen full of names it reads like a mistake — or
worse, like somebody outside the company got in.

So a record created with no one logged in belongs to the system. `Administrator`
is Frappe's own name for that, it exists on every site, and it needs nothing
created or configured to work.
"""

import frappe

SYSTEM_USER = "Administrator"


def credit_the_system(doc, method=None):
	"""Rewrite `Guest` to the system user, before the row is written.

	`set_user_and_timestamp()` runs before `before_insert`, so the field is
	already filled in by the time this sees it — and overwriting it here is what
	ends up in the database.
	"""
	if doc.get("owner") == "Guest":
		doc.owner = SYSTEM_USER
	if doc.get("modified_by") == "Guest":
		doc.modified_by = SYSTEM_USER
