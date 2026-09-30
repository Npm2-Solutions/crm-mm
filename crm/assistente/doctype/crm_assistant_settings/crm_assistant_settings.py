# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Where the assistant's model runs, and whether the centre uses it
(`crm.assistente`). The endpoint, the model, the key, the region and the contract
are the agency's (permlevel 1); whether to use it, the centre's."""

import frappe
from frappe import _
from frappe.model.document import Document

from crm.assistente import regole


class CRMAssistantSettings(Document):
	def validate(self):
		if not self.enabled:
			return
		mancano = regole.pronto(self.enabled, self.provider, self.base_url, self.model, self.no_retention)
		if mancano:
			frappe.throw("<br>".join(_(m) for m in mancano), title=_("The assistant cannot start yet"))
