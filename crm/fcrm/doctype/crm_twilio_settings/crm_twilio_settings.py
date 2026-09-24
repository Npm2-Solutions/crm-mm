# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from twilio.rest import Client

from crm.integrations.twilio.utils import get_public_url


class CRMTwilioSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		account_sid: DF.Data | None
		api_key: DF.Data | None
		api_secret: DF.Password | None
		app_name: DF.Data | None
		auth_token: DF.Password | None
		enabled: DF.Check
		record_calls: DF.Check
		recording_notice: DF.SmallText | None
		sip_trunks: DF.Code | None
		twilio_apps: DF.Data | None
		twiml_sid: DF.Data | None
		verify_webhook_signature: DF.Check
		webhook_base_url: DF.Data | None
	# end: auto-generated types

	friendly_resource_name = "Frappe CRM"  # System creates TwiML app & API keys with this name.

	def validate(self):
		old_account_sid = frappe.db.get_single_value("CRM Twilio Settings", "account_sid")
		if self.account_sid != old_account_sid:
			self.new_sid = True
		else:
			self.new_sid = False
		self.validate_twilio_account()

	def on_update(self):
		# Single doctype records are created in DB at time of installation and those field values are set as null.
		# This condition make sure that we handle null.
		if not self.account_sid:
			return

		twilio = Client(self.account_sid, self.get_password("auth_token"))
		self.set_api_credentials(twilio)
		self.set_application_credentials(twilio, self.app_name)
		self.fetch_applications()

	def validate_twilio_account(self):
		try:
			twilio = Client(self.account_sid, self.get_password("auth_token"))
			twilio.api.accounts(self.account_sid).fetch()
			return twilio
		except Exception:
			frappe.throw(_("Invalid Account SID or Auth Token."))

	def set_api_credentials(self, twilio):
		"""Generate Twilio API credentials if not exist and update them."""
		if self.api_key and self.api_secret and not self.new_sid:
			return
		new_key = self.create_api_key(twilio)
		self.api_key = new_key.sid
		self.api_secret = new_key.secret
		frappe.db.set_single_value(
			"CRM Twilio Settings",
			{"api_key": self.api_key, "api_secret": self.api_secret},
		)

	def set_application_credentials(self, twilio, app_name):
		"""Generate TwiML app credentials if not exist and update them."""
		credentials = self.get_application(twilio, app_name) or self.create_application(twilio)
		self.twiml_sid = credentials.sid
		self.app_name = credentials.friendly_name
		frappe.db.set_single_value(
			"CRM Twilio Settings", {"twiml_sid": self.twiml_sid, "app_name": self.app_name}
		)

	def create_api_key(self, twilio):
		"""Create API keys in twilio account."""
		try:
			return twilio.new_keys.create(friendly_name=self.friendly_resource_name)
		except Exception:
			frappe.log_error(title=_("Twilio API credential creation error."))
			frappe.throw(_("Twilio API credential creation error."))

	def get_twilio_voice_url(self):
		url_path = "/api/method/crm.integrations.twilio.api.voice"
		return get_public_url(url_path)

	def get_application(self, twilio, friendly_name=None):
		"""Get TwiML App from twilio account if exists."""
		friendly_name = friendly_name or self.friendly_resource_name
		applications = twilio.applications.list(friendly_name)
		default_application = twilio.applications.list(self.friendly_resource_name)

		if applications:
			return applications[0]
		if default_application:
			return default_application[0]
		return None

	def create_application(self, twilio, friendly_name=None):
		"""Create TwilML App in twilio account."""
		friendly_name = friendly_name or self.friendly_resource_name
		application = twilio.applications.create(
			voice_method="POST", voice_url=self.get_twilio_voice_url(), friendly_name=friendly_name
		)
		return application

	@frappe.whitelist()
	def fetch_applications(self):
		twilio = self.validate_twilio_account()

		if not twilio:
			frappe.throw(_("Unable to connect to Twilio account to fetch applications."))
			return

		applications = [app.friendly_name for app in twilio.applications.list()]
		frappe.db.set_single_value(
			"CRM Twilio Settings",
			"twilio_apps",
			",".join(applications),
		)

	@frappe.whitelist()
	def test_connection(self) -> dict:
		"""Prove the credentials work, and say what they reach.

		Worth its own button: without it the first sign that a key is wrong is a
		call that silently fails to connect.
		"""
		try:
			twilio = Client(self.account_sid, self.get_password("auth_token"))
			account = twilio.api.accounts(self.account_sid).fetch()
		except Exception as exc:
			return {"ok": False, "error": str(exc)[:300]}

		return {
			"ok": True,
			"account": account.friendly_name,
			"status": account.status,
			"callback_url": get_public_url("/api/method/crm.integrations.twilio.api.voice"),
		}

	@frappe.whitelist()
	def sync_caller_ids(self) -> dict:
		"""Rebuild the caller ID list from what the account really has.

		The list is a doctype rather than a string of numbers on this record, because
		each number carries facts worth keeping apart: what kind of number it is,
		whether it was verified or owned, which trunk has taken it, and whether a
		call to it reaches this CRM at all.
		"""
		from crm.telephony import caller_ids

		return caller_ids.sync("twilio")

	@frappe.whitelist()
	def fetch_sip_trunks(self) -> list[dict]:
		"""Read the account's Elastic SIP trunks and remember them for display."""
		from crm.telephony import providers

		trunks = providers.get("twilio").list_sip_trunks()
		frappe.db.set_single_value("CRM Twilio Settings", "sip_trunks", frappe.as_json(trunks))
		return trunks

	@frappe.whitelist()
	def verify_caller_id(self, phone_number: str, label: str | None = None) -> dict:
		"""Start Twilio's verification for a number the practice owns elsewhere.

		Twilio rings the number and the person answering types the code. That is the
		legitimate way to present a line you did not buy here — and the only one:
		presenting a number you cannot prove you control is spoofing.
		"""
		from crm.telephony import providers

		if not phone_number:
			frappe.throw(_("Enter the number to verify."))
		return providers.get("twilio").start_caller_id_verification(phone_number, label)

	def usable_caller_ids(self) -> list[str]:
		"""Every number this account may present, owned or verified."""
		from crm.telephony import caller_ids

		return caller_ids.usable_for_outbound("twilio")
