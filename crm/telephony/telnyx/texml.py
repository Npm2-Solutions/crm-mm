# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""TeXML, Telnyx's call-control markup, without a site (doc 64).

TeXML is TwiML's twin: a ``<Response>`` of verbs - ``<Say>``, ``<Play>``,
``<Dial>`` with its ``<Number>`` and ``<Sip>``, ``<Record>``, ``<Hangup>`` - that
Telnyx runs on a call and answers with form-encoded callbacks. What differs from
Twilio's, and is written here so nobody meets it on a live call:

- there is no ``<Client>``: a browser is rung at its credential's SIP address,
  ``sip:<sip_username>@sip.telnyx.com``;
- ``<Record>`` records both sides and never stops on silence unless asked:
  ``channels="single"`` and a ``timeout`` are always written;
- attributes are case-sensitive and an unknown one is silently ignored.

The verbs are built with ElementTree, so a centre's words in an announcement are
escaped, whatever they hold.
"""

from __future__ import annotations

from xml.etree import ElementTree as ET

#: Where a browser registered with a telephony credential is rung.
DOMINIO_SIP = "sip.telnyx.com"
#: What TeXML is answered with.
MIMETYPE = "text/xml"


def _attributi(valori: dict) -> dict:
	"""Attributes as TeXML reads them: words, the booleans in lower case, nothing
	for what is not set."""
	attributi = {}
	for nome, valore in valori.items():
		if valore is None or valore == "":
			continue
		if isinstance(valore, bool):
			valore = "true" if valore else "false"
		attributi[nome] = str(valore)
	return attributi


class Risposta:
	"""A ``<Response>`` being written, verb after verb."""

	def __init__(self):
		self.radice = ET.Element("Response")

	def _verbo(self, nome: str, testo: str | None = None, **valori) -> ET.Element:
		elemento = ET.SubElement(self.radice, nome, _attributi(valori))
		if testo:
			elemento.text = testo
		return elemento

	def say(self, testo: str, voice: str | None = None, language: str | None = None) -> Risposta:
		self._verbo("Say", testo, voice=voice, language=language)
		return self

	def play(self, indirizzo: str) -> Risposta:
		self._verbo("Play", indirizzo)
		return self

	def hangup(self) -> Risposta:
		self._verbo("Hangup")
		return self

	def reject(self, motivo: str = "rejected") -> Risposta:
		self._verbo("Reject", reason=motivo)
		return self

	def record(self, **valori) -> Risposta:
		"""``<Record>`` as DottorCloud wants it: one channel, the caller's alone."""
		self._verbo("Record", **{"channels": "single", **valori})
		return self

	def dial(self, numeri=(), sip=(), **valori) -> Risposta:
		"""``<Dial>`` with every phone of ``numeri`` and every address of ``sip``:
		``(destination, attributes)`` pairs. All ring at once; the first to answer
		takes the call."""
		dial = self._verbo("Dial", **valori)
		for destinazione, attributi in numeri:
			ET.SubElement(dial, "Number", _attributi(attributi or {})).text = destinazione
		for destinazione, attributi in sip:
			ET.SubElement(dial, "Sip", _attributi(attributi or {})).text = destinazione
		return self

	def xml(self) -> str:
		return '<?xml version="1.0" encoding="UTF-8"?>' + ET.tostring(self.radice, encoding="unicode")


def indirizzo_sip(sip_username: str) -> str:
	"""Where a browser with this credential is rung."""
	return f"sip:{sip_username}@{DOMINIO_SIP}"


def utente_sip(valore: str | None) -> str:
	"""The SIP username in an address or a caller ("sip:gencredAb1@sip.telnyx.com",
	"gencredAb1"); '' for a phone number."""
	valore = (valore or "").strip()
	if valore.lower().startswith("sip:"):
		valore = valore[4:]
	utente = valore.split("@", 1)[0]
	if not utente or utente.lstrip("+").isdigit():
		return ""
	return utente


def vuota() -> str:
	"""An empty answer: received, nothing to say, do not retry."""
	return Risposta().xml()
