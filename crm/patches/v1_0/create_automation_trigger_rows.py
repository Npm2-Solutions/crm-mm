import frappe


def execute():
	"""Move the single trigger of existing automations into the triggers table.

	An automation can now listen to several events, each with its own filters.
	The old single field stays as a mirror of the first row, so nothing that
	reads it breaks; validate() does the move on save.
	"""
	for name in frappe.get_all("CRM Automation", pluck="name"):
		if frappe.db.exists("CRM Automation Trigger", {"parent": name, "parenttype": "CRM Automation"}):
			continue
		try:
			frappe.get_doc("CRM Automation", name).save()
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Automation {name}: trigger row not created")
