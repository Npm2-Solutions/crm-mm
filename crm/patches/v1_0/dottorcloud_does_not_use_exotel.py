# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""DottorCloud no longer offers Exotel (03/10/2026): calls go through Twilio.

What the provider left on a site goes with it: its settings, with the account's
key, token and webhook secret; a person's default way of calling that named it
(the call would find no carrier and leave nothing); the calls it logged keep
everything but their carrier, an option the call log no longer has. The number
a person called from with it stays in its column: deleting a field leaves it.
"""

import frappe

IMPOSTAZIONI = "CRM Exotel Settings"


def execute():
	if frappe.db.exists("DocType", IMPOSTAZIONI):
		frappe.delete_doc("DocType", IMPOSTAZIONI, force=True, ignore_missing=True, ignore_permissions=True)
	frappe.db.delete("Custom DocPerm", {"parent": IMPOSTAZIONI})
	frappe.db.delete("Property Setter", {"doc_type": IMPOSTAZIONI})

	# what a single keeps outside its DocType: its values and its passwords
	frappe.db.delete("Singles", {"doctype": IMPOSTAZIONI})
	frappe.db.delete("__Auth", {"doctype": IMPOSTAZIONI})

	frappe.db.set_value(
		"CRM Telephony Agent", {"default_medium": "Exotel"}, "default_medium", "", update_modified=False
	)
	frappe.db.set_value(
		"CRM Call Log", {"telephony_medium": "Exotel"}, "telephony_medium", "", update_modified=False
	)
