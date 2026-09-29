import frappe


def execute():
	"""Drop the unique index on the booking webhook token before the doctype sync.

	The token becomes a Password field: the column turns into `text` and holds a mask
	of asterisks, the same for every token of the same length. Frappe leaves a unique
	index alone when a column turns into text, and MariaDB keeps it as a hash index,
	so the second connection's mask would be refused as a duplicate.
	"""
	if not frappe.db.table_exists("CRM Booking Connection"):
		return
	index = frappe.db.get_column_index("tabCRM Booking Connection", "webhook_token", unique=True)
	if index:
		frappe.db.sql_ddl(f"ALTER TABLE `tabCRM Booking Connection` DROP INDEX `{index.Key_name}`")
