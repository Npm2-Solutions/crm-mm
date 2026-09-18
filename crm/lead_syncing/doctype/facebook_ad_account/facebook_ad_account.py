# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""One advertising account this CRM is allowed to read the spend of.

Kept as a document rather than a setting because the answer to "whose money is
this?" belongs next to the numbers: a client may run several accounts, and an
agency user can see accounts that have nothing to do with this CRM. Nothing is
read until somebody turns `sync_enabled` on.
"""

from frappe.model.document import Document


class FacebookAdAccount(Document):
	pass
