"""Show the attribution snapshots on the Data tab of existing sites.

The First Touch / Last Touch sections were added to the default Lead and Deal
Data Fields layouts in ``crm/install.py``, but that seeder is skip-if-exists — so
sites installed before lead tracking never get them and the fields stay invisible
outside the Tracking tab. This appends the missing sections to the stored layout.

Purely additive and idempotent: a layout that already carries a section is left
alone, and nothing an author arranged by hand is moved or removed.
"""

import json

import frappe

from crm.install import add_attribution_sections

TARGET_LAYOUTS = ["CRM Lead-Data Fields", "CRM Deal-Data Fields"]


def execute():
	for name in TARGET_LAYOUTS:
		if not frappe.db.exists("CRM Fields Layout", name):
			continue

		doc = frappe.get_doc("CRM Fields Layout", name)
		try:
			layout = json.loads(doc.layout or "[]")
		except (ValueError, TypeError):
			continue

		if add_attribution_sections(layout, doc.dt):
			doc.layout = json.dumps(layout)
			doc.save()
