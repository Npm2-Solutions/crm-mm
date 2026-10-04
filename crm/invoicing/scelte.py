# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The choices invoicing's screens offer, in words, for the profile that is on.

Every select of invoicing's documents that holds a code speaks one vocabulary of
`crm.invoicing.engine.voci`. The screens draw those documents from the DocTypes'
own layouts (`crm.api.doc.get_fields` for the settings, the invoice form): this is
where their options stop being codes. Each one gets its name in the reader's
language and a line on when it applies, and only the ones the practice meets are
offered.

- **The profile** is the vertical's (`crm.verticali`, `Verticale.fatturazione`):
  with the clinic on, `sanitario`, and nothing else is offered.
- **A rule** can narrow a list further, by the document being edited. The expense
  types an issuer may use follow its category, so a physiotherapist invoicing in
  their own name is offered one. A module registers its rules (`registra_regola`),
  the way the Sistema TS does.
- **The stored values do not change**: still the codes the SdI and the Sistema TS
  read. A value stored before stays offered in its own field, whatever the profile.
"""

from __future__ import annotations

from collections.abc import Callable

import frappe
from frappe import _

from crm.invoicing.engine import voci

#: Which vocabulary each code select of invoicing's documents speaks.
CAMPI: dict[tuple[str, str], str] = {
	("CRM Invoicing Company", "tax_regime"): "regime_fiscale",
	("CRM Invoicing Company", "sole_shareholder"): "socio_unico",
	("CRM Invoicing Company", "liquidation_state"): "stato_liquidazione",
	("CRM Invoicing Company", "fund_type"): "cassa",
	("CRM Invoicing Company", "withholding_type"): "tipo_ritenuta",
	("CRM Invoicing Company", "payment_reason"): "causale_pagamento",
	("CRM Invoicing Company", "stamp_duty_mode"): "modalita_bollo",
	("CRM Invoicing Company", "number_format"): "formato_numero",
	("CRM Invoicing Company", "document_mode"): "modalita_documento",
	("CRM Invoicing Company", "conservation_local"): "conservazione_locale",
	("CRM Invoicing Company", "conservation_service"): "conservazione_sdi",
	("CRM Invoicing Company", "sdi_mode"): "canale_sdi",
	("CRM Invoicing Company", "sdi_flow"): "flusso_sdi",
	("CRM Invoicing Company", "provider_environment"): "ambiente",
	("CRM Invoicing Company", "sender_category"): "soggetto_inviante",
	("CRM Invoicing Company", "ts_mode"): "modalita_invio_ts",
	("CRM Invoicing Company", "ts_delegation_status"): "stato_delega",
	("CRM Billable Service", "vat_nature"): "natura",
	("CRM Billable Service", "ts_expense_type"): "tipo_spesa",
	("CRM Billable Service", "ts_expense_flag"): "flag_tipo_spesa",
	("CRM Professional Qualification", "category"): "categoria_qualifica",
	("CRM Professional Qualification", "sdi_rule"): "regola_sdi",
	("CRM Professional Qualification", "sender_category"): "soggetto_inviante",
	("CRM Professional Qualification", "fund_type"): "cassa",
	("CRM Professional Qualification", "withholding_type"): "tipo_ritenuta",
	("CRM Professional Qualification", "payment_reason"): "causale_pagamento",
	("CRM Invoice", "document_type"): "tipo_documento",
	("CRM Invoice", "recipient_type"): "tipo_destinatario",
	("CRM Invoice", "fund_type"): "cassa",
	("CRM Invoice", "withholding_type"): "tipo_ritenuta",
	("CRM Invoice", "payment_reason"): "causale_pagamento",
	("CRM Invoice", "stamp_duty_mode"): "modalita_bollo",
	("CRM Invoice", "payment_method"): "modalita_pagamento",
	("CRM Invoice", "payment_terms"): "condizioni_pagamento",
	("CRM Invoice", "ts_operation"): "operazione_ts",
	("CRM Invoice", "channel"): "canale_documento",
	("CRM Invoice", "payment_traced"): "pagamento_tracciato",
	("CRM Invoice Item", "vat_nature"): "natura",
	("CRM Invoice Item", "ts_expense_type"): "tipo_spesa",
	("CRM Invoice Item", "ts_expense_flag"): "flag_tipo_spesa",
	("CRM Invoice Payment", "payment_method"): "modalita_pagamento",
}

#: Typed as a code, offered as a list: the reason of a withholding is a closed list,
#: and the field that holds it is a two-letter text the DocType keeps as it is; the
#: number's format is a template a centre would get wrong, offered as examples.
COME_ELENCO = {"payment_reason", "number_format"}

#: A country kept as its two letters (the SdI's IdPaese), chosen by its name in the
#: reader's language, as the billing details' is: «IT» is no word for a centre.
PAESI = {("CRM Invoicing Company", "country")}

#: What Babel names that is no country of ISO 3166-1: groupings, the codes only
#: reserved (Ascension, the Canaries...), the test ones. The browser's list leaves
#: out the same (`frontend/src/utils/paesi.js`); Kosovo («XK») stays.
NON_PAESI = frozenset({"AC", "CP", "CQ", "DG", "EA", "EU", "EZ", "IC", "QO", "TA", "UN", "XA", "XB", "ZZ"})

#: In the healthcare profile a practice picks a qualification among the health
#: professions: a lawyer's, an engineer's or a developer's are not a medical
#: centre's. One already given stays, as any stored value does.
FILTRI_SANITARI: dict[tuple[str, str], dict] = {
	("CRM Service Provider", "qualification"): {"category": "sanitaria"},
}

#: family -> what narrows it, given the document being edited (a dict, possibly a
#: new one): the admitted values, or None for no narrowing.
_regole: dict[str, Callable[[dict], set[str] | frozenset[str] | None]] = {}


def registra_regola(famiglia: str, funzione: Callable[[dict], set[str] | frozenset[str] | None]) -> None:
	"""A module narrows a family by the document being edited (the Sistema TS: the
	expense types the issuer's category admits)."""
	_regole[famiglia] = funzione


def profilo() -> str:
	"""The profile of the trade that is on: the vertical's, or the general one."""
	from crm import verticali

	verticale = verticali.attiva()
	return (verticale.fatturazione if verticale else None) or voci.GENERALE


def famiglia_di(doctype: str, fieldname: str) -> str | None:
	return CAMPI.get((doctype, fieldname))


def opzioni(
	doctype: str,
	fieldname: str,
	attuale: str | list[str] | None = None,
	doc: dict | None = None,
	*,
	vuota: bool = False,
) -> list[dict]:
	"""A code select's options in words: value, name, and when it applies. The
	values already stored (one, or a table column's) are always among them."""
	famiglia = famiglia_di(doctype, fieldname)
	if not famiglia:
		return []
	regola = _regole.get(famiglia)
	ammessi = regola(doc or {}) if regola else None
	scelte = [
		{
			"value": voce.valore,
			"label": _(voce.etichetta),
			"description": _(voce.spiegazione) if voce.spiegazione else "",
		}
		for voce in voci.voci(famiglia, profilo(), attuale, ammessi)
	]
	if vuota:
		# a dash, not a blank row: an empty line in a list of names reads as broken
		scelte.insert(0, {"value": "", "label": "—", "description": ""})
	return scelte


def adatta_campi(doctype: str, campi: list) -> list:
	"""The fields of one of invoicing's DocTypes as a screen draws them, with every
	code select offering its choices in words. Others' DocTypes pass untouched."""
	if not any(chiave[0] == doctype for chiave in (*CAMPI, *FILTRI_SANITARI)):
		return campi
	sanitario = profilo() == voci.SANITARIO
	adattati = []
	for campo in campi:
		if (doctype, campo.get("fieldname")) in PAESI:
			nuovo = campo.as_dict() if hasattr(campo, "as_dict") else dict(campo)
			nuovo["fieldtype"] = "Select"
			nuovo["options"] = paesi()
			adattati.append(nuovo)
			continue
		filtro = FILTRI_SANITARI.get((doctype, campo.get("fieldname"))) if sanitario else None
		if filtro:
			adattati.append(_con_filtro(campo, filtro))
			continue
		famiglia = famiglia_di(doctype, campo.fieldname) if campo.get("fieldname") else None
		if not famiglia or not voci.tutte(famiglia):
			adattati.append(campo)
			continue
		nuovo = campo.as_dict() if hasattr(campo, "as_dict") else dict(campo)
		valori = (nuovo.get("options") or "").split("\n") if isinstance(nuovo.get("options"), str) else []
		# nothing to leave empty where the field must have a value, or starts with one
		vuota = not nuovo.get("reqd") and not nuovo.get("default")
		scelte = opzioni(doctype, campo.fieldname, nuovo.get("default"), vuota=vuota)
		if nuovo.get("fieldtype") == "Select":
			# every value the DocType admits stays possible: a profile hides, never forbids
			ammesse = {v for v in valori if v}
			scelte = [s for s in scelte if not s["value"] or s["value"] in ammesse]
		elif campo.fieldname in COME_ELENCO:
			nuovo["fieldtype"] = "Select"
		else:
			adattati.append(campo)
			continue
		nuovo["options"] = scelte
		adattati.append(nuovo)
	return adattati


def paesi(lingua: str | None = None) -> list[dict]:
	"""Every country by its name in the reader's language, kept as its two letters,
	in the order of their names. The names are Babel's, which the framework ships."""
	import unicodedata

	from babel import Locale

	try:
		nomi = Locale.parse((lingua or frappe.local.lang or "it").replace("-", "_")).territories
	except Exception:
		nomi = Locale("it").territories
	scelte = [
		{"value": codice, "label": nome}
		for codice, nome in nomi.items()
		if len(codice) == 2 and codice.isalpha() and codice not in NON_PAESI
	]
	return sorted(scelte, key=lambda scelta: unicodedata.normalize("NFKD", scelta["label"]).casefold())


def _con_filtro(campo, filtro: dict) -> dict:
	"""A link field that searches only among the records the filter admits."""
	nuovo = campo.as_dict() if hasattr(campo, "as_dict") else dict(campo)
	esistente = frappe.parse_json(nuovo.get("link_filters") or "{}")
	nuovo["link_filters"] = frappe.as_json({**(esistente if isinstance(esistente, dict) else {}), **filtro})
	return nuovo


def _scelte(doctype: str, documento: dict, righe: list | None = None) -> dict:
	"""The code selects of one DocType, for the document being edited: its own
	values, or every row's when the DocType is one of its tables."""
	meta = frappe.get_meta(doctype)
	scelte = {}
	for (dt, fieldname), _famiglia in CAMPI.items():
		campo = meta.get_field(fieldname) if dt == doctype else None
		if not campo or campo.fieldtype != "Select":
			continue
		attuale = (
			documento.get(fieldname) if righe is None else [(riga or {}).get(fieldname) for riga in righe]
		)
		scelte[fieldname] = opzioni(
			doctype, fieldname, attuale, documento, vuota=not campo.reqd and not campo.default
		)
	return scelte


@frappe.whitelist()
def get_options(doctype: str, doc: str | dict | None = None) -> dict:
	"""A form's code selects, their choices in words for the profile on and the
	document being edited: {"fields": {fieldname: [{value, label, description}]},
	"tables": {table fieldname: {fieldname: [...]}}}. What the Desk's form of an
	invoice offers, with the SPA's same words."""
	frappe.has_permission(doctype, "read", throw=True)
	documento = frappe.parse_json(doc) if isinstance(doc, str) else (doc or {})
	tabelle = {
		campo.fieldname: _scelte(campo.options, documento, documento.get(campo.fieldname) or [])
		for campo in frappe.get_meta(doctype).get_table_fields()
	}
	return {
		"fields": _scelte(doctype, documento),
		"tables": {nome: scelte for nome, scelte in tabelle.items() if scelte},
	}


@frappe.whitelist()
def get_vocabulary() -> dict:
	"""The names of every code, by family, in the reader's language: what a list row
	says instead of a code. And the qualifications by their names."""
	frappe.has_permission("CRM Invoicing Company", "read", throw=True)
	nomi = {
		famiglia: {voce.valore: _(voce.etichetta) for voce in voci.tutte(famiglia)}
		for famiglia in voci.famiglie()
	}
	nomi["qualifica"] = {
		riga.name: riga.qualification_name
		for riga in frappe.get_all("CRM Professional Qualification", fields=["name", "qualification_name"])
	}
	return {"names": nomi, "profile": profilo()}
