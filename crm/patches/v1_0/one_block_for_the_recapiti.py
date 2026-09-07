"""One block on the lead for the person's recapiti, not two.

A previous release put a read-only Contact section at the top of the lead's side
panel, above the Person section that already showed `email` and `mobile_no`. The
same person's details were on screen twice, and the two blocks disagreed about
how much they showed: one listed every number, the other only the primary.

The Person section now lists them all and lets them be edited, so the extra
block has nothing left to say. This removes it from the sites that received it.

Idempotent, and harmless on a site that never had it.
"""

import json

import frappe

LAYOUT = "CRM Lead-Side Panel"
SECTION = "contacts_section"


def execute():
	if not frappe.db.exists("CRM Fields Layout", LAYOUT):
		return

	doc = frappe.get_doc("CRM Fields Layout", LAYOUT)
	try:
		layout = json.loads(doc.layout or "[]")
	except (ValueError, TypeError):
		return

	kept = [section for section in layout if section.get("name") != SECTION]
	if len(kept) == len(layout):
		return

	doc.layout = json.dumps(kept)
	doc.save()
