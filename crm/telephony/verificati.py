# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A number of the centre's, verified to be shown on calls (doc 52).

The centre keeps its landline with its operator and wants it on the calls
DottorCloud makes: Twilio verifies it in the space. The manager writes the
number, DottorCloud asks Twilio, and Twilio calls it from +1 415 723 4000; a
recorded voice in English asks for the six digits the page shows, typed on the
phone's keypad. No document is asked. Twilio says how it went at the end of the
call (`caller_id_verified`, signed like every request of Twilio's); the page asks
too, while it waits, so a site Twilio cannot reach learns it all the same.

The row of `CRM Caller ID` is there from the start, waiting and switched off; it is
switched on when Twilio says the number is verified. A verified number is removed
from Twilio here, and stays in the list switched off, with what it was.

Since 19/08/2025 an Italian operator may block a call from abroad that shows an
Italian landline of somebody else's network (AGCOM 106/25/CONS), and Twilio shows
a verified Italian number in Italy only as far as the operators let it: the page
says so, and the call warns (`uscita_regole.incerta_in_italia`). A Twilio number,
bought or moved into the space, is shown for certain. The rules without a site are
in ``verificati_regole``.
"""

from __future__ import annotations

import frappe
import phonenumbers
from frappe import _
from frappe.utils import now_datetime
from twilio.base.exceptions import TwilioRestException

from crm.integrations.twilio.utils import get_public_url
from crm.notifiche import regole as N
from crm.notifiche.avvisi import avvisa
from crm.permissions import livelli
from crm.telephony import caller_ids, collegamento, uscita
from crm.telephony import uscita_regole as U
from crm.telephony import verificati_regole as R

NUMERO = "CRM Caller ID"
#: Where Twilio says how a verification went.
ESITO = "/api/method/crm.integrations.twilio.api.caller_id_verified"
#: The page waiting for the code: while it asks, nobody needs a notification.
_GUARDA = "dottorcloud:verifica:{}"
#: How long the page counts as watching after it last asked, in seconds.
_GUARDATA_PER = 20


def _numero(scritto: str | None) -> str:
	"""The number as Twilio takes it, in E.164 (an Italian one written without +39
	too); an error in words when it cannot be read."""
	letto = U.letto(scritto)
	if not letto:
		frappe.throw(_("This number cannot be read: write it with its country code, +39 for Italy."))
	return phonenumbers.format_number(letto, phonenumbers.PhoneNumberFormat.E164)


def _twilio():
	from crm.telephony import providers

	if not collegamento.collegato():
		frappe.throw(_("Twilio is not connected."))
	return providers.get("twilio")


def _in_parole(errore: Exception) -> str:
	"""Twilio's refusal of a verification in the reader's words."""
	if isinstance(errore, TwilioRestException) and (frase := R.rifiuto(errore.code)):
		return _(frase)
	if isinstance(errore, TwilioRestException) and errore.code and errore.status not in (401, 403, 404):
		from crm.telephony import errori

		return errori.in_parole(errore.code, errore.msg)
	return collegamento.in_parole(errore)


# ---------------------------------------------------------------------------
# asking Twilio


@frappe.whitelist(methods=["POST"])
def verify_number(
	phone_number: str,
	label: str | None = None,
	extension: str | None = None,
	call_delay: int | str | None = None,
) -> dict:
	"""Twilio calls the number and asks for the code this returns: the page shows
	it, whoever answers types it on the keypad."""
	livelli.verifica(collegamento.CENTRO)
	numero = _numero(phone_number)
	if motivo := uscita.perche_no(numero):
		frappe.throw(motivo)
	cifre, motivo = R.interno(extension)
	if motivo:
		frappe.throw(_(motivo))
	secondi, motivo = R.attesa(call_delay)
	if motivo:
		frappe.throw(_(motivo))

	riga = frappe.db.get_value(NUMERO, numero, ["source", "enabled", "verification_status"], as_dict=True)
	if riga and riga.enabled and riga.source == caller_ids.SOURCE_ACCOUNT:
		frappe.throw(_(R.RIFIUTI[21449]))
	if riga and riga.enabled and riga.source == caller_ids.SOURCE_VERIFIED:
		frappe.throw(_(R.RIFIUTI[21450]))

	twilio = _twilio()
	try:
		richiesta = twilio.start_caller_id_verification(
			numero,
			R.nome_per_twilio(label, numero),
			extension=cifre or None,
			call_delay=secondi,
			status_callback=get_public_url(ESITO),
		)
	except collegamento.NON_RISPONDE as errore:
		if isinstance(errore, TwilioRestException) and errore.code == 21450:
			# verified in Twilio already, by hand in its console: the list catches up
			caller_ids.sync("twilio")
			return stato(numero)
		collegamento._registra("DottorCloud: verifying a caller ID", errore)
		frappe.throw(_in_parole(errore))

	_in_attesa(numero, label, richiesta.get("call_sid"))
	return {**stato(numero), "validation_code": richiesta.get("validation_code")}


def _in_attesa(numero: str, etichetta: str | None, chiamata: str | None) -> None:
	"""The row of the number, waiting for the code and switched off until Twilio
	says it is verified."""
	valori = {
		"provider": "twilio",
		"source": caller_ids.SOURCE_VERIFIED,
		"enabled": 0,
		"voice_capable": 1,
		"sms_capable": 0,
		"provider_sid": None,
		"verification_status": R.IN_ATTESA,
		"verification_requested_by": frappe.session.user,
		"verification_requested_on": now_datetime(),
		"verification_call_sid": chiamata,
		"verified_on": None,
		**caller_ids._routing({"source": caller_ids.SOURCE_VERIFIED}),
	}
	if (etichetta or "").strip():
		valori["label"] = etichetta.strip()
	if frappe.db.exists(NUMERO, numero):
		riga = frappe.get_doc(NUMERO, numero)
		riga.update(valori)
		riga.save(ignore_permissions=True)
	else:
		frappe.get_doc({"doctype": NUMERO, "phone_number": numero, **valori}).insert(ignore_permissions=True)


# ---------------------------------------------------------------------------
# how it went


def stato(numero: str) -> dict:
	"""Where the number's verification stands, as the page shows it."""
	riga = frappe.db.get_value(
		NUMERO,
		numero,
		["phone_number", "label", "enabled", "source", "verification_status", "verified_on"],
		as_dict=True,
	)
	if not riga:
		return {"phone_number": numero, "status": ""}
	return {
		"phone_number": riga.phone_number,
		"label": riga.label or "",
		"status": riga.verification_status or "",
		"enabled": bool(riga.enabled),
		"verified_on": riga.verified_on,
		"uncertain_in_italy": U.paese_di(numero) == U.ITALIA and not U.cellulare_italiano(numero),
		"mobile_in_italy": U.cellulare_italiano(numero),
	}


@frappe.whitelist(methods=["POST"])
def verification_state(phone_number: str) -> dict:
	"""The page, while it waits: what Twilio said, or what Twilio has now."""
	livelli.verifica(collegamento.CENTRO)
	numero = _numero(phone_number)
	frappe.cache.set_value(_GUARDA.format(numero), 1, expires_in_sec=_GUARDATA_PER)
	riga = frappe.db.get_value(
		NUMERO, numero, ["name", "verification_status", "verification_requested_on"], as_dict=True
	)
	if riga and riga.verification_status == R.IN_ATTESA:
		_chiedi_a_twilio(riga)
	return stato(numero)


def _chiedi_a_twilio(riga) -> None:
	"""Twilio's list says whether the number is verified; past its time, it was not."""
	try:
		sid = _twilio().find_verified_caller_id(riga.name)
	except collegamento.NON_RISPONDE as errore:
		collegamento._registra("DottorCloud: a caller ID's verification", errore)
		return
	if sid:
		segna(riga.name, R.VERIFICATO, sid=sid)
	elif R.scaduta(riga.verification_requested_on, now_datetime()):
		segna(riga.name, R.NON_VERIFICATO)


def segna(numero: str, esito: str, sid: str | None = None, avvisa_chi: bool = False) -> bool:
	"""The verification is over: verified, the number is switched on; not, it stays
	off. Once: what was decided stays. Returns whether this decided it."""
	riga = frappe.get_doc(NUMERO, numero)
	if riga.verification_status != R.IN_ATTESA:
		return False
	if esito == R.VERIFICATO:
		riga.update(
			{
				"verification_status": R.VERIFICATO,
				"verified_on": now_datetime(),
				"provider_sid": sid or riga.provider_sid,
				"enabled": 1,
				"voice_capable": 1,
				"last_synced_on": now_datetime(),
			}
		)
	else:
		riga.verification_status = R.NON_VERIFICATO
	riga.save(ignore_permissions=True)
	if avvisa_chi and riga.verification_requested_by:
		avvisa(
			riga.verification_requested_by,
			"Phone",
			N.NUMERO_VERIFICATO if esito == R.VERIFICATO else N.NUMERO_NON_VERIFICATO,
			[riga.phone_number],
			oggetto=(NUMERO, riga.name),
		)
	return True


def alla_fine_della_chiamata(
	stato: str | None, chiamata: str | None, chiamato: str | None, sid: str | None
) -> None:
	"""Twilio's StatusCallback of a verification: its call (``chiamata``, to
	``chiamato``) is over, and ``stato`` says how it went, with the caller ID's ``sid``
	when verified. The one who asked hears of it, unless the page was watching."""
	esito = R.esito(stato)
	if not esito:
		return
	numero = frappe.db.get_value(NUMERO, {"verification_call_sid": chiamata}) if chiamata else None
	if not numero:
		letto = caller_ids.classify(chiamato)["e164"]
		numero = letto if letto and frappe.db.exists(NUMERO, letto) else None
	if not numero:
		frappe.log_error(
			title="DottorCloud: a verification Twilio told of",
			message=f"No caller ID waits for the call {chiamata}",
		)
		return
	guardata = bool(frappe.cache.get_value(_GUARDA.format(numero)))
	segna(numero, esito, sid=sid, avvisa_chi=not guardata)


def scadute() -> int:
	"""Verifications nobody heard of again: past their time, they did not happen."""
	adesso = now_datetime()
	finite = 0
	for riga in frappe.get_all(
		NUMERO,
		filters={"verification_status": R.IN_ATTESA},
		fields=["name", "verification_requested_on"],
	):
		if R.scaduta(riga.verification_requested_on, adesso):
			finite += segna(riga.name, R.NON_VERIFICATO)
	return finite


# ---------------------------------------------------------------------------
# taking one away


@frappe.whitelist(methods=["POST"])
def remove_verified(phone_number: str) -> dict:
	"""A verified number out of Twilio: it is not shown on calls any more. The row
	stays, switched off, with its label. Says how many people had it as their own
	line, to give them another."""
	livelli.verifica(collegamento.CENTRO)
	numero = _numero(phone_number)
	riga = frappe.get_doc(NUMERO, numero)
	if riga.source != caller_ids.SOURCE_VERIFIED:
		frappe.throw(_("Only a verified number is removed here: a number of Twilio's is released."))
	twilio = _twilio()
	try:
		sid = riga.provider_sid or twilio.find_verified_caller_id(numero)
		if sid:
			twilio.remove_verified_caller_id(sid)
	except collegamento.NON_RISPONDE as errore:
		# gone from Twilio already: what is wanted
		if not (isinstance(errore, TwilioRestException) and errore.status == 404):
			collegamento._registra("DottorCloud: removing a caller ID", errore)
			frappe.throw(_in_parole(errore))
	riga.update(
		{
			"enabled": 0,
			"verification_status": "",
			"provider_sid": None,
			"routing_note": _("Removed from Twilio: it is not shown on calls any more."),
		}
	)
	riga.save(ignore_permissions=True)
	linee = frappe.db.count("CRM Telephony Agent", {"twilio_number": numero})
	return {**stato(numero), "lines": linee}
