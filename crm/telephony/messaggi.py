# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A message left on the answering service (doc 52, third part).

When the centre wants it, the caller who hears the announcement can leave a
message after the tone. It lands on the call (`CRM Call Log.left_message`, the
recording is the message), written out when transcription is on, and whoever
follows the person is told: the person's owner, else whoever answers the number
called, else the desk that reads every call.
"""

from __future__ import annotations

import frappe
import phonenumbers

from crm.notifiche import regole as N
from crm.notifiche.avvisi import avvisa
from crm.permissions import livelli
from crm.telephony import routing

REGISTRO = "CRM Call Log"
#: The pages a person or a deal is read on.
PERSONE = ("CRM Lead", "CRM Deal")


def chi_avvisare(numero: str | None, chiamato: str | None, operatore: str = "twilio") -> list[str]:
	"""Who hears of a message: whoever follows the caller, else whoever answers
	the number called (on the carrier the call came through), else whoever reads
	every call of the centre."""
	if numero and (proprietario := routing.record_owner(numero)):
		return [proprietario]
	from crm.telephony.providers import get as provider

	if chiamato and (di_turno := list(routing.number_owners(provider(operatore), chiamato))):
		return di_turno
	return [
		utente
		for utente in frappe.get_all("User", filters={"enabled": 1, "user_type": "System User"}, pluck="name")
		if utente not in ("Administrator", "Guest")
		and livelli.nel_crm(utente)
		and livelli.ambito("telefono.registro", utente) == livelli.CENTRO
		and not livelli.e_agenzia(utente)
	]


def _leggibile(numero: str) -> str:
	try:
		return phonenumbers.format_number(
			phonenumbers.parse(numero, "IT"), phonenumbers.PhoneNumberFormat.INTERNATIONAL
		)
	except phonenumbers.NumberParseException:
		return numero


def avvisa_del_messaggio(nome: str) -> list[str]:
	"""Tell whoever follows the caller that a message was left on the call ``nome``.
	The person or deal it opens is the call's; the caller is named by their name,
	else by their number. Returns who was told."""
	from crm.fcrm.doctype.crm_notification.crm_notification import nome_di
	from crm.telephony import operatore

	chiamata = frappe.db.get_value(
		REGISTRO,
		nome,
		["from", "to", "reference_doctype", "reference_docname", "telephony_medium"],
		as_dict=True,
	)
	if not chiamata:
		return []
	riguarda = None
	chi = _leggibile(chiamata["from"] or "")
	if chiamata.reference_doctype in PERSONE and chiamata.reference_docname:
		riguarda = (chiamata.reference_doctype, chiamata.reference_docname)
		chi = nome_di(*riguarda)
	avvisati = []
	via = operatore.da_medium(chiamata.telephony_medium) or operatore.TWILIO
	for utente in chi_avvisare(chiamata["from"], chiamata["to"], via):
		if avvisa(
			utente, "Call", N.MESSAGGIO_IN_SEGRETERIA, [chi], riguarda=riguarda, oggetto=(REGISTRO, nome)
		):
			avvisati.append(utente)
	return avvisati
