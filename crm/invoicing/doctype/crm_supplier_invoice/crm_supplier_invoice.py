# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""An invoice somebody sent us.

Deliberately thin. The passive cycle here is a **register**, not an accounting
system: what arrived, from whom, and the original file. Matching it to an order,
approving it, posting it - none of that is this module's business, and pretending
otherwise would be building half a ledger.

The XML is the record. Every other field is a convenience the intermediary already
parsed, kept because it saves the desk a click and never because it is the truth.
"""

from __future__ import annotations

from frappe.model.document import Document


class CRMSupplierInvoice(Document):
	pass
