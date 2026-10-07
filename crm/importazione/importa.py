# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Settings > The centre > Your data: people brought over from the previous
software (`persone.importa`).

The sheet is uploaded private, read as it comes (`foglio`), its columns
recognised (`regole.riconosci`) and shown with what is wrong row by row before
anything is written. Then a job brings the people in: somebody already here -
found by fiscal code, email or mobile - gets only what DottorCloud did not know;
somebody new is made, with their billing details (fiscal code, birth, address)
and their notes as a note. A module that has something to do with somebody
brought over registers it (`registra_dopo`): the clinic makes them patients by
the import rule.
"""

from __future__ import annotations

from collections.abc import Callable

import frappe
from frappe import _

from crm.importazione import foglio, regole
from crm.permissions.livelli import richiede

CHIAVE = "crm:importazione"
EVENTO = "crm_importazione"
#: Rows a sheet may hold.
MASSIMO = 20000
#: Rows the preview shows.
ANTEPRIMA = 20

_dopo: list[Callable[[str], None]] = []


def registra_dopo(funzione: Callable[[str], None]) -> None:
	"""What a module does with each person brought over, new or found."""
	if funzione not in _dopo:
		_dopo.append(funzione)


def _foglio(file_url: str) -> tuple[list, list[list]]:
	file = frappe.get_doc("File", {"file_url": file_url})
	if not file.has_permission("read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	righe = foglio.leggi(file.file_name, file.get_content(encodings=[]), MASSIMO)
	righe = [riga for riga in righe if any(cella not in (None, "") for cella in riga)]
	if not righe:
		frappe.throw(_("The sheet is empty"))
	return list(righe[0]), righe[1:]


def _in_parole(problemi: list[tuple[str, str]]) -> list[str]:
	return [_(frase).format(valore) for frase, valore in problemi]


@frappe.whitelist()
@richiede("persone.importa")
def preview(file_url: str) -> dict:
	"""What the sheet holds, before anything is written: which column is what, the
	first rows as people, what is wrong, who is already here."""
	intestazione, righe = _foglio(file_url)
	mappa = regole.riconosci(intestazione)
	anteprima, con_problemi, gia_qui = [], 0, 0
	for numero, riga in enumerate(righe, start=2):
		dati, problemi = regole.persona(riga, mappa, intestazione)
		if problemi:
			con_problemi += 1
		trovata = _trova(dati)
		if trovata:
			gia_qui += 1
		if len(anteprima) < ANTEPRIMA:
			anteprima.append(
				{
					"row": numero,
					"name": " ".join(filter(None, (dati["first_name"], dati["last_name"]))),
					"email": dati["email"],
					"mobile": dati["mobile_no"] or dati["phone"],
					"fiscal_code": dati["fiscal_code"],
					"found": trovata,
					"problems": _in_parole(problemi),
				}
			)
	return {
		"columns": [{"name": str(nome or ""), "field": mappa.get(i)} for i, nome in enumerate(intestazione)],
		"total": len(righe),
		"with_problems": con_problemi,
		"found": gia_qui,
		"rows": anteprima,
		"running": frappe.cache.get_value(CHIAVE),
	}


@frappe.whitelist(methods=["POST"])
@richiede("persone.importa")
def start(file_url: str) -> dict:
	"""Bring the sheet's people in, in a job. One sheet at a time."""
	if frappe.cache.get_value(CHIAVE):
		frappe.throw(_("A sheet is already being brought in"))
	_foglio(file_url)
	frappe.cache.set_value(
		CHIAVE, {"by": frappe.session.user, "done": 0, "total": 0}, expires_in_sec=6 * 3600
	)
	frappe.enqueue(
		"crm.importazione.importa.importa",
		queue="long",
		timeout=2 * 3600,
		file_url=file_url,
		utente=frappe.session.user,
		enqueue_after_commit=True,
	)
	return {"started": True}


def importa(file_url: str, utente: str) -> dict:
	"""Bring every row in; one that fails is said, the others go on."""
	esito = {"created": 0, "updated": 0, "skipped": 0, "errors": []}
	try:
		intestazione, righe = _foglio(file_url)
		mappa = regole.riconosci(intestazione)
		for numero, riga in enumerate(righe, start=2):
			dati, problemi = regole.persona(riga, mappa, intestazione)
			if (regole.SENZA_NOME, "") in problemi:
				esito["skipped"] += 1
				continue
			try:
				nuova = _porta(dati)
				frappe.db.commit()  # nosemgrep: frappe-manual-commit — each person on their own
			except Exception as errore:
				frappe.db.rollback()
				esito["errors"].append({"row": numero, "error": str(errore)[:200]})
				continue
			esito["created" if nuova else "updated"] += 1
			if numero % 50 == 0:
				_avanza(utente, numero - 1, len(righe))
		return esito
	finally:
		frappe.cache.delete_value(CHIAVE)
		frappe.publish_realtime(EVENTO, {"state": "done", **esito}, user=utente, after_commit=False)


def _trova(dati: dict) -> str | None:
	"""The person already here, by the surest key the row has."""
	for chiave, valore in regole.chiavi(dati):
		if chiave == "fiscal_code":
			trovata = frappe.db.get_value(
				"CRM Billing Profile", {"fiscal_code": valore, "party_type": "CRM Lead"}, "party"
			)
		elif chiave == "email":
			trovata = frappe.db.get_value("CRM Lead", {"email": valore}, "name")
		else:
			trovata = frappe.db.get_value("CRM Lead", {"mobile_no": ["like", f"%{valore}"]}, "name")
		if trovata:
			return trovata
	return None


GENERE = {"M": "Male", "F": "Female"}


def _porta(dati: dict) -> bool:
	"""One person in; True when they are new. Somebody already here keeps what
	they have: the sheet only fills what DottorCloud did not know."""
	nome = _trova(dati)
	nuova = not nome
	if nuova:
		persona = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": dati["first_name"] or dati["last_name"],
				"last_name": dati["last_name"] if dati["first_name"] else "",
				"email": dati["email"] or None,
				"mobile_no": dati["mobile_no"] or None,
				"phone": dati["phone"] or None,
			}
		)
		if dati["sex"] and frappe.db.exists("Gender", GENERE[dati["sex"]]):
			persona.gender = GENERE[dati["sex"]]
		persona.insert(ignore_permissions=True)
		nome = persona.name
	else:
		persona = frappe.get_doc("CRM Lead", nome)
		cambiati = False
		for campo in ("email", "mobile_no", "phone"):
			if dati[campo] and not persona.get(campo):
				persona.set(campo, dati[campo])
				cambiati = True
		if cambiati:
			persona.save(ignore_permissions=True)

	_anagrafica(nome, dati)
	if dati["notes"] and nuova:
		frappe.get_doc(
			{
				"doctype": "FCRM Note",
				"title": _("From the previous software"),
				"content": frappe.utils.escape_html(dati["notes"]),
				"reference_doctype": "CRM Lead",
				"reference_docname": nome,
			}
		).insert(ignore_permissions=True)
	for funzione in _dopo:
		funzione(nome)
	return nuova


def _anagrafica(nome: str, dati: dict) -> None:
	"""The billing details the sheet brings: only where the person has none."""
	campi = (
		"fiscal_code",
		"birth_date",
		"sex",
		"address_line",
		"civic_number",
		"postal_code",
		"city",
		"province",
	)
	if not any(dati.get(campo) for campo in campi):
		return
	if frappe.db.exists("CRM Billing Profile", {"party_type": "CRM Lead", "party": nome}):
		return
	profilo = frappe.get_doc(
		{
			"doctype": "CRM Billing Profile",
			"party_type": "CRM Lead",
			"party": nome,
			"billing_name": " ".join(filter(None, (dati["first_name"], dati["last_name"]))),
			"country": "IT",
			**{campo: dati[campo] for campo in campi if dati.get(campo)},
		}
	)
	profilo.insert(ignore_permissions=True)


def _avanza(utente: str, fatti: int, totale: int) -> None:
	stato = {"by": utente, "done": fatti, "total": totale}
	frappe.cache.set_value(CHIAVE, stato, expires_in_sec=6 * 3600)
	frappe.publish_realtime(EVENTO, {"state": "running", **stato}, user=utente, after_commit=False)
