# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""One person, one number, one email.

A person could hold several numbers and several email addresses, with one marked
primary. It sounded harmless and it was not: every send asked which one, and
every reply asked whether it had come back on the other. The answer was worth
less than the doubt, so the CRM keeps one of each.

This collapses the entries that hold more. What is kept is the primary (or the
first row, when nothing is marked); what is dropped is **written onto the
person as a comment** before it goes, because a number somebody took the trouble
to write down is not ours to delete quietly. The person's own fields are then
aligned to what was kept.

Two people sharing one address book entry cannot be repaired by guessing, so it
is only reported: the CRM refuses to create the situation from now on.
"""

import frappe
from frappe import _


def execute():
	for contact in frappe.get_all("Contact", pluck="name"):
		collapse(contact)
	report_shared_entries()


def collapse(contact: str) -> None:
	doc = frappe.get_doc("Contact", contact)
	person = frappe.db.get_value("CRM Lead", {"contact": contact}, "name")
	dropped = []

	for table, fieldname, primary in (
		("email_ids", "email_id", "is_primary"),
		("phone_nos", "phone", "is_primary_mobile_no"),
	):
		rows = doc.get(table) or []
		if len(rows) < 2:
			continue
		keep = next((row for row in rows if row.get(primary)), rows[0])

		if table == "phone_nos" and person:
			# the landline lives on the person now, not in the address book: save
			# it there before its row goes, rather than only in a comment
			landline = next(
				(row.get(fieldname) for row in rows if row.name != keep.name and row.get("is_primary_phone")),
				None,
			)
			if landline and not frappe.db.get_value("CRM Lead", person, "phone"):
				frappe.db.set_value("CRM Lead", person, "phone", landline, update_modified=False)

		dropped += [row.get(fieldname) for row in rows if row.name != keep.name and row.get(fieldname)]
		keep.set(primary, 1)
		doc.set(table, [keep])

	if not dropped:
		return

	if person:
		remember(person, dropped)

	try:
		doc.save(ignore_permissions=True)
		frappe.db.commit()
	except Exception:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), f"Could not collapse the recapiti of {contact}")


def remember(person: str, dropped: list[str]) -> None:
	"""Park what is about to be removed where the person can still be read."""
	lines = "".join(f"<li>{frappe.utils.escape_html(value)}</li>" for value in dropped)
	try:
		frappe.get_doc("CRM Lead", person).add_comment(
			"Comment",
			_("Kept one number and one email address. Also on file until now:") + f"<ul>{lines}</ul>",
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"Could not record the old recapiti of {person}")


def report_shared_entries() -> None:
	shared = frappe.db.sql(
		"""
		SELECT contact, COUNT(name) AS people
		FROM `tabCRM Lead`
		WHERE contact IS NOT NULL AND contact != ''
		GROUP BY contact
		HAVING people > 1
		""",
		as_dict=True,
	)
	if shared:
		frappe.log_error(
			"\n".join(f"{row.contact}: {row.people} people" for row in shared),
			"Address book entries shared by more than one person",
		)
