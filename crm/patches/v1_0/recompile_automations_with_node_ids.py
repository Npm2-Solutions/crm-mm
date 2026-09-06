import frappe


def execute():
	"""Give the steps of existing automations their ids, and recompile.

	The visual editor addresses nodes by id and maps the step log back onto
	them; automations saved before the ids existed would show no statistics
	until someone opened and saved them by hand.
	"""
	for name in frappe.get_all("CRM Automation", pluck="name"):
		try:
			doc = frappe.get_doc("CRM Automation", name)
			doc.save()  # validate() assigns the ids and recompiles the program
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Automation {name} could not be recompiled")
