# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""N sessions of one service for one person: ten of physiotherapy, six of laser
(`crm.scheduling.cicli`). Its appointments point to it; it counts them."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, getdate

from crm.scheduling import cicli
from crm.scheduling import cicli_regole as C


class CRMSessionCycle(Document):
	def validate(self):
		if not 1 <= cint(self.sessions) <= C.MAX_SEDUTE:
			frappe.throw(_("A cycle has from 1 to {0} sessions").format(C.MAX_SEDUTE))
		if self.valid_until and getdate(self.valid_until) < getdate(self.starts_on):
			frappe.throw(_("A cycle ends after it starts"))
		if self.billing == cicli.INTERO and not flt(self.price):
			frappe.throw(_("A cycle paid as a whole has its price"))
		if not self.currency:
			self.currency = frappe.db.get_value("CRM Service", self.service, "currency") or "EUR"
		self.resta_di_chi_e()

	def resta_di_chi_e(self):
		"""Once an appointment is in it, the cycle stays of its person and service."""
		if self.is_new():
			return
		prima = self.get_doc_before_save()
		if (
			prima
			and (prima.lead != self.lead or prima.service != self.service)
			and frappe.db.exists(cicli.APPUNTAMENTO, {"session_cycle": self.name})
		):
			frappe.throw(_("The person and the service do not change once sessions are booked"))

	def on_trash(self):
		cicli.al_cestino(self)
