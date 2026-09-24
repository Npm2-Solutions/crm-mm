# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from crm.telephony.caller_ids import classify


class CRMCallerID(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		country: DF.Data | None
		enabled: DF.Check
		label: DF.Data | None
		last_synced_on: DF.Datetime | None
		notes: DF.SmallText | None
		number_type: DF.Literal[
			"", "Geographic", "Mobile", "Toll Free", "National", "Shared Cost", "VoIP", "Other"
		]
		phone_number: DF.Data
		provider: DF.Data | None
		routes_to_crm: DF.Check
		routing_note: DF.SmallText | None
		sip_trunk: DF.Data | None
		sip_trunk_sid: DF.Data | None
		sms_capable: DF.Check
		source: DF.Literal["Account Number", "Verified Caller ID", "Manual"]
		voice_capable: DF.Check
		voice_url: DF.SmallText | None
	# end: auto-generated types

	def before_naming(self):
		"""The row is named after the number, so the spelling has to be settled here.

		Frappe reads the name off the field before `validate` runs, and then
		`_sync_autoname_field` copies the name back over the field on every save.
		Normalising in `validate` alone was therefore undone on the way out: the
		number stayed exactly as it was typed, and `+39 02 1234 5678` could be
		listed a second time as `+390212345678`.
		"""
		self.normalise_number()

	def validate(self):
		self.normalise_number()

	def normalise_number(self):
		"""One canonical spelling, so the same number is never two rows.

		A number typed as `02 1234 5678` and the same one synced as `+390212345678`
		would otherwise both exist, and an agent would pick the one that does not work.
		"""
		if not (self.phone_number or "").strip():
			frappe.throw(_("Enter a phone number."), title=_("Number Missing"))

		facts = classify(self.phone_number)
		if not facts["number_type"]:
			# an unparseable entry would sit in the list looking usable and fail on the
			# first call; a curated list is only worth having if it is correct
			frappe.throw(
				_("{0} is not a phone number this list can use.").format(self.phone_number),
				title=_("Invalid Number"),
			)

		self.phone_number = facts["e164"]
		# the type is read from the number, never chosen: it is a fact about the
		# numbering plan, not a preference
		self.number_type = facts["number_type"]
		self.country = facts["country"]

	@property
	def display(self) -> str:
		return f"{self.label} · {self.phone_number}" if self.label else self.phone_number
