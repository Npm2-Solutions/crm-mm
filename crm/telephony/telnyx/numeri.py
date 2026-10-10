# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Italian numbers from the centre's Telnyx account, from DottorCloud (doc 65).

The same window as Twilio's (`crm.telephony.numeri`), with Telnyx's way:

1. **the kind** - geographic or toll-free: Telnyx sells no Italian mobile - with its
   price a month from Telnyx's own search, and whose it is;
2. **the number**, chosen among those Telnyx has: Italy has no approval before an
   order, so the number goes to Telnyx's check together with the documents;
3. **who it is for and the documents**: Telnyx's requirements for Italy, with the
   centre's values already in them (invoicing's company), an address in Italy, the
   documents as PDF, uploaded here;
4. **ordered**: DottorCloud uploads the documents, writes the address, gathers them
   in a requirement group and orders the number with it, already pointed at its
   TeXML application. Every hour it asks Telnyx how the order went and tells whoever
   asked; approved, the documents' files and what was written go - Telnyx has its
   copy - and the group is good for the next number of the same kind.

A document's file is one the person uploaded for this, private, or one of a request
of before: nothing else of the site's files can be sent to Telnyx from here.
"""

from __future__ import annotations

import base64
import json
import re

import frappe
import phonenumbers
from frappe import _
from frappe.utils import get_fullname, now_datetime

from crm.marchio import con_nome
from crm.notifiche import regole as N
from crm.notifiche.avvisi import avvisa
from crm.permissions import livelli
from crm.telephony import numeri as twilio_numeri
from crm.telephony import numeri_regole as T
from crm.telephony import operatore
from crm.telephony.telnyx import collegamento
from crm.telephony.telnyx import numeri_regole as R
from crm.telephony.telnyx.cliente import ErroreTelnyx, chiama, registra, tutte

RICHIESTA = "CRM Phone Number Request"
DI_TELNYX = {"provider": operatore.TELNYX}
CENTRO = collegamento.CENTRO
#: How many numbers a search shows.
QUANTI = 20


def _chiave():
	impostazioni = frappe.get_single(collegamento.IMPOSTAZIONI)
	api_secret = collegamento.chiave(impostazioni)
	if not (collegamento.collegato(impostazioni) and api_secret):
		frappe.throw(_("Telnyx is not connected."))
	return api_secret, impostazioni


def _ferma(errore: Exception):
	frappe.throw(collegamento.in_parole(errore), title=_("Telnyx"))


def _bello(numero: str) -> str:
	try:
		return phonenumbers.format_number(
			phonenumbers.parse(numero, None), phonenumbers.PhoneNumberFormat.INTERNATIONAL
		)
	except phonenumbers.NumberParseException:
		return numero


def _richiesta(nome: str):
	richiesta = frappe.get_doc(RICHIESTA, nome)
	if richiesta.provider != operatore.TELNYX:
		frappe.throw(_("This request was made to another carrier."))
	return richiesta


# ---------------------------------------------------------------------------
# what is offered


def _cerca(api_secret: str, tipo: R.Tipo, zona: str = "", cifre: str = "", quanti: int = QUANTI) -> list:
	"""The numbers Telnyx has now, of a kind - of an area, for a geographic one -
	with the digits written in them."""
	base = {
		"filter[country_code]": "IT",
		"filter[phone_number_type]": tipo.telnyx,
		"filter[limit]": quanti,
	}
	if cifre and len(cifre) >= 2:
		base["filter[phone_number][contains]"] = cifre
	tentativi = [{**base, "filter[national_destination_code]": p} for p in R.prefissi(zona)] or [base]
	for parametri in tentativi:
		trovati = (chiama("GET", "available_phone_numbers", api_secret, parametri=parametri) or {}).get(
			"data"
		) or []
		trovati = [n for n in trovati if T.del_tipo(n.get("phone_number"), tipo.chiave)]
		if zona:
			trovati = [n for n in trovati if T.nella_zona(n.get("phone_number"), zona)]
		if trovati:
			return trovati
	return []


@frappe.whitelist()
def get_number_offer() -> dict:
	"""The kinds of Italian number with their price a month, whose the number is,
	and the requests made."""
	livelli.verifica(CENTRO)
	api_secret, _impostazioni = _chiave()
	tipi = []
	for tipo in R.TIPI.values():
		prezzo, valuta = None, "USD"
		try:
			primo = _cerca(api_secret, tipo, quanti=1)
			if primo:
				costo = primo[0].get("cost_information") or {}
				prezzo, valuta = R.prezzo_al_mese(costo), costo.get("currency") or valuta
		except ErroreTelnyx as errore:
			registra("DottorCloud: Telnyx's prices", errore)
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
	dati = twilio_numeri.dati_del_centro()
	return {
		"kinds": tipi,
		"owners": [
			{"key": chiave, "label": _(nome), "description": _(spiegazione)}
			for chiave, (nome, spiegazione) in R.DI_CHI.items()
		],
		"owner": T.di_chi(dati),
		"email": dati.get("email") or "",
		# Telnyx's own way: the number before the documents, no email of its own
		"number_first": True,
		"asks_email": False,
		"files": {"extensions": list(R.ESTENSIONI), "max_mb": R.MASSIMO // (1024 * 1024)},
		"requests": richieste(),
	}


def richieste() -> list[dict]:
	"""The requests made to Telnyx, newest first, as the page shows them."""
	righe = frappe.get_all(
		RICHIESTA,
		filters=DI_TELNYX,
		fields=[
			"name",
			"number_type",
			"end_user_type",
			"area_code",
			"status",
			"failure",
			"numbers",
			"pending_orders",
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
		riga["ordered"] = [
			{"number": o.get("number"), "label": _bello(o.get("number") or "")}
			for o in _ordini(riga.pending_orders)
		]
		riga["failures"] = [r for r in (riga.failure or "").split("\n") if r]
		riga["requested_by_name"] = get_fullname(riga.requested_by) if riga.requested_by else ""
		riga["may_buy"] = T.si_compra(riga.status)
		riga["may_resend"] = T.si_rimanda(riga.status)
		del riga["failure"]
		del riga["pending_orders"]
	return righe


def _ordini(valore: str | None) -> list[dict]:
	try:
		ordini = json.loads(valore or "[]")
	except ValueError:
		return []
	return [o for o in ordini if isinstance(o, dict) and o.get("order")]


def _requisiti(api_secret: str, tipo: R.Tipo) -> tuple[str, list[dict]]:
	"""Telnyx's requirements for ordering a kind of Italian number: their id, and
	each requirement's type."""
	elenco = tutte(
		"requirements",
		api_secret,
		{
			"filter[country_code]": "IT",
			"filter[phone_number_type]": tipo.telnyx,
			"filter[action]": "ordering",
		},
		pagina=50,
	)
	if not elenco:
		frappe.throw(_("Telnyx does not sell this kind of number in Italy now."))
	primo = elenco[0]
	return str(primo.get("id") or ""), list(primo.get("requirement_types") or [])


@frappe.whitelist()
def get_number_requirements(
	number_type: str,
	end_user_type: str | None = None,
	area_code: str | None = None,
	request: str | None = None,
) -> dict:
	"""What Telnyx asks for a kind of Italian number: the fields with the centre's
	values, the documents, the address. Documents approved for the same kind - of the
	same area - are said instead: the number is ordered with those."""
	livelli.verifica(CENTRO)
	tipo = R.TIPI.get(number_type)
	if not tipo:
		frappe.throw(_("Choose the kind of number."))
	dati = twilio_numeri.dati_del_centro()
	utente = end_user_type if end_user_type in R.DI_CHI else T.di_chi(dati)
	if tipo.zona and not T.prefisso(area_code):
		frappe.throw(_("Write the prefix of the area: 02, 06, 011…"))
	gia = None if request else T.riusabile(richieste(), tipo.chiave, utente, area_code)
	if gia:
		return {"approved": gia["name"], "end_user_type": utente}
	api_secret, _impostazioni = _chiave()
	try:
		regola, requisiti = _requisiti(api_secret, tipo)
	except ErroreTelnyx as errore:
		_ferma(errore)
	campi = R.campi(requisiti, dati, utente)
	for campo in campi:
		if campo["known"]:
			campo["label"] = _(campo["label"])
	documenti = R.documenti(requisiti)
	for documento in documenti:
		for accettato in documento["accepted"]:
			if accettato["known"]:
				accettato["label"] = _(accettato["label"])
	return {
		"approved": None,
		"regulation": regola,
		"end_user_type": utente,
		"fields": campi,
		"documents": documenti,
		"address": {chiave: dati.get(chiave, "") for chiave in ("street", "city", "region", "postal_code")},
		"email": dati.get("email", ""),
		"previous": _di_prima(request),
	}


def _di_prima(request: str | None) -> dict | None:
	"""What was written for a draft or refused documents, to send them again: as
	Twilio's, with the number that was chosen."""
	if not request:
		return None
	richiesta = _richiesta(request)
	prima = twilio_numeri._di_prima_di(richiesta)
	if prima is not None:
		dettagli = frappe.parse_json(richiesta.details or "{}") or {}
		prima["phone_number"] = dettagli.get("phone_number") or ""
	return prima


@frappe.whitelist()
def search_numbers(number_type: str, area_code: str | None = None, contains: str | None = None) -> dict:
	"""The numbers Telnyx has now, of a kind - of an area, for a geographic one -
	with the digits written in them."""
	livelli.verifica(CENTRO)
	tipo = R.TIPI.get(number_type)
	if not tipo:
		frappe.throw(_("Choose the kind of number."))
	zona = T.prefisso(area_code) if tipo.zona else ""
	if tipo.zona and not zona:
		frappe.throw(_("Write the prefix of the area: 02, 06, 011…"))
	api_secret, _impostazioni = _chiave()
	cifre = re.sub(r"\D", "", contains or "")
	try:
		trovati = _cerca(api_secret, tipo, zona, cifre)
	except ErroreTelnyx as errore:
		_ferma(errore)
	numeri = []
	for numero in trovati:
		zone = {r.get("region_type"): r.get("region_name") for r in numero.get("region_information") or []}
		numeri.append(
			{
				"phone_number": numero.get("phone_number"),
				"label": _bello(numero.get("phone_number") or ""),
				"locality": zone.get("location") or zone.get("rate_center") or "",
				"region": zone.get("state") or "",
			}
		)
	return {"numbers": numeri}


# ---------------------------------------------------------------------------
# sending: the documents, the group, the order


def _testo(valore) -> str:
	return valore.strip() if isinstance(valore, str) else ""


def _file_del_centro(nome: str, richiesta: str | None = None):
	"""A document's file, if it may go to Telnyx: as Twilio's (`numeri._file_del_centro`),
	a PDF for Italy."""
	riga = twilio_numeri._file_del_centro(nome, richiesta, controlla=False)
	if problema := R.file_accettato(riga.file_name, riga.file_size):
		frappe.throw(_(problema))
	return riga


def _carica(api_secret: str, file_name: str, riferimento: str) -> str:
	"""A document's file uploaded to Telnyx: its id. Telnyx deletes a document not
	linked to anything within thirty minutes, so this happens right before the group."""
	file_doc = frappe.get_doc("File", file_name)
	contenuto = file_doc.get_content(encodings=[])
	if isinstance(contenuto, str):
		contenuto = contenuto.encode()
	return str(
		chiama(
			"POST",
			"documents",
			api_secret,
			corpo={
				"file": base64.b64encode(contenuto).decode(),
				"filename": file_doc.file_name,
				"customer_reference": riferimento,
			},
			attesa=60,
		)["data"]["id"]
	)


def _indirizzo(api_secret: str, valori: dict, indirizzo: dict, riferimento: str) -> str:
	"""The office's address in Telnyx (an address is never changed there: a new one
	each time): its id."""
	nome = valori.get("business_name") or riferimento
	return str(
		chiama(
			"POST",
			"addresses",
			api_secret,
			corpo={
				"business_name": nome,
				"first_name": valori.get("first_name") or nome,
				"last_name": valori.get("last_name") or nome,
				"street_address": indirizzo.get("street") or "",
				"locality": indirizzo.get("city") or "",
				"administrative_area": indirizzo.get("region") or indirizzo.get("city") or "",
				"postal_code": indirizzo.get("postal_code") or "",
				"country_code": "IT",
				"customer_reference": riferimento,
			},
		)["data"]["id"]
	)


def _gruppo(risposto) -> dict:
	"""A requirement group from Telnyx's answer, which comes without its `data` around it."""
	if isinstance(risposto, dict):
		return risposto.get("data") if isinstance(risposto.get("data"), dict) else risposto
	return {}


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
	phone_number: str | None = None,
) -> dict:
	"""Send the documents of a number to Telnyx and order it: the documents and the
	address uploaded, gathered in a requirement group with the fields; with every
	requirement filled, the number chosen ordered with the group, pointed at
	DottorCloud. Something missing, and the request stays a draft to put right."""
	livelli.verifica(CENTRO)
	tipo = R.TIPI.get(number_type)
	if not tipo:
		frappe.throw(_("Choose the kind of number."))
	utente = end_user_type if end_user_type in R.DI_CHI else R.AZIENDA
	zona = T.prefisso(area_code) if tipo.zona else ""
	if tipo.zona and not zona:
		frappe.throw(_("Write the prefix of the area: 02, 06, 011…"))
	numero = _testo(phone_number)
	if numero and not T.del_tipo(numero, tipo.chiave):
		frappe.throw(_("This number is not of the kind the documents are for."))
	if numero and zona and not T.nella_zona(numero, zona):
		frappe.throw(_("This number is not of the area the documents are for."))
	valori = frappe.parse_json(values) if isinstance(values, str) else dict(values or {})
	valori = {chiave: _testo(valore) for chiave, valore in (valori or {}).items() if _testo(valore)}
	documenti = frappe.parse_json(documents) if isinstance(documents, str) else list(documents or [])
	documenti = [d for d in documenti or [] if isinstance(d, dict) and d.get("type")]
	indirizzo = frappe.parse_json(address) if isinstance(address, str) else dict(address or {})
	indirizzo = {chiave: _testo(valore) for chiave, valore in (indirizzo or {}).items()}
	chiede_l_indirizzo = any(d.get("address") for d in documenti)
	if chiede_l_indirizzo and not all(indirizzo.get(k) for k in ("street", "city", "postal_code")):
		frappe.throw(_("Write the office's address: street, city and postal code."))

	richiesta = _richiesta(request) if request else frappe.new_doc(RICHIESTA)
	if request and not T.si_rimanda(richiesta.status):
		frappe.throw(_("These documents are already with Telnyx."))
	file_dei_documenti = {
		d["file"]: _file_del_centro(d["file"], richiesta.name if request else None)
		for d in documenti
		if d.get("file")
	}
	for documento in documenti:
		if not documento.get("file") and not documento.get("address"):
			frappe.throw(_("Upload the file of every document."))

	richiesta.update(
		{
			"number_type": tipo.chiave,
			"provider": operatore.TELNYX,
			"end_user_type": utente,
			"area_code": zona,
			"status": R.BOZZA,
			"regulation_sid": regulation,
			"email": _testo(email) or None,
			"requested_by": frappe.session.user,
			"requested_on": now_datetime(),
			"failure": "",
			"details": json.dumps(
				{
					"values": valori,
					"address": indirizzo,
					"phone_number": numero,
					"documents": [
						{"requirement": d.get("requirement"), "type": d["type"], "file": d.get("file")}
						for d in documenti
					],
				}
			),
		}
	)
	richiesta.save(ignore_permissions=True) if request else richiesta.insert(ignore_permissions=True)
	for nome in file_dei_documenti:
		frappe.db.set_value(
			"File", nome, {"attached_to_doctype": RICHIESTA, "attached_to_name": richiesta.name}
		)

	api_secret, impostazioni = _chiave()
	try:
		_regola, requisiti = _requisiti(api_secret, tipo)
		per_requisito = dict(valori)
		sid_documenti = []
		indirizzo_id = None
		for documento in documenti:
			if documento.get("address"):
				indirizzo_id = indirizzo_id or _indirizzo(api_secret, valori, indirizzo, richiesta.name)
				per_requisito[documento["requirement"]] = indirizzo_id
				continue
			sid = _carica(api_secret, documento["file"], richiesta.name)
			sid_documenti.append(sid)
			per_requisito[documento["requirement"]] = sid
		mancano = R.mancanti(requisiti, per_requisito)
		corpo = {
			"regulatory_requirements": [
				{"requirement_id": str(t.get("id")), "field_value": per_requisito[str(t.get("id"))]}
				for t in requisiti
				if per_requisito.get(str(t.get("id")))
			],
			"customer_reference": richiesta.name,
		}
		gruppo = None
		if richiesta.bundle_sid:
			try:
				gruppo = _gruppo(
					chiama("PATCH", f"requirement_groups/{richiesta.bundle_sid}", api_secret, corpo=corpo)
				)
			except ErroreTelnyx as errore:
				if errore.stato != 404:
					raise
		if not gruppo:
			gruppo = _gruppo(
				chiama(
					"POST",
					"requirement_groups",
					api_secret,
					corpo={
						"country_code": "IT",
						"phone_number_type": tipo.telnyx,
						"action": "ordering",
						**corpo,
					},
				)
			)
		gruppo_id = str(gruppo.get("id") or richiesta.bundle_sid or "")
		ordini = _ordini(richiesta.pending_orders)
		if not mancano:
			_chiedi_l_approvazione(api_secret, gruppo_id)
			if numero:
				ordini.append(_ordina(api_secret, impostazioni, numero, gruppo_id, richiesta.name))
	except ErroreTelnyx as errore:
		registra("DottorCloud: a Telnyx number request", errore)
		_ferma(errore)

	richiesta.update(
		{
			"bundle_sid": gruppo_id,
			"address_sid": indirizzo_id,
			"document_sids": json.dumps(sid_documenti),
			"pending_orders": json.dumps(ordini),
			"status": R.BOZZA if mancano else R.IN_VERIFICA,
			"failure": _("Telnyx asks for: {0}").format(", ".join(mancano)) if mancano else "",
		}
	)
	richiesta.save(ignore_permissions=True)
	return {
		"request": richiesta.name,
		"status": richiesta.status,
		"missing": [r for r in (richiesta.failure or "").split("\n") if r],
		"requests": richieste(),
	}


def _chiedi_l_approvazione(api_secret: str, gruppo: str) -> None:
	"""The group sent for Telnyx's approval. Italy has no approval before an order:
	Telnyx may say so, and the order goes to its check all the same."""
	try:
		chiama("POST", f"requirement_groups/{gruppo}/submit_for_approval", api_secret)
	except ErroreTelnyx as errore:
		if errore.stato is None or errore.stato >= 500:
			raise


def _ordina(api_secret: str, impostazioni, numero: str, gruppo: str, riferimento: str) -> dict:
	"""A number ordered with its documents, already on DottorCloud's TeXML application
	and messaging profile."""
	corpo = {
		"phone_numbers": [{"phone_number": numero, "requirement_group_id": gruppo}],
		"connection_id": impostazioni.texml_application_id,
		"customer_reference": riferimento,
	}
	if impostazioni.messaging_profile_id:
		corpo["messaging_profile_id"] = impostazioni.messaging_profile_id
	ordine = chiama("POST", "number_orders", api_secret, corpo=corpo)["data"]
	return {"order": str(ordine.get("id")), "number": numero}


@frappe.whitelist(methods=["POST"])
def delete_number_request(request: str) -> dict:
	"""A draft, or documents Telnyx refused, taken away: here and in Telnyx."""
	livelli.verifica(CENTRO)
	richiesta = _richiesta(request)
	if not T.si_rimanda(richiesta.status):
		frappe.throw(_("These documents are already with Telnyx."))
	if richiesta.bundle_sid and collegamento.collegato():
		api_secret, _impostazioni = _chiave()
		try:
			chiama("DELETE", f"requirement_groups/{richiesta.bundle_sid}", api_secret)
		except ErroreTelnyx as errore:
			if errore.stato != 404:
				registra("DottorCloud: a draft left in Telnyx", errore)
	twilio_numeri._togli_i_file(richiesta)
	frappe.delete_doc(RICHIESTA, richiesta.name, ignore_permissions=True)
	return {"requests": richieste()}


# ---------------------------------------------------------------------------
# how it went


def _perche(api_secret: str, richiesta) -> list[str]:
	"""Why Telnyx refused: what its reviewers wrote on the order or on the group."""
	righe = []
	for tipo, ident in (("requirement_group", richiesta.bundle_sid),):
		if not ident:
			continue
		try:
			for commento in tutte(
				"comments",
				api_secret,
				{"filter[comment_record_type]": tipo, "filter[comment_record_id]": ident},
				pagina=50,
			):
				if (commento.get("commenter_type") or "admin") == "admin" and commento.get("body"):
					righe.append(commento["body"].strip()[:300])
		except ErroreTelnyx:
			continue
	return righe or [_("Telnyx did not say why: write to Telnyx's support, or send the documents again.")]


def aggiorna_le_richieste() -> list[str]:
	"""Every hour: what Telnyx decided of the numbers ordered, told to whoever
	asked. Approved, the number is the centre's, pointed at DottorCloud, and the
	documents' files and what was written go. Returns the requests that moved."""
	in_attesa = frappe.get_all(RICHIESTA, filters={"status": R.IN_VERIFICA, **DI_TELNYX}, pluck="name")
	impostazioni = frappe.get_single(collegamento.IMPOSTAZIONI)
	api_secret = collegamento.chiave(impostazioni)
	if not in_attesa or not (collegamento.collegato(impostazioni) and api_secret):
		return []
	mosse = []
	for nome in in_attesa:
		richiesta = frappe.get_doc(RICHIESTA, nome)
		try:
			esito = _come_va(api_secret, richiesta)
		except ErroreTelnyx as errore:
			registra("DottorCloud: Telnyx's number orders", errore)
			continue
		if not esito:
			continue
		stato, comprati = esito
		richiesta.status = stato
		if comprati:
			gia = [n for n in (richiesta.numbers or "").split("\n") if n]
			richiesta.numbers = "\n".join([*gia, *[n for n in comprati if n not in gia]])
		if stato == R.RIFIUTATA:
			richiesta.failure = "\n".join(_perche(api_secret, richiesta))
		if stato == R.APPROVATA:
			richiesta.details = None
			richiesta.failure = ""
		richiesta.save(ignore_permissions=True)
		if stato == R.APPROVATA:
			twilio_numeri._togli_i_file(richiesta)
			collegamento._aggiorna_i_numeri()
			for numero in comprati:
				avvisa(
					richiesta.requested_by,
					"Phone",
					N.NUMERO_APPROVATO_TELNYX,
					[_bello(numero)],
					oggetto=(RICHIESTA, richiesta.name),
				)
		elif stato == R.RIFIUTATA:
			avvisa(
				richiesta.requested_by,
				"Phone",
				N.NUMERO_RIFIUTATO_TELNYX,
				oggetto=(RICHIESTA, richiesta.name),
			)
		mosse.append(nome)
	return mosse


def _come_va(api_secret: str, richiesta) -> tuple[str, list[str]] | None:
	"""The request's state from its orders - or its group, without one - and the
	numbers that became the centre's; None while nothing moved."""
	ordini = _ordini(richiesta.pending_orders)
	if not ordini:
		if not richiesta.bundle_sid:
			return None
		gruppo = _gruppo(chiama("GET", f"requirement_groups/{richiesta.bundle_sid}", api_secret))
		stato = R.stato_del_gruppo(gruppo.get("status"))
		return (stato, []) if stato in (R.APPROVATA, R.RIFIUTATA) else None
	restano, comprati, rifiutati = [], [], []
	for ordine in ordini:
		dati = (chiama("GET", f"number_orders/{ordine['order']}", api_secret) or {}).get("data") or {}
		stato = R.stato_dell_ordine(dati.get("status"))
		if stato == R.APPROVATA:
			comprati.append(ordine["number"])
		elif stato == R.RIFIUTATA:
			rifiutati.append(ordine["number"])
		else:
			restano.append(ordine)
	if not (comprati or rifiutati):
		return None
	richiesta.pending_orders = json.dumps(restano)
	if restano:
		return R.IN_VERIFICA, comprati
	return (R.APPROVATA if comprati else R.RIFIUTATA), comprati


@frappe.whitelist(methods=["POST"])
def refresh_number_requests() -> dict:
	"""«Check» on the numbers: the orders as Telnyx has them now."""
	livelli.verifica(CENTRO)
	aggiorna_le_richieste()
	return {"requests": richieste()}


# ---------------------------------------------------------------------------
# buying and releasing


@frappe.whitelist(methods=["POST"])
def buy_number(request: str, phone_number: str) -> dict:
	"""Order another number with documents Telnyx approved: it goes to Telnyx's
	check - Italy's numbers always do - already pointed at DottorCloud."""
	livelli.verifica(CENTRO)
	richiesta = _richiesta(request)
	if not T.si_compra(richiesta.status):
		frappe.throw(_("The documents have to be approved by Telnyx first."))
	tipo = R.TIPI[richiesta.number_type]
	numero = _testo(phone_number)
	if not T.del_tipo(numero, tipo.chiave):
		frappe.throw(_("This number is not of the kind the documents are for."))
	if tipo.zona and not T.nella_zona(numero, richiesta.area_code):
		frappe.throw(_("This number is not of the area the documents are for."))
	api_secret, impostazioni = _chiave()
	try:
		ordine = _ordina(api_secret, impostazioni, numero, richiesta.bundle_sid, richiesta.name)
	except ErroreTelnyx as errore:
		registra("DottorCloud: ordering a Telnyx number", errore)
		_ferma(errore)
	richiesta.pending_orders = json.dumps([*_ordini(richiesta.pending_orders), ordine])
	richiesta.status = R.IN_VERIFICA
	richiesta.save(ignore_permissions=True)
	return {
		"phone_number": numero,
		"label": _bello(numero),
		"pending": True,
		"requests": richieste(),
	}


@frappe.whitelist(methods=["POST"])
def release_number(phone_number: str) -> dict:
	"""Give a number back to Telnyx: it stops costing, and whoever calls it hears it
	does not exist. Only one DottorCloud manages: on its application or with its tag."""
	livelli.verifica(CENTRO)
	api_secret, impostazioni = _chiave()
	numero = _testo(phone_number)
	cifre = re.sub(r"\D", "", numero)
	try:
		trovati = [
			n
			for n in tutte("phone_numbers", api_secret, {"filter[phone_number]": cifre})
			if n.get("phone_number") == numero
		]
		if not trovati:
			frappe.throw(con_nome(_("This number is not among {brand}'s numbers in Telnyx.")))
		trovato = trovati[0]
		nostro = str(trovato.get("connection_id") or "") in collegamento.nostre(impostazioni) or (
			collegamento.segno() in (trovato.get("tags") or [])
		)
		if not nostro:
			frappe.throw(con_nome(_("This number is not among {brand}'s numbers in Telnyx.")))
		chiama("DELETE", f"phone_numbers/{trovato['id']}", api_secret)
	except ErroreTelnyx as errore:
		_ferma(errore)
	collegamento._aggiorna_i_numeri()
	return {"released": numero}
