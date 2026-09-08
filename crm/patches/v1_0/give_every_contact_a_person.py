# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""An address book entry with nobody behind it is unreachable.

The person list is the only list of people now: the separate Contacts entry is
gone from the sidebar, because two lists of the same human being was the
duplication we set out to remove. `give_every_lead_a_contact` did one direction;
this is the other, for the entries that were made before `create_person` existed
(a contact typed into a deal, an import) and never got a person.
"""

import frappe


def execute():
	linked = {
		name
		for name in frappe.get_all("CRM Lead", filters={"contact": ["is", "set"]}, pluck="contact")
		if name
	}
	for contact in frappe.get_all("Contact", pluck="name"):
		if contact in linked:
			continue
		doc = frappe.get_doc("Contact", contact)
		first_name = doc.first_name or doc.name
		email = doc.email_id or (doc.email_ids[0].email_id if doc.email_ids else "")
		mobile = doc.mobile_no or (doc.phone_nos[0].phone if doc.phone_nos else "")
		if not (email or mobile):
			continue  # nothing to reach them by: not a person, just a name
		lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": first_name,
				"last_name": doc.last_name or "",
				"salutation": doc.salutation or None,
				"gender": doc.gender or None,
				"job_title": doc.designation or "",
				"organization": doc.company_name or "",
				"email": email,
				"mobile_no": mobile,
				"contact": contact,
			}
		)
		lead.flags.ignore_mandatory = True
		try:
			lead.insert(ignore_permissions=True)
		except Exception:
			frappe.db.rollback()
			frappe.log_error(frappe.get_traceback(), f"No person could be made for contact {contact}")
		else:
			frappe.db.commit()
