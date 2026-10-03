# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The clinic's documents, on the CRM's (`crm.documenti`): the reports, the tests,
the images, the prescriptions - health data, read like the record.

- **Its kinds**, with the mark of health data: the report of a signed visit (made
  from the visit, `dal_referto`), an external report, a test result, an image, a
  prescription. Filed by who files health data (`clinica.archivia`): the desk for
  a practitioner it names, a practitioner for their patients, the medical director.
- **Its fields** on the CRM's document (`crm/clinica/custom`): who reads it - the
  care team, "my discipline", "only me" (a practitioner's choice about their own);
  obscured at the patient's request; the visit a report comes from; "never
  online" (genetic tests, HIV, a test the patient left out).
- **Who reads what carries the mark**: the dossier (`crm.clinica.dossier`,
  registered with `crm.permissions.sanitari`); every listing in the access log.
- **A report belongs to its visit**: not put right, not taken away.
- **Online** only with the patient's consent to online reports, never a document
  marked "never online", 45 days at most (the Garante's guidelines on online
  reports, 19/11/2009, and their FAQ).
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, get_fullname, getdate

from crm import lingue
from crm.clinica import dossier
from crm.documenti import api, consegna
from crm.documenti import regole as R
from crm.permissions import livelli

REFERTO = "Report"
#: The clinic's kinds, all health data; a report comes from a signed visit.
TIPI = (REFERTO, "External report", "Test result", "Imaging", "Prescription")
REFERTI_ONLINE = "online_reports"
#: The longest a report stays online (Garante, 2009).
GIORNI_ONLINE = 45


# ------------------------------------------------------------------ its fields


def _legge(doc) -> dict:
	return {
		"visibility": doc.get("visibility"),
		# shown only to who still reads it: whom it is for, who added it, the director
		"obscured": cint(doc.get("obscured")),
		"record": doc.get("record"),
		"not_online": cint(doc.get("not_online")),
	}


def _scrive(doc, dati: dict) -> None:
	scrive_la_cartella = livelli.puo("clinica.scrivi")
	tipo = R.tipo(doc.document_type)
	if tipo and tipo.clinico:
		# health data is for somebody who writes the record: oneself, or whom the desk names
		if not doc.practitioner:
			if not scrive_la_cartella:
				frappe.throw(_("Say which practitioner the document is for"))
			doc.practitioner = frappe.session.user
		if doc.practitioner != frappe.session.user and not livelli.puo("clinica.scrivi", doc.practitioner):
			frappe.throw(_("{0} does not write clinical records").format(get_fullname(doc.practitioner)))
	# "only me" and "my discipline" are a practitioner's choices about their own document
	proprio = scrive_la_cartella and doc.practitioner == frappe.session.user
	visibilita = dati.get("visibility")
	doc.visibility = visibilita if proprio and visibilita in dossier.VISIBILITA else dossier.TUTTI
	doc.not_online = cint(dati.get("not_online"))


def _scelte() -> dict:
	scrive = livelli.puo("clinica.scrivi")
	return {
		"for_me": scrive,
		# "my discipline" is offered to a practitioner who has one
		"discipline": dossier.disciplina_di(frappe.session.user) if scrive else None,
	}


def _fisso(doc) -> str | None:
	if doc.get("record"):
		return _("A report belongs to the signed visit it comes from")
	return None


def _pagina(lead: str) -> dict:
	return {"can_obscure": livelli.puo("clinica.oscura")}


def _per_chi() -> list[dict]:
	"""Whom health data can be for: the users who write the clinical record."""
	utenti = frappe.get_all(
		"User",
		filters={"enabled": 1, "user_type": "System User", "name": ("not in", ("Administrator", "Guest"))},
		fields=["name", "full_name"],
	)
	return [
		{"value": utente.name, "label": utente.full_name or utente.name}
		for utente in utenti
		if livelli.puo("clinica.scrivi", utente.name)
	]


def valida(doc, method=None) -> None:
	"""The clinic's fields on a document, checked on every save."""
	if not doc.is_new() and doc.has_value_changed("record"):
		frappe.throw(_("The file of a document is not replaced: add a new document"))
	if doc.get("visibility") == dossier.DISCIPLINA and not doc.get("discipline"):
		frappe.throw(_("{0} has no discipline: choose the care team").format(doc.practitioner))
	if doc.get("visibility") == dossier.SOLO_IO and not doc.practitioner:
		doc.practitioner = doc.added_by


# ------------------------------------------------------------------ going online


def col_consenso(lead: str) -> bool:
	return bool(
		frappe.db.exists("CRM Consent", {"lead": lead, "consent_type": REFERTI_ONLINE, "status": "Given"})
	)


def _ferma(doc) -> str | None:
	if cint(doc.get("not_online")):
		return _("This document never goes online: give it by hand")
	if cint(doc.get("clinical")) and not col_consenso(doc.lead):
		return _("The patient has not asked for their reports online: give it by hand")
	return None


def _giorni(doc) -> int | None:
	return GIORNI_ONLINE if cint(doc.get("clinical")) else None


# ------------------------------------------------------------------ from a signed visit


def dal_referto(visita) -> str | None:
	"""The report of a signed visit, among the person's documents: the visit's own
	PDF, for the practitioner who signed it, read by whoever reads the visit."""
	if not visita.get("pdf_file") or frappe.db.exists(api.DOCTYPE, {"record": visita.name}):
		return None
	doc = frappe.get_doc(
		{
			"doctype": api.DOCTYPE,
			"lead": visita.lead,
			# a title kept on the document: the centre's language, not whoever signed's
			# («Visit» stayed in English for a practitioner reading in English)
			"title": visita.get("title") or _("Visit", lang=lingue.del_centro()),
			"document_type": REFERTO,
			"document_date": getdate(visita.record_date or visita.signed_on),
			"practitioner": visita.practitioner,
			"visibility": visita.visibility or dossier.TUTTI,
			"discipline": visita.get("discipline"),
			"obscured": cint(visita.get("obscured")),
			"record": visita.name,
			"file": visita.pdf_file,
			"file_hash": visita.get("pdf_hash"),
			"appointment": visita.get("appointment"),
			"added_by": visita.practitioner,
			"added_on": visita.signed_on,
			"clinical": 1,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


# ------------------------------------------------------------------ into the CRM's documents


ESTENSIONE = api.Estensione(
	legge=_legge,
	scrive=_scrive,
	scelte=_scelte,
	fisso=_fisso,
	pagina=_pagina,
	per_chi=_per_chi,
)
REGOLA = consegna.Regola(ferma=_ferma, giorni=_giorni)


def registra() -> None:
	"""The clinic's kinds of document, its fields, and its rules for going online."""
	from crm.clinica import PIANO

	for ordine, chiave in enumerate(TIPI):
		R.registra_tipo(
			R.TipoDocumento(
				chiave,
				clinico=True,
				da_aggiungere=chiave != REFERTO,
				modulo=PIANO,
				capacita="clinica.archivia",
				ordine=11 + ordine,
			)
		)
	api.registra_estensione(ESTENSIONE)
	consegna.registra_regola(REGOLA)
