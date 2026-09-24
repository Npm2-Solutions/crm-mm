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


# A deal that is neither won nor lost is the conversation still in progress.
CLOSED_DEAL_TYPES = ("Won", "Lost")


def open_deal_of(person: str) -> str | None:
	"""The deal this person has in progress, if any -- most recent first."""
	names = deal_names_of(person)
	if not names:
		return None

	for deal in frappe.get_all(
		"CRM Deal",
		filters={"name": ["in", list(names)]},
		fields=["name", "status"],
		order_by="modified desc",
	):
		if not deal.status:
			return deal.name
		if frappe.get_cached_value("CRM Deal Status", deal.status, "type") not in CLOSED_DEAL_TYPES:
			return deal.name
	return None


def open_deal_for_inquiry(person: str, source: str | None = None) -> str | None:
	"""The deal an inquiry belongs to: the one already open, or a new one.

	The sale has one scale of states and it lives here. A person does not carry
	a stage of their own -- they are a person, not a step -- so an inquiry that
	is worth working has to open a deal, or it lands in no pipeline and nobody
	sees it.

	Not a second one while the first is open: two boards for the same
	conversation is how a customer gets called twice about the same thing. But
	once the last one closed -- won a year ago, lost in spring -- somebody
	coming back is a *new* sale, with its own stage, its own response clock and
	its own outcome. Collapsing that into the old deal is what the single
	permanent status used to do, and it is the reason a customer who returned
	stayed marked Lost.

	Silent on failure by design: this is called from webhooks and public form
	submissions, and a person who reached us must be saved even if the deal
	cannot be.
	"""
	if not person:
		return None

	existing = open_deal_of(person)
	if existing:
		return existing

	try:
		person_doc = frappe.get_cached_doc("CRM Lead", person)
		deal = frappe.new_doc("CRM Deal")
		deal.lead = person
		deal.organization = person_doc.organization
		deal.source = source or person_doc.source
		deal.deal_owner = person_doc.lead_owner
		if person_doc.contact:
			deal.append("contacts", {"contact": person_doc.contact, "is_primary": 1})

		# where the person came from is where this deal came from, and converting
		# by hand has always copied it. Not decoration: `stamp_manual_source`
		# claims for "CRM UI" any record created by a signed-in user that nothing
		# else has claimed -- and the hourly Meta reconciliation runs as one, so a
		# deal born from an ad would otherwise report as typed into the CRM.
		from crm.api.tracking import snapshot_fieldnames

		deal.visitor = person_doc.visitor
		for fieldname in snapshot_fieldnames():
			deal.set(fieldname, person_doc.get(fieldname))
		# no status: the deal controller puts it in the first stage of the
		# default pipeline, which is the one place that decides where a sale starts
		#
		# and no forecast: with `enable_forecasting` on, the deal controller
		# requires an expected value and a closing date, which nobody can supply
		# from a webhook. Refused, it would be swallowed below and the sale would
		# exist in no pipeline at all.
		deal.flags.from_inquiry = True
		deal.insert(ignore_permissions=True)

		# `converted` is read as "has a deal" -- the quick filter says so
		frappe.db.set_value("CRM Lead", person, "converted", 1, update_modified=False)
		return deal.name
	except Exception:
		frappe.log_error(
			title="Could not open a deal for an inquiry",
			message=f"person: {person}\n\n{frappe.get_traceback()}",
		)
		return None


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
