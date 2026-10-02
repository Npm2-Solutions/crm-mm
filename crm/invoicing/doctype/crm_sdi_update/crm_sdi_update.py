# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""One update Itala gave us: kept before it is applied, because Itala gives each
update once - read, it is gone - and one that fails to apply must be tried again,
not lost (`crm.invoicing.sdi.riconciliazione`). Once applied it keeps only what
identifies it: a supplier's invoice is not kept twice."""

from frappe.model.document import Document


class CRMSdIUpdate(Document):
	pass
