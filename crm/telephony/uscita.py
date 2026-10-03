# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Calls going out from DottorCloud through the centre's Twilio space (doc 52,
third part).

Before a call leaves, DottorCloud says where it may go - the countries the
manager chose, never a premium-rate number - and which number it shows: one of
the centre's, chosen for the call, else the person's own. The same countries are
set in Twilio's permissions of the space, so a key that leaked could not call
elsewhere either. The rules without a site are in ``uscita_regole``.
"""

from __future__ import annotations

import json

import frappe
from frappe import _

from crm.permissions import livelli
from crm.telephony import caller_ids, collegamento
from crm.telephony import uscita_regole as R

IMPOSTAZIONI = "CRM Twilio Settings"
CHIAMA = "telefono.chiama"


def consentiti() -> list[str]:
	"""The countries the centre may call, Italy to start with."""
	return R.paesi(frappe.db.get_single_value(IMPOSTAZIONI, "allowed_countries"))


def perche_no(numero: str | None) -> str:
	"""Why a call to ``numero`` does not leave, in the reader's words; '' when it does."""
	motivo = R.si_chiama(numero, consentiti())
	return _(motivo) if motivo else ""


def numero_da_mostrare(utente: str | None, richiesto: str | None = None) -> str | None:
	"""The number a call shows: the one asked for, when it is one of the centre's
	numbers that may be shown; else the person's own line."""
	if richiesto and richiesto in caller_ids.usable_for_outbound("twilio"):
		return richiesto
	return frappe.db.get_value("CRM Telephony Agent", utente, "twilio_number") if utente else None


@frappe.whitelist()
def get_outbound_numbers() -> dict:
	"""The numbers the session may show on a call, its own line marked, and the
	countries it may call."""
	# who sees the call buttons (`is_call_integration_enabled`): not Marketing
	livelli.verifica_nel_crm(CHIAMA)
	proprio = frappe.db.get_value("CRM Telephony Agent", frappe.session.user, "twilio_number")
	righe = frappe.get_all(
		"CRM Caller ID",
		filters=caller_ids.outbound_filters("twilio"),
		fields=["phone_number", "label", "source"],
		order_by="phone_number asc",
	)
	numeri = [
		{
			"number": riga.phone_number,
			"label": riga.label or "",
			"mobile": R.cellulare_italiano(riga.phone_number),
			# verified, not Twilio's: shown in Italy as far as the operators let it
			"verified": riga.source == caller_ids.SOURCE_VERIFIED,
			"own": riga.phone_number == proprio,
		}
		for riga in righe
	]
	if proprio and not any(n["own"] for n in numeri):
		numeri.insert(
			0,
			{
				"number": proprio,
				"label": "",
				"mobile": R.cellulare_italiano(proprio),
				"verified": _verificato(proprio),
				"own": True,
			},
		)
	return {"numbers": numeri, "countries": consentiti()}


def _verificato(numero: str | None) -> bool:
	"""Whether a number is only verified in Twilio, not one of the space's."""
	return bool(numero) and (
		frappe.db.get_value("CRM Caller ID", numero, "source") == caller_ids.SOURCE_VERIFIED
	)


@frappe.whitelist()
def check_number(number: str, show: str | None = None) -> dict:
	"""Before a call leaves: whether it may, and whether the number shown would get
	it blocked in Italy."""
	livelli.verifica_nel_crm(CHIAMA)
	motivo = perche_no(number)
	return {
		"ok": not motivo,
		"reason": motivo,
		"country": R.paese_di(number),
		"blocked_in_italy": R.bloccata_in_italia(show, number),
		"uncertain_in_italy": R.incerta_in_italia(show, number, _verificato(show)),
	}


def allinea_i_paesi(impostazioni=None) -> bool:
	"""Twilio's permissions of the space as the centre chose: only the countries
	chosen, at their ordinary numbers. Only in DottorCloud's own space: an account
	connected by hand may call for others too. Returns whether Twilio took them."""
	impostazioni = impostazioni or frappe.get_single(IMPOSTAZIONI)
	if not (collegamento.collegato(impostazioni) and impostazioni.account_owner):
		return False
	try:
		auth_token = impostazioni.get_password("auth_token", raise_exception=False)
		permessi = collegamento.Client(impostazioni.account_sid, auth_token).voice.v1.dialing_permissions
		# the space has its own, not its account's
		if permessi.settings().fetch().dialing_permissions_inheritance:
			permessi.settings().update(dialing_permissions_inheritance=False)
		# written only when something differs: the hourly check asks, it does not rewrite
		cambi = R.cambi_dei_permessi(impostazioni.allowed_countries, _attuali(permessi))
		if cambi:
			permessi.bulk_country_updates.create(update_request=json.dumps(_come_twilio(cambi)))
	except collegamento.NON_RISPONDE as errore:
		collegamento._registra("DottorCloud: Twilio's dialing permissions", errore)
		return False
	return True


def _attuali(permessi) -> list[dict]:
	"""The countries Twilio has something switched on for, each with its three switches."""
	trovati = {}
	for interruttore in R.INTERRUTTORI:
		for paese in permessi.countries.list(**{interruttore: True}):
			trovati[paese.iso_code] = {
				"iso_code": paese.iso_code,
				**{chiave: bool(getattr(paese, chiave, False)) for chiave in R.INTERRUTTORI},
			}
	return list(trovati.values())


def _come_twilio(cambi: list[dict]) -> list[dict]:
	"""Twilio's example writes its booleans as words."""
	return [
		{
			chiave: ("true" if valore is True else "false" if valore is False else valore)
			for chiave, valore in c.items()
		}
		for c in cambi
	]
