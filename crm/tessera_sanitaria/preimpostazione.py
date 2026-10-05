# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A medical centre's invoicing, set up by answering three questions.

With the clinic on, DottorCloud is a medical centre's software and its invoicing is
a medical centre's: whoever issues reports to the Sistema TS, the services are
healthcare services, exempt under art. 10, with the expense type of whoever issues.
What cannot be known is asked once, in words: who issues the invoices, under which
tax regime, and - for a professional invoicing in their own name - which
profession. The rest follows from the answers and from the register, and stays
editable on the company.

Nothing here invents a fiscal fact. The cards made from the agenda's services are
healthcare services exempt as a health profession makes them, and each one says it
waits for the accountant, as every card does until somebody ticks it; the engine
still refuses the exemption when whoever performs is not a health professional.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, getdate

from crm.invoicing import registro, scelte
from crm.invoicing.engine import diciture, voci
from crm.permissions.livelli import richiede
from crm.tessera_sanitaria.engine.codici import SoggettoInviante, tipi_spesa_ammessi
from crm.tessera_sanitaria.qualifica import MANCANO_I_CODICI

AZIENDA = "CRM Invoicing Company"
SCHEDA = "CRM Billable Service"
QUALIFICA = "CRM Professional Qualification"

#: Who issues a medical centre's invoices, in the order a centre meets them.
CHI_EMETTE = (
	SoggettoInviante.STRUTTURA_AUTORIZZATA,
	SoggettoInviante.MEDICO_ODONTOIATRA,
	SoggettoInviante.PROFESSIONISTA_SANITARIO,
	SoggettoInviante.STRUTTURA_ACCREDITATA,
)

#: A facility is a company or an association: it invoices under the ordinary
#: regime, has no fund of its own and suffers no withholding, and reports with the
#: codes the Region gave it.
STRUTTURE = frozenset({SoggettoInviante.STRUTTURA_AUTORIZZATA, SoggettoInviante.STRUTTURA_ACCREDITATA})

#: The regimes a professional invoicing in their own name may be under.
REGIMI = ("RF01", "RF19", "RF02")

#: What a professional's qualification gives the company that issues in their name.
CAMPI_DELLA_QUALIFICA = (
	"fund_type",
	"fund_rate",
	"fund_mandatory",
	"fund_subject_to_withholding",
	"withholding_rate",
	"withholding_type",
	"payment_reason",
)


def _scelta(famiglia: str, valore: str) -> dict:
	voce = next(v for v in voci.tutte(famiglia) if v.valore == valore)
	return {
		"value": voce.valore,
		"label": _(voce.etichetta),
		"description": _(voce.spiegazione) if voce.spiegazione else "",
	}


def _azienda(company: str | None) -> str | None:
	"""The company asked for, else the default one, else the only one."""
	if company:
		return company
	predefinita = frappe.db.get_single_value("CRM Invoicing Settings", "default_company")
	if predefinita:
		return predefinita
	return frappe.db.get_value(AZIENDA, {"is_default": 1, "enabled": 1}, "name") or frappe.db.get_value(
		AZIENDA, {"enabled": 1}, "name"
	)


def tipo_di_spesa(categoria: str | None) -> str:
	"""The expense type a card starts with, for whoever issues: the only one a
	health professional has, else the visits and specialist services."""
	ammessi = tipi_spesa_ammessi(categoria)
	if len(ammessi) == 1:
		return next(iter(ammessi))
	return "SR" if "SR" in ammessi else ""


def _professioni() -> dict[str, list[dict]]:
	"""The professions a professional invoicing in their own name can have, by who
	issues, by their names and with the fund each one carries."""
	righe = frappe.get_all(
		QUALIFICA,
		filters={
			"enabled": 1,
			"category": "sanitaria",
			"sender_category": [
				"in",
				[SoggettoInviante.MEDICO_ODONTOIATRA, SoggettoInviante.PROFESSIONISTA_SANITARIO],
			],
		},
		fields=["name", "qualification_name", "sender_category", "fund_type"],
		order_by="qualification_name asc",
	)
	professioni: dict[str, list[dict]] = {}
	for riga in righe:
		cassa = voci.etichetta("cassa", riga.fund_type) if riga.fund_type else ""
		professioni.setdefault(riga.sender_category, []).append(
			{
				"value": riga.name,
				"label": riga.qualification_name,
				"description": _(cassa) if cassa else "",
			}
		)
	return professioni


def _servizi_senza_scheda() -> list[dict]:
	"""The agenda's services nobody can invoice yet: no card points at them."""
	collegati = set(frappe.get_all(SCHEDA, filters={"crm_service": ["is", "set"]}, pluck="crm_service"))
	return [
		servizio
		for servizio in frappe.get_all(
			"CRM Service",
			filters={"enabled": 1},
			fields=["name", "service_name", "default_price"],
			order_by="service_name asc",
		)
		if servizio.name not in collegati
	]


@frappe.whitelist()
def get_setup(company: str | None = None) -> dict:
	"""The three questions, their choices in words, and what the company answers now."""
	frappe.has_permission(AZIENDA, "read", throw=True)
	azienda = _azienda(company)
	valori = (
		frappe.db.get_value(
			AZIENDA,
			azienda,
			["company_name", "sender_category", "tax_regime", "region_code", "asl_code", "ssa_code"],
			as_dict=True,
		)
		if azienda
		else None
	) or {}
	categoria = valori.get("sender_category")
	tipo = tipo_di_spesa(categoria)
	if categoria not in STRUTTURE:
		valori["profession"] = _professione_di(azienda, categoria)
	return {
		"company": azienda,
		"profile": scelte.profilo(),
		"values": valori,
		"done": categoria in CHI_EMETTE,
		"issuers": [_scelta("soggetto_inviante", valore) for valore in CHI_EMETTE],
		"facilities": sorted(STRUTTURE),
		"regimes": [_scelta("regime_fiscale", valore) for valore in REGIMI],
		"professions": _professioni(),
		"expense_type": _scelta("tipo_spesa", tipo) if tipo else None,
		"card_defaults": scheda_predefinita(categoria),
		"services_without_card": len(_servizi_senza_scheda()),
	}


def scheda_predefinita(categoria: str | None) -> dict:
	"""Where a medical centre's new card starts: a healthcare service, exempt with
	the annotation its invoices carry, the expense type of whoever issues."""
	return {
		"enabled": 1,
		"subject_to_stamp_duty": 1,
		"is_healthcare": 1,
		"vat_exempt": 1,
		"vat_rate": 0,
		"exemption_reference": diciture.esenzione(getdate()),
		"ts_expense_type": tipo_di_spesa(categoria),
	}


def _professione_di(azienda: str | None, categoria: str | None) -> str:
	"""The profession of whoever invoices in their own name, as the practice already
	says it: the qualification of its only provider, when it fits who issues."""
	erogatori = {
		riga.qualification
		for riga in frappe.get_all(
			"CRM Service Provider", filters={"enabled": 1}, fields=["qualification", "company"]
		)
		# a provider with no company issues for every one
		if not riga.company or riga.company == azienda
	}
	if len(erogatori) != 1 or not categoria:
		return ""
	qualifica = next(iter(erogatori))
	return qualifica if frappe.db.get_value(QUALIFICA, qualifica, "sender_category") == categoria else ""


def _codice(valore: str | None, lunghezza: int) -> str:
	codice = (valore or "").strip().upper()
	if codice and (len(codice) > lunghezza or not codice.isalnum()):
		frappe.throw(_("{0} is not a valid code: at most {1} letters or digits").format(codice, lunghezza))
	return codice


@frappe.whitelist(methods=["POST"])
@richiede("fatture.configura")
def apply_setup(
	company: str,
	issuer: str,
	regime: str = "RF01",
	profession: str = "",
	region_code: str = "",
	asl_code: str = "",
	ssa_code: str = "",
) -> dict:
	"""Write the answers on the company, and what follows from them.

	A facility: the ordinary regime, no fund, no withholding, the Region's codes. A
	professional in their own name: their regime, and the fund and withholding of
	their profession as the register has them; and, in a practice with nobody yet
	to perform its services, the professional themselves.
	"""
	if issuer not in CHI_EMETTE:
		frappe.throw(_("Choose who issues the invoices"))
	if regime not in REGIMI:
		frappe.throw(_("Choose the tax regime"))
	struttura = issuer in STRUTTURE
	if struttura and regime != "RF01":
		frappe.throw(_("A healthcare facility invoices under the ordinary regime"))

	doc = frappe.get_doc(AZIENDA, company)
	doc.check_permission("write")
	doc.sender_category = issuer
	doc.tax_regime = regime

	qualifica = None
	if struttura:
		doc.region_code = _codice(region_code, 3) or doc.region_code
		doc.asl_code = _codice(asl_code, 3) or doc.asl_code
		doc.ssa_code = _codice(ssa_code, 6) or doc.ssa_code
		if not (doc.region_code and doc.asl_code and doc.ssa_code):
			frappe.throw(MANCANO_I_CODICI())
		doc.fund_type = ""
		doc.fund_rate = 0
		doc.fund_mandatory = 0
		doc.apply_withholding_by_default = 0
	else:
		qualifica = frappe.db.get_value(
			QUALIFICA,
			{"name": profession, "enabled": 1, "sender_category": issuer},
			["name", "qualification_name", *CAMPI_DELLA_QUALIFICA],
			as_dict=True,
		)
		if not qualifica:
			frappe.throw(_("Choose the profession of whoever invoices in their own name"))
		for campo in CAMPI_DELLA_QUALIFICA:
			doc.set(campo, qualifica.get(campo))
		# a professional reports with their codice fiscale, never with a facility's codes
		doc.region_code = doc.asl_code = doc.ssa_code = ""
		# a patient is never a withholding agent: the withholding is the exception,
		# asked on the invoice to a company
		doc.apply_withholding_by_default = 0
	doc.save()

	if qualifica and not frappe.db.count("CRM Service Provider", {"enabled": 1}):
		frappe.get_doc(
			{
				"doctype": "CRM Service Provider",
				"provider_name": doc.company_name,
				"qualification": qualifica.name,
				"company": doc.name,
				"enabled": 1,
			}
		).insert()
	return get_setup(doc.name)


def _erogatore(servizio: str) -> str | None:
	"""Whoever performs a service, when the agenda says it is one person only."""
	utenti = set(
		frappe.get_all(
			"CRM Service Staff", filters={"parent": servizio, "parenttype": "CRM Service"}, pluck="user"
		)
	)
	utenti.discard(None)
	if len(utenti) != 1:
		return None
	erogatori = frappe.get_all(
		"CRM Service Provider", filters={"user": next(iter(utenti)), "enabled": 1}, pluck="name"
	)
	return erogatori[0] if len(erogatori) == 1 else None


@frappe.whitelist(methods=["POST"])
@richiede("fatture.configura")
def cards_from_services(company: str | None = None) -> dict:
	"""A card for every service of the agenda that has none: a healthcare service,
	exempt, with the expense type of whoever issues and the agenda's price - one
	only somebody who is not exempt performs (the osteopath, the kinesiologist)
	taxed at their rate (`registro.scheda_tassata`). A card of the same name that
	points nowhere is tied to its service, not doubled."""
	frappe.has_permission(SCHEDA, "create", throw=True)
	azienda = _azienda(company)
	categoria = frappe.db.get_value(AZIENDA, azienda, "sender_category") if azienda else None
	predefinita = scheda_predefinita(categoria)
	creati, collegati = [], []
	for servizio in _servizi_senza_scheda():
		omonima = frappe.db.get_value(SCHEDA, servizio.service_name, ["name", "crm_service"], as_dict=True)
		if omonima:
			if not omonima.crm_service:
				frappe.db.set_value(SCHEDA, omonima.name, "crm_service", servizio.name)
				collegati.append(omonima.name)
			continue
		scheda = frappe.get_doc(
			{
				**predefinita,
				"doctype": SCHEDA,
				"service_name": servizio.service_name,
				"fiscal_description": servizio.service_name,
				"crm_service": servizio.name,
				"default_rate": flt(servizio.default_price),
				"default_provider": _erogatore(servizio.name),
				**(registro.scheda_tassata(registro.erogatori_del_servizio(servizio.name)) or {}),
			}
		)
		scheda.insert()
		creati.append(scheda.name)
	return {"created": creati, "linked": collegati}
