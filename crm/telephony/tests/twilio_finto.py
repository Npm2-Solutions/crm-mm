# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Twilio as a test wants it: accounts and subaccounts, keys, apps, numbers, and
the Italian numbers' documents (doc 52).

``Mondo.client`` stands for ``twilio.rest.Client``: it answers only the codes of an
account it knows, and only for that account and its subaccounts, as Twilio does.
What was changed is kept in ``cambi``, so a test sees what DottorCloud asked for.

The numbers Twilio has for sale are ``Mondo.in_vendita``; its regulations are
``REGOLE``, the way its Regulation resource writes them; a bundle's evaluation looks
at what was assigned to it as Twilio would - every field of whose the number is,
a document of an accepted kind for each requirement. ``Mondo.carica`` stands for
the upload of a document's file. What a space spends this month is
``Mondo.spende``, a line of its log of problems ``Mondo.problema``; its usage
triggers are kept as Twilio keeps them.
"""

from __future__ import annotations

import json
import secrets
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

from twilio.base.exceptions import TwilioRestException


def _sid(prefisso: str) -> str:
	return prefisso + secrets.token_hex(16)


def _campi(*nomi):
	return [{"machine_name": nome, "friendly_name": nome.replace("_", " ").title()} for nome in nomi]


#: Twilio's regulations for Italy, by (number type, end user type).
REGOLE = {
	("mobile", "business"): {
		"end_user": [
			{
				"name": "Business",
				"type": "business",
				"requirement_name": "business_info",
				"detailed_fields": _campi(
					"business_name", "business_registration_number", "first_name", "last_name"
				),
			}
		],
		"supporting_document": [
			[
				{
					"name": "Business Address",
					"type": "document",
					"requirement_name": "business_address_info",
					"description": "The office's address.",
					"accepted_documents": [
						{
							"name": "Address Validation",
							"type": "address",
							"detailed_fields": _campi("address_sids"),
						}
					],
				}
			],
			[
				{
					"name": "Business Registration",
					"type": "document",
					"requirement_name": "business_registration_info",
					"description": "Proof the business exists.",
					"accepted_documents": [
						{
							"name": "Business Registration",
							"type": "business_registration",
							"detailed_fields": _campi("business_name", "business_registration_number"),
						},
						{
							"name": "Commercial Registrar Excerpt",
							"type": "commercial_registrar_excerpt",
							"detailed_fields": _campi("business_name"),
						},
					],
				}
			],
		],
	},
	("mobile", "individual"): {
		"end_user": [
			{
				"name": "Individual",
				"type": "individual",
				"requirement_name": "individual_info",
				"detailed_fields": _campi("first_name", "last_name"),
			}
		],
		"supporting_document": [
			[
				{
					"name": "Identity",
					"type": "document",
					"requirement_name": "identity_info",
					"description": "Who the person is.",
					"accepted_documents": [
						{
							"name": "Government-issued ID",
							"type": "government_issued_document",
							"detailed_fields": _campi("first_name", "last_name", "document_number"),
						}
					],
				}
			]
		],
	},
	("local", "business"): {
		"end_user": [
			{
				"name": "Business",
				"type": "business",
				"requirement_name": "business_info",
				"detailed_fields": _campi("business_name"),
			}
		],
		"supporting_document": [
			[
				{
					"name": "Local Address",
					"type": "document",
					"requirement_name": "local_address_info",
					"description": "An address in the area of the prefix, with a bill.",
					"accepted_documents": [
						{
							"name": "Utility Bill",
							"type": "utility_bill",
							"detailed_fields": _campi("address_sids", "business_name"),
						}
					],
				}
			]
		],
	},
}


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
		#: the numbers Twilio has for sale in Italy, by DottorCloud's kind
		self.in_vendita: dict[str, list[str]] = {
			"mobile": ["+393331234567", "+393337654321", "+393401112233"],
			"local": ["+390212345678", "+390287654321", "+390612345678"],
			"toll_free": ["+39800123456"],
		}
		#: Twilio's prices for Italy, as its Pricing API gives them
		self.prezzi = [
			{"number_type": "mobile", "base_price": "45.00", "current_price": "45.00"},
			{"number_type": "local", "base_price": "4.25", "current_price": "4.25"},
			{"number_type": "toll free", "base_price": "27.00", "current_price": "27.00"},
		]
		#: whose the numbers are and their documents, by SID: the regulatory world
		self.utenti: dict[str, SimpleNamespace] = {}
		self.documenti: dict[str, SimpleNamespace] = {}
		self.indirizzi: dict[str, SimpleNamespace] = {}
		self.pacchetti: dict[str, SimpleNamespace] = {}
		#: every file uploaded, (account, type, file name, attributes)
		self.caricati: list[tuple] = []
		self.regole = {chiave: _sid("RN") for chiave in REGOLE}
		#: the countries each account may call (Twilio's voice geographic permissions),
		#: and whether it takes its account's
		self.paesi: dict[str, set[str]] = {}
		#: the countries whose special and toll-fraud numbers are open, by account
		self.rischiosi: dict[str, set[str]] = {}
		self.eredita: dict[str, bool] = {}
		#: every search of numbers for sale: (kind, contains)
		self.cercati: list[tuple] = []
		#: this month's usage records by account and category, the usage triggers and
		#: the log of problems (Twilio's Monitor)
		self.consumi: dict[str, dict[str, SimpleNamespace]] = {}
		self.soglie: dict[str, list[SimpleNamespace]] = {}
		self.allarmi: dict[str, list[SimpleNamespace]] = {}

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
		self.consumi[sid], self.soglie[sid], self.allarmi[sid] = {}, [], []
		return conto

	def spende(
		self, conto: str, categoria: str, price: str, count=0, usage=0, usage_unit="", price_unit="usd"
	):
		"""This month's record of a category, as Twilio's usage records give it."""
		self.consumi[conto][categoria] = SimpleNamespace(
			category=categoria,
			count=str(count),
			usage=str(usage),
			usage_unit=usage_unit,
			price=Decimal(price),
			price_unit=price_unit,
		)

	def problema(self, conto: str, codice: str, testo: str, quando: datetime, livello: str = "error"):
		"""A line of Twilio's log of problems (Monitor's alerts)."""
		self.allarmi[conto].append(
			SimpleNamespace(
				sid=_sid("NO"),
				error_code=codice,
				alert_text=testo,
				log_level=livello,
				date_created=quando,
				more_info=f"https://www.twilio.com/docs/errors/{codice}",
			)
		)

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
			bundle_sid=None,
			address_sid=None,
		)
		for chiave, valore in valori.items():
			setattr(numero, chiave, valore)
		self.numeri[conto].append(numero)
		return numero

	def approvato(self, conto: str, tipo: str = "local") -> SimpleNamespace:
		"""A bundle of documents Twilio already approved, in ``conto``."""
		chiave = next(k for k in REGOLE if k[0] == tipo)
		pacchetto = SimpleNamespace(
			sid=_sid("BU"),
			account=conto,
			friendly_name="Centro Aurora",
			email="amministrazione@aurora.example",
			regola=chiave,
			status="twilio-approved",
			oggetti=[],
		)
		self.pacchetti[pacchetto.sid] = pacchetto
		return pacchetto

	def indirizzo(self, conto: str, **valori) -> SimpleNamespace:
		"""An address of ``conto``, as Twilio's Address resource keeps it."""
		indirizzo = SimpleNamespace(
			sid=_sid("AD"),
			account=conto,
			attributes={},
			customer_name="Centro Aurora",
			street="Via Roma 1",
			city="Milano",
			region="MI",
			postal_code="20121",
			iso_country="IT",
			friendly_name="Sede",
		)
		for chiave, valore in valori.items():
			setattr(indirizzo, chiave, valore)
		self.indirizzi[indirizzo.sid] = indirizzo
		return indirizzo

	def sottoconti(self, padre: str) -> list[SimpleNamespace]:
		return [c for c in self.conti.values() if c.owner_account_sid == padre and c.sid != padre]

	def client(self, account_sid: str, auth_token: str):
		conto = self.conti.get(account_sid)
		if not conto or conto.auth_token != auth_token:
			raise TwilioRestException(401, f"/Accounts/{account_sid}.json", "Authenticate", code=20003)
		self.clienti.append(account_sid)
		return _Client(self, conto)

	def carica(self, url: str, auth=None, data=None, files=None, timeout=None):
		"""Twilio's upload of a document's file: a document like any other, with it."""
		conto = self.conti.get((auth or ("", ""))[0])
		if not conto or conto.auth_token != auth[1]:
			return _Risposta(401, {"code": 20003, "message": "Authenticate"})
		nome_file, contenuto = files["File"]
		if not isinstance(contenuto, bytes) or not contenuto:
			# a file read as text would reach Twilio broken
			return _Risposta(400, {"code": 20001, "message": "The file is not a file"})
		documento = SimpleNamespace(
			sid=_sid("RD"),
			account=conto.sid,
			type=data["Type"],
			friendly_name=data["FriendlyName"],
			attributes=json.loads(data.get("Attributes") or "{}"),
			file=nome_file,
		)
		self.documenti[documento.sid] = documento
		self.caricati.append((conto.sid, documento.type, nome_file, documento.attributes))
		return _Risposta(201, {"sid": documento.sid})

	def valuta(self, pacchetto) -> list[dict]:
		"""What Twilio's evaluation finds of a bundle: every field of whose the number
		is, and a document of an accepted kind, with its fields, for each requirement."""
		regola = REGOLE[pacchetto.regola]
		risultati = []
		for requisito in regola["end_user"]:
			utente = next(
				(
					self.utenti[s]
					for s in pacchetto.oggetti
					if s in self.utenti and self.utenti[s].type == requisito["type"]
				),
				None,
			)
			mancano = [
				c
				for c in requisito["detailed_fields"]
				if not (utente and utente.attributes.get(c["machine_name"]))
			]
			risultati.append(_risultato(requisito, mancano, "The end user is missing." if not utente else ""))
		for gruppo in regola["supporting_document"]:
			for requisito in gruppo:
				accettati = {d["type"]: d for d in requisito["accepted_documents"]}
				documenti = [
					self.documenti[s]
					for s in pacchetto.oggetti
					if s in self.documenti and self.documenti[s].type in accettati
				]
				if not documenti:
					risultati.append(_risultato(requisito, [], "A supporting document is missing."))
					continue
				richiesti = accettati[documenti[0].type]["detailed_fields"]
				mancano = [c for c in richiesti if not documenti[0].attributes.get(c["machine_name"])]
				risultati.append(_risultato(requisito, mancano))
		return risultati


def _risultato(requisito: dict, mancano: list, motivo: str = "") -> dict:
	return {
		"friendly_name": requisito["name"],
		"requirement_friendly_name": requisito["name"],
		"requirement_name": requisito["requirement_name"],
		"passed": not (mancano or motivo),
		"failure_reason": motivo,
		"invalid": [
			{
				"friendly_name": campo["friendly_name"],
				"object_field": campo["machine_name"],
				"failure_reason": f"The {campo['friendly_name']} is missing.",
			}
			for campo in mancano
		],
	}


class _Risposta:
	def __init__(self, stato: int, corpo: dict):
		self.status_code, self._corpo = stato, corpo
		self.headers = {"content-type": "application/json"}

	def json(self):
		return self._corpo


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


class _Soglie(_Risorsa):
	"""The usage triggers, which Twilio lists by category."""

	def list(self, usage_category=None, **_filtri):
		return [c for c in self.elenco if usage_category is None or c.usage_category == usage_category]


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


class _Numeri(_Risorsa):
	"""An account's numbers: one moves to a subaccount as Twilio moves it, with an
	approved bundle and the address already there."""

	def __call__(self, sid):
		for cosa in self.elenco:
			if cosa.sid == sid:
				return _UnNumero(self, cosa)
		raise TwilioRestException(404, f"/{self.tipo}/{sid}", "Not found", code=20404)


class _UnNumero(_Una):
	"""One number: fetched, released, changed - or moved to a subaccount."""

	def update(self, account_sid=None, **valori):
		mondo, conto, numero = self.risorsa.mondo, self.risorsa.conto, self.cosa
		uri = f"/IncomingPhoneNumbers/{numero.sid}"
		if account_sid and account_sid != conto.sid:
			destinazione = mondo.conti.get(account_sid)
			if not destinazione or destinazione.owner_account_sid != conto.sid:
				raise TwilioRestException(400, uri, "Not a subaccount of this account", code=20003)
			if numero.bundle_sid:
				pacchetto = mondo.pacchetti.get(valori.get("bundle_sid"))
				if not pacchetto or pacchetto.account != account_sid or pacchetto.status != "twilio-approved":
					raise TwilioRestException(400, uri, "Bundle not approved", code=21649)
			if numero.address_sid:
				indirizzo = mondo.indirizzi.get(valori.get("address_sid"))
				if not indirizzo or indirizzo.account != account_sid:
					raise TwilioRestException(
						400, uri, "The address is not in the target account", code=21615
					)
			self.risorsa.elenco.remove(numero)
			mondo.numeri[account_sid].append(numero)
			mondo.cambi.append((conto.sid, "move IncomingPhoneNumber", numero.sid))
		for chiave, valore in valori.items():
			setattr(numero, chiave, valore)
		if valori:
			mondo.cambi.append((conto.sid, "update IncomingPhoneNumber", numero.sid))
		return numero


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


class _InArchivio:
	"""End users, documents, addresses: kept by the world, each of its account."""

	def __init__(self, mondo, conto, tipo, archivio, prefisso):
		self.mondo, self.conto, self.tipo, self.archivio, self.prefisso = (
			mondo,
			conto,
			tipo,
			archivio,
			prefisso,
		)

	def create(self, **valori):
		attributi = valori.pop("attributes", None)
		cosa = SimpleNamespace(
			sid=_sid(self.prefisso), account=self.conto.sid, attributes=dict(attributi or {}), **valori
		)
		self.archivio[cosa.sid] = cosa
		self.mondo.cambi.append((self.conto.sid, f"create {self.tipo}", cosa.sid))
		return cosa

	def __call__(self, sid):
		cosa = self.archivio.get(sid)
		if not cosa or cosa.account != self.conto.sid:
			raise TwilioRestException(404, f"/{self.tipo}/{sid}", "Not found", code=20404)
		mondo, conto, tipo, archivio = self.mondo, self.conto, self.tipo, self.archivio

		def delete():
			del archivio[sid]
			mondo.cambi.append((conto.sid, f"delete {tipo}", sid))
			return True

		return SimpleNamespace(fetch=lambda: cosa, delete=delete)


class _Pacchetto:
	"""``regulatory_compliance.bundles(sid)``: its items, its evaluation, its state."""

	def __init__(self, mondo, conto, pacchetto):
		self.mondo, self.conto, self.pacchetto = mondo, conto, pacchetto
		self.item_assignments = SimpleNamespace(create=self._assegna)
		self.evaluations = SimpleNamespace(create=self._valuta)

	def _assegna(self, object_sid=None):
		if object_sid not in self.mondo.utenti and object_sid not in self.mondo.documenti:
			raise TwilioRestException(400, "/ItemAssignments", "Unknown object", code=22209)
		self.pacchetto.oggetti.append(object_sid)
		return SimpleNamespace(sid=_sid("BV"), object_sid=object_sid)

	def _valuta(self):
		risultati = self.mondo.valuta(self.pacchetto)
		conforme = all(r["passed"] for r in risultati)
		return SimpleNamespace(
			sid=_sid("EL"), status="compliant" if conforme else "noncompliant", results=risultati
		)

	def fetch(self):
		return self.pacchetto

	def update(self, status=None, **_valori):
		if status == "pending-review":
			if self.pacchetto.status not in ("draft", "twilio-rejected"):
				raise TwilioRestException(400, "/Bundles", "Not a draft", code=22217)
			if not all(r["passed"] for r in self.mondo.valuta(self.pacchetto)):
				raise TwilioRestException(400, "/Bundles", "The bundle is not compliant", code=22216)
			self.pacchetto.status = status
		self.mondo.cambi.append((self.conto.sid, "update Bundle", self.pacchetto.sid))
		return self.pacchetto

	def delete(self):
		del self.mondo.pacchetti[self.pacchetto.sid]
		self.mondo.cambi.append((self.conto.sid, "delete Bundle", self.pacchetto.sid))
		return True


class _Pacchetti:
	def __init__(self, mondo, conto):
		self.mondo, self.conto = mondo, conto

	def create(self, friendly_name=None, email=None, regulation_sid=None, **_valori):
		chiave = next((k for k, sid in self.mondo.regole.items() if sid == regulation_sid), None)
		if not chiave:
			raise TwilioRestException(400, "/Bundles", "Unknown regulation", code=22201)
		pacchetto = SimpleNamespace(
			sid=_sid("BU"),
			account=self.conto.sid,
			friendly_name=friendly_name,
			email=email,
			regola=chiave,
			status="draft",
			oggetti=[],
		)
		self.mondo.pacchetti[pacchetto.sid] = pacchetto
		self.mondo.cambi.append((self.conto.sid, "create Bundle", pacchetto.sid))
		return pacchetto

	def __call__(self, sid):
		pacchetto = self.mondo.pacchetti.get(sid)
		if not pacchetto or pacchetto.account != self.conto.sid:
			raise TwilioRestException(404, f"/Bundles/{sid}", "Not found", code=20404)
		return _Pacchetto(self.mondo, self.conto, pacchetto)


class _Regole:
	"""``client.numbers.v2.regulatory_compliance`` of one account."""

	def __init__(self, mondo, conto):
		self.mondo = mondo
		self.regulations = SimpleNamespace(list=self._regole)
		self.end_users = _InArchivio(mondo, conto, "EndUser", mondo.utenti, "IT")
		self.supporting_documents = _InArchivio(mondo, conto, "SupportingDocument", mondo.documenti, "RD")
		self.bundles = _Pacchetti(mondo, conto)

	def _regole(self, iso_country=None, number_type=None, end_user_type=None, limit=None):
		chiave = ({"toll free": "toll_free"}.get(number_type, number_type), end_user_type)
		if iso_country != "IT" or chiave not in REGOLE:
			return []
		return [
			SimpleNamespace(
				sid=self.mondo.regole[chiave],
				iso_country="IT",
				number_type=number_type,
				end_user_type=end_user_type,
				requirements=REGOLE[chiave],
			)
		]


class _Permessi:
	"""``client.voice.v1.dialing_permissions`` of one account: its countries, or its
	account's while it inherits them."""

	INTERRUTTORI = (
		"low_risk_numbers_enabled",
		"high_risk_special_numbers_enabled",
		"high_risk_tollfraud_numbers_enabled",
	)

	def __init__(self, mondo, conto):
		self.mondo, self.conto = mondo, conto
		mondo.paesi.setdefault(conto.sid, {"IT", "US"})
		mondo.rischiosi.setdefault(conto.sid, set())
		mondo.eredita.setdefault(conto.sid, True)
		self.countries = SimpleNamespace(list=self._paesi)
		self.bulk_country_updates = SimpleNamespace(create=self._aggiorna)

	def settings(self):
		mondo, conto = self.mondo, self.conto

		def fetch():
			return SimpleNamespace(dialing_permissions_inheritance=mondo.eredita[conto.sid])

		def update(dialing_permissions_inheritance=None):
			mondo.eredita[conto.sid] = bool(dialing_permissions_inheritance)
			mondo.cambi.append((conto.sid, "update DialingPermissionsSettings", conto.sid))
			return fetch()

		return SimpleNamespace(fetch=fetch, update=update)

	def _di_chi(self) -> str:
		if self.mondo.eredita[self.conto.sid] and self.conto.owner_account_sid != self.conto.sid:
			return self.conto.owner_account_sid
		return self.conto.sid

	def _paesi(self, **filtri):
		di = self._di_chi()
		bassi, alti = self.mondo.paesi.get(di, set()), self.mondo.rischiosi.get(di, set())
		righe = [
			SimpleNamespace(
				iso_code=paese,
				low_risk_numbers_enabled=paese in bassi,
				high_risk_special_numbers_enabled=paese in alti,
				high_risk_tollfraud_numbers_enabled=paese in alti,
			)
			for paese in sorted(bassi | alti)
		]
		chiesti = {k: v for k, v in filtri.items() if k in self.INTERRUTTORI and v is not None}
		return [r for r in righe if all(getattr(r, k) == v for k, v in chiesti.items())]

	def _aggiorna(self, update_request=None):
		if self.mondo.eredita[self.conto.sid] and self.conto.owner_account_sid != self.conto.sid:
			raise TwilioRestException(400, "/BulkCountryUpdates", "Inherits its account's", code=13252)
		for cambio in json.loads(update_request):
			paese = cambio["iso_code"]
			bassi = self.mondo.paesi[self.conto.sid]
			alti = self.mondo.rischiosi[self.conto.sid]
			(bassi.add if cambio["low_risk_numbers_enabled"] == "true" else bassi.discard)(paese)
			aperti = "true" in (
				cambio["high_risk_special_numbers_enabled"],
				cambio["high_risk_tollfraud_numbers_enabled"],
			)
			(alti.add if aperti else alti.discard)(paese)
		self.mondo.cambi.append((self.conto.sid, "create BulkCountryUpdate", self.conto.sid))
		return SimpleNamespace(update_count=len(json.loads(update_request)))


class _InVendita:
	"""``available_phone_numbers("IT").<kind>``: what Twilio has for sale."""

	def __init__(self, mondo, tipo):
		self.mondo, self.tipo = mondo, tipo

	def list(self, contains=None, limit=None, **_filtri):
		self.mondo.cercati.append((self.tipo, contains))
		numeri = [n for n in self.mondo.in_vendita[self.tipo] if not contains or contains in n]
		return [
			SimpleNamespace(
				phone_number=n,
				friendly_name=n,
				locality="Milano" if n.startswith("+3902") else "",
				region="MI" if n.startswith("+3902") else "",
			)
			for n in numeri[: limit or None]
		]


class _Client:
	def __init__(self, mondo, conto):
		self.mondo, self.conto = mondo, conto
		sid = conto.sid
		self.username, self.password = conto.sid, conto.auth_token
		self.api = SimpleNamespace(v2010=SimpleNamespace(accounts=_Conti(mondo, conto)))
		self.numbers = SimpleNamespace(v2=SimpleNamespace(regulatory_compliance=_Regole(mondo, conto)))
		self.addresses = _InArchivio(mondo, conto, "Address", mondo.indirizzi, "AD")
		self.voice = SimpleNamespace(v1=SimpleNamespace(dialing_permissions=_Permessi(mondo, conto)))
		prezzi = SimpleNamespace(phone_number_prices=mondo.prezzi, price_unit="USD", iso_country="IT")
		self.pricing = SimpleNamespace(
			v1=SimpleNamespace(
				phone_numbers=SimpleNamespace(countries=lambda iso: SimpleNamespace(fetch=lambda: prezzi))
			)
		)
		in_vendita = SimpleNamespace(**{tipo: _InVendita(mondo, tipo) for tipo in mondo.in_vendita})
		self.available_phone_numbers = lambda iso: in_vendita

		def compra(phone_number=None, bundle_sid=None, address_sid=None, **valori):
			tipo = next((k for k, numeri in mondo.in_vendita.items() if phone_number in numeri), None)
			if not tipo:
				raise TwilioRestException(400, "/IncomingPhoneNumbers.json", "Not available", code=21422)
			pacchetto = mondo.pacchetti.get(bundle_sid)
			if (
				not pacchetto
				or pacchetto.account != conto.sid
				or pacchetto.status != "twilio-approved"
				or pacchetto.regola[0] != tipo
			):
				raise TwilioRestException(
					400, "/IncomingPhoneNumbers.json", "Bundle not approved", code=21649
				)
			mondo.in_vendita[tipo].remove(phone_number)
			return SimpleNamespace(
				sid=_sid("PN"),
				phone_number=phone_number,
				friendly_name=phone_number,
				voice_url=valori.get("voice_url"),
				voice_method=valori.get("voice_method", "POST"),
				voice_application_sid=None,
				sms_url=valori.get("sms_url"),
				sms_method=valori.get("sms_method", "POST"),
				sms_application_sid=None,
				trunk_sid=None,
				capabilities={"voice": True, "sms": tipo == "mobile", "mms": False},
				bundle_sid=bundle_sid,
				address_sid=address_sid,
			)

		def nuova_chiave(friendly_name=None):
			return SimpleNamespace(sid=_sid("SK"), friendly_name=friendly_name, secret=secrets.token_hex(16))

		def nuova_app(friendly_name=None, voice_url=None, voice_method="POST"):
			return SimpleNamespace(
				sid=_sid("AP"), friendly_name=friendly_name, voice_url=voice_url, voice_method=voice_method
			)

		self.keys = _Risorsa(mondo, conto, "Key", mondo.chiavi[sid])
		self.new_keys = _Risorsa(mondo, conto, "Key", mondo.chiavi[sid], crea=nuova_chiave)
		self.applications = _Risorsa(mondo, conto, "Application", mondo.app[sid], crea=nuova_app)
		self.incoming_phone_numbers = _Numeri(
			mondo, conto, "IncomingPhoneNumber", mondo.numeri[sid], crea=compra
		)
		self.outgoing_caller_ids = _Risorsa(mondo, conto, "OutgoingCallerId", [])

		def nuova_soglia(callback_url=None, trigger_value=None, usage_category=None, **valori):
			return SimpleNamespace(
				sid=_sid("UT"),
				callback_url=callback_url,
				callback_method=valori.get("callback_method", "POST"),
				trigger_value=str(trigger_value),
				usage_category=usage_category,
				trigger_by=valori.get("trigger_by"),
				recurring=valori.get("recurring"),
				friendly_name=valori.get("friendly_name"),
			)

		consumi = mondo.consumi[sid]
		self.usage = SimpleNamespace(
			records=SimpleNamespace(
				this_month=SimpleNamespace(
					list=lambda category=None, **_f: [
						r for c, r in consumi.items() if category is None or c == category
					]
				)
			),
			triggers=_Soglie(mondo, conto, "UsageTrigger", mondo.soglie[sid], crea=nuova_soglia),
		)

		def request(method, uri, data=None, **_valori):
			"""What the SDK does not have: Twilio's bundle clones."""
			parti = uri.rstrip("/").split("/")
			if method != "POST" or parti[-1] != "Clones":
				return SimpleNamespace(
					status_code=404, text=json.dumps({"message": "Not found", "code": 20404})
				)
			originale = mondo.pacchetti.get(parti[-2])
			verso = mondo.conti.get((data or {}).get("TargetAccountSid"))
			if not originale or originale.account != conto.sid:
				return SimpleNamespace(
					status_code=404, text=json.dumps({"message": "Bundle not found", "code": 20404})
				)
			if originale.status != "twilio-approved" or not verso or verso.owner_account_sid != conto.sid:
				return SimpleNamespace(
					status_code=400,
					text=json.dumps({"message": "The bundle cannot be cloned", "code": 22217}),
				)
			copia = SimpleNamespace(**{**vars(originale), "sid": _sid("BU"), "account": verso.sid})
			mondo.pacchetti[copia.sid] = copia
			mondo.cambi.append((conto.sid, "clone Bundle", copia.sid))
			return SimpleNamespace(
				status_code=201,
				text=json.dumps({"bundle_sid": copia.sid, "account_sid": verso.sid, "status": copia.status}),
			)

		self.request = request
		allarmi = mondo.allarmi[sid]
		self.monitor = SimpleNamespace(
			v1=SimpleNamespace(
				alerts=SimpleNamespace(
					list=lambda log_level=None, **_f: [
						a for a in allarmi if log_level is None or a.log_level == log_level
					]
				)
			)
		)
		self.trunking = SimpleNamespace(v1=SimpleNamespace(trunks=_Risorsa(mondo, conto, "Trunk", [])))
