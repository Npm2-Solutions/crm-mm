# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A report given to the patient (`crm.clinica.consegna`): by hand, to whom; or
online, until when, how many times it was downloaded. Kept: it is the proof of
the delivery, with its events in the audit log."""

import frappe
from frappe import _
from frappe.model.document import Document


class ClinicReportDelivery(Document):
	def on_trash(self):
		frappe.throw(_("A delivery is kept: it proves what was given, and to whom"))
