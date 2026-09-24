# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Mark the messages that had already arrived from somebody's phone.

From now on the Coexistence webhook says so as it writes them. What is already
stored cannot be asked — but it can be told apart: those rows were written
without a controller and carry a `message_id` from the first moment, while a
message sent from the CRM is inserted first and only gets its id back from Meta
after it has gone.

Incoming messages are left alone: where *they* were typed is their business.
"""

import frappe

from crm.install import add_whatsapp_custom_fields


def execute():
	if not frappe.db.exists("DocType", "WhatsApp Message"):
		return

	add_whatsapp_custom_fields()
	if not frappe.get_meta("WhatsApp Message").has_field("written_on_the_phone"):
		return

	# `creation` equal to `modified` on an outgoing message means nothing wrote
	# to it after the insert — no send, no status coming back. That is the shape
	# of a row the webhook wrote whole.
	frappe.db.sql(
		"""
		update `tabWhatsApp Message`
		set written_on_the_phone = 1
		where type = 'Outgoing'
		  and message_id is not null and message_id != ''
		  and creation = modified
		"""
	)
	frappe.db.commit()
