# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class CRMLeadFacebookSubmission(Document):
	"""One lead-ad form filled in by this person.

	The person is unique, the submissions are not: the same human being can
	answer two ads, or the same ad twice. Keeping them here is what lets the
	import find the person instead of making a second one, and still stay
	idempotent — Meta re-delivers, and the hourly reconciliation re-reads the
	last two days of every form.
	"""

	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		form: DF.Data | None
		form_name: DF.Data | None
		leadgen_id: DF.Data | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		platform: DF.Data | None
		submitted_on: DF.Datetime | None
	# end: auto-generated types

	pass
