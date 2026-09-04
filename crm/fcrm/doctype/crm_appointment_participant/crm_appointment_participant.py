# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class CRMAppointmentParticipant(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amount: DF.Currency | None
		email: DF.Data | None
		participant_name: DF.Data
		party: DF.DynamicLink | None
		party_type: DF.Literal["CRM Lead", "Contact", "CRM Deal"]
		phone: DF.Data | None
		status: DF.Literal["Booked", "Attended", "No Show", "Cancelled"]
	# end: auto-generated types

	pass
