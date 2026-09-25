# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""One event in an invoice's life. Append-only in practice: nothing rewrites it."""

from frappe.model.document import Document


class CRMInvoiceLog(Document):
	pass
