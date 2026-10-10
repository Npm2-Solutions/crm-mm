# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The centre's SMS through Telnyx (doc 65): the same as through Twilio (doc 52,
fourth part), from the same one sender (`crm.telephony.sms.mittente`).

- **Going out**: ``POST /v2/messages`` from the centre's number or its name, with
  DottorCloud's messaging profile, which Telnyx wants for a name; Telnyx's refusal
  in words, its code kept, never the number nor the words in the log.
- **Coming in**: Telnyx posts every message to the profile's webhook
  (`crm.integrations.telnyx.api.sms`); it lands in the person's conversation, and a
  STOP, a START or a reminder's answer does what it does with Twilio. Telnyx itself
  stops the English STOP words on its numbers and answers them: then DottorCloud
  records the stop and sends no answer of its own.
- **How it went**: ``message.sent`` and ``message.finalized`` say it, the first
  error's code kept and said in words.
"""

from __future__ import annotations

import frappe
from frappe import _

from crm.telephony.telnyx import errori
from crm.telephony.telnyx import errori_regole as E
from crm.telephony.telnyx import regole as R
from crm.telephony.telnyx.cliente import ErroreTelnyx, chiama

MESSAGGIO = "CRM SMS Message"
MEDIUM = "Telnyx"


def consegna(doc) -> None:
	"""Hand a queued outgoing message to Telnyx; failures land on the doc, not the
	caller."""
	from crm.demo import guardie
	from crm.integrations.telnyx.utils import get_public_url
	from crm.telephony.telnyx import collegamento

	if guardie.trattenuto(doc.to):
		# a person of the demo data, or a part of it being made: kept in the
		# conversation as sent, never handed to Telnyx (crm.demo.guardie)
		doc.db_set({"status": "Sent"})
		return
	impostazioni = frappe.get_single(collegamento.IMPOSTAZIONI)
	api_secret = collegamento.chiave(impostazioni)
	if not (collegamento.collegato(impostazioni) and api_secret):
		doc.db_set({"status": "Failed", "error_message": _("Telnyx is not enabled")})
		return
	corpo = {
		"from": doc.get("from"),
		"to": doc.to,
		"text": doc.message,
		"webhook_url": get_public_url(collegamento.SMS_IN_ARRIVO),
	}
	if impostazioni.messaging_profile_id:
		corpo["messaging_profile_id"] = impostazioni.messaging_profile_id
	try:
		risposto = chiama("POST", "messages", api_secret, corpo=corpo)
	except ErroreTelnyx as errore:
		# Telnyx's refusal in words, its code kept; the log has the code, not the person
		frappe.log_error(
			title="CRM SMS: Telnyx send failed", message=f"HTTP {errore.stato}, error {errore.codice}"
		)
		doc.db_set(
			{
				"status": "Failed",
				"error_code": E.codice(errore.codice) or 0,
				"error_message": errore.in_parole()
				if errore.stato is None or errore.stato in (401, 403)
				else errori.in_parole(errore.codice, errore.dettaglio),
			}
		)
		return
	dati = (risposto or {}).get("data") or {}
	doc.db_set({"message_sid": dati.get("id") or "", "status": "Sent"})


def _numero(parte) -> str:
	if isinstance(parte, dict):
		return parte.get("phone_number") or ""
	if isinstance(parte, list) and parte:
		return _numero(parte[0])
	return parte if isinstance(parte, str) else ""


def ricevuto(payload: dict) -> None:
	"""A message that reached one of the centre's numbers: in the person's
	conversation, and a STOP, a START or a reminder's answer heard."""
	from crm.api.sms import create_sms
	from crm.telephony import sms as sms_del_centro

	da, a = _numero(payload.get("from")), _numero(payload.get("to"))
	messaggio = None
	try:
		messaggio = create_sms(
			type="Incoming",
			from_number=da,
			to=a,
			message=payload.get("text") or "",
			telephony_medium=MEDIUM,
		)
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="Error while creating Telnyx SMS log")
		return

	# a STOP stops the centre's automatic SMS, a START has them again (doc 52), a
	# «SI» or a «NO» answers a reminder (doc 59); one that fails takes nothing of
	# the message with it
	frappe.db.savepoint("stop_o_start")
	try:
		risposta = sms_del_centro.ascolta(messaggio)
		# Telnyx stopped (or started) the number itself and answered it already
		gia_risposto = bool(risposta and payload.get("autoresponse_type"))
		if not risposta:
			from crm.scheduling import promemoria

			risposta = promemoria.alla_risposta_sms(messaggio)
		if risposta and not gia_risposto:
			doc = create_sms(
				type="Outgoing",
				from_number=a,
				to=da,
				message=risposta,
				reference_doctype=messaggio.reference_doctype,
				reference_name=messaggio.reference_name,
				telephony_medium=MEDIUM,
			)
			consegna(doc)
	except Exception:
		frappe.db.rollback(save_point="stop_o_start")
		frappe.log_error(title="DottorCloud: a STOP, a START or a reminder's answer by SMS not taken")


def aggiornato(payload: dict) -> None:
	"""How a message the centre sent went: sent, delivered, or why not."""
	destinatari = payload.get("to") or []
	primo = destinatari[0] if destinatari and isinstance(destinatari[0], dict) else {}
	stato = R.stato_sms(primo.get("status"))
	nome = payload.get("id") and frappe.db.get_value(MESSAGGIO, {"message_sid": payload.get("id")})
	if not (nome and stato):
		return
	valori = {"status": stato}
	if stato in ("Undelivered", "Failed"):
		codice, testo = E.primo_errore(payload.get("errors"))
		if codice:
			# why it did not arrive, in words (doc 52)
			valori.update(error_code=codice, error_message=errori.in_parole(codice, testo))
	frappe.db.set_value(MESSAGGIO, nome, valori)
