# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The assistant in the clinic: drafts from a signed note, which the practitioner
checks and signs (design.md, "L'assistente", point 2).

- **From what was written, and only that**: the signed note of the visit and the
  answers of its sheet. Never the patient's name, code or address: the draft
  leaves a gap in square brackets, and the practitioner fills it.
- **With the patient's consent** to the assistant, one of the clinic's consents.
- **Two drafts**: a letter to the family doctor, and the instructions after the
  visit in plain words.
- **Kept only when the practitioner says so**: a note added to the visit, still a
  draft, with the mark "AI draft, checked by … on …", signed like any note. The
  instructions may also go on the person's board in their area.
- **The register** keeps them, and only the medical director reads the clinic's
  events (`assistente.registro_clinico`): they hold health data.
"""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import escape_html, strip_html

from crm.assistente import modello, regole
from crm.clinica import ASSISTENTE, DETTATURA, ISTRUZIONI, LETTERA, RIASSUNTO, cartella
from crm.moduli import consensi
from crm.permissions import livelli

#: The patient's consent to the assistant: the clinic's (`crm.clinica.ASSISTENTE`).
CONSENSO_ASSISTENTE = ASSISTENTE

PER_TIPO = {"letter": LETTERA, "instructions": ISTRUZIONI}

_COMUNE = """{scopo}
You draft from a practitioner's signed note of a visit. Write only what the note
says: no diagnosis, advice, medicine, dose, test or date the note does not
contain, nothing added to make it sound complete. Where the note is silent and the
text needs something, leave a gap in square brackets for the practitioner, like
[to complete]. Write in the language of the note. Plain text, no markdown."""

ISTRUZIONI_PER_TIPO = {
	"letter": _COMUNE
	+ """

Draft a short letter to the patient's family doctor about this visit: a greeting
to a colleague, what was found and what was done, what was advised, the
follow-up. Name the patient as [patient's name], and sign [practitioner's name].""",
	"instructions": _COMUNE
	+ """

Draft the instructions for the patient after this visit, addressed to them, in
plain words anybody understands: what to do, what to avoid, when to come back -
only as the note says.""",
}


def _risposte(doc) -> str:
	"""The sheet's answers, as label and value: what the practitioner wrote in it."""
	if not doc.get("template_version"):
		return ""
	from crm.moduli import modelli
	from crm.moduli import schema as S

	schema = modelli.carica_schema(frappe.get_cached_doc(modelli.VERSIONE, doc.template_version).schema)
	risposte = json.loads(doc.answers or "{}") if isinstance(doc.answers, str) else (doc.answers or {})
	righe = []
	for campo in S.campi(schema):
		valore = risposte.get(campo.get("id"))
		if valore in (None, "", [], {}) or campo.get("type") in ("signature", "attachment", "paragraph"):
			continue
		righe.append(f"{campo.get('label') or campo.get('id')}: {json.dumps(valore, ensure_ascii=False)}")
	return "\n".join(righe)


def testo_della_visita(doc) -> str:
	"""What goes to the model: the note and the sheet's answers, nothing about who
	the patient is."""
	parti = [strip_html(doc.content or "").strip(), _risposte(doc)]
	return "\n\n".join(parte for parte in parti if parte)


def _visita(record: str):
	doc = frappe.get_doc(cartella.DOCTYPE, record)
	frappe.has_permission("CRM Lead", "read", doc=doc.lead, throw=True)
	if not cartella.puo_leggere(doc):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return doc


def disponibili() -> dict:
	"""What the assistant offers the session on a record, for the Clinic tab."""
	if not livelli.puo("assistente.bozze"):
		return {}
	return {
		"drafts": modello.acceso(LETTERA.chiave),
		"dictation": modello.acceso(DETTATURA.chiave),
		"summary": modello.acceso(RIASSUNTO.chiave),
	}


@frappe.whitelist(methods=["POST"])
def draft_from_note(record: str, kind: str) -> dict:
	"""A draft from one's own signed note: nothing is saved but the register's event."""
	funzione = PER_TIPO.get(kind)
	if not funzione:
		frappe.throw(_("{0} is not a draft the assistant writes").format(kind))
	livelli.verifica(funzione.usa)
	doc = _visita(record)
	if doc.practitioner != frappe.session.user:
		frappe.throw(_("Drafts come from one's own notes"), frappe.PermissionError)
	if doc.docstatus != 1:
		frappe.throw(_("Sign the note first: drafts come from what is signed"))
	if not consensi.ha_il_consenso(doc.lead, CONSENSO_ASSISTENTE.chiave):
		frappe.throw(_("The patient has not agreed to the assistant: record their consent first"))
	testo = testo_della_visita(doc)
	if not testo:
		frappe.throw(_("The note says nothing to draft from"))
	risposta = modello.chiedi(
		funzione.chiave,
		ISTRUZIONI_PER_TIPO[kind].format(scopo=regole.SCOPO),
		testo,
		riferimento=(cartella.DOCTYPE, doc.name),
	)
	return {
		"event": risposta.evento,
		"draft": risposta.testo,
		"error": _(risposta.errore) if risposta.errore else None,
	}


def _html(testo: str) -> str:
	return "".join(f"<p>{escape_html(riga)}</p>" for riga in testo.splitlines() if riga.strip())


@frappe.whitelist(methods=["POST"])
def keep_draft(event: str, text: str, post_to_area: int = 0) -> dict:
	"""The practitioner made the draft theirs: a note added to the visit, still to
	sign, with the mark; the instructions also on the person's board, if asked."""
	evento = frappe.get_doc(modello.EVENTO, event)
	funzione = next((f for f in PER_TIPO.values() if f.chiave == evento.function), None)
	if not funzione or evento.reference_doctype != cartella.DOCTYPE:
		frappe.throw(_("This is not a draft from a note"))
	livelli.verifica(funzione.usa)
	visita = _visita(evento.reference_name)
	testo = (text or "").strip()
	if not testo:
		frappe.throw(_("Write the text, or discard the draft"))
	evento = modello.accetta(event, testo)
	segno = modello.segno(evento)
	nota = cartella.save_record(
		visita.lead,
		content=_html(testo) + f"<p><em>{escape_html(segno)}</em></p>",
		kind="Note",
		visibility=visita.visibility,
		addendum_to=visita.addendum_to or visita.name,
	)
	fatto = {"note": nota["name"], "mark": segno}
	if frappe.utils.cint(post_to_area) and funzione is ISTRUZIONI:
		from crm.clinica.area import messaggi

		messaggi.post_message(visita.lead, f"{testo}\n\n{segno}")
		fatto["posted"] = True
	return fatto


@frappe.whitelist(methods=["POST"])
def discard_draft(event: str) -> None:
	modello.scarta(event)
