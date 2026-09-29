# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class CRMPlanModule(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		expires_on: DF.Date | None
		module: DF.Data
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		requested_by: DF.Link | None
		requested_on: DF.Datetime | None
		service: DF.Data | None
		source: DF.Literal["Centre", "Agency service"]
		status: DF.Literal["Active", "Trial", "Read only", "Off"]
		trial_until: DF.Date | None
	# end: auto-generated types

	pass
