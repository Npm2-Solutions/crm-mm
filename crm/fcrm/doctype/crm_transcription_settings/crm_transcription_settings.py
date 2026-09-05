# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from urllib.parse import urlparse

import frappe
from frappe import _
from frappe.model.document import Document


class CRMTranscriptionSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		api_key: DF.Password | None
		auto_transcribe: DF.Check
		base_url: DF.Data | None
		enabled: DF.Check
		language: DF.Data | None
		max_recording_mb: DF.Int
		model: DF.Data | None
		prompt: DF.SmallText | None
		recording_retention_days: DF.Int
		request_timeout: DF.Int
		transcript_retention_days: DF.Int
	# end: auto-generated types

	def validate(self):
		self.validate_endpoint()
		self.clamp_numbers()

	def validate_endpoint(self):
		if not self.enabled:
			return
		if not self.base_url:
			frappe.throw(
				_("Set the endpoint that will transcribe the recordings."), title=_("Endpoint Missing")
			)
		parsed = urlparse(self.base_url.rstrip("/"))
		if parsed.scheme not in ("http", "https") or not parsed.hostname:
			frappe.throw(_("The base URL must be a full http or https address."), title=_("Invalid URL"))
		if parsed.scheme == "http" and parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
			# recordings are personal data; in a health practice they are a special
			# category, so they do not travel to another host in the clear
			frappe.throw(
				_("Use https for a remote endpoint. Plain http is only allowed for a local one."),
				title=_("Insecure Endpoint"),
			)
		if not self.model:
			frappe.throw(_("Set the transcription model."), title=_("Model Missing"))

	def clamp_numbers(self):
		for field in ("transcript_retention_days", "recording_retention_days"):
			if self.get(field) and self.get(field) < 0:
				self.set(field, 0)
		if self.max_recording_mb is not None and self.max_recording_mb < 1:
			self.max_recording_mb = 1
		if self.request_timeout is not None and self.request_timeout < 10:
			self.request_timeout = 10
