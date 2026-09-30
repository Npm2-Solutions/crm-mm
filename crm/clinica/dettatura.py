# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The visit dictated: the practitioner's words into the fields of the specialty's
sheet (design.md, "L'assistente", point 3).

- **The words are the practitioner's**: typed, pasted or dictated with the
  device's own dictation. Nothing is recorded here, and the words are not kept:
  the register keeps their fingerprint, the proposal and what was kept of it.
- **Only what the words say**: the assistant proposes answers for the fields they
  speak of, in the field's own terms - an option of a choice, a number in its
  unit - and the engine cleans them (`schema.pulisci`): what does not fit is
  dropped, never forced in.
- **Nothing is written by itself.** The practitioner ticks what to keep.
  Medicines, allergies and doses, where scribes go wrong most, are never ticked
  for them: each is confirmed one by one.
- **Nothing about who the patient is** goes with the words.
"""

from __future__ import annotations

import json
import re

import frappe
from frappe import _

from crm.assistente import modello, regole
from crm.clinica import ASSISTENTE, DETTATURA, cartella
from crm.moduli import consensi

#: What the sheet asks and the words can answer: not a text to read, a
#: calculation, a signature or a file.
RISPONDIBILI = ("text", "number", "choice", "yesno", "date", "scale", "sides")
#: The summary's lines that are confirmed one by one.
UNO_A_UNO = ("allergies", "medications")
_DELICATO = re.compile(r"farmac|allerg|\bdos[ei]\b|terapi|medic|drug|\bdose|posolog", re.I)

ISTRUZIONI = """{scopo}
You fill the fields of a clinical sheet from the practitioner's own words about a
visit. Fill only the fields the words speak of, with what they say: no diagnosis,
value, medicine or dose the words do not contain. A choice takes one of its
options, written exactly as listed; a yes/no takes true or false; a number is a
number in the field's unit; a date is YYYY-MM-DD. Leave out every field the words
do not mention.

Answer with one JSON object and nothing else: {{"answers": {{"field_id": value}}}}

The fields:
{campi}"""


def delicato(campo: dict) -> bool:
	"""Medicines, allergies, doses: confirmed one by one."""
	return campo.get("summary") in UNO_A_UNO or bool(_DELICATO.search(campo.get("label") or ""))


def _campi(schema: dict) -> list[dict]:
	from crm.moduli import schema as S

	return [c for c in S.campi(schema) if c.get("type") in RISPONDIBILI and c.get("id")]


def descrivi_campi(campi: list[dict]) -> str:
	righe = []
	for campo in campi:
		riga = f"- {campo['id']} ({campo['type']}): {campo.get('label') or campo['id']}"
		opzioni = [
			o.get("label") for o in campo.get("options") or [] if isinstance(o, dict) and o.get("label")
		]
		if opzioni:
			riga += f" - options: {' | '.join(opzioni)}" + (
				" (more than one)" if campo.get("multiple") else ""
			)
		if campo.get("unit"):
			riga += f" - unit: {campo['unit']}"
		righe.append(riga)
	return "\n".join(righe)


def _scheda(record: str):
	doc = frappe.get_doc(cartella.DOCTYPE, record)
	frappe.has_permission("CRM Lead", "read", doc=doc.lead, throw=True)
	if doc.practitioner != frappe.session.user:
		frappe.throw(_("A visit is filled by who writes it"), frappe.PermissionError)
	if doc.docstatus != 0:
		frappe.throw(_("A signed visit is not rewritten: add to it"))
	if not doc.get("template_version"):
		frappe.throw(_("Dictation fills a visit written on a clinical sheet"))
	from crm.moduli import modelli

	schema = modelli.carica_schema(frappe.get_cached_doc(modelli.VERSIONE, doc.template_version).schema)
	return doc, schema


def _risposte(doc) -> dict:
	return json.loads(doc.answers or "{}") if isinstance(doc.answers, str) else dict(doc.answers or {})


@frappe.whitelist(methods=["POST"])
def propose_answers(record: str, text: str) -> dict:
	"""What the words fill in the sheet, to tick: nothing is written yet."""
	from crm.moduli import schema as S
	from crm.permissions import livelli

	livelli.verifica(DETTATURA.usa)
	doc, schema = _scheda(record)
	if not consensi.ha_il_consenso(doc.lead, ASSISTENTE.chiave):
		frappe.throw(_("The patient has not agreed to the assistant: record their consent first"))
	parole = (text or "").strip()
	if len(parole) < 10:
		frappe.throw(_("Write or dictate what happened in the visit"))
	campi = _campi(schema)
	risposta = modello.chiedi(
		DETTATURA.chiave,
		ISTRUZIONI.format(scopo=regole.SCOPO, campi=descrivi_campi(campi)),
		parole,
		json_atteso=True,
		riferimento=(cartella.DOCTYPE, doc.name),
	)
	if risposta.errore:
		return {"event": risposta.evento, "error": _(risposta.errore), "proposals": []}
	proposte = risposta.dati.get("answers") if isinstance(risposta.dati.get("answers"), dict) else {}
	per_id = {c["id"]: c for c in campi}
	puliti, _errori, _stato = S.pulisci(schema, {k: v for k, v in proposte.items() if k in per_id})
	attuali = _risposte(doc)
	return {
		"event": risposta.evento,
		"proposals": [
			{
				"field": chiave,
				"label": per_id[chiave].get("label") or chiave,
				"type": per_id[chiave].get("type"),
				"value": puliti[chiave],
				"current": attuali.get(chiave),
				"one_by_one": delicato(per_id[chiave]),
			}
			for chiave in per_id
			if chiave in proposte and puliti.get(chiave) not in (None, "", [])
		],
	}


@frappe.whitelist(methods=["POST"])
def apply_answers(event: str, answers) -> dict:
	"""The answers the practitioner ticked go into the draft visit; the register
	keeps what was proposed and what was kept."""
	from crm.moduli import schema as S
	from crm.permissions import livelli

	livelli.verifica(DETTATURA.usa)
	evento = frappe.get_doc(modello.EVENTO, event)
	if evento.function != DETTATURA.chiave or evento.reference_doctype != cartella.DOCTYPE:
		frappe.throw(_("This is not a dictation"))
	doc, schema = _scheda(evento.reference_name)
	scelti = frappe.parse_json(answers) if isinstance(answers, str) else (answers or {})
	ids = {c["id"] for c in _campi(schema)}
	scelti = {k: v for k, v in (scelti or {}).items() if k in ids}
	puliti, _errori, _stato = S.pulisci(schema, scelti)
	tenuti = {k: puliti[k] for k in scelti if k in puliti}
	riga = cartella.save_record(
		doc.lead,
		name=doc.name,
		content=doc.content,
		kind=doc.kind,
		visibility=doc.visibility,
		answers={**_risposte(doc), **tenuti},
	)
	proposte = (regole.estrai_json(evento.draft or "") or {}).get("answers") or {}
	modello.accetta(
		event,
		json.dumps(tenuti, ensure_ascii=False, indent=1, sort_keys=True, default=str),
		confronto=json.dumps(
			{k: v for k, v in proposte.items() if k in ids},
			ensure_ascii=False,
			indent=1,
			sort_keys=True,
			default=str,
		),
	)
	return riga


@frappe.whitelist(methods=["POST"])
def discard(event: str) -> None:
	modello.scarta(event)
