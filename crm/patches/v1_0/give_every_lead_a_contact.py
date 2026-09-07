import frappe

from crm.utils import digits_of

CHUNK = 200


def execute():
	"""One person, one record, and their details in one place.

	Until now the conversion copied the person into a second record and nothing
	kept the two in step. This walks what is already on the site: a lead without
	a contact gets one; where the two disagree the contact wins, and the value
	the lead loses is kept as another way to reach the person instead of being
	dropped; a contact nobody owns gets the lead it never had.

	Every step checks before it acts, so an interrupted run — and on a large site
	there will be one — can simply be run again.
	"""
	if not frappe.db.has_column("CRM Lead", "contact"):
		# the field arrives with this same release; nothing to reconcile before it
		return

	give_leads_their_contact()
	adopt_orphan_contacts()


def give_leads_their_contact() -> None:
	names = frappe.get_all("CRM Lead", filters={"contact": ["in", ["", None]]}, pluck="name")
	for index, name in enumerate(names, start=1):
		try:
			lead = frappe.get_doc("CRM Lead", name)
			lead.ensure_contact()
			lead.reload()
			if lead.contact:
				keep_what_the_lead_knew(lead)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Patch: no contact for lead {name}")
		if index % CHUNK == 0:
			frappe.db.commit()
	frappe.db.commit()


def keep_what_the_lead_knew(lead) -> None:
	"""Where the two copies disagree, the contact wins — but nothing is thrown away.

	The contact is what email and telephony have been using all along, so it is
	the one to trust. The lead's own number, though, is a number somebody once
	wrote down for this person: it becomes another row rather than a deleted
	value, and stays reachable.
	"""
	contact = frappe.get_doc("Contact", lead.contact)
	known_numbers = {digits_of(row.phone) for row in contact.phone_nos}
	known_emails = {(row.email_id or "").strip().lower() for row in contact.email_ids}
	added = False

	for number in (lead.mobile_no, lead.phone):
		if number and digits_of(number) not in known_numbers:
			contact.append("phone_nos", {"phone": number})
			known_numbers.add(digits_of(number))
			added = True

	if lead.email and lead.email.strip().lower() not in known_emails:
		contact.append("email_ids", {"email_id": lead.email})
		added = True

	if added:
		contact.save(ignore_permissions=True)

	# and now the lead reads what the contact says
	frappe.db.set_value(
		"CRM Lead",
		lead.name,
		{
			"email": contact.email_id or lead.email,
			"mobile_no": contact.mobile_no or lead.mobile_no,
			"phone": contact.get("phone") or lead.phone,
		},
		update_modified=False,
	)


def adopt_orphan_contacts() -> None:
	"""A contact that belongs to nobody becomes a person.

	Only the ones tied to nothing at all: a contact on a deal is already
	reachable through it, and turning those into leads would fill the leads list
	with people who are customers already.
	"""
	owned = set(frappe.get_all("CRM Lead", filters={"contact": ["is", "set"]}, pluck="contact"))
	on_a_deal = set(frappe.get_all("CRM Contacts", filters={"parenttype": "CRM Deal"}, pluck="contact"))

	names = frappe.get_all("Contact", pluck="name")
	for index, name in enumerate(names, start=1):
		if name in owned or name in on_a_deal:
			continue
		try:
			make_lead_for(name)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Patch: no lead for contact {name}")
		if index % CHUNK == 0:
			frappe.db.commit()
	frappe.db.commit()


def make_lead_for(name: str) -> None:
	contact = frappe.get_doc("Contact", name)
	if not (contact.first_name or contact.last_name or contact.email_id or contact.mobile_no):
		# nothing to call, nothing to write to, nothing to name it by
		return

	lead = frappe.get_doc(
		{
			"doctype": "CRM Lead",
			"first_name": contact.first_name or contact.email_id or contact.mobile_no,
			"last_name": contact.last_name,
			"email": contact.email_id,
			"mobile_no": contact.mobile_no,
			"phone": contact.get("phone"),
			"organization": contact.company_name,
			"contact": name,
		}
	)
	# the lead already carries its contact, so `ensure_contact` leaves it alone
	# and no second copy of the person is made
	lead.insert(ignore_permissions=True)
