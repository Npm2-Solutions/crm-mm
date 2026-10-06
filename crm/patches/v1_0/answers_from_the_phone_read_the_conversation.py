# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Conversations answered and still «to read».

An answer typed in the WhatsApp Business app on the phone reached DottorCloud and
read nothing: the conversation stayed «to read» on every screen, with its
notifications, and opened on a line of new messages drawn over everything said
before the answer. From now on such an answer reads the conversation as of
itself (`crm.api.conversations.answered`); this puts right what was left.

A conversation still «to read» with an answer after the moment it was last read
is read as of that answer: an answer from the phone, or one somebody of the
centre wrote. Never an automation's message: nobody read anything for that one.
What they wrote after the answer keeps it «to read», counted from there. One
never read here and answered by nobody counts from the last message that left
from here, not from the beginning of time.
"""

import frappe

from crm.api.conversations import RECORDS, answered, available_channels, belongs_to, scope

# who writes for DottorCloud itself, an automation's or a webhook's message
SISTEMA = ("Administrator", "Guest")


def execute():
	canali = available_channels()
	for doctype in RECORDS:
		if not frappe.get_meta(doctype).has_field("conversation_unread"):
			continue
		for row in frappe.get_all(
			doctype,
			filters={"conversation_unread": 1},
			fields=["name", "conversation_seen_until", "last_answered_on"],
			limit_page_length=0,
		):
			letta = row.conversation_seen_until
			risposta = ultima_risposta(scope(doctype, row.name), canali)
			try:
				if risposta and (not letta or letta < risposta):
					answered(doctype, row.name, risposta, tell=False)
				elif not letta and row.last_answered_on:
					# never read here, and answered by nobody: new is what came
					# after the last message that left from here, not everything
					# ever said - the line went over the whole history
					frappe.db.set_value(
						doctype,
						row.name,
						"conversation_seen_until",
						row.last_answered_on,
						update_modified=False,
					)
			except Exception:
				frappe.log_error(
					frappe.get_traceback(), f"Conversations: could not read {doctype} {row.name}"
				)
	frappe.db.commit()


def ultima_risposta(where, canali):
	"""When somebody of the centre last answered: from the phone, or written by a
	person here - not an automation's."""
	quando = None
	for nome, spec in canali.items():
		filtri = belongs_to(where)
		filtri[spec["direction"]] = ["!=", spec["incoming"]]
		if spec["doctype"] == "Communication":
			filtri["communication_type"] = "Communication"
		or_filtri = {"owner": ["not in", SISTEMA]}
		if nome == "WhatsApp" and frappe.get_meta(spec["doctype"]).has_field("written_on_the_phone"):
			or_filtri["written_on_the_phone"] = 1
		righe = frappe.get_all(
			spec["doctype"],
			filters=filtri,
			or_filters=or_filtri,
			fields=["creation"],
			order_by="creation desc",
			limit=1,
		)
		if righe and (not quando or righe[0].creation > quando):
			quando = righe[0].creation
	return quando
