# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The centre's form templates: a draft worked on, and the versions people fill.

A template (`CRM Form Template`) is worked on as a draft in Settings > Forms. What
people fill is a **published version** (`CRM Form Template Version`): immutable,
with the SHA-256 of its schema and the exact words of the consents it records,
frozen from the register the day it is published. A filled form points at the
version it was filled on, so changing a template never changes what somebody
signed, and the text a person agreed to can be shown word for word years later.

What a schema may hold and what answers mean is `crm.moduli.schema`'s business;
this module keeps drafts and versions, and says who may do what with them.

A template has a use: a **form** the person fills (on their own, from a link or the
desk's tablet, or at the desk with the operator), a **sheet** the operator writes
during an appointment - a beauty centre's treatment sheet, a gym's assessment - or
a form **on the website**, which anybody fills and which finds the person or makes
them (`crm.moduli.sito`). The centre builds its forms and sheets; marketing builds
the website's. Other modules add to it without the CRM knowing them, the way they add
capabilities: the clinic says when the "health data" mark means something
(`registra_dato_clinico`), and a sheet with the mark is its clinical sheet, written
in the clinical record.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass

import frappe
from frappe import _
from frappe.utils import cint, get_url, getdate, now_datetime

from crm.moduli import schema as S
from crm.permissions import livelli

MODELLO = "CRM Form Template"
VERSIONE = "CRM Form Template Version"
FORMA = "Form"
SCHEDA = "Sheet"
SITO = "Website"
CHIEDE = ("By hand", "First appointment", "Services")
VALIDITA = ("Forever", "One year", "Every appointment")


@dataclass(frozen=True)
class Uso:
	chiave: str
	etichetta: str
	descrizione: str = ""
	#: a use that always records health data
	clinico: bool = False
	#: filled in by the person, who gives its consents; a sheet is the operator's
	della_persona: bool = True
	#: filled at the desk, on the person's page
	al_banco: bool = True
	#: sent by link or on the tablet, and asked at a booking
	si_manda: bool = True
	#: published on the centre's website, filled in by anybody (`crm.moduli.sito`)
	sul_sito: bool = False
	#: opened by its link alone, no code: it asks nothing that is the person's to
	#: protect - no consent, no signature, no file, no health data (a survey)
	senza_codice: bool = False


_usi: dict[str, Uso] = {
	FORMA: Uso(FORMA, "Form", "Filled in and signed by the person: a privacy notice, consents, a contract"),
	SCHEDA: Uso(
		SCHEDA,
		"Sheet",
		"Written by the operator during an appointment: a treatment sheet, an assessment",
		della_persona=False,
		si_manda=False,
	),
	SITO: Uso(
		SITO,
		"Website",
		"Filled in by anybody on the centre's website: a request, a contact. It finds the person, or makes "
		"them, and opens their deal",
		al_banco=False,
		si_manda=False,
		sul_sito=True,
	),
}

#: A question of a form on the website may fill one of the person's fields.
S.registra_proprieta_comune("person")
#: The person's fields a question on the website may fill, and what they are.
CAMPI_PERSONA = {
	"full_name": "Name and surname",
	"first_name": "First name",
	"last_name": "Last name",
	"email": "Email",
	"mobile_no": "Mobile",
	"organization": "Organization",
	"job_title": "Job title",
}
_dato_clinico: list[Callable[[], bool]] = []


def registra_uso(uso: Uso) -> None:
	_usi[uso.chiave] = uso


def usi() -> list[Uso]:
	return list(_usi.values())


def uso(chiave: str | None) -> Uso:
	"""A template's use; an old one without it is a form."""
	return _usi.get(chiave or FORMA) or _usi[FORMA]


def usi_da_mandare() -> list[str]:
	"""The uses sent by a link or asked of the person: a form, a survey."""
	return [chiave for chiave, voce in _usi.items() if voce.si_manda]


def usi_della_persona() -> list[str]:
	"""The uses the person fills: what gives consents."""
	return [chiave for chiave, voce in _usi.items() if voce.della_persona]


def capacita_dell_uso(chiave: str | None) -> str:
	"""Who builds a use: a form on the website is marketing's, the rest the centre's."""
	return "moduli_lead.gestisci" if uso(chiave).sul_sito else "moduli.configura"


def verifica_uso(chiave: str | None) -> None:
	livelli.verifica(capacita_dell_uso(chiave))


def puo_costruire(chiave: str | None) -> bool:
	return livelli.puo(capacita_dell_uso(chiave))


def problemi_dell_uso(schema: dict, chiave: str | None) -> list[dict]:
	"""What the use does not allow. A consent is the person's to give, so a sheet
	the operator writes records none. A form on the website finds the person by an
	email or a mobile (the name, when it asks one, says which of a family), and is
	neither signed nor sent files."""
	voce = uso(chiave)
	problemi_trovati = []

	def problema(codice, campo, messaggio):
		problemi_trovati.append(
			{"code": codice, "field": campo.get("id") if campo else None, "message": messaggio}
		)

	for numero, campo in enumerate(S.campi(schema), 1):
		# a question without words (a signature) by its place, never its key
		etichetta = campo.get("label") or _("Question {0}").format(numero)
		if voce.senza_codice and campo.get("type") in ("consent", "signature", "attachment"):
			# opened by the link alone: nobody checked who holds it
			problema(
				"not_without_a_code",
				campo,
				_("{0}: a survey opens with its link alone, so it asks no consent, signature or file").format(
					etichetta
				),
			)
			continue
		if campo.get("type") == "consent" and not voce.della_persona:
			problema(
				"consent_on_a_sheet",
				campo,
				_("{0}: a consent is given by the person, on a form. A sheet does not record it.").format(
					etichetta
				),
			)
		if not voce.sul_sito:
			continue
		if campo.get("type") == "signature":
			problema(
				"signature_on_the_site",
				campo,
				_("{0}: a form on the website is not signed").format(etichetta),
			)
		if campo.get("type") == "attachment":
			problema("file_on_the_site", campo, _("{0}: no file is sent from the website").format(etichetta))
		if campo.get("type") == "body_chart":
			# where it hurts is health data: told at the centre, never to anybody's form
			problema(
				"body_chart_on_the_site",
				campo,
				_("{0}: where it hurts is asked at the centre, not on the website").format(etichetta),
			)
		if campo.get("person") and campo.get("person") not in CAMPI_PERSONA:
			problema(
				"person_field_unknown",
				campo,
				_("{0}: the person has no field {1}").format(etichetta, campo.get("person")),
			)
		elif campo.get("person") and campo.get("type") != "text":
			problema(
				"person_field_not_text",
				campo,
				_("{0}: only a text question fills one of the person's fields").format(etichetta),
			)
	if voce.sul_sito:
		dove = [campo.get("person") for campo in S.campi(schema) if campo.get("person")]
		for chiave_persona in {c for c in dove if dove.count(c) > 1}:
			problema(
				"person_field_twice",
				None,
				_("Two questions fill the same field of the person: {0}").format(
					_(CAMPI_PERSONA.get(chiave_persona, chiave_persona))
				),
			)
		if not {"email", "mobile_no"} & set(dove):
			problema(
				"person_without_contact",
				None,
				_(
					"A form on the website needs a question for the email or the mobile, to find the person again"
				),
			)
	return problemi_trovati


_voci_sintesi: dict[str, str] = {}


def registra_voce_sintesi(chiave: str, etichetta: str) -> None:
	"""A line of the patient's summary a field may answer (the clinic's
	allergies, medications, weight...): the builder offers it on the field."""
	_voci_sintesi[chiave] = etichetta


def voci_sintesi() -> dict[str, str]:
	return dict(_voci_sintesi)


def registra_dato_clinico(disponibile: Callable[[], bool]) -> None:
	"""Who says when marking a template "health data" means something: the clinic,
	when it is on. Without it the mark is not offered and not accepted."""
	if disponibile not in _dato_clinico:
		_dato_clinico.append(disponibile)


def dato_clinico_disponibile() -> bool:
	return any(disponibile() for disponibile in _dato_clinico)


def carica_schema(valore) -> dict:
	"""The schema as stored: a JSON field comes back as text or as a dict."""
	if isinstance(valore, dict):
		return valore
	if not valore:
		return {"sections": []}
	try:
		letto = json.loads(valore)
	except (TypeError, ValueError):
		return {"sections": []}
	return letto if isinstance(letto, dict) else {"sections": []}


def problemi(schema: dict, per_pubblicare: bool = False) -> list[dict]:
	errori = S.pronto_da_pubblicare(schema) if per_pubblicare else S.valida_schema(schema)
	return [errore.come_dict(_) for errore in errori]


def congela_consensi(schema: dict) -> list[dict]:
	"""The consents a version records, with the words they are given on today.

	Written into the schema, so the hash covers them: the PDF of a signed form
	carries the exact text, and a later rewrite of the consent is a later version.
	"""
	from crm.moduli import consensi

	sbagliati = []
	for campo in S.campi(schema):
		if campo.get("type") != "consent":
			continue
		chiave = campo.get("consent_type")
		tipo = frappe.db.get_value(
			consensi.TIPO, chiave, ["name", "label", "enabled", "text", "text_version"], as_dict=True
		)
		if not tipo:
			sbagliati.append(
				{
					"code": "unknown_consent",
					"field": campo.get("id"),
					"message": _("{0}: there is no consent called {1}").format(
						campo.get("label") or campo.get("id"), chiave
					),
				}
			)
			continue
		if not tipo.enabled:
			sbagliati.append(
				{
					"code": "consent_off",
					"field": campo.get("id"),
					"message": _("{0}: the consent {1} is switched off").format(
						campo.get("label") or campo.get("id"), tipo.label
					),
				}
			)
			continue
		campo["text"] = tipo.text
		campo["text_version"] = cint(tipo.text_version) or 1
	return sbagliati


# ------------------------------------------------------------------ reading


def _versioni(nome: str) -> list[dict]:
	return frappe.get_all(
		VERSIONE,
		filters={"template": nome},
		fields=[
			"name",
			"version",
			"published_on",
			"published_by",
			"asked_from",
			"notes",
			"schema_hash",
		],
		order_by="version desc",
	)


def _riga(modello) -> dict:
	schema = carica_schema(modello.schema)
	conteggio = {
		"sections": len(S.sezioni(schema)),
		"questions": sum(
			1 for campo in S.campi(schema) if (S.componente(campo.get("type")) or _NIENTE).risposta
		),
	}
	cambiata = True
	if modello.current_version:
		pubblicata = frappe.db.get_value(
			VERSIONE,
			modello.current_version,
			["schema_hash", "title", "use", "clinical", "specialty"],
			as_dict=True,
		)
		cambiata = not pubblicata or not _uguale_alla_versione(modello, schema, pubblicata)
	return {
		"name": modello.name,
		"title": modello.title,
		"use": modello.use,
		# where a form on the website is: /crm-form/<route>
		"route": modello.get("route") if uso(modello.use).sul_sito else None,
		"url": get_url(f"/crm-form/{modello.route}")
		if uso(modello.use).sul_sito and modello.get("route")
		else None,
		"enabled": modello.enabled,
		"clinical": modello.clinical,
		"specialty": modello.specialty,
		"current_version": modello.current_version,
		"current_version_number": modello.current_version_number,
		"published_on": modello.published_on,
		"modified": modello.modified,
		"unpublished_changes": cambiata,
		**conteggio,
	}


_NIENTE = S.Componente("", "", None, risposta=False)


def _da_pubblicare(modello, schema: dict) -> dict:
	"""The draft as a version would freeze it, consents' words included."""
	bozza = S.normalizza(schema)
	congela_consensi(bozza)
	return bozza


def _uguale_alla_versione(modello, schema: dict, pubblicata) -> bool:
	return S.impronta(_da_pubblicare(modello, schema)) == pubblicata.schema_hash and (
		modello.title,
		modello.use,
		cint(modello.clinical),
		modello.specialty or "",
	) == (pubblicata.title, pubblicata.use, cint(pubblicata.clinical), pubblicata.specialty or "")


@frappe.whitelist()
def get_templates() -> list[dict]:
	"""The templates the session builds: the centre's forms and sheets, the forms on
	the website, or both."""
	if not (livelli.puo("moduli.configura") or livelli.puo("moduli_lead.gestisci")):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return [
		_riga(modello)
		for modello in (
			frappe.get_doc(MODELLO, nome)
			for nome in frappe.get_all(MODELLO, pluck="name", order_by="modified desc")
		)
		if puo_costruire(modello.use)
	]


#: What a form on the website says and where it goes, besides its questions.
CAMPI_SITO = ("route", "button_label", "success_message", "success_url", "allowed_embedding_domains")


@frappe.whitelist()
def get_template(name: str) -> dict:
	modello = frappe.get_doc(MODELLO, name)
	verifica_uso(modello.use)
	schema = carica_schema(modello.schema)
	return {
		**_riga(modello),
		"description": modello.description,
		"ask_on": modello.ask_on,
		"services": [riga.service for riga in modello.services],
		"validity": modello.validity,
		"send_before": modello.send_before,
		**{campo: modello.get(campo) for campo in CAMPI_SITO},
		"schema": schema,
		"problems": problemi(schema) + problemi_dell_uso(schema, modello.use),
		"versions": _versioni(name),
		**_scelte(),
	}


def _usi_da_costruire() -> list[dict]:
	"""The uses the session builds, as the builder offers them."""
	return [
		{
			"value": voce.chiave,
			"label": _(voce.etichetta),
			"description": _(voce.descrizione),
			# given consents by the person; a sheet is written by the operator
			"for_the_person": voce.della_persona,
			# asked and sent: a form, not a sheet nor a form on the website
			"sent": voce.si_manda,
			"on_the_site": voce.sul_sito,
			# a survey: opened by its link alone, so it asks nothing to protect
			"without_code": voce.senza_codice,
		}
		for voce in usi()
		if puo_costruire(voce.chiave)
	]


@frappe.whitelist()
def get_uses() -> list[dict]:
	"""What a new template may be, for whoever builds one."""
	if not (livelli.puo("moduli.configura") or livelli.puo("moduli_lead.gestisci")):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return _usi_da_costruire()


def _scelte() -> dict:
	"""What the builder may offer on this site: the uses, the health data mark, the
	consents of the register and the services a form can be asked for."""
	from crm.moduli import consensi

	consensi.assicura_tipi()
	tipi = frappe.get_all(
		consensi.TIPO,
		filters={"enabled": 1},
		fields=["name", "label", "kind", "text", "plan_module"],
		order_by="creation asc",
	)
	return {
		"uses": _usi_da_costruire(),
		# the person's fields a question on the website may fill
		"person_fields": [
			{"value": chiave, "label": _(etichetta)} for chiave, etichetta in CAMPI_PERSONA.items()
		],
		"clinical_available": dato_clinico_disponibile(),
		"clinical_uses": [voce.chiave for voce in usi() if voce.clinico],
		# the lines of the patient's summary an answer may go to, where the clinic is on
		"summary_keys": [
			{"value": chiave, "label": _(etichetta)} for chiave, etichetta in voci_sintesi().items()
		]
		if dato_clinico_disponibile()
		else [],
		# the kinds, not anybody's answers: offering them tells nothing about a person
		"consent_types": [
			{"key": tipo.name, "label": _(tipo.label), "kind": tipo.kind, "text": tipo.text}
			for tipo in consensi._nel_piano(tipi)
		],
		"service_options": [
			{"value": servizio.name, "label": servizio.service_name or servizio.name}
			for servizio in frappe.get_all(
				"CRM Service",
				filters={"enabled": 1},
				fields=["name", "service_name"],
				order_by="service_name",
			)
		],
	}


@frappe.whitelist()
def get_version(name: str) -> dict:
	"""A published version, as people fill it."""
	versione = frappe.get_doc(VERSIONE, name)
	verifica_uso(versione.use)
	return {
		"name": versione.name,
		"template": versione.template,
		"version": versione.version,
		"title": versione.title,
		"use": versione.use,
		"clinical": versione.clinical,
		"specialty": versione.specialty,
		"published_on": versione.published_on,
		"asked_from": versione.asked_from,
		"notes": versione.notes,
		"schema": carica_schema(versione.schema),
		"schema_hash": versione.schema_hash,
	}


# ------------------------------------------------------------------ writing


_CAMPI_MODELLO = (
	"title",
	"description",
	"use",
	"clinical",
	"specialty",
	"ask_on",
	"validity",
	"send_before",
	"enabled",
	*CAMPI_SITO,
)


@frappe.whitelist(methods=["POST"])
def save_template(
	name: str | None = None,
	schema: dict | str | None = None,
	services: list | str | None = None,
	**campi,
) -> dict:
	"""Keep the draft. It may be half-written: what is still wrong comes back with
	it, and only publishing asks for it to be right."""
	modello = frappe.get_doc(MODELLO, name) if name else frappe.new_doc(MODELLO)
	if name:
		verifica_uso(modello.use)
	# the use it is becoming is the session's to build too
	verifica_uso(campi.get("use") or modello.use)
	for campo in _CAMPI_MODELLO:
		if campo in campi and campi[campo] is not None:
			modello.set(campo, campi[campo])
	if schema is not None:
		letto = carica_schema(schema) if isinstance(schema, str) else schema
		if not isinstance(letto, dict) or not isinstance(letto.get("sections"), list):
			frappe.throw(_("This is not a form"))
		modello.schema = json.dumps(letto, ensure_ascii=False)
	if services is not None:
		elenco = frappe.parse_json(services) if isinstance(services, str) else services
		modello.set("services", [{"service": servizio} for servizio in elenco or []])
	modello.save(ignore_permissions=True)
	return get_template(modello.name)


@frappe.whitelist(methods=["POST"])
def publish_template(name: str, notes: str | None = None, asked_from: str | None = None) -> dict:
	"""A new version, from the draft: frozen, with its hash and its consents' words.

	``asked_from`` is for a change that matters to whoever signed before (a new
	consent text): from that day they are asked to sign the new version.
	"""
	modello = frappe.get_doc(MODELLO, name)
	verifica_uso(modello.use)
	return get_version(pubblica(modello, notes, asked_from).name)


def pubblica(modello, notes: str | None = None, asked_from: str | None = None):
	"""The new version, once the draft is right; who may publish is the caller's
	business (`publish_template`, or a patch bringing forms from elsewhere)."""
	if not modello.enabled:
		frappe.throw(_("Switch the form on before publishing it"))
	schema = carica_schema(modello.schema)
	bozza = S.normalizza(schema)
	sbagliati = (
		problemi(bozza, per_pubblicare=True) + problemi_dell_uso(bozza, modello.use) + congela_consensi(bozza)
	)
	if sbagliati:
		frappe.throw(
			"<br>".join(frappe.utils.escape_html(problema["message"]) for problema in sbagliati[:10]),
			title=_("The form is not ready to publish"),
		)
	if modello.current_version:
		pubblicata = frappe.db.get_value(
			VERSIONE,
			modello.current_version,
			["schema_hash", "title", "use", "clinical", "specialty"],
			as_dict=True,
		)
		if pubblicata and _uguale_alla_versione(modello, schema, pubblicata):
			frappe.throw(_("Nothing changed since version {0}").format(modello.current_version_number))
	if asked_from and getdate(asked_from) < getdate():
		frappe.throw(_("A form is asked again from today on, not from the past"))
	return _nuova_versione(modello, modello, bozza, notes, asked_from)


def _nuova_versione(modello, fonte, schema: dict, notes: str | None = None, asked_from: str | None = None):
	"""The template's next version: ``schema`` frozen with its hash, the title, use
	and marks of ``fonte`` - the draft being published, or the version renewed."""
	numero = cint(modello.current_version_number) + 1
	versione = frappe.get_doc(
		{
			"doctype": VERSIONE,
			"template": modello.name,
			"version": numero,
			"title": fonte.title,
			"use": fonte.use,
			"clinical": fonte.clinical,
			"specialty": fonte.specialty,
			"published_on": now_datetime(),
			"published_by": frappe.session.user,
			"asked_from": asked_from or None,
			"notes": notes,
			"schema": json.dumps(schema, ensure_ascii=False),
			"schema_hash": S.impronta(schema),
		}
	).insert(ignore_permissions=True)
	modello.db_set(
		{
			"current_version": versione.name,
			"current_version_number": numero,
			"published_on": versione.published_on,
		}
	)
	return versione


def consensi_nella_lingua_del_centro() -> list[str]:
	"""A new version of every form whose consents were frozen on DottorCloud's words
	in another language than the centre's, with the register's words of today: a
	site set up in English froze its first forms in English. The draft is not
	touched, nobody who signed before is asked again, and words a centre wrote are
	never replaced. Returns the new versions."""
	from frappe.translate import print_language

	from crm import lingue
	from crm.moduli import consensi, registro

	lingua = lingue.del_centro()
	oggi = {
		riga.name: riga for riga in frappe.get_all(consensi.TIPO, fields=["name", "text", "text_version"])
	}
	nuove = []
	for riga in frappe.get_all(
		MODELLO, filters={"current_version": ("is", "set")}, fields=["name", "current_version"]
	):
		versione = frappe.get_doc(VERSIONE, riga.current_version)
		schema = carica_schema(versione.schema)
		rinnovata = False
		for campo in S.campi(schema):
			tipo = registro.tipo(campo.get("consent_type")) if campo.get("type") == "consent" else None
			adesso = oggi.get(tipo.chiave) if tipo else None
			tradotto = tipo and registro.testo_da_tradurre(tipo, campo.get("text"), lingua)
			# only when the register gives the very words the form should have had
			if not (adesso and tradotto and tradotto.strip() == (adesso.text or "").strip()):
				continue
			campo["text"] = adesso.text
			campo["text_version"] = cint(adesso.text_version) or 1
			rinnovata = True
		if rinnovata:
			with print_language(lingua):
				nota = _("The consents in the centre's language")
			nuove.append(_nuova_versione(frappe.get_doc(MODELLO, riga.name), versione, schema, nota).name)
	return nuove


def indirizzo_libero(base: str) -> str:
	"""``base``, or ``base-2``, ``base-3``...: the first no form on the website has."""
	candidato, numero = base, 1
	while frappe.db.exists(MODELLO, {"route": candidato, "use": SITO}):
		numero += 1
		candidato = f"{base}-{numero}"
	return candidato


@frappe.whitelist(methods=["POST"])
def duplicate_template(name: str) -> dict:
	originale = frappe.get_doc(MODELLO, name)
	verifica_uso(originale.use)
	copia = frappe.new_doc(MODELLO)
	for campo in _CAMPI_MODELLO:
		copia.set(campo, originale.get(campo))
	copia.title = _("Copy of {0}").format(originale.title)
	if copia.route:
		# an address is one form's
		copia.route = indirizzo_libero(f"{originale.route[:70]}-copy")
	copia.schema = originale.schema
	copia.set("services", [{"service": riga.service} for riga in originale.services])
	copia.insert(ignore_permissions=True)
	return get_template(copia.name)


@frappe.whitelist(methods=["POST"])
def delete_template(name: str) -> None:
	"""A draft never published goes; a published one is switched off instead, since
	what was signed on it points at it."""
	verifica_uso(frappe.db.get_value(MODELLO, name, "use"))
	frappe.delete_doc(MODELLO, name, ignore_permissions=True)
