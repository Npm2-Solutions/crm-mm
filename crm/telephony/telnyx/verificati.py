# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A number of the centre's, verified in Telnyx to be shown on calls (doc 65).

The same need as with Twilio (doc 52): the centre keeps its landline with its
operator and wants it on the calls DottorCloud makes. Telnyx refuses a number that
is neither its own nor verified (SIP 403 D51). Its verification goes the other way
round from Twilio's: Telnyx calls the number - or texts it, for a mobile - and
says a code; whoever answers types the code here, in DottorCloud. No document is
asked; Telnyx charges a few cents for each number verified.

The row of `CRM Caller ID` is there from the start, waiting and switched off; the
right code switches it on. A verification nobody finished is over after a quarter
of an hour, as Twilio's. Removed, the number is taken out of Telnyx and stays in
the list switched off. In Italy a verified number is shown as far as the
operators let it (AGCOM 106/25/CONS), as with Twilio.
"""

from __future__ import annotations

import re
from urllib.parse import quote

import frappe
from frappe import _
from frappe.utils import now_datetime

from crm.permissions import livelli
from crm.telephony import caller_ids, operatore, uscita, verificati
from crm.telephony import verificati_regole as V
from crm.telephony.telnyx import collegamento
from crm.telephony.telnyx.cliente import ErroreTelnyx, chiama, registra

NUMERO = "CRM Caller ID"
#: How Telnyx gives the code: a call to the number, or an SMS to it.
MODI = ("call", "sms")
#: The digits Telnyx dials once its call is answered: digits, A-D, * and #, w and W to wait.
_INTERNO = re.compile(r"[0-9A-D*#wW]{1,50}")


def _chiave() -> str:
	impostazioni = frappe.get_single(collegamento.IMPOSTAZIONI)
	api_secret = collegamento.chiave(impostazioni)
	if not (collegamento.collegato(impostazioni) and api_secret):
		frappe.throw(_("Telnyx is not connected."))
	return api_secret


def _in_parole(errore: ErroreTelnyx) -> str:
	if errore.stato == 404:
		return _("Telnyx has no verification waiting for this number: ask for a new code.")
	if errore.stato in (400, 422) and errore.dettaglio:
		return _("Telnyx says: {0}").format(errore.dettaglio.strip()[:300])
	return errore.in_parole()


def _interno(valore: str | None) -> tuple[str, str]:
	scritto = re.sub(r"[\s\-.]", "", valore or "")
	if not scritto:
		return "", ""
	if not _INTERNO.fullmatch(scritto):
		return "", "The extension takes digits, * and #, and w for half a second's wait: at most 50."
	return scritto, ""


@frappe.whitelist(methods=["POST"])
def verify_number(
	phone_number: str,
	label: str | None = None,
	extension: str | None = None,
	method: str | None = None,
) -> dict:
	"""Telnyx calls the number - or texts it - with a code, to be typed here."""
	livelli.verifica(collegamento.CENTRO)
	numero = verificati._numero(phone_number)
	if motivo := uscita.perche_no(numero, operatore.TELNYX):
		frappe.throw(motivo)
	modo = method if method in MODI else "call"
	cifre, motivo = _interno(extension)
	if motivo:
		frappe.throw(_(motivo))

	riga = frappe.db.get_value(NUMERO, numero, ["source", "enabled", "provider"], as_dict=True)
	if riga and riga.enabled and riga.provider == operatore.TELNYX:
		if riga.source == caller_ids.SOURCE_ACCOUNT:
			frappe.throw(
				_(
					"This number is already one of the centre's numbers on Telnyx: it can be shown on calls already."
				)
			)
		if riga.source == caller_ids.SOURCE_VERIFIED:
			frappe.throw(_(V.RIFIUTI[21450]))

	corpo = {"phone_number": numero, "verification_method": modo}
	if cifre and modo == "call":
		corpo["extension"] = cifre
	try:
		chiama("POST", "verified_numbers", _chiave(), corpo=corpo)
	except ErroreTelnyx as errore:
		registra("DottorCloud: verifying a caller ID on Telnyx", errore)
		frappe.throw(_in_parole(errore))
	verificati._in_attesa(numero, label, None, provider=operatore.TELNYX)
	return {**verificati.stato(numero), "method": modo}


@frappe.whitelist(methods=["POST"])
def confirm_code(phone_number: str, code: str) -> dict:
	"""The code Telnyx said, typed here: right, the number is verified and switched on."""
	livelli.verifica(collegamento.CENTRO)
	numero = verificati._numero(phone_number)
	codice = re.sub(r"\D", "", code or "")
	if not codice:
		frappe.throw(_("Write the code Telnyx said."))
	if frappe.db.get_value(NUMERO, numero, "verification_status") != V.IN_ATTESA:
		frappe.throw(_("Telnyx has no verification waiting for this number: ask for a new code."))
	try:
		chiama(
			"POST",
			f"verified_numbers/{quote(numero)}/actions/verify",
			_chiave(),
			corpo={"verification_code": codice},
		)
	except ErroreTelnyx as errore:
		if errore.stato in (400, 422):
			frappe.throw(_("The code is not right: check it and write it again, or ask for a new one."))
		registra("DottorCloud: a Telnyx verification code", errore)
		frappe.throw(_in_parole(errore))
	verificati.segna(numero, V.VERIFICATO, sid=numero)
	return verificati.stato(numero)


@frappe.whitelist(methods=["POST"])
def verification_state(phone_number: str) -> dict:
	"""Where the number's verification stands; past its time, it did not happen."""
	livelli.verifica(collegamento.CENTRO)
	numero = verificati._numero(phone_number)
	riga = frappe.db.get_value(
		NUMERO, numero, ["name", "verification_status", "verification_requested_on"], as_dict=True
	)
	if (
		riga
		and riga.verification_status == V.IN_ATTESA
		and V.scaduta(riga.verification_requested_on, now_datetime())
	):
		verificati.segna(riga.name, V.NON_VERIFICATO)
	return verificati.stato(numero)


@frappe.whitelist(methods=["POST"])
def remove_verified(phone_number: str) -> dict:
	"""A verified number out of Telnyx: it is not shown on calls any more. The row
	stays, switched off, with its label. Says how many people had it as their own
	line, to give them another."""
	livelli.verifica(collegamento.CENTRO)
	numero = verificati._numero(phone_number)
	riga = frappe.get_doc(NUMERO, numero)
	if riga.source != caller_ids.SOURCE_VERIFIED:
		frappe.throw(_("Only a verified number is removed here: a number of Telnyx's is released."))
	try:
		chiama("DELETE", f"verified_numbers/{quote(numero)}", _chiave())
	except ErroreTelnyx as errore:
		# gone from Telnyx already: what is wanted
		if errore.stato != 404:
			registra("DottorCloud: removing a caller ID from Telnyx", errore)
			frappe.throw(_in_parole(errore))
	riga.update(
		{
			"enabled": 0,
			"verification_status": "",
			"provider_sid": None,
			"routing_note": _("Removed from Telnyx: it is not shown on calls any more."),
		}
	)
	riga.save(ignore_permissions=True)
	linee = frappe.db.count("CRM Telephony Agent", {operatore.linea(operatore.TELNYX): numero})
	return {**verificati.stato(numero), "lines": linee}
