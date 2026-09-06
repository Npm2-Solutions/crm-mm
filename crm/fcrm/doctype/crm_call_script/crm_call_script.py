# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CRMCallScript(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from crm.fcrm.doctype.crm_call_script_step.crm_call_script_step import CRMCallScriptStep

		description: DF.SmallText | None
		enabled: DF.Check
		idx_hint: DF.Int
		script_name: DF.Data
		service: DF.Link | None
		steps: DF.Table[CRMCallScriptStep]
	# end: auto-generated types

	def validate(self):
		if not self.steps:
			frappe.throw(_("A script with no steps has nothing to show during a call."), title=_("No Steps"))
