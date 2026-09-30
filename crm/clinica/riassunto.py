# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The summary before the visit, with its sources (design.md, "L'assistente",
point 4).

- **From what the practitioner may read, and only that**: the signed visits and
  notes by the dossier's rules, the confirmed lines of the patient's summary, the
  titles of the archive's documents. Each is numbered, and the summary cites them
  as [1], [2].
- **Only what is written**: no scores, no ranking, no alerts, no advice. It is a
  summary to read before the visit, not a judgement on the patient.
- **Nothing is kept** but the register's event; every record it read is in the
  access log, like any reading of the record.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import format_date, get_fullname, strip_html

from crm.assistente import modello, regole
from crm.clinica import ASSISTENTE, RIASSUNTO, cartella, sintesi
from crm.moduli import consensi

#: The last entries a summary reads: what came before is in the record.
MAX_VOCI = 15
MAX_CARATTERI_VOCE = 1500

ISTRUZIONI = """{scopo}
You summarise a patient's record for the practitioner who is about to see them.
Use only the sources below, and cite each fact with its number, like [2]. Write
what the sources say and nothing else: no diagnosis they do not contain, no
score, no ranking, no alert, no advice, no guess at what might be wrong. Where the
sources disagree, say so and cite both. Short: what matters for the next visit
first, then the history. In the language of the sources. Plain text, no markdown.

The sources:
{fonti}"""


def fonti(lead: str) -> list[dict]:
	"""What the summary may read: numbered, with what it is and where it is."""
	from crm.clinica.assistente import testo_della_visita

	voci = []
	for nome in frappe.get_all(
		cartella.DOCTYPE,
		filters={"lead": lead, "docstatus": 1},
		pluck="name",
		order_by="record_date desc",
		limit=MAX_VOCI * 3,
	):
		doc = frappe.get_doc(cartella.DOCTYPE, nome)
		if not cartella.puo_leggere(doc):
			continue
		doc.add_viewed()
		testo = testo_della_visita(doc)[:MAX_CARATTERI_VOCE]
		if not testo:
			continue
		voci.append(
			{
				"doctype": cartella.DOCTYPE,
				"name": doc.name,
				"label": _("{0}, {1}, {2}").format(
					_(doc.kind), format_date(doc.record_date), get_fullname(doc.practitioner)
				),
				"text": testo,
			}
		)
		if len(voci) >= MAX_VOCI:
			break
	for riga in sintesi.sintesi(lead)["lines"]:
		if riga.get("value"):
			voci.append(
				{
					"doctype": sintesi.DOCTYPE,
					"name": riga.get("name"),
					"label": _("Summary: {0}").format(riga.get("label")),
					"text": f"{riga.get('label')}: {riga.get('value')} {riga.get('unit') or ''}".strip(),
				}
			)
	from crm.clinica import archivio

	for documento in archivio.get_documents(lead)["documents"][:MAX_VOCI]:
		voci.append(
			{
				"doctype": "Clinic Document",
				"name": documento.get("name"),
				"label": _("Document: {0}").format(documento.get("title")),
				"text": f"{documento.get('title')} ({documento.get('document_type')}, "
				f"{format_date(documento.get('document_date'))})",
			}
		)
	for numero, voce in enumerate(voci, start=1):
		voce["n"] = numero
	return voci


@frappe.whitelist(methods=["POST"])
def summary_before_visit(lead: str) -> dict:
	"""A summary of what the session may read of the record, citing its sources.
	Nothing is saved but the register's event."""
	from crm.permissions import livelli

	livelli.verifica(RIASSUNTO.usa)
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	if not consensi.ha_il_consenso(lead, ASSISTENTE.chiave):
		frappe.throw(_("The patient has not agreed to the assistant: record their consent first"))
	voci = fonti(lead)
	if not voci:
		frappe.throw(_("Nothing written yet to summarise"))
	elenco = "\n\n".join(f"[{v['n']}] {v['label']}\n{v['text']}" for v in voci)
	risposta = modello.chiedi(
		RIASSUNTO.chiave,
		ISTRUZIONI.format(scopo=regole.SCOPO, fonti=elenco),
		_("Summarise the record for the next visit."),
		riferimento=("CRM Lead", lead),
	)
	return {
		"event": risposta.evento,
		"summary": risposta.testo,
		"error": _(risposta.errore) if risposta.errore else None,
		"sources": [{k: v[k] for k in ("n", "label", "doctype", "name")} for v in voci],
	}


@frappe.whitelist(methods=["POST"])
def read(event: str) -> None:
	"""Read: the register says the practitioner saw it, as it was."""
	evento = frappe.get_doc(modello.EVENTO, event)
	if evento.function != RIASSUNTO.chiave:
		frappe.throw(_("This is not a summary"))
	modello.accetta(event, evento.draft or "")
