# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Messages sent from the phone to somebody the CRM did not know yet.

Coexistence stores them, but a message going **out** never creates a lead — the
owner's phone writes to the accountant and the supplier too, and every number
would become one. So they were filed under nothing.

When the person answered, their reply *did* create a lead, and the conversation
ended up split: the reply on the record, and the lines that opened it nowhere.
Somebody replying to nothing.

From now on the code files them the moment the number gets a record. This does
the same for the ones already stored.
"""

import frappe

from crm.integrations.api import get_contact_lead_or_deal_from_number
from crm.integrations.whatsapp.coexistence import adopt_orphans


def execute():
	if not frappe.db.exists("DocType", "WhatsApp Message"):
		return

	orphans = frappe.get_all(
		"WhatsApp Message",
		filters=[["reference_name", "is", "not set"]],
		fields=["name", "to", "from"],
		limit=2000,
	)
	if not orphans:
		return

	# one repair per number, not per message: `adopt_orphans` files all of them
	numbers = set()
	for row in orphans:
		numbers.update(n for n in (row.get("to"), row.get("from")) if n)

	filed = 0
	for number in numbers:
		try:
			reference, doctype = get_contact_lead_or_deal_from_number(number)
		except Exception:
			continue
		if doctype and reference:
			filed += adopt_orphans(number, doctype, reference)

	if filed:
		frappe.db.commit()
		print(f"WhatsApp: filed {filed} messages that had no record")
