# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The patient's summary: allergies, medications, conditions, parameters.

"Le risposte che valgono per la scheda (allergie, farmaci, peso) si propongono
alla sintesi del paziente e l'operatore le conferma" (design.md, "Il motore dei
modelli"). A field of a template can say which line of the summary it answers
(the common property ``summary``); when a form or a clinical sheet with such an
answer is signed, the answer is proposed. A practitioner confirms it, or
discards it; they can also write a line by hand. The summary is, for each line,
the last value confirmed - every value stays, with where it came from and who
decided, so the summary has a history.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import frappe
from frappe import _
from frappe.utils import get_fullname, now_datetime

from crm.permissions import livelli

DOCTYPE = "Clinic Summary Value"
PROPOSTO, CONFERMATO, SCARTATO = "Proposed", "Confirmed", "Discarded"


@dataclass(frozen=True)
class Voce:
	chiave: str
	etichetta: str
	unita: str = ""


#: The lines of the summary, in the order the Clinic tab shows them.
VOCI = (
	Voce("allergies", "Allergies"),
	Voce("medications", "Medications"),
	Voce("conditions", "Conditions"),
	Voce("weight", "Weight", "kg"),
	Voce("height", "Height", "cm"),
	Voce("blood_pressure", "Blood pressure", "mmHg"),
	Voce("heart_rate", "Heart rate", "bpm"),
)
_PER_CHIAVE = {voce.chiave: voce for voce in VOCI}


def registra() -> None:
	"""The summary's lines are what a template field may answer."""
	from crm.moduli import modelli
	from crm.moduli import schema as S

	S.registra_proprieta_comune("summary")
	for voce in VOCI:
		modelli.registra_voce_sintesi(voce.chiave, voce.etichetta)


# ------------------------------------------------------------------ proposing


def proponi(doc, schema: dict, risposte: dict, stato: dict) -> list[str]:
	"""The answers of a signed form or sheet that fill a line of the summary,
	proposed to the practitioner. Returns the new proposals."""
	from crm.moduli import pdf
	from crm.moduli import schema as S

	nuove = []
	for campo in S.campi(schema):
		chiave = campo.get("summary")
		if chiave not in _PER_CHIAVE or not stato["visible"].get(campo.get("id")):
			continue
		valore = risposte.get(campo.get("id"))
		if S.vuoto(valore):
			continue
		testo = pdf.risposta_in_parole(campo, valore, stato.get("bands", {}).get(campo.get("id")))
		if campo.get("type") == "table":
			colonne = [c for c in campo.get("columns") or [] if isinstance(c, dict)]
			testo = "; ".join(
				", ".join(str(riga.get(c.get("id"))) for c in colonne if not S.vuoto(riga.get(c.get("id"))))
				for riga in valore
				if isinstance(riga, dict)
			)
		if not testo:
			continue
		proposta = frappe.get_doc(
			{
				"doctype": DOCTYPE,
				"lead": doc.lead,
				"key": chiave,
				"value": testo,
				"raw": json.dumps(valore, ensure_ascii=False, default=str),
				"status": PROPOSTO,
				"source_doctype": doc.doctype,
				"source_name": doc.name,
				"source_title": doc.get("title") or doc.get("kind") or doc.name,
				"proposed_on": now_datetime(),
			}
		)
		proposta.insert(ignore_permissions=True)
		nuove.append(proposta.name)
	return nuove


# ------------------------------------------------------------------ reading and deciding


def _legge() -> bool:
	return livelli.puo("clinica.vedi") or livelli.puo("clinica.scrivi")


def _riga(valore) -> dict:
	voce = _PER_CHIAVE.get(valore.key)
	return {
		"name": valore.name,
		"key": valore.key,
		"label": _(voce.etichetta) if voce else valore.key,
		"unit": voce.unita if voce else "",
		"value": valore.value,
		"status": valore.status,
		"source_doctype": valore.source_doctype,
		"source_name": valore.source_name,
		"source_title": valore.source_title,
		"proposed_on": valore.proposed_on,
		"decided_by": get_fullname(valore.decided_by) if valore.decided_by else None,
		"decided_on": valore.decided_on,
	}


def sintesi(lead: str) -> dict:
	"""For each line, the last value confirmed; and the proposals waiting."""
	valori = frappe.get_all(
		DOCTYPE,
		filters={"lead": lead, "status": ("in", (PROPOSTO, CONFERMATO))},
		fields=[
			"name",
			"key",
			"value",
			"status",
			"source_doctype",
			"source_name",
			"source_title",
			"proposed_on",
			"decided_by",
			"decided_on",
		],
		order_by="decided_on desc, proposed_on desc",
	)
	# what came from an episode the patient had obscured is not there for who must
	# not know of it: the line shows the last value from what they may read
	from crm.clinica import dossier

	nascoste = dossier.fonti_nascoste(
		[(v.source_doctype, v.source_name) for v in valori if v.source_doctype and v.source_name]
	)
	valori = [v for v in valori if (v.source_doctype, v.source_name) not in nascoste]
	confermati: dict[str, dict] = {}
	for valore in valori:
		if valore.status == CONFERMATO and valore.key not in confermati:
			confermati[valore.key] = _riga(valore)
	return {
		"lines": [
			confermati.get(voce.chiave)
			or {"key": voce.chiave, "label": _(voce.etichetta), "unit": voce.unita}
			for voce in VOCI
		],
		"proposals": [_riga(v) for v in sorted(valori, key=lambda v: v.proposed_on) if v.status == PROPOSTO],
	}


def _decide(nome: str):
	livelli.verifica("clinica.scrivi")
	valore = frappe.get_doc(DOCTYPE, nome)
	frappe.has_permission("CRM Lead", "read", doc=valore.lead, throw=True)
	if valore.status != PROPOSTO:
		frappe.throw(_("This value was decided already"))
	return valore


@frappe.whitelist(methods=["POST"])
def confirm_value(name: str, value: str | None = None) -> dict:
	"""The proposal becomes the summary's line, as it is or corrected."""
	valore = _decide(name)
	valore.db_set(
		{
			"status": CONFERMATO,
			"value": (value or "").strip() or valore.value,
			"decided_by": frappe.session.user,
			"decided_on": now_datetime(),
		}
	)
	return sintesi(valore.lead)


@frappe.whitelist(methods=["POST"])
def discard_value(name: str) -> dict:
	"""The proposal does not go to the summary: it stays, discarded, with who and when."""
	valore = _decide(name)
	valore.db_set({"status": SCARTATO, "decided_by": frappe.session.user, "decided_on": now_datetime()})
	return sintesi(valore.lead)


@frappe.whitelist(methods=["POST"])
def set_value(lead: str, key: str, value: str) -> dict:
	"""A line written by hand, by the practitioner: confirmed as it is written."""
	livelli.verifica("clinica.scrivi")
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	if key not in _PER_CHIAVE:
		frappe.throw(_("There is no such line in the summary"))
	adesso = now_datetime()
	frappe.get_doc(
		{
			"doctype": DOCTYPE,
			"lead": lead,
			"key": key,
			"value": (value or "").strip(),
			"status": CONFERMATO,
			"source_title": _("By hand"),
			"proposed_on": adesso,
			"decided_by": frappe.session.user,
			"decided_on": adesso,
		}
	).insert(ignore_permissions=True)
	return sintesi(lead)


@frappe.whitelist()
def get_summary(lead: str) -> dict:
	if not _legge():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	return {**sintesi(lead), "can_decide": livelli.puo("clinica.scrivi")}


# ------------------------------------------------------------------ who sees them


def has_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	"""The summary is the care team's, like the record."""
	user = user or frappe.session.user
	if not (livelli.puo("clinica.vedi", user) or livelli.puo("clinica.scrivi", user)):
		return False
	return bool(frappe.has_permission("CRM Lead", "read", doc=doc.get("lead"), user=user))


def get_permission_query_conditions(user: str | None = None) -> str:
	"""The care team's, for the people they see."""
	user = user or frappe.session.user
	if not (livelli.puo("clinica.vedi", user) or livelli.puo("clinica.scrivi", user)):
		return "1=0"
	from crm.permissions import org_hierarchy

	visibili = org_hierarchy.visible_leads(user)
	if visibili is None:
		return ""
	valori = frappe.qb.DocType(DOCTYPE)
	return valori.lead.isin(visibili).get_sql(with_namespace=True, quote_char="`", secondary_quote_char="'")
