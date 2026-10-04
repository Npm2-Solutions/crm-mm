# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class CRMAppointmentParticipant(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amount: DF.Currency | None
		arrived_at: DF.Datetime | None
		email: DF.Data | None
		participant_name: DF.Data
		party: DF.DynamicLink | None
		party_type: DF.Literal["CRM Lead", "Contact", "CRM Deal"]
		phone: DF.Data | None
		status: DF.Literal["Booked", "Arrived", "Attended", "No Show", "Cancelled"]
		subscription: DF.Link | None
	# end: auto-generated types

	pass
