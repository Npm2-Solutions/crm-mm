# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class CRMServiceResource(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		quantity: DF.Int
		required: DF.Check
		resource: DF.Link | None
		resource_type: DF.Literal["", "Room", "Equipment", "Vehicle", "Other"]
	# end: auto-generated types

	pass
