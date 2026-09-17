# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class FacebookAd(Document):
	"""The ad that produced a lead, by name instead of by number.

	A lead arrives carrying an `ad_id` and nothing else, so the CRM could only
	say "ad 120210…" — true and useless. This is what Meta answers when asked to
	describe that ad, kept because many leads come from the same ad and the
	answer does not change between them.
	"""

	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		ad_id: DF.Data
		ad_name: DF.Data | None
		adset_name: DF.Data | None
		campaign_id: DF.Data | None
		campaign_name: DF.Data | None
		fetched_on: DF.Datetime | None
		unreadable: DF.Check
	# end: auto-generated types

	pass
