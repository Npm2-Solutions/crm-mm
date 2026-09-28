# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The Sistema TS submissions get the module they live in.

When the Sistema TS moved out of invoicing into `crm/tessera_sanitaria`, its one
doctype went with it but kept saying `"module": "Invoicing"`, and no «Tessera
Sanitaria» module was ever declared. Frappe looks for a doctype in its module's
folder, so it looked in `crm/invoicing/doctype/` and found nothing: a new site
never got the table, and the Invoices page answered 500 wherever it asked how
the year's submissions stood.

The module is declared now, and a migrate on a fresh cache creates it. This
makes the same happen on a site whose cache still holds the old list of
modules — which is every site being updated, until the cache is cleared — by
reading the doctype from the path where it is rather than from where the module
map says it should be.
"""

import frappe
from frappe.modules.import_file import import_file_by_path

MODULE = "Tessera Sanitaria"


def execute():
	if not frappe.db.exists("Module Def", MODULE):
		frappe.get_doc({"doctype": "Module Def", "module_name": MODULE, "app_name": "crm"}).insert(
			ignore_permissions=True
		)
	path = frappe.get_app_path(
		"crm", "tessera_sanitaria", "doctype", "crm_ts_submission", "crm_ts_submission.json"
	)
	import_file_by_path(path, force=True, ignore_version=True)
	frappe.clear_cache(doctype="CRM TS Submission")
