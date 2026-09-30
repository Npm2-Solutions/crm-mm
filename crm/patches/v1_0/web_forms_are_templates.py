# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The website's forms become templates of the "Website" use (`crm.moduli.sito`).

Each form built on the framework's Web Form for a person or a deal becomes a
template at the same address, its fields questions: /crm-form/<route> and the
blocks in the site's pages keep working. A published one is published again as
version 1 when it can be: a form that asks neither an email nor a mobile could
never find the person again, so it stays a draft, and the log says which. Then
the old forms, their two custom fields and the Guest `select` they needed on
the lists go: a question carries its own choices, and nobody lists anything.
"""

import json
import re

import frappe

MODULO_DEL_CRM = "FCRM"
DESTINAZIONI = ("CRM Lead", "CRM Deal")
#: The lists a stranger could pick from on the old forms (their builder opened them).
ELENCHI = (
	"CRM Lead Source",
	"CRM Territory",
	"CRM Industry",
	"CRM Service",
	"Salutation",
	"Gender",
	"Currency",
)
TESTI_LUNGHI = {"Small Text", "Text", "Long Text", "Text Editor", "HTML Editor", "Markdown Editor"}
NUMERI = {"Int", "Float", "Currency", "Percent"}
#: The person's field an old form filled, and the one its question fills now.
PERSONA = {
	"first_name": "first_name",
	"last_name": "last_name",
	"email": "email",
	"mobile_no": "mobile_no",
	"phone": "mobile_no",
	"organization": "organization",
	"organization_name": "organization",
	"job_title": "job_title",
}
#: The choices a list gives a question, at most: a longer list becomes words to write.
MAX_SCELTE = 100
#: The conditions the old forms could say simply: `eval:doc.x == 'y'`, `eval:doc.x`, `x`.
UGUALE = re.compile(r"""^\s*(?:eval:)?\s*doc\.([a-z_][a-z0-9_]*)\s*===?\s*(['"])(.*?)\2\s*$""", re.I)
PRESENTE = re.compile(r"""^\s*(?:eval:\s*doc\.)?([a-z_][a-z0-9_]*)\s*$""", re.I)


def _id(nome: str, visti: set) -> str:
	"""A question's key from a field's name: lowercase, a letter first, unique."""
	chiave = re.sub(r"[^a-z0-9_]+", "_", (nome or "").lower()).strip("_")[:56] or "domanda"
	if not chiave[0].isalpha():
		chiave = "q_" + chiave
	candidata, numero = chiave, 1
	while candidata in visti:
		numero += 1
		candidata = f"{chiave}_{numero}"
	visti.add(candidata)
	return candidata


def _condizione(espressione: str | None, chiavi: dict, tipi: dict) -> list | None:
	"""The old form's condition as the engine writes one, when it is a simple one;
	None when there is none, "?" when it could not be read."""
	if not (espressione or "").strip():
		return None
	uguale = UGUALE.match(espressione)
	if uguale and uguale.group(1) in chiavi:
		return [[{"field": chiavi[uguale.group(1)], "operator": "equals", "value": uguale.group(3)}]]
	presente = PRESENTE.match(espressione)
	if presente and presente.group(1) in chiavi:
		chiave = chiavi[presente.group(1)]
		# a ticked box is a yes; anything else is an answer given
		if tipi.get(chiave) == "yesno":
			return [[{"field": chiave, "operator": "equals", "value": "1"}]]
		return [[{"field": chiave, "operator": "is_set"}]]
	return "?"


def schema_da_campi(campi: list[dict], scelte_di=None) -> tuple[dict, list[str]]:
	"""The schema of an old form's fields, and what could not come along. Pure but
	for ``scelte_di(doctype)``, the records of a list a field linked to."""
	sezioni = [{"id": "s1", "title": "", "fields": []}]
	visti, chiavi, tipi, avvisi = set(), {}, {}, []
	persona_usata = set()
	for campo in campi:
		tipo_campo = campo.get("fieldtype")
		etichetta = (campo.get("label") or campo.get("fieldname") or "").strip()
		if tipo_campo == "Section Break":
			if sezioni[-1]["fields"] or sezioni[-1]["title"]:
				sezioni.append({"id": f"s{len(sezioni) + 1}", "title": etichetta, "fields": []})
			else:
				sezioni[-1]["title"] = etichetta
			continue
		if tipo_campo == "Column Break":
			continue
		chiave = _id(campo.get("fieldname"), visti)
		domanda = {"id": chiave, "label": etichetta or chiave}
		opzioni = campo.get("options") or ""
		if tipo_campo in TESTI_LUNGHI:
			domanda.update(type="text", multiline=True)
		elif tipo_campo == "Select":
			voci = [v.strip() for v in opzioni.split("\n") if v.strip()]
			domanda.update(
				type="choice", display="dropdown", options=[{"label": v} for v in dict.fromkeys(voci)]
			)
		elif tipo_campo == "Link":
			voci = list(dict.fromkeys(scelte_di(opzioni) if scelte_di and opzioni else []))
			if voci and len(voci) <= MAX_SCELTE:
				domanda.update(type="choice", display="dropdown", options=[{"label": v} for v in voci])
			else:
				domanda["type"] = "text"
				avvisi.append(f"{etichetta}: the list {opzioni} became words to write")
		elif tipo_campo in NUMERI:
			domanda["type"] = "number"
			if tipo_campo == "Int":
				domanda["decimals"] = 0
		elif tipo_campo == "Check":
			domanda["type"] = "yesno"
		elif tipo_campo in ("Date", "Datetime"):
			domanda["type"] = "date"
			if tipo_campo == "Datetime":
				avvisi.append(f"{etichetta}: the time of day is not asked any more")
		else:
			domanda["type"] = "text"
		persona = PERSONA.get(campo.get("fieldname"))
		if tipo_campo == "Data" and opzioni == "Email":
			persona = "email"
		elif tipo_campo == "Phone" or (tipo_campo == "Data" and opzioni == "Phone"):
			persona = persona or "mobile_no"
		if persona and domanda["type"] == "text" and persona not in persona_usata:
			domanda["person"] = persona
			persona_usata.add(persona)
		if campo.get("reqd"):
			domanda["required"] = True
		if campo.get("placeholder") and domanda["type"] in ("text", "number"):
			domanda["placeholder"] = campo["placeholder"]
		if campo.get("description"):
			domanda["description"] = campo["description"]
		for vecchia, nuova in (("depends_on", "show_if"), ("mandatory_depends_on", "required_if")):
			condizione = _condizione(campo.get(vecchia), chiavi, tipi)
			if condizione == "?":
				avvisi.append(f"{etichetta}: its condition {campo.get(vecchia)} could not be kept")
			elif condizione:
				domanda[nuova] = condizione
		if (campo.get("read_only_depends_on") or "").strip():
			avvisi.append(f"{etichetta}: a question is never read-only on the website")
		chiavi[campo.get("fieldname")] = chiave
		tipi[chiave] = domanda["type"]
		sezioni[-1]["fields"].append(domanda)
	return {"sections": [s for s in sezioni if s["fields"] or s["title"]] or sezioni[:1]}, avvisi


def _scelte_di(doctype: str) -> list[str]:
	if not frappe.db.exists("DocType", doctype):
		return []
	return frappe.get_all(doctype, pluck="name", order_by="name asc", limit=MAX_SCELTE + 1)


def converti(vecchio, campi: list[dict]) -> tuple[str, list[str]]:
	"""The template an old form becomes, published when it was and when it can be,
	and what could not come along."""
	from crm.moduli import modelli, sito
	from crm.moduli.doctype.crm_form_template.crm_form_template import INDIRIZZO, indirizzo_da

	schema, avvisi = schema_da_campi(campi, _scelte_di)
	indirizzo = sito.indirizzo(vecchio.get("route"))
	if not INDIRIZZO.match(indirizzo or ""):
		indirizzo = indirizzo_da(vecchio.get("title"))
	dopo = (vecchio.get("success_url") or "").strip()
	if dopo and not re.match(r"^(https?://|/(?!/))", dopo):
		avvisi.append(f"the page after sending, {dopo}, is not a page address")
		dopo = ""
	modello = frappe.get_doc(
		{
			"doctype": modelli.MODELLO,
			"title": (vecchio.get("title") or vecchio.get("name") or "")[:140],
			"use": modelli.SITO,
			"enabled": 1,
			"description": vecchio.get("introduction_text") or "",
			"route": modelli.indirizzo_libero(indirizzo),
			"button_label": vecchio.get("button_label") or "",
			"success_message": vecchio.get("success_message") or "",
			"success_url": dopo,
			"allowed_embedding_domains": vecchio.get("allowed_embedding_domains") or "",
			"schema": json.dumps(schema, ensure_ascii=False),
		}
	).insert(ignore_permissions=True)
	if vecchio.get("crm_published"):
		try:
			modelli.pubblica(modello, notes=f"From the web form {vecchio.get('name')}")
		except frappe.ValidationError as errore:
			avvisi.append(f"left as a draft: {frappe.utils.strip_html(str(errore))}")
	return modello.name, avvisi


def execute():
	from crm.moduli import modelli

	vecchi = []
	if frappe.db.has_column("Web Form", "crm_published"):
		vecchi = frappe.get_all(
			"Web Form",
			filters={"module": MODULO_DEL_CRM, "doc_type": ("in", DESTINAZIONI)},
			fields=[
				"name",
				"title",
				"route",
				"introduction_text",
				"button_label",
				"success_message",
				"success_url",
				"allowed_embedding_domains",
				"crm_published",
			],
		)
	for vecchio in vecchi:
		campi = frappe.get_all(
			"Web Form Field",
			filters={"parent": vecchio.name, "parenttype": "Web Form"},
			fields=[
				"fieldname",
				"fieldtype",
				"label",
				"options",
				"reqd",
				"placeholder",
				"description",
				"depends_on",
				"mandatory_depends_on",
				"read_only_depends_on",
			],
			order_by="idx asc",
		)
		nome, avvisi = converti(vecchio, campi)
		if avvisi:
			frappe.log_error(
				title=f"Web form {vecchio.name} became the template {nome}",
				message="\n".join(avvisi),
				reference_doctype=modelli.MODELLO,
				reference_name=nome,
			)
		frappe.delete_doc("Web Form", vecchio.name, ignore_permissions=True, force=True)

	for campo in ("crm_published", "crm_hidden_defaults"):
		nome = frappe.db.get_value("Custom Field", {"dt": "Web Form", "fieldname": campo})
		if nome:
			frappe.delete_doc("Custom Field", nome, ignore_permissions=True, force=True)
	frappe.clear_cache(doctype="Web Form")
	revoca_gli_elenchi()


def revoca_gli_elenchi() -> None:
	"""Only the rows the old builder wrote: Guest, level 0, `select` and nothing else."""
	for doctype in ELENCHI:
		righe = frappe.get_all(
			"Custom DocPerm",
			filters={
				"parent": doctype,
				"role": "Guest",
				"permlevel": 0,
				"if_owner": 0,
				"select": 1,
				"read": 0,
				"write": 0,
				"create": 0,
				"delete": 0,
			},
			pluck="name",
		)
		if righe:
			frappe.db.delete("Custom DocPerm", {"name": ("in", righe)})
			frappe.clear_cache(doctype=doctype)
