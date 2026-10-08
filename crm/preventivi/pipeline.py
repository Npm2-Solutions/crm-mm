# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The quotes pipeline: from the quote delivered to accepted or declined.

A quote handed to the person moves their deal - the one it had, else their open one
in the pipeline, else a new one - to "quote delivered", worth the quote. Accepted,
the deal is won; declined, lost, with the reason given. A deal that cannot move
never stops the quote. Which pipeline it is, the manager says in the settings
(`CRM Quote Settings`); with none chosen, quotes move no deal.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, flt

from crm import lingue
from crm.permissions import livelli
from crm.preventivi import rate
from crm.preventivi import rate_regole as RR
from crm.preventivi.api import DOCTYPE, IMPOSTAZIONI

#: The stages, in the centre's language (`crm.lingue`): data the board shows, not
#: strings of the interface. Name, description, then stage, colour, type,
#: probability.
PREVENTIVI = {
	"it": (
		"Preventivi",
		"Dal preventivo consegnato ad accettato o rifiutato.",
		(
			("Preventivo da fare", "gray", "Open", 10),
			("Preventivo consegnato", "blue", "Ongoing", 50),
			("Accettato", "green", "Won", 100),
			("Rifiutato", "red", "Lost", 0),
		),
	),
	"en": (
		"Quotes",
		"From the quote delivered to accepted or declined.",
		(
			("Quote to prepare", "gray", "Open", 10),
			("Quote delivered", "blue", "Ongoing", 50),
			("Accepted", "green", "Won", 100),
			("Declined", "red", "Lost", 0),
		),
	),
}
#: The stage a quote handed over moves its deal to.
CONSEGNATO = 2
ALTRO_MOTIVO = "Other"
CHIUSI = ("Won", "Lost")


def _lingua() -> str:
	lingua = lingue.del_centro()
	return lingua if lingua in PREVENTIVI else "it"


def quale() -> str | None:
	"""The quotes pipeline, if the centre has one."""
	nome = frappe.db.get_single_value(IMPOSTAZIONI, "quotes_pipeline")
	return nome if nome and frappe.db.exists("CRM Pipeline", nome) else None


def crea() -> str:
	"""The quotes pipeline, where the settings do not point at one yet. Idempotent:
	one the centre made by hand under this name is taken as it is."""
	from crm.api.pipeline import _unique_stage_name

	if attuale := quale():
		return attuale
	nome, descrizione, stadi = PREVENTIVI[_lingua()]
	if not frappe.db.exists("CRM Pipeline", nome):
		doc = frappe.new_doc("CRM Pipeline")
		doc.pipeline_name = nome
		doc.description = descrizione
		doc.insert(ignore_permissions=True)
		for posizione, (stadio, colore, tipo, probabilita) in enumerate(stadi, start=1):
			frappe.get_doc(
				{
					"doctype": "CRM Deal Status",
					"deal_status": _unique_stage_name(stadio, doc.name),
					"pipeline": doc.name,
					"position": posizione,
					"color": colore,
					"type": tipo,
					"probability": probabilita,
				}
			).insert(ignore_permissions=True)
		nome = doc.name
	frappe.db.set_single_value(IMPOSTAZIONI, "quotes_pipeline", nome)
	return nome


def _aperte(lead: str, pipeline: str) -> list[frappe._dict]:
	"""The person's deals still open in ``pipeline``, the most recent first."""
	from crm.api.lead import deal_names_of

	nomi = deal_names_of(lead)
	if not nomi:
		return []
	return [
		riga
		for riga in frappe.get_all(
			"CRM Deal",
			filters={"name": ["in", sorted(nomi)], "pipeline": pipeline},
			fields=["name", "status"],
			order_by="modified desc",
		)
		if frappe.get_cached_value("CRM Deal Status", riga.status, "type") not in CHIUSI
	]


def _stadio(pipeline: str, posizione: int | None = None, tipo: str | None = None) -> str | None:
	filtri = {"pipeline": pipeline}
	if posizione:
		filtri["position"] = posizione
	if tipo:
		filtri["type"] = tipo
	return frappe.db.get_value("CRM Deal Status", filtri, "name", order_by="position asc")


def prende_preventivi(deal: str | None) -> bool:
	"""Whether quotes may be this deal's: a deal of the quotes pipeline. A quote never
	moves a deal of another pipeline - the new clients' one follows the person to
	their first visit, and a pipeline the centre made is its own way of working."""
	pipeline = quale()
	return bool(deal and pipeline and frappe.db.get_value("CRM Deal", deal, "pipeline") == pipeline)


def si_puo_spostare(deal: str | None) -> bool:
	"""A quote's own deal goes to "quote delivered" while it is open: a closed deal
	is never opened again by a quote."""
	if not prende_preventivi(deal):
		return False
	stadio = frappe.db.get_value("CRM Deal", deal, "status")
	return frappe.get_cached_value("CRM Deal Status", stadio, "type") not in CHIUSI


def preventivo_consegnato(lead: str, valore: float, deal: str | None = None) -> str | None:
	"""A quote handed to the person: its deal to "quote delivered", worth the quote.
	None where the centre has no quotes pipeline."""
	pipeline = quale()
	stadio = _stadio(pipeline, posizione=CONSEGNATO) if pipeline else None
	if not stadio:
		return None
	if not si_puo_spostare(deal):
		deal = next((riga.name for riga in _aperte(lead, pipeline)), None)
	if deal:
		doc = frappe.get_doc("CRM Deal", deal)
	else:
		persona = frappe.get_cached_doc("CRM Lead", lead)
		doc = frappe.new_doc("CRM Deal")
		doc.lead = lead
		doc.organization = persona.organization
		doc.source = persona.source
		doc.deal_owner = persona.lead_owner
		if persona.contact:
			doc.append("contacts", {"contact": persona.contact, "is_primary": 1})
	doc.status = stadio
	doc.expected_deal_value = valore
	# the server moves it, as for an inquiry: nobody to ask a forecast of
	doc.flags.from_inquiry = True
	doc.save(ignore_permissions=True)
	frappe.db.set_value("CRM Lead", lead, "converted", 1, update_modified=False)
	return doc.name


def preventivo_chiuso(
	deal: str | None,
	accettato: bool,
	motivo: str | None = None,
	note: str | None = None,
	valore: float | None = None,
) -> None:
	"""Accepted, the quote's deal is won and worth what was agreed - the number the
	dashboards add up; declined, lost - with the reason given, or "Other" and the
	words."""
	if not (deal and frappe.db.exists("CRM Deal", deal)):
		return
	doc = frappe.get_doc("CRM Deal", deal)
	stadio = _stadio(doc.pipeline, tipo="Won" if accettato else "Lost")
	if not stadio or doc.status == stadio:
		return
	doc.status = stadio
	if accettato and valore:
		doc.deal_value = valore
		doc.expected_deal_value = valore
	if not accettato:
		doc.lost_reason = motivo if motivo and frappe.db.exists("CRM Lost Reason", motivo) else ALTRO_MOTIVO
		doc.lost_notes = note or _("Quote declined")
	doc.flags.from_inquiry = True
	doc.save(ignore_permissions=True)


def segui(doc, consegnato: bool = False, accettato=None, motivo=None, note=None) -> None:
	"""The quotes pipeline follows the quote; a deal that cannot move never stops it."""
	frappe.db.savepoint("preventivo_deal")
	try:
		if consegnato:
			deal = preventivo_consegnato(doc.lead, flt(doc.total_net), doc.deal)
			if deal and deal != doc.deal:
				doc.db_set("deal", deal, update_modified=False)
		else:
			preventivo_chiuso(doc.deal, bool(accettato), motivo, note, valore=flt(doc.total_net))
	except Exception:
		frappe.db.rollback(save_point="preventivo_deal")
		frappe.log_error(
			title=_("Quotes deal not moved for {0}").format(doc.name),
			reference_doctype=DOCTYPE,
			reference_name=doc.name,
		)


# ---------------------------------------------------------------- the settings page


@frappe.whitelist()
def get_settings() -> dict:
	"""Which pipeline quotes move, and how long a quote holds."""
	livelli.verifica("pipeline.configura")
	return {
		"quotes_pipeline": quale(),
		"valid_days": frappe.db.get_single_value(IMPOSTAZIONI, "valid_days") or None,
		# a quote paid in instalments (crm.preventivi.rate): how they are invoiced
		"instalment_invoicing": rate.modo(),
		"issue_instalment_invoices": 1 if rate.si_emettono() else 0,
	}


@frappe.whitelist(methods=["POST"])
def save_settings(
	quotes_pipeline: str | None = None,
	valid_days: int | None = None,
	instalment_invoicing: str | None = None,
	issue_instalment_invoices: int | str | None = None,
) -> dict:
	livelli.verifica("pipeline.configura")
	if quotes_pipeline and not frappe.db.exists("CRM Pipeline", quotes_pipeline):
		frappe.throw(_("{0} is not a pipeline").format(quotes_pipeline))
	doc = frappe.get_single(IMPOSTAZIONI)
	doc.quotes_pipeline = quotes_pipeline or None
	doc.valid_days = max(int(valid_days or 0), 0) or None
	if instalment_invoicing is not None:
		doc.instalment_invoicing = (
			RR.SOLO_SEGUITE if instalment_invoicing == RR.SOLO_SEGUITE else RR.OGNI_RATA
		)
	if issue_instalment_invoices is not None:
		doc.issue_instalment_invoices = 1 if cint(issue_instalment_invoices) else 0
	doc.save(ignore_permissions=True)
	return get_settings()


@frappe.whitelist(methods=["POST"])
def create_pipeline() -> dict:
	livelli.verifica("pipeline.configura")
	crea()
	return get_settings()
