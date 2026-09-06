# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now


class CRMVisitor(Document):
	"""One browser, tracked across visits by a first-party cookie.

	A visitor starts anonymous. The moment it does something that names a person —
	submits a form, books a slot, clicks a personalised link from an email — it is
	*identified*: bound to a Lead (and later the Deal that lead becomes), and its
	whole back history of sessions and events is stamped with that record. That
	back-fill is the point of the doctype: it is what turns "someone read the
	pricing page three times last week" into something you can see on the lead.
	"""

	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		browser: DF.Data | None
		contact: DF.Link | None
		country: DF.Data | None
		deal: DF.Link | None
		device_type: DF.Literal["", "Desktop", "Mobile", "Tablet", "Bot"] | None
		first_seen_on: DF.Datetime | None
		first_session: DF.Link | None
		identified_on: DF.Datetime | None
		ip_address: DF.Data | None
		last_seen_on: DF.Datetime | None
		last_session: DF.Link | None
		lead: DF.Link | None
		os: DF.Data | None
		page_view_count: DF.Int
		session_count: DF.Int
		status: DF.Literal["Anonymous", "Identified"]
		user_agent: DF.SmallText | None
		visitor_id: DF.Data
	# end: auto-generated types

	def identify(self, doctype: str, name: str) -> None:
		"""Bind this visitor to a Lead or Deal and back-fill its history.

		Idempotent, and never re-points a visitor that is already bound to a
		different record: two people sharing a browser would otherwise hand the
		second person's sessions to the first one's lead. The first identity wins;
		a later one only fills in the slot it belongs to (a Deal on a visitor that
		only had a Lead).
		"""
		field = {"CRM Lead": "lead", "CRM Deal": "deal"}.get(doctype)
		if not field:
			return
		if self.get(field) == name:
			return
		if self.get(field):
			return

		values = {field: name, "status": "Identified"}
		if not self.identified_on:
			values["identified_on"] = now()

		self.db_set(values, update_modified=False)
		self._backfill(field, name)

	def _backfill(self, field: str, name: str) -> None:
		"""Stamp every session and event this visitor already produced with the
		record it turned out to belong to, so the journey reads whole from day one
		rather than starting at the moment of the form submission."""
		for doctype in ("CRM Visitor Session", "CRM Tracking Event"):
			frappe.db.set_value(
				doctype,
				{"visitor": self.name, field: ["in", (None, "")]},
				field,
				name,
				update_modified=False,
			)


def get_or_create(visitor_id: str, defaults: dict | None = None) -> "CRMVisitor":
	"""The visitor for `visitor_id`, created on first sight.

	The id is minted server-side (see `crm.api.tracking.new_id`) and only ever
	returned to the browser that owns it, so an unknown id means a new browser —
	not something to reject.
	"""
	if frappe.db.exists("CRM Visitor", visitor_id):
		return frappe.get_doc("CRM Visitor", visitor_id)

	doc = frappe.get_doc(
		{
			"doctype": "CRM Visitor",
			"visitor_id": visitor_id,
			"status": "Anonymous",
			"first_seen_on": now(),
			"last_seen_on": now(),
			**(defaults or {}),
		}
	)
	doc.insert(ignore_permissions=True)
	return doc
