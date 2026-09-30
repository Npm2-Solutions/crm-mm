# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""How the centre runs its waiting lists: to how many a place goes at once, how
long they have to answer, where one joins, and the channels besides the email
(`crm.scheduling.attese`)."""

import frappe
from frappe import _
from frappe.model.document import Document

from crm.scheduling import attese_regole as R


class CRMWaitingListSettings(Document):
	def validate(self):
		self.offers_at_once = R.entro(self.offers_at_once, R.PER_VOLTA)
		self.hours_to_answer = R.entro(self.hours_to_answer, R.ORE_PER_RISPONDERE)
		self.days_ahead = R.entro(self.days_ahead, R.GIORNI_AVANTI)
		self.default_until_days = R.entro(self.default_until_days, R.GIORNI_IN_LISTA)
		self.min_notice_hours = max(int(self.min_notice_hours or 0), 0)
		if self.whatsapp_template and not (
			frappe.db.exists("DocType", "WhatsApp Templates")
			and frappe.db.exists("WhatsApp Templates", self.whatsapp_template)
		):
			frappe.throw(_("This WhatsApp template does not exist"))
		if (self.sms_number or "").strip():
			from crm.utils import to_e164

			# a number it cannot read comes back as it was written: only E.164 is kept
			numero = to_e164(self.sms_number)
			if not numero.startswith("+"):
				frappe.throw(_("Write the SMS number with its prefix, like +39…"))
			self.sms_number = numero
		else:
			self.sms_number = None
