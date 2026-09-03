# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, getdate


class CRMPriceList(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		currency: DF.Link
		description: DF.SmallText | None
		enabled: DF.Check
		is_default: DF.Check
		price_list_name: DF.Data
		valid_from: DF.Date | None
		valid_upto: DF.Date | None
	# end: auto-generated types

	def validate(self):
		if self.valid_from and self.valid_upto and getdate(self.valid_from) > getdate(self.valid_upto):
			frappe.throw(_("Valid From must be on or before Valid Upto"))
		if cint(self.is_default):
			# exactly one default: claiming it takes it from whoever held it
			others = frappe.get_all(
				"CRM Price List", filters={"is_default": 1, "name": ["!=", self.name]}, pluck="name"
			)
			for other in others:
				frappe.db.set_value("CRM Price List", other, "is_default", 0)
