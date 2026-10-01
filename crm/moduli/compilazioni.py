# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Filling and signing a form: the person's forms, from the draft to the PDF.

A form (`CRM Form`) is filled on a published version, which never changes. While it
is a draft the answers can be saved half-way; signing is the one step that asks
for everything at once, the way the server's own rules say (`crm.moduli.schema`):

1. the answers are cleaned and checked, and nothing required may be missing;
2. each signature is kept as the picture of the stroke, with who, as what, when by
   the server's clock, from which address and device, and the hash of the answers
   it was put on (design.md, "Le prove di ogni firma");
3. the form is submitted: from now on it is not rewritten;
4. the PDF/A is made, once, with its evidence page, and its hash kept;
5. every consent it asked goes into the register, with the words it was given on
   and the form it came from.

Every step leaves an event in the form's register (`crm.moduli.traccia`).

**Who sees a person's forms**: whoever sees the person (`moduli.vedi`), like their
consents. A form that records health data is for the care team only: the clinic
says who that is (`registra_lettore_clinico`); without the clinic there are none.

Signing is the same wherever it happens (`firma`): on the operator's screen here,
and on the desk's tablet or from a link at home through `crm.moduli.richieste`,
where nobody is logged in and only the person's own simple signature is given.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
from collections.abc import Callable

import frappe
from frappe import _
from frappe.utils import cint, get_datetime, get_fullname, now_datetime

from crm.moduli import modelli, traccia
from crm.moduli import schema as S
from crm.permissions import livelli, org_hierarchy

MODULO = "CRM Form"
RICHIESTA = "CRM Form Request"
#: How the register names the channel a form was filled on.
CANALE_DEL_REGISTRO = {
	"At the desk": "At the desk",
	"Tablet": "At the desk",
	"Link": "Web form",
	"On paper": "On paper",
	# a form on the centre's website (`crm.moduli.sito`)
	"Website": "Web form",
}
#: A PNG a finger draws is a few kilobytes: anything this big is not one.
MAX_FIRMA = 400 * 1024
_PNG = b"\x89PNG\r\n\x1a\n"

_lettori_clinici: list[Callable[[str | None], bool]] = []


def registra_lettore_clinico(legge: Callable[[str | None], bool]) -> None:
	"""The clinic says who reads forms that record health data."""
	if legge not in _lettori_clinici:
		_lettori_clinici.append(legge)


def legge_dati_clinici(user: str | None = None) -> bool:
	from crm.registrazione import carica

	# the modules register once per process: asked before a request did, it has to
	carica()
	return any(legge(user) for legge in _lettori_clinici)


# ------------------------------------------------------------------ who sees them


def has_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	if cint(doc.get("clinical")) and not legge_dati_clinici(user):
		return False
	if not doc.get("lead"):
		return True
	return bool(frappe.has_permission("CRM Lead", "read", doc=doc.get("lead"), user=user))


def get_permission_query_conditions(user: str | None = None) -> str:
	"""A person's forms follow the person; health data only for the care team."""
	return condizioni_per(MODULO, user)


def condizioni_per(doctype: str, user: str | None = None) -> str:
	"""The rows of ``doctype`` - with a person (`lead`) and a health data mark
	(`clinical`) - the user sees: the forms, and the requests to fill them."""
	moduli = frappe.qb.DocType(doctype)
	condizioni = []
	visibili = org_hierarchy.visible_leads(user)
	if visibili is not None:
		condizioni.append(moduli.lead.isin(visibili))
	if not legge_dati_clinici(user):
		condizioni.append(moduli.clinical == 0)
	if not condizioni:
		return ""
	condizione = condizioni[0]
	for altra in condizioni[1:]:
		condizione = condizione & altra
	return condizione.get_sql(with_namespace=True, quote_char="`", secondary_quote_char="'")


# ------------------------------------------------------------------ reading

#: How a link was sent and opened: part of the evidence of what it signed.
ACCESSI = ("sent", "opened", "code_sent", "code_verified")


def eventi_del_modulo(doc) -> list[dict]:
	"""The form's events and, for one filled from a link or on the tablet, how
	its link was sent and opened (design.md, "Le prove di ogni firma")."""
	eventi = list(traccia.eventi(MODULO, doc.name))
	if doc.get("request"):
		capo = frappe.db.get_value(RICHIESTA, doc.request, "via") or doc.request
		eventi += [evento for evento in traccia.eventi(RICHIESTA, capo) if evento.event in ACCESSI]
	return sorted(eventi, key=lambda evento: get_datetime(evento.occurred_on))


def riconoscimento(doc) -> str:
	"""How whoever signed was known: the operator at the desk, the tablet the
	operator handed over, or a link and a code."""
	if doc.get("request"):
		richiesta = frappe.db.get_value(
			RICHIESTA, doc.request, ["channel", "sent_by", "sent_to"], as_dict=True
		)
		if richiesta and richiesta.channel == "Tablet":
			return _("On the desk's tablet, handed over by {0}").format(get_fullname(richiesta.sent_by))
		if richiesta:
			return _("From a link sent to {0}, opened with a code sent to the same address").format(
				richiesta.sent_to
			)
	if doc.get("paper_file"):
		return _("On paper, in front of {0}, who attested the scan is a true copy of the original").format(
			get_fullname(doc.attested_by)
		)
	if doc.get("provider") and doc.get("provider_status") == "Signed":
		return _("By {0}, the signature provider, with its own identification").format(doc.provider)
	if doc.channel == "Website":
		return _("On the centre's website, by whoever filled it in: the contact they left was not checked")
	if doc.filled_by:
		return _("At the desk, with {0}").format(get_fullname(doc.filled_by))
	return _("At the desk")


def _fornitore_per_la_pagina() -> dict | None:
	from crm.moduli import firme

	fornitore = firme.attivo()
	return {"name": fornitore.nome, "levels": list(fornitore.livelli)} if fornitore else None


def _versione(doc):
	return frappe.get_cached_doc(modelli.VERSIONE, doc.template_version)


def _risposte(doc) -> dict:
	if isinstance(doc.answers, dict):
		return doc.answers
	try:
		return json.loads(doc.answers or "{}") or {}
	except ValueError:
		return {}


def _riga(doc) -> dict:
	avvisi = json.loads(doc.alerts or "[]") if isinstance(doc.alerts, str) else (doc.alerts or [])
	return {
		"name": doc.name,
		"title": doc.title,
		"version": doc.version,
		"template": doc.template,
		# a form the person fills, or a sheet the operator writes
		"use": modelli.uso(frappe.get_cached_value(modelli.VERSIONE, doc.template_version, "use")).chiave,
		"clinical": doc.clinical,
		"channel": doc.channel,
		"docstatus": doc.docstatus,
		"signed_on": doc.signed_on,
		"modified": doc.modified,
		"filled_by": doc.filled_by,
		"filled_by_name": get_fullname(doc.filled_by) if doc.filled_by else None,
		"request": doc.get("request"),
		"alerts": avvisi,
		"pdf_file": doc.pdf_file,
	}


#: What is filled at the desk: the person's forms, and the operator's sheets.
DAL_BANCO = (modelli.FORMA, modelli.SCHEDA)


def _modelli_da_compilare() -> list[dict]:
	"""The published forms the session may have somebody fill, and the sheets it may
	write for them. A sheet with health data is written in the clinical record."""
	clinico = legge_dati_clinici()
	return [
		riga
		for riga in frappe.get_all(
			modelli.MODELLO,
			filters={"enabled": 1, "current_version": ("is", "set"), "use": ("in", DAL_BANCO)},
			fields=["name", "title", "use", "clinical", "specialty", "current_version_number"],
			order_by="title asc",
		)
		if (clinico or not riga.clinical) and not (riga.use == modelli.SCHEDA and riga.clinical)
	]


@frappe.whitelist()
def get_person_forms(lead: str) -> dict:
	"""A person's forms, newest first, and what may be filled for them now."""
	livelli.verifica_nel_crm("moduli.vedi")
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	moduli = [
		_riga(frappe.get_doc(MODULO, nome))
		for nome in frappe.get_list(MODULO, filters={"lead": lead}, pluck="name", order_by="modified desc")
	]
	puo_compilare = livelli.puo("moduli.compila")
	from crm.moduli import dovuti

	return {
		"forms": moduli,
		"can_fill": puo_compilare,
		"templates": _modelli_da_compilare() if puo_compilare else [],
		# what the person owes, for their next appointment or in general
		"due": dovuti.della_persona(lead),
	}


@frappe.whitelist()
def get_form(name: str) -> dict:
	doc = frappe.get_doc(MODULO, name)
	doc.check_permission("read")
	versione = _versione(doc)
	persona = frappe.db.get_value("CRM Lead", doc.lead, ["lead_name", "first_name"], as_dict=True) or {}
	return {
		**_riga(doc),
		"lead": doc.lead,
		"lead_name": persona.get("lead_name"),
		"given_by": doc.given_by,
		"given_by_name": frappe.db.get_value("CRM Lead", doc.given_by, "lead_name") if doc.given_by else None,
		"appointment": doc.appointment,
		"schema": modelli.carica_schema(versione.schema),
		"schema_hash": versione.schema_hash,
		"answers": _risposte(doc),
		"answers_hash": doc.answers_hash,
		"pdf_hash": doc.pdf_hash,
		"pdf_conformance": doc.pdf_conformance,
		"signatures": [
			{
				"field": riga.field,
				"signer": riga.signer,
				"signer_name": riga.signer_name,
				"level": riga.level,
				"method": riga.method,
				"signed_at": riga.signed_at,
				"image": riga.image,
			}
			for riga in doc.signatures
		],
		"events": eventi_del_modulo(doc) if doc.docstatus else [],
		"recognised": riconoscimento(doc),
		"provider": _fornitore_per_la_pagina(),
		"provider_name": doc.get("provider"),
		"provider_status": doc.get("provider_status"),
		"paper": {
			"file": doc.paper_file,
			"sha256": doc.paper_hash,
			"attested_by": get_fullname(doc.attested_by) if doc.attested_by else None,
			"attested_on": doc.attested_on,
		}
		if doc.get("paper_file")
		else None,
		"can_sign": doc.docstatus == 0 and livelli.puo("moduli.compila"),
	}


# ------------------------------------------------------------------ writing


def _bozza(nome: str):
	livelli.verifica("moduli.compila")
	doc = frappe.get_doc(MODULO, nome)
	doc.check_permission("write")
	if doc.docstatus != 0:
		frappe.throw(_("This form is signed: it is not changed any more"))
	if doc.get("provider_status") == "Sent":
		frappe.throw(
			_("This form is with {0} for its signatures: wait for them, or take it back").format(doc.provider)
		)
	return doc


@frappe.whitelist(methods=["POST"])
def start_form(
	lead: str,
	template: str,
	appointment: str | None = None,
	given_by: str | None = None,
	channel: str = "At the desk",
) -> dict:
	"""A new form for a person, on the template's current version."""
	livelli.verifica("moduli.compila")
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	modello = frappe.get_doc(modelli.MODELLO, template)
	if not modello.enabled or not modello.current_version:
		frappe.throw(_("{0} is not published").format(frappe.bold(modello.title)))
	uso = modelli.uso(modello.use).chiave
	if uso not in DAL_BANCO or (uso == modelli.SCHEDA and modello.clinical):
		frappe.throw(
			_("{0} is not a form to fill: it is written in the clinical record").format(modello.title)
		)
	if uso == modelli.SCHEDA:
		# the operator's, written at the desk: never a link, never the tablet
		channel = "At the desk"
	versione = frappe.get_doc(modelli.VERSIONE, modello.current_version)
	if versione.clinical and not legge_dati_clinici():
		frappe.throw(_("This form records health data: it is for the care team"), frappe.PermissionError)
	if given_by and given_by == lead:
		given_by = None
	doc = frappe.get_doc(
		{
			"doctype": MODULO,
			"lead": lead,
			"template": modello.name,
			"template_version": versione.name,
			"version": versione.version,
			"title": versione.title,
			"clinical": versione.clinical,
			"channel": channel,
			"appointment": appointment,
			"given_by": given_by,
			"filled_by": frappe.session.user,
			"schema_hash": versione.schema_hash,
			"answers": "{}",
		}
	).insert()
	traccia.traccia(MODULO, doc.name, "created", _("Version {0}").format(versione.version))
	return get_form(doc.name)


def _leggi(valore):
	return frappe.parse_json(valore) if isinstance(valore, str) else valore


@frappe.whitelist(methods=["POST"])
def save_answers(name: str, answers: dict | str) -> dict:
	"""Keep the answers so far: a draft may be finished later. Only what converts
	is kept; what does not comes back as a problem to fix."""
	doc = _bozza(name)
	schema = modelli.carica_schema(_versione(doc).schema)
	risposte = _leggi(answers) or {}
	puliti, errori, _stato = S.pulisci(schema, _senza_firme(schema, risposte))
	doc.answers = json.dumps(puliti, ensure_ascii=False)
	doc.save()
	return {"answers": puliti, "problems": [errore.come_dict(_) for errore in errori]}


def _campi_firma(schema: dict) -> list[dict]:
	return [campo for campo in S.campi(schema) if campo.get("type") == "signature"]


def _senza_firme(schema: dict, risposte: dict) -> dict:
	"""A signature is not an answer to save: it is taken when the form is signed."""
	firme = {campo.get("id") for campo in _campi_firma(schema)}
	return {chiave: valore for chiave, valore in (risposte or {}).items() if chiave not in firme}


def impronta_risposte(schema_hash: str, risposte: dict) -> str:
	"""What a signature is put on: the version's questions and these answers."""
	contenuto = {"schema_hash": schema_hash, "answers": risposte}
	return hashlib.sha256(S.canonico(contenuto).encode("utf-8")).hexdigest()


def _png(dati_url: str, etichetta: str) -> bytes:
	"""The stroke, as the browser drew it: a PNG, and small."""
	prefisso = "data:image/png;base64,"
	if not isinstance(dati_url, str) or not dati_url.startswith(prefisso):
		frappe.throw(_("{0}: the signature is not a picture").format(etichetta))
	try:
		contenuto = base64.b64decode(dati_url[len(prefisso) :], validate=True)
	except (binascii.Error, ValueError):
		frappe.throw(_("{0}: the signature is not a picture").format(etichetta))
	if not contenuto.startswith(_PNG) or len(contenuto) > MAX_FIRMA:
		frappe.throw(_("{0}: the signature is not a picture").format(etichetta))
	return contenuto


def _veste(campo: dict, doc) -> str:
	"""As what a signature field is signed. When somebody answers for the person
	(a parent, a guardian), the person's own signature is theirs to give."""
	veste = campo.get("signer") or "patient"
	return "guardian" if veste == "patient" and doc.given_by else veste


def _firmatario(campo: dict, doc, operatore: str | None = None) -> tuple[str, str | None, str | None]:
	"""Who signs a signature field: its name, and the user or the person it is.
	The operator is whoever is at the desk, unless named (a provider's webhook
	comes with nobody logged in)."""
	veste = _veste(campo, doc)
	if veste == "operator":
		operatore = operatore or frappe.session.user
		return get_fullname(operatore), operatore, None
	if veste == "guardian":
		if not doc.given_by:
			frappe.throw(
				_("{0}: say which parent or guardian signs, in Answered by").format(campo.get("label"))
			)
		return frappe.db.get_value("CRM Lead", doc.given_by, "lead_name"), None, doc.given_by
	return doc.lead_name or frappe.db.get_value("CRM Lead", doc.lead, "lead_name"), None, doc.lead


def _richiesta() -> tuple[str | None, str | None]:
	richiesta = getattr(frappe.local, "request", None)
	if not richiesta:
		return None, None
	return getattr(frappe.local, "request_ip", None), (richiesta.headers.get("User-Agent") or "")[
		:500
	] or None


@frappe.whitelist(methods=["POST"])
def sign_form(
	name: str,
	answers: dict | str,
	signatures: dict | str,
	given_by: str | None = None,
) -> dict:
	"""Check everything, keep the signatures, submit, make the PDF, record the
	consents. ``signatures`` maps each signature field to the PNG of its stroke."""
	doc = _bozza(name)
	if given_by is not None:
		doc.given_by = None if given_by in ("", doc.lead) else given_by
	firma(doc, _leggi(answers) or {}, _leggi(signatures) or {})
	return get_form(doc.name)


def _controlla(schema: dict, risposte: dict, tratti: dict, *, senza_firme: bool = False) -> tuple[dict, dict]:
	"""The answers cleaned, and the state they give; throws on what is wrong or
	missing. ``senza_firme`` leaves the signatures for later: a form filled away
	from the desk and signed at it."""
	firme = {campo.get("id") for campo in _campi_firma(schema)}
	risposte = _senza_firme(schema, risposte)
	# a signature counts as an answer for what is required and what shows
	for chiave in firme:
		if tratti.get(chiave):
			risposte[chiave] = "signed"
	puliti, errori, stato = S.pulisci(schema, risposte)
	if errori:
		frappe.throw("<br>".join(frappe.utils.escape_html(e.testo(_)) for e in errori[:10]))
	mancanti = [chiave for chiave in stato["missing"] if not (senza_firme and chiave in firme)]
	if mancanti:
		etichette = {campo.get("id"): campo.get("label") or campo.get("id") for campo in S.campi(schema)}
		frappe.throw(
			_("Still to answer: {0}").format(", ".join(etichette[chiave] for chiave in mancanti)),
			title=_("The form is not complete"),
		)
	return {chiave: valore for chiave, valore in puliti.items() if chiave not in firme}, stato


def controlla(schema: dict, risposte: dict, *, senza_firme: bool = True) -> tuple[dict, dict]:
	"""The answers cleaned and checked as signing asks, and the state they give:
	a form's, or a clinical sheet's the practitioner signs by signing the visit."""
	return _controlla(schema, risposte, {}, senza_firme=senza_firme)


def firma(doc, risposte: dict, tratti: dict, *, da_solo: bool = False) -> None:
	"""Sign a draft: check everything, keep the signatures, submit, make the PDF,
	record the consents. ``tratti`` maps each signature field to its PNG.

	``da_solo`` is the person signing on their own, on the desk's tablet or from a
	link: nobody is logged in, the link was the permission, and only their own
	simple signature can be given - the operator's is given at the desk.
	"""
	versione = _versione(doc)
	schema = modelli.carica_schema(versione.schema)
	risposte_firmate, stato = _controlla(schema, risposte, tratti)

	firme_visibili = _firme_visibili(schema, stato)
	for campo in firme_visibili:
		if da_solo and (campo.get("signer") or "patient") == "operator":
			frappe.throw(_("{0} is signed by the operator, at the desk").format(campo.get("label")))
		if tratti.get(campo.get("id")) and (campo.get("level") or "simple") != "simple":
			# the template chose the level; a stroke on the screen is not an advanced
			# signature, and pretending it is would be worse than not signing
			frappe.throw(
				_(
					"{0} asks for an {1} signature: it is signed with a signature provider, or on paper"
				).format(campo.get("label"), _(campo.get("level")))
			)

	impronta = impronta_risposte(versione.schema_hash, risposte_firmate)
	ip, dispositivo = _richiesta()
	adesso = now_datetime()

	righe = []
	for campo in firme_visibili:
		chiave = campo.get("id")
		if not tratti.get(chiave):
			continue
		contenuto = _png(tratti[chiave], campo.get("label") or chiave)
		chi, utente, persona = _firmatario(campo, doc)
		immagine = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": f"{doc.name}-{chiave}.png",
				"attached_to_doctype": MODULO,
				"attached_to_name": doc.name,
				"is_private": 1,
				"content": contenuto,
			}
		).insert(ignore_permissions=True)
		righe.append(
			{
				"field": chiave,
				"signer": _veste(campo, doc),
				"signer_name": chi,
				"signer_user": utente,
				"signer_lead": persona,
				"level": "simple",
				"method": "Drawn",
				"image": immagine.file_url,
				"signed_at": adesso,
				"ip_address": ip,
				"user_agent": dispositivo,
				"document_hash": impronta,
			}
		)

	_chiudi(doc, schema, risposte_firmate, stato, righe, impronta, adesso, ignora_permessi=da_solo)


def _chiudi(
	doc,
	schema: dict,
	risposte_firmate: dict,
	stato: dict,
	righe: list[dict],
	impronta: str,
	adesso,
	*,
	ignora_permessi: bool = False,
	dettagli: dict | None = None,
	fai_il_pdf: Callable | None = None,
	evento: str = "signed",
) -> None:
	"""How every signature ends, however it was given: the form closed on the
	answers it was signed on, its register, its request, its PDF, its consents.
	``fai_il_pdf`` is for a PDF that is not ours to make (a provider's), or not
	now; ``evento`` for a form nobody signs (one sent from the website)."""
	doc.answers = json.dumps(risposte_firmate, ensure_ascii=False)
	doc.alerts = json.dumps(stato["stops"], ensure_ascii=False)
	doc.answers_hash = impronta
	doc.signed_on = adesso
	doc.set("signatures", righe)
	if ignora_permessi:
		# the link, the code and the session - or the provider's signed call - are the permission
		doc.flags.ignore_permissions = True
	doc.submit()
	traccia.traccia(
		MODULO,
		doc.name,
		evento,
		", ".join(riga["signer_name"] or "" for riga in righe),
		{
			"answers_hash": impronta,
			"signatures": [[r["field"], r["signer"], r["level"]] for r in righe],
			"channel": doc.channel,
			**(dettagli or {}),
		},
	)
	if doc.get("request"):
		# the request it came from is answered, wherever it was signed
		frappe.db.set_value(RICHIESTA, doc.request, {"status": "Signed", "signed_on": adesso})

	if fai_il_pdf:
		fai_il_pdf(doc)
	else:
		from crm.moduli import pdf

		pdf.genera_e_allega(doc)
	_registra_consensi(doc, schema, risposte_firmate, stato)


def _firme_visibili(schema: dict, stato: dict) -> list[dict]:
	return [campo for campo in _campi_firma(schema) if stato["visible"].get(campo.get("id"))]


# ------------------------------------------------------------------ on paper

#: What a scan may be: the first bytes of each kind.
SCANSIONI = {"pdf": b"%PDF", "png": _PNG, "jpg": b"\xff\xd8\xff", "jpeg": b"\xff\xd8\xff"}
MAX_SCANSIONE = 20 * 1024 * 1024


def _scansione(doc, file_url: str | None):
	"""The scan of the signed paper: uploaded to this form, private, a PDF or a
	picture, and not too big."""
	nome = (
		frappe.db.get_value(
			"File",
			{"file_url": file_url, "attached_to_doctype": MODULO, "attached_to_name": doc.name},
			"name",
		)
		if file_url
		else None
	)
	if not nome:
		frappe.throw(_("Upload the scan of the signed paper to this form"))
	file = frappe.get_doc("File", nome)
	if not file.is_private:
		frappe.throw(_("The scan of a signed form is kept private: upload it again as private"))
	contenuto = file.get_content(encodings=[])
	if isinstance(contenuto, str):
		contenuto = contenuto.encode()
	inizio = SCANSIONI.get((file.file_name or "").rsplit(".", 1)[-1].lower())
	if not inizio or not contenuto.startswith(inizio):
		frappe.throw(_("The scan is a PDF, a JPG or a PNG"))
	if len(contenuto) > MAX_SCANSIONE:
		frappe.throw(_("The scan is too big: at most {0} MB").format(MAX_SCANSIONE // (1024 * 1024)))
	return file, contenuto


def firma_su_carta(doc, risposte: dict, scansione: str) -> None:
	"""Signed on paper, in front of the operator: the answers as typed are
	checked, the scan is kept inside the PDF/A with its SHA-256, and the operator
	attests it is a true copy of the original (design.md, "Su carta")."""
	versione = _versione(doc)
	schema = modelli.carica_schema(versione.schema)
	risposte_firmate, stato = _controlla(schema, risposte, {}, senza_firme=True)
	file, contenuto = _scansione(doc, scansione)
	impronta_scansione = hashlib.sha256(contenuto).hexdigest()
	impronta = impronta_risposte(versione.schema_hash, risposte_firmate)
	ip, dispositivo = _richiesta()
	adesso = now_datetime()
	righe = []
	for campo in _firme_visibili(schema, stato):
		chi, utente, persona = _firmatario(campo, doc)
		righe.append(
			{
				"field": campo.get("id"),
				"signer": _veste(campo, doc),
				"signer_name": chi,
				"signer_user": utente,
				"signer_lead": persona,
				# a handwritten signature is its own thing: whatever level the field asked
				"level": "handwritten",
				"method": "On paper",
				"signed_at": adesso,
				"ip_address": ip,
				"user_agent": dispositivo,
				"document_hash": impronta,
			}
		)
	file.db_set("attached_to_field", "paper_file")
	doc.channel = "On paper"
	doc.paper_file = file.file_url
	doc.paper_hash = impronta_scansione
	doc.attested_by = frappe.session.user
	doc.attested_on = adesso
	traccia.traccia(
		MODULO,
		doc.name,
		"attested",
		get_fullname(frappe.session.user),
		{"scan_sha256": impronta_scansione, "bytes": len(contenuto)},
	)
	_chiudi(
		doc,
		schema,
		risposte_firmate,
		stato,
		righe,
		impronta,
		adesso,
		dettagli={"method": "On paper", "scan_sha256": impronta_scansione},
	)


@frappe.whitelist(methods=["POST"])
def sign_on_paper(
	name: str, answers: dict | str, scan: str, attest: int | str = 0, given_by: str | None = None
) -> dict:
	"""The form signed on paper: the answers, the scan, and the operator's word
	that the scan is a true copy of the original signed in front of them."""
	doc = _bozza(name)
	if not cint(attest):
		frappe.throw(_("Attest that the scan is a true copy of the original signed in front of you"))
	if given_by is not None:
		doc.given_by = None if given_by in ("", doc.lead) else given_by
	firma_su_carta(doc, _leggi(answers) or {}, scan)
	return get_form(doc.name)


@frappe.whitelist(methods=["GET"])
def printable_form(name: str) -> None:
	"""The form to sign on paper, as filled so far: printed, not kept."""
	doc = _bozza(name)
	from crm.moduli import pdf

	contenuto = pdf.da_firmare(doc)
	# a GET is not committed unless asked: the printing is part of the register
	frappe.local.flags.commit = True
	traccia.traccia(MODULO, doc.name, "printed", _("To sign on paper"))
	frappe.local.response.filename = f"{doc.name}.pdf"
	frappe.local.response.filecontent = contenuto
	frappe.local.response.type = "download"


# ------------------------------------------------------------------ with a provider


def _recapiti(campo: dict, doc, operatore: str | None) -> dict:
	"""Where a provider reaches a signer: their email and mobile."""
	veste = _veste(campo, doc)
	if veste == "operator":
		return {
			"email": frappe.db.get_value("User", operatore or frappe.session.user, "email"),
			"phone": None,
		}
	persona = doc.given_by if veste == "guardian" else doc.lead
	valori = frappe.db.get_value("CRM Lead", persona, ["email", "mobile_no", "phone"], as_dict=True) or {}
	return {"email": valori.get("email"), "phone": valori.get("mobile_no") or valori.get("phone")}


@frappe.whitelist(methods=["POST"])
def send_to_provider(name: str, answers: dict | str, given_by: str | None = None) -> dict:
	"""The form to the centre's signature provider: the answers are checked and
	frozen, the PDF to sign goes to the provider, and the form waits for its
	webhook. ``signers`` are where each one signs."""
	from crm.moduli import firme, pdf

	doc = _bozza(name)
	fornitore = firme.attivo() or firme.nessun_fornitore()
	if given_by is not None:
		doc.given_by = None if given_by in ("", doc.lead) else given_by
	versione = _versione(doc)
	schema = modelli.carica_schema(versione.schema)
	risposte_firmate, stato = _controlla(schema, _leggi(answers) or {}, {}, senza_firme=True)
	visibili = _firme_visibili(schema, stato)
	for campo in visibili:
		livello = campo.get("level") or "simple"
		if livello != "simple" and livello not in fornitore.livelli:
			frappe.throw(_("{0} does not give {1} signatures").format(fornitore.nome, _(livello)))
	doc.answers = json.dumps(risposte_firmate, ensure_ascii=False)
	doc.alerts = json.dumps(stato["stops"], ensure_ascii=False)
	doc.answers_hash = impronta_risposte(versione.schema_hash, risposte_firmate)
	doc.save()

	contenuto = pdf.da_firmare(doc)
	firmatari = []
	for campo in visibili:
		chi, _utente, _persona = _firmatario(campo, doc)
		firmatari.append(
			{
				"field": campo.get("id"),
				"label": campo.get("label"),
				"signer": _veste(campo, doc),
				"name": chi,
				"level": campo.get("level") or "simple",
				**_recapiti(campo, doc, None),
			}
		)
	busta = fornitore.crea(doc, contenuto, firmatari)
	doc.db_set(
		{"provider": fornitore.nome, "provider_reference": busta["reference"], "provider_status": "Sent"}
	)
	traccia.traccia(
		MODULO,
		doc.name,
		"provider_sent",
		fornitore.nome,
		{"reference": busta["reference"], "pdf_sha256": hashlib.sha256(contenuto).hexdigest()},
	)
	return {**get_form(doc.name), "signers": busta.get("signers") or []}


@frappe.whitelist()
def provider_links(name: str) -> list[dict]:
	"""Where each signer of a form at the provider signs: a link can be asked again."""
	from crm.moduli import firme

	doc = frappe.get_doc(MODULO, name)
	doc.check_permission("read")
	# a form already sent is signed where it went, even after the module ended
	fornitore = firme.attivo(nuove=False)
	if doc.docstatus != 0 or doc.provider_status != "Sent" or not fornitore or fornitore.nome != doc.provider:
		return []
	schema = modelli.carica_schema(_versione(doc).schema)
	stato = S.valuta(schema, _risposte(doc))
	return [
		{
			"field": campo.get("id"),
			"label": campo.get("label"),
			"url": fornitore.pagina(doc.provider_reference, campo.get("id")),
		}
		for campo in _firme_visibili(schema, stato)
	]


@frappe.whitelist(methods=["POST"])
def take_back_from_provider(name: str) -> dict:
	"""The form back from the provider, unsigned: it can be changed again. What
	the provider still has is not signed here any more."""
	livelli.verifica("moduli.compila")
	doc = frappe.get_doc(MODULO, name)
	doc.check_permission("write")
	if doc.docstatus != 0 or doc.provider_status != "Sent":
		frappe.throw(_("This form is not waiting for a signature provider"))
	traccia.traccia(
		MODULO, doc.name, "provider_withdrawn", doc.provider, {"reference": doc.provider_reference}
	)
	doc.db_set({"provider_status": None, "provider_reference": None})
	return get_form(doc.name)


def dal_fornitore(doc, fornitore, esito: dict) -> None:
	"""What the provider's webhook said about a form it has. Signed, the form is
	closed on the answers that went to it, with the provider's PDF; a repeated
	call changes nothing."""
	if doc.docstatus != 0 or doc.provider_status != "Sent":
		return
	evento = esito.get("event")
	if evento in ("declined", "expired"):
		doc.db_set("provider_status", "Declined" if evento == "declined" else "Expired")
		traccia.traccia(MODULO, doc.name, f"provider_{evento}", fornitore.nome)
		return
	if evento != "signed":
		return
	versione = _versione(doc)
	schema = modelli.carica_schema(versione.schema)
	risposte_firmate, stato = _controlla(schema, _risposte(doc), {}, senza_firme=True)
	impronta = impronta_risposte(versione.schema_hash, risposte_firmate)
	adesso = now_datetime()
	riferimento = doc.provider_reference
	# the operator of an operator's signature is whoever sent it to the provider
	mandato = frappe.get_all(
		traccia.REGISTRO,
		filters={"reference_doctype": MODULO, "reference_name": doc.name, "event": "provider_sent"},
		pluck="user",
		order_by="creation desc",
		limit=1,
	)
	operatore = doc.filled_by or (mandato[0] if mandato else None)
	firmati = {firmatario.get("field"): firmatario for firmatario in esito.get("signers") or []}
	righe = []
	for campo in _firme_visibili(schema, stato):
		chi, utente, persona = _firmatario(campo, doc, operatore)
		dati = firmati.get(campo.get("id")) or {}
		righe.append(
			{
				"field": campo.get("id"),
				"signer": _veste(campo, doc),
				"signer_name": chi,
				"signer_user": utente,
				"signer_lead": persona,
				"level": campo.get("level") or "simple",
				"method": "Provider",
				"provider": fornitore.nome,
				"provider_reference": riferimento,
				"signed_at": dati.get("signed_at") or adesso,
				"ip_address": dati.get("ip_address"),
				"user_agent": dati.get("user_agent"),
				"document_hash": impronta,
			}
		)
	firmato = fornitore.firmato(riferimento)
	prove = fornitore.prove(riferimento)
	doc.provider_status = "Signed"

	from crm.moduli import pdf

	_chiudi(
		doc,
		schema,
		risposte_firmate,
		stato,
		righe,
		impronta,
		adesso,
		ignora_permessi=True,
		dettagli={"method": "Provider", "provider": fornitore.nome, "reference": riferimento},
		fai_il_pdf=lambda firmando: pdf.allega_dal_fornitore(firmando, firmato, prove, fornitore.nome),
	)


def completa(doc, risposte: dict) -> None:
	"""A form filled away from the desk and signed at it: every answer is checked
	now, the signatures are left for the desk."""
	schema = modelli.carica_schema(_versione(doc).schema)
	puliti, stato = _controlla(schema, risposte, {}, senza_firme=True)
	doc.answers = json.dumps(puliti, ensure_ascii=False)
	doc.alerts = json.dumps(stato["stops"], ensure_ascii=False)
	doc.flags.ignore_permissions = True
	doc.save()
	traccia.traccia(MODULO, doc.name, "filled", _("To sign at the desk"), {"channel": doc.channel})


def _registra_consensi(doc, schema: dict, risposte: dict, stato: dict) -> None:
	"""Every consent the form asked goes into the register, on the words it showed.
	A sheet records none: a consent is the person's to give."""
	from crm.moduli import consensi, registro

	if not modelli.uso(_versione(doc).use).della_persona:
		return
	ip, dispositivo = _richiesta()
	for campo in S.campi(schema):
		chiave = campo.get("id")
		if campo.get("type") != "consent" or not stato["visible"].get(chiave) or chiave not in risposte:
			continue
		consensi.registra_risposta(
			doc.lead,
			campo.get("consent_type"),
			registro.DATO if risposte[chiave] else registro.RIFIUTATO,
			CANALE_DEL_REGISTRO.get(doc.channel, "At the desk"),
			testo=campo.get("text"),
			versione_testo=campo.get("text_version"),
			fonte=(MODULO, doc.name),
			ip=ip,
			browser=dispositivo,
			dato_da=doc.given_by,
		)
		traccia.traccia(
			MODULO,
			doc.name,
			"consent_recorded",
			campo.get("consent_type"),
			{"consent": campo.get("consent_type"), "given": bool(risposte[chiave])},
		)


@frappe.whitelist(methods=["POST"])
def discard_form(name: str) -> None:
	"""A draft goes, with the events of it: nothing was signed on it."""
	doc = _bozza(name)
	if doc.get("request"):
		# the request it came from goes with it: its link opens nothing any more
		frappe.db.set_value(RICHIESTA, doc.request, {"form": None, "status": "Cancelled"})
	frappe.db.delete(traccia.REGISTRO, {"reference_doctype": MODULO, "reference_name": doc.name})
	frappe.delete_doc(MODULO, doc.name)
