# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class CRMAvailabilityException(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		date: DF.Date
		end_time: DF.Time | None
		reason: DF.Data | None
		start_time: DF.Time | None
		unavailable: DF.Check
	# end: auto-generated types

	pass
