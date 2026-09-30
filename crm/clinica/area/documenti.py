# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The documents the centre gave online, in the client area (design.md, "L'area
cliente"): while they are online, downloaded after a code verified in the last
minutes, and logged like the page `/referto` (`crm.clinica.consegna`).
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime

from crm.area import accesso
from crm.area.api import _mia

CONSEGNA = "Clinic Report Delivery"


def _online(person: str) -> list:
	from crm.clinica import consegna

	adesso = now_datetime()
	return [
		riga
		for riga in frappe.get_all(
			CONSEGNA,
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


@frappe.whitelist()
def get_documents(person: str) -> dict:
	"""What the centre gave online, while it is online."""
	_mia(person)
	voci = []
	for riga in _online(person):
		documento = frappe.db.get_value(
			"Clinic Document", riga.document, ["title", "document_type", "document_date"], as_dict=True
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
	"""A document, after a code verified in the last minutes; logged like /referto."""
	from crm.clinica import archivio, consegna
	from crm.moduli import traccia

	_mia(person)
	if not accesso.verificato_da_poco():
		frappe.throw(_("Enter your code again to download it"), frappe.PermissionError)
	riga = next((r for r in _online(person) if r.name == delivery), None)
	if not riga:
		frappe.throw(_("This document is no longer online: ask the centre"), frappe.PermissionError)
	documento = frappe.get_doc("Clinic Document", riga.document)
	file_url = archivio._file_di(documento)
	contenuto = frappe.get_doc("File", {"file_url": file_url}).get_content(encodings=[])
	frappe.local.flags.commit = True
	frappe.db.set_value(
		CONSEGNA,
		riga.name,
		{
			"status": consegna.SCARICATO,
			"downloads": (riga.downloads or 0) + 1,
			"last_download_on": now_datetime(),
		},
	)
	traccia.traccia(CONSEGNA, riga.name, "downloaded", _("From the client area"))
	frappe.local.response.filename = file_url.rsplit("/", 1)[-1]
	frappe.local.response.filecontent = contenuto
	frappe.local.response.type = "download"
