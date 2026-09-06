# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class CRMTrackingEvent(Document):
	"""One thing a visitor did: a page read, a form sent, a link clicked.

	Page views and conversions share a table on purpose — the journey a salesperson
	wants to read is a single chronological stream ("landed on /prezzi, read the
	case study, then booked"), not two lists to merge in the UI.
	"""

	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		deal: DF.Link | None
		duration: DF.Int
		event_type: DF.Literal[
			"Page View",
			"Form View",
			"Form Submitted",
			"Link Clicked",
			"Booking",
			"Call",
			"Identified",
			"Custom",
		]
		label: DF.Data | None
		lead: DF.Link | None
		metadata: DF.SmallText | None
		occurred_on: DF.Datetime
		path: DF.Data | None
		reference_doctype: DF.Link | None
		reference_name: DF.DynamicLink | None
		referrer: DF.SmallText | None
		session: DF.Link | None
		url: DF.SmallText | None
		visitor: DF.Link | None
	# end: auto-generated types
