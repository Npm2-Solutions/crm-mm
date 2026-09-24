# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class CRMBookingPlatformBlock(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		appointment: DF.Link | None
		connection: DF.Link
		ends_on: DF.Datetime | None
		error: DF.SmallText | None
		external_block_id: DF.Data | None
		staff: DF.Link | None
		starts_on: DF.Datetime | None
		status: DF.Literal["Active", "Removed", "Failed"]
	# end: auto-generated types

	pass
