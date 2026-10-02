# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""DottorCloud no longer connects to ERPNext (02/10/2026).

What the integration left on a site goes with it: its settings, with the remote
site's API key and secret, the products sync's open issues, the fields it added to
deals and products (and to ERPNext's items, quotations and customers where ERPNext
sat on the same site), and the form script that made a quotation from a deal.
Deleting a field leaves its column: what it held stays in the database.
"""

import frappe

IMPOSTAZIONI = "ERPNext CRM Settings"
PROBLEMI = "CRM Product Sync Issue"
SCRIPT = "Create Quotation from CRM Deal"
CAMPI = (
	("CRM Deal", "erpnext_customer"),
	("CRM Product", "erpnext_item_code"),
	("Item", "crm_product_code"),
	("Quotation", "crm_deal"),
	("Customer", "crm_deal"),
)


def execute():
	for doctype, fieldname in CAMPI:
		for nome in frappe.get_all("Custom Field", {"dt": doctype, "fieldname": fieldname}, pluck="name"):
			frappe.delete_doc("Custom Field", nome, force=True, ignore_permissions=True)

	if frappe.db.exists("CRM Form Script", SCRIPT):
		frappe.delete_doc("CRM Form Script", SCRIPT, force=True, ignore_permissions=True)

	# the settings before their table of issues, which they hold
	for doctype in (IMPOSTAZIONI, PROBLEMI):
		if frappe.db.exists("DocType", doctype):
			frappe.delete_doc("DocType", doctype, force=True, ignore_missing=True, ignore_permissions=True)
		frappe.db.delete("Custom DocPerm", {"parent": doctype})
		frappe.db.delete("Property Setter", {"doc_type": doctype})

	# what a single keeps outside its DocType: its values and its passwords
	frappe.db.delete("Singles", {"doctype": IMPOSTAZIONI})
	frappe.db.delete("__Auth", {"doctype": IMPOSTAZIONI})

	# a table drop commits: only where there is one
	if frappe.db.table_exists(PROBLEMI, cached=False):
		frappe.db.sql_ddl("DROP TABLE `tabCRM Product Sync Issue`")
