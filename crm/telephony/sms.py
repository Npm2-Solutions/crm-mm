# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The centre's SMS through its carrier, Twilio or Telnyx (doc 52, fourth part;
doc 65).

Every SMS DottorCloud sends - the one written by hand from a person's page, an
automation's, a waiting list's offer, the news of the client area - leaves from
one sender, the centre's: its name, or one of its numbers when the answers must
come back. Before, each place had its own, and a person could get the centre's
messages from four different senders. The rules without a site are in
``sms_regole``.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, now_datetime

from crm.telephony import operatore
from crm.telephony import sms_regole as R

#: Twilio's settings, as the callers of before name them: the centre's carrier's
#: are `operatore.impostazioni()`.
IMPOSTAZIONI = operatore.IMPOSTAZIONI[operatore.TWILIO]
NOME, NUMERO = "Name", "Number"
#: The consent a STOP withdraws: news, offers and recalls, the centre's marketing.
CONSENSO = "marketing"
#: How the register says it arrived.
CANALE = "By SMS"


def numeri_sms(nome: str | None = None) -> list[str]:
	"""The numbers of the centre's carrier (or of ``nome``) that can send SMS."""
	nome = nome or operatore.attivo()
	if not nome:
		return []
	return frappe.get_all(
		"CRM Caller ID",
		filters={"enabled": 1, "provider": nome, "sms_capable": 1},
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
	made from the centre's. None while no carrier is connected, or with nothing to
	send from."""
	nome = operatore.attivo()
	if not nome:
		return None
	scelta = frappe.db.get_singles_dict(operatore.impostazioni(nome))
	if not cint(scelta.get("enabled")):
		return None
	numeri = numeri_sms(nome)
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


# ------------------------------------------------------------------ STOP and START


def persona_di(doctype: str | None, nome: str | None) -> str | None:
	"""The person a record is about: the person, or a deal's."""
	if doctype == "CRM Lead":
		return nome
	if doctype == "CRM Deal" and nome:
		return frappe.db.get_value("CRM Deal", nome, "lead")
	return None


def ha_fermato(doctype: str | None, nome: str | None) -> bool:
	"""Whether the person of a record wrote STOP to the centre's SMS."""
	persona = persona_di(doctype, nome)
	return bool(persona and cint(frappe.db.get_value("CRM Lead", persona, "sms_opt_out")))


def fermato_il(doctype: str | None, nome: str | None):
	"""When the person of a record wrote STOP, or None."""
	persona = persona_di(doctype, nome)
	if not persona:
		return None
	fermo = frappe.db.get_value("CRM Lead", persona, ["sms_opt_out", "sms_opt_out_on"], as_dict=True)
	return fermo.sms_opt_out_on if fermo and cint(fermo.sms_opt_out) else None


def ascolta(messaggio) -> str:
	"""An SMS received that is nothing but STOP or START: the person stops the
	centre's automatic SMS, or has them again. The answer to send back; '' for a
	message, which stays a message."""
	parola = R.parola_chiave(messaggio.message)
	persona = persona_di(messaggio.reference_doctype, messaggio.reference_name)
	if not (parola and persona):
		return ""
	from crm.moduli.richieste import nome_del_centro

	centro = nome_del_centro()
	if parola == "stop":
		ferma(persona)
		if not centro:
			return _("You will not receive our automatic SMS any more. Write START to have them again.")
		return _(
			"You will not receive automatic SMS from {0} any more. Write START to have them again."
		).format(centro)
	riprendi(persona)
	if not centro:
		return _("You will receive our SMS again. Write STOP to stop them.")
	return _("You will receive the SMS of {0} again. Write STOP to stop them.").format(centro)


def ferma(persona: str) -> None:
	"""No automatic SMS reaches the person any more, and the register says they
	said no to the centre's marketing: the consent withdrawn, or refused when there
	was none."""
	from crm.moduli import consensi, registro

	frappe.db.set_value("CRM Lead", persona, {"sms_opt_out": 1, "sms_opt_out_on": now_datetime()})
	nota = _("Wrote STOP by SMS")
	try:
		stato = consensi.stato(persona, CONSENSO)
		if stato == registro.DATO:
			consensi.revoca(persona, CONSENSO, canale=CANALE, nota=nota)
		elif stato is None:
			consensi.registra_risposta(persona, CONSENSO, stato=registro.RIFIUTATO, canale=CANALE, nota=nota)
	except frappe.ValidationError:
		# the stop holds whatever the register says; what it refused is kept
		frappe.log_error(title="DottorCloud: a STOP the consent register did not take")


def riprendi(persona: str) -> None:
	"""The automatic SMS reach the person again; the marketing consent is not
	given back by a word: it is asked again, the way it always is."""
	frappe.db.set_value("CRM Lead", persona, {"sms_opt_out": 0, "sms_opt_out_on": None})


def valida_il_mittente(impostazioni) -> None:
	"""The SMS sender as the carrier takes it: a name it accepts, or one of its
	numbers that can send SMS. Asked only when the choice changes: a number taken
	away later is the sender's fallback's business, not every save's."""
	if not any(
		impostazioni.has_value_changed(campo)
		for campo in ("sms_from", "sms_sender_name", "sms_sender_number")
	):
		return
	if impostazioni.sms_from == NOME:
		impostazioni.sms_sender_name = (impostazioni.sms_sender_name or "").strip()
		if motivo := R.problema_del_nome(impostazioni.sms_sender_name):
			frappe.throw(_(motivo), title=_("SMS Sender"))
	elif impostazioni.sms_from == NUMERO:
		nome = next((n for n, d in operatore.IMPOSTAZIONI.items() if d == impostazioni.doctype), None)
		if impostazioni.sms_sender_number not in numeri_sms(nome):
			frappe.throw(_("Choose one of the numbers that can send SMS."), title=_("SMS Sender"))


@frappe.whitelist()
def get_sms_sender_options() -> dict:
	"""For the carrier's page: its numbers that can send SMS, the name made from
	the centre's, and who the SMS come from now."""
	from crm.permissions import livelli

	livelli.verifica_nel_crm("telefono.configura")
	nome = operatore.attivo()
	etichette = dict(
		frappe.get_all(
			"CRM Caller ID",
			filters={"enabled": 1, "provider": nome or "", "sms_capable": 1},
			fields=["phone_number", "label"],
			as_list=True,
		)
	)
	return {
		"numbers": [{"number": n, "label": etichette.get(n) or ""} for n in numeri_sms(nome)],
		"name": nome_proposto(),
		"sender": mittente(),
	}
