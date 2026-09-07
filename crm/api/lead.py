import frappe
from frappe import _

DEAL_FIELDS = [
	"name",
	"organization",
	"currency",
	"deal_value",
	"status",
	"deal_owner",
	"modified",
]


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
