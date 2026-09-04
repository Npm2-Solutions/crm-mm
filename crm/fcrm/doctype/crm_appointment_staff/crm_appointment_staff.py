# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class CRMAppointmentStaff(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		required: DF.Check
		role: DF.Data | None
		status: DF.Literal["Assigned", "Confirmed", "Declined"]
		user: DF.Link
	# end: auto-generated types

	pass
