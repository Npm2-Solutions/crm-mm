# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""How an area user asked to hear of news besides the email (`crm.area.avvisi`):
the channel, on or off. The number is never kept here: it is the person's own,
verified each time."""

from frappe.model.document import Document


class CRMAreaNotice(Document):
	pass
