# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A number the centre already has in its own Twilio account, moved into
DottorCloud's space (doc 52, sixth part).

Twilio moves a number into a subaccount only with the account's own codes, which
DottorCloud never keeps: the manager pastes them again, they serve the request and
are gone with it. An Italian number moves with its approved documents, copied to the
space first (Twilio's bundle clone, approved there too), and with its address;
then it is pointed at DottorCloud and joins the list of the centre's numbers. Only
in a space of the centre's own account: the agency's account is another account.
The rules without a site are in ``trasloco_regole``.
"""

from __future__ import annotations

import json

import frappe
from frappe import _
from twilio.base.exceptions import TwilioRestException

from crm.marchio import con_nome
from crm.permissions import livelli
from crm.telephony import collegamento, errori
from crm.telephony import collegamento_regole as C
from crm.telephony import errori_regole as E
from crm.telephony import trasloco_regole as R

#: Twilio's bundle clones, which the SDK DottorCloud uses does not have yet.
CLONI = "https://numbers.twilio.com/v2/RegulatoryCompliance/Bundles/{}/Clones"


def _principale(account_sid: str, auth_token: str):
	"""The centre's own account, from the codes pasted for this one request: only the
	account DottorCloud's space is in, only when the space is the centre's."""
	livelli.verifica(collegamento.CENTRO)
	impostazioni = frappe.get_single(collegamento.IMPOSTAZIONI)
	if not (collegamento.collegato(impostazioni) and impostazioni.account_owner == C.CENTRO):
		frappe.throw(_("Only a number of the centre's own Twilio account moves into its space."))
	manca = C.cosa_manca(account_sid, auth_token)
	if manca:
		frappe.throw(_(manca))
	account_sid, auth_token = C.pulito(account_sid), C.pulito(auth_token)
	if account_sid != impostazioni.main_account_sid:
		frappe.throw(con_nome(_("These are not the codes of the account {brand}'s space is in.")))
	return collegamento.Client(account_sid, auth_token), impostazioni


def _in_parole(errore: Exception) -> str:
	"""Twilio's refusal in DottorCloud's words: a code it knows, else the connection's."""
	if isinstance(errore, TwilioRestException) and E.frase(errore.code):
		return errori.in_parole(errore.code)
	return collegamento.in_parole(errore)


@frappe.whitelist(methods=["POST"])
def get_account_numbers(account_sid: str, auth_token: str) -> list[dict]:
	"""The numbers of the centre's own account, outside DottorCloud's space: the ones
	that can move first. The codes serve this request and are not kept."""
	principale, _impostazioni = _principale(account_sid, auth_token)
	try:
		numeri = [
			{
				"sid": numero.sid,
				"phone_number": numero.phone_number,
				"friendly_name": numero.friendly_name,
				"trunk_sid": numero.trunk_sid,
			}
			for numero in principale.incoming_phone_numbers.list()
		]
	except collegamento.NON_RISPONDE as errore:
		frappe.throw(_in_parole(errore), title=_("Twilio"))
	return [
		{
			"sid": riga["sid"],
			"number": riga["phone_number"],
			"label": riga["friendly_name"] if riga["friendly_name"] != riga["phone_number"] else "",
			"reason": _(riga["reason"]) if riga["reason"] else "",
		}
		for riga in R.da_spostare(numeri)
	]


@frappe.whitelist(methods=["POST"])
def move_number(account_sid: str, auth_token: str, number_sid: str) -> dict:
	"""One number of the centre's own account into DottorCloud's space: its approved
	documents and its address copied there, then it moves and is pointed at
	DottorCloud. The codes serve this request and are not kept."""
	principale, impostazioni = _principale(account_sid, auth_token)
	spazio = impostazioni.account_sid
	try:
		numero = principale.incoming_phone_numbers(number_sid).fetch()
		if motivo := R.perche_resta({"trunk_sid": numero.trunk_sid}):
			frappe.throw(_(motivo))
		pacchetto, indirizzo = R.cosa_serve(
			{"bundle_sid": numero.bundle_sid, "address_sid": numero.address_sid}
		)
		cliente = collegamento.Client(spazio, impostazioni.get_password("auth_token", raise_exception=False))
		valori = {"account_sid": spazio}
		if pacchetto:
			valori["bundle_sid"] = _clona(principale, numero.bundle_sid, spazio)
		if indirizzo:
			valori["address_sid"] = _copia_l_indirizzo(principale, cliente, numero.address_sid)
		principale.incoming_phone_numbers(number_sid).update(**valori)
		# in the space now: its calls and SMS to DottorCloud, like every other there
		collegamento._numeri(cliente)
	except collegamento.NON_RISPONDE as errore:
		collegamento._registra("DottorCloud: moving a number into the space", errore)
		frappe.throw(_in_parole(errore), title=_("Twilio"))
	collegamento._aggiorna_i_numeri()
	return {"number": numero.phone_number}


def _clona(principale, pacchetto: str, verso: str) -> str:
	"""The number's approved documents, copied into the space as Twilio's bundle clone:
	approved there too, so the number can move."""
	indirizzo = CLONI.format(pacchetto)
	risposta = principale.request("POST", indirizzo, data={"TargetAccountSid": verso, "MoveToDraft": "false"})
	try:
		dati = json.loads(risposta.text or "{}")
	except ValueError:
		dati = {}
	if risposta.status_code >= 400 or not dati.get("bundle_sid"):
		raise TwilioRestException(
			risposta.status_code,
			indirizzo,
			dati.get("message") or "No bundle in Twilio's answer",
			code=dati.get("code"),
		)
	return dati["bundle_sid"]


def _copia_l_indirizzo(principale, cliente, sid: str) -> str:
	"""The number's address, written again in the space: Twilio moves a number only
	to an account that has its address."""
	vecchio = principale.addresses(sid).fetch()
	return cliente.addresses.create(
		customer_name=vecchio.customer_name,
		street=vecchio.street,
		city=vecchio.city,
		region=vecchio.region,
		postal_code=vecchio.postal_code,
		iso_country=vecchio.iso_country,
		friendly_name=getattr(vecchio, "friendly_name", None) or vecchio.customer_name,
	).sid
