# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class CRMDemoRecord(Document):
	"""One record the demo data made (crm/demo/registro.py): written only by the
	demo, read when they are taken away."""


def on_doctype_update():
	import frappe

	# asked by doctype and name together: is this record one of the demo's?
	frappe.db.add_index("CRM Demo Record", ["ref_doctype", "ref_name"])
