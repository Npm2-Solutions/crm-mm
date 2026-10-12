# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.query_builder import Interval
from frappe.query_builder.functions import Now


class CRMEventReminder(Document):
	"""An event's reminder that left by email (`crm.api.event`): written by the
	round alone, before the email leaves, and named by its key - the event, which
	of its reminders, to whom, by which way, for which time - so the database takes
	it once and a second round finds it there."""

	def autoname(self):
		from crm.api.event import nome_del_promemoria

		self.name = nome_del_promemoria(
			self.event, self.reminder, self.recipient, self.channel, self.starts_on
		)

	@staticmethod
	def clear_old_logs(days=90):
		"""Log Settings' retention: the reminders of an event that started longer ago
		than this go - no round looks at it again, unless it is still under way."""
		tabella = frappe.qb.DocType("CRM Event Reminder")
		frappe.db.delete(tabella, filters=(tabella.starts_on < (Now() - Interval(days=days))))
