# Modifications copyright (c) 2026, NPM2 Solutions Srl

import frappe
from frappe.model.utils.mask import mask_field_value


@frappe.whitelist()
def get_deal_contacts(name: str):
	frappe.has_permission("CRM Deal", "read", name, throw=True)

	contacts = frappe.get_all(
		"CRM Contacts",
		filters={"parenttype": "CRM Deal", "parent": name},
		fields=["contact", "is_primary"],
		order_by="is_primary desc, idx asc",
		distinct=True,
	)
	deal_contacts = []
	for contact in contacts:
		if not contact.contact:
			continue

		is_primary = contact.is_primary
		doc = frappe.get_doc("Contact", contact.contact)
		# an entry is little else than an email and a phone: whoever does not read
		# it (Marketing, who sees people masked) gets them masked here too, as on
		# the person's page. The deal is no way around the address book.
		legge = frappe.has_permission("Contact", "read", doc=doc)

		_contact = {
			"name": doc.name,
			"image": doc.image,
			"full_name": doc.full_name,
			"email": doc.email_id if legge else _mascherato("email", doc.email_id),
			"mobile_no": doc.mobile_no if legge else _mascherato("mobile_no", doc.mobile_no),
			"is_primary": is_primary,
		}
		deal_contacts.append(_contact)
	return deal_contacts


def _mascherato(fieldname: str, valore: str | None) -> str | None:
	"""``valore`` masked the way Frappe masks the person's own ``fieldname``."""
	return mask_field_value(frappe.get_meta("CRM Lead").get_field(fieldname), valore)
