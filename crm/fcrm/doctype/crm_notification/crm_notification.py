# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# Modifications copyright (c) 2026, NPM2 Solutions Srl
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CRMNotification(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		comment: DF.Link | None
		from_user: DF.Link | None
		message: DF.HTMLEditor | None
		notification_text: DF.Text | None
		notification_type_doc: DF.DynamicLink | None
		notification_type_doctype: DF.Link | None
		read: DF.Check
		reference_doctype: DF.Link | None
		reference_name: DF.DynamicLink | None
		to_user: DF.Link
		type: DF.Literal["Mention", "Task", "Assignment", "WhatsApp"]
	# end: auto-generated types

	def on_update(self):
		if self.to_user:
			frappe.publish_realtime("crm_notification", user=self.to_user)


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
	"""
	Notify the assigned user
	"""
	notification = frappe._dict(notification)
	if notification.owner == notification.assigned_to:
		return

	values = frappe._dict(
		doctype="CRM Notification",
		from_user=notification.owner,
		to_user=notification.assigned_to,
		type=notification.notification_type,
		message=notification.message,
		notification_text=notification.notification_text,
		notification_type_doctype=notification.reference_doctype,
		notification_type_doc=notification.reference_docname,
		reference_doctype=notification.redirect_to_doctype,
		reference_name=notification.redirect_to_docname,
	)

	if frappe.db.exists("CRM Notification", values):
		return
	frappe.get_doc(values).insert(ignore_permissions=True)


def in_grassetto(testo) -> str:
	"""A name inside a notification's sentence, the way the panel shows names."""
	return f'<span class="font-medium text-ink-gray-9">{frappe.utils.escape_html(testo or "")}</span>'


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
