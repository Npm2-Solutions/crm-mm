# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Where Telnyx calls DottorCloud (doc 64), and the browser's phone.

TeXML's callbacks come form-encoded, the messaging profile's events as JSON; all
are signed by Telnyx with the account's key (Ed25519 over the timestamp and the
raw body), and nothing is read before the signature is right. A request about a
connection or a messaging profile that is not DottorCloud's is refused too: the
agency's account holds other sites' resources, signed with the same key.

- ``incoming_call``: a call to one of the centre's numbers (the TeXML application's
  voice URL): the answering service, or everyone ringing at once;
- ``ring_ended``, ``message_taken``, ``message_recorded``: as with Twilio;
- ``call_status``: a call's progress, onto its log;
- ``recording_ready``: a recorded call, fetched at once (the link lasts ten minutes);
- ``voice``: a call from a browser, parked by Telnyx until DottorCloud says where it
  may go and which number it shows;
- ``recording_notice``: what the person being called hears first, when the call is
  recorded;
- ``sms``: the messages that arrive, and how the ones sent went;
- ``generate_access_token``, ``prepare_call``: the browser's phone.
"""

from __future__ import annotations

import time

import frappe
from frappe import _
from frappe.utils import cint, get_datetime
from werkzeug.wrappers import Response

from crm.telephony import inbound, operatore, uscita
from crm.telephony.providers import get as get_provider
from crm.telephony.telnyx import regole as R
from crm.telephony.telnyx import texml

REGISTRO = "CRM Call Log"
#: How long a call the browser announced waits for Telnyx to ask about it, in seconds.
ATTESA_DELLA_CHIAMATA = 120
#: How long an event of Telnyx's is remembered, so that one delivered twice counts once.
EVENTO_VISTO = 24 * 3600


def _impostazioni():
	return frappe.get_single("CRM Telnyx Settings")


def _controllo_acceso(impostazioni) -> bool:
	"""On unless it has been switched off on purpose: nothing stored reads as on."""
	stored = impostazioni.get("verify_webhook_signature")
	return True if stored is None else bool(cint(stored))


def valida_la_richiesta() -> object:
	"""Refuse anything Telnyx did not send: the signature is the gate. Returns the
	settings."""
	from crm.telephony.telnyx import collegamento

	impostazioni = _impostazioni()
	if not collegamento.collegato(impostazioni):
		frappe.throw(_("Telnyx configuration is missing"), frappe.PermissionError)
	if _controllo_acceso(impostazioni):
		richiesta = getattr(frappe.local, "request", None)
		if not richiesta:
			frappe.throw(_("Invalid Telnyx signature"), frappe.PermissionError)
		if not R.firma_valida(
			richiesta.get_data(cache=True) or b"",
			richiesta.headers.get("telnyx-signature-ed25519"),
			richiesta.headers.get("telnyx-timestamp"),
			collegamento.pubblica(impostazioni),
			time.time(),
		):
			frappe.throw(_("Invalid Telnyx signature"), frappe.PermissionError)
	return impostazioni


def _della_connessione(args, impostazioni) -> None:
	"""A call of another site's connection, signed with the same account's key - the
	agency's account holds every site's resources - is not this site's to act on."""
	from crm.telephony.telnyx import collegamento

	if impostazioni.account_owner != R.AGENZIA:
		return
	connessione = frappe.utils.cstr(args.get("ConnectionId"))
	if connessione and connessione not in collegamento.nostre(impostazioni):
		frappe.throw(_("Invalid Telnyx connection"), frappe.PermissionError)


def _texml(istruzione) -> Response:
	return Response(istruzione.body, mimetype=istruzione.mimetype)


def _ricevuto() -> Response:
	"""An empty TeXML 200 — received, nothing to say, do not retry."""
	return Response(texml.vuota(), mimetype=texml.MIMETYPE)


def _scuse() -> Response:
	from crm.telephony import answering

	config = answering.settings()
	risposta = texml.Risposta().say(
		_("We're unable to connect your call right now. Please try again later."),
		voice=config.voice or "alice",
		language=config.language or "it-IT",
	)
	return Response(risposta.hangup().xml(), mimetype=texml.MIMETYPE)


def _numero(valore: str | None) -> str:
	"""A number as a callback carries it: "+39…", or a SIP address with it."""
	valore = (valore or "").strip()
	if valore.lower().startswith("sip:"):
		valore = valore[4:].split("@", 1)[0]
	return valore


def _quando(valore) -> str | None:
	"""A moment of Telnyx's (ISO, in UTC unless it says otherwise) as the site's
	clock reads it."""
	from datetime import timezone

	from frappe.utils import convert_utc_to_system_timezone

	if not valore:
		return None
	try:
		momento = get_datetime(valore)
	except Exception:
		return None
	if momento.tzinfo is not None:
		momento = momento.astimezone(timezone.utc).replace(tzinfo=None)
	return str(convert_utc_to_system_timezone(momento).replace(tzinfo=None, microsecond=0))


# ---------------------------------------------------------------------------
# the call's log


def _registro(call_sid: str, tipo: str, da: str, a: str, stato: str, chiamante: str | None = None):
	"""The call's log, linked to the person whose number it is."""
	from crm.integrations.twilio.api import link

	call_log = frappe.get_doc(
		{
			"doctype": REGISTRO,
			"id": call_sid,
			"type": tipo,
			"status": stato,
			"from": da,
			"to": a,
			"caller": chiamante or "",
			"receiver": "",
			"telephony_medium": operatore.ETICHETTE[operatore.TELNYX],
		}
	)
	link(da if tipo == "Incoming" else a, call_log)
	call_log.save(ignore_permissions=True)
	frappe.db.commit()  # nosemgrep: frappe-manual-commit — the caller's except rolls back; a real call must not vanish
	return call_log


# ---------------------------------------------------------------------------
# a call to one of the centre's numbers


# webhook authenticity is enforced by valida_la_richiesta(); Telnyx posts here, as it is told
@frappe.whitelist(allow_guest=True, methods=["POST"])  # nosemgrep: guest-whitelisted-method
def incoming_call(**kwargs):
	"""A call to one of the centre's numbers: the answering service, or everyone
	who answers the number ringing at once."""
	args = frappe._dict(kwargs)
	impostazioni = valida_la_richiesta()
	_della_connessione(args, impostazioni)

	if args.CallSid and frappe.db.exists(REGISTRO, args.CallSid):
		# Telnyx asked again for the same call
		call_log = frappe.get_doc(REGISTRO, args.CallSid)
	else:
		try:
			call_log = _registro(
				args.CallSid,
				"Incoming",
				args.From,
				args.To,
				R.stato_chiamata(args.CallStatus or "ringing"),
			)
		except Exception:
			frappe.db.rollback()
			frappe.log_error(title="Error while creating Telnyx call log")
			frappe.db.commit()
			return _scuse()

	istruzione = inbound.handle_incoming_call(
		get_provider(operatore.TELNYX), args.From, args.To, call_log=call_log
	)
	frappe.db.commit()  # nosemgrep: frappe-manual-commit — Telnyx calls back into this log before we are done
	return _texml(istruzione)


# webhook authenticity is enforced by valida_la_richiesta(); Telnyx posts here, as it is told
@frappe.whitelist(allow_guest=True, methods=["POST"])  # nosemgrep: guest-whitelisted-method
def ring_ended(**kwargs):
	"""Everyone rang: picked up, nothing more is said; nobody did, the answering
	service or the apology."""
	args = frappe._dict(kwargs)
	impostazioni = valida_la_richiesta()
	_della_connessione(args, impostazioni)

	if (args.DialCallStatus or "").lower() in ("completed", "answered", "in-progress"):
		return Response(texml.Risposta().hangup().xml(), mimetype=texml.MIMETYPE)

	call_log = frappe.get_doc(REGISTRO, args.CallSid) if frappe.db.exists(REGISTRO, args.CallSid) else None
	istruzione = inbound.nobody_answered(get_provider(operatore.TELNYX), call_log=call_log)
	frappe.db.commit()  # nosemgrep: frappe-manual-commit — the callback queued here must be there when Telnyx calls back
	return _texml(istruzione)


# webhook authenticity is enforced by valida_la_richiesta(); Telnyx posts here, as it is told
@frappe.whitelist(allow_guest=True, methods=["POST"])  # nosemgrep: guest-whitelisted-method
def message_taken(**kwargs):
	"""The caller finished the message, or hung up: thanks, and goodbye."""
	from crm.telephony import answering

	args = frappe._dict(kwargs)
	impostazioni = valida_la_richiesta()
	_della_connessione(args, impostazioni)

	config = answering.settings()
	risposta = texml.Risposta()
	if cint(args.RecordingDuration) > 0 or (args.RecordingUrl and args.RecordingDuration is None):
		risposta.say(
			answering.message_thanks(), voice=config.voice or "alice", language=config.language or "it-IT"
		)
	return Response(risposta.hangup().xml(), mimetype=texml.MIMETYPE)


# webhook authenticity is enforced by valida_la_richiesta(); Telnyx posts here, as it is told
@frappe.whitelist(allow_guest=True, methods=["POST"])  # nosemgrep: guest-whitelisted-method
def message_recorded(**kwargs):
	"""A message left on the answering service, recorded: fetched at once onto the
	call, then written out when transcription is on and told to whoever follows the
	caller (`registrazioni.scarica`)."""
	from crm.telephony.telnyx import registrazioni

	args = frappe._dict(kwargs)
	impostazioni = valida_la_richiesta()
	_della_connessione(args, impostazioni)

	call_sid = args.CallSid
	if not (call_sid and frappe.db.exists(REGISTRO, call_sid)):
		frappe.log_error(f"Telnyx message for an unknown call: {call_sid}", "CRM Telephony")
		return _ricevuto()
	if not args.RecordingUrl or (args.RecordingDuration is not None and cint(args.RecordingDuration) < 1):
		# the tone, then silence: nothing was left
		return _ricevuto()
	registrazioni.accoda(call_sid, args.RecordingUrl, messaggio=True)
	frappe.db.commit()  # nosemgrep: frappe-manual-commit — the job is queued after the commit
	return _ricevuto()


# webhook authenticity is enforced by valida_la_richiesta(); Telnyx posts here, as it is told
@frappe.whitelist(allow_guest=True, methods=["POST"])  # nosemgrep: guest-whitelisted-method
def recording_ready(**kwargs):
	"""A recorded call: its recording fetched at once, before Telnyx's link expires."""
	from crm.telephony.telnyx import registrazioni

	args = frappe._dict(kwargs)
	impostazioni = valida_la_richiesta()
	_della_connessione(args, impostazioni)

	call_sid = args.ParentCallSid if frappe.db.exists(REGISTRO, args.ParentCallSid or "") else args.CallSid
	if not (call_sid and frappe.db.exists(REGISTRO, call_sid)):
		frappe.log_error(f"Telnyx recording for an unknown call: {call_sid}", "CRM Telephony")
		return _ricevuto()
	if args.RecordingUrl and (args.RecordingStatus or "completed") == "completed":
		registrazioni.accoda(call_sid, args.RecordingUrl)
		frappe.db.commit()  # nosemgrep: frappe-manual-commit — the job is queued after the commit
	return _ricevuto()


#: How far a call went: a leg of the same call that rang and lost does not take
#: back what another one reached.
_PASSI = {
	"Queued": 0,
	"Initiated": 1,
	"Ringing": 2,
	"No Answer": 3,
	"Busy": 3,
	"Failed": 3,
	"Canceled": 3,
	"In Progress": 4,
	"Completed": 5,
}


def _chi_ha_risposto(destinazione: str | None) -> str | None:
	"""Who picked up a leg: the person whose browser it rang, or whose mobile."""
	utente_sip = texml.utente_sip(destinazione)
	if utente_sip:
		return frappe.db.get_value("CRM Telephony Agent", {"telnyx_sip_username": utente_sip}, "name")
	numero = _numero(destinazione)
	if numero:
		return frappe.db.get_value("CRM Telephony Agent", {"mobile_no": numero}, "name")
	return None


# webhook authenticity is enforced by valida_la_richiesta(); Telnyx posts here, as it is told
@frappe.whitelist(allow_guest=True, methods=["POST"])  # nosemgrep: guest-whitelisted-method
def call_status(**kwargs):
	"""A call's progress onto its log: a leg rung by ``<Dial>`` (``ParentCallSid``)
	or the call itself (the TeXML application's status callback)."""
	args = frappe._dict(kwargs)
	impostazioni = valida_la_richiesta()
	_della_connessione(args, impostazioni)

	padre = args.ParentCallSid or ""
	nome = padre if frappe.db.exists(REGISTRO, padre) else args.CallSid
	if not (nome and frappe.db.exists(REGISTRO, nome)):
		return _ricevuto()

	if padre and nome == padre and args.CallSid:
		# the leg is the browser's call for a while: its notes go on the call's log
		frappe.cache.set_value(_chiave_gamba(args.CallSid), padre, expires_in_sec=4 * 3600)
	call_log = frappe.get_doc(REGISTRO, nome)
	stato = R.stato_chiamata(args.CallStatus)
	valori = {}
	if _PASSI.get(stato, 0) >= _PASSI.get(call_log.status, 0):
		valori["status"] = stato
	if padre and stato == "In Progress" and call_log.type == "Incoming" and not call_log.receiver:
		if chi := _chi_ha_risposto(args.To):
			valori["receiver"] = chi
	if (args.CallStatus or "").lower() == "completed" and (not padre or nome == padre):
		durata = cint(args.CallDuration) or cint(args.DialCallDuration)
		if durata:
			valori["duration"] = durata
		if inizio := _quando(args.StartTime or args.AnsweredTime):
			valori["start_time"] = inizio
		if fine := _quando(args.EndTime):
			valori["end_time"] = fine
	if valori:
		call_log.update(valori)
		call_log.save(ignore_permissions=True)
	return _ricevuto()


def _chiave_gamba(call_sid: str) -> str:
	return f"dottorcloud:telnyx:gamba:{call_sid}"


@frappe.whitelist()
def call_log_for(call_control_id: str) -> str | None:
	"""The call's log a browser's leg belongs to: its own, for a call it placed; the
	call that rang it, for one it answered."""
	from crm.permissions import livelli

	livelli.verifica_nel_crm(uscita.CHIAMA)
	if not call_control_id:
		return None
	if frappe.db.exists(REGISTRO, call_control_id):
		return call_control_id
	padre = frappe.cache.get_value(_chiave_gamba(call_control_id))
	return padre if padre and frappe.db.exists(REGISTRO, padre) else None


@frappe.whitelist()
def who_is_calling(number: str) -> dict:
	"""Who a call ringing in the browser is from, when the browser is shown the
	centre's number (a phone was rung too): the last call to that number, still
	ringing."""
	from frappe.utils import add_to_date, now_datetime

	from crm.permissions import livelli

	livelli.verifica_nel_crm(uscita.CHIAMA)
	riga = frappe.get_all(
		REGISTRO,
		filters={
			"to": number,
			"type": "Incoming",
			"telephony_medium": "Telnyx",
			"status": ["in", ["Initiated", "Ringing", "Queued"]],
			"creation": [">", add_to_date(now_datetime(), seconds=-90)],
		},
		fields=["from"],
		order_by="creation desc",
		limit=1,
	)
	return {"number": riga[0]["from"] if riga else None}


# ---------------------------------------------------------------------------
# a call from the browser


def _chiave_di(utente_sip: str) -> str:
	return f"dottorcloud:telnyx:chiamata:{utente_sip}"


def _chiave_verso(numero: str) -> str:
	return f"dottorcloud:telnyx:verso:{''.join(c for c in numero if c.isdigit())}"


@frappe.whitelist(methods=["POST"])
def prepare_call(number: str, show: str | None = None) -> dict:
	"""The browser is about to call ``number`` showing ``show``: whether it may, and
	what Telnyx's question about the call will be answered with. The server decides
	again when Telnyx asks (`voice`), whatever the browser did."""
	from crm.permissions import livelli
	from crm.telephony.telnyx import collegamento

	livelli.verifica_nel_crm(uscita.CHIAMA)
	if motivo := uscita.perche_no(number, operatore.TELNYX):
		return {"ok": False, "reason": motivo}
	propria = collegamento.credenziale(frappe.session.user)
	intenzione = {"user": frappe.session.user, "to": number, "show": show or ""}
	if propria:
		frappe.cache.set_value(
			_chiave_di(propria["sip_username"]), intenzione, expires_in_sec=ATTESA_DELLA_CHIAMATA
		)
	frappe.cache.set_value(_chiave_verso(number), intenzione, expires_in_sec=ATTESA_DELLA_CHIAMATA)
	return {"ok": True}


def _chi_chiama(richiesta) -> tuple[str | None, str | None]:
	"""Who places a call from the browser, and the number they chose to show: by
	the credential it comes from, else by the call DottorCloud was told of."""
	utente_sip = texml.utente_sip(richiesta.From) or texml.utente_sip(richiesta.CallerId)
	utente = (
		frappe.db.get_value("CRM Telephony Agent", {"telnyx_sip_username": utente_sip}, "name")
		if utente_sip
		else None
	)
	intenzione = frappe.cache.get_value(_chiave_di(utente_sip)) if utente_sip else None
	if not intenzione:
		intenzione = frappe.cache.get_value(_chiave_verso(_numero(richiesta.To)))
		if intenzione and utente and intenzione.get("user") != utente:
			intenzione = None
	if intenzione:
		return intenzione.get("user"), intenzione.get("show") or None
	numero = _numero(richiesta.From)
	return utente, (numero if numero.startswith("+") else None)


# webhook authenticity is enforced by valida_la_richiesta(); Telnyx asks here about every
# call a browser places on DottorCloud's credential connection, parked until it answers
@frappe.whitelist(allow_guest=True, methods=["POST"])  # nosemgrep: guest-whitelisted-method
def voice(**kwargs):
	"""A call from a browser: where it may go (the centre's countries, never a
	premium-rate number) and the number it shows - the one chosen when it is the
	centre's, else the person's own line; never one the browser made up."""
	args = frappe._dict(kwargs)
	impostazioni = valida_la_richiesta()
	_della_connessione(args, impostazioni)
	provider = get_provider(operatore.TELNYX)

	destinazione = _numero(args.To)
	if motivo := uscita.perche_no(destinazione, operatore.TELNYX):
		return _texml(provider.rifiuta(motivo))

	utente, scelto = _chi_chiama(args)
	mostrato = uscita.numero_da_mostrare(utente, scelto, operatore.TELNYX)
	if not mostrato:
		return _texml(
			provider.rifiuta(
				_("Your account has no number to call from. Ask whoever manages the centre's phone.")
			)
		)
	try:
		_registro(args.CallSid, "Outgoing", mostrato, destinazione, "Initiated", chiamante=utente)
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="Error while creating Telnyx call log")
		frappe.db.commit()
		return _scuse()
	# outgoing: the person being rung is the one who has not been told yet
	return _texml(provider.verso(mostrato, destinazione))


# webhook authenticity is enforced by valida_la_richiesta(); Telnyx asks here before it puts
# the person being called through
@frappe.whitelist(allow_guest=True, methods=["POST"])  # nosemgrep: guest-whitelisted-method
def recording_notice(**kwargs):
	"""Spoken to the person being called, before they are connected: recording
	someone without telling them is not a choice a practice gets to make."""
	from crm.telephony import answering

	valida_la_richiesta()
	risposta = texml.Risposta()
	if avviso := get_provider(operatore.TELNYX).recording_notice():
		config = answering.settings()
		risposta.say(avviso, voice=config.voice or "alice", language=config.language or "it-IT")
	return Response(risposta.xml(), mimetype=texml.MIMETYPE)


@frappe.whitelist()
def generate_access_token():
	"""The token the browser's phone registers with: Telnyx's JWT for the person's
	credential on DottorCloud's credential connection, a day long."""
	from crm.telephony.telnyx import collegamento

	impostazioni = _impostazioni()
	if not collegamento.collegato(impostazioni):
		return {}
	if not frappe.db.get_value("CRM Telephony Agent", frappe.session.user, operatore.linea(operatore.TELNYX)):
		return {
			"ok": False,
			"error": "caller_phone_identity_missing",
			"detail": "Phone number is not mapped to the caller",
		}
	try:
		gettone = collegamento.gettone(frappe.session.user)
	except collegamento.NON_RISPONDE as errore:
		from crm.telephony.telnyx.cliente import registra

		registra("DottorCloud: a Telnyx browser token", errore)
		return {"ok": False, "error": "token", "detail": errore.in_parole()}
	return {"token": gettone} if gettone else {}


# ---------------------------------------------------------------------------
# the SMS


# webhook authenticity is enforced by valida_la_richiesta(); the messaging profile posts here.
# The request commits what it wrote.
@frappe.whitelist(allow_guest=True, methods=["POST"])  # nosemgrep: guest-whitelisted-method
def sms(**kwargs):
	"""The messaging profile's events: a message received, how one sent went."""
	from crm.telephony.telnyx import sms as sms_telnyx

	impostazioni = valida_la_richiesta()
	corpo = (frappe.request.get_data(cache=True) or b"{}").decode("utf-8", "replace")
	try:
		evento = frappe.parse_json(corpo) or {}
	except ValueError:
		evento = {}
	dati = evento.get("data") or {}
	payload = dati.get("payload") or {}
	profilo = payload.get("messaging_profile_id")
	if (
		profilo
		and impostazioni.messaging_profile_id
		and str(profilo) != str(impostazioni.messaging_profile_id)
	):
		frappe.throw(_("Invalid Telnyx messaging profile"), frappe.PermissionError)
	# an event delivered twice counts once
	# nosemgrep: frappe-cache-breaks-multitenancy — make_key puts the site's prefix on it
	if dati.get("id") and not frappe.cache.set(
		frappe.cache.make_key(f"dottorcloud:telnyx:evento:{dati['id']}"), 1, nx=True, ex=EVENTO_VISTO
	):
		return {"ok": True}
	tipo = dati.get("event_type")
	if tipo == "message.received":
		sms_telnyx.ricevuto(payload)
	elif tipo in ("message.sent", "message.finalized"):
		sms_telnyx.aggiornato(payload)
	return {"ok": True}
