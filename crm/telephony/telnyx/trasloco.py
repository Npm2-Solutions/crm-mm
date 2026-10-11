# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A number the centre already has in its own Telnyx account, taken into
DottorCloud (doc 65).

With Twilio a number moves from the account into DottorCloud's space, with the
account's codes pasted again. Telnyx has no space: DottorCloud already works in the
centre's account, and taking a number in is pointing it at DottorCloud's TeXML
application and messaging profile, with DottorCloud's tag. A number on the
centre's own switchboard (a SIP connection) stays there; one on another
application of the centre's leaves it, and the page says so before. Only in the
centre's own account: the agency's holds other sites' numbers.
"""

from __future__ import annotations

import frappe
from frappe import _

from crm.permissions import livelli
from crm.telephony.telnyx import collegamento
from crm.telephony.telnyx import regole as R
from crm.telephony.telnyx.cliente import ErroreTelnyx, chiama, registra, tutte


def _del_centro():
	livelli.verifica(collegamento.CENTRO)
	impostazioni = frappe.get_single(collegamento.IMPOSTAZIONI)
	api_secret = collegamento.chiave(impostazioni)
	if not (collegamento.collegato(impostazioni) and api_secret and impostazioni.account_owner == R.CENTRO):
		frappe.throw(_("Only a number of the centre's own Telnyx account is taken into its phone."))
	return api_secret, impostazioni


@frappe.whitelist(methods=["POST"])
def get_account_numbers() -> list[dict]:
	"""The numbers of the centre's account that DottorCloud does not manage: the ones
	that can be taken in first, the ones on a switchboard with why they stay."""
	api_secret, impostazioni = _del_centro()
	segno = collegamento.segno()
	nostre = collegamento.nostre(impostazioni)
	try:
		connessioni = {str(c.get("id")): c for c in tutte("connections", api_secret)}
		numeri = tutte("phone_numbers", api_secret)
	except ErroreTelnyx as errore:
		frappe.throw(errore.in_parole(), title=_("Telnyx"))
	righe = []
	for numero in numeri:
		connessione = str(numero.get("connection_id") or "")
		if connessione in nostre or segno in (numero.get("tags") or []):
			continue
		altra = connessioni.get(connessione) or {}
		nome = altra.get("connection_name") or numero.get("connection_name") or connessione
		if altra.get("record_type") in R.CENTRALINI:
			motivo = _("It answers on the switchboard of the connection {0}: it stays there.").format(nome)
		else:
			motivo = ""
		righe.append(
			{
				"sid": str(numero.get("id")),
				"number": numero.get("phone_number"),
				"label": numero.get("customer_reference") or "",
				"reason": motivo,
				"now_on": nome if connessione and not motivo else "",
			}
		)
	return sorted(righe, key=lambda r: (bool(r["reason"]), r["number"] or ""))


@frappe.whitelist(methods=["POST"])
def move_number(number_sid: str) -> dict:
	"""One number of the centre's account taken into DottorCloud: its calls to the
	TeXML application, its SMS to the messaging profile, DottorCloud's tag on it."""
	api_secret, impostazioni = _del_centro()
	try:
		numero = (chiama("GET", f"phone_numbers/{number_sid}", api_secret) or {}).get("data") or {}
		connessione = str(numero.get("connection_id") or "")
		if connessione and connessione not in collegamento.nostre(impostazioni):
			altra = (chiama("GET", f"connections/{connessione}", api_secret) or {}).get("data") or {}
			if altra.get("record_type") in R.CENTRALINI:
				frappe.throw(_("This number answers on the centre's switchboard: it stays there."))
		segno = collegamento.segno()
		etichette = list(numero.get("tags") or [])
		chiama(
			"PATCH",
			f"phone_numbers/{number_sid}",
			api_secret,
			corpo={
				"connection_id": impostazioni.texml_application_id,
				"tags": etichette if segno in etichette else [*etichette, segno],
			},
		)
		if impostazioni.messaging_profile_id:
			try:
				messaggi = (chiama("GET", f"phone_numbers/{number_sid}/messaging", api_secret) or {}).get(
					"data"
				) or {}
				if (messaggi.get("features") or {}).get("sms"):
					chiama(
						"PATCH",
						f"phone_numbers/{number_sid}/messaging",
						api_secret,
						corpo={"messaging_profile_id": impostazioni.messaging_profile_id},
					)
			except ErroreTelnyx as errore:
				# its calls reach DottorCloud all the same; its SMS go at the next check
				registra("DottorCloud: a moved number's SMS on Telnyx", errore)
	except ErroreTelnyx as errore:
		registra("DottorCloud: taking a number into Telnyx's phone", errore)
		frappe.throw(errore.in_parole(), title=_("Telnyx"))
	collegamento._aggiorna_i_numeri()
	return {"number": numero.get("phone_number")}
