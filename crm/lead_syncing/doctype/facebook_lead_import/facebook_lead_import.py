# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class FacebookLeadImport(Document):
	"""One lead-ad submission this CRM has already taken in.

	Deleting the person it produced used to invite it straight back: the import
	asked "does a lead carry this leadgen id?", the answer was no, and the
	hourly reconciliation — which re-reads the last two days of every form —
	imported it again within the hour. Whether a submission was already handled
	is a fact about the import, not about a record somebody may since have
	deleted, so it is kept here and outlives the person.
	"""

	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		deleted_on: DF.Datetime | None
		form: DF.Data | None
		form_name: DF.Data | None
		imported_on: DF.Datetime | None
		lead: DF.Data | None
		leadgen_id: DF.Data
		outcome: DF.Literal["Created", "Merged"]
		platform: DF.Data | None
	# end: auto-generated types

	pass
