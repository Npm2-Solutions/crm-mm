import frappe

from crm.integrations.meta.client import GRAPH_BASE, GRAPH_VERSION


def execute():
	"""Give the already connected WhatsApp accounts an endpoint to send to.

	`frappe_whatsapp` composes every call as f"{url}/{version}/{phone_id}/messages",
	and the accounts we created before this patch have neither field set: the
	request was never issued, and sending failed on the error of a request that
	does not exist, "'NoneType' object has no attribute 'json'".
	"""
	if not frappe.db.table_exists("WhatsApp Account"):
		return

	meta = frappe.get_meta("WhatsApp Account")
	defaults = {"url": GRAPH_BASE, "version": GRAPH_VERSION}
	fields = [field for field in defaults if meta.has_field(field)]
	if not fields:
		return

	for name in frappe.get_all("WhatsApp Account", pluck="name"):
		for field in fields:
			if not frappe.db.get_value("WhatsApp Account", name, field):
				frappe.db.set_value("WhatsApp Account", name, field, defaults[field], update_modified=False)
