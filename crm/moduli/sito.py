# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Forms on the centre's website (docs/gestionale-medico/design.md, "Il builder").

A template of the "Website" use is published at ``/crm-form/<route>``, embedded in
another site with ``?embed=1``, or placed in a page of the centre's own site
(`crm.api.site_render.crm_form_html`). Anybody fills it in, and what they send:

- finds the person by their email or mobile, as a booking does, or makes them
  (`crm.api.booking.find_or_create_person`: a family shares a contact, and the
  name says whose record it is);
- fills the person's fields its questions stand for, where they are empty: what
  a stranger types never overwrites what the centre knows;
- is kept as a form of theirs, on the version they saw, with its PDF;
- records the consents it asked, as given on the website;
- opens their deal, and tells the automations "Lead Form Submitted".

Nobody signs it and nobody is sent it; it records no health data, since whoever
sends it is nobody's patient yet.
"""

from __future__ import annotations

import json
import re

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import now_datetime

from crm.moduli import compilazioni, modelli, traccia
from crm.moduli import schema as S

MODULO = "CRM Form"
#: Where a form of the website was filled, on the form and in the consents' register.
CANALE = "Website"
#: Where the people a form of the website finds came from.
FONTE = "Web Form"
#: What a question may write on the person, at most: the length of their fields.
MAX_CAMPO = 140
#: The fields that find the person, or name them: the rest is only filled in.
TROVANO = ("full_name", "first_name", "last_name", "email", "mobile_no")


def indirizzo(valore: str | None) -> str:
	"""An address as the forms keep it: what the old forms had, "Contact_Us", is
	contact-us - the links and the pages of the site still find it."""
	testo = (valore or "").strip().strip("/").lower()
	return re.sub(r"[^a-z0-9-]+", "-", testo).strip("-")


def pubblicato(modello) -> bool:
	return bool(modello.enabled and modello.current_version)


def modello_del_sito(route: str | None, *, anteprima: bool = False):
	"""The template at ``route``: the published one, or a draft for whoever builds
	the website's forms and is trying it (``anteprima``). None when there is none
	to show."""
	chiave = indirizzo(route)
	if not chiave:
		return None
	nome = frappe.db.get_value(modelli.MODELLO, {"route": chiave, "use": modelli.SITO}, "name")
	if not nome:
		return None
	modello = frappe.get_doc(modelli.MODELLO, nome)
	if pubblicato(modello):
		return modello
	if anteprima and modelli.puo_costruire(modelli.SITO):
		return modello
	return None


def per_la_pagina(modello) -> dict:
	"""What a page draws: the published version's questions, or the draft's for
	whoever tries it before publishing."""
	if pubblicato(modello):
		versione = frappe.get_cached_doc(modelli.VERSIONE, modello.current_version)
		titolo, schema = versione.title, modelli.carica_schema(versione.schema)
	else:
		titolo, schema = modello.title, modelli.carica_schema(modello.schema)
	return {
		"route": modello.route,
		"title": titolo,
		"description": modello.description or "",
		"schema": schema,
		"button_label": modello.button_label or _("Send"),
		"success_message": modello.success_message or _("Thank you: the centre will be in touch soon."),
		"success_url": modello.success_url or "",
		"draft": not pubblicato(modello),
	}


# ------------------------------------------------------------------ the person


def la_persona(schema: dict, risposte: dict, visibili: dict) -> dict:
	"""What the answers say of the person: the fields their questions stand for,
	with the spaces tidied. A hidden question says nothing. Pure."""
	persona = {}
	for campo in S.campi(schema):
		chiave = campo.get("person")
		if chiave not in modelli.CAMPI_PERSONA or not visibili.get(campo.get("id")):
			continue
		valore = risposte.get(campo.get("id"))
		if isinstance(valore, str) and valore.strip():
			persona[chiave] = " ".join(valore.split())[:MAX_CAMPO]
	return persona


def nome_di(persona: dict) -> str:
	"""The name, in one box or in two. Pure."""
	if persona.get("full_name"):
		return persona["full_name"]
	return " ".join(parte for parte in (persona.get("first_name"), persona.get("last_name")) if parte)


def recapito(persona: dict) -> tuple[str, str]:
	"""The email and the mobile, checked: one of them at least, or the centre
	could not answer."""
	email = (persona.get("email") or "").strip().lower()
	if email and not frappe.utils.validate_email_address(email):
		frappe.throw(_("Please enter a valid email address"))
	telefono = (persona.get("mobile_no") or "").strip()
	if telefono:
		from crm.utils import to_e164

		telefono = to_e164(telefono) or telefono
	if not (email or telefono):
		frappe.throw(_("Leave an email or a mobile number, so that the centre can answer you"))
	return email, telefono


def _completa(lead: str, persona: dict) -> None:
	"""The other fields the questions stand for, where the person has none yet."""
	altri = {chiave: valore for chiave, valore in persona.items() if chiave not in TROVANO}
	if not altri:
		return
	doc = frappe.get_doc("CRM Lead", lead)
	vuoti = {chiave: valore for chiave, valore in altri.items() if not doc.get(chiave)}
	if not vuoti:
		return
	doc.update(vuoti)
	doc.flags.ignore_permissions = True
	doc.save()


def trova_o_crea(persona: dict, crm_vid: str | None = None, crm_sid: str | None = None) -> tuple[str, str]:
	"""``(the person the form is for, who owns the contact)``: the same person, or
	somebody the owner filled it in for - a child, a parent - with a record of
	their own (`crm.persone.collegate`)."""
	from crm.api.booking import find_or_create_person
	from crm.api.lead import find_person

	email, telefono = recapito(persona)
	lead = find_or_create_person(
		nome_di(persona),
		email,
		telefono,
		crm_vid=crm_vid,
		crm_sid=crm_sid,
		source=FONTE,
		medium="form",
		source_dimension="web_form",
		conversione=None,
	)
	return lead, find_person(email=email, phone=telefono) or lead


# ------------------------------------------------------------------ sending it


def manda(modello, risposte: dict, *, crm_vid: str | None = None, crm_sid: str | None = None) -> dict:
	"""The form sent from the website: checked on the version published, kept as
	the person's, their consents and their deal. What it made, by name."""
	versione = frappe.get_doc(modelli.VERSIONE, modello.current_version)
	schema = modelli.carica_schema(versione.schema)
	puliti, stato = compilazioni.controlla(schema, risposte, senza_firme=True)
	persona = la_persona(schema, puliti, stato["visible"])
	lead, titolare = trova_o_crea(persona, crm_vid, crm_sid)
	_completa(lead, persona)

	doc = frappe.get_doc(
		{
			"doctype": MODULO,
			"lead": lead,
			"template": modello.name,
			"template_version": versione.name,
			"version": versione.version,
			"title": versione.title,
			"clinical": 0,
			"channel": CANALE,
			# filled in by whoever owns the contact, for somebody of theirs
			"given_by": titolare if titolare != lead else None,
			"schema_hash": versione.schema_hash,
			"answers": "{}",
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert()
	traccia.traccia(MODULO, doc.name, "created", _("Version {0}").format(versione.version))
	compilazioni._chiudi(
		doc,
		schema,
		puliti,
		stato,
		[],
		compilazioni.impronta_risposte(versione.schema_hash, puliti),
		now_datetime(),
		ignora_permessi=True,
		evento="sent_from_website",
		fai_il_pdf=_pdf_dopo,
	)

	from crm.api.lead import open_deal_for_inquiry
	from crm.api.tracking import record_conversion

	# the visit that led here is the one of whoever owns the contact
	record_conversion(frappe.get_doc("CRM Lead", titolare), "form_submit", versione.title, reference=doc)
	trattativa = open_deal_for_inquiry(lead, source=FONTE)
	_annuncia(lead, modello.name, doc.name)
	return {"lead": lead, "form": doc.name, "deal": trattativa}


def _pdf_dopo(doc) -> None:
	"""The PDF is made once the answer went back: whoever sent it does not wait."""
	frappe.enqueue(
		"crm.moduli.sito.fai_il_pdf", modulo=doc.name, enqueue_after_commit=True, now=frappe.in_test
	)


def fai_il_pdf(modulo: str) -> None:
	from crm.moduli import pdf

	pdf.genera_e_allega(frappe.get_doc(MODULO, modulo))


def _annuncia(lead: str, modello: str, modulo: str) -> None:
	"""The automations hear a form was filled in, whoever filled it: a person the
	centre knows for years as well as a new one. A failure there loses nothing."""
	try:
		from crm.automation.engine import process_event

		process_event(
			"form_submitted",
			frappe.get_doc("CRM Lead", lead),
			{"form_template": modello, "form": modulo, "source": FONTE},
		)
	except Exception:
		frappe.log_error(title=f"Website form {modulo}: automations failed", message=frappe.get_traceback())


def _leggi(answers) -> dict:
	if isinstance(answers, dict):
		return answers
	try:
		valore = json.loads(answers or "{}")
	except ValueError:
		frappe.throw(_("The answers could not be read"))
	if not isinstance(valore, dict):
		frappe.throw(_("The answers could not be read"))
	return valore


# nosemgrep: guest-whitelisted-method — a published form is for anybody; 10/h an address, a robot trap
@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=10, seconds=60 * 60)
def submit_site_form(
	route: str,
	answers: str | dict,
	crm_vid: str | None = None,
	crm_sid: str | None = None,
	website: str | None = None,
) -> dict:
	"""Anybody sends the form published at ``route``. The answer says only that it
	went: who the person is stays with the centre."""
	modello = modello_del_sito(route)
	if not modello or not pubblicato(modello):
		frappe.throw(_("This form is not on the website"), frappe.DoesNotExistError)
	if (website or "").strip():
		# a box nobody sees: only a robot fills it in, and hears it went
		return {"sent": True}
	manda(modello, _leggi(answers), crm_vid=crm_vid, crm_sid=crm_sid)
	return {"sent": True}


@frappe.whitelist(methods=["POST"])
def try_site_form(route: str, answers: str | dict) -> dict:
	"""Whoever builds the website's forms tries a draft on its page: the answers are
	checked as the published form checks them, and nothing is kept."""
	modelli.verifica_uso(modelli.SITO)
	modello = modello_del_sito(route, anteprima=True)
	if not modello:
		frappe.throw(_("There is no form at this address"), frappe.DoesNotExistError)
	schema = per_la_pagina(modello)["schema"]
	puliti, stato = compilazioni.controlla(schema, _leggi(answers), senza_firme=True)
	recapito(la_persona(schema, puliti, stato["visible"]))
	return {"tried": True}
