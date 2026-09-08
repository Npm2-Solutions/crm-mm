import frappe
from frappe import _

from crm.utils import to_e164

DEAL_FIELDS = [
	"name",
	"organization",
	"currency",
	"deal_value",
	"status",
	"deal_owner",
	"modified",
]


def find_person(email: str | None = None, phone: str | None = None) -> str | None:
	"""The person behind an email address or a phone number — deal or no deal.

	Looking them up with `converted = 0` was the bug: a customer who comes back
	(books again, fills another form, writes again) already has a deal, so the
	lookup missed them and a second person was born for the same human being.
	In Salesforce a converted lead is frozen history and there is a Contact to
	find instead; here the person record IS the person and stays, so there is
	nothing to exclude.

	The address book is searched too: the second email address and the second
	number of somebody are rows on their Contact, not fields on the person.
	"""
	email = (email or "").strip()
	if email:
		person = frappe.db.get_value("CRM Lead", {"email": email}, "name", order_by="modified desc")
		if person:
			return person
		for contact in frappe.get_all(
			"Contact Email", filters={"email_id": email, "parenttype": "Contact"}, pluck="parent"
		):
			person = frappe.db.get_value("CRM Lead", {"contact": contact}, "name")
			if person:
				return person

	number = to_e164(phone)
	if number:
		for fieldname in ("mobile_no", "phone"):
			person = frappe.db.get_value("CRM Lead", {fieldname: number}, "name", order_by="modified desc")
			if person:
				return person
		for contact in frappe.get_all(
			"Contact Phone", filters={"phone": number, "parenttype": "Contact"}, pluck="parent"
		):
			person = frappe.db.get_value("CRM Lead", {"contact": contact}, "name")
			if person:
				return person
	return None


def deal_names_of(lead: str) -> set[str]:
	"""This person's deals, found both ways they can be tied to them.

	A deal names the lead it was opened from, and it also lists the person among
	its contacts. The two do not always agree — a deal made before that link
	existed has only the second — and a deal missed here is a conversation
	nobody can read any more.
	"""
	names = set(frappe.get_all("CRM Deal", filters={"lead": lead}, pluck="name"))

	contact = frappe.db.get_value("CRM Lead", lead, "contact")
	if contact:
		names.update(
			frappe.get_all(
				"CRM Contacts",
				filters={"contact": contact, "parenttype": "CRM Deal"},
				pluck="parent",
			)
		)
	return names


@frappe.whitelist()
def get_deals(lead: str) -> list[dict]:
	"""The relationships this person has with us — none, one, or several.

	A lead is not something that turns into a deal and then stops existing: the
	person stays, and the deals come and go. Showing them on the lead is what
	makes that true on screen instead of only in the database.

	Two ways in, because they do not always agree: a deal names the lead it was
	opened from, and it also lists the person among its contacts — a deal made
	straight from the address book has the second and not the first.
	"""
	if not frappe.has_permission("CRM Lead", "read", lead):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	names = deal_names_of(lead)
	if not names:
		return []

	# get_list, not get_all: a deal this user is not allowed to see must not
	# appear just because the person is theirs
	return frappe.get_list(
		"CRM Deal",
		filters={"name": ["in", list(names)]},
		fields=DEAL_FIELDS,
		order_by="modified desc",
	)


@frappe.whitelist()
def get_contact_details(lead: str) -> dict:
	"""This person's address book entry, in the shape the side panel edits.

	The lead's `email` and `mobile_no` show only the primary ones. Handing the
	whole entry over lets the same control the Contact page uses list every
	number and every address, and add, correct or promote one — so there is a
	single block for the recapiti instead of two saying different halves of the
	same thing.
	"""
	if not frappe.has_permission("CRM Lead", "read", lead):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	contact = frappe.db.get_value("CRM Lead", lead, "contact")
	if not contact or not frappe.has_permission("Contact", "read", contact):
		return {}

	doc = frappe.get_doc("Contact", contact)
	return {
		"name": doc.name,
		"email_id": doc.email_id,
		"mobile_no": doc.mobile_no,
		"email_ids": [{"name": row.name, "email_id": row.email_id} for row in doc.email_ids if row.email_id],
		"phone_nos": [{"name": row.name, "phone": row.phone} for row in doc.phone_nos if row.phone],
	}
