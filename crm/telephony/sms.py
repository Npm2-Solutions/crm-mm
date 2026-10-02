# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The centre's SMS through its Twilio space (doc 52, fourth part).

Every SMS DottorCloud sends - the one written by hand from a person's page, an
automation's, a waiting list's offer, the news of the client area - leaves from
one sender, the centre's: its name, or one of its numbers when the answers must
come back. Before, each place had its own, and a person could get the centre's
messages from four different senders. The rules without a site are in
``sms_regole``.
"""

from __future__ import annotations

import frappe
from frappe.utils import cint

from crm.telephony import sms_regole as R

IMPOSTAZIONI = "CRM Twilio Settings"
NOME, NUMERO = "Name", "Number"


def numeri_sms() -> list[str]:
	"""The space's numbers that can send SMS."""
	return frappe.get_all(
		"CRM Caller ID",
		filters={"enabled": 1, "provider": "twilio", "sms_capable": 1},
		pluck="phone_number",
		order_by="phone_number asc",
	)


def nome_proposto() -> str:
	"""A sender's name made from the centre's, for a centre that chose none."""
	from crm.moduli.richieste import nome_del_centro

	return R.nome_dal_centro(nome_del_centro())


def mittente() -> str | None:
	"""Who every SMS of the centre comes from: what the manager chose - its name, or
	one of its numbers that can send SMS - else its first such number, else a name
	made from the centre's. None while Twilio is off, or with nothing to send from."""
	scelta = frappe.db.get_singles_dict(IMPOSTAZIONI)
	if not cint(scelta.get("enabled")):
		return None
	numeri = numeri_sms()
	nome = (scelta.get("sms_sender_name") or "").strip()
	if scelta.get("sms_from") == NOME and not R.problema_del_nome(nome):
		return nome
	if scelta.get("sms_from") == NUMERO and scelta.get("sms_sender_number") in numeri:
		return scelta.get("sms_sender_number")
	if numeri:
		return numeri[0]
	return nome_proposto() or None


def si_risponde(da: str | None) -> bool:
	"""Whether a person can answer an SMS from ``da``: a number, not a name."""
	return bool(da) and da.startswith("+")


@frappe.whitelist()
def get_sms_sender_options() -> dict:
	"""For Twilio's page: the space's numbers that can send SMS, the name made
	from the centre's, and who the SMS come from now."""
	from crm.permissions import livelli

	livelli.verifica_nel_crm("telefono.configura")
	etichette = dict(
		frappe.get_all(
			"CRM Caller ID",
			filters={"enabled": 1, "provider": "twilio", "sms_capable": 1},
			fields=["phone_number", "label"],
			as_list=True,
		)
	)
	return {
		"numbers": [{"number": n, "label": etichette.get(n) or ""} for n in numeri_sms()],
		"name": nome_proposto(),
		"sender": mittente(),
	}
