# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A form from paper: the PDF the centre already uses, the assistant proposes the
fields, whoever builds the template checks them (design.md, "Dal modulo di carta").
Office work: a blank form, nobody's data.

1. The text of the PDF. A scan has none, and says so: no reading of images here.
2. The assistant proposes a schema of the forms engine, told the components the
   engine registers - a new component is offered by itself - and the consents the
   centre has.
3. The engine's own rules check it (`schema.valida_schema`); what is wrong comes
   back with it, to put right in the builder.
4. Accepted, it becomes a draft template, finished and published in the builder
   like any other. Nothing is published by the assistant.
"""

from __future__ import annotations

import io
import json

import frappe
from frappe import _

from crm.assistente import DAL_MODULO_DI_CARTA, modello, regole
from crm.permissions import livelli

#: A paper form is a few pages; a book is not a form.
MAX_PAGINE = 20

ISTRUZIONI = """You turn a blank paper form into a JSON schema for a forms engine.
{scopo}

Write only what the paper says. Keep its words and its language. Invent no
question, no option, no legal text, no field the paper does not have.

Answer with one JSON object and nothing else:
{{"title": "...", "sections": [{{"id": "...", "title": "...", "fields": [...]}}]}}

Ids: lowercase letters, digits and underscores, starting with a letter, unique in
the whole form.

The components, with their "type" and what each may carry besides "id", "label",
"description" and "required":
{componenti}

- A choice: "options": [{{"label": "..."}}]; "multiple": true when more boxes may be ticked.
- Text to read (a notice, instructions, a paragraph of the law): "paragraph" with "text".
- A signature line: "signature" with "signer" one of patient, guardian, operator, and "level": "simple".
- A box to agree to something: "consent" with "consent_type" one of {consensi}; if none fits, "yesno".
- "required": true only where the paper says so (an asterisk, "obbligatorio").
"""


def _componenti() -> str:
	from crm.moduli import schema as S

	return "\n".join(
		f"- {c.tipo} ({c.etichetta}): {', '.join(c.proprieta) or 'nothing more'}"
		for c in S.componenti()
		# a calculation or a score is the builder's work, not the paper's
		if c.tipo not in ("calc", "score")
	)


def _consensi() -> str:
	righe = frappe.get_all(
		"CRM Consent Type", filters={"enabled": 1}, fields=["key", "label"], order_by="key asc"
	)
	return ", ".join(f'"{r.key}" ({r.label})' for r in righe) or "none"


def istruzioni() -> str:
	return ISTRUZIONI.format(scopo=regole.SCOPO, componenti=_componenti(), consensi=_consensi())


def testo_del_pdf(contenuto: bytes) -> str:
	"""The words of the PDF, page after page."""
	from pypdf import PdfReader

	lettore = PdfReader(io.BytesIO(contenuto))
	if len(lettore.pages) > MAX_PAGINE:
		frappe.throw(_("A form of at most {0} pages").format(MAX_PAGINE))
	return "\n\n".join((pagina.extract_text() or "").strip() for pagina in lettore.pages).strip()


def _pdf(file_url: str) -> tuple[str, bytes]:
	nome = frappe.db.get_value("File", {"file_url": file_url}, "name")
	if not nome:
		frappe.throw(_("There is no such file"))
	file = frappe.get_doc("File", nome)
	file.check_permission("read")
	contenuto = file.get_content(encodings=[])
	if isinstance(contenuto, str):
		contenuto = contenuto.encode("latin-1", "ignore")
	if not contenuto.startswith(b"%PDF"):
		frappe.throw(_("The paper form is a PDF"))
	return file.name, contenuto


def ripulisci(proposta: dict) -> tuple[str, dict]:
	"""The title, and the schema without what the engine does not keep."""
	titolo = str(proposta.get("title") or "").strip()[:140]
	sezioni = proposta.get("sections") if isinstance(proposta.get("sections"), list) else []
	return titolo, {"sections": [s for s in sezioni if isinstance(s, dict)]}


@frappe.whitelist(methods=["POST"])
def propose(file_url: str) -> dict:
	"""What the assistant reads in the paper form: a schema to check, with what is
	still wrong in it. Nothing is saved but the register's event."""
	from crm.moduli import modelli

	livelli.verifica(DAL_MODULO_DI_CARTA.usa)
	modello.verifica_acceso(DAL_MODULO_DI_CARTA.chiave)
	file, contenuto = _pdf(file_url)
	testo = testo_del_pdf(contenuto)
	if len(testo) < 20:
		frappe.throw(
			_(
				"This PDF has no text to read: it is a scan. Upload the file the centre prints the form from, or build it in the builder."
			)
		)
	risposta = modello.chiedi(
		DAL_MODULO_DI_CARTA.chiave,
		istruzioni(),
		testo,
		json_atteso=True,
		riferimento=("File", file),
	)
	if risposta.errore:
		return {"event": risposta.evento, "error": _(risposta.errore)}
	titolo, schema = ripulisci(risposta.dati)
	return {
		"event": risposta.evento,
		"title": titolo,
		"schema": schema,
		"problems": modelli.problemi(schema),
		"purpose": _(regole.SCOPO),
	}


@frappe.whitelist(methods=["POST"])
def create_draft(event: str, title: str, schema) -> dict:
	"""The proposal, as checked, becomes a draft template: finished and published in
	the builder. The register keeps what the person changed of it."""
	from crm.moduli import modelli

	livelli.verifica(DAL_MODULO_DI_CARTA.usa)
	letto = frappe.parse_json(schema) if isinstance(schema, str) else schema
	if not isinstance(letto, dict) or not isinstance(letto.get("sections"), list):
		frappe.throw(_("This is not a form"))
	if frappe.db.get_value(modello.EVENTO, event, "function") != DAL_MODULO_DI_CARTA.chiave:
		frappe.throw(_("This is not a proposal of a form from paper"))
	fatto = modelli.save_template(title=(title or "").strip() or _("Form from paper"), schema=letto)
	# the difference is between schemas, written the same way
	_titolo, proposta = ripulisci(
		regole.estrai_json(frappe.db.get_value(modello.EVENTO, event, "draft") or "") or {}
	)
	modello.accetta(
		event,
		_scritto(letto),
		riferimento=(modelli.MODELLO, fatto["name"]),
		confronto=_scritto(proposta),
	)
	return {"template": fatto["name"]}


def _scritto(schema: dict) -> str:
	return json.dumps(schema, ensure_ascii=False, indent=1, sort_keys=True)


@frappe.whitelist(methods=["POST"])
def discard(event: str) -> None:
	livelli.verifica(DAL_MODULO_DI_CARTA.usa)
	modello.scarta(event)
