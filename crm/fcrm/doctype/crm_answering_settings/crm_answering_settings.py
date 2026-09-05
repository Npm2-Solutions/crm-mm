# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CRMAnsweringSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		after_hours_greeting_audio: DF.Attach | None
		after_hours_greeting_text: DF.SmallText | None
		answer_mode: DF.Literal["Always Answering Service", "Ring Agents First"]
		callback_hours: DF.Int
		dedupe_window_hours: DF.Int
		enabled: DF.Check
		greeting_audio: DF.Attach | None
		greeting_source: DF.Literal["Text to Speech", "Audio File"]
		greeting_text: DF.SmallText | None
		language: DF.Data | None
		max_callback_attempts: DF.Int
		retry_after_hours: DF.Int
		use_working_hours: DF.Check
		voice: DF.Literal["alice", "man", "woman", "Polly.Bianca", "Polly.Carla", "Polly.Giorgio"]
	# end: auto-generated types

	def validate(self):
		self.validate_audio_is_present()
		self.clamp_numbers()

	def validate_audio_is_present(self):
		"""An audio announcement with no file would answer the call with silence."""
		if not self.enabled or self.greeting_source != "Audio File":
			return
		if not self.greeting_audio:
			frappe.throw(
				_("Upload the announcement audio, or switch the source back to text to speech."),
				title=_("Announcement Missing"),
			)
		if self.use_working_hours and not self.after_hours_greeting_audio:
			# closed hours fall back to the open-hours file rather than to silence, but
			# say so explicitly instead of letting it surprise whoever configured it
			frappe.msgprint(
				_("No closed-hours audio set — callers outside working hours hear the open-hours one."),
				indicator="orange",
				alert=True,
			)

	def clamp_numbers(self):
		for field in ("callback_hours", "dedupe_window_hours", "max_callback_attempts", "retry_after_hours"):
			if self.get(field) and self.get(field) < 0:
				self.set(field, 0)
		if self.enabled and not self.callback_hours:
			frappe.throw(_("Set how soon callers are promised a callback."), title=_("Callback Time Missing"))


@frappe.whitelist()
def is_enabled() -> bool:
	return bool(frappe.db.get_single_value("CRM Answering Settings", "enabled"))
