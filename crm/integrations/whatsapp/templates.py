# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""WhatsApp message templates, managed from the CRM.

Outside the 24-hour window that opens when a customer writes, WhatsApp only
allows **approved templates**, so creating them cannot be a trip into the Desk:
it belongs in the CRM next to the chat.

frappe_whatsapp owns the `WhatsApp Templates` doctype and submits each one to
Meta for review when it is saved; this module is the CRM-facing surface over it.
Field names are read from the installed doctype rather than assumed, so a
different frappe_whatsapp release degrades instead of breaking.

A template lives on a WhatsApp Business account, never on a number
(`modelli_regole`): the page shows each number's, a new one is made on the
number chosen, and the templates are brought in from Meta here, every number's,
every page of them - frappe_whatsapp's `fetch` read the first number only, one
page of it, and kept one template of each name for all of them.
"""

import json
import re

import frappe
from frappe import _

from crm import lingue
from crm.integrations.whatsapp import modelli_regole as R

EDITABLE_FIELDS = (
	"template_name",
	"category",
	"language",
	"header",
	"header_type",
	"template",
	"footer",
	"sample_values",
)

# {{1}}, {{2}}… — Meta wants an example for every one of them, and wants them
# numbered from 1 without holes
PLACEHOLDER = re.compile(r"\{\{\s*(\d+)\s*\}\}")

# The only three Meta accepts. The installed doctype still offers TRANSACTIONAL,
# retired in 2023, and choosing it fails at submission with
# "(#100) Param category must be one of {UTILITY, MARKETING, AUTHENTICATION}" —
# after the template has been saved, so it looks like the CRM lost it.
META_CATEGORIES = ("UTILITY", "MARKETING", "AUTHENTICATION")


def _check_manager():
	from crm.permissions.livelli import verifica

	verifica("modelli_messaggio.gestisci", messaggio=_("Only sales managers can manage WhatsApp templates"))


def templates_available() -> bool:
	return bool(frappe.db.exists("DocType", "WhatsApp Templates"))


def _known_fields() -> set[str]:
	return {df.fieldname for df in frappe.get_meta("WhatsApp Templates").fields}


def _options_for(fieldname: str) -> list[str]:
	"""Select options straight from the installed doctype."""
	meta = frappe.get_meta("WhatsApp Templates")
	field = meta.get_field(fieldname)
	if not field or field.fieldtype != "Select" or not field.options:
		return []
	return [option for option in field.options.split("\n") if option]


def _languages() -> list[dict]:
	"""The languages the doctype will accept, which are Frappe's own.

	`language_code` is derived from this by frappe_whatsapp — it is not a field
	to fill in by hand, and the short hardcoded list we offered before ("en",
	"en_US", "it") both looked like a duplicate and left `language`, which is
	mandatory, empty.
	"""
	languages = frappe.get_all("Language", fields=["name", "language_name"], order_by="language_name")
	# the centre's own first: its templates are written in it, and the list
	# opened on Afrikaans. Each by its name, which is unique: the code is Meta's
	own = lingue.del_centro()
	languages.sort(key=lambda language: language.name != own)
	return [
		{"value": language.name, "label": language.language_name or language.name} for language in languages
	]


def _categories() -> list[str]:
	"""What the doctype offers, minus what Meta has stopped accepting."""
	usable = [option for option in _options_for("category") if option.upper() in META_CATEGORIES]
	return usable or list(META_CATEGORIES)


def numeri() -> list[dict]:
	"""The centre's numbers: the one that sends first, then the others in use,
	then the ones taken out of use, each with the WhatsApp Business account its
	templates are kept on (`waba`: for the server, the ids are what Meta calls
	things, and a manager choosing a number has no use for them)."""
	# a bench without the WhatsApp app has no table of numbers
	if not frappe.db.table_exists("WhatsApp Account"):
		return []
	from crm.api.whatsapp import sending_account_name

	invia = sending_account_name()
	fields = ["name", "status"] + [
		campo for campo in ("account_name", "business_id") if frappe.db.has_column("WhatsApp Account", campo)
	]
	righe = [
		{
			"name": riga.name,
			"label": riga.get("account_name") or riga.name,
			"active": riga.status != "Inactive",
			"sends": riga.name == invia,
			"waba": riga.get("business_id") or "",
		}
		for riga in frappe.get_all("WhatsApp Account", fields=fields, order_by="creation asc")
	]
	return sorted(righe, key=lambda numero: (not numero["sends"], not numero["active"]))


def _per_lo_schermo(numeri_: list[dict]) -> list[dict]:
	"""The numbers as the page reads them: no ids, and the ones each shares its
	templates with, by their names."""
	return [
		{
			**{chiave: valore for chiave, valore in numero.items() if chiave != "waba"},
			"shares": [
				altro["label"]
				for altro in numeri_
				if altro["name"] != numero["name"] and numero["waba"] and altro["waba"] == numero["waba"]
			],
		}
		for numero in numeri_
	]


def _pulsanti_di(nomi: list[str]) -> dict[str, list[dict]]:
	"""Each template's buttons, as the screens read them."""
	if not nomi or not frappe.db.exists("DocType", "WhatsApp Button"):
		return {}
	righe = frappe.get_all(
		"WhatsApp Button",
		filters={"parenttype": "WhatsApp Templates", "parent": ["in", nomi]},
		fields=[
			"parent",
			"button_type",
			"button_label",
			"website_url",
			"url_type",
			"example_url",
			"phone_number",
		],
		order_by="idx asc",
	)
	per_modello: dict[str, list[dict]] = {}
	for riga in righe:
		per_modello.setdefault(riga.parent, []).append(riga)
	return {nome: R.pulsanti_delle_righe(righe) for nome, righe in per_modello.items()}


@frappe.whitelist()
def get_templates() -> dict:
	_check_manager()
	if not templates_available():
		return {"available": False, "templates": []}

	known = _known_fields()
	fields = ["name"] + [
		f
		for f in ("template_name", "status", "whatsapp_account", "language_code", *EDITABLE_FIELDS)
		if f in known
	]
	modelli = frappe.get_all(
		"WhatsApp Templates", fields=list(dict.fromkeys(fields)), order_by="modified desc"
	)
	numeri_ = numeri()
	invia = next((numero["name"] for numero in numeri_ if numero["sends"]), None)
	pulsanti = _pulsanti_di([modello.name for modello in modelli])
	for modello in modelli:
		# the numbers that can send it: every one of its WhatsApp Business account
		modello["numbers"] = R.numeri_che_possono(modello.get("whatsapp_account"), numeri_, invia)
		modello["buttons"] = pulsanti.get(modello.name, [])
	return {
		"available": True,
		"templates": modelli,
		"numbers": _per_lo_schermo(numeri_),
		"categories": _categories(),
		"languages": _languages(),
		"language": lingue.del_centro(),
		"fields": sorted(known & set(EDITABLE_FIELDS)),
	}


def modelli_approvati(campi: tuple = (), per: str | None = None) -> list[dict]:
	"""The approved templates, with `campi` besides their names and words; the
	ones for the document type `per` and for any, when it is given."""
	if not templates_available():
		return []
	known = _known_fields()
	fields = ["name", "template_name", "template"] + [
		campo for campo in ("whatsapp_account", *campi) if campo in known
	]
	filters = {"status": "APPROVED"}
	if per and "for_doctype" in known:
		filters["for_doctype"] = ["in", [per, ""]]
	return frappe.get_all(
		"WhatsApp Templates",
		filters=filters,
		fields=list(dict.fromkeys(fields)),
		order_by="template_name asc",
	)


def modelli_inviabili(campi: tuple = (), per: str | None = None) -> list[dict]:
	"""The approved templates the number that sends can send: its WhatsApp
	Business account's, and the ones nobody wrote an account on (they go out
	from whichever number sends, as they always did). What every chooser of a
	template offers - the chat, the automations, the waiting list, the area -:
	another account's is a choice that can only fail."""
	from crm.api.whatsapp import sending_account_name

	numeri_ = numeri()
	invia = sending_account_name()
	return [
		modello
		for modello in modelli_approvati(campi, per)
		if not invia
		or not modello.get("whatsapp_account")
		or R.stesso_account(modello.get("whatsapp_account"), invia, numeri_)
	]


def check_placeholders(values: dict) -> None:
	"""Every {{1}} needs an example, and they must run 1, 2, 3 without holes.

	Meta requires an example value for each parameter at creation time, and
	rejects the template the moment it is submitted when one is missing — so the
	CRM shows it saved and Meta answers REJECTED a second later, with the reason
	only in WhatsApp Manager. Better to refuse it here, while the person is still
	looking at the body they wrote.
	"""
	found = [int(number) for number in PLACEHOLDER.findall(values.get("template") or "")]
	if not found:
		return

	wanted = sorted(set(found))
	if wanted != list(range(1, len(wanted) + 1)):
		frappe.throw(
			# {{1}} goes in as a value: in the sentence .format() would make it {1}
			_("The placeholders must be numbered from {0} without gaps. This body has: {1}").format(
				"{{1}}", ", ".join(f"{{{{{number}}}}}" for number in wanted)
			)
		)

	samples = [value.strip() for value in (values.get("sample_values") or "").split(",") if value.strip()]
	if len(samples) != len(wanted):
		frappe.throw(
			_(
				"Meta wants an example for every placeholder: this body has {0} and {1} were given. "
				"Write them separated by commas, in order."
			).format(len(wanted), len(samples))
		)


@frappe.whitelist(methods=["POST"])
def sync_templates() -> dict:
	"""Bring in the templates that live on Meta but not here, every number's.

	The list is read from the local records, so a template made in WhatsApp
	Manager — or `hello_world`, which Meta creates by itself with every new
	WhatsApp Business Account — exists on Meta and is invisible here, and cannot
	be sent.

	It also refreshes the status of the ones we did create: normally that arrives
	on the `message_template_status_update` webhook, and this is the way back if
	one is ever missed. What a number could not bring in is said by its name,
	and the others come in all the same.
	"""
	_check_manager()
	if not templates_available():
		frappe.throw(_("The WhatsApp app is not installed on this site"))

	problemi = porta_dentro()
	risposta = get_templates()
	risposta["problems"] = problemi
	return risposta


#: what is asked of Meta for each template
CAMPI_DI_META = "id,name,status,category,language,components"


def porta_dentro() -> list[dict]:
	"""Every template of every number in use, from Meta, kept here.

	Once per WhatsApp Business account (two numbers of one account have the same
	templates), every page of them (Meta gives a hundred at most at a time). A
	template is found by Meta's id, else by its name and language on the same
	account; nothing is sent back to Meta (`_conserva` writes without the
	document's hooks, which would submit it again). What one account could not
	bring in is returned, by the number's name."""
	from crm.integrations.meta.client import MetaAPIError, get_whatsapp_app_secret, graph_get_paginated

	tutti = numeri()
	lingue_note = set(frappe.get_all("Language", pluck="name"))
	fatti, problemi = set(), []
	for numero in tutti:
		if not numero["active"] or (numero["waba"] or numero["name"]) in fatti:
			continue
		fatti.add(numero["waba"] or numero["name"])
		if not numero["waba"]:
			problemi.append(
				{
					"number": numero["label"],
					"error": _("Its WhatsApp Business account is not known: connect the number again."),
				}
			)
			continue
		token = frappe.get_doc("WhatsApp Account", numero["name"]).get_password(
			"token", raise_exception=False
		)
		try:
			da_meta = list(
				graph_get_paginated(
					f"{numero['waba']}/message_templates",
					token,
					{"fields": CAMPI_DI_META, "limit": 100},
					secret=get_whatsapp_app_secret(),
				)
			)
		except MetaAPIError as errore:
			problemi.append({"number": numero["label"], "error": str(errore)})
			continue
		_conserva(da_meta, numero["name"], R.numeri_che_possono(numero["name"], tutti, None), lingue_note)
	return problemi


def _conserva(da_meta: list[dict], account: str, conti: list[str], lingue_note: set[str]) -> None:
	"""One account's templates as Meta has them, kept here; the ones Meta no
	longer has marked so (`R.SPARITO`), never deleted: the messages sent with
	them still name them."""
	campi = ["name", "id", "status", "actual_name", "template_name", "language_code", "whatsapp_account"]
	locali = frappe.get_all("WhatsApp Templates", fields=campi)
	per_id = {locale.id: locale for locale in locali if locale.id}
	del_conto = [locale for locale in locali if locale.whatsapp_account in conti]

	su_meta = set()
	for modello in da_meta:
		valori = R.da_meta(modello)
		su_meta.add(valori["id"])
		locale = per_id.get(valori["id"]) or next(
			(
				locale
				for locale in locali
				if not locale.id
				and (locale.whatsapp_account in conti or not locale.whatsapp_account)
				and valori["actual_name"] in (locale.actual_name, locale.template_name)
				and locale.language_code == valori["language_code"]
			),
			None,
		)
		_scrivi(valori, locale, account, conti, lingue_note)

	for nome in R.spariti(del_conto, su_meta):
		frappe.db.set_value("WhatsApp Templates", nome, "status", R.SPARITO, update_modified=False)


def _etichetta_libera(nome: str, lingua: str, account: str) -> str:
	"""The label a template brought in is shown by: its name on Meta, unless
	another one has it (frappe_whatsapp keeps the label unique) - the same name
	in another language, or on another account -, then with the language, then
	with the number too."""
	for etichetta in (nome, f"{nome} ({lingua})", f"{nome} ({lingua}, {account})"):
		if not frappe.db.exists("WhatsApp Templates", {"template_name": etichetta}):
			return etichetta
	from frappe.model.naming import append_number_if_name_exists

	return append_number_if_name_exists("WhatsApp Templates", etichetta, fieldname="template_name")


def _scrivi(valori: dict, locale, account: str, conti: list[str], lingue_note: set[str]) -> None:
	"""A template as Meta describes it, written without the document's hooks:
	saved, frappe_whatsapp would submit it to Meta again."""
	from frappe.model.naming import append_number_if_name_exists

	known = _known_fields()
	righe = valori.pop("buttons")
	if locale:
		doc = frappe.get_doc("WhatsApp Templates", locale.name)
	else:
		doc = frappe.new_doc("WhatsApp Templates")
		doc.template_name = _etichetta_libera(valori["actual_name"], valori["language_code"], account)
		doc.name = append_number_if_name_exists(
			"WhatsApp Templates", f"{valori['actual_name']}-{valori['language_code']}"
		)
	doc.update({campo: valore for campo, valore in valori.items() if campo in known})
	if "whatsapp_account" in known and doc.get("whatsapp_account") not in conti:
		doc.whatsapp_account = account
	if "language" in known and not doc.get("language"):
		doc.language = R.lingua(valori["language_code"], lingue_note)
	doc.set("buttons", righe)

	if locale:
		doc.db_update()
		frappe.db.delete("WhatsApp Button", {"parent": doc.name, "parenttype": doc.doctype})
	else:
		doc.db_insert()
	for riga in doc.get("buttons"):
		riga.parent, riga.parenttype, riga.parentfield = doc.name, doc.doctype, "buttons"
		riga.db_insert()


@frappe.whitelist(methods=["POST"])
def save_template(template: dict | str, name: str | None = None, number: str | None = None) -> dict:
	"""Create or update a template. Saving submits it to Meta for review.

	A new one is made on `number`'s WhatsApp Business account (the number that
	sends, when none is named): every number of that account can send it, no
	other. Its `buttons`, when given, replace the ones it had."""
	_check_manager()
	if not templates_available():
		frappe.throw(_("The WhatsApp app is not installed on this site"))
	if isinstance(template, str):
		template = json.loads(template)

	pulsanti = template.get("buttons")
	if pulsanti is not None:
		problemi = R.problemi_dei_pulsanti(pulsanti)
		if problemi:
			frappe.throw("<br>".join(problema.testo(_) for problema in problemi))

	known = _known_fields()
	values = {
		field: template.get(field)
		for field in EDITABLE_FIELDS
		if field in known and template.get(field) is not None
	}
	if not values.get("template"):
		frappe.throw(_("The message body is required"))
	if not name and not values.get("template_name"):
		frappe.throw(_("A template name is required"))

	check_placeholders(values)

	# frappe_whatsapp only puts the header in the payload when `header_type` says
	# what kind it is; without it the header typed here was dropped in silence.
	# A picture or a document brought in from Meta has no words here, and stays.
	if "header_type" in known:
		prima = frappe.db.get_value("WhatsApp Templates", name, "header_type") if name else ""
		if values.get("header"):
			values["header_type"] = "TEXT"
		elif prima not in ("IMAGE", "DOCUMENT", "VIDEO"):
			values["header_type"] = ""

	category = values.get("category")
	if category and category.upper() not in META_CATEGORIES:
		# say it here, before the template is saved and Meta rejects it with a
		# number instead of a reason
		frappe.throw(
			_("Meta no longer accepts the category {0}. Choose Utility, Marketing or Authentication.").format(
				category
			)
		)

	if name:
		doc = frappe.get_doc("WhatsApp Templates", name)
		# Meta changes a template's words, never its name, language or kind, nor
		# the account it lives on: frappe_whatsapp sends it the words only, and a
		# language changed here would ask Meta for a template it does not have
		for fisso in ("template_name", "language", "category"):
			values.pop(fisso, None)
		doc.update(values)
	else:
		doc = frappe.get_doc({"doctype": "WhatsApp Templates", **values})
		if "whatsapp_account" in known:
			doc.whatsapp_account = _numero_per_un_modello(number)
	if pulsanti is not None:
		doc.set("buttons", R.righe_dei_pulsanti(pulsanti))
	if name:
		doc.save()
	else:
		doc.insert()
	return {"name": doc.name, "status": doc.get("status") or ""}


def _numero_per_un_modello(number: str | None) -> str:
	"""The number a new template is made on: the one named, in use, else the one
	that sends."""
	from crm.api.whatsapp import sending_account_name

	number = number or sending_account_name()
	if not number or not frappe.db.exists("WhatsApp Account", number):
		frappe.throw(_("Choose the WhatsApp number the template is for"))
	if frappe.db.get_value("WhatsApp Account", number, "status") == "Inactive":
		frappe.throw(_("{0} is no longer in use: its templates cannot be sent").format(number))
	return number


@frappe.whitelist(methods=["POST"])
def delete_template(name: str) -> None:
	_check_manager()
	frappe.delete_doc("WhatsApp Templates", name)
