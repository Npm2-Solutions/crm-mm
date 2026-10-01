# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The documents the centre gave online, in the client area: while they are
online, downloaded after a code verified in the last minutes, and logged like the
page `/documento` (`crm.documenti.consegna`).
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime

from crm.area import accesso, anteprima
from crm.area.api import _mia
from crm.documenti import consegna


def _online(person: str) -> list:
	adesso = now_datetime()
	return [
		riga
		for riga in frappe.get_all(
			consegna.CONSEGNA,
			filters={
				"lead": person,
				"channel": consegna.ONLINE,
				"status": ("in", (consegna.DISPONIBILE, consegna.SCARICATO)),
			},
			fields=["name", "document", "given_on", "expires_on", "downloads"],
			order_by="given_on desc",
		)
		if get_datetime(riga.expires_on) > adesso
	]


def documenti_online(person: str) -> int:
	"""How many documents the person has online now: the area shows the place then."""
	return len(_online(person))


@frappe.whitelist()
def get_documents(person: str) -> dict:
	"""What the centre gave online, while it is online. In the centre's preview,
	a document whoever previews does not read keeps its place, with nothing of it."""
	_mia(person, anche_in_anteprima=True)
	voci = []
	for riga in _online(person):
		if not anteprima.vede(consegna.DOCUMENTO, riga.document):
			voci.append({**anteprima.coperta(riga), "expires_on": riga.expires_on})
			continue
		documento = frappe.db.get_value(
			consegna.DOCUMENTO, riga.document, ["title", "document_type", "document_date"], as_dict=True
		)
		if not documento:
			continue
		voci.append(
			{
				"name": riga.name,
				"title": documento.title,
				"document_type": documento.document_type,
				"document_date": documento.document_date,
				"given_on": riga.given_on,
				"expires_on": riga.expires_on,
				"downloaded": bool(riga.downloads),
			}
		)
	return {"documents": voci, "verified": accesso.verificato_da_poco()}


@frappe.whitelist(methods=["GET"])
def download_document(person: str, delivery: str) -> None:
	"""A document, after a code verified in the last minutes; logged like /documento."""
	_mia(person)
	if not accesso.verificato_da_poco():
		frappe.throw(_("Enter your code again to download it"), frappe.PermissionError)
	riga = next((r for r in _online(person) if r.name == delivery), None)
	if not riga:
		frappe.throw(_("This document is no longer online: ask the centre"), frappe.PermissionError)
	consegna.scarica(riga, frappe.get_doc(consegna.DOCUMENTO, riga.document), _("From the client area"))
