import frappe
from frappe import _


def validate(doc, method):
	update_deals_email_mobile_no(doc)
	update_leads_email_mobile_no(doc)


def update_leads_email_mobile_no(doc):
	"""A lead's recapiti follow its contact, the way a deal's already do.

	The contact is where a person's numbers live; the fields on the lead are a
	copy kept for everything that reads `lead.mobile_no`. Without this the copy
	goes stale the moment somebody edits the number in the address book, which is
	precisely how the two came to disagree before they were tied together.
	"""
	wanted = {
		"email": doc.email_id,
		"mobile_no": doc.mobile_no,
		"phone": doc.get("phone"),
	}
	for lead in frappe.get_all("CRM Lead", filters={"contact": doc.name}, pluck="name"):
		current = frappe.db.get_values("CRM Lead", lead, list(wanted), as_dict=True)[0]
		if any(current.get(field) != value for field, value in wanted.items()):
			frappe.db.set_value("CRM Lead", lead, wanted)


def update_deals_email_mobile_no(doc):
	linked_deals = frappe.get_all(
		"CRM Contacts",
		filters={"contact": doc.name, "is_primary": 1},
		fields=["parent"],
	)

	for linked_deal in linked_deals:
		deal = frappe.db.get_values("CRM Deal", linked_deal.parent, ["email", "mobile_no"], as_dict=True)[0]
		if deal.email != doc.email_id or deal.mobile_no != doc.mobile_no:
			frappe.db.set_value(
				"CRM Deal",
				linked_deal.parent,
				{
					"email": doc.email_id,
					"mobile_no": doc.mobile_no,
				},
			)


@frappe.whitelist()
def create_person(person: dict | str) -> dict:
	"""Add someone to the address book — which means adding a person.

	A Contact on its own belongs to nobody: no chat opens on it, the Inbox skips
	it, and a message from that number lands in a place no one looks. So an
	address book entry is created as a **lead**, which brings its contact along,
	and both names come back — the caller decides which one to open.
	"""
	if isinstance(person, str):
		person = frappe.parse_json(person)

	lead = frappe.get_doc(
		{
			"doctype": "CRM Lead",
			"salutation": person.get("salutation"),
			"first_name": person.get("first_name"),
			"last_name": person.get("last_name"),
			"gender": person.get("gender"),
			"job_title": person.get("designation"),
			"organization": person.get("company_name"),
			"image": person.get("image"),
			"email": person.get("email_id") or first_of(person.get("email_ids"), "email_id"),
			"mobile_no": person.get("mobile_no") or first_of(person.get("phone_nos"), "phone"),
			"phone": person.get("phone"),
		}
	)
	lead.insert()
	lead.reload()
	return {"lead": lead.name, "contact": lead.contact}


@frappe.whitelist()
def get_owning_lead(contact: str) -> str | None:
	"""The person whose address book entry this is, if the CRM knows them.

	Every lead now carries its own contact, so a contact almost always has an
	owner. Opening the owner instead of the contact is the whole point: the lead
	has the chat, the activity and the timeline, while the Contact page has none
	of them and reads like a second, poorer copy of the same person.

	Returns nothing for a contact nobody owns — an old record, or one made
	outside the CRM — and the caller then shows the Contact page as before.
	"""
	if not contact:
		return None

	if not frappe.has_permission("Contact", "read", contact):
		return None

	leads = frappe.get_all(
		"CRM Lead",
		filters={"contact": contact},
		pluck="name",
		order_by="creation asc",
		limit=1,
	)
	return leads[0] if leads else None


def first_of(rows, fieldname: str):
	"""The first value in one of the modal's child tables, if it sent any."""
	for row in rows or []:
		value = row.get(fieldname) if isinstance(row, dict) else getattr(row, fieldname, None)
		if value:
			return value
	return None


@frappe.whitelist()
def get_linked_deals(contact: str):
	"""Get linked deals for a contact"""

	if not frappe.has_permission("Contact", "read", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	deal_names = frappe.get_all(
		"CRM Contacts",
		filters={"contact": contact, "parenttype": "CRM Deal"},
		fields=["parent"],
		distinct=True,
	)

	# get deals data
	deals = []
	for d in deal_names:
		deal = frappe.get_cached_doc(
			"CRM Deal",
			d.parent,
			fields=[
				"name",
				"organization",
				"currency",
				"deal_value",
				"status",
				"email",
				"mobile_no",
				"deal_owner",
				"modified",
			],
		)
		deals.append(deal.as_dict())

	return deals


@frappe.whitelist()
def create_new(contact: str, field: str, value: str):
	"""Create new email or phone for a contact"""
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	contact = frappe.get_cached_doc("Contact", contact)

	if field == "email":
		email = {"email_id": value, "is_primary": 1 if len(contact.email_ids) == 0 else 0}
		contact.append("email_ids", email)
	elif field in ("mobile_no", "phone"):
		mobile_no = {"phone": value, "is_primary_mobile_no": 1 if len(contact.phone_nos) == 0 else 0}
		contact.append("phone_nos", mobile_no)
	else:
		frappe.throw(_("Invalid field"))

	contact.save()
	return True


@frappe.whitelist()
def set_as_primary(contact: str, field: str, value: str):
	"""Set email or phone as primary for a contact"""
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	contact = frappe.get_doc("Contact", contact)

	if field == "email":
		for email in contact.email_ids:
			if email.email_id == value:
				email.is_primary = 1
			else:
				email.is_primary = 0
	elif field in ("mobile_no", "phone"):
		name = "is_primary_mobile_no" if field == "mobile_no" else "is_primary_phone"
		for phone in contact.phone_nos:
			if phone.phone == value:
				phone.set(name, 1)
			else:
				phone.set(name, 0)
	else:
		frappe.throw(_("Invalid field"))

	contact.save()
	return True


@frappe.whitelist()
def search_emails(txt: str):
	doctype = "Contact"
	meta = frappe.get_meta(doctype)
	filters = [["Contact", "email_id", "is", "set"]]

	if meta.get("fields", {"fieldname": "enabled", "fieldtype": "Check"}):
		filters.append([doctype, "enabled", "=", 1])
	if meta.get("fields", {"fieldname": "disabled", "fieldtype": "Check"}):
		filters.append([doctype, "disabled", "!=", 1])

	or_filters = []
	search_fields = ["full_name", "email_id", "name"]
	if txt:
		for f in search_fields:
			or_filters.append([doctype, f.strip(), "like", f"%{txt}%"])

	results = frappe.get_list(
		doctype,
		filters=filters,
		fields=search_fields,
		or_filters=or_filters,
		limit_start=0,
		limit_page_length=20,
		order_by="email_id, full_name, name",
		ignore_permissions=False,
		as_list=True,
		strict=False,
	)

	return results
