# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
import requests
from frappe import _
from frappe.model.document import Document

from crm.permissions import livelli


class CRMExotelSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		account_sid: DF.Data | None
		api_key: DF.Password | None
		api_token: DF.Password | None
		enabled: DF.Check
		record_call: DF.Check
		subdomain: DF.Data | None
		webhook_verify_token: DF.Password | None
	# end: auto-generated types

	def validate(self):
		# the keys are the agency's, and so is connecting the account: the centre
		# decides whether calls are recorded (doc 30)
		if self.has_value_changed("enabled"):
			livelli.verifica_nel_crm(
				"tecnico.integrazioni", messaggio=_("The agency connects and disconnects Exotel.")
			)
		self.verify_credentials()

	def verify_credentials(self):
		if self.enabled:
			response = requests.get(
				"https://{subdomain}/v1/Accounts/{sid}".format(
					subdomain=self.subdomain, sid=self.account_sid
				),
				auth=(self.get_password("api_key"), self.get_password("api_token")),
			)
			if response.status_code != 200:
				frappe.throw(
					_(f"Please enter valid exotel Account SID, API key & API token: {response.reason}"),
					title=_("Invalid credentials"),
				)
