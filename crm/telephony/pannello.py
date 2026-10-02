# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The phone at hand (docs/progetto-ghl/34): what the phone button at the top of
every page opens, where the keypad of the menu used to be a page of its own.

- **The last calls** the session may read (`telefono.registro`, the register's
  scope: `org_hierarchy` on the call log), each with the person it was with and
  whether nobody answered it.
- **The callbacks** the answering service promised, owed now.
- **Somebody to call**, found by name or by number (`telefono.chiama`): only
  people the session may read, and only those with a number.

Calling itself is the browser's (`CallUI`), after the server's yes
(`uscita.perche_no`).
"""

from __future__ import annotations

import frappe

from crm.permissions import livelli
from crm.telephony import callbacks

ULTIME = 8
TROVATE = 8
#: What an incoming call that nobody took ends as, at Twilio and by hand.
PERSE = ("No Answer", "Busy", "Failed", "Canceled")
#: The trailing digits that decide two numbers are the same: the whole national
#: number of most plans, whatever the prefix and the spaces (as `callbacks`).
CIFRE_DEL_NUMERO = 9


def persa(riga) -> bool:
	"""An incoming call nobody took: not answered, or a message left instead."""
	return riga.get("type") == "Incoming" and (riga.get("status") in PERSE or bool(riga.get("left_message")))


def _nomi(righe) -> dict:
	"""The names of the people and deals the calls were with, in two queries."""
	nomi = {}
	for doctype, campo in (("CRM Lead", "lead_name"), ("CRM Deal", "lead_name")):
		quali = {r.reference_docname for r in righe if r.reference_doctype == doctype and r.reference_docname}
		if quali:
			for r in frappe.get_all(doctype, filters={"name": ["in", list(quali)]}, fields=["name", campo]):
				nomi[(doctype, r.name)] = r.get(campo)
	return nomi


@frappe.whitelist()
def get_phone_panel() -> dict:
	"""The last calls the session may read and the callbacks owed now."""
	chiama = livelli.puo("telefono.chiama")
	if not (chiama or livelli.puo("telefono.registro")):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)

	righe = []
	if livelli.puo("telefono.registro"):
		righe = frappe.get_list(
			"CRM Call Log",
			fields=[
				"name",
				"type",
				"status",
				"from",
				"to",
				"start_time",
				"creation",
				"duration",
				"reference_doctype",
				"reference_docname",
				"left_message",
			],
			order_by="creation desc",
			limit=ULTIME,
		)
	nomi = _nomi(righe)
	chiamate = [
		{
			"name": r.name,
			"type": r.type,
			"missed": persa(r),
			"number": r.get("from") if r.type == "Incoming" else r.get("to"),
			"when": str(r.start_time or r.creation),
			"duration": r.duration,
			"person": nomi.get((r.reference_doctype, r.reference_docname)),
			"reference_doctype": r.reference_doctype,
			"reference_docname": r.reference_docname,
		}
		for r in righe
	]
	return {
		"calls": chiamate,
		"callbacks": callbacks.pending_summary() if chiama else None,
		"can_call": chiama,
	}


def _cifre(testo: str) -> str:
	return "".join(c for c in testo or "" if c.isdigit())


@frappe.whitelist()
def find_people(text: str | None = None) -> list[dict]:
	"""People to call, by name or by number: the ones the session may read, with
	a number. A number is matched on its last digits, written with or without its
	prefix and spaces."""
	livelli.verifica("telefono.chiama")
	testo = (text or "").strip()
	if len(testo) < 2:
		return []

	cifre = _cifre(testo)
	if cifre and not any(c.isalpha() for c in testo):
		if len(cifre) < 3:
			return []
		coda = cifre[-CIFRE_DEL_NUMERO:]
		# the numbers as written - "+39 340 111 2233" - read as digits only
		candidati = frappe.db.sql(
			"""select name from `tabCRM Lead`
			where replace(replace(replace(replace(coalesce(mobile_no, ''), ' ', ''), '-', ''), '.', ''), '/', '') like %(coda)s
			or replace(replace(replace(replace(coalesce(phone, ''), ' ', ''), '-', ''), '.', ''), '/', '') like %(coda)s
			order by modified desc limit 50""",
			{"coda": f"%{coda}%"},
			pluck=True,
		)
		if not candidati:
			return []
		filtri, o_filtri = {"name": ["in", candidati]}, None
	else:
		filtri, o_filtri = {}, [["lead_name", "like", f"%{testo}%"], ["name", "like", f"%{testo}%"]]

	righe = frappe.get_list(
		"CRM Lead",
		filters=filtri,
		or_filters=o_filtri,
		fields=["name", "lead_name", "mobile_no", "phone", "image"],
		order_by="modified desc",
		limit=TROVATE * 3,
	)
	return [r for r in righe if r.mobile_no or r.phone][:TROVATE]
