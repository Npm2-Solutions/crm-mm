# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Who a call to one of our numbers would ring, if anyone.

Nothing here is carrier-specific: a provider only says which field on
``CRM Telephony Agent`` holds its numbers, and the rest is the same question
whoever carries the call.
"""

from __future__ import annotations

import frappe


def number_owners(provider, phone_number: str | None) -> dict:
	"""Agents who use this number, and how they would be reached.

	>>> number_owners(twilio, "+390212345678")
	{'agent@studio.it': {'name': ..., 'call_receiving_device': 'Computer', 'mobile_no': ...}}
	"""
	if not (provider.agent_number_field and phone_number):
		return {}

	cleaned = "".join(c for c in phone_number if c.isdigit() or c == "+")
	agents = frappe.get_all(
		"CRM Telephony Agent",
		filters={provider.agent_number_field: cleaned},
		fields=["name", "call_receiving_device"],
	)
	if not agents:
		return {}

	owners = {row["name"]: dict(row) for row in agents}
	for user in frappe.get_all("User", filters={"name": ["in", list(owners)]}, fields=["name", "mobile_no"]):
		owners[user["name"]]["mobile_no"] = user["mobile_no"]
	return owners


def logged_in(users: list[str]) -> set[str]:
	"""Which of these users currently has a session open."""
	if not users:
		return set()
	rows = frappe.db.sql(
		"""
		SELECT `user`
		FROM `tabSessions`
		WHERE `user` IN %(users)s
		""",
		{"users": users},
	)
	return {row[0] for row in rows}


def record_owner(caller: str | None) -> str | None:
	"""The salesperson who already knows this caller, if the number matches a record."""
	if not caller:
		return None
	owner = frappe.db.get_value("CRM Deal", {"mobile_no": caller}, "deal_owner")
	if not owner:
		owner = frappe.db.get_value("CRM Lead", {"mobile_no": caller, "converted": False}, "lead_owner")
	return owner


def pick_attender(owners: dict, caller: str | None = None) -> dict | None:
	"""Which of a number's owners takes the call.

	With more than one of them online, the lead or deal owner wins — the caller
	reaches the person who already knows them. That preference is applied by
	looking at them first, not by filtering the others out, so it holds whether
	they answer at their desk or on their mobile.
	"""
	if not owners:
		return None

	online = logged_in(list(owners))
	candidates = list(owners.items())

	if len(online) > 1 and (preferred := record_owner(caller)) in owners:
		candidates.sort(key=lambda item: item[0] != preferred)

	for name, details in candidates:
		on_phone = details.get("call_receiving_device") == "Phone" and details.get("mobile_no")
		at_desk = details.get("call_receiving_device") == "Computer" and name in online
		if on_phone or at_desk:
			return details
	return None


def find_attender(provider, to_number: str | None, caller: str | None = None) -> dict | None:
	"""The agent a call to ``to_number`` should ring, or ``None`` if nobody would."""
	return pick_attender(number_owners(provider, to_number), caller)
