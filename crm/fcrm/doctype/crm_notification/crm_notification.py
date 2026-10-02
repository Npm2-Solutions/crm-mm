# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# Modifications copyright (c) 2026, NPM2 Solutions Srl
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.query_builder import Interval
from frappe.query_builder.functions import Now


class CRMNotification(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		comment: DF.Link | None
		count: DF.Int
		email_due: DF.Check
		emailed_on: DF.Datetime | None
		from_user: DF.Link | None
		message: DF.HTMLEditor | None
		notification_text: DF.Text | None
		notification_type_doc: DF.DynamicLink | None
		notification_type_doctype: DF.Link | None
		read: DF.Check
		reference_doctype: DF.Link | None
		reference_name: DF.DynamicLink | None
		sentence: DF.SmallText | None
		sentence_args: DF.JSON | None
		to_user: DF.Link
		type: DF.Literal[
			"Mention",
			"Task",
			"Assignment",
			"WhatsApp",
			"SMS",
			"Email",
			"Invoicing",
			"Agenda",
			"Area",
			"Automation",
			"Phone",
			"Call",
		]
	# end: auto-generated types

	def after_insert(self):
		# the panel and the sidebar's count, in every tab the person has open, once
		# the notification can be read
		if self.to_user:
			frappe.publish_realtime(
				"crm_notification", {"event": "new", "name": self.name}, user=self.to_user, after_commit=True
			)

	def on_update(self):
		if self.to_user and not self.flags.in_insert:
			frappe.publish_realtime(
				"crm_notification", {"event": "changed"}, user=self.to_user, after_commit=True
			)

	@staticmethod
	def clear_old_logs(days=180):
		"""Log Settings' retention: a notification older than this goes, read or not."""
		tabella = frappe.qb.DocType("CRM Notification")
		frappe.db.delete(tabella, filters=(tabella.creation < (Now() - Interval(days=days))))


def on_doctype_update():
	# the panel asks for one person's notifications, newest first
	frappe.db.add_index("CRM Notification", ["to_user", "creation"])


def get_permission_query_conditions(user=None):
	if not user:
		user = frappe.session.user

	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		return ""

	return f"`tabCRM Notification`.`to_user` = {frappe.db.escape(user)}"


def has_permission(doc, ptype, user):
	if not user:
		user = frappe.session.user

	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		return True

	if ptype == "create":
		return False

	if not doc.to_user:
		return True

	return doc.to_user == user


def notify_user(notification):
	"""A notification written by its sender's words (`notification_text`): what the
	CRM did before its sentences were kept apart. The CRM's own notifications come
	in by `crm.notifiche.avvisi.avvisa`."""
	from crm.notifiche.avvisi import avvisa

	notification = frappe._dict(notification)
	avvisa(
		notification.assigned_to,
		notification.notification_type,
		testo_html=notification.notification_text,
		da=notification.owner,
		riguarda=(notification.redirect_to_doctype, notification.redirect_to_docname),
		oggetto=(notification.reference_doctype, notification.reference_docname),
		messaggio=notification.message,
	)


def nome_di(reference_doctype: str, reference_name: str) -> str:
	"""What a notification is about, by the name one reads: a person's name, a deal's
	company or person; the ID when there is neither.

	The sentences name a person by their name alone and a deal as "the deal": a
	doctype's name glued into a sentence reads wrong in any language but English, and
	where the clinic is on a person is a patient."""
	if reference_doctype == "CRM Lead":
		return frappe.db.get_value("CRM Lead", reference_name, "lead_name") or reference_name
	if reference_doctype == "CRM Deal":
		deal = frappe.db.get_value("CRM Deal", reference_name, ["organization", "lead_name"], as_dict=True)
		return (deal and (deal.organization or deal.lead_name)) or reference_name
	return reference_name
