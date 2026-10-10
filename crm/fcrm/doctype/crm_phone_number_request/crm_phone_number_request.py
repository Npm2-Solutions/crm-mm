# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A new Italian number asked of the centre's carrier (doc 52, doc 64): written
only by `crm.telephony.numeri` for Twilio and `crm.telephony.telnyx.numeri` for
Telnyx, which send the documents and follow the carrier's check. For Telnyx the
bundle is its requirement group, the documents its documents, the address its
address; it has no regulation nor end user of its own."""

from frappe.model.document import Document


class CRMPhoneNumberRequest(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		address_sid: DF.Data | None
		area_code: DF.Data | None
		bundle_sid: DF.Data | None
		details: DF.JSON | None
		document_sids: DF.SmallText | None
		email: DF.Data | None
		end_user_sid: DF.Data | None
		end_user_type: DF.Literal["business", "individual"]
		failure: DF.SmallText | None
		number_type: DF.Literal["mobile", "local", "toll_free"]
		numbers: DF.SmallText | None
		pending_orders: DF.SmallText | None
		provider: DF.Literal["twilio", "telnyx"]
		regulation_sid: DF.Data | None
		requested_by: DF.Link | None
		requested_on: DF.Datetime | None
		status: DF.Literal["Draft", "In review", "Approved", "Rejected"]
	# end: auto-generated types

	pass
