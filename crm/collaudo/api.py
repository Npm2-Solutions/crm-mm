# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What the simulation's people read and what the bench went through, for the
suite (e2e/simulazione): the mail each person received (the bench's email is
muted, so it stays in the queue, never sent), the SMS written to them, the errors
the server logged, the week's script. Only on a test bench, only for the agency."""

from __future__ import annotations

import email
import email.policy
import html
import re

import frappe
from frappe import _
from frappe.utils import get_datetime

from crm.collaudo import regole as R
from crm.collaudo import verifica

_LINK = re.compile(r"""href=["']([^"']+)["']""", re.IGNORECASE)
_LINK_NEL_TESTO = re.compile(r"https?://[^\s<>\"')]+")


def _parti(grezzo: str) -> tuple[str, str]:
	"""The words and the HTML of a message as the queue keeps it."""
	messaggio = email.message_from_string(grezzo or "", policy=email.policy.default)
	testo, pagina = "", ""
	for parte in messaggio.walk():
		if parte.is_multipart():
			continue
		tipo = parte.get_content_type()
		try:
			contenuto = parte.get_content()
		except Exception:
			continue
		if not isinstance(contenuto, str):
			continue
		if tipo == "text/html" and not pagina:
			pagina = contenuto
		elif tipo == "text/plain" and not testo:
			testo = contenuto
	return testo, pagina


def _soggetto(grezzo: str) -> str:
	return str(email.message_from_string(grezzo or "", policy=email.policy.default).get("Subject") or "")


def _in_chiaro(pagina: str) -> str:
	senza = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", pagina or "", flags=re.S | re.I)
	senza = re.sub(r"<br\s*/?>|</p>|</div>|</tr>|</h\d>", "\n", senza, flags=re.I)
	return re.sub(r"[ \t]+", " ", html.unescape(re.sub(r"<[^>]+>", " ", senza))).strip()


@frappe.whitelist()
def posta(a: str | None = None, dopo: str | None = None) -> list[dict]:
	"""The emails written to ``a`` - to anybody, without it - since ``dopo`` (the
	bench's hour), oldest first: recipients, subject, words, the links in them."""
	verifica()
	condizioni = {}
	if a:
		nomi = frappe.get_all(
			"Email Queue Recipient", filters={"recipient": a.strip().lower()}, pluck="parent", limit=500
		)
		if not nomi:
			return []
		condizioni["name"] = ["in", nomi]
	if dopo:
		condizioni["creation"] = [">=", get_datetime(dopo)]
	if not condizioni:
		frappe.throw(_("Say whose mail, or since when"))
	fuori = []
	for coda in frappe.get_all(
		"Email Queue",
		filters=condizioni,
		fields=["name", "creation", "message", "status", "reference_doctype", "reference_name"],
		order_by="creation asc",
		limit=300,
	):
		testo, pagina = _parti(coda.message)
		parole = testo or _in_chiaro(pagina)
		collegamenti = [html.unescape(link) for link in _LINK.findall(pagina or "")]
		collegamenti += [link for link in _LINK_NEL_TESTO.findall(testo or "") if link not in collegamenti]
		fuori.append(
			{
				"name": coda.name,
				"at": str(coda.creation),
				"to": frappe.get_all(
					"Email Queue Recipient", filters={"parent": coda.name}, pluck="recipient"
				),
				"subject": _soggetto(coda.message),
				"text": parole,
				"links": collegamenti,
				"status": coda.status,
				"reference": [coda.reference_doctype, coda.reference_name],
			}
		)
	return fuori


@frappe.whitelist()
def sms(a: str | None = None, dopo: str | None = None) -> list[dict]:
	"""The SMS DottorCloud wrote (to ``a``), as their register keeps them."""
	verifica()
	filtri = {}
	if dopo:
		filtri["creation"] = [">=", get_datetime(dopo)]
	righe = frappe.get_all(
		"CRM SMS Message",
		filters=filtri,
		fields=["name", "creation", "to", "message", "status", "error_message", "type"],
		order_by="creation asc",
		limit=500,
	)
	cifre = re.sub(r"\D", "", a or "")[-9:]
	return [r for r in righe if not cifre or re.sub(r"\D", "", r.to or "")[-9:] == cifre]


@frappe.whitelist()
def errori(dopo: str) -> list[dict]:
	"""What the server logged as an error since ``dopo`` (the bench's hour): a step
	of the simulation leaves none."""
	verifica()
	return frappe.get_all(
		"Error Log",
		filters={"creation": [">=", get_datetime(dopo)]},
		fields=["name", "creation", "method", "error"],
		order_by="creation asc",
		limit=50,
	)


@frappe.whitelist()
def copione() -> dict:
	"""The week's script: the centre, its team and their password, the people who
	will come, the services, and the week to play - the Monday after the last day
	anything was booked, so that a second week never meets the first."""
	verifica()
	from frappe.utils import getdate, nowdate

	from crm.collaudo import prepara

	ultimo = frappe.db.sql("select max(starts_on) from `tabCRM Appointment`")[0][0]
	dal = max(getdate(nowdate()), getdate(ultimo) if ultimo else getdate(nowdate()))
	lunedi = R.lunedi_dopo(dal)
	return {
		"centre": R.NOME_DEL_CENTRO,
		"password": prepara.password(),
		"team": prepara.squadra(),
		"people": [
			{
				"key": p.chiave,
				"first_name": p.nome,
				"last_name": p.cognome,
				"email": p.email,
				"mobile": p.cellulare,
				"sex": p.sesso,
				"birth_date": p.nascita,
				"device": p.dispositivo,
				"parent": p.genitore,
				"fiscal_code": R.codice_fiscale(p),
				"address": {
					"street": "Via Torino",
					"number": str(10 + i),
					"postcode": "20123",
					"city": "Milano",
				},
			}
			for i, p in enumerate(R.PERSONE)
		],
		"services": {s.chiave: s.nome for s in R.SERVIZI},
		# each location's record, as the invoices and the closings name it
		"locations": {
			chiave: frappe.db.get_value("CRM Location", {"location_name": nome}) or nome
			for chiave, nome, *_resto in R.SEDI
		},
		"location_titles": {chiave: nome for chiave, nome, *_resto in R.SEDI},
		"convention": R.CONVENZIONE["nome"],
		"company_client": {
			"name": R.AZIENDA_CLIENTE["nome"],
			"vat": R.AZIENDA_CLIENTE["partita_iva"],
			"street": f"{R.AZIENDA_CLIENTE['indirizzo'][0]} {R.AZIENDA_CLIENTE['indirizzo'][1]}",
			"postcode": R.AZIENDA_CLIENTE["indirizzo"][2],
			"city": R.AZIENDA_CLIENTE["indirizzo"][3],
			"person": R.AZIENDA_CLIENTE["persona"],
		},
		"subscriptions": {chiave: nome for chiave, nome, *_resto in R.ABBONAMENTI},
		"week": {nome: str(giorno) for nome, giorno in R.settimana(lunedi).items()},
	}
