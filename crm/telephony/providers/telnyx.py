# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Telnyx, speaking TeXML (doc 65).

The decisions are the same as Twilio's - `crm.telephony.inbound` makes them - and
this renders them in TeXML, Telnyx's twin of TwiML. Where Twilio rings a browser
with ``<Client>``, Telnyx rings the person's credential at its SIP address; where
Twilio shows the caller's own number on a phone that is rung, Telnyx shows the
number called, the centre's: Telnyx refuses to present a number that is neither
its own nor verified (SIP 403 D51).
"""

from __future__ import annotations

import frappe

from crm.telephony.providers.base import Announcement, CallInstruction, Message, Ring, TelephonyProvider
from crm.telephony.telnyx import texml

#: Where Telnyx comes back to: the ringing over, a call's progress, a recording,
#: a message taken and its recording, the notice before a call is put through.
SQUILLO_FINITO = "/api/method/crm.integrations.telnyx.api.ring_ended"
STATO = "/api/method/crm.integrations.telnyx.api.call_status"
REGISTRAZIONE = "/api/method/crm.integrations.telnyx.api.recording_ready"
MESSAGGIO_PRESO = "/api/method/crm.integrations.telnyx.api.message_taken"
MESSAGGIO_REGISTRATO = "/api/method/crm.integrations.telnyx.api.message_recorded"
AVVISO = "/api/method/crm.integrations.telnyx.api.recording_notice"

#: A leg's progress, every step of it.
EVENTI = "initiated ringing answered completed"


def _indirizzo(percorso: str) -> str:
	from crm.integrations.telnyx.utils import get_public_url

	return get_public_url(percorso)


class TelnyxProvider(TelephonyProvider):
	name = "telnyx"
	label = "Telnyx"
	agent_number_field = "telnyx_number"
	controls_call_flow = True
	rings_browser = True

	def is_enabled(self) -> bool:
		return bool(frappe.db.get_single_value("CRM Telnyx Settings", "enabled"))

	def settings(self):
		return frappe.get_cached_doc("CRM Telnyx Settings")

	# ------------------------------------------------------------------
	# recording: on the call, its notice, where it goes
	# ------------------------------------------------------------------

	def recording_notice(self) -> str | None:
		"""What to say before connecting, when the call is being recorded."""
		impostazioni = self.settings()
		if not impostazioni.record_calls:
			return None
		return (impostazioni.recording_notice or "").strip() or None

	def _registra(self) -> dict:
		"""What a ``<Dial>`` carries to record the call, when the centre records."""
		if not self.settings().record_calls:
			return {}
		return {
			"record": "record-from-answer",
			"recordingChannels": "single",
			"recordingStatusCallback": _indirizzo(REGISTRAZIONE),
			"recordingStatusCallbackEvent": "completed",
			"recordingStatusCallbackMethod": "POST",
		}

	def _avviso(self, risposta: texml.Risposta) -> None:
		"""The recording notice, spoken to whoever is on the line already."""
		if avviso := self.recording_notice():
			from crm.telephony import answering

			config = answering.settings()
			risposta.say(avviso, voice=config.voice or "alice", language=config.language or "it-IT")

	def _segui(self) -> dict:
		"""What a leg carries so its progress comes back to the call's log."""
		return {
			"statusCallback": _indirizzo(STATO),
			"statusCallbackEvent": EVENTI,
			"statusCallbackMethod": "POST",
		}

	# ------------------------------------------------------------------
	# what an incoming call hears
	# ------------------------------------------------------------------

	def say(self, announcement: Announcement, hang_up: bool = True) -> CallInstruction:
		risposta = texml.Risposta()
		if announcement.audio_url:
			risposta.play(announcement.audio_url)
		elif announcement.text:
			risposta.say(
				announcement.text,
				voice=announcement.voice or "alice",
				language=announcement.language or "it-IT",
			)
		if hang_up:
			risposta.hangup()
		return CallInstruction(risposta.xml(), texml.MIMETYPE)

	def _sip_di(self, agenti) -> list[str]:
		"""The SIP addresses of the people's browsers: only those with a credential,
		which their browser made when it opened."""
		if not agenti:
			return []
		righe = frappe.get_all(
			"CRM Telephony Agent",
			filters={"name": ["in", list(agenti)], "telnyx_sip_username": ["is", "set"]},
			fields=["name", "telnyx_sip_username"],
		)
		per_nome = {riga.name: riga.telnyx_sip_username for riga in righe}
		return [texml.indirizzo_sip(per_nome[agente]) for agente in agenti if per_nome.get(agente)]

	def ring(self, ring: Ring) -> CallInstruction:
		"""One ``<Dial>`` with everyone in it: browsers and phones ring together, the
		first to pick up takes the call, and the end of the ringing comes back to
		``ring_ended``. The caller hears the ringing until somebody picks up, and the
		recording notice first, being already on the line."""
		risposta = texml.Risposta()
		self._avviso(risposta)
		segui = self._segui()
		# a browser sees who calls; a phone rung on its own network is shown the
		# centre's number, Telnyx refusing one that is neither its own nor verified
		mostrato = (ring.called or ring.caller_id) if ring.phones else (ring.caller_id or ring.called)
		risposta.dial(
			numeri=[(telefono, segui) for telefono in ring.phones],
			sip=[(indirizzo, segui) for indirizzo in self._sip_di(ring.agents)],
			callerId=mostrato,
			timeout=ring.seconds,
			action=_indirizzo(SQUILLO_FINITO),
			method="POST",
			answerOnBridge=True,
			ringTone="it",
			**self._registra(),
		)
		return CallInstruction(risposta.xml(), texml.MIMETYPE)

	def dial_agent(self, agent: str) -> CallInstruction:
		return self.ring(Ring(agents=(agent,)))

	def dial_phone(self, caller_id: str, to_number: str) -> CallInstruction:
		return self.ring(Ring(phones=(to_number,), caller_id=caller_id, called=caller_id))

	def take_message(self, announcement: Announcement, message: Message) -> CallInstruction:
		"""The announcement, the words before the tone, then ``<Record>``: the
		recording reaches ``message_recorded``, the end of it ``message_taken``."""
		risposta = texml.Risposta()
		if announcement.audio_url:
			risposta.play(announcement.audio_url)
		elif announcement.text:
			risposta.say(announcement.text, voice=announcement.voice, language=announcement.language)
		risposta.say(message.prompt, voice=message.voice, language=message.language)
		risposta.record(
			action=_indirizzo(MESSAGGIO_PRESO),
			method="POST",
			maxLength=message.seconds,
			timeout=5,
			playBeep=True,
			finishOnKey="#",
			trim="trim-silence",
			recordingStatusCallback=_indirizzo(MESSAGGIO_REGISTRATO),
			recordingStatusCallbackEvent="completed",
			recordingStatusCallbackMethod="POST",
		)
		return CallInstruction(risposta.xml(), texml.MIMETYPE)

	# ------------------------------------------------------------------
	# a call going out from the browser, once DottorCloud said yes
	# ------------------------------------------------------------------

	def verso(self, mostrato: str, destinazione: str) -> CallInstruction:
		"""The browser's call put through: ``destinazione`` rung showing ``mostrato``;
		the person being rung is the one to hear the recording notice, on their own
		leg (its ``url``), before they are connected."""
		risposta = texml.Risposta()
		numero = self._segui()
		if self.recording_notice():
			numero = {**numero, "url": _indirizzo(AVVISO), "method": "POST"}
		risposta.dial(
			numeri=[(destinazione, numero)],
			callerId=mostrato,
			answerOnBridge=True,
			**self._registra(),
		)
		return CallInstruction(risposta.xml(), texml.MIMETYPE)

	def rifiuta(self, motivo: str) -> CallInstruction:
		"""A call that may not leave: why, in words, and the line closed."""
		from crm.telephony import answering

		config = answering.settings()
		risposta = texml.Risposta().say(
			motivo, voice=config.voice or "alice", language=config.language or "it-IT"
		)
		return CallInstruction(risposta.hangup().xml(), texml.MIMETYPE)

	# ------------------------------------------------------------------
	# what this account can present, and how each number is routed
	# ------------------------------------------------------------------

	def list_caller_ids(self) -> list[dict]:
		"""Every number of the account and every verified one, with its routing.

		A number of the account is the centre's to show and to answer on, when it is
		on DottorCloud's TeXML application; a verified number may be shown, and its
		calls ring wherever the line is."""
		from crm.telephony.telnyx import collegamento
		from crm.telephony.telnyx.cliente import ErroreTelnyx, tutte

		impostazioni = self.settings()
		api_secret = collegamento.chiave(impostazioni)
		applicazione = str(impostazioni.texml_application_id or "")
		segno = collegamento.segno()
		agenzia = impostazioni.account_owner == "Agency"
		try:
			sms = {
				riga.get("phone_number"): bool((riga.get("features") or {}).get("sms"))
				for riga in tutte("phone_numbers/messaging", api_secret)
			}
		except ErroreTelnyx:
			sms = {}
		try:
			connessioni = {str(c.get("id")): c for c in tutte("connections", api_secret)}
		except ErroreTelnyx:
			connessioni = {}
		righe = []
		for numero in tutte("phone_numbers", api_secret):
			connessione = str(numero.get("connection_id") or "")
			if agenzia and connessione != applicazione and segno not in (numero.get("tags") or []):
				# the agency's account holds other sites' numbers: only this one's are listed
				continue
			altra = connessioni.get(connessione) or {}
			centralino = altra.get("record_type") in (
				"ip_connection",
				"fqdn_connection",
				"credential_connection",
			)
			righe.append(
				{
					"sid": str(numero.get("id") or ""),
					"phone_number": numero.get("phone_number"),
					"label": numero.get("customer_reference") or "",
					"source": "Account Number",
					"voice_capable": True,
					"sms_capable": bool(sms.get(numero.get("phone_number"))),
					"points_at_crm": bool(connessione) and connessione == applicazione,
					"sip_trunk_sid": connessione if centralino else None,
					"sip_trunk": (altra.get("connection_name") or connessione) if centralino else None,
					"voice_url": (
						(numero.get("connection_name") or altra.get("connection_name") or connessione)
						if connessione and connessione != applicazione and not centralino
						else None
					),
				}
			)
		try:
			verificati = tutte("verified_numbers", api_secret, pagina=250)
		except ErroreTelnyx:
			verificati = []
		for verificato in verificati:
			if not verificato.get("verified_at"):
				continue
			righe.append(
				{
					"sid": verificato.get("phone_number"),
					"phone_number": verificato.get("phone_number"),
					"label": "",
					"source": "Verified Caller ID",
					"voice_capable": True,
					"sms_capable": False,
				}
			)
		return righe
