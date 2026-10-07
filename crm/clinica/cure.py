# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The teeth, and what dentistry adds to the CRM's quotes (docs/verticali/clinica,
phase 3: "piani di cura (odontoiatria)"); the rules without a site are `cure_regole`.

- **The chart** (`Clinic Dental Chart`, one per person): what each tooth is now, one
  row per condition. Written by the dentists (`cure.scrivi` and a dentist's
  qualification), read like the record: who started it, and the others with the
  dossier. Its changes stay in its history; every opening goes in the access log.
- **A care plan is a quote** (`crm.preventivi`) a dentist writes: the clinic adds a
  tooth and its surfaces to its rows (`crm/clinica/custom`), checks them, and reads
  them in words - "Tooth 36 · OM" - on the page, the PDF and the area. Only a
  dentist puts a tooth on a quote. What a health professional writes is health
  data: the quote carries the mark, and is read like the record.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import get_fullname, now_datetime, nowdate

from crm.clinica import cure_regole as R
from crm.clinica import dossier
from crm.permissions import livelli

CARTELLA = "Clinic Dental Chart"


# ------------------------------------------------------------------ who


def dentista(user: str | None = None) -> bool:
	"""Whether ``user`` writes charts and teeth on quotes: the capability, and a
	dentist's qualification on their provider record."""
	user = user or frappe.session.user
	return livelli.puo("cure.scrivi", user) and R.scrive(dossier.disciplina_di(user))


def _sql(condizione) -> str:
	return condizione.get_sql(with_namespace=True, quote_char="`", secondary_quote_char="'")


def puo_leggere_cartella(doc, user: str | None = None) -> bool:
	"""Who started it; the others like the record, with the dossier."""
	user = user or frappe.session.user
	return doc.get("practitioner") == user or dossier.legge_le_altre(doc, user)


def has_chart_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	user = user or frappe.session.user
	ptype = ptype or "read"
	if ptype == "create":
		return dentista(user)
	if ptype == "write":
		return dentista(user) and puo_leggere_cartella(doc, user)
	if ptype in ("delete", "submit", "cancel", "amend"):
		return False
	return puo_leggere_cartella(doc, user)


def get_chart_permission_query_conditions(user: str | None = None) -> str:
	user = user or frappe.session.user
	cartella = frappe.qb.DocType(CARTELLA)
	condizione = cartella.practitioner == user
	condivisa = dossier.condizione_condivisa(cartella, user)
	if condivisa is not None:
		condizione = condizione | condivisa
	return _sql(condizione)


def _legge() -> bool:
	return livelli.puo("clinica.vedi") or livelli.puo("cure.scrivi")


def _della_persona(lead: str) -> None:
	if not _legge():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)


def _problemi(problemi: list) -> None:
	if problemi:
		frappe.throw("<br>".join(p.testo(_) for p in problemi))


# ------------------------------------------------------------------ reading


def _cartella(doc) -> dict:
	return {
		"name": doc.name,
		"dentition": doc.dentition or R.PERMANENTE,
		"teeth": [
			{
				"tooth": riga.tooth,
				"condition": riga.condition,
				"surfaces": riga.surfaces or "",
				"note": riga.note or "",
				"noted_on": str(riga.noted_on) if riga.noted_on else None,
				"noted_by_name": get_fullname(riga.noted_by) if riga.noted_by else None,
			}
			for riga in doc.teeth
		],
		"notes": doc.notes,
		"updated_on": str(doc.updated_on) if doc.updated_on else None,
		"updated_by_name": get_fullname(doc.updated_by) if doc.updated_by else None,
		"can_write": dentista() and puo_leggere_cartella(doc),
	}


@frappe.whitelist()
def get_dental(lead: str) -> dict:
	"""The person's chart the session reads, for the Clinic tab. The care plans are
	quotes, on the Quotes tab."""
	_della_persona(lead)
	cartella = None
	nome = frappe.db.get_value(CARTELLA, {"lead": lead}, "name")
	if nome:
		doc = frappe.get_doc(CARTELLA, nome)
		if puo_leggere_cartella(doc):
			doc.add_viewed()
			cartella = _cartella(doc)
		elif livelli.puo("clinica.vedi"):
			# a colleague's, without the dossier: said, not shown
			cartella = {"hidden": True, "practitioner_name": get_fullname(doc.practitioner)}
	return {"chart": cartella, "is_dentist": dentista()}


# ------------------------------------------------------------------ the chart


@frappe.whitelist(methods=["POST"])
def save_chart(lead: str, teeth: str | list, dentition: str | None = None, notes: str | None = None) -> dict:
	"""The chart as the dentist left it: a row that did not change keeps who noted it
	and when."""
	_della_persona(lead)
	if not dentista():
		frappe.throw(_("The chart is written by a dentist"), frappe.PermissionError)
	righe = frappe.parse_json(teeth) if isinstance(teeth, str) else (teeth or [])
	_problemi(R.valida_stato(righe))
	nome = frappe.db.get_value(CARTELLA, {"lead": lead}, "name")
	utente = frappe.session.user
	if nome:
		doc = frappe.get_doc(CARTELLA, nome)
		if not puo_leggere_cartella(doc):
			frappe.throw(
				_("The chart was started by a colleague: with the dossier consent you read it and write it"),
				frappe.PermissionError,
			)
	else:
		doc = frappe.new_doc(CARTELLA)
		doc.lead = lead
		doc.practitioner = utente
		doc.discipline = dossier.disciplina_di(utente)
	prima = {(riga.tooth, riga.condition): riga for riga in doc.teeth}
	doc.set("teeth", [])
	for riga in R.pulisci_stato(righe):
		vecchia = prima.get((riga["tooth"], riga["condition"]))
		uguale = (
			vecchia is not None
			and (vecchia.surfaces or "") == riga["surfaces"]
			and (vecchia.note or "") == riga["note"]
		)
		doc.append(
			"teeth",
			{
				**riga,
				"noted_on": vecchia.noted_on if uguale else nowdate(),
				"noted_by": vecchia.noted_by if uguale else utente,
			},
		)
	if dentition in R.DENTIZIONI:
		doc.dentition = dentition
	if notes is not None:
		doc.notes = notes.strip() or None
	doc.updated_on = now_datetime()
	doc.updated_by = utente
	if doc.is_new():
		doc.insert()
	else:
		doc.save()
	return _cartella(doc)


# ------------------------------------------------------------------ on the CRM's quotes


def _pulisci_voce(preventivo, voce) -> None:
	"""A tooth kept as its number, its surfaces in their order; none without a tooth."""
	dente = voce.get("tooth")
	if dente and R.e_dente(dente):
		voce.tooth = str(int(dente))
	voce.surfaces = (R.superfici(voce.get("surfaces")) or None) if voce.get("tooth") else None


def _legge_voce(voce) -> dict:
	return {"tooth": voce.get("tooth"), "surfaces": voce.get("surfaces")}


def _dettaglio(voce) -> str | None:
	if not voce.get("tooth"):
		return None
	lati = f" {voce.surfaces}" if voce.get("surfaces") else ""
	return _("Tooth {0}").format(voce.tooth) + lati


def _valida(voci: list[dict]) -> list:
	problemi = R.valida_denti(voci)
	if any(voce.get("tooth") for voce in voci) and not dentista():
		problemi.append(R.Problema("A tooth goes on a quote written by a dentist"))
	return problemi


def _offre() -> dict:
	# the editor offers the tooth and its surfaces to a dentist
	return {"teeth": dentista()}


def registra() -> None:
	"""The tooth and its surfaces on the CRM's quotes."""
	from crm.preventivi import api as preventivi

	preventivi.registra_estensione(
		preventivi.Estensione(
			campi_voce=("tooth", "surfaces"),
			pulisci_voce=_pulisci_voce,
			legge_voce=_legge_voce,
			dettaglio=_dettaglio,
			valida=_valida,
			offre=_offre,
		)
	)
