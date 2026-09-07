"""Show the person's address book entry on the side of an existing lead.

The Deal side panel has had a Contacts section from the start; the Lead never
did, because before every lead carried its own contact there was nothing to
show. Now there is, and the seeder in ``crm/install.py`` is skip-if-exists — so
sites installed earlier would never see it.

Purely additive and idempotent: a layout that already carries the section is
left alone, and nothing an author arranged by hand is moved or removed.
"""

import json

import frappe

LAYOUT = "CRM Lead-Side Panel"
# the name is the deal's on purpose: SidePanelLayout only renders a section
# without fields when it is called this, and this is the same idea -- who the
# person is, above what we know about them
SECTION = {"label": "Contact", "name": "contacts_section", "opened": True, "editable": False}


def execute():
	if not frappe.db.exists("CRM Fields Layout", LAYOUT):
		return

	doc = frappe.get_doc("CRM Fields Layout", LAYOUT)
	try:
		layout = json.loads(doc.layout or "[]")
	except (ValueError, TypeError):
		return

	if any(section.get("name") == SECTION["name"] for section in layout):
		return

	# first, as on the deal: who this is comes before what we know about them
	layout.insert(0, SECTION)
	doc.layout = json.dumps(layout)
	doc.save()
