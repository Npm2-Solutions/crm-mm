import frappe
from frappe import _

from crm.utils import to_e164


def validate(doc, method):
	normalise_numbers(doc)
	keep_one_of_each(doc)
	update_deals_email_mobile_no(doc)
	update_leads_email_mobile_no(doc)


def keep_one_of_each(doc):
	"""One number and one email per person — decided, not discovered.

	A second number is a second question at every send (which one? and was the
	reply on the other?) and the answer was worth less than the doubt. The CRM's
	own screens no longer offer adding one; this is the guard for everything else
	(the Desk, an import, a script), so the rule holds wherever the entry is
	edited from.

	What is kept is the primary, or the first row when nothing is marked — never
	nothing, because dropping every row would take the person's number away.
	"""
	for table, primary in (("email_ids", "is_primary"), ("phone_nos", "is_primary_mobile_no")):
		rows = doc.get(table) or []
		if len(rows) < 2:
			continue
		keep = next((row for row in rows if row.get(primary)), rows[0])
		keep.set(primary, 1)
		doc.set(table, [keep])


def normalise_numbers(doc):
	"""Every number written the one way that cannot be misread.

	`370 340 0189` is a number only if you already know which country it belongs
	to; the same person is then `+39 370 340 0189` in the chat, and the two look
	like two people to anything that compares them — which is exactly how an
	Italian number came to be read as Indian. Storing E.164, prefix and all,
	takes the guess out of every later comparison and out of what the user reads.

	It runs before the copies go out to the leads and the deals, so they get the
	unambiguous form too. A number the library cannot make sense of is left as
	somebody wrote it: guessing a prefix would be worse than saying nothing.
	"""
	for row in doc.phone_nos or []:
		row.phone = to_e164(row.phone) or row.phone

	# these are filled from the rows by the Contact controller, which has already
	# run by the time this hook does
	doc.mobile_no = to_e164(doc.mobile_no) or doc.mobile_no
	doc.phone = to_e164(doc.phone) or doc.phone


def update_leads_email_mobile_no(doc):
	"""A lead's recapiti follow its contact, the way a deal's already do.

	The contact is where a person's numbers live; the fields on the lead are a
	copy kept for everything that reads `lead.mobile_no`. Without this the copy
	goes stale the moment somebody edits the number in the address book, which is
	precisely how the two came to disagree before they were tied together.
	"""
	# the landline is not an address book entry: it lives on the person and
	# nowhere else, so it is not copied back from here (it would be copied as
	# empty, and clear what somebody typed)
	wanted = {
		"email": doc.email_id,
		"mobile_no": doc.mobile_no,
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
