# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Italian numbers in the centre's Twilio space, from DottorCloud (doc 52, second part).

A number is asked for here, in three steps:

1. **the kind** (mobile, geographic, toll-free), with what it is for and its price a
   month from Twilio's own prices, and whose it is: a company or a professional in
   their own name;
2. **who it is for**: the fields of Twilio's regulation for Italy, with the centre's
   values already in them (invoicing's company), and the documents that prove them,
   uploaded here: a PDF, JPEG or PNG of 5 MB at most;
3. **sent to Twilio**, which checks them in a few days. Before sending, Twilio's own
   evaluation says what is missing, and nothing goes for review until it passes;
   after, DottorCloud asks every hour how it went, and tells whoever asked - Twilio
   writes to the centre's email too.

Approved, the number is chosen among those Twilio has and bought with one click,
already pointed at DottorCloud. Approved documents are good for more numbers of the
same kind (of the same area, for a geographic one): the next number is bought at
once. Once Twilio approved them, the documents' files and what was written are not
kept here: Twilio has its copy. A number of the space can be released.

A document's file is one the person uploaded for this, private, or one of a request
of before: nothing else of the site's files can be sent to Twilio from here.

Everything happens in DottorCloud's space, with the space's codes
(`crm.telephony.collegamento`).
"""

from __future__ import annotations

import json
import re

import frappe
import phonenumbers
import requests
from frappe import _
from frappe.utils import get_fullname, now_datetime, validate_email_address

from crm import marchio
from crm.marchio import con_nome
from crm.notifiche import regole as N
from crm.notifiche.avvisi import avvisa
from crm.permissions import livelli
from crm.telephony import collegamento
from crm.telephony import numeri_regole as R

RICHIESTA = "CRM Phone Number Request"
CENTRO = collegamento.CENTRO
#: Where Twilio takes a document's file: the SDK has no upload of its own.
CARICAMENTO = "https://numbers-upload.twilio.com/v2/RegulatoryCompliance/SupportingDocuments"
#: How many numbers a search shows.
QUANTI = 20


def _cliente(impostazioni=None):
	"""The space's client: the numbers live there."""
	impostazioni = impostazioni or frappe.get_single(collegamento.IMPOSTAZIONI)
	if not collegamento.collegato(impostazioni):
		frappe.throw(_("Twilio is not connected."))
	auth_token = impostazioni.get_password("auth_token", raise_exception=False)
	return collegamento.Client(impostazioni.account_sid, auth_token)


def _ferma(errore: Exception):
	frappe.throw(collegamento.in_parole(errore), title=_("Twilio"))


def _posta(url: str, **valori):
	"""A request to Twilio outside the SDK: the documents' upload."""
	return requests.post(url, **valori)


def dati_del_centro() -> dict:
	"""What DottorCloud already knows of the centre, for the fields Twilio asks:
	invoicing's company, the default one first. The email Twilio writes to is an
	ordinary one: a PEC mailbox may refuse what is not PEC."""
	nome = frappe.db.get_single_value("CRM Invoicing Settings", "default_company") or frappe.db.get_value(
		"CRM Invoicing Company", {"enabled": 1}, "name", order_by="is_default desc"
	)
	azienda = frappe.db.get_value("CRM Invoicing Company", nome, "*", as_dict=True) if nome else None
	email = (
		(azienda.email if azienda else None)
		or frappe.db.get_single_value("FCRM Settings", "reply_to_email")
		or frappe.db.get_value("User", frappe.session.user, "email")
		or ""
	)
	if not azienda:
		return {
			"business_name": frappe.db.get_single_value("FCRM Settings", "brand_name") or "",
			"email": email,
		}
	return {
		"business_name": azienda.company_name or "",
		"vat_number": azienda.tax_id or "",
		"fiscal_code": azienda.fiscal_code or "",
		"first_name": azienda.first_name or "",
		"last_name": azienda.last_name or "",
		"email": email,
		"phone": azienda.phone or "",
		"nationality": "IT",
		"street": " ".join(p for p in (azienda.address_line, azienda.civic_number) if p),
		"city": azienda.city or "",
		"region": azienda.province or "",
		"postal_code": azienda.postal_code or "",
	}


def _in_parole(campi: list[dict]) -> list[dict]:
	"""The words DottorCloud gives a field, in the reader's language; Twilio's stay."""
	return [{**campo, "label": _(campo["label"]) if campo["known"] else campo["label"]} for campo in campi]


def _parole_dei_campi() -> dict:
	return {nome: _(parole) for nome, (parole, _fonte) in R.CAMPI_NOTI.items()}


def _bello(numero: str) -> str:
	"""A number as people read it: +39 02 1234 5678."""
	try:
		return phonenumbers.format_number(
			phonenumbers.parse(numero, None), phonenumbers.PhoneNumberFormat.INTERNATIONAL
		)
	except phonenumbers.NumberParseException:
		return numero


# ---------------------------------------------------------------------------
# what is offered


@frappe.whitelist()
def get_number_offer() -> dict:
	"""The kinds of Italian number with their price a month, whose the number is,
	and the requests made."""
	livelli.verifica(CENTRO)
	prezzi, valuta = [], "USD"
	try:
		paese = _cliente().pricing.v1.phone_numbers.countries("IT").fetch()
		prezzi = [dict(p) for p in (paese.phone_number_prices or [])]
		valuta = paese.price_unit or valuta
	except collegamento.NON_RISPONDE as errore:
		collegamento._registra("DottorCloud: Twilio's prices", errore)
	tipi = []
	for tipo in R.TIPI.values():
		prezzo = R.prezzo_al_mese(prezzi, tipo.chiave)
		tipi.append(
			{
				"key": tipo.chiave,
				"name": _(tipo.nome),
				"description": _(tipo.spiegazione),
				"calls_out": tipo.chiama,
				"sms": tipo.sms,
				"area": tipo.zona,
				"price": float(prezzo) if prezzo is not None else None,
				"currency": valuta,
			}
		)
	dati = dati_del_centro()
	return {
		"kinds": tipi,
		"owners": [
			{"key": chiave, "label": _(nome), "description": _(spiegazione)}
			for chiave, (nome, spiegazione) in R.DI_CHI.items()
		],
		"owner": R.di_chi(dati),
		"email": dati.get("email") or "",
		"requests": richieste(),
	}


def richieste() -> list[dict]:
	"""The requests, newest first, as the page shows them."""
	righe = frappe.get_all(
		RICHIESTA,
		fields=[
			"name",
			"number_type",
			"end_user_type",
			"area_code",
			"status",
			"failure",
			"numbers",
			"email",
			"requested_by",
			"requested_on",
		],
		order_by="creation desc",
		limit=50,
	)
	for riga in righe:
		tipo = R.TIPI.get(riga.number_type)
		riga["kind"] = _(tipo.nome) if tipo else riga.number_type
		riga["numbers"] = [{"number": n, "label": _bello(n)} for n in (riga.numbers or "").split("\n") if n]
		riga["failures"] = [r for r in (riga.failure or "").split("\n") if r]
		riga["requested_by_name"] = get_fullname(riga.requested_by) if riga.requested_by else ""
		riga["may_buy"] = R.si_compra(riga.status)
		riga["may_resend"] = R.si_rimanda(riga.status)
		del riga["failure"]
	return righe


@frappe.whitelist()
def get_number_requirements(
	number_type: str,
	end_user_type: str | None = None,
	area_code: str | None = None,
	request: str | None = None,
) -> dict:
	"""What Twilio asks for a kind of number, in Italy, of a company or of a
	professional: the fields with the centre's values, the documents, the address.
	Documents already approved for the same kind - of the same area - are said
	instead: the number is bought with those. With ``request``, a draft or refused
	documents to send again: what was written then, and the files uploaded."""
	livelli.verifica(CENTRO)
	tipo = R.TIPI.get(number_type)
	if not tipo:
		frappe.throw(_("Choose the kind of number."))
	dati = dati_del_centro()
	utente = end_user_type if end_user_type in R.DI_CHI else R.di_chi(dati)
	if tipo.zona and not R.prefisso(area_code):
		frappe.throw(_("Write the prefix of the area: 02, 06, 011…"))
	gia = None if request else R.riusabile(richieste(), tipo.chiave, utente, area_code)
	if gia:
		return {"approved": gia["name"], "end_user_type": utente}
	try:
		regole = _cliente().numbers.v2.regulatory_compliance.regulations.list(
			iso_country="IT", number_type=tipo.twilio, end_user_type=utente, limit=1
		)
	except collegamento.NON_RISPONDE as errore:
		_ferma(errore)
	if not regole:
		frappe.throw(_("Twilio does not sell this kind of number in Italy now."))
	regola = regole[0]
	requisiti = regola.requirements or {}
	utenti = requisiti.get("end_user") or []
	documenti = R.documenti_della_regola(requisiti.get("supporting_document") or [], dati)
	for documento in documenti:
		for accettato in documento["accepted"]:
			accettato["label"] = _(accettato["label"]) if accettato["known"] else accettato["label"]
			accettato["inputs"] = _in_parole(accettato["inputs"])
	return {
		"approved": None,
		"regulation": regola.sid,
		"end_user_type": utente,
		"fields": _in_parole(
			R.campi_della_regola((utenti[0].get("detailed_fields") if utenti else None) or [], dati)
		),
		"documents": documenti,
		"address": {chiave: dati.get(chiave, "") for chiave in ("street", "city", "region", "postal_code")},
		"email": dati.get("email", ""),
		"previous": _di_prima(request),
	}


def _di_prima(request: str | None) -> dict | None:
	"""What was written for a draft or for refused documents, to send them again
	without writing it twice: the values, the address, the documents chosen and
	their files, still the request's."""
	if not request:
		return None
	richiesta = frappe.get_doc(RICHIESTA, request)
	if not R.si_rimanda(richiesta.status):
		return None
	dettagli = frappe.parse_json(richiesta.details or "{}") or {}
	documenti = [d for d in dettagli.get("documents") or [] if isinstance(d, dict) and d.get("requirement")]
	suoi = {
		f.name: f
		for f in frappe.get_all(
			"File",
			filters={"attached_to_doctype": RICHIESTA, "attached_to_name": richiesta.name},
			fields=["name", "file_name"],
		)
	}
	return {
		"request": richiesta.name,
		"values": dettagli.get("values") or {},
		"address": dettagli.get("address") or {},
		"email": richiesta.email or "",
		"choices": {d["requirement"]: d.get("type") for d in documenti},
		"document_values": {
			f"{d['requirement']}:{campo}": valore
			for d in documenti
			for campo, valore in (d.get("values") or {}).items()
		},
		"files": {d["requirement"]: suoi[d["file"]] for d in documenti if d.get("file") in suoi},
	}


@frappe.whitelist()
def search_numbers(number_type: str, area_code: str | None = None, contains: str | None = None) -> dict:
	"""The numbers Twilio has now, of a kind - of an area, for a geographic one -
	with the digits written in them. Before the documents too: what there is."""
	livelli.verifica(CENTRO)
	tipo = R.TIPI.get(number_type)
	if not tipo:
		frappe.throw(_("Choose the kind of number."))
	zona = R.prefisso(area_code) if tipo.zona else ""
	if tipo.zona and not zona:
		frappe.throw(_("Write the prefix of the area: 02, 06, 011…"))
	cifre = re.sub(r"\D", "", contains or "")
	# the area's digits and the ones written, wherever Twilio finds them; the area
	# is checked here, from the start of the number
	filtro = (zona + cifre) if zona else cifre
	try:
		elenco = getattr(_cliente().available_phone_numbers("IT"), tipo.chiave).list(
			contains=filtro if len(filtro) >= 2 else None, limit=QUANTI
		)
	except collegamento.NON_RISPONDE as errore:
		_ferma(errore)
	numeri = []
	for numero in elenco:
		if not R.del_tipo(numero.phone_number, tipo.chiave):
			continue
		if zona and not R.nella_zona(numero.phone_number, zona):
			continue
		numeri.append(
			{
				"phone_number": numero.phone_number,
				"label": _bello(numero.phone_number),
				"locality": numero.locality or "",
				"region": numero.region or "",
			}
		)
	return {"numbers": numeri}


# ---------------------------------------------------------------------------
# sending


def _file_del_centro(nome: str, richiesta: str | None = None):
	"""A document's file, if it may go to Twilio: uploaded by this person for this,
	private and attached to nothing yet, or a request's own. Nothing else of the
	site's files - a person's records - leaves from here."""
	riga = frappe.db.get_value(
		"File",
		nome,
		["name", "file_name", "file_size", "is_private", "owner", "attached_to_doctype", "attached_to_name"],
		as_dict=True,
	)
	suo = bool(riga) and (
		(riga.attached_to_doctype == RICHIESTA and (not richiesta or riga.attached_to_name == richiesta))
		or (not riga.attached_to_doctype and riga.owner == frappe.session.user)
	)
	if not (suo and riga.is_private):
		frappe.throw(_("A document's file is not among those uploaded here: upload it again."))
	problema = R.file_accettato(riga.file_name, riga.file_size)
	if problema:
		frappe.throw(_(problema))
	return riga


def _testo(valore) -> str:
	return valore.strip() if isinstance(valore, str) else ""


@frappe.whitelist(methods=["POST"])
def send_number_request(
	number_type: str,
	regulation: str,
	values: str | dict,
	documents: str | list,
	address: str | dict | None = None,
	email: str | None = None,
	area_code: str | None = None,
	end_user_type: str | None = None,
	request: str | None = None,
) -> dict:
	"""Send the documents of a number to Twilio: whose it is, the address, each
	document with its file, gathered in one bundle. Twilio's evaluation says what
	is missing before it goes for review; nothing is submitted until it passes, and
	the request stays a draft to put right (``request``, sent again)."""
	livelli.verifica(CENTRO)
	tipo = R.TIPI.get(number_type)
	if not tipo:
		frappe.throw(_("Choose the kind of number."))
	utente = end_user_type if end_user_type in R.DI_CHI else R.AZIENDA
	zona = R.prefisso(area_code) if tipo.zona else ""
	if tipo.zona and not zona:
		frappe.throw(_("Write the prefix of the area: 02, 06, 011…"))
	valori = frappe.parse_json(values) if isinstance(values, str) else dict(values or {})
	valori = {chiave: _testo(valore) for chiave, valore in (valori or {}).items() if _testo(valore)}
	documenti = frappe.parse_json(documents) if isinstance(documents, str) else list(documents or [])
	documenti = [d for d in documenti or [] if isinstance(d, dict) and d.get("type")]
	indirizzo = frappe.parse_json(address) if isinstance(address, str) else dict(address or {})
	indirizzo = {chiave: _testo(valore) for chiave, valore in (indirizzo or {}).items()}
	email = _testo(email) or dati_del_centro().get("email") or ""
	if not validate_email_address(email):
		frappe.throw(_("Write the email Twilio writes to about the documents."))
	if R.chiede_l_indirizzo(documenti) and not all(
		indirizzo.get(k) for k in ("street", "city", "postal_code")
	):
		frappe.throw(_("Write the office's address: street, city and postal code."))

	richiesta = frappe.get_doc(RICHIESTA, request) if request else frappe.new_doc(RICHIESTA)
	if request and not R.si_rimanda(richiesta.status):
		frappe.throw(_("These documents are already with Twilio."))
	# every file is checked before anything goes to Twilio
	file_dei_documenti = {
		d["file"]: _file_del_centro(d["file"], richiesta.name if request else None)
		for d in documenti
		if d.get("file")
	}
	for documento in documenti:
		if not documento.get("file") and not documento.get("address"):
			frappe.throw(_("Upload the file of every document."))

	prima = {
		"bundle": richiesta.bundle_sid,
		"oggetti": [richiesta.end_user_sid, *json.loads(richiesta.document_sids or "[]")],
	}
	richiesta.update(
		{
			"number_type": tipo.chiave,
			"end_user_type": utente,
			"area_code": zona,
			"status": R.BOZZA,
			"regulation_sid": regulation,
			"email": email,
			"requested_by": frappe.session.user,
			"requested_on": now_datetime(),
			"failure": "",
			"details": json.dumps(
				{
					"values": valori,
					"address": indirizzo,
					"documents": [
						{
							"requirement": d.get("requirement"),
							"type": d["type"],
							"values": d.get("values") or {},
							"file": d.get("file"),
						}
						for d in documenti
					],
				}
			),
		}
	)
	richiesta.save(ignore_permissions=True) if request else richiesta.insert(ignore_permissions=True)
	# the documents' files are the request's: private, and gone once Twilio approves
	for nome in file_dei_documenti:
		frappe.db.set_value(
			"File", nome, {"attached_to_doctype": RICHIESTA, "attached_to_name": richiesta.name}
		)

	cliente = _cliente()
	regole = cliente.numbers.v2.regulatory_compliance
	nome_del_centro = valori.get("business_name") or " ".join(
		p for p in (valori.get("first_name"), valori.get("last_name")) if p
	)
	try:
		persona = regole.end_users.create(
			friendly_name=nome_del_centro or richiesta.name, type=utente, attributes=valori
		)
		sid_indirizzo = None
		if R.chiede_l_indirizzo(documenti):
			sid_indirizzo = cliente.addresses.create(
				customer_name=nome_del_centro or richiesta.name,
				street=indirizzo.get("street") or "",
				city=indirizzo.get("city") or "",
				region=indirizzo.get("region") or indirizzo.get("city") or "",
				postal_code=indirizzo.get("postal_code") or "",
				iso_country="IT",
			).sid
		sid_documenti = [_documento(cliente, documento, valori, sid_indirizzo) for documento in documenti]
		pacchetto = regole.bundles.create(
			friendly_name=f"{marchio.nome()} · {tipo.twilio}"[:64],
			email=email,
			regulation_sid=regulation,
		)
		for sid in (persona.sid, *sid_documenti):
			regole.bundles(pacchetto.sid).item_assignments.create(object_sid=sid)
		valutazione = regole.bundles(pacchetto.sid).evaluations.create()
		errori = R.errori_della_valutazione(list(valutazione.results or []), _parole_dei_campi())
		if not errori:
			regole.bundles(pacchetto.sid).update(status="pending-review")
	except collegamento.NON_RISPONDE as errore:
		_ferma(errore)

	richiesta.update(
		{
			"bundle_sid": pacchetto.sid,
			"end_user_sid": persona.sid,
			"address_sid": sid_indirizzo,
			"document_sids": json.dumps(sid_documenti),
			"status": R.BOZZA if errori else R.IN_VERIFICA,
			"failure": "\n".join(errori),
		}
	)
	richiesta.save(ignore_permissions=True)
	if prima["bundle"]:
		_togli_da_twilio(cliente, prima["bundle"], prima["oggetti"])
	return {"request": richiesta.name, "status": richiesta.status, "missing": errori, "requests": richieste()}


def _documento(cliente, documento: dict, valori: dict, sid_indirizzo: str | None) -> str:
	"""One document in Twilio: its fields from what was written for it, else from
	whose the number is, the address, and its file."""
	campi = [c for c in documento.get("fields") or [] if isinstance(c, str)]
	propri = documento.get("values") or {}
	attributi = {
		campo: _testo(propri.get(campo)) or valori.get(campo) for campo in campi if campo != "address_sids"
	}
	if "address_sids" in campi and sid_indirizzo:
		attributi["address_sids"] = [sid_indirizzo]
	attributi = {chiave: valore for chiave, valore in attributi.items() if valore}
	nome = f"{marchio.nome()} · {documento['type']}"[:64]
	if documento.get("file"):
		return _carica(cliente, nome, documento["type"], attributi, documento["file"])
	return cliente.numbers.v2.regulatory_compliance.supporting_documents.create(
		friendly_name=nome, type=documento["type"], attributes=attributi
	).sid


def _carica(cliente, nome: str, tipo: str, attributi: dict, file_name: str) -> str:
	"""A document with its file, to Twilio's upload."""
	from twilio.base.exceptions import TwilioRestException

	file_doc = frappe.get_doc("File", file_name)
	# the bytes as they are: no encodings to try, a PDF is not text
	contenuto = file_doc.get_content(encodings=[])
	risposta = _posta(
		CARICAMENTO,
		auth=(cliente.username, cliente.password),
		data={"FriendlyName": nome, "Type": tipo, "Attributes": json.dumps(attributi)},
		files={"File": (file_doc.file_name, contenuto)},
		timeout=60,
	)
	try:
		corpo = risposta.json()
	except ValueError:
		corpo = {}
	if risposta.status_code >= 400 or not corpo.get("sid"):
		raise TwilioRestException(
			risposta.status_code, CARICAMENTO, corpo.get("message", ""), corpo.get("code")
		)
	return corpo["sid"]


def _togli_da_twilio(cliente, bundle: str, oggetti: list):
	"""What a draft sent again left in Twilio: its bundle, whose and its documents.
	Free there, but nobody needs them."""
	regole = cliente.numbers.v2.regulatory_compliance
	try:
		regole.bundles(bundle).delete()
		for sid in oggetti:
			if not sid:
				continue
			risorsa = regole.end_users if sid.startswith("IT") else regole.supporting_documents
			risorsa(sid).delete()
	except collegamento.NON_RISPONDE as errore:
		collegamento._registra("DottorCloud: a draft left in Twilio", errore)


@frappe.whitelist(methods=["POST"])
def delete_number_request(request: str) -> dict:
	"""A draft, or documents Twilio refused, taken away: here and in Twilio."""
	livelli.verifica(CENTRO)
	richiesta = frappe.get_doc(RICHIESTA, request)
	if not R.si_rimanda(richiesta.status):
		frappe.throw(_("These documents are already with Twilio."))
	if richiesta.bundle_sid and collegamento.collegato():
		_togli_da_twilio(
			_cliente(),
			richiesta.bundle_sid,
			[richiesta.end_user_sid, *json.loads(richiesta.document_sids or "[]")],
		)
	_togli_i_file(richiesta)
	frappe.delete_doc(RICHIESTA, richiesta.name, ignore_permissions=True)
	return {"requests": richieste()}


# ---------------------------------------------------------------------------
# how it went


def aggiorna_le_richieste() -> list[str]:
	"""Every hour: what Twilio decided of the requests in review, told to whoever
	asked. Approved, the documents' files and what was written go: Twilio has its
	copy. Returns the requests that moved."""
	in_attesa = frappe.get_all(
		RICHIESTA, filters={"status": R.IN_VERIFICA, "bundle_sid": ["is", "set"]}, pluck="name"
	)
	if not in_attesa or not collegamento.collegato():
		return []
	mosse = []
	try:
		cliente = _cliente()
		regole = cliente.numbers.v2.regulatory_compliance
		for nome in in_attesa:
			richiesta = frappe.get_doc(RICHIESTA, nome)
			stato = R.stato_della_richiesta(regole.bundles(richiesta.bundle_sid).fetch().status)
			if stato in (richiesta.status, R.BOZZA):
				continue
			richiesta.status = stato
			if stato == R.RIFIUTATA:
				richiesta.failure = "\n".join(_perche(regole, richiesta))
			if stato == R.APPROVATA:
				richiesta.details = None
				richiesta.failure = ""
			richiesta.save(ignore_permissions=True)
			if stato == R.APPROVATA:
				_togli_i_file(richiesta)
			avvisa(
				richiesta.requested_by,
				"Phone",
				N.NUMERO_APPROVATO if stato == R.APPROVATA else N.NUMERO_RIFIUTATO,
				oggetto=(RICHIESTA, richiesta.name),
			)
			mosse.append(nome)
	except collegamento.NON_RISPONDE as errore:
		collegamento._registra("DottorCloud: Twilio's bundles", errore)
	return mosse


def _perche(regole, richiesta) -> list[str]:
	"""Why Twilio refused: what its evaluation finds now, else where it wrote."""
	try:
		valutazione = regole.bundles(richiesta.bundle_sid).evaluations.create()
		errori = R.errori_della_valutazione(list(valutazione.results or []), _parole_dei_campi())
	except collegamento.NON_RISPONDE:
		errori = []
	return errori or [_("Twilio wrote why to {0}.").format(richiesta.email)]


def _togli_i_file(richiesta):
	for file_doc in frappe.get_all(
		"File", filters={"attached_to_doctype": RICHIESTA, "attached_to_name": richiesta.name}, pluck="name"
	):
		frappe.delete_doc("File", file_doc, ignore_permissions=True)


@frappe.whitelist(methods=["POST"])
def refresh_number_requests() -> dict:
	"""«Check» on the numbers: the requests as Twilio has them now."""
	livelli.verifica(CENTRO)
	aggiorna_le_richieste()
	return {"requests": richieste()}


# ---------------------------------------------------------------------------
# buying and releasing


@frappe.whitelist(methods=["POST"])
def buy_number(request: str, phone_number: str) -> dict:
	"""Buy a number with approved documents, already pointed at DottorCloud."""
	livelli.verifica(CENTRO)
	richiesta = frappe.get_doc(RICHIESTA, request)
	if not R.si_compra(richiesta.status):
		frappe.throw(_("The documents have to be approved by Twilio first."))
	tipo = R.TIPI[richiesta.number_type]
	numero = _testo(phone_number)
	if not R.del_tipo(numero, tipo.chiave):
		frappe.throw(_("This number is not of the kind the documents are for."))
	if tipo.zona and not R.nella_zona(numero, richiesta.area_code):
		frappe.throw(_("This number is not of the area the documents are for."))
	dove = collegamento.indirizzi()
	valori = {
		"phone_number": numero,
		"bundle_sid": richiesta.bundle_sid,
		"voice_url": dove["voce"],
		"voice_method": "POST",
	}
	if tipo.sms:
		valori.update({"sms_url": dove["sms"], "sms_method": "POST"})
	if richiesta.address_sid:
		valori["address_sid"] = richiesta.address_sid
	try:
		comprato = _cliente().incoming_phone_numbers.create(**valori)
	except collegamento.NON_RISPONDE as errore:
		_ferma(errore)
	numeri = [n for n in (richiesta.numbers or "").split("\n") if n]
	richiesta.numbers = "\n".join([*numeri, comprato.phone_number])
	richiesta.save(ignore_permissions=True)
	collegamento._aggiorna_i_numeri()
	return {
		"phone_number": comprato.phone_number,
		"label": _bello(comprato.phone_number),
		"requests": richieste(),
	}


@frappe.whitelist(methods=["POST"])
def release_number(phone_number: str) -> dict:
	"""Give a number of the space back to Twilio: it stops costing, and whoever calls
	it hears it does not exist. Only in DottorCloud's own space: an account connected
	by hand may hold other sites' numbers."""
	livelli.verifica(CENTRO)
	impostazioni = frappe.get_single(collegamento.IMPOSTAZIONI)
	if not impostazioni.account_owner:
		frappe.throw(
			con_nome(
				_("This Twilio account was connected by hand: release its numbers from Twilio's console.")
			)
		)
	cliente = _cliente(impostazioni)
	numero = _testo(phone_number)
	try:
		trovati = [
			n for n in cliente.incoming_phone_numbers.list(phone_number=numero) if n.phone_number == numero
		]
		if not trovati:
			frappe.throw(con_nome(_("This number is not in {brand}'s space.")))
		cliente.incoming_phone_numbers(trovati[0].sid).delete()
	except collegamento.NON_RISPONDE as errore:
		_ferma(errore)
	collegamento._aggiorna_i_numeri()
	return {"released": numero}
