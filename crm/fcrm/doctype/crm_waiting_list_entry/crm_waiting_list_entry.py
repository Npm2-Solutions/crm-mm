# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Somebody waiting for a service, or for a seat in a class that is full, and
what was offered to them (`crm.scheduling.attese`)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, getdate

from crm.scheduling import attese_regole as R

#: More places than this in one entry are a group, not a person and their guests.
MASSIMO_POSTI = 20


class CRMWaitingListEntry(Document):
	def validate(self):
		self.seats = cint(self.seats) or 1
		if not 1 <= self.seats <= MASSIMO_POSTI:
			frappe.throw(_("An entry waits for 1 to {0} places").format(MASSIMO_POSTI))
		if self.from_date and self.until and getdate(self.until) < getdate(self.from_date):
			frappe.throw(_("The last day comes after the first"))
		if self.channel not in R.CANALI:
			self.channel = R.EMAIL
		if self.contact == self.lead:
			self.contact = None
		self.chi_la_fa()
		self.quale_lezione()
		self.una_sola()

	def chi_la_fa(self):
		"""The professional asked for does the service."""
		if not self.staff:
			return
		if not frappe.db.exists(
			"CRM Service Staff", {"parenttype": "CRM Service", "parent": self.service, "user": self.staff}
		):
			frappe.throw(_("{0} does not do this service").format(frappe.utils.get_fullname(self.staff)))

	def quale_lezione(self):
		"""A seat in a class: one of this service, still to happen."""
		if not self.class_session:
			return
		riga = frappe.db.get_value("CRM Appointment", self.class_session, ["service", "status"], as_dict=True)
		if not riga or riga.service != self.service:
			frappe.throw(_("The class is of another service"))
		if cint(frappe.db.get_value("CRM Service", self.service, "max_participants")) <= 1:
			frappe.throw(_("{0} is not a class: wait for the service instead").format(self.service))
		if self.is_new() and riga.status not in R.ATTIVI:
			frappe.throw(_("This class is not going ahead"))

	def una_sola(self):
		"""One entry per person and service (and class) in the line: joining again
		changes it."""
		if self.status not in R.APERTE:
			return
		altra = frappe.db.get_value(
			self.doctype,
			{
				"name": ("!=", self.name or ""),
				"lead": self.lead,
				"service": self.service,
				"class_session": self.class_session or ("is", "not set"),
				"status": ("in", R.APERTE),
			},
			"name",
		)
		if altra:
			frappe.throw(_("{0} is on this waiting list already").format(self.lead_name or self.lead))
