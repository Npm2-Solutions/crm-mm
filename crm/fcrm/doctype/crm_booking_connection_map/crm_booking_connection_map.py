# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class CRMBookingConnectionMap(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		external_id: DF.Data
		external_name: DF.Data | None
		map_type: DF.Literal["Service", "Staff", "Resource"]
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		resource: DF.Link | None
		service: DF.Link | None
		staff: DF.Link | None
	# end: auto-generated types

	pass
