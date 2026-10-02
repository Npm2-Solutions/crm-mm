# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Twilio as a test wants it: accounts and subaccounts, keys, apps, numbers.

``Mondo.client`` stands for ``twilio.rest.Client``: it answers only the codes of an
account it knows, and only for that account and its subaccounts, as Twilio does.
What was changed is kept in ``cambi``, so a test sees what DottorCloud asked for.
"""

from __future__ import annotations

import secrets
from types import SimpleNamespace

from twilio.base.exceptions import TwilioRestException


def _sid(prefisso: str) -> str:
	return prefisso + secrets.token_hex(16)


class Mondo:
	def __init__(self):
		self.conti: dict[str, SimpleNamespace] = {}
		self.chiavi: dict[str, list[SimpleNamespace]] = {}
		self.app: dict[str, list[SimpleNamespace]] = {}
		self.numeri: dict[str, list[SimpleNamespace]] = {}
		#: (account, what, sid) of every change asked for
		self.cambi: list[tuple] = []
		#: every client made, with the account it was made for
		self.clienti: list[str] = []

	def conto(self, nome: str, padre: str | None = None, tipo: str = "Full", stato: str = "active"):
		sid = _sid("AC")
		conto = SimpleNamespace(
			sid=sid,
			auth_token=secrets.token_hex(16),
			friendly_name=nome,
			owner_account_sid=padre or sid,
			status=stato,
			type=tipo,
		)
		self.conti[sid] = conto
		self.chiavi[sid], self.app[sid], self.numeri[sid] = [], [], []
		return conto

	def numero(self, conto: str, telefono: str, sms: bool = False, **valori):
		numero = SimpleNamespace(
			sid=_sid("PN"),
			phone_number=telefono,
			friendly_name=telefono,
			voice_url=None,
			voice_method="POST",
			voice_application_sid=None,
			sms_url=None,
			sms_method="POST",
			sms_application_sid=None,
			trunk_sid=None,
			capabilities={"voice": True, "sms": sms, "mms": False},
		)
		for chiave, valore in valori.items():
			setattr(numero, chiave, valore)
		self.numeri[conto].append(numero)
		return numero

	def sottoconti(self, padre: str) -> list[SimpleNamespace]:
		return [c for c in self.conti.values() if c.owner_account_sid == padre and c.sid != padre]

	def client(self, account_sid: str, auth_token: str):
		conto = self.conti.get(account_sid)
		if not conto or conto.auth_token != auth_token:
			raise TwilioRestException(401, f"/Accounts/{account_sid}.json", "Authenticate", code=20003)
		self.clienti.append(account_sid)
		return _Client(self, conto)


class _Risorsa:
	"""A list of Twilio's resources of one account: list, create, and one by its SID."""

	def __init__(self, mondo, conto, tipo, elenco, crea=None):
		self.mondo, self.conto, self.tipo, self.elenco, self._crea = mondo, conto, tipo, elenco, crea

	def __call__(self, sid):
		for cosa in self.elenco:
			if cosa.sid == sid:
				return _Una(self, cosa)
		raise TwilioRestException(404, f"/{self.tipo}/{sid}", "Not found", code=20404)

	def list(self, friendly_name=None, **_filtri):
		return [c for c in self.elenco if friendly_name is None or c.friendly_name == friendly_name]

	def create(self, **valori):
		cosa = self._crea(**valori)
		self.elenco.append(cosa)
		self.mondo.cambi.append((self.conto.sid, f"create {self.tipo}", cosa.sid))
		return cosa


class _Una:
	def __init__(self, risorsa, cosa):
		self.risorsa, self.cosa = risorsa, cosa

	def fetch(self):
		return self.cosa

	def update(self, **valori):
		for chiave, valore in valori.items():
			setattr(self.cosa, chiave, valore)
		self.risorsa.mondo.cambi.append(
			(self.risorsa.conto.sid, f"update {self.risorsa.tipo}", self.cosa.sid)
		)
		return self.cosa

	def delete(self):
		self.risorsa.elenco.remove(self.cosa)
		self.risorsa.mondo.cambi.append(
			(self.risorsa.conto.sid, f"delete {self.risorsa.tipo}", self.cosa.sid)
		)
		return True


class _Conti:
	"""``client.api.v2010.accounts``: the account itself and its subaccounts."""

	def __init__(self, mondo, conto):
		self.mondo, self.conto = mondo, conto

	def _visibili(self):
		return [self.conto, *self.mondo.sottoconti(self.conto.sid)]

	def __call__(self, sid):
		for conto in self._visibili():
			if conto.sid == sid:
				return _Una(_Risorsa(self.mondo, self.conto, "Account", []), conto)
		raise TwilioRestException(404, f"/Accounts/{sid}.json", "Not found", code=20404)

	def list(self, friendly_name=None, status=None, **_filtri):
		return [
			c
			for c in self._visibili()
			if (friendly_name is None or c.friendly_name == friendly_name)
			and (status is None or c.status == status)
		]

	def create(self, friendly_name=None):
		if self.conto.owner_account_sid != self.conto.sid:
			raise TwilioRestException(
				403, "/Accounts.json", "Subaccounts cannot make subaccounts", code=20005
			)
		nuovo = self.mondo.conto(friendly_name, padre=self.conto.sid, tipo=self.conto.type)
		self.mondo.cambi.append((self.conto.sid, "create Account", nuovo.sid))
		return nuovo


class _Client:
	def __init__(self, mondo, conto):
		self.mondo, self.conto = mondo, conto
		sid = conto.sid
		self.api = SimpleNamespace(v2010=SimpleNamespace(accounts=_Conti(mondo, conto)))

		def nuova_chiave(friendly_name=None):
			return SimpleNamespace(sid=_sid("SK"), friendly_name=friendly_name, secret=secrets.token_hex(16))

		def nuova_app(friendly_name=None, voice_url=None, voice_method="POST"):
			return SimpleNamespace(
				sid=_sid("AP"), friendly_name=friendly_name, voice_url=voice_url, voice_method=voice_method
			)

		self.keys = _Risorsa(mondo, conto, "Key", mondo.chiavi[sid])
		self.new_keys = _Risorsa(mondo, conto, "Key", mondo.chiavi[sid], crea=nuova_chiave)
		self.applications = _Risorsa(mondo, conto, "Application", mondo.app[sid], crea=nuova_app)
		self.incoming_phone_numbers = _Risorsa(mondo, conto, "IncomingPhoneNumber", mondo.numeri[sid])
		self.outgoing_caller_ids = _Risorsa(mondo, conto, "OutgoingCallerId", [])
		self.trunking = SimpleNamespace(v1=SimpleNamespace(trunks=_Risorsa(mondo, conto, "Trunk", [])))
