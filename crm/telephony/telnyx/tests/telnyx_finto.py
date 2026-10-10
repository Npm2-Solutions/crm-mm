# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Telnyx as a test wants it (doc 64): the account's resources, its numbers, the
browsers' credentials, the messages, Italy's requirements and orders, the usage,
the verified numbers - in memory, answering the calls DottorCloud makes as
Telnyx's API v2 answers them.

``TelnyxFinto`` stands for `crm.telephony.telnyx.cliente._trasporto`: it answers
only its own key (401, code 10009, otherwise), keeps what was asked in
``chiamate`` and what each resource holds in its dictionaries. ``rifiuta`` makes
the next call answer an error, once. It signs webhooks as Telnyx does
(``firma``), with a key pair of its own whose public half is ``pubblica``.
"""

from __future__ import annotations

import base64
import itertools
import time
import uuid
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

CHIAVE = "KEY0189A1B2C3D4E5F6071829AB3C4D5E_5FhZonmFvcw8Yq0dME27Bg"

#: Telnyx's requirements for an Italian number, by kind: text, an address, documents.
REQUISITI = {
	"local": [
		{
			"id": "r-tipo",
			"name": "Customer Type",
			"type": "textual",
			"acceptance_criteria": {
				"acceptable_values": ["natural_person", "legal_entity", "sole_proprietorship"]
			},
		},
		{"id": "r-ragione", "name": "Company Name", "type": "textual"},
		{"id": "r-iva", "name": "VAT Number", "type": "textual"},
		{"id": "r-nome", "name": "Representative First Name", "type": "textual"},
		{"id": "r-cognome", "name": "Representative Last Name", "type": "textual"},
		{"id": "r-indirizzo", "name": "Address in Italy", "type": "address"},
		{"id": "r-visura", "name": "Local Company Registration Certificate", "type": "document"},
		{"id": "r-identita", "name": "Copy of ID or Passport (front and back)", "type": "document"},
	],
	"toll_free": [
		{"id": "t-ragione", "name": "Company Name", "type": "textual"},
		{"id": "t-visura", "name": "Business Registration Certificate", "type": "document"},
	],
}


class TelnyxFinto:
	def __init__(self):
		self.numeri_id = itertools.count(1293384261075731000)
		self.chiave = CHIAVE
		self._privata = Ed25519PrivateKey.generate()
		self.pubblica = base64.b64encode(
			self._privata.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
		).decode()
		self.bilancio = {"balance": "120.00", "available_credit": "120.00", "currency": "USD"}
		self.profili_voce: dict[str, dict] = {}
		self.applicazioni: dict[str, dict] = {}
		self.profili_sms: dict[str, dict] = {}
		self.connessioni: dict[str, dict] = {}
		#: the account's other connections: the centre's switchboard, another app
		self.altre_connessioni: dict[str, dict] = {}
		self.numeri: dict[str, dict] = {}
		#: which numbers send SMS
		self.sms: set[str] = set()
		self.credenziali: dict[str, dict] = {}
		self.messaggi: list[dict] = []
		self.documenti: dict[str, dict] = {}
		self.indirizzi: dict[str, dict] = {}
		self.gruppi: dict[str, dict] = {}
		self.ordini: dict[str, dict] = {}
		self.commenti: list[dict] = []
		#: what Telnyx sells, by kind
		self.in_vendita: dict[str, list[str]] = {"local": [], "toll_free": []}
		self.uso: dict[str, list[dict]] = {}
		self.addebiti: dict | None = None
		self.falliti: list[dict] = []
		self.verificati: dict[str, dict] = {}
		self.codici: dict[str, str] = {}
		self.chiamate: list[tuple[str, str]] = []
		self.rifiuta: tuple[int, dict] | None = None

	def __enter__(self):
		self._patch = patch("crm.telephony.telnyx.cliente._trasporto", self)
		self._patch.start()
		return self

	def __exit__(self, *args):
		self._patch.stop()

	# ------------------------------------------------------------------ helpers for the tests

	def numero(self, telefono: str, connection_id: str = "", sms: bool = False, tags=None, **altro) -> dict:
		ident = str(next(self.numeri_id))
		riga = {
			"id": ident,
			"record_type": "phone_number",
			"phone_number": telefono,
			"connection_id": connection_id,
			"messaging_profile_id": "",
			"tags": list(tags or []),
			"status": "active",
			"phone_number_type": "local",
			**altro,
		}
		self.numeri[ident] = riga
		if sms:
			self.sms.add(telefono)
		return riga

	def connessione(self, nome: str, tipo: str = "ip_connection") -> str:
		ident = str(next(self.numeri_id))
		self.altre_connessioni[ident] = {"id": ident, "record_type": tipo, "connection_name": nome}
		return ident

	def per_numero(self, telefono: str) -> dict:
		return next(n for n in self.numeri.values() if n["phone_number"] == telefono)

	def firma(self, corpo: bytes, momento: int | None = None) -> dict:
		"""The headers Telnyx signs a webhook with."""
		momento = int(momento if momento is not None else time.time())
		segno = self._privata.sign(str(momento).encode() + b"|" + corpo)
		return {
			"telnyx-signature-ed25519": base64.b64encode(segno).decode(),
			"telnyx-timestamp": str(momento),
		}

	# ------------------------------------------------------------------ the transport

	def __call__(self, metodo, indirizzo, intestazioni, parametri, corpo, file, dati, attesa):
		percorso = indirizzo.split("/v2/", 1)[1].split("?")[0]
		self.chiamate.append((metodo, percorso))
		if intestazioni.get("Authorization") != f"Bearer {self.chiave}":
			return 401, {"errors": [{"code": "10009", "title": "Authentication failed"}]}
		if self.rifiuta:
			risposta, self.rifiuta = self.rifiuta, None
			return risposta
		return self._rispondi(metodo, percorso, dict(parametri or {}), dict(corpo or {}))

	@staticmethod
	def _lista(righe) -> tuple[int, dict]:
		righe = list(righe)
		return 200, {"data": righe, "meta": {"total_pages": 1, "total_results": len(righe), "page_number": 1}}

	@staticmethod
	def _manca() -> tuple[int, dict]:
		return 404, {"errors": [{"code": "10005", "title": "Resource not found"}]}

	def _risorsa(self, raccolta: dict, metodo, ident, corpo, campo, filtro, parametri, tipo):
		if ident is None:
			if metodo == "GET":
				cerca = parametri.get(filtro) or ""
				return self._lista(
					r for r in raccolta.values() if cerca.lower() in (r.get(campo) or "").lower()
				)
			nuovo = {"id": str(next(self.numeri_id)), "record_type": tipo, **corpo}
			raccolta[nuovo["id"]] = nuovo
			return 201, {"data": nuovo}
		if ident not in raccolta:
			return self._manca()
		if metodo == "GET":
			return 200, {"data": raccolta[ident]}
		if metodo == "PATCH":
			for chiave, valore in corpo.items():
				if isinstance(valore, dict):
					raccolta[ident][chiave] = {**(raccolta[ident].get(chiave) or {}), **valore}
				else:
					raccolta[ident][chiave] = valore
			return 200, {"data": raccolta[ident]}
		if metodo == "DELETE":
			return 200, {"data": raccolta.pop(ident)}
		return 405, {}

	def _rispondi(self, metodo, percorso, parametri, corpo):
		parti = percorso.split("/")
		testa = parti[0]
		ident = parti[1] if len(parti) > 1 else None
		if testa == "balance":
			return 200, {"data": {"record_type": "balance", **self.bilancio}}
		if testa == "outbound_voice_profiles":
			return self._risorsa(
				self.profili_voce,
				metodo,
				ident,
				corpo,
				"name",
				"filter[name][contains]",
				parametri,
				"outbound_voice_profile",
			)
		if testa == "texml_applications":
			return self._risorsa(
				self.applicazioni,
				metodo,
				ident,
				corpo,
				"friendly_name",
				"filter[friendly_name]",
				parametri,
				"texml_application",
			)
		if testa == "messaging_profiles":
			return self._risorsa(
				self.profili_sms,
				metodo,
				ident,
				corpo,
				"name",
				"filter[name][contains]",
				parametri,
				"messaging_profile",
			)
		if testa == "credential_connections":
			return self._risorsa(
				self.connessioni,
				metodo,
				ident,
				corpo,
				"connection_name",
				"filter[connection_name][contains]",
				parametri,
				"credential_connection",
			)
		if testa == "connections":
			tutte = {
				**{k: {**v, "connection_name": v.get("friendly_name")} for k, v in self.applicazioni.items()},
				**self.connessioni,
				**self.altre_connessioni,
			}
			if ident:
				return (200, {"data": tutte[ident]}) if ident in tutte else self._manca()
			return self._lista(tutte.values())
		if testa == "phone_numbers":
			return self._numeri(metodo, parti, parametri, corpo)
		if testa == "telephony_credentials":
			if ident is None:
				nuova = {
					"id": str(uuid.uuid4()),
					"record_type": "credential",
					"sip_username": "gencred" + uuid.uuid4().hex[:20],
					"user_id": "utente-del-conto",
					**corpo,
				}
				self.credenziali[nuova["id"]] = nuova
				return 201, {"data": nuova}
			if ident not in self.credenziali:
				return self._manca()
			if len(parti) > 2 and parti[2] == "token":
				return 201, f"jwt.per.{self.credenziali[ident]['sip_username']}"
			if metodo == "DELETE":
				return 200, {"data": self.credenziali.pop(ident)}
			return 200, {"data": self.credenziali[ident]}
		if testa == "messages":
			if not corpo.get("text"):
				return 422, {"errors": [{"code": "40316", "title": "No content provided for message"}]}
			messaggio = {"id": str(uuid.uuid4()), "record_type": "message", **corpo}
			self.messaggi.append(messaggio)
			return 200, {"data": {**messaggio, "to": [{"phone_number": corpo.get("to"), "status": "queued"}]}}
		if testa == "available_phone_numbers":
			tipo = parametri.get("filter[phone_number_type]")
			zona = parametri.get("filter[national_destination_code]") or ""
			cifre = parametri.get("filter[phone_number][contains]") or ""
			righe = [
				{
					"phone_number": n,
					"record_type": "available_phone_number",
					"region_information": [{"region_type": "location", "region_name": "Milano"}],
					"cost_information": {"monthly_cost": "1.00", "upfront_cost": "1.00", "currency": "USD"},
					"features": [{"name": "voice"}],
				}
				for n in self.in_vendita.get(tipo, [])
				if (not zona or n.startswith("+39" + zona)) and cifre in n
			]
			return self._lista(righe[: int(parametri.get("filter[limit]") or 20)])
		if testa == "requirements":
			tipo = parametri.get("filter[phone_number_type]")
			return self._lista(
				[{"id": f"req-{tipo}", "country_code": "IT", "requirement_types": REQUISITI.get(tipo, [])}]
				if tipo in REQUISITI
				else []
			)
		if testa == "documents":
			nuovo = {
				"id": str(uuid.uuid4()),
				"filename": corpo.get("filename"),
				"size": len(corpo.get("file") or ""),
			}
			self.documenti[nuovo["id"]] = nuovo
			return 200, {"data": nuovo}
		if testa == "addresses":
			nuovo = {"id": str(next(self.numeri_id)), **corpo}
			self.indirizzi[nuovo["id"]] = nuovo
			return 200, {"data": nuovo}
		if testa == "requirement_groups":
			return self._gruppi(metodo, parti, corpo)
		if testa == "number_orders":
			return self._ordini(metodo, ident, corpo)
		if testa == "comments":
			ident = parametri.get("filter[comment_record_id]")
			return self._lista(c for c in self.commenti if c["comment_record_id"] == ident)
		if testa == "usage_reports":
			return self._lista(self.uso.get(parametri.get("product"), []))
		if testa == "charges_summary":
			return 200, {"data": self.addebiti or {"summary": {"lines": []}}}
		if testa == "detail_records":
			return self._lista(self.falliti)
		if testa == "verified_numbers":
			return self._verificati(metodo, parti, corpo)
		return 404, {"errors": [{"code": "10005", "title": f"No fake for {metodo} {percorso}"}]}

	def _numeri(self, metodo, parti, parametri, corpo):
		if len(parti) == 1:
			cifre = parametri.get("filter[phone_number]") or ""
			return self._lista(n for n in self.numeri.values() if cifre in n["phone_number"])
		if parti[1] == "messaging":
			return self._lista(
				{
					"phone_number": n["phone_number"],
					"messaging_profile_id": n.get("messaging_profile_id"),
					"features": {
						"sms": {"domestic_two_way": True} if n["phone_number"] in self.sms else None
					},
				}
				for n in self.numeri.values()
			)
		numero = self.numeri.get(parti[1])
		if not numero:
			return self._manca()
		if len(parti) > 2 and parti[2] == "messaging":
			if metodo == "PATCH":
				numero["messaging_profile_id"] = corpo.get("messaging_profile_id")
			return 200, {
				"data": {
					"phone_number": numero["phone_number"],
					"messaging_profile_id": numero.get("messaging_profile_id"),
					"features": {
						"sms": {"domestic_two_way": True} if numero["phone_number"] in self.sms else None
					},
				}
			}
		if metodo == "PATCH":
			numero.update(corpo)
		if metodo == "DELETE":
			return 200, {"data": self.numeri.pop(parti[1])}
		return 200, {"data": numero}

	def _gruppi(self, metodo, parti, corpo):
		if len(parti) == 1:
			if metodo == "GET":
				return 200, list(self.gruppi.values())
			nuovo = {
				"id": str(uuid.uuid4()),
				"status": "unapproved",
				"record_type": "requirement_group",
				**corpo,
			}
			self.gruppi[nuovo["id"]] = nuovo
			# a requirement group comes without `data` around it
			return 200, nuovo
		gruppo = self.gruppi.get(parti[1])
		if not gruppo:
			return self._manca()
		if len(parti) > 2 and parti[2] == "submit_for_approval":
			# Italy approves no group before an order
			return 422, {"errors": [{"code": "10015", "title": "Pre-approval not supported for IT"}]}
		if metodo == "PATCH":
			gruppo.update(corpo)
		if metodo == "DELETE":
			return 200, self.gruppi.pop(parti[1])
		return 200, gruppo

	def _ordini(self, metodo, ident, corpo):
		if ident is None:
			numeri = corpo.get("phone_numbers") or []
			for riga in numeri:
				gruppo = self.gruppi.get(riga.get("requirement_group_id"))
				if not gruppo:
					return 422, {"errors": [{"code": "10015", "title": "Requirement group missing"}]}
			nuovo = {"id": str(uuid.uuid4()), "status": "pending", "record_type": "number_order", **corpo}
			self.ordini[nuovo["id"]] = nuovo
			return 200, {"data": nuovo}
		if ident not in self.ordini:
			return self._manca()
		return 200, {"data": self.ordini[ident]}

	def esito(self, ordine: str, stato: str) -> None:
		"""Telnyx's check of an order over: success makes the number the account's,
		on the order's connection."""
		dati = self.ordini[ordine]
		dati["status"] = stato
		if stato == "success":
			for riga in dati["phone_numbers"]:
				self.numero(riga["phone_number"], connection_id=dati.get("connection_id") or "")

	def _verificati(self, metodo, parti, corpo):
		from urllib.parse import unquote

		if len(parti) == 1:
			if metodo == "GET":
				return self._lista(self.verificati.values())
			numero = corpo.get("phone_number")
			self.codici[numero] = "123456"
			self.verificati[numero] = {
				"phone_number": numero,
				"record_type": "verified_number",
				"verified_at": None,
			}
			return 200, {"phone_number": numero, "verification_method": corpo.get("verification_method")}
		numero = unquote(parti[1])
		if numero not in self.verificati:
			return self._manca()
		if len(parti) > 3 and parti[3] == "verify":
			if corpo.get("verification_code") != self.codici.get(numero):
				return 422, {"errors": [{"code": "10015", "title": "Invalid verification code"}]}
			self.verificati[numero]["verified_at"] = "2026-10-10T10:00:00Z"
			return 200, {"data": self.verificati[numero]}
		if metodo == "DELETE":
			return 200, {"data": self.verificati.pop(numero)}
		return 200, {"data": self.verificati[numero]}
