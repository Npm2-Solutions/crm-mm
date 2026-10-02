# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from crm.api.doc import assigned_users_of
from crm.fcrm.doctype.crm_notification.crm_notification import nome_di
from crm.notifiche import regole as R
from crm.notifiche.avvisi import avvisa


class CRMSMSMessage(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		error_message: DF.SmallText | None
		message: DF.SmallText
		message_sid: DF.Data | None
		reference_doctype: DF.Link | None
		reference_name: DF.DynamicLink | None
		status: DF.Literal["Queued", "Sent", "Delivered", "Undelivered", "Failed", "Received"]
		telephony_medium: DF.Literal["Twilio"]
		to: DF.Data
		type: DF.Literal["Incoming", "Outgoing"]
	# end: auto-generated types

	def validate(self):
		if not self.reference_name:
			self.link_with_reference_doc()

	def link_with_reference_doc(self):
		"""Attach the message to the lead/deal that owns the counterpart number."""
		from crm.integrations.api import adopt_unknown_number, get_contact_lead_or_deal_from_number

		phone_number = self.get("from") if self.type == "Incoming" else self.to
		if not phone_number:
			return
		try:
			name, doctype = get_contact_lead_or_deal_from_number(phone_number)
			if not doctype and self.type == "Incoming":
				# nobody owns this number yet; without a lead the message would
				# be stored and never seen
				name, doctype = adopt_unknown_number(phone_number) or (None, None)
			if doctype and name:
				self.reference_doctype = doctype
				self.reference_name = name
		except Exception:
			frappe.log_error(frappe.get_traceback(), "CRM SMS: failed to resolve contact from number")

	def on_update(self):
		# nosemgrep: frappe-realtime-pick-room — Conversations.vue refreshes wherever the agent is; the payload is two ids, no text
		frappe.publish_realtime(
			"crm_sms_message",
			{
				"reference_doctype": self.reference_doctype,
				"reference_name": self.reference_name,
			},
		)
		self.notify_agents()

	def after_insert(self):
		self.run_automation_triggers()

	def run_automation_triggers(self):
		if self.type != "Incoming":
			return
		try:
			from crm.automation.engine import process_event

			process_event("sms_received", self)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "CRM SMS: automation trigger failed")

	def notify_agents(self):
		"""An SMS from a person: whoever follows them reads it in their panel; the
		ones after it, while it is unread, add to it."""
		if self.type != "Incoming" or not self.reference_doctype or not self.reference_name:
			return
		trattativa = self.reference_doctype == "CRM Deal"
		nomi = [nome_di(self.reference_doctype, self.reference_name)]
		for user in assigned_users_of(self.reference_doctype, self.reference_name):
			avvisa(
				user,
				"SMS",
				R.SMS_TRATTATIVA if trattativa else R.SMS,
				nomi,
				frase_molti=R.SMS_TRATTATIVA_MOLTI if trattativa else R.SMS_MOLTI,
				da=self.owner,
				riguarda=(self.reference_doctype, self.reference_name),
				oggetto=("CRM SMS Message", self.name),
				messaggio=self.message,
			)
